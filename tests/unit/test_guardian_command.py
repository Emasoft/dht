import os
import sys

# Import helper functions
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from helpers import mock_bash_script, run_bash_command


def test_guardian_command_status():
    """Test the guardian_command function with status subcommand."""
    # Create a script that sources the module and calls the function
    dht_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src/DHT'))
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))

    script_content = f'''#!/bin/bash
    # Set up environment variables
    export DHTL_SESSION_ID="test_session"
    export DHT_DIR="{dht_dir}"
    export PROJECT_ROOT="{project_root}"

    # Create mock guardian files
    mkdir -p "$DHT_DIR/.process_guardian"
    echo "12345" > "$DHT_DIR/.process_guardian/process_watchdog.pid"

    # Mock ps command to always return true
    function ps() {{
        # If checking for PID, return success
        if [ "$1" == "-p" ]; then
            return 0  # Process exists
        fi
        return 1  # Default to failure
    }}
    export -f ps

    # Mock log functions
    function log_info() {{
        echo "$@"
    }}
    function log_success() {{
        echo "$@"
    }}
    function log_warning() {{
        echo "$@"
    }}
    function log_error() {{
        echo "$@"
    }}
    export -f log_info log_success log_warning log_error

    # Source the module
    source "{dht_dir}/modules/dhtl_guardian_command.sh"

    # Call the function
    guardian_command status
    '''

    script_path = mock_bash_script(script_content)

    try:
        # Run the script
        result = run_bash_command(script_path)

        # Check the output
        assert "Checking Process Guardian status" in result
        assert "Process Guardian is running with PID: 12345" in result
    finally:
        # Clean up the temporary script and mock guardian files
        os.unlink(script_path)
        guardian_dir = os.path.join(dht_dir, '.process_guardian')
        if os.path.exists(guardian_dir):
            import shutil
            shutil.rmtree(guardian_dir)

def test_guardian_command_start():
    """Test the guardian_command function with start subcommand."""
    # Create a script that sources the module and calls the function
    dht_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src/DHT'))
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))

    script_content = f'''#!/bin/bash
    # Set up environment variables
    export DHTL_SESSION_ID="test_session"
    export DHT_DIR="{dht_dir}"
    export PROJECT_ROOT="{project_root}"

    # Create mock guardian directory
    mkdir -p "$DHT_DIR/.process_guardian"

    # Create mock process-guardian-watchdog.py
    echo '#!/usr/bin/env python3
    import sys
    import os

    if len(sys.argv) > 1 and sys.argv[1] == "start":
        # Write a mock PID file
        with open(os.path.join(os.environ["DHT_DIR"], ".process_guardian/process_watchdog.pid"), "w") as f:
            f.write("54321")
        print("Process Guardian started.")
        sys.exit(0)
    else:
        print("Usage: process-guardian-watchdog.py start|stop|status")
        sys.exit(1)
    ' > "$DHT_DIR/process-guardian-watchdog.py"
    chmod +x "$DHT_DIR/process-guardian-watchdog.py"

    # Mock Python and related commands
    function python3() {{
        # Handle psutil check
        if [[ "$1" == "-c" ]] && [[ "$2" == *"import psutil"* ]]; then
            return 0  # psutil is available
        fi

        # Handle running the watchdog script
        if [[ "$1" == *"process-guardian-watchdog.py" ]] && [[ "$2" == "start" ]]; then
            # Create the PID file as if the watchdog started
            echo "54321" > "$DHT_DIR/.process_guardian/process_watchdog.pid"
            return 0
        fi

        return 0
    }}
    export -f python3

    # Mock get_python_cmd function to return python3
    function get_python_cmd() {{
        echo "python3"
    }}
    export -f get_python_cmd

    function ps() {{
        # If checking for PID, return success
        if [ "$1" == "-p" ]; then
            return 0  # Process exists
        fi
        return 1  # Default to failure
    }}
    export -f ps

    # Mock log functions
    function log_info() {{
        echo "$@"
    }}
    function log_success() {{
        echo "$@"
    }}
    function log_warning() {{
        echo "$@"
    }}
    function log_error() {{
        echo "$@"
    }}
    export -f log_info log_success log_warning log_error

    # Source the module
    source "{dht_dir}/modules/dhtl_guardian_command.sh"

    # Call the function
    guardian_command start
    '''

    script_path = mock_bash_script(script_content)

    try:
        # Run the script
        result = run_bash_command(script_path)

        # Check the output
        assert "Starting Process Guardian" in result
        assert "Process Guardian started successfully with PID: 54321" in result
    finally:
        # Clean up the temporary script and mock guardian files
        os.unlink(script_path)
        mock_watchdog = os.path.join(dht_dir, 'process-guardian-watchdog.py')
        if os.path.exists(mock_watchdog):
            os.unlink(mock_watchdog)
        guardian_dir = os.path.join(dht_dir, '.process_guardian')
        if os.path.exists(guardian_dir):
            import shutil
            shutil.rmtree(guardian_dir)

