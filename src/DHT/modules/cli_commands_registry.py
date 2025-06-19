#!/usr/bin/env python3

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Refactored to use helper modules to reduce file size
# - Imports command definitions from specialized modules
# - Maintains backward compatibility with original API
#

"""
CLI commands registry module for DHT.

This module provides a comprehensive registry of CLI commands for various
development tools. It includes:
- Command definitions for different operations (version, config, etc.)
- Category assignments matching the system taxonomy
- Format specifications for output parsing
- Platform restrictions for platform-specific tools

The registry is designed to be extensible and integrate with the system
taxonomy for platform-aware filtering.
"""

from typing import Any

from . import system_taxonomy
from .cli_commands_build_tools import BUILD_TOOLS_COMMANDS
from .cli_commands_devops import DEVOPS_COMMANDS
from .cli_commands_language_runtimes import LANGUAGE_RUNTIME_COMMANDS
from .cli_commands_package_managers import PACKAGE_MANAGER_COMMANDS
from .cli_commands_utilities import UTILITY_COMMANDS

# Import command definitions from helper modules
from .cli_commands_version_control import VERSION_CONTROL_COMMANDS

# Combine all commands into the main registry
CLI_COMMANDS: dict[str, dict[str, Any]] = {}

# Merge all command dictionaries
CLI_COMMANDS.update(VERSION_CONTROL_COMMANDS)
CLI_COMMANDS.update(LANGUAGE_RUNTIME_COMMANDS)
CLI_COMMANDS.update(PACKAGE_MANAGER_COMMANDS)
CLI_COMMANDS.update(BUILD_TOOLS_COMMANDS)
CLI_COMMANDS.update(DEVOPS_COMMANDS)
CLI_COMMANDS.update(UTILITY_COMMANDS)


def get_platform_specific_commands(platform: str | None = None) -> dict[str, dict[str, Any]]:
    """
    Get commands filtered by platform.

    Args:
        platform: Platform to filter for (uses current platform if None or empty)

    Returns:
        dict: Filtered commands for the specified platform
    """
    # Handle empty string or None
    if not platform:
        platform = system_taxonomy.get_current_platform()

    filtered_commands = {}

    for cmd_name, cmd_def in CLI_COMMANDS.items():
        # Check if command has platform restrictions
        if 'platforms' in cmd_def:
            # If platform is restricted, check if current platform is allowed
            if platform in cmd_def['platforms']:
                filtered_commands[cmd_name] = cmd_def
        else:
            # No platform restrictions, check with system taxonomy
            if system_taxonomy.is_tool_available_on_platform(cmd_name, platform):
                filtered_commands[cmd_name] = cmd_def

    return filtered_commands


def get_commands_by_category(category: str | None) -> dict[str, dict[str, Any]]:
    """
    Get commands filtered by category (supports partial matches).

    Args:
        category: Category to filter by (supports nested categories)

    Returns:
        dict: Commands matching the category
    """
    # Handle None category
    if category is None:
        return {}

    filtered_commands = {}

    for cmd_name, cmd_def in CLI_COMMANDS.items():
        cmd_category = cmd_def.get('category', '')

        # Check for exact match or if command category starts with requested category
        if cmd_category == category or cmd_category.startswith(category + '.'):
            filtered_commands[cmd_name] = cmd_def
        # Also check if requested category is a subcategory of command category
        elif category.startswith(cmd_category + '.'):
            filtered_commands[cmd_name] = cmd_def

    return filtered_commands
