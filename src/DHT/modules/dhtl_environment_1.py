#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Python replacement for dhtl_environment_1.sh
# - Provides environment detection and setup
# - Cross-platform compatible
# - Removed duplicate find_project_root and detect_platform functions, now imported from common_utils
# 

"""
DHT Dhtl Environment 1 Module.

Provides environment detection and setup functionality.
"""

import os
import sys
import platform
from pathlib import Path
from typing import Optional, Dict, Any

from .common_utils import find_project_root, detect_platform
from .dhtl_error_handling import log_error, log_warning, log_info, log_success


def setup_environment() -> Dict[str, str]:
    """Set up environment variables."""
    env = os.environ.copy()
    
    # Add DHT-specific variables
    project_root = find_project_root()
    env["PROJECT_ROOT"] = str(project_root)
    env["PLATFORM"] = detect_platform()
    
    return env
