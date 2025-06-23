#!/usr/bin/env python3
from __future__ import annotations

"""
environment_snapshot_models.py - Data models for environment snapshots  This module contains the data models used by the environment reproducer.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

"""
environment_snapshot_models.py - Data models for environment snapshots

This module contains the data models used by the environment reproducer.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Extracted from environment_reproducer.py to reduce file size
# - Contains EnvironmentSnapshot and ReproductionResult dataclasses
#


from dataclasses import dataclass, field
from typing import Any


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
    python_packages: dict[str, str] = field(default_factory=dict)  # name -> version
    system_packages: dict[str, str] = field(default_factory=dict)  # name -> version

    # Tool versions (exact versions for reproducibility)
    tool_versions: dict[str, str] = field(default_factory=dict)  # tool -> version
    tool_paths: dict[str, str] = field(default_factory=dict)  # tool -> path
    tool_configs: dict[str, Any] = field(default_factory=dict)  # tool -> config

    # Environment variables and settings
    environment_variables: dict[str, str] = field(default_factory=dict)
    path_entries: list[str] = field(default_factory=list)

    # Project-specific information
    project_path: str = ""
    project_type: str = ""
    lock_files: dict[str, str] = field(default_factory=dict)  # filename -> content
    config_files: dict[str, str] = field(default_factory=dict)  # filename -> content

    # Checksums for verification
    checksums: dict[str, str] = field(default_factory=dict)  # file -> checksum

    # Reproduction instructions
    reproduction_steps: list[str] = field(default_factory=list)
    platform_notes: list[str] = field(default_factory=list)


@dataclass
class ReproductionResult:
    """Result of environment reproduction attempt."""

    success: bool
    snapshot_id: str
    platform: str

    # Verification results
    tools_verified: dict[str, bool] = field(default_factory=dict)
    versions_verified: dict[str, bool] = field(default_factory=dict)
    configs_verified: dict[str, bool] = field(default_factory=dict)

    # Discrepancies found
    version_mismatches: dict[str, tuple[str, str]] = field(default_factory=dict)  # tool -> (expected, actual)
    missing_tools: list[str] = field(default_factory=list)
    config_differences: dict[str, str] = field(default_factory=dict)  # file -> diff

    # Reproduction actions taken
    actions_completed: list[str] = field(default_factory=list)
    actions_failed: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    execution_time: float = 0.0
