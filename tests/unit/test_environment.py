import os
import sys

import pytest

# Import helper functions
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from helpers import create_mock_file, mock_bash_script, run_bash_command


def test_detect_active_venv(monkeypatch):
    """Test the detect_active_venv function."""
    # Create a script that sources the module and calls the function
    dht_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src/DHT"))
    script_content = f'''#!/bin/bash
    source "{dht_dir}/modules/environment.sh"
    detect_active_venv
    '''

    script_path = mock_bash_script(script_content)

    try:
        # Run with no active venv
        result = run_bash_command(script_path, env={"VIRTUAL_ENV": "", "CONDA_PREFIX": ""})
        assert result.strip() == ""

        # Run with VIRTUAL_ENV set
        mock_venv_path = "/path/to/venv"
        result = run_bash_command(script_path, env={"VIRTUAL_ENV": mock_venv_path, "CONDA_PREFIX": ""})
        assert result.strip() == mock_venv_path

        # Run with CONDA_PREFIX set
        mock_conda_path = "/path/to/conda"
        result = run_bash_command(script_path, env={"VIRTUAL_ENV": "", "CONDA_PREFIX": mock_conda_path})
        assert result.strip() == mock_conda_path

        # Run with both set (VIRTUAL_ENV should take precedence)
        result = run_bash_command(script_path, env={"VIRTUAL_ENV": mock_venv_path, "CONDA_PREFIX": mock_conda_path})
        assert result.strip() == mock_venv_path
    finally:
        # Clean up the temporary script
        os.unlink(script_path)


def test_env_command_output(mock_dht_env):
    """Test the env_command function produces expected output."""
    # Create a script that sources the module and calls the function
    dht_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src/DHT"))
    script_content = f'''#!/bin/bash
    # Set up required environment variables
    export DHTL_SESSION_ID="test_session"
    export DHT_DIR="{dht_dir}"
    export PROJECT_ROOT="{os.path.dirname(__file__)}"

    # Source dependencies
    source "{dht_dir}/modules/environment.sh"
    source "{dht_dir}/modules/dhtl_environment_2.sh"

    # Mock the run_diagnostics function
    function run_diagnostics() {{
        echo "Mock diagnostics running..."
        # Create a minimal report file
        cat > "$DHT_DIR/.dht_environment_report.json" <<EOF
{{
    "system": {{
        "platform": "linux",
        "python_version": "3.10.0"
    }},
    "tools": {{
        "git": "installed",
        "docker": "installed"
    }}
}}
EOF
        return 0
    }}
    export -f run_diagnostics

    # Mock log_error function
    function log_error() {{
        echo "ERROR: $1"
        return 0
    }}
    export -f log_error

    env_command
    '''

    script_path = mock_bash_script(script_content)

    try:
        # Run the script and check for expected output patterns
        result = run_bash_command(script_path, env=mock_dht_env)

        # Check for the main header
        assert "Development Helper Toolkit Environment Information" in result

        # Check that the JSON report was displayed
        assert '"system"' in result
        assert '"platform"' in result
        assert '"python_version"' in result
        assert '"tools"' in result
        assert '"git"' in result
        assert '"docker"' in result
    finally:
        # Clean up the temporary script
        os.unlink(script_path)


@pytest.mark.skip(reason="setup_environment function was removed - canonical logic is in dhtl_init.sh")
def test_setup_environment(tmp_path, mock_dht_env):
    """Test the setup_environment function."""
    # Create a minimal script to call setup_environment
    project_root = os.path.join(str(tmp_path), "test_project")
    os.makedirs(project_root, exist_ok=True)

    # Create a pyproject.toml file
    create_mock_file(
        project_root,
        "pyproject.toml",
        '[build-system]\nrequires = ["setuptools>=42"]\nbuild-backend = "setuptools.build_meta"\n',
    )

    # Create a script that sources the module and calls the function
    dht_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src/DHT"))
    script_content = f'''#!/bin/bash
    source "{dht_dir}/modules/environment.sh"

    # Create a mock function to simulate uv
    function uv() {{
        echo "Running uv $@"
        if [ "$1" == "venv" ]; then
            # Create a mock venv structure
            mkdir -p "$2/bin"
            touch "$2/bin/activate"
            echo "#!/bin/bash" > "$2/bin/python"
            chmod +x "$2/bin/python"
        fi
    }}
    export -f uv

    # Mock Python
    function python3() {{
        echo "Python 3.10.0"
    }}
    export -f python3

    # Call the function with a mock venv directory
    setup_environment "{project_root}" "{project_root}/.venv" "linux" "3.10"

    # Check if the directory was created
    if [ -d "{project_root}/.venv" ]; then
        echo "VENV_CREATED"
    fi
    '''

    script_path = mock_bash_script(script_content)

    try:
        # Run the script
        result = run_bash_command(script_path, env=mock_dht_env)

        # Check if the venv was "created" (our mock function should have created it)
        assert "VENV_CREATED" in result
        assert "Running uv venv" in result
    finally:
        # Clean up the temporary script
        os.unlink(script_path)
