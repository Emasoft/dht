import os
import sys
import pytest
from pathlib import Path

# Import helper functions
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from helpers import run_bash_command, mock_bash_script

def test_init_command_creates_structure(tmp_path):
    """Test that the init_command creates the proper directory structure."""
    # Create a script that sources the module and calls the function
    temp_dir = str(tmp_path)
    dht_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src/DHT'))
    script_content = '''#!/bin/bash
    # Set up environment variables
    export DHTL_SESSION_ID="test_session"
    export DHT_DIR="%s"
    export DHTL_DIR="%s"
    export PROJECT_ROOT="%s"
    export PLATFORM="linux"
    
    # Source dependencies
    source "%s/modules/environment.sh"
    source "%s/modules/utils.sh"
    
    # Mock log functions
    function log_info() {
        echo "$@"
    }
    function log_success() {
        echo "$@"
    }
    function log_warning() {
        echo "$@"
    }
    function log_error() {
        echo "$@"
    }
    export -f log_info log_success log_warning log_error
    
    # Source the module
    source "%s/modules/dhtl_init.sh"
    
    # Call the function
    init_command "%s"
    
    # Check if the structure was created properly
    if [ -d "%s/DHT" ] && [ -f "%s/dhtl.sh" ]; then
        echo "STRUCTURE_CREATED=true"
    else
        echo "STRUCTURE_CREATED=false"
    fi
    
    # Check if the orchestrator.sh file exists
    if [ -f "%s/DHT/modules/orchestrator.sh" ]; then
        echo "ORCHESTRATOR_EXISTS=true"
    else
        echo "ORCHESTRATOR_EXISTS=false"
    fi
    
    # Check if the README.md file exists
    if [ -f "%s/DHT/README.md" ]; then
        echo "README_EXISTS=true"
    else
        echo "README_EXISTS=false"
    fi
    
    # Check if the uv_commands.md file exists
    if [ -f "%s/DHT/uv_commands.md" ]; then
        echo "UV_COMMANDS_EXISTS=true"
    else
        echo "UV_COMMANDS_EXISTS=false"
    fi
    
    # Check if the test framework exists
    if [ -f "%s/DHT/tests/conftest.py" ] && [ -f "%s/DHT/tests/pytest.ini" ]; then
        echo "TEST_FRAMEWORK_EXISTS=true"
    else
        echo "TEST_FRAMEWORK_EXISTS=false"
    fi
    ''' % (
        dht_dir,
        os.path.dirname(dht_dir),
        os.path.dirname(dht_dir),
        dht_dir,
        dht_dir,
        dht_dir,
        temp_dir,
        temp_dir,
        temp_dir,
        temp_dir,
        temp_dir,
        temp_dir,
        temp_dir,
        temp_dir
    )
    
    script_path = mock_bash_script(script_content)
    
    try:
        # Run the script
        result = run_bash_command(script_path)
        
        # Check the output
        assert "Initializing DHT" in result
        assert "STRUCTURE_CREATED=true" in result
        assert "ORCHESTRATOR_EXISTS=true" in result
        assert "README_EXISTS=true" in result
        assert "UV_COMMANDS_EXISTS=true" in result
        assert "TEST_FRAMEWORK_EXISTS=true" in result
        
        # Verify the structure on disk
        assert os.path.isdir(os.path.join(temp_dir, "DHT")), "DHT directory not created"
        assert os.path.isdir(os.path.join(temp_dir, "DHT/modules")), "DHT modules directory not created"
        assert os.path.isdir(os.path.join(temp_dir, "DHT/tests")), "DHT tests directory not created"
        assert os.path.isfile(os.path.join(temp_dir, "dhtl.sh")), "dhtl.sh launcher not created"
    finally:
        # Clean up the temporary script
        os.unlink(script_path)

