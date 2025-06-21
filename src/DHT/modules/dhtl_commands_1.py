#!/usr/bin/env python3

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Python replacement for dhtl_commands_1.sh
# - Implements restore command functionality
# - Integrated with DHT command dispatcher
# - Restores dependencies from lock files
#

"""
DHT Restore Commands Module.

Provides dependency restoration functionality from lock files.
"""

import os
import shutil
import subprocess
import sys

from .common_utils import find_project_root, find_virtual_env
from .dhtl_error_handling import log_error, log_info, log_success, log_warning
from .dhtl_guardian_utils import run_with_guardian


def restore_command(*args, **kwargs) -> int:
    """Restore project dependencies from lock files."""
    log_info("📦 Restoring project dependencies...")

    # Find project root
    project_root = find_project_root()

    # Find virtual environment
    venv_dir = find_virtual_env(project_root)
    if not venv_dir:
        venv_dir = project_root / ".venv"

    # Check for lock files
    restored = False

    # Python: uv.lock or requirements.txt
    uv_lock = project_root / "uv.lock"
    requirements_txt = project_root / "requirements.txt"
    pyproject_toml = project_root / "pyproject.toml"

    if uv_lock.exists():
        log_info("Found uv.lock - restoring with uv...")

        # Check for uv
        uv_cmd = None
        if shutil.which("uv"):
            uv_cmd = "uv"
        elif venv_dir and (venv_dir / "bin" / "uv").exists():
            uv_cmd = str(venv_dir / "bin" / "uv")
        elif venv_dir and (venv_dir / "Scripts" / "uv.exe").exists():
            uv_cmd = str(venv_dir / "Scripts" / "uv.exe")

        if not uv_cmd:
            log_error("uv is not installed")
            log_info("Install uv: curl -LsSf https://astral.sh/uv/install.sh | sh")
            return 1

        # Create venv if needed
        if not venv_dir.exists():
            log_info("Creating virtual environment...")
            result = subprocess.run([uv_cmd, "venv"])
            if result.returncode != 0:
                log_error("Failed to create virtual environment")
                return 1

        # Get memory limit
        mem_limit = int(os.environ.get("PYTHON_MEM_LIMIT", "2048"))

        # Run uv sync
        sync_cmd = [uv_cmd, "sync"]

        exit_code = run_with_guardian(sync_cmd[0], "uv-sync", mem_limit, *sync_cmd[1:])

        if exit_code == 0:
            log_success("Python dependencies restored successfully!")
            restored = True
        else:
            log_error("Failed to restore Python dependencies")
            return exit_code

    elif requirements_txt.exists():
        log_info("Found requirements.txt - restoring with pip...")

        # Ensure virtual environment exists
        if not venv_dir.exists():
            log_info("Creating virtual environment...")
            result = subprocess.run([sys.executable, "-m", "venv", str(venv_dir)])
            if result.returncode != 0:
                log_error("Failed to create virtual environment")
                return 1

        # Find pip
        pip_cmd = None
        if venv_dir and (venv_dir / "bin" / "pip").exists():
            pip_cmd = str(venv_dir / "bin" / "pip")
        elif venv_dir and (venv_dir / "Scripts" / "pip.exe").exists():
            pip_cmd = str(venv_dir / "Scripts" / "pip.exe")
        else:
            pip_cmd = "pip"
            log_warning("Using global pip")

        # Get memory limit
        mem_limit = int(os.environ.get("PYTHON_MEM_LIMIT", "2048"))

        # Install from requirements.txt
        install_cmd = [pip_cmd, "install", "-r", str(requirements_txt)]

        exit_code = run_with_guardian(install_cmd[0], "pip-install", mem_limit, *install_cmd[1:])

        if exit_code == 0:
            log_success("Python dependencies restored successfully!")
            restored = True
        else:
            log_error("Failed to restore Python dependencies")
            return exit_code

    elif pyproject_toml.exists():
        log_info("Found pyproject.toml but no lock file")
        log_info("Run 'dhtl sync' to install dependencies")

    # Node.js: package-lock.json or yarn.lock
    package_lock = project_root / "package-lock.json"
    yarn_lock = project_root / "yarn.lock"
    pnpm_lock = project_root / "pnpm-lock.yaml"

    if package_lock.exists():
        log_info("Found package-lock.json - restoring with npm...")

        if not shutil.which("npm"):
            log_error("npm is not installed")
            return 1

        result = subprocess.run(["npm", "ci"], cwd=project_root)
        if result.returncode == 0:
            log_success("Node.js dependencies restored successfully!")
            restored = True
        else:
            log_error("Failed to restore Node.js dependencies")
            return result.returncode

    elif yarn_lock.exists():
        log_info("Found yarn.lock - restoring with yarn...")

        if not shutil.which("yarn"):
            log_error("yarn is not installed")
            return 1

        result = subprocess.run(["yarn", "install", "--frozen-lockfile"], cwd=project_root)
        if result.returncode == 0:
            log_success("Node.js dependencies restored successfully!")
            restored = True
        else:
            log_error("Failed to restore Node.js dependencies")
            return result.returncode

    elif pnpm_lock.exists():
        log_info("Found pnpm-lock.yaml - restoring with pnpm...")

        if not shutil.which("pnpm"):
            log_error("pnpm is not installed")
            return 1

        result = subprocess.run(["pnpm", "install", "--frozen-lockfile"], cwd=project_root)
        if result.returncode == 0:
            log_success("Node.js dependencies restored successfully!")
            restored = True
        else:
            log_error("Failed to restore Node.js dependencies")
            return result.returncode

    if not restored:
        log_warning("No lock files found to restore from")
        log_info("Supported lock files:")
        log_info("  - Python: uv.lock, requirements.txt")
        log_info("  - Node.js: package-lock.json, yarn.lock, pnpm-lock.yaml")
        return 1

    return 0


# For backward compatibility
def placeholder_command(*args, **kwargs) -> int:
    """Placeholder command implementation."""
    return restore_command(*args, **kwargs)


# Export command functions
__all__ = ["restore_command", "placeholder_command"]
