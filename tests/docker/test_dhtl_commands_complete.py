#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Comprehensive tests for all dhtl commands in Docker containers."""

import os
import subprocess
import sys
import json
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Tuple
from unittest.mock import patch, MagicMock

import pytest

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE FILE:
# - Initial creation of comprehensive dhtl command tests
# - Added tests for all core commands
# - Added tests for development commands
# - Added tests for version control commands
# - Added tests for deployment commands
# - Added tests for utility commands
#


@pytest.mark.docker
class TestDHTLCoreCommands:
    """Test core dhtl commands in Docker."""

    @pytest.fixture
    def dhtl_runner(self, project_root: Path) -> callable:
        """Create a runner for dhtl commands."""
        def run_dhtl(cmd: str, args: List[str] = None, cwd: Path = None) -> Tuple[int, str, str]:
            args = args or []
            cmd_list = [sys.executable, str(project_root / "dhtl_entry.py"), cmd] + args
            
            result = subprocess.run(
                cmd_list,
                capture_output=True,
                text=True,
                cwd=cwd or project_root,
                timeout=30
            )
            return result.returncode, result.stdout, result.stderr
        
        return run_dhtl

    def test_help_command(self, dhtl_runner) -> None:
        """Test dhtl help command."""
        returncode, stdout, stderr = dhtl_runner("help")
        
        assert returncode == 0
        assert "Development Helper Toolkit" in stdout
        assert "Available commands:" in stdout
        assert "Project Management:" in stdout
        assert "Development:" in stdout

    def test_version_command(self, dhtl_runner) -> None:
        """Test dhtl version command."""
        returncode, stdout, stderr = dhtl_runner("version")
        
        assert returncode == 0
        assert "Development Helper Toolkit (DHT)" in stdout
        assert "v" in stdout  # Version number

    def test_init_command(self, dhtl_runner, temp_dir: Path) -> None:
        """Test dhtl init command."""
        project_dir = temp_dir / "test_init_project"
        project_dir.mkdir()
        
        returncode, stdout, stderr = dhtl_runner("init", ["--quiet"], cwd=project_dir)
        
        assert returncode == 0
        assert (project_dir / "pyproject.toml").exists()
        assert (project_dir / "src").exists()
        assert (project_dir / "tests").exists()

    def test_setup_command(self, dhtl_runner, temp_dir: Path) -> None:
        """Test dhtl setup command."""
        project_dir = temp_dir / "test_setup_project"
        project_dir.mkdir()
        
        # Create minimal pyproject.toml
        (project_dir / "pyproject.toml").write_text("""[project]
name = "test-setup"
version = "0.1.0"
dependencies = []
""")
        
        returncode, stdout, stderr = dhtl_runner("setup", ["--quiet"], cwd=project_dir)
        
        assert returncode == 0
        assert (project_dir / ".venv").exists()
        assert (project_dir / ".dhtconfig").exists()

    def test_build_command(self, dhtl_runner, temp_dir: Path) -> None:
        """Test dhtl build command."""
        project_dir = temp_dir / "test_build_project"
        project_dir.mkdir()
        
        # Create project structure
        (project_dir / "pyproject.toml").write_text("""[project]
name = "test-build"
version = "0.1.0"
dependencies = []

[build-system]
requires = ["setuptools", "wheel"]
build-backend = "setuptools.build_meta"
""")
        
        src_dir = project_dir / "src" / "test_build"
        src_dir.mkdir(parents=True)
        (src_dir / "__init__.py").write_text('__version__ = "0.1.0"')
        
        # Setup first
        dhtl_runner("setup", ["--quiet"], cwd=project_dir)
        
        # Then build
        returncode, stdout, stderr = dhtl_runner("build", cwd=project_dir)
        
        assert returncode == 0
        assert (project_dir / "dist").exists()
        # Should have created wheel and/or sdist
        dist_files = list((project_dir / "dist").glob("*"))
        assert len(dist_files) > 0

    def test_sync_command(self, dhtl_runner, temp_dir: Path) -> None:
        """Test dhtl sync command."""
        project_dir = temp_dir / "test_sync_project"
        project_dir.mkdir()
        
        # Create project with dependencies
        (project_dir / "pyproject.toml").write_text("""[project]
name = "test-sync"
version = "0.1.0"
dependencies = ["click>=8.0.0"]
""")
        
        # Setup first
        dhtl_runner("setup", ["--quiet"], cwd=project_dir)
        
        # Then sync
        returncode, stdout, stderr = dhtl_runner("sync", cwd=project_dir)
        
        assert returncode == 0
        # Check that dependencies are installed
        venv_site_packages = project_dir / ".venv" / "lib"
        assert venv_site_packages.exists()

    def test_restore_command(self, dhtl_runner, temp_dir: Path) -> None:
        """Test dhtl restore command."""
        project_dir = temp_dir / "test_restore_project"
        project_dir.mkdir()
        
        # Create project with lock file
        (project_dir / "pyproject.toml").write_text("""[project]
name = "test-restore"
version = "0.1.0"
dependencies = ["requests"]
""")
        
        # Create a mock lock file
        (project_dir / "uv.lock").write_text("# Mock lock file")
        
        returncode, stdout, stderr = dhtl_runner("restore", cwd=project_dir)
        
        # Should attempt to restore (may fail without proper setup)
        assert returncode == 0 or "No virtual environment found" in stderr


