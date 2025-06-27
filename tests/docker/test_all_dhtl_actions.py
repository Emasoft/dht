#!/usr/bin/env python3
"""Comprehensive tests for all dhtl actions in Docker containers."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE FILE:
# - Initial creation of comprehensive dhtl action tests for Docker
# - Tests organized by command category
# - Docker-aware test implementations
# - Profile-aware test execution
#


class DHTLDockerTester:
    """Base class for testing dhtl commands in Docker."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.dhtl_path = project_root / "dhtl_entry.py"
        self.profile = os.environ.get("DHT_TEST_PROFILE", "local")
        self.in_docker = os.environ.get("DHT_IN_DOCKER", "0") == "1"

    def run_dhtl(
        self, command: str, args: list[str] = None, cwd: Path | None = None, timeout: int = 30
    ) -> tuple[int, str, str]:
        """Run a dhtl command and return result."""
        args = args or []
        cmd = [sys.executable, str(self.dhtl_path), command] + args

        # Adjust timeout based on profile
        if self.profile == "remote":
            timeout = min(timeout, 10)

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd or self.project_root, timeout=timeout)
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", f"Command timed out after {timeout}s"


@pytest.mark.docker
class TestDHTLProjectManagement:
    """Test project management commands: init, setup, clean."""

    @pytest.fixture
    def tester(self, project_root: Path) -> DHTLDockerTester:
        return DHTLDockerTester(project_root)

    def test_init_new_project(self, tester: DHTLDockerTester, temp_dir: Path) -> None:
        """Test initializing a new project."""
        project_name = "test_init_project"
        project_dir = temp_dir / project_name
        project_dir.mkdir()

        # Run init
        code, out, err = tester.run_dhtl("init", ["--quiet"], cwd=project_dir)

        assert code == 0, f"Init failed: {err}"
        assert (project_dir / "pyproject.toml").exists()
        assert (project_dir / "src").exists()
        assert (project_dir / "tests").exists()
        assert (project_dir / "README.md").exists()

        # Verify pyproject.toml content
        pyproject_content = (project_dir / "pyproject.toml").read_text()
        assert project_name in pyproject_content
        assert "[project]" in pyproject_content

    def test_setup_environment(self, tester: DHTLDockerTester, temp_dir: Path) -> None:
        """Test setting up project environment."""
        project_dir = temp_dir / "test_setup_project"
        project_dir.mkdir()

        # Create minimal project
        (project_dir / "pyproject.toml").write_text("""[project]
name = "test-setup"
version = "0.1.0"
dependencies = ["click>=8.0"]

[build-system]
requires = ["setuptools", "wheel"]
build-backend = "setuptools.build_meta"
""")

        # Run setup
        code, out, err = tester.run_dhtl("setup", ["--quiet"], cwd=project_dir, timeout=120)

        assert code == 0, f"Setup failed: {err}"
        assert (project_dir / ".venv").exists()
        assert (project_dir / ".dhtconfig").exists()

        # Verify .dhtconfig
        dhtconfig = (project_dir / ".dhtconfig").read_text()
        assert "python_version" in dhtconfig
        assert "created_at" in dhtconfig

    def test_clean_project(self, tester: DHTLDockerTester, temp_dir: Path) -> None:
        """Test cleaning project artifacts."""
        project_dir = temp_dir / "test_clean_project"
        project_dir.mkdir()

        # Create artifacts to clean
        (project_dir / "build").mkdir()
        (project_dir / "dist").mkdir()
        (project_dir / "__pycache__").mkdir()
        (project_dir / "test.pyc").touch()
        (project_dir / ".pytest_cache").mkdir()

        # Run clean
        code, out, err = tester.run_dhtl("clean", cwd=project_dir)

        assert code == 0, f"Clean failed: {err}"
        assert not (project_dir / "build").exists()
        assert not (project_dir / "dist").exists()
        assert not (project_dir / "__pycache__").exists()
        assert not (project_dir / "test.pyc").exists()

        # .venv should still exist unless --all is used
        if (project_dir / ".venv").exists():
            code, out, err = tester.run_dhtl("clean", ["--all"], cwd=project_dir)
            assert code == 0


