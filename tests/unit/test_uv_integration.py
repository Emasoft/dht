import os
import sys

# Import helper functions
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from helpers import mock_bash_script, run_bash_command


def test_uv_is_available():
    """Test the uv_is_available function."""
    # Create a script that sources the module and calls the function
    dht_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src/DHT"))
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))

    script_content = f'''#!/bin/bash
    # Set up environment variables
    export DHTL_SESSION_ID="test_session"
    export DHT_DIR="{dht_dir}"
    export PROJECT_ROOT="{project_root}"

    # Source dependencies
    source "{dht_dir}/modules/environment.sh"

    # Source the module
    source "{dht_dir}/modules/dhtl_uv.sh"

    # Mock the command function to simulate UV not being in PATH
    command() {{
        if [[ "$1" == "-v" ]] && [[ "$2" == "uv" ]]; then
            return 1  # UV not found in PATH
        else
            builtin command "$@"
        fi
    }}
    export -f command

    # Create test directory with mock venv
    test_dir="{project_root}/test_uv_dir"
    mkdir -p "$test_dir/.venv/bin"
    touch "$test_dir/.venv/bin/uv"
    chmod +x "$test_dir/.venv/bin/uv"

    # Test with uv available in venv
    uv_is_available "$test_dir/.venv" && echo "UV_AVAILABLE_IN_VENV=true" || echo "UV_AVAILABLE_IN_VENV=false"

    # Test with uv not available
    rm "$test_dir/.venv/bin/uv"
    uv_is_available "$test_dir/.venv" && echo "UV_AVAILABLE_AFTER_REMOVAL=true" || echo "UV_AVAILABLE_AFTER_REMOVAL=false"

    # Clean up
    rm -rf "$test_dir"
    '''

    script_path = mock_bash_script(script_content)

    try:
        # Run the script
        result = run_bash_command(script_path)

        # Check the output
        assert "UV_AVAILABLE_IN_VENV=true" in result
        assert "UV_AVAILABLE_AFTER_REMOVAL=false" in result
    finally:
        # Clean up the temporary script
        os.unlink(script_path)
        # Clean up test directory if it exists
        test_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../test_uv_dir"))
        if os.path.exists(test_dir):
            import shutil

            shutil.rmtree(test_dir)


def test_get_uv_command():
    """Test the get_uv_command function."""
    # Create a script that sources the module and calls the function
    dht_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src/DHT"))
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))

    script_content = f'''#!/bin/bash
    # Set up environment variables
    export DHTL_SESSION_ID="test_session"
    export DHT_DIR="{dht_dir}"
    export PROJECT_ROOT="{project_root}"

    # Source dependencies
    source "{dht_dir}/modules/environment.sh"

    # Source the module
    source "{dht_dir}/modules/dhtl_uv.sh"

    # Create test directory with mock venv
    test_dir="{project_root}/test_uv_dir"
    mkdir -p "$test_dir/.venv/bin"
    touch "$test_dir/.venv/bin/uv"
    chmod +x "$test_dir/.venv/bin/uv"

    # Test with uv available in venv
    cmd=$(get_uv_command "$test_dir/.venv")
    echo "UV_COMMAND=$cmd"

    # Test with uv not available
    rm "$test_dir/.venv/bin/uv"
    cmd=$(get_uv_command "$test_dir/.venv")
    echo "UV_COMMAND_AFTER_REMOVAL=$cmd"

    # Clean up
    rm -rf "$test_dir"
    '''

    script_path = mock_bash_script(script_content)

    try:
        # Run the script
        result = run_bash_command(script_path)

        # Check the output
        assert "UV_COMMAND=" in result
        test_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../test_uv_dir"))
        expected_path = f"{test_dir}/.venv/bin/uv"
        assert f"UV_COMMAND={expected_path}" in result
        # After removal, the command should be empty or fallback to global uv
        assert "UV_COMMAND_AFTER_REMOVAL=" in result
    finally:
        # Clean up the temporary script
        os.unlink(script_path)
        # Clean up test directory if it exists
        test_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../test_uv_dir"))
        if os.path.exists(test_dir):
            import shutil

            shutil.rmtree(test_dir)


def test_uv_create_venv():
    """Test the uv_create_venv function."""
    # Create a script that sources the module and calls the function
    dht_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src/DHT"))
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))

    script_content = f'''#!/bin/bash
    # Set up environment variables
    export DHTL_SESSION_ID="test_session"
    export DHT_DIR="{dht_dir}"
    export PROJECT_ROOT="{project_root}"

    # Source dependencies
    source "{dht_dir}/modules/environment.sh"

    # Source the module
    source "{dht_dir}/modules/dhtl_uv.sh"

    # Create test directory
    test_dir="{project_root}/test_uv_dir"
    mkdir -p "$test_dir"

    # Mock uv command
    function uv() {{
        if [ "$1" == "venv" ]; then
            # Create mock venv structure
            mkdir -p "$2/bin"
            touch "$2/bin/activate"
            echo "#!/bin/bash" > "$2/bin/python"
            chmod +x "$2/bin/python"
            echo "Created mock venv at $2"
            # Check if Python version was specified
            if [ "$3" == "--python" ] && [ -n "$4" ]; then
                echo "Using Python version: $4"
            fi
        else
            echo "Mock uv command called with args: $@"
        fi
    }}
    export -f uv

    # Mock get_uv_command to return 'uv'
    function get_uv_command() {{
        echo "uv"
    }}
    export -f get_uv_command

    # Test creating a venv
    uv_create_venv "$test_dir/.venv"

    # Check if venv exists
    if [ -d "$test_dir/.venv" ] && [ -f "$test_dir/.venv/bin/activate" ]; then
        echo "VENV_CREATED=true"
    else
        echo "VENV_CREATED=false"
    fi

    # Test with Python version
    uv_create_venv "$test_dir/.venv2" "3.10"

    # Clean up
    rm -rf "$test_dir"
    '''

    script_path = mock_bash_script(script_content)

    try:
        # Run the script
        result = run_bash_command(script_path)

        # Check the output
        assert "Creating virtual environment" in result
        assert "Created mock venv" in result
        assert "VENV_CREATED=true" in result
        # Check that Python version was passed
        assert "3.10" in result
    finally:
        # Clean up the temporary script
        os.unlink(script_path)
        # Clean up test directory if it exists
        test_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../test_uv_dir"))
        if os.path.exists(test_dir):
            import shutil

            shutil.rmtree(test_dir)


def test_uv_command_help():
    """Test the uv_command help function."""
    # Create a script that sources the module and calls the function
    dht_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src/DHT"))
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))

    script_content = f'''#!/bin/bash
    # Set up environment variables
    export DHTL_SESSION_ID="test_session"
    export DHT_DIR="{dht_dir}"
    export PROJECT_ROOT="{project_root}"

    # Source dependencies
    source "{dht_dir}/modules/environment.sh"

    # Source the module
    source "{dht_dir}/modules/dhtl_uv.sh"

    # Call the function with help
    uv_command help
    '''

    script_path = mock_bash_script(script_content)

    try:
        # Run the script
        result = run_bash_command(script_path)

        # Check for help content
        assert "UV Command Usage:" in result
        assert "setup" in result
        assert "venv" in result
        assert "sync" in result
        assert "install" in result
        assert "tool run" in result
        assert "tool install" in result
        assert "build" in result
        assert "help" in result
    finally:
        # Clean up the temporary script
        os.unlink(script_path)