def test_init_command_creates_project_structure(tmp_path):
    """Test that the init_command creates a project structure if one doesn't exist."""
    # Create a script that sources the module and calls the function
    temp_dir = str(tmp_path)
    dht_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src/DHT'))
    script_content = '''#!/bin/bash
    # Set up environment variables
    export DHTL_SESSION_ID="test_session"
    export DHT_DIR="%s"
    export DHTL_DIR="%s"
    export PROJECT_ROOT="%s"
    export PLATFORM="linux"
    
    # Source dependencies
    source "%s/modules/environment.sh"
    source "%s/modules/utils.sh"
    
    # Mock log functions
    function log_info() {
        echo "$@"
    }
    function log_success() {
        echo "$@"
    }
    function log_warning() {
        echo "$@"
    }
    function log_error() {
        echo "$@"
    }
    export -f log_info log_success log_warning log_error
    
    # Source the module
    source "%s/modules/dhtl_init.sh"
    
    # Call the function
    init_command "%s"
    
    # Check if the project structure was created properly
    if [ -d "%s/src" ] && [ -d "%s/tests" ] && [ -d "%s/docs" ]; then
        echo "PROJECT_STRUCTURE_CREATED=true"
    else
        echo "PROJECT_STRUCTURE_CREATED=false"
    fi
    
    # Check if the pyproject.toml file was created
    if [ -f "%s/pyproject.toml" ]; then
        echo "PYPROJECT_EXISTS=true"
    else
        echo "PYPROJECT_EXISTS=false"
    fi
    ''' % (
        dht_dir,
        os.path.dirname(dht_dir),
        os.path.dirname(dht_dir),
        dht_dir,
        dht_dir,
        dht_dir,
        temp_dir,
        temp_dir,
        temp_dir,
        temp_dir,
        temp_dir
    )
    
    script_path = mock_bash_script(script_content)
    
    try:
        # Run the script
        result = run_bash_command(script_path)
        
        # Check the output
        assert "src/" in result and "structure created" in result  # Check for src structure creation
        assert "PROJECT_STRUCTURE_CREATED=true" in result
        assert "PYPROJECT_EXISTS=true" in result
        
        # Verify the structure on disk
        assert os.path.isdir(os.path.join(temp_dir, "src")), "src directory not created"
        assert os.path.isdir(os.path.join(temp_dir, "tests")), "tests directory not created"
        assert os.path.isdir(os.path.join(temp_dir, "docs")), "docs directory not created"
        assert os.path.isfile(os.path.join(temp_dir, "pyproject.toml")), "pyproject.toml not created"
        assert os.path.isfile(os.path.join(temp_dir, "README.md")), "README.md not created"
    finally:
        # Clean up the temporary script
        os.unlink(script_path)

def test_init_command_leaves_existing_structure(tmp_path):
    """Test that the init_command doesn't overwrite existing project structure."""
    # Create a project structure
    temp_dir = str(tmp_path)
    src_dir = os.path.join(temp_dir, "src")
    tests_dir = os.path.join(temp_dir, "tests")
    os.makedirs(src_dir)
    os.makedirs(tests_dir)
    
    # Create a custom pyproject.toml
    pyproject_path = os.path.join(temp_dir, "pyproject.toml")
    with open(pyproject_path, "w") as f:
        f.write("[custom]\ncustom_setting = true\n")
    
    # Create a script that sources the module and calls the function
    dht_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src/DHT'))
    script_content = '''#!/bin/bash
    # Set up environment variables
    export DHTL_SESSION_ID="test_session"
    export DHT_DIR="%s"
    export DHTL_DIR="%s"
    export PROJECT_ROOT="%s"
    export PLATFORM="linux"
    
    # Source dependencies
    source "%s/modules/environment.sh"
    source "%s/modules/utils.sh"
    
    # Mock log functions
    function log_info() {
        echo "$@"
    }
    function log_success() {
        echo "$@"
    }
    function log_warning() {
        echo "$@"
    }
    function log_error() {
        echo "$@"
    }
    export -f log_info log_success log_warning log_error
    
    # Source the module
    source "%s/modules/dhtl_init.sh"
    
    # Call the function
    init_command "%s"
    
    # Check if the custom pyproject.toml was preserved
    if grep -q "custom_setting" "%s/pyproject.toml"; then
        echo "CUSTOM_PYPROJECT_PRESERVED=true"
    else
        echo "CUSTOM_PYPROJECT_PRESERVED=false"
    fi
    ''' % (
        dht_dir,
        os.path.dirname(dht_dir),
        os.path.dirname(dht_dir),
        dht_dir,
        dht_dir,
        dht_dir,
        temp_dir,
        temp_dir
    )
    
    script_path = mock_bash_script(script_content)
    
    try:
        # Run the script
        result = run_bash_command(script_path)
        
        # Check the output
        assert "pyproject.toml already exists" in result  # This indicates existing structure was detected
        assert "CUSTOM_PYPROJECT_PRESERVED=true" in result
        
        # Verify the file was preserved
        with open(pyproject_path, "r") as f:
            content = f.read()
            assert "custom_setting = true" in content, "Custom pyproject.toml was overwritten"
    finally:
        # Clean up the temporary script
        os.unlink(script_path)