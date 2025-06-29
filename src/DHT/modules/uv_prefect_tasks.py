#!/usr/bin/env python3
from __future__ import annotations

"""
UV Prefect Tasks Module.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

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


from DHT.modules.uv_build_tasks import (
    build_project,
)
from DHT.modules.uv_dependency_tasks import (
    add_dependency,
    generate_lock_file,
    install_dependencies,
    remove_dependency,
    sync_dependencies,
)
from DHT.modules.uv_environment_tasks import (
    create_virtual_environment,
    setup_project_environment,
)
from DHT.modules.uv_pip_tasks import (
    pip_install_project,
    pip_install_requirements,
)
from DHT.modules.uv_python_tasks import (
    check_uv_available,
    detect_python_version,
    ensure_python_version,
    list_python_versions,
)
from DHT.modules.uv_script_tasks import (
    run_python_script,
)

# Import all tasks from helper modules
from DHT.modules.uv_task_models import UVTaskError
from DHT.modules.uv_task_utils import (
    extract_min_python_version,
    find_uv_executable,
)

# Export all tasks and flows
__all__ = [
    # Utilities
    "find_uv_executable",
    "extract_min_python_version",
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
