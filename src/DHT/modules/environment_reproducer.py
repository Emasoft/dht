#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Initial implementation of deterministic environment reproducer
# - Implements version-based validation over hash matching
# - Provides cross-platform environment reproduction
# - Supports tool isolation and platform normalization
# - Creates reproducible lock files and configuration snapshots
# - Integrates with UV, diagnostic reporter, and environment configurator
# 

"""
Deterministic Environment Reproducer Module.

This module implements DHT's core philosophy: "Identical behavior matters more than 
identical binaries." It ensures that environments can be reproduced deterministically
across different platforms by focusing on functional equivalence rather than binary 
matching.

Key Features:
- Version-based validation over hash matching
- Tool isolation and platform normalization 
- Reproducible environment snapshots
- Cross-platform compatibility verification
- Deterministic build environments
- Configuration fingerprinting
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Union, Tuple
import tempfile

from prefect import task, flow, get_run_logger
from prefect.artifacts import create_markdown_artifact, create_table_artifact

from DHT.diagnostic_reporter_v2 import build_system_report
from DHT.modules.environment_configurator import EnvironmentConfigurator, EnvironmentConfig
from DHT.modules.uv_prefect_tasks import (
    check_uv_available,
    list_python_versions,
    generate_lock_file,
    ensure_python_version
)
from DHT.modules.guardian_prefect import run_with_guardian, ResourceLimits

# Import refactored modules
from DHT.modules.environment_snapshot_models import EnvironmentSnapshot, ReproductionResult
from DHT.modules.platform_normalizer import (
    get_platform_info,
    normalize_platform_name,
    get_tool_command,
    verify_platform_compatibility,
    normalize_environment_variables
)
from DHT.modules.lock_file_manager import LockFileManager, LockFileInfo
from DHT.modules.environment_validator import EnvironmentValidator
from DHT.modules.tool_version_manager import ToolVersionManager
from DHT.modules.environment_snapshot_io import EnvironmentSnapshotIO
from DHT.modules.reproduction_artifacts import ReproductionArtifactCreator
from DHT.modules.environment_reproduction_steps import ReproductionStepsGenerator
from DHT.modules.dependencies_installer import DependenciesInstaller


# Note: EnvironmentSnapshot and ReproductionResult are now imported from environment_snapshot_models.py


class EnvironmentReproducer:
    """Deterministic environment reproduction system."""
    
    def __init__(self):
        """Initialize the environment reproducer."""
        self.logger = None
        self.configurator = EnvironmentConfigurator()
        self.lock_manager = LockFileManager()
        self.validator = EnvironmentValidator()
        self.tool_manager = ToolVersionManager()
        self.snapshot_io = EnvironmentSnapshotIO()
        
        # Use tool manager's categorization
        self.version_critical_tools = self.tool_manager.version_critical_tools
        self.behavior_compatible_tools = self.tool_manager.behavior_compatible_tools
        
        # Initialize other helpers
        self.artifact_creator = ReproductionArtifactCreator(self.version_critical_tools)
        self.steps_generator = ReproductionStepsGenerator(self.version_critical_tools)
        self.deps_installer = DependenciesInstaller()
    
    def _get_logger(self):
        """Get logger with fallback."""
        if self.logger is None:
            try:
                self.logger = get_run_logger()
            except Exception:
                import logging
                self.logger = logging.getLogger(__name__)
        return self.logger
    
    @task(
        name="capture_environment_snapshot",
        description="Capture complete environment snapshot for reproduction"
    )
    def capture_environment_snapshot(
        self,
        project_path: Optional[Path] = None,
        include_system_info: bool = True,
        include_configs: bool = True
    ) -> EnvironmentSnapshot:
        """
        Capture a complete snapshot of the current environment.
        
        Args:
            project_path: Optional project path to include project-specific info
            include_system_info: Whether to include detailed system information
            include_configs: Whether to include configuration files
            
        Returns:
            EnvironmentSnapshot with all environment details
        """
        logger = self._get_logger()
        logger.info("Capturing environment snapshot...")
        
        # Generate snapshot metadata
        snapshot_id = self._generate_snapshot_id()
        timestamp = datetime.now().isoformat()
        
        # Get platform information
        platform_info = get_platform_info()
        
        snapshot = EnvironmentSnapshot(
            timestamp=timestamp,
            platform=platform_info["system"],
            architecture=platform_info["architecture"],
            dht_version=self._get_dht_version(),
            snapshot_id=snapshot_id,
            python_version=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            python_executable=sys.executable
        )
        
        # Capture Python environment
        self._capture_python_environment(snapshot)
        
        # Capture system tools
        self._capture_system_tools(snapshot)
        
        # Capture environment variables
        self._capture_environment_variables(snapshot)
        
        # Capture project-specific information if provided
        if project_path:
            project_path = Path(project_path)
            if project_path.exists():
                self._capture_project_info(snapshot, project_path, include_configs)
        
        # Generate reproduction steps
        self.steps_generator.generate_reproduction_steps(snapshot)
        
        logger.info(f"Environment snapshot captured: {snapshot_id}")
        return snapshot
    
    def _generate_snapshot_id(self) -> str:
        """Generate a unique snapshot ID."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        platform_short = platform.system().lower()[:3]
        random_suffix = hashlib.md5(str(datetime.now()).encode()).hexdigest()[:8]
        return f"dht_{platform_short}_{timestamp}_{random_suffix}"
    
    def _get_dht_version(self) -> str:
        """Get DHT version."""
        try:
            # Try to get version from pyproject.toml
            pyproject_path = Path(__file__).parent.parent.parent / "pyproject.toml"
            if pyproject_path.exists():
                try:
                    import tomllib
                except ImportError:
                    import tomli as tomllib
                
                with open(pyproject_path, "rb") as f:
                    data = tomllib.load(f)
                
                return data.get("project", {}).get("version", "unknown")
        except Exception:
            pass
        
        return "development"
    
    def _capture_python_environment(self, snapshot: EnvironmentSnapshot):
        """Capture Python environment details."""
        logger = self._get_logger()
        
        try:
            # Get installed packages using pip list
            result = subprocess.run([
                sys.executable, "-m", "pip", "list", "--format=json"
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                packages = json.loads(result.stdout)
                for pkg in packages:
                    snapshot.python_packages[pkg["name"]] = pkg["version"]
            
        except Exception as e:
            logger.warning(f"Failed to capture Python packages: {e}")
        
        # Try to get UV packages if available
        try:
            uv_check = check_uv_available()
            if uv_check["available"]:
                # Get UV managed packages
                result = subprocess.run([
                    "uv", "pip", "list", "--format=json"
                ], capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    uv_packages = json.loads(result.stdout)
                    for pkg in uv_packages:
                        # UV packages take precedence as they're more precisely managed
                        snapshot.python_packages[pkg["name"]] = pkg["version"]
                        
        except Exception as e:
            logger.debug(f"UV package listing failed: {e}")
    
    def _capture_system_tools(self, snapshot: EnvironmentSnapshot):
        """Capture system tool versions."""
        logger = self._get_logger()
        
        # Use tool manager to capture tool versions
        tools_info = self.tool_manager.capture_tool_versions()
        
        for tool_name, info in tools_info.items():
            snapshot.tool_versions[tool_name] = info["version"]
            snapshot.tool_paths[tool_name] = info["path"]
    
    
    def _capture_environment_variables(self, snapshot: EnvironmentSnapshot):
        """Capture relevant environment variables."""
        # Important environment variables for development
        important_vars = {
            "PATH", "PYTHONPATH", "VIRTUAL_ENV", "CONDA_DEFAULT_ENV",
            "NODE_ENV", "UV_PYTHON", "PIP_INDEX_URL", "PIP_EXTRA_INDEX_URL",
            "PYTHONDONTWRITEBYTECODE", "PYTHONUNBUFFERED",
            "CC", "CXX", "CFLAGS", "CXXFLAGS"
        }
        
        env_vars = {}
        for var in important_vars:
            value = os.environ.get(var)
            if value:
                env_vars[var] = value
        
        # Normalize environment variables for platform compatibility
        snapshot.environment_variables = normalize_environment_variables(env_vars)
        
        # Capture PATH entries separately for analysis
        path_var = os.environ.get("PATH", "")
        if path_var:
            snapshot.path_entries = path_var.split(os.pathsep)
    
    def _capture_project_info(
        self, 
        snapshot: EnvironmentSnapshot, 
        project_path: Path, 
        include_configs: bool
    ):
        """Capture project-specific information."""
        logger = self._get_logger()
        
        snapshot.project_path = str(project_path)
        
        # Analyze project with configurator
        try:
            analysis = self.configurator.analyze_environment_requirements(
                project_path=project_path,
                include_system_info=False
            )
            
            project_info = analysis.get("project_info", {})
            snapshot.project_type = project_info.get("project_type", "unknown")
            
        except Exception as e:
            logger.warning(f"Failed to analyze project: {e}")
        
        # Use lock file manager to handle lock files
        try:
            lock_files_info = self.lock_manager.generate_project_lock_files(
                project_path, snapshot.project_type
            )
            
            for filename, lock_info in lock_files_info.items():
                snapshot.lock_files[filename] = lock_info.content
                snapshot.checksums[filename] = lock_info.checksum
        except Exception as e:
            logger.warning(f"Failed to capture lock files: {e}")
        
        # Capture configuration files if requested
        if include_configs:
            config_files = [
                "pyproject.toml", "setup.py", "setup.cfg", 
                "package.json", "tsconfig.json",
                ".python-version", ".node-version",
                "ruff.toml", "mypy.ini", "pytest.ini",
                ".pre-commit-config.yaml", ".gitignore"
            ]
            
            for config_file in config_files:
                config_path = project_path / config_file
                if config_path.exists():
                    try:
                        content = config_path.read_text(encoding='utf-8')
                        snapshot.config_files[config_file] = content
                        checksum = hashlib.sha256(content.encode()).hexdigest()
                        snapshot.checksums[config_file] = checksum
                    except Exception as e:
                        logger.warning(f"Failed to read {config_file}: {e}")
    
    
    @task(
        name="reproduce_environment",
        description="Reproduce environment from snapshot"
    )
    def reproduce_environment(
        self,
        snapshot: EnvironmentSnapshot,
        target_path: Optional[Path] = None,
        strict_mode: bool = True,
        auto_install: bool = False
    ) -> ReproductionResult:
        """
        Reproduce an environment from a snapshot.
        
        Args:
            snapshot: Environment snapshot to reproduce
            target_path: Target directory for reproduction
            strict_mode: Whether to require exact version matches
            auto_install: Whether to automatically install missing tools
            
        Returns:
            ReproductionResult with verification details
        """
        logger = self._get_logger()
        logger.info(f"Reproducing environment from snapshot {snapshot.snapshot_id}")
        
        result = ReproductionResult(
            success=False,
            snapshot_id=snapshot.snapshot_id,
            platform=platform.system().lower()
        )
        
        try:
            # 1. Verify platform compatibility
            self._verify_platform_compatibility(snapshot, result)
            
            # 2. Verify Python version
            self._verify_python_version(snapshot, result, auto_install)
            
            # 3. Verify tools
            self._verify_tools(snapshot, result, strict_mode, auto_install)
            
            # 4. Reproduce project environment if specified
            if target_path and snapshot.project_path:
                self._reproduce_project_environment(
                    snapshot, result, target_path, auto_install
                )
            
            # 5. Verify configurations
            if target_path:
                self._verify_configurations(snapshot, result, target_path)
            
            # Determine overall success
            result.success = (
                len(result.actions_failed) == 0 and
                len(result.missing_tools) == 0 and
                all(result.tools_verified.values()) and
                all(result.versions_verified.values())
            )
            
            logger.info(f"Environment reproduction {'succeeded' if result.success else 'failed'}")
            
        except Exception as e:
            logger.error(f"Environment reproduction failed: {e}")
            result.actions_failed.append(f"reproduction_error: {str(e)}")
        
        return result
    
    def _verify_platform_compatibility(
        self, 
        snapshot: EnvironmentSnapshot, 
        result: ReproductionResult
    ):
        """Verify platform compatibility."""
        is_compatible, warnings = verify_platform_compatibility(
            snapshot.platform,
            platform.system().lower()
        )
        
        result.warnings.extend(warnings)
        
        if not is_compatible:
            result.actions_failed.append(
                f"Platform incompatibility: {snapshot.platform} -> {platform.system().lower()}"
            )
    
    def _verify_python_version(
        self, 
        snapshot: EnvironmentSnapshot, 
        result: ReproductionResult,
        auto_install: bool
    ):
        """Verify Python version compatibility."""
        current_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        expected_version = snapshot.python_version
        
        result.versions_verified["python"] = current_version == expected_version
        
        if not result.versions_verified["python"]:
            result.version_mismatches["python"] = (expected_version, current_version)
            
            # Check if version is compatible (same major.minor)
            expected_parts = expected_version.split(".")
            current_parts = current_version.split(".")
            
            if (len(expected_parts) >= 2 and len(current_parts) >= 2 and
                expected_parts[0] == current_parts[0] and
                expected_parts[1] == current_parts[1]):
                result.warnings.append(
                    f"Python version compatible: {current_version} vs {expected_version}"
                )
            else:
                if auto_install:
                    self._install_python_version(snapshot, result)
                else:
                    result.actions_failed.append(
                        f"Python version mismatch: need {expected_version}, have {current_version}"
                    )
    
    def _verify_tools(
        self, 
        snapshot: EnvironmentSnapshot, 
        result: ReproductionResult,
        strict_mode: bool,
        auto_install: bool
    ):
        """Verify tool versions."""
        for tool, expected_version in snapshot.tool_versions.items():
            # Check if tool is installed
            tool_path = shutil.which(tool)
            if not tool_path:
                result.missing_tools.append(tool)
                result.tools_verified[tool] = False
                
                if auto_install:
                    self._install_tool(tool, expected_version, result)
                continue
            
            # Get current version
            try:
                version_cmd = self._get_version_command(tool)
                if version_cmd:
                    proc_result = subprocess.run(
                        version_cmd,
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    
                    if proc_result.returncode == 0:
                        current_version = self.tool_manager.extract_version_from_output(
                            proc_result.stdout + proc_result.stderr
                        )
                        
                        if current_version:
                            # Check version compatibility
                            versions_match = self.tool_manager.compare_versions(
                                expected_version, current_version, tool, strict_mode
                            )
                            
                            result.tools_verified[tool] = True
                            result.versions_verified[tool] = versions_match
                            
                            if not versions_match:
                                result.version_mismatches[tool] = (expected_version, current_version)
                        else:
                            result.tools_verified[tool] = True
                            result.versions_verified[tool] = False
                            result.warnings.append(f"Could not determine {tool} version")
                    else:
                        result.tools_verified[tool] = False
                        result.warnings.append(f"Failed to check {tool} version")
                        
            except Exception as e:
                result.tools_verified[tool] = False
                result.warnings.append(f"Error checking {tool}: {e}")
    
    def _get_version_command(self, tool: str) -> Optional[List[str]]:
        """Get version command for a tool."""
        return get_tool_command(tool)
    
    
    def _install_python_version(
        self, 
        snapshot: EnvironmentSnapshot, 
        result: ReproductionResult
    ):
        """Attempt to install the required Python version."""
        logger = self._get_logger()
        
        try:
            # Try using UV to install Python
            uv_check = check_uv_available()
            if uv_check["available"]:
                python_path = ensure_python_version(snapshot.python_version)
                result.actions_completed.append(
                    f"Installed Python {snapshot.python_version} via UV"
                )
                logger.info(f"Installed Python {snapshot.python_version} at {python_path}")
                return
                
        except Exception as e:
            logger.warning(f"Failed to install Python via UV: {e}")
        
        # Provide manual installation instructions
        result.warnings.append(
            f"Manual installation required: Python {snapshot.python_version}"
        )
        result.actions_failed.append(
            f"Could not auto-install Python {snapshot.python_version}"
        )
    
    def _install_tool(self, tool: str, version: str, result: ReproductionResult):
        """Attempt to install a missing tool."""
        logger = self._get_logger()
        
        install_cmd = self.tool_manager.get_installation_command(tool, version)
        
        if install_cmd:
            result.warnings.append(
                f"Manual installation suggested for {tool}: {install_cmd}"
            )
        else:
            result.warnings.append(
                f"No automatic installation available for {tool} on {platform.system().lower()}"
            )
        
        result.missing_tools.append(tool)
    
    def _reproduce_project_environment(
        self,
        snapshot: EnvironmentSnapshot,
        result: ReproductionResult,
        target_path: Path,
        auto_install: bool
    ):
        """Reproduce the project environment."""
        logger = self._get_logger()
        
        try:
            target_path = Path(target_path)
            target_path.mkdir(parents=True, exist_ok=True)
            
            # Restore lock files
            for filename, content in snapshot.lock_files.items():
                lock_file_path = target_path / filename
                lock_file_path.write_text(content, encoding='utf-8')
                
                # Verify checksum
                actual_checksum = hashlib.sha256(content.encode()).hexdigest()
                expected_checksum = snapshot.checksums.get(filename)
                
                if expected_checksum and actual_checksum == expected_checksum:
                    result.actions_completed.append(f"Restored {filename}")
                else:
                    result.warnings.append(f"Checksum mismatch for {filename}")
            
            # Restore configuration files
            for filename, content in snapshot.config_files.items():
                config_file_path = target_path / filename
                config_file_path.write_text(content, encoding='utf-8')
                result.actions_completed.append(f"Restored config {filename}")
            
            # Install dependencies if auto_install is enabled
            if auto_install:
                self.deps_installer.install_project_dependencies(snapshot, result, target_path)
                
        except Exception as e:
            logger.error(f"Failed to reproduce project environment: {e}")
            result.actions_failed.append(f"project_reproduction_error: {str(e)}")
    
    
    def _verify_configurations(
        self,
        snapshot: EnvironmentSnapshot,
        result: ReproductionResult,
        target_path: Path
    ):
        """Verify configuration files match the snapshot."""
        # Use validator to verify configurations
        config_results = self.validator.verify_configurations(
            target_path,
            snapshot.config_files,
            snapshot.checksums
        )
        
        result.configs_verified = config_results["verified"]
        result.config_differences = config_results["differences"]
    
    @task(
        name="save_environment_snapshot",
        description="Save environment snapshot to file"
    )
    def save_environment_snapshot(
        self,
        snapshot: EnvironmentSnapshot,
        output_path: Path,
        format: str = "json"
    ) -> Path:
        """Save environment snapshot to file."""
        return self.snapshot_io.save_snapshot(snapshot, output_path, format)
    
    def load_environment_snapshot(self, snapshot_path: Path) -> EnvironmentSnapshot:
        """Load environment snapshot from file."""
        return self.snapshot_io.load_snapshot(snapshot_path)
    
    @flow(
        name="create_reproducible_environment",
        description="Complete flow for creating reproducible environments"
    )
    def create_reproducible_environment(
        self,
        project_path: Path,
        output_dir: Optional[Path] = None,
        include_system_info: bool = True,
        save_snapshot: bool = True,
        verify_reproduction: bool = True
    ) -> Dict[str, Any]:
        """
        Complete flow for creating reproducible environments.
        
        Args:
            project_path: Path to project to make reproducible
            output_dir: Directory to save snapshots and verification results
            include_system_info: Whether to include system information
            save_snapshot: Whether to save snapshot to file
            verify_reproduction: Whether to verify reproduction works
            
        Returns:
            Dictionary with flow results
        """
        import time
        start_time = time.time()
        
        logger = self._get_logger()
        project_path = Path(project_path)
        
        if output_dir is None:
            output_dir = project_path / ".dht" / "snapshots"
        
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        results = {
            "project_path": str(project_path),
            "timestamp": datetime.now().isoformat(),
            "steps": []
        }
        
        try:
            # Step 1: Capture environment snapshot
            logger.info("Capturing environment snapshot...")
            snapshot = self.capture_environment_snapshot(
                project_path=project_path,
                include_system_info=include_system_info
            )
            results["snapshot_id"] = snapshot.snapshot_id
            results["steps"].append("capture_snapshot")
            
            # Step 2: Save snapshot if requested
            if save_snapshot:
                snapshot_file = output_dir / f"{snapshot.snapshot_id}.json"
                saved_path = self.save_environment_snapshot(
                    snapshot=snapshot,
                    output_path=snapshot_file
                )
                results["snapshot_file"] = str(saved_path)
                results["steps"].append("save_snapshot")
                logger.info(f"Snapshot saved to {saved_path}")
            
            # Step 3: Verify reproduction if requested
            if verify_reproduction:
                logger.info("Verifying environment reproduction...")
                
                # Create temporary directory for verification
                with tempfile.TemporaryDirectory() as temp_dir:
                    verification_result = self.reproduce_environment(
                        snapshot=snapshot,
                        target_path=Path(temp_dir) / "verification",
                        strict_mode=False,  # Use lenient mode for verification
                        auto_install=False  # Don't auto-install during verification
                    )
                    
                    results["verification"] = {
                        "success": verification_result.success,
                        "tools_verified": verification_result.tools_verified,
                        "version_mismatches": verification_result.version_mismatches,
                        "missing_tools": verification_result.missing_tools,
                        "warnings": verification_result.warnings
                    }
                    results["steps"].append("verify_reproduction")
            
            # Step 4: Generate reproduction guide
            self.artifact_creator.create_reproduction_artifacts(snapshot, results, output_dir)
            results["steps"].append("create_artifacts")
            
            results["success"] = True
            
        except Exception as e:
            logger.error(f"Reproducible environment creation failed: {e}")
            results["success"] = False
            results["error"] = str(e)
        
        results["execution_time"] = time.time() - start_time
        
        logger.info(f"Reproducible environment creation {'completed' if results['success'] else 'failed'}")
        return results
    


# Export public API
__all__ = [
    "EnvironmentReproducer",
    "EnvironmentSnapshot",
    "ReproductionResult"
]