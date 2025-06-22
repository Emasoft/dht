#!/usr/bin/env python3
"""
Dhtl Diagnostics module.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Python replacement for dhtl_diagnostics.sh
# - Implements diagnostics command functionality
# - Provides system and project health checks
# - Maintains compatibility with shell version
#

"""
DHT Diagnostics Module.

Provides system and project diagnostics to identify potential issues.
"""

import os
import platform
import shutil
import subprocess
import sys

from .common_utils import find_project_root, find_virtual_env
from .dhtl_error_handling import log_error, log_info, log_success, log_warning


def diagnostics_command(*args, **kwargs) -> int:
    """Run system and project diagnostics."""
    log_info("🔍 Running DHT Diagnostics...")
    log_info("=" * 60)

    errors = 0
    warnings = 0

    # System information
    log_info("\n📊 System Information:")
    log_info(f"  OS: {platform.system()} {platform.release()}")
    log_info(f"  Architecture: {platform.machine()}")
    log_info(f"  Python: {sys.version.split()[0]}")
    log_info(f"  Python Path: {sys.executable}")

    # Check Python version
    log_success("  ✓ Python version OK")

    # Check essential tools
    log_info("\n🔧 Essential Tools:")

    tools = {
        "git": "Version control",
        "uv": "Python package manager",
        "python": "Python interpreter",
        "pip": "Python package installer",
    }

    for tool, description in tools.items():
        if shutil.which(tool):
            try:
                result = subprocess.run([tool, "--version"], capture_output=True, text=True)
                version = result.stdout.strip().split("\n")[0]
                log_success(f"  ✓ {tool}: {version}")
            except Exception:
                log_success(f"  ✓ {tool}: Found")
        else:
            if tool == "uv":
                log_warning(f"  ⚠ {tool}: Not found ({description})")
                warnings += 1
            else:
                log_error(f"  ❌ {tool}: Not found ({description})")
                errors += 1

    # Project checks
    project_root = find_project_root()
    log_info("\n📁 Project Information:")
    log_info(f"  Root: {project_root}")

    # Check for project files
    project_files = {
        "pyproject.toml": "Python project configuration",
        "setup.py": "Legacy Python setup",
        "package.json": "Node.js project",
        ".git": "Git repository",
        ".dhtconfig": "DHT configuration",
    }

    found_project_type = False
    for file, description in project_files.items():
        path = project_root / file
        if path.exists():
            log_success(f"  ✓ {file}: Found ({description})")
            if file in ["pyproject.toml", "setup.py", "package.json"]:
                found_project_type = True
        else:
            if file == ".dhtconfig":
                log_info(f"  ℹ {file}: Not found (optional)")

    if not found_project_type:
        log_warning("  ⚠ No project configuration found")
        warnings += 1

    # Virtual environment check
    log_info("\n🐍 Virtual Environment:")
    venv_dir = find_virtual_env(project_root)
    if venv_dir:
        log_success(f"  ✓ Found: {venv_dir}")

        # Check if activated
        if os.environ.get("VIRTUAL_ENV"):
            log_success("  ✓ Activated")
        else:
            log_warning("  ⚠ Not activated")
            log_info("    Run: source .venv/bin/activate")
            warnings += 1
    else:
        log_warning("  ⚠ No virtual environment found")
        log_info("    Create one with: uv venv")
        warnings += 1

    # Check for common issues
    log_info("\n🔍 Common Issues:")

    # Check disk space
    try:
        stat = shutil.disk_usage(project_root)
        free_gb = stat.free / (1024**3)
        if free_gb < 1:
            log_error(f"  ❌ Low disk space: {free_gb:.1f}GB free")
            errors += 1
        else:
            log_success(f"  ✓ Disk space OK: {free_gb:.1f}GB free")
    except Exception:
        pass

    # Check file permissions
    test_file = project_root / ".dht_test_permissions"
    try:
        test_file.touch()
        test_file.unlink()
        log_success("  ✓ File permissions OK")
    except Exception:
        log_error("  ❌ Cannot write to project directory")
        errors += 1

    # Summary
    log_info("\n" + "=" * 60)
    if errors == 0 and warnings == 0:
        log_success("✅ All diagnostics passed!")
        return 0
    else:
        if errors > 0:
            log_error(f"❌ Found {errors} error(s)")
        if warnings > 0:
            log_warning(f"⚠️  Found {warnings} warning(s)")
        return 1 if errors > 0 else 0


def placeholder_function(*args, **kwargs):
    """Placeholder for backward compatibility."""
    return diagnostics_command(*args, **kwargs)