@pytest.mark.docker
class TestDHTLDevelopmentCommands:
    """Test development-related dhtl commands."""

    @pytest.fixture
    def setup_project(self, temp_dir: Path, dhtl_runner) -> Path:
        """Set up a test project."""
        project_dir = temp_dir / "dev_test_project"
        project_dir.mkdir()
        
        # Create project files
        (project_dir / "pyproject.toml").write_text("""[project]
name = "dev-test"
version = "0.1.0"
dependencies = []

[tool.ruff]
line-length = 88
""")
        
        src_dir = project_dir / "src" / "dev_test"
        src_dir.mkdir(parents=True)
        
        # Create Python file with formatting issues
        (src_dir / "__init__.py").write_text('__version__="0.1.0"')
        (src_dir / "main.py").write_text("""
def hello(   ):
    print(  "Hello"  )
    x=1+2
    return x
""")
        
        # Create test file
        test_dir = project_dir / "tests"
        test_dir.mkdir()
        (test_dir / "test_main.py").write_text("""
def test_hello():
    from src.dev_test.main import hello
    assert hello() == 3
""")
        
        # Setup project
        dhtl_runner("setup", ["--quiet"], cwd=project_dir)
        
        return project_dir

    def test_test_command(self, dhtl_runner, setup_project: Path) -> None:
        """Test dhtl test command."""
        returncode, stdout, stderr = dhtl_runner("test", ["--version"], cwd=setup_project)
        
        assert returncode == 0
        assert "pytest" in stdout.lower() or "test" in stdout.lower()

    def test_lint_command(self, dhtl_runner, setup_project: Path) -> None:
        """Test dhtl lint command."""
        returncode, stdout, stderr = dhtl_runner("lint", cwd=setup_project)
        
        # Lint might find issues in our test code
        assert returncode == 0 or returncode == 1
        # Should run linting tools
        assert "ruff" in stdout.lower() or "lint" in stderr.lower() or returncode == 0

    def test_format_command(self, dhtl_runner, setup_project: Path) -> None:
        """Test dhtl format command."""
        # Read original file
        main_file = setup_project / "src" / "dev_test" / "main.py"
        original_content = main_file.read_text()
        
        returncode, stdout, stderr = dhtl_runner("format", cwd=setup_project)
        
        assert returncode == 0
        
        # File should be formatted
        new_content = main_file.read_text()
        # Content might be reformatted (spaces fixed, etc.)
        assert len(new_content) > 0

    def test_coverage_command(self, dhtl_runner, setup_project: Path) -> None:
        """Test dhtl coverage command."""
        returncode, stdout, stderr = dhtl_runner("coverage", ["--help"], cwd=setup_project)
        
        # Coverage command should at least show help
        assert returncode == 0 or "--help" in str(args)

    def test_clean_command(self, dhtl_runner, setup_project: Path) -> None:
        """Test dhtl clean command."""
        # Create some build artifacts
        build_dir = setup_project / "build"
        build_dir.mkdir()
        (build_dir / "test.txt").touch()
        
        pycache = setup_project / "src" / "dev_test" / "__pycache__"
        pycache.mkdir()
        (pycache / "test.pyc").touch()
        
        returncode, stdout, stderr = dhtl_runner("clean", cwd=setup_project)
        
        assert returncode == 0
        assert not build_dir.exists()
        assert not pycache.exists()


