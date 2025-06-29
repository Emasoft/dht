#!/usr/bin/env python3
"""
DHT Modules Package.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE FILE:
# - Created __init__.py for modules package
# - Exports main command modules and utilities
# - Import prefect_compat early to ensure Prefect 3.x compatibility
#

"""DHT Modules Package."""

# Import prefect_compat first to ensure Prefect 3.x compatibility patches are applied
from . import prefect_compat

# Version info
__version__ = "1.0.0"

# Export main modules
from .command_dispatcher import CommandDispatcher
from .command_registry import CommandRegistry
from .common_utils import detect_platform, find_project_root, find_virtual_env
from .dhtl_error_handling import log_debug, log_error, log_info, log_success, log_warning

__all__ = [
    "CommandDispatcher",
    "CommandRegistry",
    "find_project_root",
    "find_virtual_env",
    "detect_platform",
    "log_info",
    "log_error",
    "log_warning",
    "log_success",
    "log_debug",
    "prefect_compat",
]
