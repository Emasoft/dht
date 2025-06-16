#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Refactored to use helper modules to reduce file size
# - Imports and re-exports all tasks from helper modules
# - Maintains backward compatibility with original API
# 

"""
UV Prefect Tasks Module.

This module provides Prefect task wrappers for all UV operations with proper
resource management, error handling, and monitoring capabilities.
"""

from __future__ import annotations

# Import all tasks from helper modules
from DHT.modules.uv_task_models import UVTaskError
from DHT.modules.uv_python_tasks import (
    check_uv_available,
    detect_python_version,
    list_python_versions,
    ensure_python_version,
)
from DHT.modules.uv_environment_tasks import (
    create_virtual_environment,
    setup_project_environment,
)
from DHT.modules.uv_dependency_tasks import (
    install_dependencies,
    sync_dependencies,
    generate_lock_file,
    add_dependency,
    remove_dependency,
)
from DHT.modules.uv_pip_tasks import (
    pip_install_requirements,
    pip_install_project,
)
from DHT.modules.uv_build_tasks import (
    build_project,
)
from DHT.modules.uv_script_tasks import (
    run_python_script,
)

# Export all tasks and flows
__all__ = [
    # Python version management
    "check_uv_available",
    "detect_python_version",
    "list_python_versions",
    "ensure_python_version",
    # Virtual environment management
    "create_virtual_environment",
    "setup_project_environment",
    # Dependency management
    "install_dependencies",
    "sync_dependencies",
    "generate_lock_file",
    "add_dependency",
    "remove_dependency",
    # Pip operations
    "pip_install_requirements",
    "pip_install_project",
    # Build operations
    "build_project",
    # Script execution
    "run_python_script",
    # Exceptions
    "UVTaskError",
]