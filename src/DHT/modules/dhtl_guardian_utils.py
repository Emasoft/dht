#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Temporary stub module for guardian utilities
# - Will be replaced when converting guardian modules
# - Provides minimal implementation to avoid import errors
# 

"""
DHT Guardian Utils Module (Stub).

Temporary stub module that will be replaced when converting guardian modules.
"""

import subprocess
from typing import List, Union


def run_with_guardian(command: str, name: str, mem_limit: int, *args: str) -> int:
    """
    Run a command with memory limits (stub implementation).
    
    This is a stub that directly runs the command without guardian features.
    Will be replaced when guardian modules are converted.
    
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