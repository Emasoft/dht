#!/usr/bin/env python3
"""
project_heuristics.py - Intelligent project type detection and configuration inference  This module provides heuristics for: - Detecting project types (Django, Flask, FastAPI, etc.) - Inferring system dependencies from imports - Suggesting optimal configurations - Identifying best practices and patterns

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

"""
project_heuristics.py - Intelligent project type detection and configuration inference

This module provides heuristics for:
- Detecting project types (Django, Flask, FastAPI, etc.)
- Inferring system dependencies from imports
- Suggesting optimal configurations
- Identifying best practices and patterns
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Initial implementation of project heuristics module
# - Added project type detection for Python frameworks
# - Added system dependency inference from imports
# - Added configuration suggestions based on project type
# - Integrated with project analyzer output
# - Added support for data science and CLI projects
# - Added complete type annotations to fix mypy errors
# - Refactored into smaller modules to comply with 10KB file size limit
# - Delegates to specialized analyzer modules
#

import logging
from typing import Any, cast

from prefect import flow

from .project_heuristics_analyzer import ProjectTypeAnalyzer
from .project_heuristics_deps import DependencyInferrer
from .project_heuristics_quality import CodeQualityAnalyzer


class ProjectHeuristics:
    """
    Analyzes project structure and content to make intelligent inferences
    about project type, dependencies, and optimal configuration.

    This class now delegates to specialized analyzers to maintain
    modularity and keep file sizes under 10KB.
    """

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self.type_analyzer = ProjectTypeAnalyzer()
        self.dep_inferrer = DependencyInferrer()
        self.quality_analyzer = CodeQualityAnalyzer()

    def detect_project_type(self, analysis_result: dict[str, Any]) -> dict[str, Any]:
        """
        Detect the primary project type and characteristics.
        Delegates to ProjectTypeAnalyzer.

        Args:
            analysis_result: Output from ProjectAnalyzer

        Returns:
            Dictionary with project type information and confidence scores
        """
        return cast(dict[str, Any], self.type_analyzer.detect_project_type(analysis_result))

    def infer_system_dependencies(self, analysis_result: dict[str, Any]) -> dict[str, Any]:
        """
        Infer system dependencies based on Python imports.
        Delegates to DependencyInferrer.

        Args:
            analysis_result: Output from ProjectAnalyzer

        Returns:
            Dictionary mapping dependency names to system packages
        """
        return cast(dict[str, Any], self.dep_inferrer.infer_system_dependencies(analysis_result))

    def suggest_configurations(
        self, project_type_info: dict[str, Any], analysis_result: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Suggest optimal configurations based on project type.
        Delegates to CodeQualityAnalyzer.

        Args:
            project_type_info: Output from detect_project_type
            analysis_result: Output from ProjectAnalyzer

        Returns:
            Configuration suggestions and templates
        """
        return cast(dict[str, Any], self.quality_analyzer.suggest_configurations(project_type_info, analysis_result))

    def analyze_code_quality(self, analysis_result: dict[str, Any]) -> dict[str, Any]:
        """
        Analyze code quality indicators and suggest improvements.
        Delegates to CodeQualityAnalyzer.

        Args:
            analysis_result: Output from ProjectAnalyzer

        Returns:
            Code quality metrics and suggestions
        """
        return cast(dict[str, Any], self.quality_analyzer.analyze_code_quality(analysis_result))

    @flow(name="analyze_project_heuristics")  # type: ignore[misc]
    def analyze(self, analysis_result: dict[str, Any]) -> dict[str, Any]:
        """
        Run complete heuristic analysis on a project.

        Args:
            analysis_result: Output from ProjectAnalyzer

        Returns:
            Complete heuristic analysis including type, dependencies, and suggestions
        """
        # Detect project type
        project_type = self.detect_project_type(analysis_result)

        # Infer system dependencies
        system_deps = self.infer_system_dependencies(analysis_result)

        # Suggest configurations
        config_suggestions = self.suggest_configurations(project_type, analysis_result)

        # Analyze code quality
        quality_analysis = self.analyze_code_quality(analysis_result)

        return {
            "project_type": project_type,
            "system_dependencies": system_deps,
            "configuration_suggestions": config_suggestions,
            "code_quality": quality_analysis,
            "analysis_timestamp": analysis_result.get("analysis_timestamp"),
        }
