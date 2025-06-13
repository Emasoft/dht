#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
project_analysis_models.py - Data models for project analysis

This module contains the data classes used for project analysis results
and validation.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Extracted from project_type_detector.py to reduce file size
# - Contains ProjectAnalysis and ValidationResult dataclasses
# - Imports ProjectType and ProjectCategory from new enums module
#

from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass, field

from DHT.modules.project_type_enums import ProjectType, ProjectCategory


@dataclass
class ProjectAnalysis:
    """Results of project type analysis."""
    type: ProjectType
    category: ProjectCategory
    confidence: float
    detected_types: List[ProjectType] = field(default_factory=list)
    markers: List[str] = field(default_factory=list)
    primary_dependencies: List[str] = field(default_factory=list)
    ml_frameworks: List[str] = field(default_factory=list)
    cli_frameworks: List[str] = field(default_factory=list)
    has_notebooks: bool = False
    uses_poetry: bool = False
    uses_pipenv: bool = False
    uses_conda: bool = False
    migration_suggested: bool = False
    migration_paths: List[str] = field(default_factory=list)
    is_publishable: bool = False
    project_path: Optional[Path] = None
    analysis_timestamp: Optional[str] = None


@dataclass
class ValidationResult:
    """Configuration validation results."""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    summary: str = ""