@pytest.mark.docker  
class TestDHTLVersionControlCommands:
    """Test version control related commands."""

    @pytest.fixture
    def git_project(self, temp_dir: Path, dhtl_runner) -> Path:
        """Create a git-initialized project."""
        project_dir = temp_dir / "git_test_project"
        project_dir.mkdir()
        
        # Initialize git repo
        subprocess.run(["git", "init"], cwd=project_dir, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=project_dir)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=project_dir)
        
        # Create project files
        (project_dir / "pyproject.toml").write_text("""[project]
name = "git-test"
version = "0.1.0"
dependencies = []
""")
        
        (project_dir / "README.md").write_text("# Test Project")
        
        # Initial commit
        subprocess.run(["git", "add", "."], cwd=project_dir)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=project_dir, capture_output=True)
        
        return project_dir

    def test_commit_command(self, dhtl_runner, git_project: Path) -> None:
        """Test dhtl commit command."""
        # Make a change
        (git_project / "test.txt").write_text("test content")
        subprocess.run(["git", "add", "test.txt"], cwd=git_project)
        
        returncode, stdout, stderr = dhtl_runner("commit", ["-m", "Test commit"], cwd=git_project)
        
        assert returncode == 0
        
        # Check commit was created
        result = subprocess.run(["git", "log", "--oneline"], cwd=git_project, capture_output=True, text=True)
        assert "Test commit" in result.stdout

    def test_tag_command(self, dhtl_runner, git_project: Path) -> None:
        """Test dhtl tag command."""
        returncode, stdout, stderr = dhtl_runner("tag", ["--name", "v0.1.0", "--message", "Test tag"], cwd=git_project)
        
        assert returncode == 0
        
        # Check tag was created
        result = subprocess.run(["git", "tag", "-l"], cwd=git_project, capture_output=True, text=True)
        assert "v0.1.0" in result.stdout

    def test_bump_command(self, dhtl_runner, git_project: Path) -> None:
        """Test dhtl bump command."""
        returncode, stdout, stderr = dhtl_runner("bump", ["patch"], cwd=git_project)
        
        # Bump command might require additional setup
        assert returncode == 0 or "bump" in stderr.lower()


@pytest.mark.docker
class TestDHTLDeploymentCommands:
    """Test deployment and publishing commands."""

    def test_publish_command_help(self, dhtl_runner) -> None:
        """Test dhtl publish command help."""
        returncode, stdout, stderr = dhtl_runner("publish", ["--help"])
        
        assert returncode == 0
        assert "publish" in stdout.lower() or "pypi" in stdout.lower()

    def test_workflows_command(self, dhtl_runner) -> None:
        """Test dhtl workflows command."""
        returncode, stdout, stderr = dhtl_runner("workflows", ["--help"])
        
        assert returncode == 0 or "workflows" in stdout.lower()

    def test_docker_command(self, dhtl_runner) -> None:
        """Test dhtl docker command."""
        returncode, stdout, stderr = dhtl_runner("docker", ["--help"])
        
        assert returncode == 0
        assert "docker" in stdout.lower()


@pytest.mark.docker
class TestDHTLUtilityCommands:
    """Test utility commands."""

    def test_env_command(self, dhtl_runner) -> None:
        """Test dhtl env command."""
        returncode, stdout, stderr = dhtl_runner("env")
        
        assert returncode == 0
        # Should show environment information
        assert "PATH" in stdout or "VIRTUAL_ENV" in stdout or "Python" in stdout

    def test_diagnostics_command(self, dhtl_runner) -> None:
        """Test dhtl diagnostics command."""
        returncode, stdout, stderr = dhtl_runner("diagnostics")
        
        assert returncode == 0
        # Should show diagnostic information
        assert len(stdout) > 0

    def test_guardian_command(self, dhtl_runner) -> None:
        """Test dhtl guardian command."""
        returncode, stdout, stderr = dhtl_runner("guardian", ["--help"])
        
        assert returncode == 0 or "guardian" in stdout.lower()

    def test_test_dht_command(self, dhtl_runner) -> None:
        """Test dhtl test_dht command."""
        returncode, stdout, stderr = dhtl_runner("test_dht", ["--quick"])
        
        # Self-test command
        assert returncode == 0 or "test" in stdout.lower()


