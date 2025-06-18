#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Temporary stub module for guardian utilities
# - Will be replaced when converting guardian modules
# - Provides minimal implementation to avoid import errors
# 

"""
DHT Guardian Utils Module.

Provides guardian functionality using the converted guardian modules.
"""

import subprocess
from typing import List, Union

# Import from the converted guardian modules
from .dhtl_guardian_1 import run_with_guardian as _run_with_guardian_v1
from .dhtl_guardian_2 import ensure_process_guardian_running


def run_with_guardian(command: str, name: str, mem_limit: int, *args: str) -> int:
    """
    Run a command with memory limits.
    
    Args:
        command: The command to run
        name: Name for the process (ignored in stub)
        mem_limit: Memory limit in MB (ignored in stub)
        *args: Additional arguments for the command
        
    Returns:
        Exit code from the command
    """
    # Build full command
    cmd_list = [command] + list(args)
    
    try:
        # Run the command directly (no guardian features in stub)
        result = subprocess.run(cmd_list, check=False)
        return result.returncode
    except FileNotFoundError:
        print(f"❌ Error: Command not found: {command}")
        return 127
    except Exception as e:
        print(f"❌ Error running command: {e}")
        return 1