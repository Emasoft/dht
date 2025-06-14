#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
environment_config_models.py - Data models for environment configuration

This module contains the data models used by the environment configurator.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Extracted from environment_configurator.py to reduce file size
# - Contains EnvironmentConfig and ConfigurationResult dataclasses
#

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field


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