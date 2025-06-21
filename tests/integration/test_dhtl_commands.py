import os
import shutil
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

# Assuming conftest.py provides mock_project_dir fixture
# Assuming run_dhtl_command helper from test_dhtl_setup_init


def run_dhtl_command(command: list, cwd: Path, env: dict = None, timeout: int = 300):
    """Helper to run dhtl commands via subprocess."""
    # Use Python implementation instead of shell script
    import sys

    cmd_list = [sys.executable, "-m", "src.DHT.dhtl"] + command
    print(f"\nRunning command: {' '.join(cmd_list)} in {cwd}")

    # Use a fresh environment or merge with provided
    run_env = os.environ.copy()
    if env:
        run_env.update(env)
    # Ensure PROJECT_ROOT is set correctly for the script execution if not already mocked
    run_env["PROJECT_ROOT"] = str(cwd)
    run_env["DHT_DIR"] = str(cwd / "DHT")  # Ensure DHT_DIR points inside mock project

    # Add the DHT project directory to PYTHONPATH so the module can be found
    dht_project_root = Path(__file__).parent.parent.parent  # tests/integration -> tests -> dht
    python_path = run_env.get("PYTHONPATH", "")
    run_env["PYTHONPATH"] = f"{dht_project_root}:{python_path}" if python_path else str(dht_project_root)

    # Ensure PATH includes uv if installed globally, otherwise setup might fail early
    uv_path = shutil.which("uv")
    if uv_path:
        run_env["PATH"] = f"{os.path.dirname(uv_path)}:{run_env.get('PATH', '')}"

    process = subprocess.run(cmd_list, capture_output=True, text=True, env=run_env, cwd=cwd, timeout=timeout)
    print("STDOUT:")
    print(process.stdout)
    print("STDERR:")
    print(process.stderr)
    return process


# --- Setup Fixture ---
@pytest.fixture(scope="function")  # Use function scope for isolation
def setup_project(mock_project_dir):
    """Fixture to run dhtl setup once per test function."""
    # Create basic pyproject.toml for setup to succeed
    (mock_project_dir / "pyproject.toml").write_text("""
[project]
name = "cmd-test-proj"
version = "0.1.0"
requires-python = ">=3.9"
[project.optional-dependencies]
dev = ["pytest", "pytest-cov", "ruff", "black", "pre-commit", "tox", "uv"] # Added pytest-cov
    """)
    # Create dummy src file for linters/coverage
    (mock_project_dir / "src").mkdir(exist_ok=True)
    (mock_project_dir / "src" / "cmd_test_proj").mkdir(exist_ok=True)
    (mock_project_dir / "src" / "cmd_test_proj" / "__init__.py").write_text("__version__ = '0.1.0'")
    (mock_project_dir / "src" / "cmd_test_proj" / "main.py").write_text("def main():\n    print('hello')\n")
    # Create dummy test file
    (mock_project_dir / "tests").mkdir(exist_ok=True)
    (mock_project_dir / "tests" / "test_main.py").write_text("def test_success(): assert True")
    # Create dummy shell script for 'dhtl script' command test
    dht_scripts_dir = mock_project_dir / "DHT" / "scripts"
    dht_scripts_dir.mkdir(parents=True, exist_ok=True)
    (dht_scripts_dir / "hello.sh").write_text("#!/bin/bash\necho 'Hello from DHT script!'\necho \"Args: $@\"\n")
    (dht_scripts_dir / "hello.sh").chmod(0o755)

    # Run setup
    result = run_dhtl_command(["setup"], cwd=mock_project_dir)
    assert result.returncode == 0, "Setup fixture failed"
    # Activate venv for subsequent commands in tests (by modifying PATH)
    # Note: This affects the test process environment, not the subprocess environment directly.
    # The run_dhtl_command helper ensures the subprocess uses the correct PATH.
    os.environ["PATH"] = f"{mock_project_dir / '.venv' / 'bin'}:{os.environ.get('PATH', '')}"
    yield mock_project_dir
    # Teardown: Restore PATH if needed (though test isolation should handle this)


# --- Test Cases ---


