#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
environment_snapshot_models.py - Data models for environment snapshots

This module contains the data models used by the environment reproducer.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Extracted from environment_reproducer.py to reduce file size
# - Contains EnvironmentSnapshot and ReproductionResult dataclasses
#

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple


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