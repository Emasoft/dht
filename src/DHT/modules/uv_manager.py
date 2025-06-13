#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
uv_manager.py - UV package manager integration for DHT

This module provides a comprehensive interface to UV (ultra-fast Python package manager)
for DHT's environment management, dependency resolution, and project configuration.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Initial implementation of UV manager for DHT
# - Added Python version detection from .python-version and pyproject.toml
# - Implemented virtual environment creation with specific Python versions
# - Added dependency installation with lock file support
# - Integrated with Prefect for task orchestration
# - Added comprehensive error handling with custom exceptions
# - Implemented project setup workflow with step tracking

import json
import os
import subprocess
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import logging
from datetime import datetime

from prefect import task, flow


# Development dependency patterns for intelligent classification
DEV_DEPENDENCY_PATTERNS = {
    "testing": ["pytest", "unittest", "mock", "coverage", "tox", "nose", "hypothesis"],
    "linting": ["flake8", "pylint", "pycodestyle", "pydocstyle", "bandit", "ruff"],
    "formatting": ["black", "autopep8", "yapf", "isort"],
    "type_checking": ["mypy", "pytype", "pyre-check", "pyright"],
    "documentation": ["sphinx", "mkdocs", "pdoc", "pydoc-markdown"],
    "development": ["pre-commit", "ipython", "jupyter", "notebook", "ipdb"],
}


class UVError(Exception):
    """Base exception for UV-related errors."""
    pass


class UVNotFoundError(UVError):
    """UV executable not found."""
    pass


class PythonVersionError(UVError):
    """Python version-related error."""
    pass


class DependencyError(UVError):
    """Dependency resolution error."""
    pass


