#!/usr/bin/env python3
"""
project_type_detection_helpers.py - Helper functions for project type detection

This module contains helper functions used by the ProjectTypeDetector class
for analyzing projects and extracting information.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Extracted from project_type_detector.py to reduce file size
# - Contains helper methods for dependency analysis, framework detection, etc.
#

import json
from pathlib import Path
from typing import Any

from DHT.modules.project_type_enums import ProjectCategory, ProjectType


def get_all_dependencies(analysis_result: dict[str, Any]) -> set[str]:
    """Get all project dependencies."""
    deps = set()

    dep_data = analysis_result.get("dependencies", {})
    for _lang, lang_deps in dep_data.items():
        if isinstance(lang_deps, dict):
            deps.update(lang_deps.get("all", []))
            deps.update(lang_deps.get("runtime", []))
            deps.update(lang_deps.get("dev", []))

    return deps


def get_primary_dependencies(analysis_result: dict[str, Any]) -> list[str]:
    """Get primary project dependencies."""
    deps = get_all_dependencies(analysis_result)

    # Filter to primary/framework dependencies
    primary = []
    framework_deps = {"django", "flask", "fastapi", "streamlit", "gradio", "uvicorn", "gunicorn", "celery"}

    for dep in deps:
        dep_lower = dep.lower()
        if any(fw in dep_lower for fw in framework_deps):
            primary.append(dep)

    return primary


def detect_ml_frameworks(analysis_result: dict[str, Any]) -> list[str]:
    """Detect machine learning frameworks."""
    ml_frameworks = []
    deps = get_all_dependencies(analysis_result)

    framework_names = {"tensorflow", "torch", "pytorch", "keras", "scikit-learn", "sklearn", "xgboost", "lightgbm"}

    for dep in deps:
        dep_lower = dep.lower()
        for fw in framework_names:
            if fw in dep_lower:
                ml_frameworks.append(dep)
                break

    return list(set(ml_frameworks))


def detect_cli_frameworks(analysis_result: dict[str, Any]) -> list[str]:
    """Detect CLI frameworks."""
    cli_frameworks = []
    deps = get_all_dependencies(analysis_result)

    cli_names = {"click", "typer", "fire", "argparse"}

    for dep in deps:
        dep_lower = dep.lower()
        if dep_lower in cli_names:
            cli_frameworks.append(dep)

    # Also check imports
    for file_data in analysis_result.get("file_analysis", {}).values():
        for imp in file_data.get("imports", []):
            module = imp.get("module", "") if isinstance(imp, dict) else str(imp)
            if module in cli_names:
                cli_frameworks.append(module)

    return list(set(cli_frameworks))


def has_notebooks(analysis_result: dict[str, Any]) -> bool:
    """Check if project has Jupyter notebooks."""
    # Check in file analysis
    for file_path in analysis_result.get("file_analysis", {}):
        if file_path.endswith(".ipynb"):
            return True

    # Also check in all collected files
    files = analysis_result.get("files", [])
    for file_info in files:
        if isinstance(file_info, dict) and file_info.get("path", "").endswith(".ipynb"):
            return True
        elif isinstance(file_info, str) and file_info.endswith(".ipynb"):
            return True

    # Check in project path if we have it
    project_path = analysis_result.get("project_path")
    if project_path:
        project_dir = Path(project_path)
        if project_dir.exists():
            for _ipynb in project_dir.rglob("*.ipynb"):
                return True

    return False


def is_publishable_library(project_type: ProjectType, analysis_result: dict[str, Any]) -> bool:
    """Check if project is a publishable library."""
    if project_type != ProjectType.LIBRARY:
        return False

    # Check configurations from analyzer
    configs = analysis_result.get("configurations", {})

    # A library is publishable if it has package metadata files
    has_pyproject = configs.get("has_pyproject", False)
    has_setup_py = configs.get("has_setup_py", False)

    # Also check in file paths
    file_paths = list(analysis_result.get("file_analysis", {}).keys())
    has_setup_cfg = any("setup.cfg" in f for f in file_paths)

    return has_pyproject or has_setup_py or has_setup_cfg


def extract_markers(analysis_result: dict[str, Any], heuristic_result: dict[str, Any]) -> list[str]:
    """Extract project markers."""
    markers = []

    # Get entry points
    structure = analysis_result.get("structure", {})
    entry_points = structure.get("entry_points", [])
    markers.extend(entry_points)

    # Get framework matches from heuristics
    frameworks = heuristic_result["project_type"].get("frameworks", {})
    for _framework, info in frameworks.items():
        markers.extend(info.get("matches", []))

    return list(set(markers))


def check_for_react_vue(analysis_result: dict[str, Any]) -> list[ProjectType]:
    """Check for React or Vue in the project."""
    detected_types = []

    # First check file_analysis if package.json was analyzed
    file_analysis = analysis_result.get("file_analysis", {})
    for file_path, file_data in file_analysis.items():
        if "package.json" in file_path:
            # The analyzer might have already parsed it
            if "parsed_content" in file_data:
                pkg = file_data["parsed_content"]
                deps = pkg.get("dependencies", {})
                if "react" in deps:
                    detected_types.append(ProjectType.REACT)
                if "vue" in deps:
                    detected_types.append(ProjectType.VUE)
                return detected_types  # Found and parsed, we're done

    # If not in file_analysis, check if package.json exists in the project
    project_path = analysis_result.get("project_path")
    if project_path:
        package_json_path = Path(project_path) / "package.json"
        if package_json_path.exists():
            try:
                with open(package_json_path) as f:
                    pkg = json.load(f)
                    deps = pkg.get("dependencies", {})
                    if "react" in deps:
                        detected_types.append(ProjectType.REACT)
                    if "vue" in deps:
                        detected_types.append(ProjectType.VUE)
            except Exception:
                pass

    return detected_types


def calculate_confidence_boost(
    project_type: ProjectType, analysis_result: dict[str, Any], heuristic_result: dict[str, Any]
) -> float:
    """Calculate confidence score boost based on markers found."""
    markers = 0
    structure = analysis_result.get("structure", {})
    file_paths = list(analysis_result.get("file_analysis", {}).keys())

    if project_type == ProjectType.DJANGO:
        # Check for Django-specific files
        entry_points = structure.get("entry_points", [])
        if any("manage.py" in str(ep) for ep in entry_points):
            markers += 1  # manage.py is a strong indicator but count once

        # Also check in project structure for Django detection
        frameworks = analysis_result.get("frameworks", [])
        if "django" in frameworks:
            markers += 2  # Framework was detected by analyzer

        # Check for Django files
        if any("settings.py" in f for f in file_paths):
            markers += 1
        if any("urls.py" in f for f in file_paths):
            markers += 1
        if any("models.py" in f for f in file_paths):
            markers += 1

        # Check for Django in dependencies
        deps = get_all_dependencies(analysis_result)
        if any("django" in d.lower() for d in deps):
            markers += 1

    elif project_type == ProjectType.FASTAPI:
        # Check for FastAPI markers
        if any("main.py" in f or "app.py" in f for f in file_paths):
            markers += 2
        if any("routers" in f for f in file_paths):
            markers += 1
        if any("models" in f for f in file_paths):
            markers += 1

        # Check dependencies
        deps = get_all_dependencies(analysis_result)
        if any("fastapi" in d.lower() for d in deps):
            markers += 3
        if any("uvicorn" in d.lower() for d in deps):
            markers += 1

    elif project_type == ProjectType.DATA_SCIENCE:
        # Check for data science markers
        characteristics = heuristic_result["project_type"].get("characteristics", [])
        if "data_science" in characteristics:
            markers += 3
        if "notebooks" in characteristics:
            markers += 2

        # Check for ML frameworks
        deps = get_all_dependencies(analysis_result)
        ml_deps = {"tensorflow", "torch", "pytorch", "sklearn", "scikit-learn", "keras"}
        for dep in deps:
            if any(ml in dep.lower() for ml in ml_deps):
                markers += 1

        # Check for data directories
        if any("data" in str(f) for f in file_paths):
            markers += 1
        if any("models" in str(f) for f in file_paths):
            markers += 1
        if any("notebooks" in str(f) for f in file_paths):
            markers += 1

    # Boost confidence based on markers
    # Each marker adds 0.04, with max boost of 0.25
    confidence_boost = min(markers * 0.04, 0.25)

    return confidence_boost


def detect_project_type(
    analysis_result: dict[str, Any], heuristic_result: dict[str, Any]
) -> tuple[ProjectType, list[ProjectType]]:
    """Detect project type from analysis results."""
    detected_types = []

    # Get all detected frameworks from heuristics
    frameworks = heuristic_result["project_type"].get("frameworks", {})

    # Map heuristic types to our enum
    type_mapping = {
        "django": ProjectType.DJANGO,
        "flask": ProjectType.FLASK,
        "fastapi": ProjectType.FASTAPI,
        "streamlit": ProjectType.STREAMLIT,
        "library": ProjectType.LIBRARY,
        "data_science": ProjectType.DATA_SCIENCE,
        "generic": ProjectType.GENERIC,
    }

    # Check all frameworks that meet minimum confidence
    for fw_name, fw_data in frameworks.items():
        fw_confidence = fw_data.get("confidence", 0.0)
        min_confidence = 0.15 if fw_name in ["fastapi", "django", "flask", "data_science"] else 0.3

        if fw_confidence >= min_confidence:
            fw_type = type_mapping.get(fw_name)
            if fw_type and fw_type not in detected_types:
                detected_types.append(fw_type)

    # Get primary type from heuristics
    primary_type = heuristic_result["project_type"]["primary_type"]
    primary_confidence = heuristic_result["project_type"].get("confidence", 0.0)

    # Determine main project type
    if detected_types:
        # Use the first detected type as primary
        project_type = detected_types[0]
    else:
        project_type = ProjectType.GENERIC
        detected_types.append(project_type)

    # Check for additional types
    # Check for React/Vue
    react_vue_types = check_for_react_vue(analysis_result)
    detected_types.extend(react_vue_types)

    # Check for Django REST
    deps = get_all_dependencies(analysis_result)
    if "djangorestframework" in deps and project_type == ProjectType.DJANGO:
        project_type = ProjectType.DJANGO_REST

    # Check for ML/DS
    characteristics = heuristic_result["project_type"].get("characteristics", [])
    if "data_science" in characteristics:
        if project_type == ProjectType.GENERIC:
            project_type = ProjectType.DATA_SCIENCE
        detected_types.append(ProjectType.DATA_SCIENCE)

    # Check for CLI first (more specific than library)
    if "cli" in characteristics:
        # CLI takes precedence over library
        if project_type in [ProjectType.GENERIC, ProjectType.LIBRARY]:
            project_type = ProjectType.CLI
        detected_types.append(ProjectType.CLI)

    # Check for library (only if not already CLI)
    elif "library" in characteristics and project_type == ProjectType.GENERIC:
        project_type = ProjectType.LIBRARY
        detected_types.append(ProjectType.LIBRARY)

    # Handle hybrid projects
    if len(detected_types) > 1 and ProjectType.GENERIC not in detected_types:
        # Multiple web frameworks = Hybrid
        web_frameworks = {ProjectType.DJANGO, ProjectType.DJANGO_REST, ProjectType.FLASK, ProjectType.FASTAPI}
        detected_web = [t for t in detected_types if t in web_frameworks]

        # Django + React/Vue = Full stack
        if ProjectType.DJANGO in detected_types and (
            ProjectType.REACT in detected_types or ProjectType.VUE in detected_types
        ):
            project_type = ProjectType.HYBRID
        # Multiple backend frameworks = Hybrid
        elif len(detected_web) > 1:
            project_type = ProjectType.HYBRID

    return project_type, detected_types


def determine_category(project_type: ProjectType, detected_types: list[ProjectType]) -> ProjectCategory:
    """Determine project category from type."""
    if project_type == ProjectType.HYBRID:
        return ProjectCategory.FULL_STACK

    category_mapping = {
        ProjectType.DJANGO: ProjectCategory.WEB_FRAMEWORK,
        ProjectType.DJANGO_REST: ProjectCategory.WEB_API,
        ProjectType.FLASK: ProjectCategory.WEB_FRAMEWORK,
        ProjectType.FASTAPI: ProjectCategory.WEB_API,
        ProjectType.STREAMLIT: ProjectCategory.DATA_ANALYSIS,
        ProjectType.DATA_SCIENCE: ProjectCategory.MACHINE_LEARNING,
        ProjectType.MACHINE_LEARNING: ProjectCategory.MACHINE_LEARNING,
        ProjectType.CLI: ProjectCategory.COMMAND_LINE,
        ProjectType.LIBRARY: ProjectCategory.PACKAGE,
    }

    return category_mapping.get(project_type, ProjectCategory.UNKNOWN)