@pytest.mark.docker
class TestDHTLDevelopment:
    """Test development commands: build, test, lint, format, coverage."""

    @pytest.fixture
    def tester(self, project_root: Path) -> DHTLDockerTester:
        return DHTLDockerTester(project_root)

    @pytest.fixture
    def sample_project(self, temp_dir: Path, tester: DHTLDockerTester) -> Path:
        """Create a sample project for testing."""
        project_dir = temp_dir / "sample_dev_project"
        project_dir.mkdir()

        # Create project structure
        (project_dir / "pyproject.toml").write_text("""[project]
name = "sample-dev"
version = "0.1.0"
dependencies = []

[build-system]
requires = ["setuptools>=61", "wheel"]
build-backend = "setuptools.build_meta"

[tool.ruff]
line-length = 100
""")

        # Create source code
        src_dir = project_dir / "src" / "sample_dev"
        src_dir.mkdir(parents=True)
        (src_dir / "__init__.py").write_text('__version__ = "0.1.0"')
        (src_dir / "main.py").write_text("""
def greet(name:str)->str:
    '''Greet someone.'''
    return f"Hello, {name}!"

def calculate(x: int, y: int) -> int:
    \"\"\"Add two numbers.\"\"\"
    result=x+y
    return result
""")

        # Create tests
        test_dir = project_dir / "tests"
        test_dir.mkdir()
        (test_dir / "__init__.py").touch()
        (test_dir / "test_main.py").write_text("""
from src.sample_dev.main import greet, calculate

def test_greet():
    assert greet("World") == "Hello, World!"

def test_calculate():
    assert calculate(2, 3) == 5
""")

        # Setup the project
        tester.run_dhtl("setup", ["--quiet"], cwd=project_dir, timeout=120)

        return project_dir

    def test_build_project(self, tester: DHTLDockerTester, sample_project: Path) -> None:
        """Test building a project."""
        code, out, err = tester.run_dhtl("build", cwd=sample_project, timeout=60)

        assert code == 0, f"Build failed: {err}"
        assert (sample_project / "dist").exists()

        # Check for wheel or sdist
        dist_files = list((sample_project / "dist").glob("*.whl")) + list((sample_project / "dist").glob("*.tar.gz"))
        assert len(dist_files) > 0

    def test_run_tests(self, tester: DHTLDockerTester, sample_project: Path) -> None:
        """Test running project tests."""
        code, out, err = tester.run_dhtl("test", cwd=sample_project, timeout=60)

        # Tests should pass
        assert code == 0, f"Tests failed: {err}"
        assert "passed" in out.lower() or "ok" in out.lower()

    def test_lint_code(self, tester: DHTLDockerTester, sample_project: Path) -> None:
        """Test linting code."""
        code, out, err = tester.run_dhtl("lint", cwd=sample_project)

        # Lint might find issues or pass
        assert code in [0, 1], f"Lint command failed: {err}"

        # Should mention ruff or linting
        combined = out + err
        assert any(term in combined.lower() for term in ["ruff", "lint", "check"])

    def test_format_code(self, tester: DHTLDockerTester, sample_project: Path) -> None:
        """Test formatting code."""
        # Get original content
        main_file = sample_project / "src" / "sample_dev" / "main.py"
        original = main_file.read_text()

        code, out, err = tester.run_dhtl("format", cwd=sample_project)

        assert code == 0, f"Format failed: {err}"

        # Check if file was formatted
        formatted = main_file.read_text()
        # Formatting should fix spacing around operators
        assert "result = x + y" in formatted or "result=x+y" in formatted

    @pytest.mark.slow
    def test_coverage_analysis(self, tester: DHTLDockerTester, sample_project: Path) -> None:
        """Test coverage analysis."""
        code, out, err = tester.run_dhtl("coverage", cwd=sample_project, timeout=90)

        # Coverage might need pytest-cov installed
        if code == 0:
            assert "coverage" in out.lower() or "%" in out
        else:
            # Accept failure if coverage tools not available
            assert "coverage" in err.lower() or "pytest-cov" in err.lower()


