#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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
from typing import Dict, List, Optional, Any
from pathlib import Path


@dataclass
class ActConfig:
    """Configuration for act runner."""
    runner_image: str = "catthehacker/ubuntu:act-latest"
    platform: str = "ubuntu-latest"
    container_runtime: str = "podman"  # Prefer podman for rootless
    use_gh_extension: bool = True
    artifact_server_path: Optional[str] = None
    cache_server_path: Optional[str] = None
    reuse_containers: bool = False
    bind_workdir: bool = True


@dataclass
class WorkflowInfo:
    """Information about a GitHub workflow."""
    file: str
    name: str
    path: str
    on: Dict[str, Any]
    jobs: List[str]
    error: Optional[str] = None


@dataclass
class LintResult:
    """Result from linting a workflow."""
    success: bool
    errors: List[Dict[str, Any]]
    warnings: List[Dict[str, Any]]
    raw_output: Optional[str] = None


@dataclass
class ActCheckResult:
    """Result from checking act availability."""
    gh_cli_available: bool
    gh_cli_version: Optional[str]
    act_extension_installed: bool
    act_extension_version: Optional[str]
    standalone_act_available: bool
    standalone_act_version: Optional[str]
    act_available: bool
    preferred_method: Optional[str]


@dataclass 
class ContainerSetupResult:
    """Result from container environment setup."""
    success: bool
    runtime_available: bool
    runtime: Optional[str]
    socket_path: Optional[str]
    volumes: List[str]
    environment: Dict[str, str]
    error: Optional[str] = None