#!/usr/bin/env python3
"""
DHT Flows - Prefect-based implementations of DHT actions.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Initial creation of dht_flows package for Prefect-based DHT actions
# - Package structure for converting shell scripts to Prefect flows
#

"""
DHT Flows - Prefect-based implementations of DHT actions.

This package contains Prefect flows and tasks that replace shell script
implementations with modern Python-based workflow management.
"""

from pathlib import Path

# Import flows and tasks for easy access
from .restore_flow import (
    create_virtual_environment,
    detect_virtual_environment,
    find_project_root,
    install_dependencies,
    restore_dependencies_flow,
    verify_installation,
)
from .test_flow import (
    check_test_resources,
    discover_tests,
    parse_test_output,
    prepare_test_command,
    run_tests,
    test_command_flow,
)
from .utils import (
    get_default_resource_limits,
    get_venv_pip_path,
    get_venv_python_path,
    normalize_path_for_platform,
    safe_command_join,
    validate_project_path,
)

# Package metadata
__version__ = "0.1.0"
__all__ = [
    # Flows
    "restore_dependencies_flow",
    "test_command_flow",
    # Restore tasks
    "find_project_root",
    "detect_virtual_environment",
    "create_virtual_environment",
    "install_dependencies",
    "verify_installation",
    # Test tasks
    "check_test_resources",
    "discover_tests",
    "prepare_test_command",
    "run_tests",
    "parse_test_output",
    # Utilities
    "get_venv_python_path",
    "get_venv_pip_path",
    "safe_command_join",
    "normalize_path_for_platform",
    "get_default_resource_limits",
    "validate_project_path",
]

# Base paths
DHT_ROOT = Path(__file__).parent.parent.parent.parent
DHT_MODULES = DHT_ROOT / "DHT" / "modules"
