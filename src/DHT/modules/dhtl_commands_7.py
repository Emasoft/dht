#!/usr/bin/env python3

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Python replacement for dhtl_commands_7.sh
# - Implements publish command functionality
# - Integrated with DHT command dispatcher
# - Publishes Python packages to PyPI or other repositories
#

"""
DHT Publish Commands Module.

Provides package publishing functionality for Python projects.
"""

import os
import shutil

from .common_utils import find_project_root, find_virtual_env
from .dhtl_error_handling import log_error, log_info, log_success
from .dhtl_guardian_utils import run_with_guardian


def publish_command(*args, **kwargs) -> int:
    """Publish Python package to PyPI or other repositories."""
    log_info("🚀 Publishing Python package...")

    # Find project root
    project_root = find_project_root()

    # Check for pyproject.toml or setup.py
    pyproject_toml = project_root / "pyproject.toml"
    setup_py = project_root / "setup.py"

    if not pyproject_toml.exists() and not setup_py.exists():
        log_error("No pyproject.toml or setup.py found")
        log_info("This doesn't appear to be a Python package")
        return 1

    # Find virtual environment
    venv_dir = find_virtual_env(project_root)
    if not venv_dir:
        venv_dir = project_root / ".venv"

    # Check for build tool
    uv_cmd = None
    twine_cmd = None

    # Prefer uv for publishing
    if shutil.which("uv"):
        uv_cmd = "uv"
    elif venv_dir and (venv_dir / "bin" / "uv").exists():
        uv_cmd = str(venv_dir / "bin" / "uv")
    elif venv_dir and (venv_dir / "Scripts" / "uv.exe").exists():
        uv_cmd = str(venv_dir / "Scripts" / "uv.exe")

    # Check for twine as fallback
    if not uv_cmd:
        if venv_dir and (venv_dir / "bin" / "twine").exists():
            twine_cmd = str(venv_dir / "bin" / "twine")
        elif venv_dir and (venv_dir / "Scripts" / "twine.exe").exists():
            twine_cmd = str(venv_dir / "Scripts" / "twine.exe")
        elif shutil.which("twine"):
            twine_cmd = "twine"

    # Check for dist directory
    dist_dir = project_root / "dist"
    if not dist_dir.exists() or not list(dist_dir.glob("*.whl")) and not list(dist_dir.glob("*.tar.gz")):
        log_error("No distribution files found in dist/")
        log_info("Build the package first: dhtl build")
        return 1

    # Determine repository
    repository = "pypi"
    test_pypi = False

    if "--test" in args or "--test-pypi" in args:
        repository = "testpypi"
        test_pypi = True
        log_info("Publishing to TestPyPI...")

    # Get memory limit
    mem_limit = int(os.environ.get("PYTHON_MEM_LIMIT", "2048"))

    if uv_cmd:
        # Use uv to publish
        log_info("Publishing with uv...")

        publish_cmd = [uv_cmd, "publish"]

        if test_pypi:
            publish_cmd.extend(["--publish-url", "https://test.pypi.org/legacy/"])

        # Run with guardian
        exit_code = run_with_guardian(publish_cmd[0], "uv-publish", mem_limit, *publish_cmd[1:])
    elif twine_cmd:
        # Use twine to publish
        log_info("Publishing with twine...")

        publish_cmd = [twine_cmd, "upload"]

        if test_pypi:
            publish_cmd.extend(["-r", "testpypi"])

        # Add all distribution files
        publish_cmd.extend(["dist/*"])

        # Run with guardian
        exit_code = run_with_guardian(publish_cmd[0], "twine-upload", mem_limit, *publish_cmd[1:])
    else:
        log_error("No publishing tool found (uv or twine)")
        log_info("Install uv or twine: uv pip install twine")
        return 1

    if exit_code == 0:
        log_success("Package published successfully!")
        if test_pypi:
            log_info("View at: https://test.pypi.org/project/[your-package-name]/")
        else:
            log_info("View at: https://pypi.org/project/[your-package-name]/")
    else:
        log_error(f"Publishing failed with exit code {exit_code}")

    return exit_code


# For backward compatibility
def placeholder_command(*args, **kwargs) -> int:
    """Placeholder command implementation."""
    return publish_command(*args, **kwargs)


# Export command functions
__all__ = ["publish_command", "placeholder_command"]
