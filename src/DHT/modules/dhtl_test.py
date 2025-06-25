#!/usr/bin/env python3
"""
Dhtl Test module.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Python replacement for dhtl_test.sh
# - Implements test_dht and verify_dht commands
# - Tests DHT itself and verifies installation
# - Integrated with DHT command dispatcher
#

"""
DHT Test Module.

Provides commands to test DHT itself and verify its installation.
"""

import shutil
import subprocess
import sys
from typing import Any

from .common_utils import find_project_root, get_venv_executable
from .dhtl_error_handling import log_error, log_info, log_success, log_warning
from .guardian_prefect import ResourceLimits, guardian_sequential_flow


def test_dht_command(args: list[str]) -> int:
    """Run tests for the DHT toolkit itself."""
    log_info("🧪 Testing DHT toolkit...")

    # Find DHT root
    dht_root = find_project_root()
    tests_dir = dht_root / "tests"

    if not tests_dir.exists():
        log_error(f"Tests directory not found: {tests_dir}")
        return 1

    # Parse options
    unit_only = False
    integration_only = False
    pattern = None
    test_path = None
    coverage = False

    i = 0
    while i < len(args):
        if args[i] == "--unit":
            unit_only = True
        elif args[i] == "--integration":
            integration_only = True
        elif args[i] == "--pattern" and i + 1 < len(args):
            pattern = args[i + 1]
            i += 1
        elif args[i] == "--path" and i + 1 < len(args):
            test_path = args[i + 1]
            i += 1
        elif args[i] in ["--report", "--coverage"]:
            coverage = True
        i += 1

    # Get pytest executable
    pytest_exe = get_venv_executable("pytest")
    if not pytest_exe:
        log_error("pytest not found in virtual environment")
        log_info("Run: uv pip install pytest pytest-cov")
        return 1

    # Build test command
    test_cmd = [pytest_exe]

    # Add test directory or path
    if test_path:
        test_cmd.append(test_path)
    else:
        test_cmd.append(str(tests_dir))

    # Add options
    test_cmd.extend(["-v", "--tb=short"])

    if pattern:
        test_cmd.extend(["-k", pattern])

    if unit_only:
        test_cmd.extend(["-m", "unit"])
    elif integration_only:
        test_cmd.extend(["-m", "integration"])

    if coverage:
        test_cmd.extend(["--cov=src/DHT", "--cov-report=term-missing", "--cov-report=html"])

    # Show what we're doing
    log_info(f"Running: {' '.join(test_cmd)}")

    # Run tests with guardian
    command = " ".join(test_cmd)
    limits = ResourceLimits(memory_mb=4096, cpu_percent=100, timeout=1800)  # 30 min timeout

    results = guardian_sequential_flow(commands=[command], stop_on_failure=True, default_limits=limits)

    if results and results[0]["returncode"] == 0:
        log_success("✓ All DHT tests passed!")
        if results[0].get("stdout"):
            print(results[0]["stdout"])
        if coverage:
            log_info("Coverage report saved to htmlcov/index.html")
        return 0
    else:
        log_error("✗ Some DHT tests failed")
        if results and results[0].get("stderr"):
            print(results[0]["stderr"], file=sys.stderr)
        return 1


def verify_dht_command(*args: Any, **kwargs: Any) -> int:
    """Verify the DHT installation."""
    log_info("🔍 Verifying DHT installation...")

    errors = 0
    warnings = 0

    # Check DHT directory structure
    log_info("\nChecking directory structure...")
    dht_root = find_project_root()

    required_dirs = [
        "src/DHT",
        "src/DHT/modules",
        "tests",
    ]

    for dir_path in required_dirs:
        full_path = dht_root / dir_path
        if full_path.exists():
            log_success(f"✓ {dir_path}")
        else:
            log_error(f"✗ {dir_path} - Missing")
            errors += 1

    # Check essential modules
    log_info("\nChecking essential modules...")
    essential_modules = [
        "src/DHT/modules/dhtl_commands.py",
        "src/DHT/modules/command_registry.py",
        "src/DHT/modules/dhtl_error_handling.py",
        "src/DHT/modules/common_utils.py",
        "src/DHT/modules/guardian_prefect.py",
    ]

    for module_path in essential_modules:
        full_path = dht_root / module_path
        if full_path.exists():
            log_success(f"✓ {module_path}")
        else:
            log_error(f"✗ {module_path} - Missing")
            errors += 1

    # Check launcher script
    log_info("\nChecking launcher script...")
    launcher_path = dht_root / "dhtl.py"
    if launcher_path.exists():
        log_success("✓ dhtl.py")
    else:
        log_error("✗ dhtl.py - Missing")
        errors += 1

    # Check virtual environment
    log_info("\nChecking virtual environment...")
    venv_path = dht_root / ".venv"
    if venv_path.exists():
        log_success("✓ Virtual environment exists")

        # Check Python version
        python_exe = get_venv_executable("python")
        if python_exe:
            result = subprocess.run([python_exe, "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                log_success(f"✓ Python: {result.stdout.strip()}")
            else:
                log_error("✗ Failed to get Python version")
                errors += 1
    else:
        log_error("✗ Virtual environment not found")
        errors += 1

    # Check essential tools
    log_info("\nChecking essential tools...")
    tools = [
        ("git", "Version control"),
        ("uv", "Package manager"),
        ("pytest", "Test runner"),
        ("ruff", "Linter"),
    ]

    for tool, description in tools:
        exe = get_venv_executable(tool) or shutil.which(tool)
        if exe:
            log_success(f"✓ {tool} - {description}")
        else:
            log_warning(f"⚠ {tool} - {description} (not found)")
            warnings += 1

    # Check git integration
    log_info("\nChecking git integration...")
    if (dht_root / ".git").exists():
        log_success("✓ Git repository initialized")

        # Check git hooks
        hooks_dir = dht_root / ".git" / "hooks"
        if (hooks_dir / "pre-commit").exists():
            log_success("✓ Git hooks installed")
        else:
            log_warning("⚠ Git hooks not installed")
            warnings += 1
    else:
        log_warning("⚠ Not a git repository")
        warnings += 1

    # Check configuration files
    log_info("\nChecking configuration files...")
    config_files = [
        ("pyproject.toml", "Project configuration"),
        (".gitignore", "Git ignore rules"),
        ("ruff.toml", "Ruff configuration"),
    ]

    for config_file, description in config_files:
        if (dht_root / config_file).exists():
            log_success(f"✓ {config_file} - {description}")
        else:
            log_warning(f"⚠ {config_file} - {description} (not found)")
            warnings += 1

    # Summary
    log_info("\n" + "=" * 50)
    log_info("Verification Summary:")

    if errors == 0 and warnings == 0:
        log_success("✓ DHT installation is complete and verified!")
        return 0
    else:
        if errors > 0:
            log_error(f"✗ Found {errors} error(s)")
        if warnings > 0:
            log_warning(f"⚠ Found {warnings} warning(s)")

        if errors > 0:
            log_info("\nRun 'dhtl setup' to fix installation issues")
            return 1
        else:
            log_info("\nDHT is functional but some optional components are missing")
            return 0


# For backward compatibility
def placeholder_function() -> Any:
    """Placeholder function."""
    log_warning("Use test_dht_command or verify_dht_command instead")
    return True


# Export command functions
__all__ = ["test_dht_command", "verify_dht_command", "placeholder_function"]