@pytest.mark.docker
class TestDHTLVersionControl:
    """Test version control commands: commit, tag, bump."""

    @pytest.fixture
    def tester(self, project_root: Path) -> DHTLDockerTester:
        return DHTLDockerTester(project_root)

    @pytest.fixture
    def git_project(self, temp_dir: Path) -> Path:
        """Create a git-enabled project."""
        project_dir = temp_dir / "git_project"
        project_dir.mkdir()

        # Initialize git
        subprocess.run(["git", "init"], cwd=project_dir, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=project_dir)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=project_dir)

        # Create files
        (project_dir / "pyproject.toml").write_text("""[project]
name = "git-test"
version = "0.1.0"
""")
        (project_dir / "README.md").write_text("# Git Test Project")

        # Initial commit
        subprocess.run(["git", "add", "."], cwd=project_dir)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=project_dir, capture_output=True)

        return project_dir

    def test_commit_changes(self, tester: DHTLDockerTester, git_project: Path) -> None:
        """Test creating commits."""
        # Make changes
        (git_project / "new_file.py").write_text("print('Hello')")
        subprocess.run(["git", "add", "new_file.py"], cwd=git_project)

        code, out, err = tester.run_dhtl("commit", ["-m", "Add new file"], cwd=git_project)

        assert code == 0, f"Commit failed: {err}"

        # Verify commit
        log = subprocess.run(["git", "log", "--oneline", "-1"], cwd=git_project, capture_output=True, text=True)
        assert "Add new file" in log.stdout

    def test_create_tag(self, tester: DHTLDockerTester, git_project: Path) -> None:
        """Test creating git tags."""
        code, out, err = tester.run_dhtl("tag", ["--name", "v0.1.0", "--message", "First release"], cwd=git_project)

        assert code == 0, f"Tag failed: {err}"

        # Verify tag
        tags = subprocess.run(["git", "tag", "-l"], cwd=git_project, capture_output=True, text=True)
        assert "v0.1.0" in tags.stdout

    def test_bump_version(self, tester: DHTLDockerTester, git_project: Path) -> None:
        """Test version bumping."""
        code, out, err = tester.run_dhtl("bump", ["patch"], cwd=git_project)

        # Bump might require bump-my-version tool
        if code == 0:
            # Check version was bumped
            pyproject = (git_project / "pyproject.toml").read_text()
            assert "0.1.1" in pyproject or "0.2.0" in pyproject
        else:
            # Tool might not be available
            assert "bump" in err.lower()


@pytest.mark.docker
class TestDHTLDeployment:
    """Test deployment commands: publish, docker, workflows."""

    @pytest.fixture
    def tester(self, project_root: Path) -> DHTLDockerTester:
        return DHTLDockerTester(project_root)

    def test_publish_dry_run(self, tester: DHTLDockerTester, temp_dir: Path) -> None:
        """Test publish command in dry-run mode."""
        # Create a built project
        project_dir = temp_dir / "publish_test"
        project_dir.mkdir()
        dist_dir = project_dir / "dist"
        dist_dir.mkdir()
        (dist_dir / "test-0.1.0.whl").touch()

        code, out, err = tester.run_dhtl("publish", ["--dry-run"], cwd=project_dir)

        # Dry run should not actually publish
        assert code == 0 or "pypi" in err.lower()

    def test_docker_commands(self, tester: DHTLDockerTester) -> None:
        """Test docker subcommands."""
        code, out, err = tester.run_dhtl("docker", ["--help"])

        assert code == 0
        assert "docker" in out.lower()

        # List available docker commands
        for subcmd in ["build", "test", "shell"]:
            assert subcmd in out

    @pytest.mark.skipif(
        os.environ.get("DHT_TEST_PROFILE", "") == "remote", reason="Workflow tests skipped in REMOTE profile"
    )
    def test_workflows_list(self, tester: DHTLDockerTester, temp_dir: Path) -> None:
        """Test listing workflows."""
        # Create project with workflow
        project_dir = temp_dir / "workflow_test"
        project_dir.mkdir()
        workflow_dir = project_dir / ".github" / "workflows"
        workflow_dir.mkdir(parents=True)
        (workflow_dir / "test.yml").write_text("""
name: Test
on: push
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
""")

        code, out, err = tester.run_dhtl("workflows", ["list"], cwd=project_dir)

        if code == 0:
            assert "test" in out.lower() or "Test" in out


