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

from .config_generation_tasks import (
    generate_django_settings_task,
    generate_docker_compose_task,
    generate_dockerfile_task,
    generate_env_file_task,
    generate_fastapi_main_task,
    generate_github_workflow_task,
    generate_makefile_task,
)
from .database_config_tasks import (
    generate_alembic_config_task,
    generate_mongodb_config_task,
    generate_redis_config_task,
    generate_sqlalchemy_config_task,
)
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
from .testing_config_tasks import (
    generate_coverage_config_task,
    generate_factory_boy_factories_task,
    generate_hypothesis_strategies_task,
    generate_pytest_config_task,
    generate_tox_config_task,
)

__all__ = [
    # Flows
    "initialize_project_flow",
    "setup_project_flow",
    # Basic templates
    "generate_gitignore_task",
    "generate_license_task",
    "generate_github_actions_task",
    "generate_pyproject_toml_task",
    "generate_readme_task",
    "generate_pre_commit_config_task",
    # Configuration generation
    "generate_django_settings_task",
    "generate_fastapi_main_task",
    "generate_dockerfile_task",
    "generate_docker_compose_task",
    "generate_env_file_task",
    "generate_makefile_task",
    "generate_github_workflow_task",
    # Database configuration
    "generate_alembic_config_task",
    "generate_sqlalchemy_config_task",
    "generate_redis_config_task",
    "generate_mongodb_config_task",
    # Testing configuration
    "generate_pytest_config_task",
    "generate_factory_boy_factories_task",
    "generate_coverage_config_task",
    "generate_tox_config_task",
    "generate_hypothesis_strategies_task",
]
