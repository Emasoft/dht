#!/usr/bin/env python3
"""
Test Dhtl Setup Init module.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest

# Assuming conftest.py provides mock_project_dir fixture


def run_dhtl_command(command: list, cwd: Path, env: dict = None) -> Any:
    """Helper to run dhtl commands via subprocess."""
    dhtl_script = cwd / "DHT" / "dhtl.sh"  # Assumes DHT is directly under cwd
    if not dhtl_script.exists():
        # Try finding the real DHT script relative to this test file for copying
        real_dht_dir = Path(__file__).parent.parent.parent
        if (real_dht_dir / "dhtl.sh").exists():
            (cwd / "DHT").mkdir(parents=True, exist_ok=True)
            shutil.copy(real_dht_dir / "dhtl.sh", dhtl_script)
            # Copy essential modules needed for setup/init
            modules_to_copy = [
                "orchestrator.sh",
                "dhtl_init.sh",
                "dhtl_uv.sh",
                "dhtl_diagnostics.sh",
                "dhtl_secrets.sh",
                "environment.sh",
                "dhtl_environment_1.sh",
                "dhtl_environment_2.sh",
                "dhtl_environment_3.sh",
                "dhtl_utils.sh",
                "user_interface.sh",
                "dhtl_guardian_1.sh",
                "dhtl_guardian_2.sh",
                "dhtl_guardian_command.sh",
                "dhtl_commands_1.sh",
                "dhtl_commands_8.sh",  # Add others as needed
            ]
            (cwd / "DHT" / "modules").mkdir(exist_ok=True)
            for module in modules_to_copy:
                module_path = real_dht_dir / "modules" / module
                if module_path.exists():
                    shutil.copy(module_path, cwd / "DHT" / "modules" / module)
                else:
                    print(f"Warning: Could not find module {module} at {module_path} to copy for test setup.")
        else:
            pytest.fail(f"Cannot find dhtl.sh in mock project {cwd} or real location {real_dht_dir}")

    cmd_list = ["bash", str(dhtl_script)] + command
    print(f"\nRunning command: {' '.join(cmd_list)} in {cwd}")

    # Use a fresh environment or merge with provided
    run_env = os.environ.copy()
    if env:
        run_env.update(env)
    # Ensure PROJECT_ROOT is set correctly for the script execution if not already mocked
    run_env["PROJECT_ROOT"] = str(cwd)
    run_env["DHT_DIR"] = str(cwd / "DHT")  # Ensure DHT_DIR points inside mock project
    # Ensure PATH includes uv if installed globally, otherwise setup might fail early
    # This is a workaround for testing; ideally uv would be mocked or installed in a controlled way
    uv_path = shutil.which("uv")
    if uv_path:
        run_env["PATH"] = f"{os.path.dirname(uv_path)}:{run_env.get('PATH', '')}"

    process = subprocess.run(
        cmd_list,
        capture_output=True,
        text=True,
        env=run_env,
        cwd=cwd,
        timeout=300,  # Increased timeout for potentially slow installs
    )
    print("STDOUT:")
    print(process.stdout)
    print("STDERR:")
    print(process.stderr)
    return process


@pytest.mark.integration
def test_dhtl_setup_creates_venv_and_installs_deps(mock_project_dir) -> Any:
    """Test that 'dhtl setup' creates venv, installs uv, tox, pytest, and alias."""
    # Arrange
    # Create a basic pyproject.toml requiring some dev deps
    (mock_project_dir / "pyproject.toml").write_text("""
[project]
name = "test-proj"
version = "0.1.0"
requires-python = ">=3.9"

