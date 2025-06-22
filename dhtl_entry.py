#!/usr/bin/env python3
"""
Dhtl Entry module.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Python replacement for dhtl.sh entry point
# - Maintains same functionality as shell version
# - Locates and executes the DHT Python launcher
# - Handles development mode and installed mode
#

"""
DHT Main Entry Point (Python Script).

This is the primary entry point for DHT on all systems.
It locates and executes the Python launcher (dhtl.py).
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path


def find_python_launcher():
    """Find the DHT Python launcher in various locations."""
    # Get the directory containing this script
    script_dir = Path(__file__).parent.resolve()
    dht_root = script_dir

    # Check if we're in development mode (src/ structure)
    dev_launcher = dht_root / "src" / "DHT" / "dhtl.py"
    if dev_launcher.exists():
        os.environ["DHTL_DEV_MODE"] = "1"
        # Add src to Python path for imports
        sys.path.insert(0, str(dht_root / "src"))
        return str(dev_launcher)

    # Check legacy mode - direct structure
    legacy_launcher = dht_root / "DHT" / "dhtl.py"
    if legacy_launcher.exists():
        os.environ["DHTL_DEV_MODE"] = "1"
        return str(legacy_launcher)

    # Try installed dhtl command
    dhtl_cmd = shutil.which("dhtl")
    if dhtl_cmd:
        # Use the installed command directly
        return dhtl_cmd

    return None


def get_python_executable():
    """Get the appropriate Python executable."""
    # If in virtual environment, use its Python
    if os.environ.get("VIRTUAL_ENV"):
        return sys.executable

    # Try python3 first, then python
    for cmd in ["python3", "python"]:
        if shutil.which(cmd):
            return cmd

    return None


def main():
    """Main entry point."""
    # Find the launcher
    launcher = find_python_launcher()
    if not launcher:
        print("❌ Error: DHT launcher not found", file=sys.stderr)
        print("Please ensure DHT is properly installed or run from the correct directory", file=sys.stderr)
        return 1

    # Set environment variables for compatibility
    script_dir = Path(__file__).parent.resolve()
    os.environ["DHT_ROOT"] = str(script_dir)
    os.environ["SCRIPT_DIR"] = str(script_dir)
    os.environ["DHTL_SHELL_ENTRY"] = "1"

    # If launcher is the installed dhtl command, execute it directly
    if launcher == shutil.which("dhtl"):
        try:
            result = subprocess.run([launcher] + sys.argv[1:])
            return result.returncode
        except KeyboardInterrupt:
            return 130
        except Exception as e:
            print(f"❌ Error executing dhtl: {e}", file=sys.stderr)
            return 1

    # Otherwise, find Python and execute the launcher
    python_exe = get_python_executable()
    if not python_exe:
        print("❌ Error: Python not found", file=sys.stderr)
        print("Please install Python 3.10+ or activate a virtual environment", file=sys.stderr)
        return 1

    # Execute the launcher
    try:
        # Use sys.executable if it's the same as python_exe to preserve the exact Python being used
        if python_exe == "python" and sys.executable.endswith("python"):
            python_exe = sys.executable
        elif python_exe == "python3" and sys.executable.endswith("python3"):
            python_exe = sys.executable

        result = subprocess.run([python_exe, launcher] + sys.argv[1:])
        return result.returncode
    except KeyboardInterrupt:
        return 130
    except Exception as e:
        print(f"❌ Error executing launcher: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
