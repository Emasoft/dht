#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Python replacement for utils.sh
# - Contains command argument parsing and formatting utilities
# - Maintains compatibility with shell version functionality
# - Uses error handling from dhtl_error_handling.py
# 

"""
DHT Utils Module.

Contains utility functions for argument parsing and code formatting.
"""

import os
import shutil
from pathlib import Path
from typing import List, Tuple, Dict, Any

# Import from our modules
from .dhtl_error_handling import (
    log_error, log_warning, log_info, log_success
)
from .dhtl_environment_utils import find_project_root, find_virtual_env
from .dhtl_guardian_utils import run_with_guardian


def check_command_args(args: List[str]) -> Tuple[List[str], Dict[str, Any]]:
    """
    Check command line arguments for special flags.
    
    Args:
        args: List of command line arguments
        
    Returns:
        Tuple of (cleaned_args, options_dict)
        - cleaned_args: Arguments with special flags removed
        - options_dict: Dictionary with parsed options
    """
    options = {
        "use_guardian": True,
        "quiet_mode": False
    }
    
    cleaned_args = []
    
    for arg in args:
        if arg == "--no-guardian":
            options["use_guardian"] = False
        elif arg == "--quiet":
            options["quiet_mode"] = True
        else:
            cleaned_args.append(arg)
    
    # Also update environment variables for compatibility
    if not options["use_guardian"]:
        os.environ["USE_GUARDIAN"] = "false"
    
    if options["quiet_mode"]:
        os.environ["QUIET_MODE"] = "true"
    
    return cleaned_args, options


class FormatCommand:
    """Handler for the format command."""
    
    def __init__(self):
        """Initialize the format command handler."""
        # Get memory limit from environment
        self.python_mem_limit = int(os.environ.get("PYTHON_MEM_LIMIT", "2048"))
    
    def run(self) -> int:
        """
        Format code in the project using available formatters.
        
        Returns:
            0 if successful, 1 if errors occurred
        """
        log_info("🎨 Formatting code in project...")
        
        # Find project root
        project_root = find_project_root()
        
        # Find virtual environment
        venv_dir = find_virtual_env(project_root)
        if not venv_dir:
            venv_dir = project_root / ".venv"
        else:
            venv_dir = Path(venv_dir)
        
        # Check which formatters are available
        formatters = self._check_formatters(venv_dir)
        
        # Format code
        return self._run_formatters(project_root, venv_dir, formatters)
    
    def _check_formatters(self, venv_dir: Path) -> Dict[str, Tuple[bool, str]]:
        """
        Check which formatters are available.
        
        Returns:
            Dictionary mapping formatter names to (is_available, command_path)
        """
        formatters = {}
        
        # Check ruff
        if (venv_dir / "bin" / "ruff").exists():
            formatters["ruff"] = (True, str(venv_dir / "bin" / "ruff"))
        elif (venv_dir / "Scripts" / "ruff.exe").exists():
            formatters["ruff"] = (True, str(venv_dir / "Scripts" / "ruff.exe"))
        elif shutil.which("ruff"):
            formatters["ruff"] = (True, "ruff")
        else:
            formatters["ruff"] = (False, "")
        
        # Check black
        if (venv_dir / "bin" / "black").exists():
            formatters["black"] = (True, str(venv_dir / "bin" / "black"))
        elif (venv_dir / "Scripts" / "black.exe").exists():
            formatters["black"] = (True, str(venv_dir / "Scripts" / "black.exe"))
        elif shutil.which("black"):
            formatters["black"] = (True, "black")
        else:
            formatters["black"] = (False, "")
        
        # Check isort
        if (venv_dir / "bin" / "isort").exists():
            formatters["isort"] = (True, str(venv_dir / "bin" / "isort"))
        elif (venv_dir / "Scripts" / "isort.exe").exists():
            formatters["isort"] = (True, str(venv_dir / "Scripts" / "isort.exe"))
        elif shutil.which("isort"):
            formatters["isort"] = (True, "isort")
        else:
            formatters["isort"] = (False, "")
        
        return formatters
    
    def _run_formatters(self, project_root: Path, venv_dir: Path, 
                        formatters: Dict[str, Tuple[bool, str]]) -> int:
        """Run available formatters on the project."""
        format_errors = False
        
        log_info("🎨 Formatting Python files...")
        
        # First try ruff format
        if formatters["ruff"][0]:
            log_info("🔄 Running ruff format...")
            
            exit_code = run_with_guardian(
                formatters["ruff"][1], "ruff", self.python_mem_limit,
                "format", str(project_root)
            )
            
            if exit_code != 0:
                format_errors = True
                log_error("Ruff format encountered errors.")
            else:
                log_success("Ruff format completed successfully.")
        
        # Try black if ruff isn't available
        elif formatters["black"][0]:
            log_info("🔄 Running black...")
            
            exit_code = run_with_guardian(
                formatters["black"][1], "black", self.python_mem_limit,
                str(project_root)
            )
            
            if exit_code != 0:
                format_errors = True
                log_error("Black encountered errors.")
            else:
                log_success("Black completed successfully.")
        
        # Run isort if available and ruff wasn't used
        # (ruff format includes import sorting)
        if formatters["isort"][0] and not formatters["ruff"][0]:
            log_info("🔄 Running isort...")
            
            exit_code = run_with_guardian(
                formatters["isort"][1], "isort", self.python_mem_limit,
                str(project_root)
            )
            
            if exit_code != 0:
                format_errors = True
                log_error("Isort encountered errors.")
            else:
                log_success("Isort completed successfully.")
        
        # Check if any formatters were available
        if not any(f[0] for f in formatters.values()):
            log_warning("No Python formatters (ruff, black, isort) found.")
            log_warning("Consider running 'dhtl setup' or installing formatters manually.")
            return 1
        
        # Final result
        if not format_errors:
            log_success("All formatting completed successfully.")
            return 0
        else:
            log_warning("Some formatters encountered errors.")
            return 1


# Export convenience functions
def format_command() -> int:
    """Run the format command."""
    cmd = FormatCommand()
    return cmd.run()


# Note: file_exists_in_tree is already defined in dhtl_utils.py
# Importing it here for completeness
