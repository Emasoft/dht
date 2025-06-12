#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Initial implementation of environment configurator module
# - Uses diagnostic info tree for intelligent configuration
# - Supports multiple project types and environments
# - Generates platform-specific configurations
# - Integrates with UV, Python, and system tools
# 

"""
Environment Configurator Module.

This module uses the information tree from diagnostic_reporter_v2 to intelligently
configure development environments based on detected tools, project structure,
and platform capabilities.
"""

from __future__ import annotations

import os
import json
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Union
from dataclasses import dataclass, field
from datetime import datetime

from prefect import task, flow, get_run_logger
from prefect.artifacts import create_markdown_artifact

from DHT.diagnostic_reporter_v2 import build_system_report
from DHT.modules.project_analyzer import ProjectAnalyzer
from DHT.modules.uv_prefect_tasks import (
    check_uv_available,
    detect_python_version,
    ensure_python_version,
    create_virtual_environment,
    install_dependencies,
    generate_lock_file
)
from DHT.modules.guardian_prefect import run_with_guardian, ResourceLimits


@dataclass
class EnvironmentConfig:
    """Configuration for a development environment."""
    project_path: Path
    project_type: str
    python_version: Optional[str] = None
    node_version: Optional[str] = None
    system_packages: List[str] = field(default_factory=list)
    python_packages: List[str] = field(default_factory=list)
    dev_packages: List[str] = field(default_factory=list)
    environment_variables: Dict[str, str] = field(default_factory=dict)
    pre_install_commands: List[str] = field(default_factory=list)
    post_install_commands: List[str] = field(default_factory=list)
    quality_tools: List[str] = field(default_factory=list)
    test_frameworks: List[str] = field(default_factory=list)
    build_tools: List[str] = field(default_factory=list)
    container_config: Optional[Dict[str, Any]] = None
    ci_config: Optional[Dict[str, Any]] = None


@dataclass
class ConfigurationResult:
    """Result of environment configuration."""
    success: bool
    config: EnvironmentConfig
    steps_completed: List[str] = field(default_factory=list)
    steps_failed: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    info_tree: Optional[Dict[str, Any]] = None
    execution_time: float = 0.0


