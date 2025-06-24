#!/usr/bin/env python3
"""
diagnostic_parser_utils.py - Output parsing utilities for diagnostic reporter.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Extracted from diagnostic_reporter_v2.py to reduce file size
# - Contains command output parsing utilities
# - Supports JSON, YAML, key-value, and auto-detection parsing
# - Follows CLAUDE.md modularity guidelines
#

import json
import re
from typing import Any

# Try to import optional dependencies
try:
    import yaml

    HAS_YAML = True
except ImportError:
    HAS_YAML = False


def snake_case(s: str) -> str:
    """
    Convert a string to snake_case.

    Args:
        s: Input string

    Returns:
        str: Snake case version
    """
    # Replace spaces and dashes with underscores
    s = re.sub(r"[\s\-]+", "_", s)
    # Insert underscore before uppercase letters
    s = re.sub(r"([a-z])([A-Z])", r"\1_\2", s)
    return s.lower()


def coerce_value(value: str) -> Any:
    """
    Coerce a string value to an appropriate type.

    Args:
        value: String value to coerce

    Returns:
        Coerced value (bool, int, float, or str)
    """
    # Boolean values
    if value.lower() in ("true", "yes", "on", "enabled"):
        return True
    if value.lower() in ("false", "no", "off", "disabled"):
        return False

    # Numeric values
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        pass

    return value


def extract_version(text: str) -> str | None:
    """
    Extract version from text using common patterns.

    Args:
        text: Text to search for version

    Returns:
        str: Version string or None if not found
    """
    # Common version patterns
    patterns = [
        r"(?:version|v)\s+(\d+(?:\.\d+)*(?:[-\w]+)?)",  # version 1.2.3 or v1.2.3
        r"(\d+\.\d+(?:\.\d+)*(?:[-\w]+)?)",  # Just numbers like 1.2.3
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)

    return None


def parse_json_output(text: str) -> tuple[dict[str, Any], list[str]]:
    """Parse JSON output from command."""
    try:
        data = json.loads(text)
        return data if isinstance(data, dict) else {"data": data}, []
    except json.JSONDecodeError:
        return {}, []


def parse_yaml_output(text: str) -> tuple[dict[str, Any], list[str]]:
    """Parse YAML output from command."""
    if not HAS_YAML:
        return {}, []
    try:
        data = yaml.safe_load(text)
        return data if isinstance(data, dict) else {"data": data}, []
    except yaml.YAMLError:
        return {}, []


def parse_key_value_output(text: str) -> tuple[dict[str, Any], list[str]]:
    """
    Parse key-value output (like 'key: value' or 'key = value').

    Returns:
        tuple: (parsed_data, unparsed_lines)
    """
    data = {}
    unparsed = []

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue

        # Try different key-value patterns
        patterns = [
            r"^([^:=]+)[:\s]+(.+)$",  # key: value
            r"^([^=]+)=(.+)$",  # key=value
        ]

        matched = False
        for pattern in patterns:
            match = re.match(pattern, line)
            if match:
                key = snake_case(match.group(1).strip())
                value = coerce_value(match.group(2).strip())
                data[key] = value
                matched = True
                break

        if not matched:
            unparsed.append(line)

    return data, unparsed


def parse_auto_output(text: str) -> tuple[dict[str, Any], list[str]]:
    """
    Automatically detect and parse output format.

    Returns:
        tuple: (parsed_data, unparsed_lines)
    """
    # Try JSON first
    data, unparsed = parse_json_output(text)
    if data:
        return data, unparsed

    # Try YAML
    data, unparsed = parse_yaml_output(text)
    if data:
        return data, unparsed

    # Fall back to key-value
    return parse_key_value_output(text)


def parse_command_output(text: str, format_hint: str = "auto") -> tuple[dict[str, Any], list[str]]:
    """
    Parse command output based on format hint.

    Args:
        text: Output text to parse
        format_hint: Format hint (json, yaml, keyvalue, auto)

    Returns:
        tuple: (parsed_data, unparsed_lines)
    """
    if format_hint == "json":
        return parse_json_output(text)
    elif format_hint == "yaml":
        return parse_yaml_output(text)
    elif format_hint == "keyvalue":
        return parse_key_value_output(text)
    else:
        return parse_auto_output(text)


def add_unparsed_lines(data: dict[str, Any], lines: list[str]) -> dict[str, Any]:
    """
    Add unparsed lines to data dict as additional_info if any exist.

    Args:
        data: Parsed data dictionary
        lines: List of unparsed lines

    Returns:
        dict: Updated data dictionary
    """
    if lines:
        data["additional_info"] = lines
    return data
