#!/usr/bin/env python3
"""
act_integration_models.py - Data models for act integration  This module contains data models and structures used by the act integration system.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

"""
act_integration_models.py - Data models for act integration

This module contains data models and structures used by the act integration system.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Extracted from act_integration.py to reduce file size
# - Contains ActConfig dataclass and related type definitions
#

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ActConfig:
    """Configuration for act runner."""

    runner_image: str = "catthehacker/ubuntu:act-latest"
    platform: str = "ubuntu-latest"
    container_runtime: str = "podman"  # Prefer podman for rootless
    use_gh_extension: bool = True
    artifact_server_path: str | None = None
    cache_server_path: str | None = None
    reuse_containers: bool = False
    bind_workdir: bool = True


@dataclass
class WorkflowInfo:
    """Information about a GitHub workflow."""

    file: str
    name: str
    path: str
    on: dict[str, Any]
    jobs: list[str]
    error: str | None = None


@dataclass
class LintResult:
    """Result from linting a workflow."""

    success: bool
    errors: list[dict[str, Any]]
    warnings: list[dict[str, Any]]
    raw_output: str | None = None


@dataclass
class ActCheckResult:
    """Result from checking act availability."""

    gh_cli_available: bool
    gh_cli_version: str | None
    act_extension_installed: bool
    act_extension_version: str | None
    standalone_act_available: bool
    standalone_act_version: str | None
    act_available: bool
    preferred_method: str | None


@dataclass
class ContainerSetupResult:
    """Result from container environment setup."""

    success: bool
    runtime_available: bool
    runtime: str | None
    socket_path: str | None
    volumes: list[str]
    environment: dict[str, str]
    error: str | None = None