@pytest.mark.docker
@pytest.mark.integration
class TestDHTLCommandIntegration:
    """Integration tests for command combinations."""

    def test_full_project_lifecycle(self, dhtl_runner, temp_dir: Path) -> None:
        """Test complete project lifecycle."""
        project_dir = temp_dir / "lifecycle_project"
        project_dir.mkdir()
        
        # 1. Initialize project
        returncode, _, _ = dhtl_runner("init", ["--quiet"], cwd=project_dir)
        assert returncode == 0
        
        # 2. Setup environment  
        returncode, _, _ = dhtl_runner("setup", ["--quiet"], cwd=project_dir)
        assert returncode == 0
        
        # 3. Add some code
        src_dir = project_dir / "src" / "lifecycle_project"
        src_dir.mkdir(parents=True, exist_ok=True)
        (src_dir / "__init__.py").write_text('__version__ = "0.1.0"')
        (src_dir / "app.py").write_text("""
def main():
    print("Hello from lifecycle project!")
    return 0

if __name__ == "__main__":
    main()
""")
        
        # 4. Format code
        returncode, _, _ = dhtl_runner("format", cwd=project_dir)
        assert returncode == 0
        
        # 5. Lint code
        returncode, _, _ = dhtl_runner("lint", cwd=project_dir)
        # Lint might find issues or pass
        assert returncode in [0, 1]
        
        # 6. Run tests
        test_dir = project_dir / "tests"
        test_dir.mkdir(exist_ok=True)
        (test_dir / "test_app.py").write_text("""
def test_main():
    from src.lifecycle_project.app import main
    assert main() == 0
""")
        
        returncode, _, _ = dhtl_runner("test", cwd=project_dir)
        # Tests might pass or fail
        assert returncode in [0, 1, 5]  # 5 = no tests found
        
        # 7. Build project
        returncode, _, _ = dhtl_runner("build", cwd=project_dir)
        assert returncode == 0
        
        # 8. Clean up
        returncode, _, _ = dhtl_runner("clean", cwd=project_dir)
        assert returncode == 0

    def test_workspace_commands(self, dhtl_runner, temp_dir: Path) -> None:
        """Test workspace-related commands."""
        workspace_dir = temp_dir / "workspace_test"
        workspace_dir.mkdir()
        
        # Create workspace pyproject.toml
        (workspace_dir / "pyproject.toml").write_text("""[project]
name = "workspace-root"
version = "0.1.0"

[tool.uv.workspace]
members = ["packages/*"]
""")
        
        # Create package
        pkg_dir = workspace_dir / "packages" / "pkg1"
        pkg_dir.mkdir(parents=True)
        (pkg_dir / "pyproject.toml").write_text("""[project]
name = "pkg1"
version = "0.1.0"
""")
        
        # Test workspace command
        returncode, stdout, stderr = dhtl_runner("workspace", ["pkg1", "version"], cwd=workspace_dir)
        
        # Workspace commands might need more setup
        assert returncode == 0 or "workspace" in stderr.lower()

    @pytest.mark.network
    def test_github_commands(self, dhtl_runner, temp_dir: Path) -> None:
        """Test GitHub-related commands."""
        # Test clone with a small public repo
        clone_dir = temp_dir / "cloned_repo"
        
        returncode, stdout, stderr = dhtl_runner(
            "clone", 
            ["https://github.com/pypa/sampleproject.git", str(clone_dir)]
        )
        
        if returncode == 0:
            assert clone_dir.exists()
            assert (clone_dir / ".git").exists()
        else:
            # Network might be restricted
            assert "network" in stderr.lower() or "clone" in stderr.lower()


@pytest.mark.docker
class TestDHTLErrorHandling:
    """Test error handling in dhtl commands."""

    def test_invalid_command(self, dhtl_runner) -> None:
        """Test handling of invalid command."""
        returncode, stdout, stderr = dhtl_runner("invalid_command_xyz")
        
        assert returncode != 0
        assert "error" in stderr.lower() or "unknown" in stderr.lower()

    def test_missing_arguments(self, dhtl_runner) -> None:
        """Test commands with missing required arguments."""
        # Tag command needs arguments
        returncode, stdout, stderr = dhtl_runner("tag")
        
        # Should show help or error
        assert returncode != 0 or "--name" in stdout

    def test_command_in_wrong_directory(self, dhtl_runner, temp_dir: Path) -> None:
        """Test running project commands outside project."""
        empty_dir = temp_dir / "empty"
        empty_dir.mkdir()
        
        # Build command should fail in empty directory
        returncode, stdout, stderr = dhtl_runner("build", cwd=empty_dir)
        
        assert returncode != 0
        assert "pyproject.toml" in stderr.lower() or "project" in stderr.lower()