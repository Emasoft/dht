#!/usr/bin/env python3

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Guardian utilities module
# - Re-exports functionality from guardian modules
# - Provides single import point for guardian functionality
#

"""
DHT Guardian Utils Module.

Provides guardian functionality using the converted guardian modules.
"""

# Import from the converted guardian modules
from .dhtl_guardian_1 import run_with_guardian
from .dhtl_guardian_2 import ensure_process_guardian_running

# Re-export for compatibility
__all__ = ["run_with_guardian", "ensure_process_guardian_running"]