class EnvironmentConfigurator:
    """Intelligent environment configurator using system information tree."""
    
    def __init__(self):
        """Initialize the environment configurator."""
        self.logger = None
        self.analyzer = ProjectAnalyzer()
        
        # Platform-specific package mappings
        self.system_package_mappings = {
            "python-dev": {
                "darwin": [],  # Usually available via Xcode tools
                "linux": ["python3-dev", "python3-distutils"],
                "windows": []  # Usually not needed
            },
            "build-essential": {
                "darwin": [],  # Xcode command line tools
                "linux": ["build-essential", "gcc", "g++", "make"],
                "windows": []  # Visual Studio Build Tools
            },
            "git": {
                "darwin": ["git"],  # via Xcode or Homebrew
                "linux": ["git"],
                "windows": ["git"]  # Git for Windows
            },
            "curl": {
                "darwin": ["curl"],
                "linux": ["curl"],
                "windows": ["curl"]
            },
            "openssl": {
                "darwin": ["openssl"],
                "linux": ["libssl-dev", "openssl"],
                "windows": []
            }
        }
        
        # Tool-specific configurations
        self.tool_configs = {
            "pytest": {
                "packages": ["pytest", "pytest-cov", "pytest-xdist"],
                "config_files": ["pytest.ini", "pyproject.toml"],
                "env_vars": {"PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1"}
            },
            "black": {
                "packages": ["black"],
                "config_files": ["pyproject.toml", ".black"],
                "env_vars": {}
            },
            "ruff": {
                "packages": ["ruff"],
                "config_files": ["ruff.toml", "pyproject.toml"],
                "env_vars": {}
            },
            "mypy": {
                "packages": ["mypy"],
                "config_files": ["mypy.ini", "pyproject.toml"],
                "env_vars": {}
            },
            "pre-commit": {
                "packages": ["pre-commit"],
                "config_files": [".pre-commit-config.yaml"],
                "env_vars": {}
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
        name="analyze_environment_requirements",
        description="Analyze project to determine environment requirements"
    )
    def analyze_environment_requirements(
        self, 
        project_path: Path,
        include_system_info: bool = True
    ) -> Dict[str, Any]:
        """
        Analyze project and system to determine environment requirements.
        
        Args:
            project_path: Path to project root
            include_system_info: Whether to include full system info tree
            
        Returns:
            Analysis results with requirements and recommendations
        """
        logger = self._get_logger()
        project_path = Path(project_path).resolve()
        
        logger.info(f"Analyzing environment requirements for {project_path}")
        
        # Get project analysis
        project_info = self.analyzer.analyze_project(project_path)
        
        # Get system information tree if requested
        info_tree = None
        if include_system_info:
            logger.info("Building system information tree...")
            info_tree = build_system_report()
        
        # Extract key information
        analysis = {
            "project_info": project_info,
            "detected_tools": self._detect_tools_from_project(project_path, project_info),
            "recommended_tools": self._recommend_tools(project_info),
            "system_requirements": self._determine_system_requirements(project_info),
            "python_requirements": self._determine_python_requirements(project_path, project_info),
            "quality_setup": self._recommend_quality_tools(project_info),
            "ci_setup": self._recommend_ci_setup(project_info),
            "info_tree": info_tree
        }
        
        logger.info(f"Analysis complete: {len(analysis['detected_tools'])} tools detected")
        return analysis
    
    def _detect_tools_from_project(
        self, 
        project_path: Path, 
        project_info: Dict[str, Any]
    ) -> List[str]:
        """Detect tools already configured in the project."""
        detected = []
        
        # Check for Python tools in pyproject.toml
        pyproject = project_path / "pyproject.toml"
        if pyproject.exists():
            try:
                import tomllib
            except ImportError:
                import tomli as tomllib
            
            try:
                with open(pyproject, "rb") as f:
                    data = tomllib.load(f)
                
                # Check tool configurations
                tools_section = data.get("tool", {})
                for tool in ["black", "ruff", "mypy", "pytest", "coverage"]:
                    if tool in tools_section:
                        detected.append(tool)
                
                # Check dependencies
                project_deps = data.get("project", {}).get("dependencies", [])
                optional_deps = data.get("project", {}).get("optional-dependencies", {})
                
                for dep_list in [project_deps] + list(optional_deps.values()):
                    for dep in dep_list:
                        dep_name = dep.split("[")[0].split("=")[0].split(">")[0].split("<")[0].strip()
                        if dep_name in self.tool_configs:
                            detected.append(dep_name)
                            
            except Exception as e:
                self._get_logger().warning(f"Failed to parse pyproject.toml: {e}")
        
        # Check for configuration files
        for tool, config in self.tool_configs.items():
            for config_file in config["config_files"]:
                if (project_path / config_file).exists():
                    detected.append(tool)
                    break
        
        return list(set(detected))
    
    def _recommend_tools(self, project_info: Dict[str, Any]) -> List[str]:
        """Recommend tools based on project type and structure."""
        recommended = []
        project_type = project_info.get("project_type", "unknown")
        
        if project_type == "python":
            # Core Python development tools
            recommended.extend(["black", "ruff", "mypy", "pytest"])
            
            # If it's a package/library
            if project_info.get("configurations", {}).get("has_pyproject"):
                recommended.extend(["build", "twine"])
            
            # Quality tools
            recommended.append("pre-commit")
            
        elif project_type == "nodejs":
            recommended.extend(["eslint", "prettier", "jest"])
            
        # Universal tools
        if not project_info.get("configurations", {}).get("has_git"):
            recommended.append("git")
        
        return recommended
    
    def _determine_system_requirements(self, project_info: Dict[str, Any]) -> List[str]:
        """Determine system-level package requirements."""
        requirements = []
        project_type = project_info.get("project_type", "unknown")
        configs = project_info.get("configurations", {})
        
        if project_type == "python":
            requirements.extend(["python-dev", "build-essential"])
            
            # SSL support for pip installs
            requirements.append("openssl")
        
        if configs.get("has_git", False):
            requirements.append("git")
        
        if configs.get("has_dockerfile", False):
            requirements.append("docker")
            
        # Universal tools
        requirements.extend(["curl"])
        
        return requirements
    
    def _determine_python_requirements(
        self, 
        project_path: Path, 
        project_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Determine Python version and package requirements."""
        requirements = {
            "version": None,
            "runtime_packages": [],
            "dev_packages": [],
            "build_packages": []
        }
        
        # Detect Python version
        if project_info.get("project_type") == "python":
            # Try to detect from project files
            version = None
            
            # Check .python-version
            python_version_file = project_path / ".python-version"
            if python_version_file.exists():
                try:
                    version = python_version_file.read_text().strip()
                except Exception:
                    pass
            
            # Check pyproject.toml
            if not version:
                pyproject = project_path / "pyproject.toml"
                if pyproject.exists():
                    try:
                        import tomllib
                    except ImportError:
                        import tomli as tomllib
                    
                    try:
                        with open(pyproject, "rb") as f:
                            data = tomllib.load(f)
                        
                        requires_python = data.get("project", {}).get("requires-python")
                        if requires_python:
                            # Extract minimum version
                            import re
                            match = re.search(r'>=?\s*(\d+\.\d+)', requires_python)
                            if match:
                                version = match.group(1)
                    except Exception:
                        pass
            
            requirements["version"] = version or "3.11"  # Default to 3.11
            
            # Standard development packages
            requirements["dev_packages"] = [
                "pip", "setuptools", "wheel", "build"
            ]
            
            # Build packages for compiled extensions
            requirements["build_packages"] = [
                "Cython", "pybind11"
            ]
        
        return requirements
    
    def _recommend_quality_tools(self, project_info: Dict[str, Any]) -> Dict[str, Any]:
        """Recommend quality and testing tools."""
        quality = {
            "linting": [],
            "formatting": [],
            "testing": [],
            "type_checking": [],
            "pre_commit": False
        }
        
        project_type = project_info.get("project_type", "unknown")
        
        if project_type == "python":
            quality["linting"] = ["ruff", "flake8"]
            quality["formatting"] = ["black", "isort"]
            quality["testing"] = ["pytest", "coverage"]
            quality["type_checking"] = ["mypy"]
            quality["pre_commit"] = True
            
        elif project_type == "nodejs":
            quality["linting"] = ["eslint"]
            quality["formatting"] = ["prettier"]
            quality["testing"] = ["jest", "mocha"]
            quality["type_checking"] = ["typescript"]
            quality["pre_commit"] = True
        
        return quality
    
    def _recommend_ci_setup(self, project_info: Dict[str, Any]) -> Dict[str, Any]:
        """Recommend CI/CD setup based on project structure."""
        ci_config = {
            "recommended": False,
            "platforms": [],
            "workflows": [],
            "matrix_testing": False
        }
        
        # If it's a substantial project, recommend CI
        configs = project_info.get("configurations", {})
        if (
            configs.get("has_git", False) and 
            len(project_info.get("dependencies", {}).get("python", {}).get("all", [])) > 3
        ):
            ci_config["recommended"] = True
            ci_config["platforms"] = ["github-actions"]
            
            project_type = project_info.get("project_type", "unknown")
            if project_type == "python":
                ci_config["workflows"] = ["test", "lint", "build"]
                ci_config["matrix_testing"] = True
        
        return ci_config
    
    @task(
        name="generate_environment_config",
        description="Generate environment configuration from analysis"
    )
    def generate_environment_config(
        self, 
        project_path: Path,
        analysis: Dict[str, Any],
        custom_requirements: Optional[Dict[str, Any]] = None
    ) -> EnvironmentConfig:
        """
        Generate environment configuration from analysis results.
        
        Args:
            project_path: Path to project root
            analysis: Analysis results from analyze_environment_requirements
            custom_requirements: Custom requirements to override defaults
            
        Returns:
            EnvironmentConfig object
        """
        logger = self._get_logger()
        project_path = Path(project_path)
        
        project_info = analysis["project_info"]
        project_type = project_info.get("project_type", "unknown")
        
        # Start with base configuration
        config = EnvironmentConfig(
            project_path=project_path,
            project_type=project_type
        )
        
        # Python version
        python_req = analysis.get("python_requirements", {})
        config.python_version = python_req.get("version")
        
        # System packages
        system_reqs = analysis.get("system_requirements", [])
        config.system_packages = self._resolve_system_packages(system_reqs)
        
        # Python packages
        if project_type == "python":
            config.python_packages = python_req.get("runtime_packages", [])
            config.dev_packages = python_req.get("dev_packages", [])
            
            # Add recommended tools
            for tool in analysis.get("recommended_tools", []):
                if tool in self.tool_configs:
                    config.dev_packages.extend(self.tool_configs[tool]["packages"])
        
        # Quality tools
        quality = analysis.get("quality_setup", {})
        config.quality_tools = (
            quality.get("linting", []) + 
            quality.get("formatting", []) + 
            quality.get("type_checking", [])
        )
        config.test_frameworks = quality.get("testing", [])
        
        # Build tools
        if project_type == "python":
            config.build_tools = ["build", "wheel", "setuptools"]
        
        # Environment variables
        config.environment_variables = {
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONUNBUFFERED": "1",
            "PIP_NO_CACHE_DIR": "1"
        }
        
        # Add tool-specific environment variables
        for tool in config.quality_tools:
            if tool in self.tool_configs:
                config.environment_variables.update(
                    self.tool_configs[tool]["env_vars"]
                )
        
        # Container configuration
        if project_info.get("configurations", {}).get("has_dockerfile"):
            config.container_config = self._generate_container_config(config)
        
        # CI configuration
        ci_setup = analysis.get("ci_setup", {})
        if ci_setup.get("recommended", False):
            config.ci_config = self._generate_ci_config(config, ci_setup)
        
        # Apply custom requirements
        if custom_requirements:
            config = self._apply_custom_requirements(config, custom_requirements)
        
        # Remove duplicates
        config.python_packages = list(set(config.python_packages))
        config.dev_packages = list(set(config.dev_packages))
        config.system_packages = list(set(config.system_packages))
        
        logger.info(f"Generated configuration for {project_type} project")
        return config
    
    def _resolve_system_packages(self, requirements: List[str]) -> List[str]:
        """Resolve system package names for current platform."""
        import platform
        system = platform.system().lower()
        
        # Map system names
        platform_map = {
            "darwin": "darwin",
            "linux": "linux", 
            "windows": "windows"
        }
        platform_key = platform_map.get(system, "linux")
        
        resolved = []
        for req in requirements:
            if req in self.system_package_mappings:
                resolved.extend(self.system_package_mappings[req][platform_key])
            else:
                resolved.append(req)
        
        return resolved
    
    def _generate_container_config(self, config: EnvironmentConfig) -> Dict[str, Any]:
        """Generate container configuration."""
        container_config = {
            "base_image": "python:3.11-slim" if config.project_type == "python" else "ubuntu:22.04",
            "system_packages": config.system_packages,
            "python_version": config.python_version,
            "working_dir": "/app",
            "exposed_ports": [],
            "volumes": [],
            "environment": config.environment_variables
        }
        
        # Add common development ports
        if config.project_type == "python":
            container_config["exposed_ports"] = [8000, 5000]
        elif config.project_type == "nodejs":
            container_config["exposed_ports"] = [3000, 8080]
        
        return container_config
    
    def _generate_ci_config(
        self, 
        config: EnvironmentConfig, 
        ci_setup: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate CI/CD configuration."""
        ci_config = {
            "platforms": ci_setup.get("platforms", []),
            "workflows": ci_setup.get("workflows", []),
            "matrix_testing": ci_setup.get("matrix_testing", False),
            "python_versions": ["3.9", "3.10", "3.11", "3.12"] if ci_setup.get("matrix_testing") else [config.python_version],
            "os_matrix": ["ubuntu-latest", "macos-latest", "windows-latest"] if ci_setup.get("matrix_testing") else ["ubuntu-latest"],
            "steps": []
        }
        
        # Define workflow steps
        if "test" in ci_config["workflows"]:
            ci_config["steps"].extend([
                "checkout",
                "setup-python",
                "install-dependencies", 
                "run-tests"
            ])
        
        if "lint" in ci_config["workflows"]:
            ci_config["steps"].extend([
                "run-linting",
                "run-formatting-check"
            ])
        
        if "build" in ci_config["workflows"]:
            ci_config["steps"].extend([
                "build-package",
                "upload-artifacts"
            ])
        
        return ci_config
    
    def _apply_custom_requirements(
        self, 
        config: EnvironmentConfig, 
        custom: Dict[str, Any]
    ) -> EnvironmentConfig:
        """Apply custom requirements to override defaults."""
        # Override Python version
        if "python_version" in custom:
            config.python_version = custom["python_version"]
        
        # Add custom packages
        if "python_packages" in custom:
            config.python_packages.extend(custom["python_packages"])
        
        if "dev_packages" in custom:
            config.dev_packages.extend(custom["dev_packages"])
        
        if "system_packages" in custom:
            config.system_packages.extend(custom["system_packages"])
        
        # Override environment variables
        if "environment_variables" in custom:
            config.environment_variables.update(custom["environment_variables"])
        
        return config
    
    @flow(
        name="configure_development_environment",
        description="Complete development environment configuration flow"
    )
    def configure_development_environment(
        self,
        project_path: Path,
        auto_install: bool = True,
        include_system_info: bool = True,
        custom_requirements: Optional[Dict[str, Any]] = None,
        create_artifacts: bool = True
    ) -> ConfigurationResult:
        """
        Configure a complete development environment for a project.
        
        Args:
            project_path: Path to project root
            auto_install: Whether to automatically install dependencies
            include_system_info: Whether to include full system analysis
            custom_requirements: Custom requirements to override defaults
            create_artifacts: Whether to create configuration artifacts
            
        Returns:
            ConfigurationResult with success status and details
        """
        import time
        start_time = time.time()
        
        logger = self._get_logger()
        project_path = Path(project_path).resolve()
        
        logger.info(f"Starting environment configuration for {project_path}")
        
        result = ConfigurationResult(
            success=False,
            config=EnvironmentConfig(project_path=project_path, project_type="unknown")
        )
        
        try:
            # Step 1: Analyze requirements
            logger.info("Analyzing environment requirements...")
            analysis = self.analyze_environment_requirements(
                project_path=project_path,
                include_system_info=include_system_info
            )
            result.steps_completed.append("analyze_requirements")
            result.info_tree = analysis.get("info_tree")
            
            # Step 2: Generate configuration
            logger.info("Generating environment configuration...")
            config = self.generate_environment_config(
                project_path=project_path,
                analysis=analysis,
                custom_requirements=custom_requirements
            )
            result.config = config
            result.steps_completed.append("generate_configuration")
            
            # Step 3: Install environment if requested
            if auto_install and config.project_type == "python":
                logger.info("Installing Python environment...")
                install_success = self._install_python_environment(config, result)
                if install_success:
                    result.steps_completed.append("install_environment")
                else:
                    result.steps_failed.append("install_environment")
            
            # Step 4: Configure quality tools
            if config.quality_tools:
                logger.info("Configuring quality tools...")
                quality_success = self._configure_quality_tools(config, result)
                if quality_success:
                    result.steps_completed.append("configure_quality_tools")
                else:
                    result.steps_failed.append("configure_quality_tools")
            
            # Step 5: Generate configuration files
            logger.info("Generating configuration files...")
            files_success = self._generate_config_files(config, result)
            if files_success:
                result.steps_completed.append("generate_config_files")
            else:
                result.steps_failed.append("generate_config_files")
            
            # Determine overall success
            result.success = len(result.steps_failed) == 0
            
            # Create artifacts if requested
            if create_artifacts:
                self._create_configuration_artifacts(result, analysis)
            
        except Exception as e:
            logger.error(f"Environment configuration failed: {e}")
            result.steps_failed.append(f"configuration_error: {str(e)}")
        
        result.execution_time = time.time() - start_time
        
        status = "✅ Success" if result.success else "❌ Failed"
        logger.info(f"Environment configuration completed: {status}")
        
        return result
    
    def _install_python_environment(
        self, 
        config: EnvironmentConfig, 
        result: ConfigurationResult
    ) -> bool:
        """Install Python environment based on configuration."""
        logger = self._get_logger()
        
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
            
            # Install dependencies
            deps_result = install_dependencies(
                project_path=config.project_path,
                dev=True
            )
            
            if not deps_result["success"]:
                result.warnings.append(f"Dependency installation issues: {deps_result.get('message')}")
            
            # Install additional development packages
            if config.dev_packages:
                self._install_additional_packages(config.project_path, config.dev_packages)
            
            return True
            
        except Exception as e:
            logger.error(f"Python environment installation failed: {e}")
            result.warnings.append(str(e))
            return False
    
    def _install_with_pip(
        self, 
        config: EnvironmentConfig, 
        result: ConfigurationResult
    ) -> bool:
        """Fallback installation using system pip."""
        logger = self._get_logger()
        
        try:
            # Create virtual environment with venv
            venv_path = config.project_path / ".venv"
            
            import subprocess
            import sys
            
            subprocess.run([
                sys.executable, "-m", "venv", str(venv_path)
            ], check=True)
            
            # Determine pip path
            if os.name == 'nt':  # Windows
                pip_path = venv_path / "Scripts" / "pip.exe"
            else:
                pip_path = venv_path / "bin" / "pip"
            
            # Install packages
            all_packages = config.python_packages + config.dev_packages
            if all_packages:
                subprocess.run([
                    str(pip_path), "install"
                ] + all_packages, check=True)
            
            logger.info(f"Installed Python environment with pip at {venv_path}")
            return True
            
        except Exception as e:
            logger.error(f"Pip installation failed: {e}")
            return False
    
    def _install_additional_packages(self, project_path: Path, packages: List[str]):
        """Install additional packages in the project environment."""
        if not packages:
            return
        
        try:
            # Use UV to install packages
            from DHT.modules.uv_prefect_tasks import add_dependency
            
            for package in packages:
                try:
                    add_dependency(
                        project_path=project_path,
                        package=package,
                        dev=True
                    )
                except Exception as e:
                    self._get_logger().warning(f"Failed to install {package}: {e}")
                    
        except Exception as e:
            self._get_logger().warning(f"Additional package installation failed: {e}")
    
    def _configure_quality_tools(
        self, 
        config: EnvironmentConfig, 
        result: ConfigurationResult
    ) -> bool:
        """Configure quality tools like linters and formatters."""
        logger = self._get_logger()
        
        try:
            # Generate tool configurations
            configs_generated = []
            
            for tool in config.quality_tools:
                if tool == "ruff":
                    self._generate_ruff_config(config.project_path)
                    configs_generated.append("ruff.toml")
                elif tool == "black":
                    self._generate_black_config(config.project_path)
                    configs_generated.append("pyproject.toml[tool.black]")
                elif tool == "mypy":
                    self._generate_mypy_config(config.project_path)
                    configs_generated.append("mypy.ini")
                elif tool == "pytest":
                    self._generate_pytest_config(config.project_path)
                    configs_generated.append("pytest.ini")
            
            # Generate pre-commit configuration
            if "pre-commit" in config.quality_tools:
                self._generate_precommit_config(config.project_path, config.quality_tools)
                configs_generated.append(".pre-commit-config.yaml")
            
            logger.info(f"Generated configurations: {', '.join(configs_generated)}")
            return True
            
        except Exception as e:
            logger.error(f"Quality tools configuration failed: {e}")
            return False
    
    def _generate_config_files(
        self, 
        config: EnvironmentConfig, 
        result: ConfigurationResult
    ) -> bool:
        """Generate various configuration files."""
        logger = self._get_logger()
        
        try:
            files_created = []
            
            # Generate .gitignore if needed
            if not (config.project_path / ".gitignore").exists():
                self._generate_gitignore(config.project_path, config.project_type)
                files_created.append(".gitignore")
            
            # Generate Dockerfile if container config exists
            if config.container_config:
                self._generate_dockerfile(config)
                files_created.append("Dockerfile")
            
            # Generate GitHub Actions workflow if CI config exists
            if config.ci_config and "github-actions" in config.ci_config["platforms"]:
                self._generate_github_workflow(config)
                files_created.append(".github/workflows/ci.yml")
            
            # Generate environment file
            if config.environment_variables:
                self._generate_env_file(config)
                files_created.append(".env.example")
            
            logger.info(f"Created configuration files: {', '.join(files_created)}")
            return True
            
        except Exception as e:
            logger.error(f"Configuration file generation failed: {e}")
            return False
    
    def _generate_ruff_config(self, project_path: Path):
        """Generate ruff configuration."""
        config_content = '''# Ruff configuration
target-version = "py311"
line-length = 88
select = [
    "E",  # pycodestyle errors
    "W",  # pycodestyle warnings  
    "F",  # pyflakes
    "I",  # isort
    "B",  # flake8-bugbear
    "C4", # flake8-comprehensions
    "UP", # pyupgrade
]
ignore = [
    "E501",  # line too long (handled by black)
    "B008",  # do not perform function calls in argument defaults
]

[per-file-ignores]
"__init__.py" = ["F401"]
"tests/**/*" = ["B011"]

[isort]
known-first-party = ["dht"]
'''
        
        ruff_config = project_path / "ruff.toml"
        ruff_config.write_text(config_content)
    
    def _generate_black_config(self, project_path: Path):
        """Generate black configuration in pyproject.toml."""
        pyproject = project_path / "pyproject.toml"
        
        # Read existing or create new
        config_dict = {}
        if pyproject.exists():
            try:
                import tomllib
            except ImportError:
                import tomli as tomllib
            
            try:
                with open(pyproject, "rb") as f:
                    config_dict = tomllib.load(f)
            except Exception:
                pass
        
        # Add black configuration
        if "tool" not in config_dict:
            config_dict["tool"] = {}
        
        config_dict["tool"]["black"] = {
            "line-length": 88,
            "target-version": ["py311"],
            "include": r'\.pyi?$',
            "extend-exclude": r"""
/(
    \.eggs
  | \.git
  | \.hg
  | \.mypy_cache
  | \.tox
  | \.venv
  | _build
  | buck-out
  | build
  | dist
)/
"""
        }
        
        # Write back
        try:
            import tomli_w
            with open(pyproject, "wb") as f:
                tomli_w.dump(config_dict, f)
        except ImportError:
            # Fallback: write TOML manually for the common case
            # This is a simplified TOML writer that handles our specific case
            lines = []
            if "tool" in config_dict and "black" in config_dict["tool"]:
                lines.append("[tool.black]")
                black_config = config_dict["tool"]["black"]
                for key, value in black_config.items():
                    if isinstance(value, str):
                        # Handle multiline strings
                        if "\n" in value:
                            lines.append(f'{key} = """{value}"""')
                        else:
                            lines.append(f'{key} = "{value}"')
                    elif isinstance(value, list):
                        lines.append(f'{key} = {value}')
                    else:
                        lines.append(f'{key} = {value}')
            
            with open(pyproject, "w") as f:
                f.write("\n".join(lines) + "\n")
    
    def _generate_mypy_config(self, project_path: Path):
        """Generate mypy configuration."""
        config_content = '''[mypy]
python_version = 3.11
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True
disallow_incomplete_defs = True
check_untyped_defs = True
disallow_untyped_decorators = True
no_implicit_optional = True
warn_redundant_casts = True
warn_unused_ignores = True
warn_no_return = True
warn_unreachable = True
strict_equality = True
'''
        
        mypy_config = project_path / "mypy.ini"
        mypy_config.write_text(config_content)
    
    def _generate_pytest_config(self, project_path: Path):
        """Generate pytest configuration."""
        config_content = '''[tool:pytest]
minversion = 6.0
addopts = -ra -q --strict-markers --strict-config
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
'''
        
        pytest_config = project_path / "pytest.ini"
        pytest_config.write_text(config_content)
    
    def _generate_precommit_config(self, project_path: Path, quality_tools: List[str]):
        """Generate pre-commit configuration."""
        import yaml
        
        repos = []
        
        # Add pre-commit hooks based on configured tools
        if "black" in quality_tools:
            repos.append({
                "repo": "https://github.com/psf/black",
                "rev": "23.7.0",
                "hooks": [{"id": "black"}]
            })
        
        if "ruff" in quality_tools:
            repos.append({
                "repo": "https://github.com/astral-sh/ruff-pre-commit",
                "rev": "v0.0.287",
                "hooks": [
                    {"id": "ruff", "args": ["--fix"]},
                    {"id": "ruff-format"}
                ]
            })
        
        if "mypy" in quality_tools:
            repos.append({
                "repo": "https://github.com/pre-commit/mirrors-mypy",
                "rev": "v1.5.1",
                "hooks": [{"id": "mypy", "additional_dependencies": ["types-all"]}]
            })
        
        # Add common hooks
        repos.append({
            "repo": "https://github.com/pre-commit/pre-commit-hooks",
            "rev": "v4.4.0",
            "hooks": [
                {"id": "trailing-whitespace"},
                {"id": "end-of-file-fixer"},
                {"id": "check-yaml"},
                {"id": "check-added-large-files"}
            ]
        })
        
        config = {
            "repos": repos,
            "default_language_version": {
                "python": "python3.11"
            }
        }
        
        precommit_config = project_path / ".pre-commit-config.yaml"
        with open(precommit_config, "w") as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    
    def _generate_gitignore(self, project_path: Path, project_type: str):
        """Generate appropriate .gitignore file."""
        gitignore_content = """# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# C extensions
*.so

# Distribution / packaging
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
pip-wheel-metadata/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# PyInstaller
*.manifest
*.spec

# Installer logs
pip-log.txt
pip-delete-this-directory.txt

# Unit test / coverage reports
htmlcov/
.tox/
.nox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
*.py,cover
.hypothesis/
.pytest_cache/

# Translations
*.mo
*.pot

# Django stuff:
*.log
local_settings.py
db.sqlite3
db.sqlite3-journal

# Flask stuff:
instance/
.webassets-cache

# Scrapy stuff:
.scrapy

# Sphinx documentation
docs/_build/

# PyBuilder
target/

# Jupyter Notebook
.ipynb_checkpoints

# IPython
profile_default/
ipython_config.py

# pyenv
.python-version

# pipenv
Pipfile.lock

# PEP 582
__pypackages__/

# Celery stuff
celerybeat-schedule
celerybeat.pid

# SageMath parsed files
*.sage.py

# Environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# Spyder project settings
.spyderproject
.spyproject

# Rope project settings
.ropeproject

# mkdocs documentation
/site

# mypy
.mypy_cache/
.dmypy.json
dmypy.json

# Pyre type checker
.pyre/

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~

# OS generated files
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db
"""
        
        if project_type == "nodejs":
            gitignore_content += """
# Node.js
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
.npm
.eslintcache
"""
        
        gitignore_file = project_path / ".gitignore"
        gitignore_file.write_text(gitignore_content)
    
    def _generate_dockerfile(self, config: EnvironmentConfig):
        """Generate Dockerfile from container configuration."""
        container_config = config.container_config
        
        dockerfile_content = f'''FROM {container_config["base_image"]}

# Set working directory
WORKDIR {container_config["working_dir"]}

# Install system dependencies
'''
        
        if container_config["system_packages"]:
            if "ubuntu" in container_config["base_image"] or "debian" in container_config["base_image"]:
                dockerfile_content += f'''RUN apt-get update && apt-get install -y \\
    {" ".join(container_config["system_packages"])} \\
    && rm -rf /var/lib/apt/lists/*

'''
        
        if config.project_type == "python":
            dockerfile_content += '''# Copy requirements first for better caching
COPY requirements.txt* pyproject.toml* uv.lock* ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt || \\
    pip install --no-cache-dir -e . || \\
    echo "No requirements file found"

# Copy project files
COPY . .

'''
        
        if container_config["exposed_ports"]:
            for port in container_config["exposed_ports"]:
                dockerfile_content += f'EXPOSE {port}\n'
        
        dockerfile_content += '''
# Default command
CMD ["python", "-m", "your_module"]
'''
        
        dockerfile_path = config.project_path / "Dockerfile"
        dockerfile_path.write_text(dockerfile_content)
    
    def _generate_github_workflow(self, config: EnvironmentConfig):
        """Generate GitHub Actions workflow."""
        import yaml
        
        ci_config = config.ci_config
        
        workflow = {
            "name": "CI",
            "on": {
                "push": {"branches": ["main", "develop"]},
                "pull_request": {"branches": ["main"]}
            },
            "jobs": {
                "test": {
                    "runs-on": "${{ matrix.os }}",
                    "strategy": {
                        "matrix": {
                            "os": ci_config["os_matrix"],
                            "python-version": ci_config["python_versions"]
                        }
                    },
                    "steps": [
                        {
                            "uses": "actions/checkout@v4"
                        },
                        {
                            "name": "Set up Python ${{ matrix.python-version }}",
                            "uses": "actions/setup-python@v4",
                            "with": {
                                "python-version": "${{ matrix.python-version }}"
                            }
                        },
                        {
                            "name": "Install dependencies",
                            "run": "pip install -e .[dev]"
                        }
                    ]
                }
            }
        }
        
        # Add workflow-specific steps
        if "test" in ci_config["workflows"]:
            workflow["jobs"]["test"]["steps"].append({
                "name": "Run tests",
                "run": "pytest"
            })
        
        if "lint" in ci_config["workflows"]:
            workflow["jobs"]["test"]["steps"].extend([
                {
                    "name": "Run linting",
                    "run": "ruff check ."
                },
                {
                    "name": "Check formatting",
                    "run": "black --check ."
                }
            ])
        
        # Ensure .github/workflows directory exists
        workflows_dir = config.project_path / ".github" / "workflows"
        workflows_dir.mkdir(parents=True, exist_ok=True)
        
        workflow_file = workflows_dir / "ci.yml"
        with open(workflow_file, "w") as f:
            yaml.dump(workflow, f, default_flow_style=False, sort_keys=False)
    
    def _generate_env_file(self, config: EnvironmentConfig):
        """Generate .env.example file."""
        env_content = "# Environment Variables\n"
        env_content += "# Copy this file to .env and fill in the values\n\n"
        
        for key, value in config.environment_variables.items():
            env_content += f"{key}={value}\n"
        
        env_file = config.project_path / ".env.example"
        env_file.write_text(env_content)
    
    def _create_configuration_artifacts(
        self, 
        result: ConfigurationResult, 
        analysis: Dict[str, Any]
    ):
        """Create Prefect artifacts with configuration details."""
        # Generate environment report
        config = result.config
        
        report = f"""# Environment Configuration Report

**Project**: {config.project_path.name}
**Type**: {config.project_type}
**Timestamp**: {datetime.now().isoformat()}
**Success**: {'✅' if result.success else '❌'}

## Configuration Summary

### Python Environment
- **Version**: {config.python_version or 'Default'}
- **Runtime Packages**: {len(config.python_packages)}
- **Development Packages**: {len(config.dev_packages)}

### Quality Tools
- **Configured**: {', '.join(config.quality_tools) if config.quality_tools else 'None'}
- **Test Frameworks**: {', '.join(config.test_frameworks) if config.test_frameworks else 'None'}

### System Requirements
- **Packages**: {len(config.system_packages)}
- **Build Tools**: {', '.join(config.build_tools) if config.build_tools else 'None'}

## Steps Completed
"""
        
        for step in result.steps_completed:
            report += f"- ✅ {step}\n"
        
        if result.steps_failed:
            report += "\n## Steps Failed\n"
            for step in result.steps_failed:
                report += f"- ❌ {step}\n"
        
        if result.warnings:
            report += "\n## Warnings\n"
            for warning in result.warnings:
                report += f"- ⚠️ {warning}\n"
        
        report += f"\n## Execution Time\n{result.execution_time:.2f} seconds"
        
        # Create configuration artifact
        create_markdown_artifact(
            key="environment-configuration-report",
            markdown=report,
            description="Environment configuration report"
        )
        
        # Create detailed configuration as JSON artifact
        config_data = {
            "project_path": str(config.project_path),
            "project_type": config.project_type,
            "python_version": config.python_version,
            "system_packages": config.system_packages,
            "python_packages": config.python_packages,
            "dev_packages": config.dev_packages,
            "quality_tools": config.quality_tools,
            "test_frameworks": config.test_frameworks,
            "build_tools": config.build_tools,
            "environment_variables": config.environment_variables,
            "container_config": config.container_config,
            "ci_config": config.ci_config
        }
        
        # Save detailed configuration
        config_file = config.project_path / ".dht" / "environment_config.json"
        config_file.parent.mkdir(exist_ok=True)
        
        with open(config_file, "w") as f:
            json.dump(config_data, f, indent=2, default=str)


# Export public API
__all__ = [
    "EnvironmentConfigurator",
    "EnvironmentConfig", 
    "ConfigurationResult"
]