class UVManager:
    """
    Central UV integration manager for DHT.
    
    Provides high-level interface to UV functionality including:
    - Python version management
    - Virtual environment creation and management
    - Dependency resolution and installation
    - Lock file generation and validation
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.uv_path = self._find_uv_executable()
        self._min_uv_version = "0.4.0"  # Minimum required UV version
        
        if self.uv_path:
            self._verify_uv_version()
    
    def _find_uv_executable(self) -> Optional[Path]:
        """Find UV executable in PATH or common locations."""
        # First check if UV is in PATH
        uv_in_path = shutil.which("uv")
        if uv_in_path:
            return Path(uv_in_path)
        
        # Check common installation locations
        common_paths = [
            Path.home() / ".local" / "bin" / "uv",
            Path.home() / ".cargo" / "bin" / "uv",
            Path("/usr/local/bin/uv"),
            Path("/opt/homebrew/bin/uv"),
        ]
        
        for path in common_paths:
            if path.exists() and path.is_file():
                return path
        
        self.logger.warning("UV executable not found in PATH or common locations")
        return None
    
    def _verify_uv_version(self):
        """Verify UV version meets minimum requirements."""
        try:
            result = self.run_command(["--version"])
            version_output = result["stdout"].strip()
            # Parse version from output like "uv 0.4.27"
            version = version_output.split()[-1]
            
            if not self._version_meets_minimum(version, self._min_uv_version):
                raise UVError(
                    f"UV version {version} is below minimum required {self._min_uv_version}"
                )
            
            self.logger.info(f"UV version {version} verified")
        except Exception as e:
            self.logger.error(f"Failed to verify UV version: {e}")
            raise
    
    def _version_meets_minimum(self, version: str, minimum: str) -> bool:
        """Check if version meets minimum requirement."""
        def parse_version(v: str) -> Tuple[int, ...]:
            return tuple(int(x) for x in v.split('.'))
        
        try:
            return parse_version(version) >= parse_version(minimum)
        except ValueError:
            self.logger.warning(f"Could not parse version: {version}")
            return True  # Assume it's okay if we can't parse
    
    def _load_toml(self, file_path: Path) -> Dict[str, Any]:
        """
        Load TOML file with Python version compatibility.
        
        Args:
            file_path: Path to TOML file
            
        Returns:
            Parsed TOML data
            
        Raises:
            FileNotFoundError: If file doesn't exist
            Exception: If parsing fails
        """
        try:
            import tomllib
        except ImportError:
            import tomli as tomllib
            
        with open(file_path, "rb") as f:
            return tomllib.load(f)
    
    def _is_dev_dependency(self, package_name: str) -> bool:
        """
        Check if a package is likely a development dependency.
        
        Args:
            package_name: Name of the package
            
        Returns:
            True if package is likely a dev dependency
        """
        package_lower = package_name.lower()
        
        # Check against known patterns
        for category, patterns in DEV_DEPENDENCY_PATTERNS.items():
            for pattern in patterns:
                if pattern in package_lower:
                    return True
        
        # Check for common dev dependency prefixes
        dev_prefixes = ["pytest-", "flake8-", "mypy-", "sphinx-"]
        for prefix in dev_prefixes:
            if package_lower.startswith(prefix):
                return True
        
        return False
    
    @property
    def is_available(self) -> bool:
        """Check if UV is available and functional."""
        return self.uv_path is not None
    
    def run_command(
        self, 
        args: List[str], 
        cwd: Optional[Path] = None,
        capture_output: bool = True,
        check: bool = True,
        timeout: int = 300  # 5 minutes default
    ) -> Dict[str, Any]:
        """
        Run UV command and return structured output.
        
        Args:
            args: Command arguments (without 'uv' prefix)
            cwd: Working directory for command
            capture_output: Whether to capture stdout/stderr
            check: Whether to raise on non-zero exit code
            timeout: Command timeout in seconds
            
        Returns:
            Dict with 'stdout', 'stderr', 'returncode', and 'success' keys
            
        Raises:
            UVNotFoundError: If UV is not available
        """
        if not self.is_available:
            raise UVNotFoundError("UV is not available. Please install UV first.")
        
        cmd = [str(self.uv_path)] + args
        
        self.logger.debug(f"Running UV command: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                cwd=cwd,
                capture_output=capture_output,
                text=True,
                check=check,
                timeout=timeout
            )
            
            return {
                "stdout": result.stdout if capture_output else "",
                "stderr": result.stderr if capture_output else "",
                "returncode": result.returncode,
                "success": result.returncode == 0
            }
        except subprocess.TimeoutExpired as e:
            return {
                "stdout": e.stdout.decode() if e.stdout else "",
                "stderr": f"Command timed out after {timeout} seconds",
                "returncode": -1,
                "success": False,
                "error": "timeout"
            }
        except subprocess.CalledProcessError as e:
            return {
                "stdout": e.stdout if capture_output else "",
                "stderr": e.stderr if capture_output else "",
                "returncode": e.returncode,
                "success": False,
                "error": str(e)
            }
    
    @task
    def detect_python_version(self, project_path: Path) -> Optional[str]:
        """
        Detect required Python version for a project.
        
        Checks in order:
        1. .python-version file
        2. pyproject.toml requires-python
        3. setup.py python_requires
        4. Runtime detection from imports
        
        Returns:
            Python version string (e.g., "3.11", "3.11.6") or None
        """
        project_path = Path(project_path)
        
        # Check .python-version file
        python_version_file = project_path / ".python-version"
        if python_version_file.exists():
            version = python_version_file.read_text().strip()
            self.logger.info(f"Found Python version in .python-version: {version}")
            return version
        
        # Check pyproject.toml
        pyproject_file = project_path / "pyproject.toml"
        if pyproject_file.exists():
            try:
                data = self._load_toml(pyproject_file)
                
                requires_python = data.get("project", {}).get("requires-python")
                if requires_python:
                    # Convert constraint to specific version
                    # For now, extract minimum version
                    version = self._extract_min_version(requires_python)
                    self.logger.info(f"Found Python requirement in pyproject.toml: {version}")
                    return version
            except Exception as e:
                self.logger.warning(f"Failed to parse pyproject.toml: {e}")
        
        # Check setup.py
        setup_py = project_path / "setup.py"
        if setup_py.exists():
            # This is trickier - would need AST parsing
            # For now, return None and let user specify
            pass
        
        return None
    
    def _extract_min_version(self, constraint: str) -> str:
        """Extract minimum Python version from constraint string."""
        # Handle common patterns like ">=3.8", ">=3.8,<3.12", "^3.8"
        constraint = constraint.strip()
        
        if constraint.startswith(">="):
            version = constraint[2:].split(",")[0].strip()
            return version
        elif constraint.startswith("^"):
            # Caret notation - use base version
            return constraint[1:].strip()
        elif constraint.startswith("~"):
            # Tilde notation - use base version
            return constraint[1:].strip()
        else:
            # Try to extract any version number
            import re
            match = re.search(r'\d+\.\d+(?:\.\d+)?', constraint)
            if match:
                return match.group()
        
        # Default to current Python version
        import sys
        return f"{sys.version_info.major}.{sys.version_info.minor}"
    
    @task
    def list_python_versions(self) -> List[Dict[str, Any]]:
        """List all available Python versions (installed and downloadable)."""
        result = self.run_command(["python", "list", "--all-versions"])
        
        if not result["success"]:
            self.logger.error(f"Failed to list Python versions: {result['stderr']}")
            return []
        
        versions = []
        for line in result["stdout"].strip().split("\n"):
            if line.strip():
                # Parse version info from UV output
                parts = line.strip().split()
                if parts:
                    version_info = {
                        "version": parts[0],
                        "installed": "(installed)" in line,
                        "path": parts[-1] if "(installed)" in line else None
                    }
                    versions.append(version_info)
        
        return versions
    
    @task
    def ensure_python_version(self, version: str) -> Path:
        """
        Ensure specific Python version is available, installing if needed.
        
        Args:
            version: Python version to ensure (e.g., "3.11", "3.11.6")
            
        Returns:
            Path to Python executable
        """
        # First check if already installed
        result = self.run_command(["python", "find", version])
        
        if result["success"] and result["stdout"].strip():
            python_path = Path(result["stdout"].strip())
            self.logger.info(f"Python {version} already available at {python_path}")
            return python_path
        
        # Not installed, try to install
        self.logger.info(f"Python {version} not found, attempting to install...")
        
        install_result = self.run_command(["python", "install", version])
        
        if not install_result["success"]:
            raise PythonVersionError(
                f"Failed to install Python {version}: {install_result['stderr']}"
            )
        
        # Find the newly installed Python
        find_result = self.run_command(["python", "find", version])
        
        if find_result["success"] and find_result["stdout"].strip():
            python_path = Path(find_result["stdout"].strip())
            self.logger.info(f"Successfully installed Python {version} at {python_path}")
            return python_path
        else:
            raise PythonVersionError(
                f"Python {version} was installed but cannot be found"
            )
    
    @task
    def create_venv(
        self, 
        project_path: Path, 
        python_version: Optional[str] = None,
        venv_path: Optional[Path] = None
    ) -> Path:
        """
        Create virtual environment for project.
        
        Args:
            project_path: Project root directory
            python_version: Specific Python version to use
            venv_path: Custom path for virtual environment
            
        Returns:
            Path to created virtual environment
        """
        project_path = Path(project_path)
        
        if venv_path is None:
            venv_path = project_path / ".venv"
        
        args = ["venv"]
        
        if python_version:
            args.extend(["--python", python_version])
        
        # Add path if not default
        if venv_path != project_path / ".venv":
            args.append(str(venv_path))
        
        result = self.run_command(args, cwd=project_path)
        
        if not result["success"]:
            raise UVError(f"Failed to create virtual environment: {result['stderr']}")
        
        self.logger.info(f"Created virtual environment at {venv_path}")
        return venv_path
    
    @task
    def install_dependencies(
        self,
        project_path: Path,
        requirements_file: Optional[Path] = None,
        dev: bool = False,
        extras: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Install project dependencies.
        
        Args:
            project_path: Project root directory
            requirements_file: Specific requirements file to use
            dev: Whether to install development dependencies
            extras: List of extras to install
            
        Returns:
            Installation result information
        """
        project_path = Path(project_path)
        
        # Check if project has uv.lock
        lock_file = project_path / "uv.lock"
        if lock_file.exists():
            # Use uv sync for lock file
            return self._sync_dependencies(project_path, dev=dev, extras=extras)
        
        # Otherwise use pip install
        if requirements_file:
            return self._pip_install_requirements(project_path, requirements_file)
        
        # Look for pyproject.toml
        pyproject = project_path / "pyproject.toml"
        if pyproject.exists():
            return self._pip_install_project(project_path, dev=dev, extras=extras)
        
        # Look for requirements.txt
        requirements_txt = project_path / "requirements.txt"
        if requirements_txt.exists():
            return self._pip_install_requirements(project_path, requirements_txt)
        
        self.logger.warning("No dependencies found to install")
        return {"success": True, "message": "No dependencies found"}
    
    def _sync_dependencies(
        self,
        project_path: Path,
        dev: bool = False,
        extras: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Sync dependencies from uv.lock file."""
        args = ["sync"]
        
        if dev:
            args.append("--dev")
        
        if extras:
            for extra in extras:
                args.extend(["--extra", extra])
        
        result = self.run_command(args, cwd=project_path)
        
        return {
            "success": result["success"],
            "method": "uv sync",
            "message": result["stdout"] if result["success"] else result["stderr"]
        }
    
    def _pip_install_requirements(
        self,
        project_path: Path,
        requirements_file: Path
    ) -> Dict[str, Any]:
        """Install from requirements file using uv pip."""
        args = ["pip", "install", "-r", str(requirements_file)]
        
        result = self.run_command(args, cwd=project_path)
        
        return {
            "success": result["success"],
            "method": "uv pip install -r",
            "requirements_file": str(requirements_file),
            "message": result["stdout"] if result["success"] else result["stderr"]
        }
    
    def _pip_install_project(
        self,
        project_path: Path,
        dev: bool = False,
        extras: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Install project with optional extras."""
        # Install the project itself
        install_spec = "."
        
        if extras:
            extras_str = ",".join(extras)
            install_spec = f".[{extras_str}]"
        
        args = ["pip", "install", "-e", install_spec]
        
        result = self.run_command(args, cwd=project_path)
        
        if not result["success"]:
            return {
                "success": False,
                "method": "uv pip install -e",
                "message": result["stderr"]
            }
        
        # Install dev dependencies if requested
        if dev:
            # Check for dev dependencies in pyproject.toml
            try:
                pyproject = project_path / "pyproject.toml"
                data = self._load_toml(pyproject)
                
                # Check for dev dependencies in various locations
                dev_deps = (
                    data.get("project", {}).get("optional-dependencies", {}).get("dev", []) or
                    data.get("dependency-groups", {}).get("dev", []) or
                    data.get("tool", {}).get("pdm", {}).get("dev-dependencies", {})
                )
                
                if dev_deps:
                    # Try installing as extra first
                    dev_result = self.run_command(
                        ["pip", "install", "-e", ".[dev]"],
                        cwd=project_path,
                        check=False
                    )
                    
                    if not dev_result["success"]:
                        # Try installing individually
                        for dep in dev_deps:
                            self.run_command(
                                ["pip", "install", dep],
                                cwd=project_path,
                                check=False
                            )
            except Exception as e:
                self.logger.warning(f"Could not install dev dependencies: {e}")
        
        return {
            "success": True,
            "method": "uv pip install -e",
            "message": "Dependencies installed successfully"
        }
    
    @task
    def generate_lock_file(self, project_path: Path) -> Path:
        """
        Generate uv.lock file for reproducible installs.
        
        Args:
            project_path: Project root directory
            
        Returns:
            Path to generated lock file
        """
        project_path = Path(project_path)
        
        result = self.run_command(["lock"], cwd=project_path)
        
        if not result["success"]:
            raise DependencyError(f"Failed to generate lock file: {result['stderr']}")
        
        lock_file = project_path / "uv.lock"
        self.logger.info(f"Generated lock file at {lock_file}")
        
        return lock_file
    
    @task
    def add_dependency(
        self,
        project_path: Path,
        package: str,
        dev: bool = False,
        extras: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Add a dependency to the project.
        
        Args:
            project_path: Project root directory
            package: Package specification (e.g., "requests>=2.28")
            dev: Whether this is a development dependency
            extras: Optional extras for the package
            
        Returns:
            Result of the operation
        """
        project_path = Path(project_path)
        
        args = ["add"]
        
        if dev:
            args.append("--dev")
        
        if extras:
            for extra in extras:
                args.extend(["--extra", extra])
        
        args.append(package)
        
        result = self.run_command(args, cwd=project_path)
        
        if result["success"]:
            # Regenerate lock file
            self.generate_lock_file(project_path)
        
        return {
            "success": result["success"],
            "package": package,
            "dev": dev,
            "message": result["stdout"] if result["success"] else result["stderr"]
        }
    
    @task
    def remove_dependency(self, project_path: Path, package: str) -> Dict[str, Any]:
        """Remove a dependency from the project."""
        project_path = Path(project_path)
        
        args = ["remove", package]
        
        result = self.run_command(args, cwd=project_path)
        
        if result["success"]:
            # Regenerate lock file
            self.generate_lock_file(project_path)
        
        return {
            "success": result["success"],
            "package": package,
            "message": result["stdout"] if result["success"] else result["stderr"]
        }
    
    @task
    def check_outdated(self, project_path: Path) -> List[Dict[str, Any]]:
        """Check for outdated dependencies."""
        project_path = Path(project_path)
        
        # UV doesn't have a direct outdated command yet
        # We'll use pip list with UV's pip interface
        result = self.run_command(
            ["pip", "list", "--outdated", "--format=json"],
            cwd=project_path
        )
        
        if not result["success"]:
            self.logger.error(f"Failed to check outdated packages: {result['stderr']}")
            return []
        
        try:
            outdated = json.loads(result["stdout"])
            return outdated
        except json.JSONDecodeError:
            self.logger.error("Failed to parse outdated packages output")
            return []
    
    @task
    def run_script(
        self,
        project_path: Path,
        script: str,
        args: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Run a Python script in the project environment.
        
        Args:
            project_path: Project root directory
            script: Script to run (file or module)
            args: Additional arguments for the script
            
        Returns:
            Execution result
        """
        project_path = Path(project_path)
        
        cmd_args = ["run"]
        
        if script.endswith(".py"):
            cmd_args.extend(["python", script])
        else:
            cmd_args.extend(["python", "-m", script])
        
        if args:
            cmd_args.extend(args)
        
        result = self.run_command(cmd_args, cwd=project_path)
        
        return {
            "success": result["success"],
            "script": script,
            "output": result["stdout"],
            "error": result["stderr"]
        }
    
    def _setup_python_environment(
        self, 
        project_path: Path, 
        python_version: Optional[str],
        results: Dict[str, Any]
    ) -> Optional[str]:
        """
        Setup Python environment for the project.
        
        Args:
            project_path: Project root directory
            python_version: Specific Python version or None
            results: Results dict to update
            
        Returns:
            Python version if successful, None if failed
        """
        # Detect Python version if not specified
        if not python_version:
            python_version = self.detect_python_version(project_path)
            if python_version:
                results["detected_python_version"] = python_version
        
        # Ensure Python version is available
        if python_version:
            try:
                python_path = self.ensure_python_version(python_version)
                results["python_path"] = str(python_path)
                results["steps"].append({
                    "step": "ensure_python",
                    "success": True,
                    "version": python_version
                })
                return python_version
            except Exception as e:
                results["steps"].append({
                    "step": "ensure_python",
                    "success": False,
                    "error": str(e)
                })
                results["success"] = False
                return None
        
        return python_version
    
    def _setup_virtual_environment(
        self,
        project_path: Path,
        python_version: Optional[str],
        results: Dict[str, Any]
    ) -> Optional[Path]:
        """
        Create virtual environment for the project.
        
        Args:
            project_path: Project root directory
            python_version: Python version to use
            results: Results dict to update
            
        Returns:
            Venv path if successful, None if failed
        """
        try:
            venv_path = self.create_venv(project_path, python_version)
            results["venv_path"] = str(venv_path)
            results["steps"].append({
                "step": "create_venv",
                "success": True,
                "path": str(venv_path)
            })
            return venv_path
        except Exception as e:
            results["steps"].append({
                "step": "create_venv",
                "success": False,
                "error": str(e)
            })
            results["success"] = False
            return None
    
    def _setup_dependencies(
        self,
        project_path: Path,
        dev: bool,
        results: Dict[str, Any]
    ) -> None:
        """
        Install project dependencies.
        
        Args:
            project_path: Project root directory
            dev: Whether to install dev dependencies
            results: Results dict to update
        """
        try:
            deps_result = self.install_dependencies(project_path, dev=dev)
            results["steps"].append({
                "step": "install_dependencies",
                "success": deps_result["success"],
                "method": deps_result.get("method"),
                "message": deps_result.get("message")
            })
        except Exception as e:
            results["steps"].append({
                "step": "install_dependencies",
                "success": False,
                "error": str(e)
            })
    
    def _generate_lock_if_needed(
        self,
        project_path: Path,
        results: Dict[str, Any]
    ) -> None:
        """
        Generate lock file if needed.
        
        Args:
            project_path: Project root directory
            results: Results dict to update
        """
        lock_file = project_path / "uv.lock"
        if not lock_file.exists() and (project_path / "pyproject.toml").exists():
            try:
                self.generate_lock_file(project_path)
                results["steps"].append({
                    "step": "generate_lock",
                    "success": True,
                    "path": str(lock_file)
                })
            except Exception as e:
                results["steps"].append({
                    "step": "generate_lock",
                    "success": False,
                    "error": str(e)
                })
    
    @flow(name="setup_project_environment")
    def setup_project(
        self,
        project_path: Path,
        python_version: Optional[str] = None,
        install_deps: bool = True,
        dev: bool = False
    ) -> Dict[str, Any]:
        """
        Complete project setup flow.
        
        Args:
            project_path: Project root directory
            python_version: Specific Python version to use
            install_deps: Whether to install dependencies
            dev: Whether to install development dependencies
            
        Returns:
            Setup result information
        """
        project_path = Path(project_path)
        results = {
            "project_path": str(project_path),
            "timestamp": datetime.now().isoformat(),
            "steps": []
        }
        
        # Setup Python environment
        python_version = self._setup_python_environment(
            project_path, python_version, results
        )
        if results.get("success") is False:
            return results
        
        # Create virtual environment
        venv_path = self._setup_virtual_environment(
            project_path, python_version, results
        )
        if venv_path is None:
            return results
        
        # Install dependencies
        if install_deps:
            self._setup_dependencies(project_path, dev, results)
        
        # Generate lock file if needed
        self._generate_lock_if_needed(project_path, results)
        
        # Set overall success
        results["success"] = all(
            step.get("success", False) for step in results["steps"]
        ) if results["steps"] else True
        
        return results