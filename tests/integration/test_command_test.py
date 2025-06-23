#!/usr/bin/env python3
"""
Test Command Test module.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

import os
import subprocess
import sys
from typing import Any

import pytest

# Import helper functions
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from helpers import create_mock_file


@pytest.mark.integration
def test_test_command_with_pytest_script(mock_project_with_venv) -> Any:
    """Test that the test command runs pytest with the correct arguments."""
    # Create a mock test file
    test_file = create_mock_file(
        mock_project_with_venv / "tests",
        "test_example.py",
        """
def test_example() -> Any:
    assert True
""",
    )

    # Create a mock pytest script that just prints the command arguments
    pytest_path = mock_project_with_venv / ".venv/bin/pytest"
    pytest_path.write_text("""#!/bin/sh
echo "Running pytest with args: $@"
exit 0
""")
    pytest_path.chmod(0o755)

    # Set up the DHT directory structure within the mock project
    dht_dir = mock_project_with_venv / "DHT"
    dht_dir.mkdir(exist_ok=True)

    # Create mock modules directory
    modules_dir = dht_dir / "modules"
    modules_dir.mkdir(exist_ok=True)

    # Create mock commands.sh with test_command function
    commands_path = modules_dir / "commands.sh"
    commands_path.write_text("""
test_command() {
    echo "🧪 Running tests on project..."
    PROJECT_ROOT="$1"
    VENV_DIR="$PROJECT_ROOT/.venv"
    PYTEST_CMD="$VENV_DIR/bin/pytest"

    if [ -f "$PYTEST_CMD" ]; then
        echo "🔄 Running pytest..."
        "$PYTEST_CMD" -xvs "$PROJECT_ROOT/tests"
        return $?
    else
        echo "❌ No pytest found in venv."
        return 1
    fi
}
""")

    # Create mock dhtl.sh script
    dhtl_path = mock_project_with_venv / "dhtl.sh"
    dhtl_path.write_text("""#!/bin/bash
source "./DHT/modules/commands.sh"

if [ "$1" == "test" ]; then
    test_command "$(pwd)"
    exit $?
else
    echo "Unknown command: $1"
    exit 1
fi
""")
    dhtl_path.chmod(0o755)

    # Run the test command
    result = subprocess.run(["./dhtl.sh", "test"], cwd=mock_project_with_venv, capture_output=True, text=True)

    # Check the output
    assert result.returncode == 0
    assert "Running pytest" in result.stdout
    assert "-xvs" in result.stdout


@pytest.mark.integration
def test_test_command_with_fast_option(mock_project_with_venv) -> Any:
    """Test that the --fast option for test command works."""
    # Create a mock test file
    test_file = create_mock_file(
        mock_project_with_venv / "tests",
        "test_example.py",
        """
def test_example() -> Any:
    assert True
""",
    )

    # Create a mock pytest script that just prints the command arguments
    pytest_path = mock_project_with_venv / ".venv/bin/pytest"
    pytest_path.write_text("""#!/bin/sh
echo "Running pytest with args: $@"
exit 0
""")
    pytest_path.chmod(0o755)

    # Set up the DHT directory structure within the mock project
    dht_dir = mock_project_with_venv / "DHT"
    dht_dir.mkdir(exist_ok=True)

    # Create mock modules directory
    modules_dir = dht_dir / "modules"
    modules_dir.mkdir(exist_ok=True)

    # Create mock commands.sh with test_command function
    commands_path = modules_dir / "commands.sh"
    commands_path.write_text("""
test_command() {
    echo "🧪 Running tests on project..."
    PROJECT_ROOT="$1"
    FAST_MODE=false

    # Process arguments
    for arg in "$@"; do
        if [ "$arg" == "--fast" ]; then
            FAST_MODE=true
            break
        fi
    done

    VENV_DIR="$PROJECT_ROOT/.venv"
    PYTEST_CMD="$VENV_DIR/bin/pytest"

    if [ -f "$PYTEST_CMD" ]; then
        echo "🔄 Running pytest..."
        if [ "$FAST_MODE" = true ]; then
            echo "🔄 Running in fast mode - only critical tests"
            "$PYTEST_CMD" -xvs -k 'critical or basic or essential' "$PROJECT_ROOT/tests"
        else
            "$PYTEST_CMD" -xvs "$PROJECT_ROOT/tests"
        fi
        return $?
    else
        echo "❌ No pytest found in venv."
        return 1
    fi
}
""")

    # Create mock dhtl.sh script
    dhtl_path = mock_project_with_venv / "dhtl.sh"
    dhtl_path.write_text("""#!/bin/bash
source "./DHT/modules/commands.sh"

if [ "$1" == "test" ]; then
    shift
    test_command "$(pwd)" "$@"
    exit $?
else
    echo "Unknown command: $1"
    exit 1
fi
""")
    dhtl_path.chmod(0o755)

    # Run the test command with --fast option
    result = subprocess.run(["./dhtl.sh", "test", "--fast"], cwd=mock_project_with_venv, capture_output=True, text=True)

    # Check the output
    assert result.returncode == 0
    assert "Running in fast mode" in result.stdout
    assert "critical or basic or essential" in result.stdout
