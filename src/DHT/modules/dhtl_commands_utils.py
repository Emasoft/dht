#!/usr/bin/env python3
"""
dhtl_commands_utils.py - Shared utilities for dhtl commands

This module contains utilities shared by multiple dhtl command modules.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Created to share common functionality between command modules
# - Contains parse_requirements and other shared utilities
#

from pathlib import Path


def parse_requirements(requirements_path: Path) -> list[str]:
    """Parse requirements.txt file and return list of dependencies."""
    deps = []
    with open(requirements_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                deps.append(line)
    return deps


__all__ = ["parse_requirements"]
