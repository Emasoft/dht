#!/usr/bin/env python3
"""
project_heuristics_quality.py - Code quality analysis and suggestions.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Extracted from project_heuristics.py to reduce file size
# - Contains code quality analysis logic
# - Follows CLAUDE.md modularity guidelines
#

import logging
from pathlib import Path
from typing import Any

from prefect import task

from .project_heuristics_patterns import CONFIG_TEMPLATES


class CodeQualityAnalyzer:
    """Handles code quality analysis and configuration suggestions."""

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

    @task  # type: ignore[misc]
    def suggest_configurations(
        self, project_type_info: dict[str, Any], analysis_result: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Suggest optimal configurations based on project type.

        Args:
            project_type_info: Output from detect_project_type
            analysis_result: Output from ProjectAnalyzer

        Returns:
            Configuration suggestions and templates
        """
        suggestions: dict[str, Any] = {
            "recommended_files": [],
            "config_templates": {},
            "best_practices": [],
            "missing_files": [],
        }

        primary_type = project_type_info.get("primary_type", "generic")
        characteristics = project_type_info.get("characteristics", [])

        # Get config templates for primary type
        if primary_type in CONFIG_TEMPLATES:
            suggestions["config_templates"] = CONFIG_TEMPLATES[primary_type]

        # Check for missing recommended files
        existing_files = {Path(f).name for f in self._extract_file_paths(analysis_result)}

        # Common recommendations
        if "pyproject.toml" not in existing_files:
            suggestions["missing_files"].append("pyproject.toml")
            suggestions["best_practices"].append("Use pyproject.toml for modern Python packaging")

        if ".gitignore" not in existing_files:
            suggestions["missing_files"].append(".gitignore")
            suggestions["best_practices"].append("Add .gitignore to exclude build artifacts")

        if "README.md" not in existing_files and "README.rst" not in existing_files:
            suggestions["missing_files"].append("README.md")
            suggestions["best_practices"].append("Add README for project documentation")

        # Type-specific recommendations
        if primary_type == "django":
            suggestions["recommended_files"].extend(
                [
                    ".env.example",
                    "requirements/base.txt",
                    "requirements/dev.txt",
                    "requirements/prod.txt",
                ]
            )
            suggestions["best_practices"].extend(
                [
                    "Use environment variables for sensitive settings",
                    "Split requirements by environment",
                    "Add django-debug-toolbar for development",
                ]
            )

        elif primary_type == "fastapi":
            suggestions["recommended_files"].extend(
                [
                    ".env.example",
                    "alembic.ini",
                    "docker-compose.yml",
                ]
            )
            suggestions["best_practices"].extend(
                [
                    "Use Alembic for database migrations",
                    "Implement proper CORS configuration",
                    "Add OpenAPI documentation",
                ]
            )

        elif primary_type == "flask":
            suggestions["recommended_files"].extend(
                [
                    ".env",
                    ".flaskenv",
                    "requirements.txt",
                ]
            )
            suggestions["best_practices"].extend(
                [
                    "Use Flask-Migrate for database migrations",
                    "Implement application factory pattern",
                    "Add Flask-CORS for API endpoints",
                ]
            )

        # Testing recommendations
        if "testing" in characteristics:
            if "pytest.ini" not in existing_files and "tox.ini" not in existing_files:
                suggestions["missing_files"].append("pytest.ini")
            suggestions["best_practices"].append("Configure pytest with coverage reporting")

        # CI/CD recommendations
        if not any(".github/workflows" in str(f) for f in self._extract_file_paths(analysis_result)):
            suggestions["recommended_files"].append(".github/workflows/tests.yml")
            suggestions["best_practices"].append("Add GitHub Actions for CI/CD")

        # Docker recommendations
        if "containerized" in characteristics or primary_type in ["fastapi", "django"]:
            if "Dockerfile" not in existing_files:
                suggestions["missing_files"].append("Dockerfile")
            if "docker-compose.yml" not in existing_files:
                suggestions["recommended_files"].append("docker-compose.yml")

        return suggestions

    @task  # type: ignore[misc]
    def analyze_code_quality(self, analysis_result: dict[str, Any]) -> dict[str, Any]:
        """
        Analyze code quality indicators and suggest improvements.

        Args:
            analysis_result: Output from ProjectAnalyzer

        Returns:
            Code quality metrics and suggestions
        """
        quality_indicators: dict[str, Any] = {
            "has_tests": False,
            "has_type_hints": False,
            "has_docstrings": False,
            "has_linting": False,
            "has_formatting": False,
            "test_coverage": "unknown",
            "suggestions": [],
        }

        file_analysis = analysis_result.get("file_analysis", {})
        existing_files = {Path(f).name for f in self._extract_file_paths(analysis_result)}

        # Check for tests
        test_files = [f for f in file_analysis if "test" in f.lower()]
        quality_indicators["has_tests"] = len(test_files) > 0

        # Check for type hints in Python files
        type_hint_count = 0
        total_functions = 0

        for file_path, file_data in file_analysis.items():
            if file_path.endswith(".py") and "functions" in file_data:
                for func in file_data.get("functions", []):
                    total_functions += 1
                    if func.get("has_type_hints"):
                        type_hint_count += 1

        if total_functions > 0:
            type_hint_ratio = type_hint_count / total_functions
            quality_indicators["has_type_hints"] = type_hint_ratio > 0.5
            quality_indicators["type_hint_coverage"] = f"{type_hint_ratio:.1%}"

        # Check for linting/formatting configs
        linting_configs = {
            ".flake8",
            "setup.cfg",
            ".pylintrc",
            "pyproject.toml",
            ".pre-commit-config.yaml",
            "ruff.toml",
        }
        quality_indicators["has_linting"] = bool(linting_configs & existing_files)

        formatting_configs = {".black", "pyproject.toml", ".yapfrc", ".style.yapf"}
        quality_indicators["has_formatting"] = bool(formatting_configs & existing_files)

        # Generate suggestions
        if not quality_indicators["has_tests"]:
            quality_indicators["suggestions"].append("Add unit tests with pytest")

        if not quality_indicators["has_type_hints"]:
            quality_indicators["suggestions"].append("Add type hints to improve code clarity")

        if not quality_indicators["has_linting"]:
            quality_indicators["suggestions"].append("Configure linting with ruff or flake8")

        if not quality_indicators["has_formatting"]:
            quality_indicators["suggestions"].append("Set up automatic formatting with black")

        if ".pre-commit-config.yaml" not in existing_files:
            quality_indicators["suggestions"].append("Add pre-commit hooks for code quality")

        return quality_indicators

    def _extract_file_paths(self, analysis_result: dict[str, Any]) -> list[str]:
        """Extract all file paths from analysis result."""
        file_paths: list[str] = []

        # From file_analysis section
        if "file_analysis" in analysis_result:
            file_paths.extend(analysis_result["file_analysis"].keys())

        # From structure section
        structure = analysis_result.get("structure", {})
        if "entry_points" in structure:
            file_paths.extend(structure["entry_points"])

        return file_paths
