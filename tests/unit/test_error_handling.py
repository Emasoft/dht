import os
import sys

import pytest

# Import helper functions
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from helpers import mock_bash_script, run_bash_command

# Skip all tests in this file since we've migrated from shell to Python
pytestmark = pytest.mark.skip(
    reason="Shell scripts have been migrated to Python. Error handling is now tested through Python unit tests."
)


def test_log_error():
    """Test the log_error function."""
    # Create a script that sources the module and calls the function
    script_content = """#!/bin/bash
    # Set up environment variables
    export DHTL_SESSION_ID="test_session"
    export DHT_DIR="{}"
    export DEBUG_MODE=true

    # Source the module
    source "{}/modules/dhtl_error_handling.sh"

    # Test log_error with default error code
    log_error "Test error message"
    echo "EXIT_CODE_1=$?"

    # Test log_error with custom error code
    log_error "Test error message with custom code" 42
    echo "EXIT_CODE_2=$?"

    # Test log_error with stack trace
    log_error "Test error message with stack trace" 10 stack_trace
    echo "EXIT_CODE_3=$?"
    """.format(
        os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src/DHT")),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src/DHT")),
    )

    script_path = mock_bash_script(script_content)

    try:
        # Run the script
        result = run_bash_command(script_path)

        # Check the output
        assert "❌ ERROR: Test error message" in result
        assert "EXIT_CODE_1=1" in result
        assert "EXIT_CODE_2=42" in result
        assert "EXIT_CODE_3=10" in result
        assert "Stack trace:" in result
    finally:
        # Clean up the temporary script
        os.unlink(script_path)


def test_log_warning():
    """Test the log_warning function."""
    # Create a script that sources the module and calls the function
    script_content = """#!/bin/bash
    # Set up environment variables
    export DHTL_SESSION_ID="test_session"
    export DHT_DIR="{}"

    # Source the module
    source "{}/modules/dhtl_error_handling.sh"

    # Test log_warning
    log_warning "Test warning message"
    echo "EXIT_CODE=$?"
    """.format(
        os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src/DHT")),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src/DHT")),
    )

    script_path = mock_bash_script(script_content)

    try:
        # Run the script
        result = run_bash_command(script_path)

        # Check the output
        assert "⚠️ WARNING: Test warning message" in result
        assert "EXIT_CODE=0" in result
    finally:
        # Clean up the temporary script
        os.unlink(script_path)


def test_check_dependency():
    """Test the check_dependency function."""
    # Create a script that sources the module and calls the function
    script_content = """#!/bin/bash
    # Set up environment variables
    export DHTL_SESSION_ID="test_session"
    export DHT_DIR="{}"

    # Source the module
    source "{}/modules/dhtl_error_handling.sh"

    # Test check_dependency for a dependency that should exist
    check_dependency "bash"
    echo "EXIT_CODE_1=$?"

    # Test check_dependency for a dependency that should not exist
    check_dependency "non_existent_command"
    echo "EXIT_CODE_2=$?"

    # Test check_dependency for a dependency with custom error message
    check_dependency "non_existent_command" "Custom error message"
    echo "EXIT_CODE_3=$?"
    """.format(
        os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src/DHT")),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src/DHT")),
    )

    script_path = mock_bash_script(script_content)

    try:
        # Run the script
        result = run_bash_command(script_path)

        # Check the output
        assert "EXIT_CODE_1=0" in result
        assert "EXIT_CODE_2=3" in result
        assert "EXIT_CODE_3=3" in result
        assert "Custom error message" in result
    finally:
        # Clean up the temporary script
        os.unlink(script_path)


