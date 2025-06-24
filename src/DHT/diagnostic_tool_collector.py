#!/usr/bin/env python3
"""
diagnostic_tool_collector.py - Tool information collection utilities.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Extracted from diagnostic_reporter_v2.py to reduce file size
# - Contains tool detection and information collection
# - Supports parallel tool collection with ThreadPoolExecutor
# - Follows CLAUDE.md modularity guidelines
#

import os
import platform
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from DHT.modules import cli_commands_registry

from .diagnostic_parser_utils import add_unparsed_lines, extract_version, parse_command_output, snake_case


def run_command(cmd: str, timeout: int = 30) -> tuple[str, str | None]:
    """
    Execute a command and return (stdout, error).

    Args:
        cmd: Command to execute
        timeout: Timeout in seconds

    Returns:
        tuple: (stdout, error) where error is None on success
    """
    try:
        result = subprocess.run(cmd, capture_output=True, shell=True, text=True, timeout=timeout, env=os.environ.copy())

        if result.returncode == 0:
            return result.stdout, None
        else:
            error_msg = result.stderr or f"Command failed with return code {result.returncode}"
            return result.stdout, error_msg

    except subprocess.TimeoutExpired:
        return "", f"Command timed out after {timeout} seconds"
    except Exception as e:
        return "", str(e)


def check_tool_installed(tool_name: str) -> bool:
    """
    Check if a tool is installed by trying common lookup methods.

    Args:
        tool_name: Name of the tool to check

    Returns:
        bool: True if tool appears to be installed
    """
    # Method 1: Check if tool is in PATH
    if platform.system().lower() == "windows":
        check_cmd = f"where {tool_name}"
    else:
        check_cmd = f"which {tool_name}"

    stdout, error = run_command(check_cmd, timeout=5)
    if error is None and stdout.strip():
        return True

    # Method 2: Try running with --version
    version_cmd = f"{tool_name} --version"
    stdout, error = run_command(version_cmd, timeout=5)
    if error is None:
        return True

    # Method 3: Try running with version subcommand
    version_cmd = f"{tool_name} version"
    stdout, error = run_command(version_cmd, timeout=5)
    if error is None:
        return True

    return False


def collect_tool_info(tool_name: str, tool_spec: dict[str, Any]) -> dict[str, Any]:
    """
    Collect information about a specific tool.

    Args:
        tool_name: Name of the tool
        tool_spec: Tool specification from registry

    Returns:
        dict: Tool information including install status and command outputs
    """
    info: dict[str, Any] = {
        "is_installed": check_tool_installed(tool_name),
        "category": tool_spec.get("category", "unknown"),
    }

    if not info["is_installed"]:
        return info

    # Run each command defined for this tool
    commands = tool_spec.get("commands", {})
    format_hint = tool_spec.get("format", "auto")

    for cmd_name, cmd_template in commands.items():
        stdout, error = run_command(cmd_template)

        if error:
            info[f"{cmd_name}_error"] = error
            continue

        # Parse the output
        parsed_data, unparsed_lines = parse_command_output(stdout, format_hint)

        # If we got version info, extract it
        if cmd_name == "version" and not parsed_data.get("version"):
            version = extract_version(stdout)
            if version:
                parsed_data["version"] = version

        # Add any unparsed lines
        parsed_data = add_unparsed_lines(parsed_data, unparsed_lines)

        # Store parsed data with snake_case command name
        cmd_key = snake_case(cmd_name)
        if parsed_data:
            # Flatten single-field results
            if cmd_key == "version" and "version" in parsed_data:
                info["version"] = parsed_data["version"]
            else:
                info[cmd_key] = parsed_data

    return info


def insert_into_tree(tree: dict[str, Any], path: str, value: Any) -> None:
    """
    Insert a value into the tree at the specified path.

    Args:
        tree: Tree dictionary to modify
        path: Dot-separated path where to insert
        value: Value to insert
    """
    parts = path.split(".")
    current = tree

    for part in parts[:-1]:
        if part not in current:
            current[part] = {}
        current = current[part]

    current[parts[-1]] = value


def collect_all_tools(categories: list[str] | None = None, tools: list[str] | None = None) -> dict[str, Any]:
    """
    Collect information about all tools or filtered subset.

    Args:
        categories: List of categories to include (None for all)
        tools: List of specific tools to include (None for all)

    Returns:
        dict: Tree structure with tool information
    """
    # Get platform-specific commands
    platform_name = platform.system().lower()
    commands = cli_commands_registry.get_platform_specific_commands(platform_name)

    # Filter by categories if specified
    if categories:
        filtered_commands = {}
        for cat in categories:
            cat_commands = cli_commands_registry.get_commands_by_category(cat)
            filtered_commands.update(cat_commands)
        commands = {k: v for k, v in commands.items() if k in filtered_commands}

    # Filter by specific tools if specified
    if tools:
        commands = {k: v for k, v in commands.items() if k in tools}

    # Collect tool information in parallel
    tool_results = {}

    with ThreadPoolExecutor(max_workers=10) as executor:
        # Submit all tool collection tasks
        future_to_tool = {
            executor.submit(collect_tool_info, tool_name, tool_spec): (tool_name, tool_spec)
            for tool_name, tool_spec in commands.items()
        }

        # Collect results as they complete
        for future in as_completed(future_to_tool):
            tool_name, tool_spec = future_to_tool[future]
            try:
                tool_info = future.result()
                tool_results[tool_name] = tool_info
            except Exception as exc:
                tool_results[tool_name] = {
                    "is_installed": False,
                    "error": str(exc),
                    "category": tool_spec.get("category", "unknown"),
                }

    # Build the tree structure
    tree: dict[str, Any] = {}

    for tool_name, tool_info in tool_results.items():
        category = tool_info.get("category", "unknown")

        # Create the path for this tool
        # Convert category paths like "package_managers.language.python" to proper tree structure
        if category.startswith("package_managers.language."):
            # Special handling for language package managers
            parts = category.split(".")
            lang = parts[2] if len(parts) > 2 else "unknown"
            path = f"tools.package_managers.language.{lang}.{tool_name}"
        elif category.startswith("package_managers.system."):
            # Special handling for system package managers
            parts = category.split(".")
            sys_type = parts[2] if len(parts) > 2 else "unknown"
            path = f"tools.package_managers.system.{tool_name}"
        else:
            # Standard category path
            path = f"tools.{category}.{tool_name}"

        # Remove category from tool info since it's encoded in the path
        tool_info_clean = {k: v for k, v in tool_info.items() if k != "category"}

        insert_into_tree(tree, path, tool_info_clean)

    return tree
