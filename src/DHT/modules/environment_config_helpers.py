#!/usr/bin/env python3
from __future__ import annotations

"""
environment_config_helpers.py - Helper functions for environment configuration  This module contains helper functions and constants used by the environment configurator.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

"""
environment_config_helpers.py - Helper functions for environment configuration

This module contains helper functions and constants used by the environment configurator.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Extracted from environment_configurator.py to reduce file size
# - Contains configuration generation and artifact creation functions
#


import json
from datetime import datetime
from typing import Any

from prefect.artifacts import create_markdown_artifact

from DHT.modules.environment_config_models import ConfigurationResult, EnvironmentConfig

# Platform-specific package mappings
SYSTEM_PACKAGE_MAPPINGS = {
    "python-dev": {
        "darwin": [],  # Usually available via Xcode tools
        "linux": ["python3-dev", "python3-distutils"],
        "windows": [],  # Usually not needed
    },
    "build-essential": {
        "darwin": [],  # Xcode command line tools
        "linux": ["build-essential", "gcc", "g++", "make"],
        "windows": [],  # Visual Studio Build Tools
    },
    "git": {
        "darwin": ["git"],  # via Xcode or Homebrew
        "linux": ["git"],
        "windows": ["git"],  # Git for Windows
    },
    "curl": {"darwin": ["curl"], "linux": ["curl"], "windows": ["curl"]},
    "openssl": {"darwin": ["openssl"], "linux": ["libssl-dev", "openssl"], "windows": []},
}

# Tool-specific configurations
TOOL_CONFIGS = {
    "pytest": {
        "packages": ["pytest", "pytest-cov", "pytest-xdist"],
        "config_files": ["pytest.ini", "pyproject.toml"],
        "env_vars": {"PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1"},
    },
    "black": {"packages": ["black"], "config_files": ["pyproject.toml", ".black"], "env_vars": {}},
    "ruff": {"packages": ["ruff"], "config_files": ["ruff.toml", "pyproject.toml"], "env_vars": {}},
    "mypy": {"packages": ["mypy"], "config_files": ["mypy.ini", "pyproject.toml"], "env_vars": {}},
    "pre-commit": {"packages": ["pre-commit"], "config_files": [".pre-commit-config.yaml"], "env_vars": {}},
}


def generate_container_config(config: EnvironmentConfig) -> dict[str, Any]:
    """Generate container configuration."""
    container_config = {
        "base_image": "python:3.11-slim" if config.project_type == "python" else "ubuntu:22.04",
        "system_packages": config.system_packages,
        "python_version": config.python_version,
        "working_dir": "/app",
        "exposed_ports": [],
        "volumes": [],
        "environment": config.environment_variables,
    }

    # Add common development ports
    if config.project_type == "python":
        container_config["exposed_ports"] = [8000, 5000]
    elif config.project_type == "nodejs":
        container_config["exposed_ports"] = [3000, 8080]

    return container_config


def generate_ci_config(config: EnvironmentConfig, ci_setup: dict[str, Any]) -> dict[str, Any]:
    """Generate CI/CD configuration."""
    ci_config = {
        "platforms": ci_setup.get("platforms", []),
        "workflows": ci_setup.get("workflows", []),
        "matrix_testing": ci_setup.get("matrix_testing", False),
        "python_versions": ["3.9", "3.10", "3.11", "3.12"]
        if ci_setup.get("matrix_testing")
        else [config.python_version],
        "os_matrix": ["ubuntu-latest", "macos-latest", "windows-latest"]
        if ci_setup.get("matrix_testing")
        else ["ubuntu-latest"],
        "steps": [],
    }

    # Define workflow steps
    if "test" in ci_config["workflows"]:
        ci_config["steps"].extend(["checkout", "setup-python", "install-dependencies", "run-tests"])

    if "lint" in ci_config["workflows"]:
        ci_config["steps"].extend(["run-linting", "run-formatting-check"])

    if "build" in ci_config["workflows"]:
        ci_config["steps"].extend(["build-package", "upload-artifacts"])

    return ci_config


def apply_custom_requirements(config: EnvironmentConfig, custom: dict[str, Any]) -> EnvironmentConfig:
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


def resolve_system_packages(requirements: list[str]) -> list[str]:
    """Resolve system package names for current platform."""
    import platform

    system = platform.system().lower()

    # Map system names
    platform_map = {"darwin": "darwin", "linux": "linux", "windows": "windows"}
    platform_key = platform_map.get(system, "linux")

    resolved = []
    for req in requirements:
        if req in SYSTEM_PACKAGE_MAPPINGS:
            resolved.extend(SYSTEM_PACKAGE_MAPPINGS[req][platform_key])
        else:
            resolved.append(req)

    return resolved


def create_configuration_artifacts(result: ConfigurationResult, analysis: dict[str, Any]) -> None:
    """Create Prefect artifacts with configuration details."""
    # Generate environment report
    config = result.config

    report = f"""# Environment Configuration Report

**Project**: {config.project_path.name}
**Type**: {config.project_type}
**Timestamp**: {datetime.now().isoformat()}
**Success**: {"✅" if result.success else "❌"}

## Configuration Summary

### Python Environment
- **Version**: {config.python_version or "Default"}
- **Runtime Packages**: {len(config.python_packages)}
- **Development Packages**: {len(config.dev_packages)}

### Quality Tools
- **Configured**: {", ".join(config.quality_tools) if config.quality_tools else "None"}
- **Test Frameworks**: {", ".join(config.test_frameworks) if config.test_frameworks else "None"}

### System Requirements
- **Packages**: {len(config.system_packages)}
- **Build Tools**: {", ".join(config.build_tools) if config.build_tools else "None"}

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
        key="environment-configuration-report", markdown=report, description="Environment configuration report"
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
        "ci_config": config.ci_config,
    }

    # Save detailed configuration
    config_file = config.project_path / ".dht" / "environment_config.json"
    config_file.parent.mkdir(exist_ok=True)

    with open(config_file, "w") as f:
        json.dump(config_data, f, indent=2, default=str)