@pytest.mark.integration
def test_dhtl_lint_command(setup_project):
    """Test the 'dhtl lint' command."""
    # Arrange (setup_project fixture already ran setup)
    # Create a pre-commit config to test that path
    (setup_project / ".pre-commit-config.yaml").write_text("""
repos:
-   repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0
    hooks:
    -   id: check-yaml
    """)
    # Run setup again to install hooks
    run_dhtl_command(["setup"], cwd=setup_project)

    # Act
    result = run_dhtl_command(["lint"], cwd=setup_project)

    # Assert
    assert result.returncode == 0
    assert "Running linters on project..." in result.stdout
    assert "Running pre-commit hooks" in result.stdout  # Check it used pre-commit
    assert "check-yaml" in result.stdout
    assert "Passed" in result.stdout
    assert "All linting checks passed" in result.stdout


@pytest.mark.integration
def test_dhtl_format_command(setup_project):
    """Test the 'dhtl format' command."""
    # Arrange
    # Create a file that needs formatting
    badly_formatted_file = setup_project / "src" / "cmd_test_proj" / "bad_format.py"
    badly_formatted_file.write_text("import os, sys\ndef my_func(  x ):\n  return x+1\n")
    original_content = badly_formatted_file.read_text()

    # Act
    result = run_dhtl_command(["format"], cwd=setup_project)

    # Assert
    assert result.returncode == 0
    assert "Formatting code in project..." in result.stdout
    assert "Running ruff format..." in result.stdout  # Assuming ruff is default
    assert "Running ruff check --fix..." in result.stdout
    # The message changed slightly in the script
    assert (
        "Code formatting completed successfully" in result.stdout
        or "All formatting completed successfully" in result.stdout
    )
    # Check if the file was actually changed
    new_content = badly_formatted_file.read_text()
    assert new_content != original_content
    assert "import os" in new_content  # Check for some formatting change
    assert "import sys" in new_content
    assert "def my_func(x):" in new_content


@pytest.mark.integration
def test_dhtl_build_command(setup_project):
    """Test the 'dhtl build' command."""
    # Arrange
    dist_dir = setup_project / "dist"
    if dist_dir.exists():  # Clean previous build
        shutil.rmtree(dist_dir)

    # Act
    result = run_dhtl_command(["build", "--no-checks"], cwd=setup_project)  # Skip checks for speed

    # Assert
    assert result.returncode == 0
    assert "Building Python package..." in result.stdout
    assert "Building with uv..." in result.stdout  # Check it used uv
    assert "Build completed successfully" in result.stdout
    assert dist_dir.is_dir()
    # Check for wheel and sdist
    built_files = list(dist_dir.glob("*"))
    assert any(f.name.endswith(".whl") for f in built_files), "Wheel file not found"
    assert any(f.name.endswith(".tar.gz") for f in built_files), "Source distribution not found"


@pytest.mark.integration
def test_dhtl_clean_command(setup_project):
    """Test the 'dhtl clean' command."""
    # Arrange
    cache_dir = setup_project / "DHT" / ".dht_cache"
    guardian_dir = setup_project / "DHT" / ".process_guardian"
    report_file = setup_project / "DHT" / ".dht_environment_report.json"
    cache_dir.mkdir(parents=True, exist_ok=True)
    guardian_dir.mkdir(parents=True, exist_ok=True)
    (cache_dir / "dummy_cache.txt").touch()
    (guardian_dir / "dummy_log.log").touch()
    report_file.touch()

    # Act
    result = run_dhtl_command(["clean"], cwd=setup_project)

    # Assert
    assert result.returncode == 0
    assert "Cleaning Development Helper Toolkit caches" in result.stdout
    assert "Removing cache directory" in result.stdout
    assert "Removing guardian logs" in result.stdout
    assert "Removing diagnostics report" in result.stdout
    assert not (cache_dir / "dummy_cache.txt").exists()
    assert not (guardian_dir / "dummy_log.log").exists()
    assert not report_file.exists()
    # Check dirs were recreated if needed (cache dir is)
    assert cache_dir.is_dir()


@pytest.mark.integration
def test_dhtl_commit_command(setup_project):
    """Test the 'dhtl commit' command (basic execution)."""
    # Arrange
    # Initialize git repo
    subprocess.run(["git", "init"], cwd=setup_project, capture_output=True, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=setup_project, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=setup_project, check=True)
    # Create a change
    (setup_project / "new_file.txt").write_text("commit test")

    # Act
    # Run commit with a message, skip checks for simplicity in this test
    result = run_dhtl_command(["commit", "--no-checks", "--no-backup", "-m", "Test commit via dhtl"], cwd=setup_project)

    # Assert
    assert result.returncode == 0
    assert "Committing changes to git..." in result.stdout
    assert "Staging all changes..." in result.stdout
    assert "Committing changes with message: Test commit via dhtl" in result.stdout
    assert "Changes committed successfully" in result.stdout

    # Verify commit exists
    log_result = subprocess.run(
        ["git", "log", "-1", "--pretty=%s"], cwd=setup_project, capture_output=True, text=True, check=True
    )
    assert "Test commit via dhtl" in log_result.stdout


