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
from dataclasses import dataclass, field
import tempfile

from prefect import task, flow, get_run_logger
from prefect.artifacts import create_markdown_artifact, create_table_artifact

from DHT.diagnostic_reporter_v2 import build_system_report
from DHT.modules.environment_configurator import EnvironmentConfigurator, EnvironmentConfig
from DHT.modules.uv_prefect_tasks import (
    check_uv_available,
    list_python_versions,
    generate_lock_file
)
from DHT.modules.guardian_prefect import run_with_guardian, ResourceLimits


@dataclass
class EnvironmentSnapshot:
    """Snapshot of a development environment for reproduction."""
    
    # Metadata
    timestamp: str
    platform: str
    architecture: str
    dht_version: str
    snapshot_id: str
    
    # Core environment
    python_version: str
    python_executable: str
    python_packages: Dict[str, str] = field(default_factory=dict)  # name -> version
    system_packages: Dict[str, str] = field(default_factory=dict)  # name -> version  
    
    # Tool versions (exact versions for reproducibility)
    tool_versions: Dict[str, str] = field(default_factory=dict)  # tool -> version
    tool_paths: Dict[str, str] = field(default_factory=dict)     # tool -> path
    tool_configs: Dict[str, Any] = field(default_factory=dict)   # tool -> config
    
    # Environment variables and settings
    environment_variables: Dict[str, str] = field(default_factory=dict)
    path_entries: List[str] = field(default_factory=list)
    
    # Project-specific information
    project_path: str = ""
    project_type: str = ""
    lock_files: Dict[str, str] = field(default_factory=dict)  # filename -> content
    config_files: Dict[str, str] = field(default_factory=dict)  # filename -> content
    
    # Checksums for verification
    checksums: Dict[str, str] = field(default_factory=dict)  # file -> checksum
    
    # Reproduction instructions
    reproduction_steps: List[str] = field(default_factory=list)
    platform_notes: List[str] = field(default_factory=list)


@dataclass 
class ReproductionResult:
    """Result of environment reproduction attempt."""
    success: bool
    snapshot_id: str
    platform: str
    
    # Verification results
    tools_verified: Dict[str, bool] = field(default_factory=dict)
    versions_verified: Dict[str, bool] = field(default_factory=dict)
    configs_verified: Dict[str, bool] = field(default_factory=dict)
    
    # Discrepancies found
    version_mismatches: Dict[str, Tuple[str, str]] = field(default_factory=dict)  # tool -> (expected, actual)
    missing_tools: List[str] = field(default_factory=list)
    config_differences: Dict[str, str] = field(default_factory=dict)  # file -> diff
    
    # Reproduction actions taken
    actions_completed: List[str] = field(default_factory=list)
    actions_failed: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    execution_time: float = 0.0


