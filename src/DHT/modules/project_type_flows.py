#!/usr/bin/env python3
"""
project_type_flows.py - Prefect flows for project type detection  This module contains Prefect flows for orchestrating project type detection and configuration generation.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

"""
project_type_flows.py - Prefect flows for project type detection

This module contains Prefect flows for orchestrating project type detection
and configuration generation.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Extracted from project_type_detector.py to reduce file size
# - Contains the main flow for project detection and configuration
#

import logging
from pathlib import Path

from prefect import flow

from DHT.modules.project_analysis_models import ProjectAnalysis
from DHT.modules.project_type_detector import ProjectTypeDetector


@flow(name="detect_and_configure_project")  # type: ignore[misc]
def detect_and_configure_project(project_path: Path) -> tuple[ProjectAnalysis, dict[str, str]]:
    """
    Complete flow for project detection and configuration generation.

    Args:
        project_path: Path to project directory

    Returns:
        Tuple of analysis results and generated configurations
    """
    detector = ProjectTypeDetector()

    # Analyze project
    analysis = detector.analyze(project_path)

    # Generate configurations
    configs = detector.generate_configurations(analysis)

    # Validate configurations
    validation = detector.validate_configurations(configs, analysis)

    if not validation.is_valid:
        logger = logging.getLogger(__name__)
        for error in validation.errors:
            logger.error(f"Configuration error: {error}")

    return analysis, configs
