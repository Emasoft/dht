#!/usr/bin/env python3
"""
project_analysis_models.py - Data models for project analysis  This module contains the data classes used for project analysis results and validation.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

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

from dataclasses import dataclass, field
from pathlib import Path

from DHT.modules.project_type_enums import ProjectCategory, ProjectType


@dataclass
class ProjectAnalysis:
    """Results of project type analysis."""

    type: ProjectType
    category: ProjectCategory
    confidence: float
    detected_types: list[ProjectType] = field(default_factory=list)
    markers: list[str] = field(default_factory=list)
    primary_dependencies: list[str] = field(default_factory=list)
    ml_frameworks: list[str] = field(default_factory=list)
    cli_frameworks: list[str] = field(default_factory=list)
    has_notebooks: bool = False
    uses_poetry: bool = False
    uses_pipenv: bool = False
    uses_conda: bool = False
    migration_suggested: bool = False
    migration_paths: list[str] = field(default_factory=list)
    is_publishable: bool = False
    project_path: Path | None = None
    analysis_timestamp: str | None = None


@dataclass
class ValidationResult:
    """Configuration validation results."""

    is_valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    summary: str = ""
