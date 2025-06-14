#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
environment_installer.py - Environment installation and setup

This module handles Python environment installation and package management.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Extracted from environment_configurator.py to reduce file size
# - Contains environment installation and package management functions
#

from __future__ import annotations

import os
import sys
import subprocess
import logging as std_logging
from pathlib import Path
from typing import List, Optional

from prefect import task, get_run_logger

from DHT.modules.environment_config_models import EnvironmentConfig, ConfigurationResult
from DHT.modules.uv_prefect_tasks import (
    check_uv_available,
    ensure_python_version,
    create_virtual_environment,
    install_dependencies,
    add_dependency
)


def _get_logger():
    """Get logger, falling back to standard logging if not in Prefect context."""
    try:
        return get_run_logger()
    except Exception:
        return std_logging.getLogger(__name__)


class EnvironmentInstaller:
    """Handles environment installation and setup."""
    
    @task(
        name="install_python_environment",
        description="Install Python environment based on configuration"
    )
    def install_python_environment(
        self, 
        config: EnvironmentConfig, 
        result: ConfigurationResult
    ) -> bool:
        """
        Install Python environment based on configuration.
        
        Args:
            config: Environment configuration
            result: Configuration result to update
            
        Returns:
            True if installation succeeded
        """
        logger = _get_logger()
        
        try:
            # Check UV availability
            uv_check = check_uv_available()
            if not uv_check["available"]:
                result.warnings.append("UV not available, using system pip")
                return self._install_with_pip(config, result)
            
            # Ensure Python version
            if config.python_version:
                try:
                    python_path = ensure_python_version(config.python_version)
                    logger.info(f"Python {config.python_version} available at {python_path}")
                except Exception as e:
                    result.warnings.append(f"Failed to ensure Python version: {e}")
            
            # Create virtual environment
            venv_path = create_virtual_environment(
                project_path=config.project_path,
                python_version=config.python_version
            )
            logger.info(f"Created virtual environment at {venv_path}")
            result.steps_completed.append("create_virtual_environment")
            
            # Install dependencies
            deps_result = install_dependencies(
                project_path=config.project_path,
                dev=True
            )
            
            if not deps_result["success"]:
                result.warnings.append(f"Dependency installation issues: {deps_result.get('message')}")
            else:
                result.steps_completed.append("install_dependencies")
            
            # Install additional development packages
            if config.dev_packages:
                self._install_additional_packages(config.project_path, config.dev_packages)
                result.steps_completed.append("install_dev_packages")
            
            # Install quality tools
            if config.quality_tools:
                self._install_quality_tools(config.project_path, config.quality_tools)
                result.steps_completed.append("install_quality_tools")
            
            return True
            
        except Exception as e:
            logger.error(f"Python environment installation failed: {e}")
            result.warnings.append(str(e))
            result.steps_failed.append("install_python_environment")
            return False
    
    def _install_with_pip(
        self, 
        config: EnvironmentConfig, 
        result: ConfigurationResult
    ) -> bool:
        """Fallback installation using system pip."""
        try:
            logger = _get_logger()
        except Exception:
            # Not in a Prefect context, use standard logging
            import logging
            logger = logging.getLogger(__name__)
        
        try:
            # Create virtual environment with venv
            venv_path = config.project_path / ".venv"
            
            subprocess.run([
                sys.executable, "-m", "venv", str(venv_path)
            ], check=True)
            
            # Determine pip path
            if os.name == 'nt':  # Windows
                pip_path = venv_path / "Scripts" / "pip.exe"
            else:
                pip_path = venv_path / "bin" / "pip"
            
            # Upgrade pip
            subprocess.run([
                str(pip_path), "install", "--upgrade", "pip"
            ], check=True)
            
            # Install packages
            all_packages = config.python_packages + config.dev_packages
            if all_packages:
                subprocess.run([
                    str(pip_path), "install"
                ] + all_packages, check=True)
            
            logger.info(f"Installed Python environment with pip at {venv_path}")
            result.steps_completed.append("create_virtual_environment_pip")
            return True
            
        except Exception as e:
            logger.error(f"Pip installation failed: {e}")
            result.steps_failed.append("install_with_pip")
            return False
    
    def _install_additional_packages(self, project_path: Path, packages: List[str]) -> None:
        """Install additional packages in the project environment."""
        if not packages:
            return
        
        logger = _get_logger()
        
        try:
            # Use UV to install packages
            for package in packages:
                try:
                    add_dependency(
                        project_path=project_path,
                        package=package,
                        dev=True
                    )
                    logger.info(f"Installed {package}")
                except Exception as e:
                    logger.warning(f"Failed to install {package}: {e}")
                    
        except Exception as e:
            logger.warning(f"Additional package installation failed: {e}")
    
    def _install_quality_tools(self, project_path: Path, tools: List[str]) -> None:
        """Install quality tools as development dependencies."""
        logger = _get_logger()
        
        # Map tool names to package names
        tool_packages = {
            "black": "black",
            "ruff": "ruff",
            "mypy": "mypy",
            "pytest": "pytest",
            "coverage": "coverage[toml]",
            "pre-commit": "pre-commit",
            "isort": "isort",
            "flake8": "flake8",
            "pylint": "pylint",
            "bandit": "bandit",
            "safety": "safety"
        }
        
        packages_to_install = []
        for tool in tools:
            if tool in tool_packages:
                packages_to_install.append(tool_packages[tool])
        
        if packages_to_install:
            self._install_additional_packages(project_path, packages_to_install)
    
    @task(
        name="install_system_packages",
        description="Install system-level packages"
    )
    def install_system_packages(
        self,
        config: EnvironmentConfig,
        result: ConfigurationResult,
        platform: str
    ) -> bool:
        """
        Install system-level packages.
        
        Args:
            config: Environment configuration
            result: Configuration result to update
            platform: Current platform (darwin, linux, windows)
            
        Returns:
            True if installation succeeded
        """
        logger = _get_logger()
        
        if not config.system_packages:
            logger.info("No system packages to install")
            return True
        
        # Platform-specific package managers
        package_managers = {
            "darwin": {
                "check": ["brew", "--version"],
                "install": ["brew", "install"]
            },
            "linux": {
                "check": ["apt-get", "--version"],
                "install": ["sudo", "apt-get", "install", "-y"]
            }
        }
        
        if platform not in package_managers:
            logger.warning(f"System package installation not supported on {platform}")
            result.warnings.append(f"System packages not installed: unsupported platform {platform}")
            return True
        
        pm = package_managers[platform]
        
        try:
            # Check if package manager is available
            subprocess.run(pm["check"], capture_output=True, check=True)
        except Exception:
            logger.warning(f"Package manager not available on {platform}")
            result.warnings.append("System package manager not available")
            return True
        
        # Install packages
        failed_packages = []
        for package in config.system_packages:
            try:
                cmd = pm["install"] + [package]
                subprocess.run(cmd, check=True)
                logger.info(f"Installed system package: {package}")
            except Exception as e:
                logger.warning(f"Failed to install {package}: {e}")
                failed_packages.append(package)
        
        if failed_packages:
            result.warnings.append(f"Failed to install system packages: {', '.join(failed_packages)}")
        else:
            result.steps_completed.append("install_system_packages")
        
        return len(failed_packages) == 0
    
    @task(
        name="run_post_install_commands",
        description="Run post-installation commands"
    )
    def run_post_install_commands(
        self,
        config: EnvironmentConfig,
        result: ConfigurationResult
    ) -> bool:
        """
        Run post-installation commands.
        
        Args:
            config: Environment configuration
            result: Configuration result to update
            
        Returns:
            True if all commands succeeded
        """
        logger = _get_logger()
        
        if not config.post_install_commands:
            return True
        
        failed_commands = []
        for command in config.post_install_commands:
            try:
                # Run command in project directory
                subprocess.run(
                    command,
                    shell=True,
                    cwd=config.project_path,
                    check=True
                )
                logger.info(f"Executed post-install command: {command}")
            except Exception as e:
                logger.warning(f"Failed to execute command '{command}': {e}")
                failed_commands.append(command)
        
        if failed_commands:
            result.warnings.append(f"Failed commands: {'; '.join(failed_commands)}")
        else:
            result.steps_completed.append("run_post_install_commands")
        
        return len(failed_commands) == 0