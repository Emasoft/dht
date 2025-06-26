#!/usr/bin/env python3
"""
project_heuristics_analyzer.py - Project type detection and characteristic analysis.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Extracted from project_heuristics.py to reduce file size
# - Contains project type detection and characteristic analysis logic
# - Follows CLAUDE.md modularity guidelines
#

import logging
from typing import Any, cast

from prefect import task

from .project_heuristics_patterns import FRAMEWORK_PATTERNS


class ProjectTypeAnalyzer:
    """Handles project type detection and characteristic analysis."""

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

    @task
    def detect_project_type(self, analysis_result: dict[str, Any]) -> dict[str, Any]:
        """
        Detect the primary project type and characteristics.

        Args:
            analysis_result: Output from ProjectAnalyzer

        Returns:
            Dictionary with project type information and confidence scores
        """
        scores: dict[str, dict[str, Any]] = {}

        # Extract relevant data from analysis
        file_paths = self._extract_file_paths(analysis_result)
        imports = self._extract_all_imports(analysis_result)
        structure = analysis_result.get("structure", {})

        # Score each framework
        for framework, patterns in FRAMEWORK_PATTERNS.items():
            score = 0
            matches: list[str] = []

            # Check for marker files
            for marker_file in patterns["files"]:
                if any(marker_file in str(f) for f in file_paths):
                    # Give less weight to generic files
                    if marker_file in ["main.py", "app.py"] and framework in ["fastapi", "flask"]:
                        score += 2  # Reduced from 10
                    elif marker_file == "manage.py" and framework == "django":
                        score += 15  # manage.py is a strong Django indicator
                    elif marker_file in ["settings.py", "urls.py", "models.py"] and framework == "django":
                        score += 3  # Generic Django files get less weight
                    else:
                        score += 10
                    matches.append(f"file:{marker_file}")

            # Check for imports
            for import_pattern in patterns["imports"]:
                if import_pattern in imports:
                    score += 3  # Reduced from 5
                    matches.append(f"import:{import_pattern}")

            # Check structure hints
            for hint in patterns["structure_hints"]:
                if any(hint in str(f) for f in file_paths):
                    score += 2  # Reduced from 3
                    matches.append(f"structure:{hint}")

            # Check config files
            for config in patterns["config_files"]:
                if any(config in str(f) for f in file_paths):
                    score += 2
                    matches.append(f"config:{config}")

            if score > 0:
                scores[framework] = {
                    "score": score,
                    "matches": matches,
                    "confidence": min(score / 30.0, 1.0),  # Normalize to 0-1
                }

        # Detect additional project characteristics
        characteristics = self._detect_characteristics(file_paths, imports, analysis_result)

        # Sort frameworks by score
        ranked_frameworks = sorted(scores.items(), key=lambda x: cast(int, x[1]["score"]), reverse=True)

        result = {
            "primary_type": ranked_frameworks[0][0] if ranked_frameworks else "generic",
            "frameworks": dict(ranked_frameworks),
            "characteristics": characteristics,
            "confidence": ranked_frameworks[0][1]["confidence"] if ranked_frameworks else 0.0,
        }

        # Add project category
        if result["primary_type"] in ["django", "flask", "fastapi", "streamlit"]:
            result["category"] = "web"
        elif result["primary_type"] == "library":
            result["category"] = "library"
        elif "data_science" in characteristics:
            result["category"] = "data_science"
        elif "cli" in characteristics:
            result["category"] = "cli"
        elif "library" in characteristics:
            result["category"] = "library"
        else:
            result["category"] = "application"

        return result

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

    def _extract_all_imports(self, analysis_result: dict[str, Any]) -> set[str]:
        """Extract all unique imports from the analysis."""
        imports: set[str] = set()

        # From file analysis
        for file_data in analysis_result.get("file_analysis", {}).values():
            if "imports" in file_data:
                for imp in file_data["imports"]:
                    if isinstance(imp, dict):
                        module = imp.get("module", "")
                        if module:
                            imports.add(module)
                            # Also add parent modules for submodule matching
                            parts = module.split(".")
                            for i in range(1, len(parts)):
                                imports.add(".".join(parts[:i]))
                    else:
                        imports.add(str(imp))

        # From dependencies
        deps = analysis_result.get("dependencies", {})
        for lang_deps in deps.values():
            if isinstance(lang_deps, dict) and "all" in lang_deps:
                imports.update(lang_deps["all"])

        return imports

    def _detect_characteristics(
        self, file_paths: list[str], imports: set[str], analysis_result: dict[str, Any]
    ) -> list[str]:
        """Detect additional project characteristics."""
        characteristics: list[str] = []

        # Testing framework
        if any("test" in str(f) for f in file_paths):
            characteristics.append("testing")
            if "pytest" in imports:
                characteristics.append("pytest")
            elif "unittest" in imports:
                characteristics.append("unittest")

        # Data science indicators
        ml_imports = {"sklearn", "tensorflow", "torch", "keras", "pandas", "numpy"}
        if ml_imports & imports:
            characteristics.append("data_science")
            if any(".ipynb" in str(f) for f in file_paths):
                characteristics.append("notebooks")

        # CLI indicators
        cli_imports = {"click", "argparse", "typer", "fire"}
        if cli_imports & imports:
            characteristics.append("cli")

        # API indicators
        api_imports = {"fastapi", "flask", "django.rest_framework", "graphene"}
        if api_imports & imports:
            characteristics.append("api")

        # Database usage
        db_imports = {"sqlalchemy", "django.db", "pymongo", "redis", "psycopg2"}
        if db_imports & imports:
            characteristics.append("database")

        # Async programming
        if any("async def" in str(analysis_result.get("file_analysis", {}).get(f, {})) for f in file_paths):
            characteristics.append("async")

        # Containerization
        if any("Dockerfile" in str(f) or "docker-compose" in str(f) for f in file_paths):
            characteristics.append("containerized")

        # Library project
        # Check for package files in file paths directly
        has_package_files = any(
            "setup.py" in str(f) or "setup.cfg" in str(f) or "pyproject.toml" in str(f) for f in file_paths
        )

        if has_package_files:
            # Check if it's not a web framework project
            web_frameworks = {"django", "flask", "fastapi", "streamlit", "tornado", "aiohttp"}
            if not any(framework in imports for framework in web_frameworks):
                characteristics.append("library")

        return characteristics