def test_guardian_command_stop():
    """Test the guardian_command function with stop subcommand."""
    # Create a script that sources the module and calls the function
    dht_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src/DHT'))
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))

    script_content = f'''#!/bin/bash
    # Set up environment variables
    export DHTL_SESSION_ID="test_session"
    export DHT_DIR="{dht_dir}"
    export PROJECT_ROOT="{project_root}"

    # Create mock guardian files
    mkdir -p "$DHT_DIR/.process_guardian"
    echo "67890" > "$DHT_DIR/.process_guardian/process_watchdog.pid"

    # Mock ps and kill commands
    ps_call_count=0
    function ps() {{
        # If checking for PID, return success for first call, failure for second
        if [ "$1" == "-p" ]; then
            if [ $ps_call_count -eq 0 ]; then
                ps_call_count=$((ps_call_count+1))
                return 0  # Process exists on first check
            else
                return 1  # Process doesn't exist on second check (after kill)
            fi
        fi
        return 1  # Default to failure
    }}
    export -f ps

    function kill() {{
        # Mock kill command
        echo "Mock kill command called with args: $@"
        return 0
    }}
    export -f kill

    # Mock log functions
    function log_info() {{
        echo "$@"
    }}
    function log_success() {{
        echo "$@"
    }}
    function log_warning() {{
        echo "$@"
    }}
    function log_error() {{
        echo "$@"
    }}
    export -f log_info log_success log_warning log_error

    # Source the module
    source "{dht_dir}/modules/dhtl_guardian_command.sh"

    # Call the function
    guardian_command stop
    '''

    script_path = mock_bash_script(script_content)

    try:
        # Run the script
        result = run_bash_command(script_path)

        # Check the output
        assert "Stopping Process Guardian" in result
        assert "Sending SIGTERM to Process Guardian" in result
        assert "Process Guardian stopped successfully" in result
    finally:
        # Clean up the temporary script and mock guardian files
        os.unlink(script_path)
        guardian_dir = os.path.join(dht_dir, '.process_guardian')
        if os.path.exists(guardian_dir):
            import shutil
            shutil.rmtree(guardian_dir)

def test_guardian_help():
    """Test the guardian help command."""
    # Create a script that sources the module and calls the function
    dht_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src/DHT'))

    script_content = f'''#!/bin/bash
    # Set up environment variables
    export DHTL_SESSION_ID="test_session"
    export DHT_DIR="{dht_dir}"

    # Mock log functions
    function log_info() {{
        echo "$@"
    }}
    function log_success() {{
        echo "$@"
    }}
    function log_warning() {{
        echo "$@"
    }}
    function log_error() {{
        echo "$@"
    }}
    export -f log_info log_success log_warning log_error

    # Source the module
    source "{dht_dir}/modules/dhtl_guardian_command.sh"

    # Call the function
    show_guardian_help
    '''

    script_path = mock_bash_script(script_content)

    try:
        # Run the script
        result = run_bash_command(script_path)

        # Check for help content
        assert "Process Guardian Command Usage:" in result
        assert "status" in result
        assert "start" in result
        assert "stop" in result
        assert "restart" in result
        assert "help" in result
    finally:
        # Clean up the temporary script
        os.unlink(script_path)
