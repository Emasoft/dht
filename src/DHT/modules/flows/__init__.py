#!/usr/bin/env python3
"""
DHT Prefect Flows Package.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE FILE:
# - Initial creation of flows package
# - Central location for all Prefect flows and tasks
# - Exports all flows for easy importing
#

from .project_init_flow import initialize_project_flow
from .project_setup_flow import setup_project_flow
from .template_tasks import (
    generate_github_actions_task,
    generate_gitignore_task,
    generate_license_task,
    generate_pre_commit_config_task,
    generate_pyproject_toml_task,
    generate_readme_task,
)

__all__ = [
    "initialize_project_flow",
    "setup_project_flow",
    "generate_gitignore_task",
    "generate_license_task",
    "generate_github_actions_task",
    "generate_pyproject_toml_task",
    "generate_readme_task",
    "generate_pre_commit_config_task",
]
