#!/usr/bin/env python3
"""
environment_config_models.py - Data models for environment configuration

This module contains the data models used by the environment configurator.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Extracted from environment_configurator.py to reduce file size
# - Contains EnvironmentConfig and ConfigurationResult dataclasses
#

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class EnvironmentConfig:
    """Configuration for a development environment."""

    project_path: Path
    project_type: str
    python_version: str | None = None
    node_version: str | None = None
    system_packages: list[str] = field(default_factory=list)
    python_packages: list[str] = field(default_factory=list)
    dev_packages: list[str] = field(default_factory=list)
    environment_variables: dict[str, str] = field(default_factory=dict)
    pre_install_commands: list[str] = field(default_factory=list)
    post_install_commands: list[str] = field(default_factory=list)
    quality_tools: list[str] = field(default_factory=list)
    test_frameworks: list[str] = field(default_factory=list)
    build_tools: list[str] = field(default_factory=list)
    container_config: dict[str, Any] | None = None
    ci_config: dict[str, Any] | None = None


@dataclass
class ConfigurationResult:
    """Result of environment configuration."""

    success: bool
    config: EnvironmentConfig
    steps_completed: list[str] = field(default_factory=list)
    steps_failed: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    info_tree: dict[str, Any] | None = None
    execution_time: float = 0.0
