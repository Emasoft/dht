import os
import subprocess
import shlex
from pathlib import Path
import tempfile
import shutil

def run_dhtl_command(command, cwd=None, env=None, check=True, capture_output=True):
    """
    Run a DHTL command and return the result.
    
    Args:
        command (str): The command to run (e.g., "test", "lint")
        cwd (str, optional): The working directory to run the command in
        env (dict, optional): Environment variables to use
        check (bool, optional): Whether to check the return code
        capture_output (bool, optional): Whether to capture stdout/stderr
        
    Returns:
        subprocess.CompletedProcess: The completed process
    """
    # Determine the source DHT directory (where the original dhtl.sh and modules are)
    # This assumes tests are run from the project root or DHT_SOURCE_DIR is set.
    source_dht_dir = Path(os.environ.get("DHT_SOURCE_DIR", Path(__file__).parent.parent.parent)) # Assumes helpers.py is in DHT/tests/
    if not (source_dht_dir / "dhtl.sh").exists():
        # Fallback if DHT_SOURCE_DIR is not set and script is not in expected location
        source_dht_dir = Path(os.environ.get("DHT_DIR", source_dht_dir))


    with tempfile.TemporaryDirectory() as temp_project_root_str:
        temp_project_root = Path(temp_project_root_str)

        # Create a mock DHT structure within the temporary project root
        temp_dht_dir = temp_project_root / "DHT"
        temp_dht_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy dhtl.sh
        source_dhtl_script = source_dht_dir / "dhtl.sh"
        if source_dhtl_script.exists():
            shutil.copy(source_dhtl_script, temp_dht_dir / "dhtl.sh")
            (temp_dht_dir / "dhtl.sh").chmod(0o755)
        else:
            raise FileNotFoundError(f"Source dhtl.sh not found at {source_dhtl_script}")

        # Copy modules directory
        source_modules_dir = source_dht_dir / "modules"
        temp_modules_dir = temp_dht_dir / "modules"
        if source_modules_dir.is_dir():
            shutil.copytree(source_modules_dir, temp_modules_dir, dirs_exist_ok=True)
        else:
            raise FileNotFoundError(f"Source modules directory not found at {source_modules_dir}")

        # Prepare the command to run the copied dhtl.sh
        dhtl_executable = temp_dht_dir / "dhtl.sh"
        full_command = [str(dhtl_executable)]
        
        if command:
            if isinstance(command, list):
                full_command.extend(command)
            else:
                full_command.extend(shlex.split(command))
        
        # Determine effective CWD: if cwd is provided, it's relative to temp_project_root or absolute
        effective_cwd = Path(cwd) if cwd else temp_project_root
        if not effective_cwd.is_absolute():
            effective_cwd = temp_project_root / effective_cwd
        effective_cwd.mkdir(parents=True, exist_ok=True) # Ensure CWD exists

        # Prepare environment
        run_env = os.environ.copy()
        if env:
            run_env.update(env)
        # Ensure PROJECT_ROOT is set correctly for the dhtl script within the temp env
        run_env["PROJECT_ROOT"] = str(temp_project_root)
        run_env["DHT_DIR"] = str(temp_dht_dir) # dhtl.sh expects DHT_DIR to be its own location

        return subprocess.run(
            full_command,
            cwd=str(effective_cwd),
            env=run_env,
            check=check,
            capture_output=capture_output,
            text=True
        )

def run_bash_command(command, cwd=None, env=None):
    """
    Run a bash command and return the output.
    
    Args:
        command (str): The bash command to run
        cwd (str, optional): The working directory to run the command in
        env (dict, optional): Environment variables to use
        
    Returns:
        str: The command output (both stdout and stderr combined)
    """
    result = subprocess.run(
        ["bash", "-c", command],
        cwd=cwd,
        env=env,
        check=True,
        capture_output=True,
        text=True
    )
    # Combine stdout and stderr for tests that expect error messages
    output = result.stdout
    if result.stderr:
        output += result.stderr
    return output.strip()

def create_mock_file(directory, filename, content=""):
    """Create a mock file with the given content."""
    file_path = Path(directory) / filename
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content)
    return file_path

def mock_bash_script(script_content):
    """
    Create a temporary bash script with the given content and return its path.
    
    Args:
        script_content (str): The content of the script
        
    Returns:
        str: The path to the temporary script
    """
    fd, script_path = tempfile.mkstemp(suffix=".sh")
    os.close(fd)
    
    with open(script_path, "w") as f:
        f.write(script_content)
    
    os.chmod(script_path, 0o755)
    return script_path

def verify_dhtl_components(project_dir):
    """
    Verify that the essential DHT components are present in the project.
    
    Args:
        project_dir (str): The project directory
        
    Returns:
        bool: True if all components are present, False otherwise
    """
    required_files = [
        "dhtl.sh",
        "DHT/README.md",
        "DHT/modules/core.sh",
        "DHT/modules/environment.sh",
        "DHT/modules/commands.sh"
    ]
    
    for file_path in required_files:
        if not (Path(project_dir) / file_path).exists():
            return False
    
    return True
