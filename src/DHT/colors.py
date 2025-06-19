#!/usr/bin/env python3

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Extracted Colors class from dhtl.py for modularity
# - Reduced size of main launcher file
# - Follows CLAUDE.md modularity guidelines
#

"""
Terminal Colors Utility.

ANSI color codes for cross-platform terminal output.
"""

import os
import sys


class Colors:
    """ANSI color codes for terminal output."""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

    @staticmethod
    def disable():
        """Disable colors for environments that don't support them."""
        Colors.HEADER = ''
        Colors.BLUE = ''
        Colors.CYAN = ''
        Colors.GREEN = ''
        Colors.YELLOW = ''
        Colors.RED = ''
        Colors.ENDC = ''
        Colors.BOLD = ''
        Colors.UNDERLINE = ''

    @staticmethod
    def supports_color() -> bool:
        """Check if the terminal supports color output."""
        # Disable color for non-interactive or dumb terminals
        if not sys.stdout.isatty():
            return False

        term = os.environ.get('TERM', '')
        if term == 'dumb':
            return False

        # Windows console might not support ANSI colors
        if sys.platform == "win32" and not os.environ.get("ANSICON"):
            try:
                import colorama
                colorama.init()
                return True
            except ImportError:
                return False

        return True