def test_validate_argument():
    """Test the validate_argument function."""
    # Create a script that sources the module and calls the function
    script_content = """#!/bin/bash
    # Set up environment variables
    export DHTL_SESSION_ID="test_session"
    export DHT_DIR="{}"

    # Source the module
    source "{}/modules/dhtl_error_handling.sh"

    # Test validate_argument with matching pattern
    validate_argument "123" "^[0-9]+$"
    echo "EXIT_CODE_1=$?"

    # Test validate_argument with non-matching pattern
    validate_argument "abc" "^[0-9]+$"
    echo "EXIT_CODE_2=$?"

    # Test validate_argument with custom error message
    validate_argument "abc" "^[0-9]+$" "Custom error message"
    echo "EXIT_CODE_3=$?"
    """.format(
        os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src/DHT")),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src/DHT")),
    )

    script_path = mock_bash_script(script_content)

    try:
        # Run the script
        result = run_bash_command(script_path)

        # Check the output
        assert "EXIT_CODE_1=0" in result
        assert "EXIT_CODE_2=4" in result
        assert "EXIT_CODE_3=4" in result
        assert "Custom error message" in result
    finally:
        # Clean up the temporary script
        os.unlink(script_path)


def test_check_file():
    """Test the check_file function."""
    # Create a script that sources the module and calls the function
    script_content = """#!/bin/bash
    # Set up environment variables
    export DHTL_SESSION_ID="test_session"
    export DHT_DIR="{}"

    # Source the module
    source "{}/modules/dhtl_error_handling.sh"

    # Create a temporary file
    TEMP_FILE=$(mktemp)
    echo "test" > "$TEMP_FILE"

    # Test check_file with existing file
    check_file "$TEMP_FILE"
    echo "EXIT_CODE_1=$?"

    # Test check_file with non-existing file
    check_file "non_existent_file"
    echo "EXIT_CODE_2=$?"

    # Test check_file with custom error message
    check_file "non_existent_file" "Custom error message"
    echo "EXIT_CODE_3=$?"

    # Clean up
    rm -f "$TEMP_FILE"
    """.format(
        os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src/DHT")),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src/DHT")),
    )

    script_path = mock_bash_script(script_content)

    try:
        # Run the script
        result = run_bash_command(script_path)

        # Check the output
        assert "EXIT_CODE_1=0" in result
        assert "EXIT_CODE_2=6" in result
        assert "EXIT_CODE_3=6" in result
        assert "Custom error message" in result
    finally:
        # Clean up the temporary script
        os.unlink(script_path)


def test_create_temp_file():
    """Test the create_temp_file function."""
    # Create a script that sources the module and calls the function
    script_content = """#!/bin/bash
    # Set up environment variables
    export DHTL_SESSION_ID="test_session"
    export DHT_DIR="{}"

    # Source the module
    source "{}/modules/dhtl_error_handling.sh"

    # Test create_temp_file
    TEMP_FILE=$(create_temp_file "test")
    echo "TEMP_FILE=$TEMP_FILE"

    # Check if the file exists
    if [ -f "$TEMP_FILE" ]; then
        echo "TEMP_FILE_EXISTS=true"
    else
        echo "TEMP_FILE_EXISTS=false"
    fi

    # Test create_temp_file with suffix
    TEMP_FILE_WITH_SUFFIX=$(create_temp_file "test" ".txt")
    echo "TEMP_FILE_WITH_SUFFIX=$TEMP_FILE_WITH_SUFFIX"

    # Check if the file has the correct suffix
    if [[ "$TEMP_FILE_WITH_SUFFIX" == *".txt" ]]; then
        echo "SUFFIX_CORRECT=true"
    else
        echo "SUFFIX_CORRECT=false"
    fi
    """.format(
        os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src/DHT")),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src/DHT")),
    )

    script_path = mock_bash_script(script_content)

    try:
        # Run the script
        result = run_bash_command(script_path)

        # Check the output
        assert "TEMP_FILE=" in result
        assert "TEMP_FILE_EXISTS=true" in result
        assert "TEMP_FILE_WITH_SUFFIX=" in result
        assert "SUFFIX_CORRECT=true" in result
    finally:
        # Clean up the temporary script
        os.unlink(script_path)
