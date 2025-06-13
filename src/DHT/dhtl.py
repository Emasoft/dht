#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Minimal entry point for DHT
# - Delegates to DHTLauncher class for actual functionality
# - Keeps file size under 10KB as per CLAUDE.md
# 

"""
Development Helper Toolkit Launcher (DHTL) - Main Entry Point

This is the minimal entry point for DHT that delegates to the launcher class.
It maintains the shell-based architecture while providing Python coordination.
"""

import sys
import argparse
try:
    from .launcher import DHTLauncher
except ImportError:
    # Handle script execution
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))
    from launcher import DHTLauncher

# Version information
__version__ = "1.0.0"


def main(argv=None):
    """Main entry point for DHT."""
    if argv is None:
        argv = sys.argv
    
    # Parse arguments
    parser = argparse.ArgumentParser(
        description="Development Helper Toolkit Launcher",
        add_help=False,  # We handle help ourselves
        allow_abbrev=False
    )
    
    # Global options
    parser.add_argument('--no-guardian', action='store_true', 
                      help='Disable process guardian')
    parser.add_argument('--quiet', action='store_true',
                      help='Reduce output verbosity')
    parser.add_argument('--debug', action='store_true',
                      help='Enable debug mode')
    
    # Parse known args to separate global options from command
    args, remaining = parser.parse_known_args(argv[1:])
    
    # Create launcher and apply global options
    launcher = DHTLauncher()
    launcher.use_guardian = not args.no_guardian
    launcher.quiet_mode = args.quiet
    launcher.debug_mode = args.debug
    
    # Display banner
    launcher.display_banner()
    
    # Check bash availability
    if not launcher.check_shell_available():
        return 1
    
    # Extract command and its arguments
    if not remaining:
        launcher.display_help()
        return 0
    
    command = remaining[0]
    command_args = remaining[1:]
    
    # Run the command
    return launcher.run_command(command, command_args)


if __name__ == "__main__":
    sys.exit(main())