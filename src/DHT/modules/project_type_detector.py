#!/usr/bin/env python3
"""
project_type_detector.py - Comprehensive project type detection and configuration system

This module provides advanced project type detection, configuration generation,
and setup recommendations for various Python frameworks and project types.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Initial implementation of project type detector
# - Added ProjectType and ProjectCategory enums
# - Added comprehensive framework detection logic
# - Added configuration generation for multiple frameworks
# - Added setup recommendations system
# - Added migration detection from other package managers
# - Added support for hybrid projects
# - Integrated with project analyzer and heuristics
# - Refactored to reduce file size: extracted enums, models, framework configs, and config generators

import json
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime

from prefect import task

from DHT.modules.project_analyzer import ProjectAnalyzer
from DHT.modules.project_heuristics import ProjectHeuristics
from DHT.modules.project_type_enums import ProjectType, ProjectCategory
from DHT.modules.project_analysis_models import ProjectAnalysis, ValidationResult
from DHT.modules.framework_configs import FrameworkConfig
from DHT.modules.config_generators import (
    generate_django_configs,
    generate_fastapi_configs,
    generate_ml_configs,
    generate_library_configs,
    generate_cli_configs,
    generate_common_configs,
)
from DHT.modules.setup_recommendations import get_setup_recommendations
from DHT.modules.project_type_detection_helpers import (
    get_all_dependencies,
    get_primary_dependencies,
    detect_ml_frameworks,
    detect_cli_frameworks,
    has_notebooks,
    is_publishable_library,
    extract_markers,
    check_for_react_vue,
    calculate_confidence_boost,
    detect_project_type,
    determine_category,
)


class ProjectTypeDetector:
    """
    Advanced project type detection system that analyzes project structure,
    dependencies, and code patterns to determine project type and generate
    appropriate configurations.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.analyzer = ProjectAnalyzer()
        self.heuristics = ProjectHeuristics()
    
    @task
    def analyze(self, project_path: Path) -> ProjectAnalysis:
        """
        Analyze project and detect its type with confidence scoring.
        
        Args:
            project_path: Path to project directory
            
        Returns:
            ProjectAnalysis with detection results
        """
        project_path = Path(project_path)
        
        # Run project analyzer
        analysis_result = self.analyzer.analyze_project(project_path)
        
        # Add project path to analysis result for file access
        analysis_result["project_path"] = str(project_path)
        
        # Run heuristics
        heuristic_result = self.heuristics.analyze(analysis_result)
        
        # Detect project type
        project_type, detected_types = detect_project_type(
            analysis_result, heuristic_result
        )
        
        # Determine category
        category = determine_category(project_type, detected_types)
        
        # Calculate confidence
        confidence = self._calculate_confidence(
            project_type, analysis_result, heuristic_result
        )
        
        # Extract markers
        markers = extract_markers(analysis_result, heuristic_result)
        
        # Get primary dependencies
        primary_deps = get_primary_dependencies(analysis_result)
        
        # Check for special characteristics
        ml_frameworks = detect_ml_frameworks(analysis_result)
        cli_frameworks = detect_cli_frameworks(analysis_result)
        has_notebooks_flag = has_notebooks(analysis_result)
        
        # Check package managers
        uses_poetry = (project_path / "poetry.lock").exists()
        uses_pipenv = (project_path / "Pipfile.lock").exists()
        uses_conda = (project_path / "environment.yml").exists()
        
        # Check if migration needed
        migration_suggested = uses_poetry or uses_pipenv or uses_conda
        migration_paths = []
        if uses_poetry:
            migration_paths.append("poetry_to_uv")
        if uses_pipenv:
            migration_paths.append("pipenv_to_uv")
        if uses_conda:
            migration_paths.append("conda_to_uv")
        
        # Check if publishable
        is_publishable_flag = is_publishable_library(
            project_type, analysis_result
        )
        
        return ProjectAnalysis(
            type=project_type,
            category=category,
            confidence=confidence,
            detected_types=detected_types,
            markers=markers,
            primary_dependencies=primary_deps,
            ml_frameworks=ml_frameworks,
            cli_frameworks=cli_frameworks,
            has_notebooks=has_notebooks_flag,
            uses_poetry=uses_poetry,
            uses_pipenv=uses_pipenv,
            uses_conda=uses_conda,
            migration_suggested=migration_suggested,
            migration_paths=migration_paths,
            is_publishable=is_publishable_flag,
            project_path=project_path,
            analysis_timestamp=datetime.now().isoformat()
        )
    
    @task
    def generate_configurations(
        self, 
        analysis: ProjectAnalysis
    ) -> dict[str, str]:
        """
        Generate configuration files based on project type.
        
        Args:
            analysis: Project analysis results
            
        Returns:
            Dictionary of filename to file content
        """
        configs = {}
        
        if analysis.type == ProjectType.DJANGO:
            configs.update(generate_django_configs(analysis))
        elif analysis.type == ProjectType.FASTAPI:
            configs.update(generate_fastapi_configs(analysis))
        elif analysis.type == ProjectType.DATA_SCIENCE:
            configs.update(generate_ml_configs(analysis))
        elif analysis.type == ProjectType.LIBRARY:
            configs.update(generate_library_configs(analysis))
        elif analysis.type == ProjectType.CLI:
            configs.update(generate_cli_configs(analysis))
        
        # Add common configs
        configs.update(generate_common_configs(analysis))
        
        return configs
    
    @task
    def get_setup_recommendations(
        self, 
        analysis: ProjectAnalysis
    ) -> dict[str, Any]:
        """
        Get setup recommendations based on project type.
        
        Args:
            analysis: Project analysis results
            
        Returns:
            Dictionary of recommendations by category
        """
        return get_setup_recommendations(analysis)
    
    @task
    def validate_configurations(
        self,
        configs: dict[str, str],
        analysis: ProjectAnalysis
    ) -> ValidationResult:
        """
        Validate generated configurations.
        
        Args:
            configs: Generated configuration files
            analysis: Project analysis results
            
        Returns:
            Validation results
        """
        errors = []
        warnings = []
        
        # Validate required files exist
        if analysis.type == ProjectType.DJANGO:
            if "pyproject.toml" not in configs:
                errors.append("Missing pyproject.toml for Django project")
            if ".env.example" not in configs:
                warnings.append("Missing .env.example file")
        
        # Validate Docker configs for API projects
        if analysis.category == ProjectCategory.WEB_API:
            if "Dockerfile" not in configs:
                warnings.append("API project should have Dockerfile")
        
        # More validation logic...
        
        is_valid = len(errors) == 0
        summary = "All configurations valid" if is_valid else f"{len(errors)} errors found"
        
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            summary=summary
        )
    
    
    
    def _calculate_confidence(
        self,
        project_type: ProjectType,
        analysis_result: dict[str, Any],
        heuristic_result: dict[str, Any]
    ) -> float:
        """Calculate confidence score for detection."""
        base_confidence = heuristic_result["project_type"]["confidence"]
        
        # Calculate confidence boost based on markers
        confidence_boost = calculate_confidence_boost(
            project_type, analysis_result, heuristic_result
        )
        
        # Calculate markers count for minimum confidence thresholds
        # This is a simplified version - the actual marker counting is in the helper
        markers = int(confidence_boost / 0.04)  # Reverse calculation from boost
        
        # Calculate final confidence, capped at 1.0
        final_confidence = min(base_confidence + confidence_boost, 1.0)
        
        # Round to avoid floating point precision issues (e.g., 0.6000000000000001)
        final_confidence = round(final_confidence, 3)
        
        # Don't override the calculated confidence, just ensure minimums
        # This allows confidence to drop when markers are removed
        return final_confidence
