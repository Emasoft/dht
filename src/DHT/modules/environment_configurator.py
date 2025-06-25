#!/usr/bin/env python3
from __future__ import annotations

"""
Environment Configurator module.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Initial implementation of environment configurator module
# - Uses diagnostic info tree for intelligent configuration
# - Supports multiple project types and environments
# - Generates platform-specific configurations
# - Integrates with UV, Python, and system tools
# - Refactored to use separate modules for better organization
# - Removed duplicate generator methods to use imported functions
# - Extracted constants and helpers to environment_config_helpers.py
#

"""
Environment Configurator Module.

This module uses the information tree from diagnostic_reporter_v2 to intelligently
configure development environments based on detected tools, project structure,
and platform capabilities.
"""

import logging
from pathlib import Path
from typing import Any, cast

from prefect import flow, get_run_logger, task

from DHT.diagnostic_reporter_v2 import build_system_report
from DHT.modules.config_file_generators import generate_all_configs
from DHT.modules.environment_analyzer import EnvironmentAnalyzer
from DHT.modules.environment_config_helpers import (
    SYSTEM_PACKAGE_MAPPINGS,
    TOOL_CONFIGS,
    apply_custom_requirements,
    create_configuration_artifacts,
    generate_ci_config,
    generate_container_config,
    resolve_system_packages,
)

# Import from new modules
from DHT.modules.environment_config_models import ConfigurationResult, EnvironmentConfig
from DHT.modules.environment_installer import EnvironmentInstaller
from DHT.modules.project_analyzer import ProjectAnalyzer
from DHT.modules.project_file_generators import (
    generate_dockerfile,
    generate_dockerignore,
    generate_env_file,
    generate_github_workflow,
    generate_gitignore,
    generate_makefile,
)


class EnvironmentConfigurator:
    """Intelligent environment configurator using system information tree."""

    def __init__(self) -> None:
        """Initialize the environment configurator."""
        self.logger: logging.Logger | None = None
        self.analyzer = ProjectAnalyzer()
        self.env_analyzer = EnvironmentAnalyzer()
        self.installer = EnvironmentInstaller()

        # Use constants from environment_config_helpers
        self.system_package_mappings = SYSTEM_PACKAGE_MAPPINGS
        self.tool_configs = TOOL_CONFIGS

    def _get_logger(self) -> Any:
        """Get logger with fallback."""
        if self.logger is None:
            try:
                self.logger = get_run_logger()
            except Exception:
                self.logger = logging.getLogger(__name__)
        return self.logger

    @task(name="analyze_environment_requirements", description="Analyze project to determine environment requirements")  # type: ignore[misc]
    def analyze_environment_requirements(self, project_path: Path, include_system_info: bool = True) -> dict[str, Any]:
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
            "info_tree": info_tree,
        }

        logger.info(f"Analysis complete: {len(analysis['detected_tools'])} tools detected")
        return analysis

    def _detect_tools_from_project(self, project_path: Path, project_info: dict[str, Any]) -> list[str]:
        """Delegate to environment analyzer."""
        return cast(list[str], self.env_analyzer.detect_tools_from_project(project_path, project_info))

    def _recommend_tools(self, project_info: dict[str, Any]) -> list[str]:
        """Delegate to environment analyzer."""
        return cast(list[str], self.env_analyzer.recommend_tools(project_info))

    def _determine_system_requirements(self, project_info: dict[str, Any]) -> list[str]:
        """Delegate to environment analyzer."""
        return cast(list[str], self.env_analyzer.determine_system_requirements(project_info))

    def _determine_python_requirements(self, project_path: Path, project_info: dict[str, Any]) -> dict[str, Any]:
        """Delegate to environment analyzer."""
        return cast(dict[str, Any], self.env_analyzer.determine_python_requirements(project_path, project_info))

    def _recommend_quality_tools(self, project_info: dict[str, Any]) -> dict[str, Any]:
        """Delegate to environment analyzer."""
        return cast(dict[str, Any], self.env_analyzer.recommend_quality_tools(project_info))

    def _recommend_ci_setup(self, project_info: dict[str, Any]) -> dict[str, Any]:
        """Delegate to environment analyzer."""
        return cast(dict[str, Any], self.env_analyzer.recommend_ci_setup(project_info))

    @task(name="generate_environment_config", description="Generate environment configuration from analysis")  # type: ignore[misc]
    def generate_environment_config(
        self, project_path: Path, analysis: dict[str, Any], custom_requirements: dict[str, Any] | None = None
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
        config = EnvironmentConfig(project_path=project_path, project_type=project_type)

        # Python version
        python_req = analysis.get("python_requirements", {})
        config.python_version = python_req.get("version")

        # System packages
        system_reqs = analysis.get("system_requirements", [])
        config.system_packages = resolve_system_packages(system_reqs)

        # Python packages
        if project_type == "python":
            config.python_packages = python_req.get("runtime_packages", [])
            config.dev_packages = python_req.get("dev_packages", [])

            # Add recommended tools
            for tool in analysis.get("recommended_tools", []):
                if tool in TOOL_CONFIGS:
                    config.dev_packages.extend(TOOL_CONFIGS[tool]["packages"])

        # Quality tools
        quality = analysis.get("quality_setup", {})
        config.quality_tools = (
            quality.get("linting", []) + quality.get("formatting", []) + quality.get("type_checking", [])
        )
        config.test_frameworks = quality.get("testing", [])

        # Build tools
        if project_type == "python":
            config.build_tools = ["build", "wheel", "setuptools"]

        # Environment variables
        config.environment_variables = {
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONUNBUFFERED": "1",
            "PIP_NO_CACHE_DIR": "1",
        }

        # Add tool-specific environment variables
        for tool in config.quality_tools:
            if tool in TOOL_CONFIGS:
                config.environment_variables.update(TOOL_CONFIGS[tool]["env_vars"])

        # Container configuration
        if project_info.get("configurations", {}).get("has_dockerfile"):
            config.container_config = generate_container_config(config)

        # CI configuration
        ci_setup = analysis.get("ci_setup", {})
        if ci_setup.get("recommended", False):
            config.ci_config = generate_ci_config(config, ci_setup)

        # Apply custom requirements
        if custom_requirements:
            config = apply_custom_requirements(config, custom_requirements)

        # Remove duplicates
        config.python_packages = list(set(config.python_packages))
        config.dev_packages = list(set(config.dev_packages))
        config.system_packages = list(set(config.system_packages))

        logger.info(f"Generated configuration for {project_type} project")
        return config

    @flow(name="configure_development_environment", description="Complete development environment configuration flow")  # type: ignore[misc]
    def configure_development_environment(
        self,
        project_path: Path,
        auto_install: bool = True,
        include_system_info: bool = True,
        custom_requirements: dict[str, Any] | None = None,
        create_artifacts: bool = True,
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
            success=False, config=EnvironmentConfig(project_path=project_path, project_type="unknown")
        )

        try:
            # Step 1: Analyze requirements
            logger.info("Analyzing environment requirements...")
            analysis = self.analyze_environment_requirements(
                project_path=project_path, include_system_info=include_system_info
            )
            result.steps_completed.append("analyze_requirements")
            result.info_tree = analysis.get("info_tree")

            # Step 2: Generate configuration
            logger.info("Generating environment configuration...")
            config = self.generate_environment_config(
                project_path=project_path, analysis=analysis, custom_requirements=custom_requirements
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
                create_configuration_artifacts(result, analysis)

        except Exception as e:
            logger.error(f"Environment configuration failed: {e}")
            result.steps_failed.append(f"configuration_error: {str(e)}")

        result.execution_time = time.time() - start_time

        status = "✅ Success" if result.success else "❌ Failed"
        logger.info(f"Environment configuration completed: {status}")

        return result

    def _install_python_environment(self, config: EnvironmentConfig, result: ConfigurationResult) -> bool:
        """Delegate to environment installer."""
        return cast(bool, self.installer.install_python_environment(config, result))

    def _install_with_pip(self, config: EnvironmentConfig, result: ConfigurationResult) -> bool:
        """Delegate to environment installer."""
        return cast(bool, self.installer._install_with_pip(config, result))

    def _install_additional_packages(self, project_path: Path, packages: list[str]) -> None:
        """Delegate to environment installer."""
        self.installer._install_additional_packages(project_path, packages)

    def _configure_quality_tools(self, config: EnvironmentConfig, result: ConfigurationResult) -> bool:
        """Configure quality tools like linters and formatters."""
        logger = self._get_logger()

        try:
            # Generate all configurations using the generator module
            configs_generated = generate_all_configs(
                project_path=config.project_path,
                quality_tools=config.quality_tools,
                test_frameworks=config.test_frameworks,
            )

            logger.info(f"Generated configurations: {', '.join(configs_generated)}")
            return True

        except Exception as e:
            logger.error(f"Quality tools configuration failed: {e}")
            return False

    def _generate_config_files(self, config: EnvironmentConfig, result: ConfigurationResult) -> bool:
        """Generate various configuration files."""
        logger = self._get_logger()

        try:
            files_created: list[Any] = []

            # Generate .gitignore if needed
            if not (config.project_path / ".gitignore").exists():
                generate_gitignore(config.project_path, config.project_type)
                files_created.append(".gitignore")

            # Generate Dockerfile if container config exists
            if config.container_config:
                generate_dockerfile(config)
                files_created.append("Dockerfile")
                generate_dockerignore(config.project_path)
                files_created.append(".dockerignore")

            # Generate GitHub Actions workflow if CI config exists
            if config.ci_config and "github-actions" in config.ci_config.get("platforms", []):
                generate_github_workflow(config)
                files_created.append(".github/workflows/ci.yml")

            # Generate environment file
            if config.environment_variables:
                generate_env_file(config)
                files_created.append(".env.example")

            # Generate Makefile if build tools configured
            if config.build_tools:
                generate_makefile(config)
                files_created.append("Makefile")

            logger.info(f"Created configuration files: {', '.join(files_created)}")
            return True

        except Exception as e:
            logger.error(f"Configuration file generation failed: {e}")
            return False


# Export public API
__all__ = ["EnvironmentConfigurator", "EnvironmentConfig", "ConfigurationResult"]
