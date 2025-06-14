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
from typing import Dict, List, Any, Optional


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
    snapshot: EnvironmentSnapshot
    
    # Steps completed
    steps_completed: List[str] = field(default_factory=list)
    steps_failed: List[str] = field(default_factory=list)
    
    # Verification results
    platform_compatible: bool = True
    python_version_matched: bool = False
    tools_matched: Dict[str, bool] = field(default_factory=dict)
    packages_installed: Dict[str, bool] = field(default_factory=dict)
    configs_verified: Dict[str, bool] = field(default_factory=dict)
    
    # Issues encountered
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    
    # Platform differences
    platform_differences: List[str] = field(default_factory=list)
    required_adaptations: List[str] = field(default_factory=list)
    
    # Timing
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    duration_seconds: float = 0.0
    
    # Artifacts created
    created_files: List[str] = field(default_factory=list)
    lock_files_generated: List[str] = field(default_factory=list)