@pytest.mark.integration
def test_dhtl_coverage_command(setup_project):
    """Test the 'dhtl coverage' command."""
    # Arrange
    coverage_dir = setup_project / "coverage_report"
    if coverage_dir.exists():
        shutil.rmtree(coverage_dir)

    # Act
    result = run_dhtl_command(["coverage"], cwd=setup_project)

    # Assert
    assert result.returncode == 0
    assert "Running test coverage on project..." in result.stdout
    assert "Coverage analysis completed successfully" in result.stdout
    assert (coverage_dir / "index.html").exists()
    assert (coverage_dir / "coverage.xml").exists()


@pytest.mark.integration
@patch("subprocess.run")
def test_dhtl_publish_command(mock_subprocess, setup_project):
    """Test the 'dhtl publish' command (mocks underlying script)."""
    # Arrange
    # Mock the actual publish script to avoid network calls/git pushes
    mock_subprocess.return_value = subprocess.CompletedProcess(
        args=[], returncode=0, stdout="Mock publish script executed", stderr=""
    )
    # Create a dummy publish script for dhtl to find
    publish_script = setup_project / "DHT" / "publish_to_github.sh"
    publish_script.touch(mode=0o755)

    # Act
    result = run_dhtl_command(["publish", "--skip-tests", "--skip-linters", "--no-backup"], cwd=setup_project)

    # Assert
    assert result.returncode == 0
    assert "Publishing to GitHub..." in result.stdout
    assert "Skipping backup as requested" in result.stdout
    assert f"Running publish script: {publish_script} --skip-tests --skip-linters" in result.stdout
    assert "Project published to GitHub successfully" in result.stdout
    # Check that the mock subprocess was called (via run_with_guardian -> bash)
    assert any(
        str(publish_script) in call_args[0] and "--skip-tests" in call_args[0] and "--skip-linters" in call_args[0]
        for call_args in mock_subprocess.call_args_list
    ), "Publish script was not called with expected arguments"


@pytest.mark.integration
@patch("subprocess.run")
def test_dhtl_rebase_command(mock_subprocess, setup_project):
    """Test the 'dhtl rebase' command (mocks git and zip)."""
    # Arrange
    # Initialize git repo
    subprocess.run(["git", "init"], cwd=setup_project, capture_output=True, check=True)
    subprocess.run(["git", "remote", "add", "origin", "mock-remote-url"], cwd=setup_project, check=True)
    subprocess.run(["git", "commit", "--allow-empty", "-m", "Initial"], cwd=setup_project, check=True)
    subprocess.run(["git", "branch", "-M", "main"], cwd=setup_project, check=True)

    # Mock zip and git commands called by rebase_command
    def mock_run(*args, **kwargs):
        cmd = args[0]
        mock_process = subprocess.CompletedProcess(args=cmd, returncode=0, stdout="", stderr="")
        if cmd[0] == "zip":
            mock_process.stdout = "Mock zip successful"
        elif "git" in cmd[0] and "fetch" in cmd:
            mock_process.stdout = "Mock fetch successful"
        elif "git" in cmd[0] and "reset" in cmd:
            mock_process.stdout = "Mock reset successful"
        elif "git" in cmd[0] and "clean" in cmd:
            mock_process.stdout = "Mock clean successful"
        elif "git" in cmd[0] and "remote show origin" in cmd:
            mock_process.stdout = "  HEAD branch: main"  # Simulate default branch detection
        # Allow other git commands (like status, rev-parse) to pass through or mock if needed
        elif "git" in cmd[0]:
            pass  # Allow other git commands needed for setup/checks
        else:
            # Let other commands (like bash, echo etc.) run normally
            original_run = subprocess.run
            return original_run(*args, **kwargs)

        return mock_process

    mock_subprocess.side_effect = mock_run

    # Act
    result = run_dhtl_command(["rebase", "--no-backup"], cwd=setup_project)  # Skip backup for simplicity

    # Assert
    assert result.returncode == 0
    assert "Resetting local repository" in result.stdout
    assert "Fetching latest changes" in result.stdout
    assert "Resetting to origin/main" in result.stdout
    assert "Cleaning untracked files" in result.stdout
    assert "Local repository has been reset" in result.stdout


