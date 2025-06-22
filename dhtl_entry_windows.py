#!/usr/bin/env python3
"""
Dhtl Entry Windows module.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Python replacement for dhtl.bat entry point for Windows
# - Maintains same functionality as batch version
# - Cross-platform compatible but optimized for Windows
# - Handles development mode and installed mode
#

"""
DHT Main Entry Point for Windows (Python Script).

This is the Windows-specific entry point for DHT.
It locates and executes the Python launcher (dhtl.py).
Works on Windows with or without Git Bash/WSL.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path


def find_python_launcher():
    """Find the DHT Python launcher in various locations."""
    # Get the directory containing this script
    script_path = Path(__file__).resolve()
    script_dir = script_path.parent
    dht_root = script_dir

    # Check if we're in development mode (src/ structure)
    dev_launcher = dht_root / "src" / "DHT" / "dhtl.py"
    if dev_launcher.exists():
        os.environ["DHTL_DEV_MODE"] = "1"
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

    # Windows-specific: Check Scripts directory in virtual env
    if os.environ.get("VIRTUAL_ENV"):
        venv_path = Path(os.environ["VIRTUAL_ENV"])
        scripts_dhtl = venv_path / "Scripts" / "dhtl.exe"
        if scripts_dhtl.exists():
            return str(scripts_dhtl)
        scripts_dhtl_py = venv_path / "Scripts" / "dhtl"
        if scripts_dhtl_py.exists():
            return str(scripts_dhtl_py)

    return None


def get_python_executable():
    """Get the appropriate Python executable for Windows."""
    # If in virtual environment, use its Python
    if os.environ.get("VIRTUAL_ENV"):
        venv_path = Path(os.environ["VIRTUAL_ENV"])
        # On Windows, Python is in Scripts folder
        python_exe = venv_path / "Scripts" / "python.exe"
        if python_exe.exists():
            return str(python_exe)
        # Fallback to standard location
        python_exe = venv_path / "python.exe"
        if python_exe.exists():
            return str(python_exe)
        # Use sys.executable as last resort for venv
        return sys.executable

    # Try python3 first, then python
    # On Windows, python3 might not exist, so we also check python
    for cmd in ["python3.exe", "python3", "python.exe", "python"]:
        exe_path = shutil.which(cmd)
        if exe_path:
            return exe_path

    # Last resort - use current Python
    return sys.executable


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
    if launcher == shutil.which("dhtl") or launcher.endswith("dhtl.exe"):
        try:
            # On Windows, use subprocess.run with shell=False for better handling
            result = subprocess.run([launcher] + sys.argv[1:], shell=False)
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
        # On Windows, ensure we handle paths with spaces properly
        cmd = [python_exe, launcher] + sys.argv[1:]

        # Use subprocess with proper Windows handling
        startupinfo = None
        if sys.platform == "win32":
            # Prevent console window from flashing on Windows
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE

        result = subprocess.run(cmd, shell=False, startupinfo=startupinfo)
        return result.returncode
    except KeyboardInterrupt:
        # Ctrl+C returns 130 on Unix, but we use it on Windows too for consistency
        return 130
    except Exception as e:
        print(f"❌ Error executing launcher: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