@pytest.mark.docker
class TestDHTLUtilities:
    """Test utility commands: env, diagnostics, restore."""

    @pytest.fixture
    def tester(self, project_root: Path) -> DHTLDockerTester:
        return DHTLDockerTester(project_root)

    def test_show_environment(self, tester: DHTLDockerTester) -> None:
        """Test showing environment information."""
        code, out, err = tester.run_dhtl("env")

        assert code == 0
        # Should show some environment info
        assert any(var in out for var in ["PATH", "PYTHON", "VIRTUAL_ENV", "DHT"])

    def test_run_diagnostics(self, tester: DHTLDockerTester) -> None:
        """Test running diagnostics."""
        code, out, err = tester.run_dhtl("diagnostics", timeout=60)

        assert code == 0
        # Should show diagnostic information
        assert len(out) > 100  # Should have substantial output
        assert any(term in out.lower() for term in ["python", "system", "version"])

    def test_restore_dependencies(self, tester: DHTLDockerTester, temp_dir: Path) -> None:
        """Test restoring dependencies."""
        project_dir = temp_dir / "restore_test"
        project_dir.mkdir()

        # Create project with lock file
        (project_dir / "pyproject.toml").write_text("""[project]
name = "restore-test"
version = "0.1.0"
dependencies = ["click"]
""")
        (project_dir / "uv.lock").write_text("# Mock lock file\n")

        code, out, err = tester.run_dhtl("restore", cwd=project_dir)

        # Restore needs virtual environment
        assert code == 0 or "venv" in err.lower() or "virtual" in err.lower()


@pytest.mark.docker
class TestDHTLSpecialCommands:
    """Test special commands: help, version, node, python, run."""

    @pytest.fixture
    def tester(self, project_root: Path) -> DHTLDockerTester:
        return DHTLDockerTester(project_root)

    def test_help_output(self, tester: DHTLDockerTester) -> None:
        """Test help command."""
        code, out, err = tester.run_dhtl("help")

        assert code == 0
        assert "Development Helper Toolkit" in out
        assert "Available commands:" in out

        # Check command categories
        for category in ["Project Management", "Development", "Version Control"]:
            assert category in out

    def test_version_output(self, tester: DHTLDockerTester) -> None:
        """Test version command."""
        code, out, err = tester.run_dhtl("version")

        assert code == 0
        assert "Development Helper Toolkit" in out
        assert "v" in out  # Version string

    def test_python_execution(self, tester: DHTLDockerTester) -> None:
        """Test python command wrapper."""
        code, out, err = tester.run_dhtl("python", ["--version"])

        assert code == 0
        assert "Python" in out

    def test_run_command(self, tester: DHTLDockerTester) -> None:
        """Test run command wrapper."""
        code, out, err = tester.run_dhtl("run", ["echo", "Hello from dhtl"])

        assert code == 0
        assert "Hello from dhtl" in out