[project.optional-dependencies]
dev = ["pytest", "ruff", "tox", "uv", "pre-commit"] # Added pre-commit
    """)
    venv_dir = mock_project_dir / ".venv"
    venv_bin = venv_dir / "bin"
    alias_script = venv_bin / "activate.d" / "dhtl_alias.sh"

    # Act
    result = run_dhtl_command(["setup"], cwd=mock_project_dir)

    # Assert
    assert result.returncode == 0, "dhtl setup command failed"
    assert "DHT Setup completed successfully" in result.stdout
    assert venv_dir.is_dir(), "Virtual environment directory was not created"
    assert (venv_bin / "python").exists(), "Python executable not found in venv bin"
    assert (venv_bin / "uv").exists(), "uv executable not found in venv bin"
    assert (venv_bin / "pytest").exists(), "pytest executable not found in venv bin"
    assert (venv_bin / "ruff").exists(), "ruff executable not found in venv bin"
    assert (venv_bin / "tox").exists(), "tox executable not found in venv bin"
    assert (venv_bin / "pre-commit").exists(), "pre-commit executable not found in venv bin"
    assert alias_script.exists(), "Alias script was not created"
    assert "alias dhtl=" in alias_script.read_text()
    assert "DHT/dhtl.sh" in alias_script.read_text()
    assert (mock_project_dir / "DHT" / ".dht_environment_report.json").exists(), "Diagnostics report missing"


@pytest.mark.integration
def test_dhtl_init_creates_structure_and_runs_setup(mock_project_dir) -> Any:
    """Test that 'dhtl init' creates files/dirs and runs the setup steps."""
    # Arrange
    # Use a subdirectory within mock_project_dir to simulate initializing in a new location
    init_target_dir = mock_project_dir / "new_project_init"  # Use different name
    init_target_dir.mkdir()
    venv_dir = init_target_dir / ".venv"
    venv_bin = venv_dir / "bin"
    alias_script = venv_bin / "activate.d" / "dhtl_alias.sh"

    # Act
    # Run init from one level up, targeting the new directory
    # Need to run the *source* dhtl.sh, not one potentially created by init
    source_dht_dir = mock_project_dir / "DHT"  # Assume setup copied DHT here first
    result = run_dhtl_command(["init", str(init_target_dir)], cwd=mock_project_dir)

    # Assert
    assert result.returncode == 0, "dhtl init command failed"
    assert "DHT initialized successfully" in result.stdout

    # Check created files/dirs
    assert (init_target_dir / "DHT").is_dir()
    assert (init_target_dir / "DHT" / "modules" / "dhtl_init.sh").exists()
    assert (init_target_dir / "dhtl.sh").exists()  # Project root launcher
    assert (init_target_dir / "pyproject.toml").exists()
    assert (init_target_dir / "README.md").exists()
    assert (init_target_dir / "tox.ini").exists()
    assert (init_target_dir / ".gitignore").exists()
    assert (init_target_dir / "src").is_dir()
    assert (init_target_dir / "tests").is_dir()
    assert (init_target_dir / ".github" / "workflows" / "tests.yml").exists()
    assert (init_target_dir / ".github" / "workflows" / "publish.yml").exists()

    # Check setup steps ran
    assert venv_dir.is_dir(), "Virtual environment directory was not created by init"
    assert (venv_bin / "python").exists(), "Python executable not found in venv bin (init)"
    assert (venv_bin / "uv").exists(), "uv executable not found in venv bin (init)"
    # Check a dev dep known to be installed by default template
    assert (venv_bin / "pytest").exists(), "pytest executable not found in venv bin (init)"
    assert alias_script.exists(), "Alias script was not created by init"
    assert (init_target_dir / "DHT" / ".dht_environment_report.json").exists(), "Diagnostics report missing after init"


@pytest.mark.integration
def test_dhtl_setup_is_idempotent(mock_project_dir) -> Any:
    """Test that running 'dhtl setup' multiple times works correctly."""
    # Arrange
    (mock_project_dir / "pyproject.toml").write_text("""