@pytest.mark.integration
@patch("subprocess.run")
def test_dhtl_workflows_command(mock_subprocess, setup_project):
    """Test the 'dhtl workflows' command (mocks gh)."""

    # Arrange
    # Mock gh commands
    def mock_run(*args, **kwargs):
        cmd = args[0]
        mock_process = subprocess.CompletedProcess(args=cmd, returncode=0, stdout="", stderr="")
        if "gh" in cmd[0] and "auth status" in cmd:
            mock_process.stdout = "Logged in"  # Simulate logged in
        elif "gh" in cmd[0] and "repo view" in cmd:
            mock_process.stdout = '{"nameWithOwner": "test/repo"}'  # Simulate repo found
        elif "gh" in cmd[0] and "workflow list" in cmd:
            mock_process.stdout = "test.yml\t123\t.github/workflows/test.yml\n"  # Simulate workflow list
        elif "gh" in cmd[0] and "run list" in cmd:
            mock_process.stdout = "Run 456\tmain\tSuccess\n"  # Simulate run list
        elif "gh" in cmd[0] and "workflow run" in cmd:
            mock_process.stdout = "Workflow run triggered"
        else:
            # Let other commands pass through
            original_run = subprocess.run
            return original_run(*args, **kwargs)
        return mock_process

    mock_subprocess.side_effect = mock_run

    # Act
    result_list = run_dhtl_command(["workflows", "list"], cwd=setup_project)
    result_run = run_dhtl_command(["workflows", "run", "test.yml"], cwd=setup_project)

    # Assert
    assert result_list.returncode == 0
    assert "Managing GitHub workflows..." in result_list.stdout
    assert "Listing workflows for test/repo" in result_list.stdout
    assert "Listing recent workflow runs" in result_list.stdout

    assert result_run.returncode == 0
    assert "Triggering specific workflow 'test.yml'" in result_run.stdout


@pytest.mark.integration
def test_dhtl_env_command(setup_project):
    """Test the 'dhtl env' command."""
    # Arrange (setup_project fixture already ran setup)

    # Act
    result = run_dhtl_command(["env"], cwd=setup_project)

    # Assert
    assert result.returncode == 0
    assert "Displaying Environment Information..." in result.stdout
    assert "Environment Report" in result.stdout  # Checks if diagnostics ran and report is mentioned
    # Check if some key info is present (exact values depend on test env)
    assert "Platform:" in result.stdout
    assert "Project Root:" in result.stdout
    assert "Active:" in result.stdout  # Virtual Env section


@pytest.mark.integration
def test_dhtl_restore_command(setup_project):
    """Test the 'dhtl restore' command."""
    # Arrange
    # Simulate removing a dependency file from venv to trigger reinstall/sync
    ruff_path = setup_project / ".venv" / "bin" / "ruff"
    if ruff_path.exists():
        ruff_path.unlink()
    assert not ruff_path.exists()

    # Act
    result = run_dhtl_command(["restore"], cwd=setup_project)

    # Assert
    assert result.returncode == 0
    assert "Restoring project dependencies..." in result.stdout
    # Check if sync or install happened (output depends on lock file presence)
    assert "Dependencies restored successfully" in result.stdout or "Dependencies synced successfully" in result.stdout
    # Check if the tool was reinstalled
    assert ruff_path.exists()


@pytest.mark.integration
def test_dhtl_script_command(setup_project):
    """Test the 'dhtl script' command."""
    # Arrange (setup_project fixture created DHT/scripts/hello.sh)

    # Act
    result = run_dhtl_command(["script", "hello", "arg1", "arg2"], cwd=setup_project)

    # Assert
    assert result.returncode == 0
    assert "Running script: hello" in result.stdout
    assert "Hello from DHT script!" in result.stdout
    assert "Args: arg1 arg2" in result.stdout


@pytest.mark.integration
def test_dhtl_script_command_not_found(setup_project):
    """Test 'dhtl script' when the script doesn't exist."""
    # Act
    result = run_dhtl_command(["script", "nonexistent"], cwd=setup_project)

    # Assert
    assert result.returncode == 1  # Should fail
    assert "Script not found" in result.stderr or "Script not found" in result.stdout  # Check error message