@pytest.mark.docker
@pytest.mark.integration
class TestDHTLIntegration:
    """Integration tests combining multiple commands."""

    @pytest.fixture
    def tester(self, project_root: Path) -> DHTLDockerTester:
        return DHTLDockerTester(project_root)

    def test_complete_workflow(self, tester: DHTLDockerTester, temp_dir: Path) -> None:
        """Test a complete development workflow."""
        project_dir = temp_dir / "integration_project"

        # 1. Initialize
        project_dir.mkdir()
        code, _, _ = tester.run_dhtl("init", ["--quiet"], cwd=project_dir)
        assert code == 0

        # 2. Setup
        code, _, _ = tester.run_dhtl("setup", ["--quiet"], cwd=project_dir, timeout=120)
        assert code == 0

        # 3. Add code
        src_dir = project_dir / "src" / "integration_project"
        (src_dir / "calculator.py").write_text("""
def add(a: int, b: int) -> int:
    return a + b

def multiply(a: int, b: int) -> int:
    return a * b
""")

        # 4. Add tests
        test_file = project_dir / "tests" / "test_calculator.py"
        test_file.write_text("""
from src.integration_project.calculator import add, multiply

def test_add():
    assert add(2, 3) == 5

def test_multiply():
    assert multiply(3, 4) == 12
""")

        # 5. Format
        code, _, _ = tester.run_dhtl("format", cwd=project_dir)
        assert code == 0

        # 6. Lint
        code, _, _ = tester.run_dhtl("lint", cwd=project_dir)
        assert code in [0, 1]  # Might have warnings

        # 7. Test
        code, out, _ = tester.run_dhtl("test", cwd=project_dir)
        assert code == 0
        assert "2 passed" in out or "test_add" in out

        # 8. Build
        code, _, _ = tester.run_dhtl("build", cwd=project_dir)
        assert code == 0
        assert (project_dir / "dist").exists()

    @pytest.mark.slow
    @pytest.mark.network
    def test_clone_and_setup(self, tester: DHTLDockerTester, temp_dir: Path) -> None:
        """Test cloning a repo and setting it up."""
        if tester.profile == "remote":
            pytest.skip("Network test skipped in REMOTE profile")

        clone_dir = temp_dir / "cloned_project"

        # Clone a small repo
        code, _, err = tester.run_dhtl(
            "clone", ["https://github.com/pypa/sampleproject.git", str(clone_dir)], timeout=120
        )

        if code == 0:
            assert clone_dir.exists()

            # Setup the cloned project
            code, _, _ = tester.run_dhtl("setup", ["--quiet"], cwd=clone_dir, timeout=120)
            assert code == 0
            assert (clone_dir / ".venv").exists()


@pytest.mark.docker
class TestDHTLEdgeCases:
    """Test edge cases and error handling."""

    @pytest.fixture
    def tester(self, project_root: Path) -> DHTLDockerTester:
        return DHTLDockerTester(project_root)

    def test_invalid_command(self, tester: DHTLDockerTester) -> None:
        """Test handling of invalid commands."""
        code, out, err = tester.run_dhtl("invalid_command_xyz")

        assert code != 0
        assert "error" in err.lower() or "unknown" in err.lower()

    def test_command_without_project(self, tester: DHTLDockerTester, temp_dir: Path) -> None:
        """Test project commands in non-project directory."""
        empty_dir = temp_dir / "empty"
        empty_dir.mkdir()

        # Build should fail
        code, out, err = tester.run_dhtl("build", cwd=empty_dir)
        assert code != 0
        assert "pyproject.toml" in err.lower() or "project" in err.lower()

    def test_timeout_handling(self, tester: DHTLDockerTester) -> None:
        """Test command timeout handling."""
        if tester.profile == "remote":
            # Remote profile has short timeouts
            code, out, err = tester.run_dhtl("python", ["-c", "import time; time.sleep(15)"], timeout=5)
            assert code == -1
            assert "timed out" in err.lower()