class EnvironmentReproducer:
    """Deterministic environment reproduction system."""
    
    def __init__(self):
        """Initialize the environment reproducer."""
        self.logger = None
        self.configurator = EnvironmentConfigurator()
        
        # Critical tools that must match versions exactly
        self.version_critical_tools = {
            "python", "pip", "uv", "git", "node", "npm", 
            "black", "ruff", "mypy", "pytest"
        }
        
        # Tools where behavior compatibility is more important than exact versions
        self.behavior_compatible_tools = {
            "curl", "wget", "tar", "zip", "make", "gcc", "clang"
        }
        
        # Platform-specific tool mappings for equivalence
        self.platform_tool_equivalents = {
            "package_manager": {
                "darwin": ["brew", "port"],
                "linux": ["apt", "yum", "dnf", "pacman", "zypper"],
                "windows": ["choco", "winget", "scoop"]
            },
            "compiler": {
                "darwin": ["clang", "gcc"],
                "linux": ["gcc", "clang"],
                "windows": ["cl", "gcc", "clang"]
            }
        }
    
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
        platform_info = platform.uname()
        
        snapshot = EnvironmentSnapshot(
            timestamp=timestamp,
            platform=platform_info.system.lower(),
            architecture=platform_info.machine,
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
        self._generate_reproduction_steps(snapshot)
        
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
        
        # Define tools to check with their version commands
        tools_to_check = {
            "git": ["git", "--version"],
            "uv": ["uv", "--version"],
            "node": ["node", "--version"],
            "npm": ["npm", "--version"],
            "docker": ["docker", "--version"],
            "make": ["make", "--version"],
            "gcc": ["gcc", "--version"],
            "clang": ["clang", "--version"],
            "python": ["python", "--version"],
            "pip": ["pip", "--version"],
            "black": ["black", "--version"],
            "ruff": ["ruff", "--version"],
            "mypy": ["mypy", "--version"],
            "pytest": ["pytest", "--version"],
        }
        
        for tool_name, version_cmd in tools_to_check.items():
            try:
                # Check if tool is available
                tool_path = shutil.which(version_cmd[0])
                if tool_path:
                    snapshot.tool_paths[tool_name] = tool_path
                    
                    # Get version
                    result = subprocess.run(
                        version_cmd, 
                        capture_output=True, 
                        text=True, 
                        timeout=10
                    )
                    
                    if result.returncode == 0:
                        version = self._extract_version_from_output(
                            result.stdout + result.stderr
                        )
                        if version:
                            snapshot.tool_versions[tool_name] = version
                            
            except Exception as e:
                logger.debug(f"Failed to check {tool_name}: {e}")
    
    def _extract_version_from_output(self, output: str) -> Optional[str]:
        """Extract version number from tool output."""
        import re
        
        # Common version patterns
        patterns = [
            r'(\d+\.\d+\.\d+)',           # x.y.z
            r'(\d+\.\d+)',                # x.y
            r'v(\d+\.\d+\.\d+)',          # vx.y.z
            r'version (\d+\.\d+\.\d+)',   # version x.y.z
        ]
        
        for pattern in patterns:
            match = re.search(pattern, output)
            if match:
                return match.group(1)
        
        return None
    
    def _capture_environment_variables(self, snapshot: EnvironmentSnapshot):
        """Capture relevant environment variables."""
        # Important environment variables for development
        important_vars = {
            "PATH", "PYTHONPATH", "VIRTUAL_ENV", "CONDA_DEFAULT_ENV",
            "NODE_ENV", "UV_PYTHON", "PIP_INDEX_URL", "PIP_EXTRA_INDEX_URL",
            "PYTHONDONTWRITEBYTECODE", "PYTHONUNBUFFERED",
            "CC", "CXX", "CFLAGS", "CXXFLAGS"
        }
        
        for var in important_vars:
            value = os.environ.get(var)
            if value:
                snapshot.environment_variables[var] = value
        
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
        
        # Capture lock files
        lock_files = [
            "uv.lock", "poetry.lock", "Pipfile.lock", "package-lock.json",
            "yarn.lock", "pnpm-lock.yaml", "requirements.txt"
        ]
        
        for lock_file in lock_files:
            lock_path = project_path / lock_file
            if lock_path.exists():
                try:
                    content = lock_path.read_text(encoding='utf-8')
                    snapshot.lock_files[lock_file] = content
                    # Generate checksum
                    checksum = hashlib.sha256(content.encode()).hexdigest()
                    snapshot.checksums[lock_file] = checksum
                except Exception as e:
                    logger.warning(f"Failed to read {lock_file}: {e}")
        
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
    
    def _generate_reproduction_steps(self, snapshot: EnvironmentSnapshot):
        """Generate platform-specific reproduction steps."""
        steps = []
        
        # 1. Python version setup
        steps.append(f"Install Python {snapshot.python_version}")
        if "uv" in snapshot.tool_versions:
            steps.append(f"Install UV {snapshot.tool_versions['uv']}")
            steps.append(f"uv python pin {snapshot.python_version}")
        
        # 2. Create virtual environment
        steps.append("Create virtual environment")
        if "uv" in snapshot.tool_versions:
            steps.append("uv venv")
        else:
            steps.append(f"python -m venv .venv")
        
        # 3. Install packages
        if snapshot.lock_files:
            if "uv.lock" in snapshot.lock_files:
                steps.append("uv sync")
            elif "requirements.txt" in snapshot.lock_files:
                steps.append("pip install -r requirements.txt")
            elif "package-lock.json" in snapshot.lock_files:
                steps.append("npm ci")
        
        # 4. Verify tool versions
        for tool, version in snapshot.tool_versions.items():
            if tool in self.version_critical_tools:
                steps.append(f"Verify {tool} version {version}")
        
        # 5. Platform-specific notes
        platform_notes = []
        if snapshot.platform == "darwin":
            platform_notes.append("macOS: Use Homebrew for system packages")
            platform_notes.append("Install Xcode Command Line Tools if needed")
        elif snapshot.platform == "linux":
            platform_notes.append("Linux: Use system package manager (apt/yum/etc)")
            platform_notes.append("Install build-essential if needed")
        elif snapshot.platform == "windows":
            platform_notes.append("Windows: Use chocolatey or winget")
            platform_notes.append("Install Visual Studio Build Tools if needed")
        
        snapshot.reproduction_steps = steps
        snapshot.platform_notes = platform_notes
    
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
        current_platform = platform.system().lower()
        
        if current_platform != snapshot.platform:
            result.warnings.append(
                f"Platform mismatch: snapshot from {snapshot.platform}, "
                f"reproducing on {current_platform}"
            )
            
            # Check if platforms are compatible
            compatible_platforms = {
                "darwin": ["darwin"],  # macOS is quite specific
                "linux": ["linux"],    # Linux distros are generally compatible
                "windows": ["windows"] # Windows versions are generally compatible
            }
            
            if current_platform not in compatible_platforms.get(snapshot.platform, []):
                result.warnings.append(
                    "Cross-platform reproduction may require tool substitutions"
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
                        current_version = self._extract_version_from_output(
                            proc_result.stdout + proc_result.stderr
                        )
                        
                        if current_version:
                            # Check version compatibility
                            versions_match = self._compare_versions(
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
        version_commands = {
            "git": ["git", "--version"],
            "uv": ["uv", "--version"],
            "python": ["python", "--version"],
            "pip": ["pip", "--version"],
            "node": ["node", "--version"],
            "npm": ["npm", "--version"],
            "black": ["black", "--version"],
            "ruff": ["ruff", "--version"],
            "mypy": ["mypy", "--version"],
            "pytest": ["pytest", "--version"],
            "docker": ["docker", "--version"],
            "make": ["make", "--version"],
            "gcc": ["gcc", "--version"],
            "clang": ["clang", "--version"],
        }
        
        return version_commands.get(tool)
    
    def _compare_versions(
        self, 
        expected: str, 
        actual: str, 
        tool: str, 
        strict_mode: bool
    ) -> bool:
        """Compare versions with appropriate tolerance."""
        if expected == actual:
            return True
        
        # For critical tools, require exact match in strict mode
        if strict_mode and tool in self.version_critical_tools:
            return False
        
        # For behavior-compatible tools, allow different versions
        if tool in self.behavior_compatible_tools:
            return True
        
        # For other tools, check semantic compatibility
        try:
            expected_parts = [int(x) for x in expected.split(".")]
            actual_parts = [int(x) for x in actual.split(".")]
            
            # Same major version is usually compatible
            if len(expected_parts) >= 1 and len(actual_parts) >= 1:
                return expected_parts[0] == actual_parts[0]
                
        except ValueError:
            # Non-numeric versions, fall back to string comparison
            pass
        
        return not strict_mode
    
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
                from DHT.modules.uv_prefect_tasks import ensure_python_version
                
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
        
        installation_commands = {
            "darwin": {
                "git": "brew install git",
                "node": "brew install node",
                "uv": "curl -LsSf https://astral.sh/uv/install.sh | sh",
                "docker": "brew install --cask docker",
            },
            "linux": {
                "git": "apt-get install git",  # Ubuntu/Debian
                "node": "apt-get install nodejs npm",
                "uv": "curl -LsSf https://astral.sh/uv/install.sh | sh",
                "docker": "apt-get install docker.io",
            },
            "windows": {
                "git": "choco install git",
                "node": "choco install nodejs",
                "uv": "powershell -c \"irm https://astral.sh/uv/install.ps1 | iex\"",
                "docker": "choco install docker-desktop",
            }
        }
        
        current_platform = platform.system().lower()
        platform_commands = installation_commands.get(current_platform, {})
        install_cmd = platform_commands.get(tool)
        
        if install_cmd:
            result.warnings.append(
                f"Manual installation suggested for {tool}: {install_cmd}"
            )
        else:
            result.warnings.append(
                f"No automatic installation available for {tool} on {current_platform}"
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
                self._install_project_dependencies(snapshot, result, target_path)
                
        except Exception as e:
            logger.error(f"Failed to reproduce project environment: {e}")
            result.actions_failed.append(f"project_reproduction_error: {str(e)}")
    
    def _install_project_dependencies(
        self,
        snapshot: EnvironmentSnapshot,
        result: ReproductionResult,
        target_path: Path
    ):
        """Install project dependencies."""
        logger = self._get_logger()
        
        try:
            if "uv.lock" in snapshot.lock_files:
                # Use UV sync
                cmd_result = run_with_guardian(
                    ["uv", "sync"],
                    limits=ResourceLimits(memory_mb=2048, timeout=600),
                    cwd=str(target_path)
                )
                
                if cmd_result.success:
                    result.actions_completed.append("Installed dependencies via UV sync")
                else:
                    result.actions_failed.append(f"UV sync failed: {cmd_result.stderr}")
                    
            elif "requirements.txt" in snapshot.lock_files:
                # Use pip install
                cmd_result = run_with_guardian(
                    ["pip", "install", "-r", "requirements.txt"],
                    limits=ResourceLimits(memory_mb=2048, timeout=600),
                    cwd=str(target_path)
                )
                
                if cmd_result.success:
                    result.actions_completed.append("Installed dependencies via pip")
                else:
                    result.actions_failed.append(f"Pip install failed: {cmd_result.stderr}")
                    
            elif "package-lock.json" in snapshot.lock_files:
                # Use npm ci
                cmd_result = run_with_guardian(
                    ["npm", "ci"],
                    limits=ResourceLimits(memory_mb=2048, timeout=600),
                    cwd=str(target_path)
                )
                
                if cmd_result.success:
                    result.actions_completed.append("Installed dependencies via npm ci")
                else:
                    result.actions_failed.append(f"npm ci failed: {cmd_result.stderr}")
                    
        except Exception as e:
            logger.error(f"Failed to install dependencies: {e}")
            result.actions_failed.append(f"dependency_installation_error: {str(e)}")
    
    def _verify_configurations(
        self,
        snapshot: EnvironmentSnapshot,
        result: ReproductionResult,
        target_path: Path
    ):
        """Verify configuration files match the snapshot."""
        for filename, expected_content in snapshot.config_files.items():
            config_path = target_path / filename
            
            if not config_path.exists():
                result.config_differences[filename] = "File missing"
                continue
            
            try:
                actual_content = config_path.read_text(encoding='utf-8')
                
                if actual_content == expected_content:
                    result.configs_verified[filename] = True
                else:
                    result.configs_verified[filename] = False
                    # Generate a simple diff description
                    result.config_differences[filename] = "Content differs"
                    
            except Exception as e:
                result.configs_verified[filename] = False
                result.config_differences[filename] = f"Read error: {e}"
    
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
        """
        Save environment snapshot to file.
        
        Args:
            snapshot: Environment snapshot to save
            output_path: Path to save the snapshot
            format: Output format ('json' or 'yaml')
            
        Returns:
            Path to saved snapshot file
        """
        logger = self._get_logger()
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert snapshot to dictionary
        snapshot_dict = {
            "metadata": {
                "timestamp": snapshot.timestamp,
                "platform": snapshot.platform,
                "architecture": snapshot.architecture,
                "dht_version": snapshot.dht_version,
                "snapshot_id": snapshot.snapshot_id
            },
            "environment": {
                "python_version": snapshot.python_version,
                "python_executable": snapshot.python_executable,
                "python_packages": snapshot.python_packages,
                "system_packages": snapshot.system_packages,
                "tool_versions": snapshot.tool_versions,
                "tool_paths": snapshot.tool_paths,
                "environment_variables": snapshot.environment_variables,
                "path_entries": snapshot.path_entries
            },
            "project": {
                "project_path": snapshot.project_path,
                "project_type": snapshot.project_type,
                "lock_files": snapshot.lock_files,
                "config_files": snapshot.config_files,
                "checksums": snapshot.checksums
            },
            "reproduction": {
                "steps": snapshot.reproduction_steps,
                "platform_notes": snapshot.platform_notes
            }
        }
        
        # Save in requested format
        if format.lower() == "yaml":
            import yaml
            with open(output_path, 'w') as f:
                yaml.dump(snapshot_dict, f, default_flow_style=False, sort_keys=False)
        else:
            with open(output_path, 'w') as f:
                json.dump(snapshot_dict, f, indent=2, sort_keys=True)
        
        logger.info(f"Environment snapshot saved to {output_path}")
        return output_path
    
    @task(
        name="load_environment_snapshot",
        description="Load environment snapshot from file"
    )
    def load_environment_snapshot(self, snapshot_path: Path) -> EnvironmentSnapshot:
        """
        Load environment snapshot from file.
        
        Args:
            snapshot_path: Path to snapshot file
            
        Returns:
            EnvironmentSnapshot object
        """
        snapshot_path = Path(snapshot_path)
        
        if not snapshot_path.exists():
            raise FileNotFoundError(f"Snapshot file not found: {snapshot_path}")
        
        # Determine format by extension
        if snapshot_path.suffix.lower() in ['.yaml', '.yml']:
            import yaml
            with open(snapshot_path) as f:
                data = yaml.safe_load(f)
        else:
            with open(snapshot_path) as f:
                data = json.load(f)
        
        # Reconstruct snapshot object
        metadata = data["metadata"]
        environment = data["environment"]
        project = data["project"]
        reproduction = data["reproduction"]
        
        snapshot = EnvironmentSnapshot(
            timestamp=metadata["timestamp"],
            platform=metadata["platform"],
            architecture=metadata["architecture"],
            dht_version=metadata["dht_version"],
            snapshot_id=metadata["snapshot_id"],
            python_version=environment["python_version"],
            python_executable=environment["python_executable"],
            python_packages=environment["python_packages"],
            system_packages=environment["system_packages"],
            tool_versions=environment["tool_versions"],
            tool_paths=environment["tool_paths"],
            environment_variables=environment["environment_variables"],
            path_entries=environment["path_entries"],
            project_path=project["project_path"],
            project_type=project["project_type"],
            lock_files=project["lock_files"],
            config_files=project["config_files"],
            checksums=project["checksums"],
            reproduction_steps=reproduction["steps"],
            platform_notes=reproduction["platform_notes"]
        )
        
        return snapshot
    
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
            self._create_reproduction_artifacts(snapshot, results, output_dir)
            results["steps"].append("create_artifacts")
            
            results["success"] = True
            
        except Exception as e:
            logger.error(f"Reproducible environment creation failed: {e}")
            results["success"] = False
            results["error"] = str(e)
        
        results["execution_time"] = time.time() - start_time
        
        logger.info(f"Reproducible environment creation {'completed' if results['success'] else 'failed'}")
        return results
    
    def _create_reproduction_artifacts(
        self,
        snapshot: EnvironmentSnapshot,
        results: Dict[str, Any],
        output_dir: Path
    ):
        """Create Prefect artifacts with reproduction information."""
        
        # Create reproduction guide markdown
        guide = f"""# Environment Reproduction Guide

**Snapshot ID**: {snapshot.snapshot_id}
**Platform**: {snapshot.platform} ({snapshot.architecture})
**Python Version**: {snapshot.python_version}
**Timestamp**: {snapshot.timestamp}

## Quick Reproduction

### Prerequisites
"""
        
        for tool, version in snapshot.tool_versions.items():
            if tool in self.version_critical_tools:
                guide += f"- {tool} {version}\n"
        
        guide += "\n### Reproduction Steps\n"
        for i, step in enumerate(snapshot.reproduction_steps, 1):
            guide += f"{i}. {step}\n"
        
        if snapshot.platform_notes:
            guide += "\n### Platform-Specific Notes\n"
            for note in snapshot.platform_notes:
                guide += f"- {note}\n"
        
        # Add verification results if available
        if "verification" in results:
            verification = results["verification"]
            guide += f"\n## Verification Results\n"
            guide += f"**Status**: {'✅ Passed' if verification['success'] else '❌ Failed'}\n\n"
            
            if verification["version_mismatches"]:
                guide += "### Version Mismatches\n"
                for tool, (expected, actual) in verification["version_mismatches"].items():
                    guide += f"- {tool}: expected {expected}, found {actual}\n"
            
            if verification["missing_tools"]:
                guide += "### Missing Tools\n"
                for tool in verification["missing_tools"]:
                    guide += f"- {tool}\n"
            
            if verification["warnings"]:
                guide += "### Warnings\n"
                for warning in verification["warnings"]:
                    guide += f"- {warning}\n"
        
        # Create markdown artifact
        create_markdown_artifact(
            key=f"reproduction-guide-{snapshot.snapshot_id}",
            markdown=guide,
            description=f"Environment reproduction guide for {snapshot.snapshot_id}"
        )
        
        # Create tool versions table
        tool_data = []
        for tool, version in snapshot.tool_versions.items():
            path = snapshot.tool_paths.get(tool, "")
            critical = "Yes" if tool in self.version_critical_tools else "No"
            tool_data.append({
                "Tool": tool,
                "Version": version,
                "Path": path,
                "Critical": critical
            })
        
        create_table_artifact(
            key=f"tool-versions-{snapshot.snapshot_id}",
            table=tool_data,
            description=f"Tool versions for snapshot {snapshot.snapshot_id}"
        )
        
        # Save reproduction guide to file
        guide_file = output_dir / f"{snapshot.snapshot_id}_reproduction_guide.md"
        guide_file.write_text(guide, encoding='utf-8')


# Export public API
__all__ = [
    "EnvironmentReproducer",
    "EnvironmentSnapshot",
    "ReproductionResult"
]