[project]
name = "idempotent-proj"
version = "0.1.0"
requires-python = ">=3.9"
[project.optional-dependencies]
dev = ["pytest"]
    """)

    # Act
    result1 = run_dhtl_command(["setup"], cwd=mock_project_dir)
    # Add a file to venv to check if it persists
    (mock_project_dir / ".venv" / "test_marker.txt").touch()
    result2 = run_dhtl_command(["setup"], cwd=mock_project_dir)  # Run again

    # Assert
    assert result1.returncode == 0, "First dhtl setup command failed"
    assert result2.returncode == 0, "Second dhtl setup command failed"
    assert "DHT Setup completed successfully" in result1.stdout
    assert "DHT Setup completed successfully" in result2.stdout
    # Check a file that should exist after setup
    assert (mock_project_dir / ".venv" / "bin" / "pytest").exists()
    # Check that the venv wasn't completely wiped (our marker file should still be there)
    assert (mock_project_dir / ".venv" / "test_marker.txt").exists(), "Second setup run wiped the venv unexpectedly"


@pytest.mark.integration
def test_dhtl_setup_handles_secrets(mock_project_dir) -> Any:
    """Test that 'dhtl setup' checks secrets and creates/updates .env file correctly."""
    # Arrange
    # Create a mock test file that references a secret
    (mock_project_dir / "tests").mkdir(exist_ok=True)
    (mock_project_dir / "tests" / "test_secrets.py").write_text(
        "import os\ndef test_secret() -> Any: assert os.environ.get('MY_TEST_SECRET')"
    )
    env_file = mock_project_dir / ".env"
    gitignore_file = mock_project_dir / ".gitignore"

    # Mock global environment variable
    mock_env = os.environ.copy()
    mock_env["MY_TEST_SECRET"] = "global_value"
    mock_env["OTHER_SECRET"] = "other_value"  # Should not be added

    # Act
    result = run_dhtl_command(["setup"], cwd=mock_project_dir, env=mock_env)

    # Assert - First run (creates .env)
    assert result.returncode == 0, "dhtl setup command failed"
    assert "Required secrets identified: MY_TEST_SECRET" in result.stdout
    assert env_file.exists(), ".env file was not created"
    env_content = env_file.read_text()
    assert "export MY_TEST_SECRET='global_value'" in env_content
    assert "OTHER_SECRET" not in env_content  # Ensure only required secrets are added
    assert gitignore_file.exists()
    assert "/.env" in gitignore_file.read_text()

    # Test idempotency: run again, ensure existing value in .env is preserved
    # Modify .env locally
    env_file.write_text("export MY_TEST_SECRET='local_override'\nexport USER_VAR='user_value'")
    result2 = run_dhtl_command(["setup"], cwd=mock_project_dir, env=mock_env)
    assert result2.returncode == 0, "Second dhtl setup failed"
    env_content_after = env_file.read_text()
    assert "export MY_TEST_SECRET='local_override'" in env_content_after, "Local .env value was overwritten"
    assert "export USER_VAR='user_value'" in env_content_after, "User variable in .env was removed"
    # Check that the globally found secret wasn't re-added if already present
    assert env_content_after.count("export MY_TEST_SECRET=") == 1

    # Test adding a new global secret
    mock_env["NEW_GLOBAL_SECRET"] = "new_global"
    # Add a mock check that would detect this new secret
    (mock_project_dir / "tests" / "test_new_secret.py").write_text(
        "import os\ndef test_new() -> Any: assert os.environ.get('NEW_GLOBAL_SECRET')"
    )
    result3 = run_dhtl_command(["setup"], cwd=mock_project_dir, env=mock_env)
    assert result3.returncode == 0, "Third dhtl setup failed"
    env_content_final = env_file.read_text()
    assert "export MY_TEST_SECRET='local_override'" in env_content_final  # Still preserved
    assert "export USER_VAR='user_value'" in env_content_final  # Still preserved
    assert "export NEW_GLOBAL_SECRET='new_global'" in env_content_final  # New one added


@pytest.mark.integration
def test_dhtl_setup_respects_python_version_file(mock_project_dir) -> Any:
    """Test that 'dhtl setup' uses the python version from .python-version."""
    # Arrange
    # Create a .python-version file
    python_version_to_test = "3.10"  # Use a version likely available but maybe not default
    (mock_project_dir / ".python-version").write_text(f"{python_version_to_test}\n")
    (mock_project_dir / "pyproject.toml").touch()  # Need pyproject for setup to proceed fully
    venv_dir = mock_project_dir / ".venv"

    # Act
    result = run_dhtl_command(["setup"], cwd=mock_project_dir)

    # Assert
    assert result.returncode == 0, "dhtl setup command failed"
    assert venv_dir.is_dir(), "Virtual environment directory was not created"
    # Check the output for the python version request (this is fragile)
    assert f"requesting Python {python_version_to_test}" in result.stdout
    # A more robust check would be to inspect the created venv's python version,
    # but that requires running python from the venv.
    py_version_check = subprocess.run(
        [str(venv_dir / "bin" / "python"), "--version"], capture_output=True, text=True, cwd=mock_project_dir
    )
    assert py_version_check.returncode == 0
    # Check if the major.minor version matches
    assert f"Python {python_version_to_test}." in py_version_check.stdout
