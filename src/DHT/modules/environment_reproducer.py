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
import platform
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import tempfile

from prefect import task, flow, get_run_logger

from DHT.modules.environment_configurator import EnvironmentConfigurator

# Import refactored modules
from DHT.modules.environment_snapshot_models import EnvironmentSnapshot, ReproductionResult
from DHT.modules.platform_normalizer import (
    get_platform_info
)
from DHT.modules.lock_file_manager import LockFileManager
from DHT.modules.environment_validator import EnvironmentValidator
from DHT.modules.tool_version_manager import ToolVersionManager
from DHT.modules.environment_snapshot_io import EnvironmentSnapshotIO
from DHT.modules.reproduction_artifacts import ReproductionArtifactCreator
from DHT.modules.environment_reproduction_steps import ReproductionStepsGenerator
from DHT.modules.dependencies_installer import DependenciesInstaller
from DHT.modules.environment_capture_utils import EnvironmentCaptureUtils
from DHT.modules.project_capture_utils import ProjectCaptureUtils
from DHT.modules.environment_verification_utils import EnvironmentVerificationUtils
from DHT.modules.reproduction_flow_utils import ReproductionFlowUtils


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
        self.env_capture_utils = EnvironmentCaptureUtils()
        self.project_capture_utils = ProjectCaptureUtils()
        self.env_verification_utils = EnvironmentVerificationUtils()
        self.flow_utils = ReproductionFlowUtils(self)
    
    def _get_logger(self):
        """Get logger with fallback."""
        if self.logger is None:
            try:
                self.logger = get_run_logger()
            except Exception:
                import logging
                self.logger = logging.getLogger(__name__)
        return self.logger
    
    def _capture_environment_snapshot_impl(
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
            dht_version=self.env_capture_utils.get_dht_version(),
            snapshot_id=snapshot_id,
            python_version=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            python_executable=sys.executable
        )
        
        # Capture Python environment
        self.env_capture_utils.capture_python_packages(snapshot)
        
        # Capture system tools
        self._capture_system_tools(snapshot)
        
        # Capture environment variables
        self.env_capture_utils.capture_environment_variables(snapshot)
        
        # Capture project-specific information if provided
        if project_path:
            project_path = Path(project_path)
            if project_path.exists():
                self.project_capture_utils.capture_project_info(snapshot, project_path, include_configs)
        
        # Generate reproduction steps
        self.steps_generator.generate_reproduction_steps(snapshot)
        
        logger.info(f"Environment snapshot captured: {snapshot_id}")
        return snapshot
    
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
        """Prefect task wrapper for capture_environment_snapshot."""
        return self._capture_environment_snapshot_impl(project_path, include_system_info, include_configs)
    
    def _generate_snapshot_id(self) -> str:
        """Generate a unique snapshot ID."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        platform_short = platform.system().lower()[:3]
        random_suffix = hashlib.md5(str(datetime.now()).encode()).hexdigest()[:8]
        return f"dht_{platform_short}_{timestamp}_{random_suffix}"
    
    
    
    def _capture_system_tools(self, snapshot: EnvironmentSnapshot):
        """Capture system tool versions."""
        logger = self._get_logger()
        
        # Use tool manager to capture tool versions
        tools_info = self.tool_manager.capture_tool_versions()
        
        for tool_name, info in tools_info.items():
            snapshot.tool_versions[tool_name] = info["version"]
            snapshot.tool_paths[tool_name] = info["path"]
    
    
    
    
    
    def _reproduce_environment_impl(
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
            self.env_verification_utils.verify_platform_compatibility(snapshot, result)
            
            # 2. Verify Python version
            self.env_verification_utils.verify_python_version(snapshot, result, auto_install)
            
            # 3. Verify tools
            self.env_verification_utils.verify_tools(snapshot, result, strict_mode, auto_install)
            
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
        """Prefect task wrapper for reproduce_environment."""
        return self._reproduce_environment_impl(snapshot, target_path, strict_mode, auto_install)
    
    
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
    
    def _save_environment_snapshot_impl(
        self,
        snapshot: EnvironmentSnapshot,
        output_path: Path,
        format: str = "json"
    ) -> Path:
        """Save environment snapshot to file."""
        return self.snapshot_io.save_snapshot(snapshot, output_path, format)
    
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
        """Prefect task wrapper for save_environment_snapshot."""
        return self._save_environment_snapshot_impl(snapshot, output_path, format)
    
    def load_environment_snapshot(self, snapshot_path: Path) -> EnvironmentSnapshot:
        """Load environment snapshot from file."""
        return self.snapshot_io.load_snapshot(snapshot_path)
    
    def _create_reproducible_environment_impl(
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
            snapshot = self._capture_environment_snapshot_impl(
                project_path=project_path,
                include_system_info=include_system_info
            )
            results["snapshot_id"] = snapshot.snapshot_id
            results["steps"].append("capture_snapshot")
            
            # Step 2: Save snapshot if requested
            if save_snapshot:
                snapshot_file = output_dir / f"{snapshot.snapshot_id}.json"
                saved_path = self._save_environment_snapshot_impl(
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
                    verification_result = self._reproduce_environment_impl(
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
        """Prefect flow wrapper for create_reproducible_environment."""
        return self._create_reproducible_environment_impl(
            project_path, output_dir, include_system_info, save_snapshot, verify_reproduction
        )


# Export public API
__all__ = [
    "EnvironmentReproducer",
    "EnvironmentSnapshot",
    "ReproductionResult"
]