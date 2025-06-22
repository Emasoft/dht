#!/usr/bin/env python3
"""
Dhtl Environment 3 module.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Python replacement for dhtl_environment_3.sh
# - Provides environment detection and setup
# - Cross-platform compatible
# - Removed duplicate find_project_root and detect_platform functions, now imported from common_utils
#

"""
DHT Dhtl Environment 3 Module.

Provides environment detection and setup functionality.
"""

import os

from .common_utils import detect_platform, find_project_root


def setup_environment() -> dict[str, str]:
    """Set up environment variables."""
    env = os.environ.copy()

    # Add DHT-specific variables
    project_root = find_project_root()
    env["PROJECT_ROOT"] = str(project_root)
    env["PLATFORM"] = detect_platform()

    return env
