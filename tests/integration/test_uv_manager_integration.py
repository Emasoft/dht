#!/usr/bin/env python3
"""
Integration tests for UV manager using real UV installation and GitHub repos.

These tests require UV to be installed and network access for cloning repos.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Initial integration tests for UV manager
# - Uses real UV commands without mocking
# - Tests with actual GitHub repositories
# - Follows UV documentation best practices
#

import subprocess
import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest

from DHT.modules.uv_manager import UVManager


class TestUVManagerIntegration:
    """Integration tests for UV Manager with real UV commands."""

    @pytest.fixture
    def temp_project_dir(self) -> Generator[Path, None, None]:
        """Create a temporary directory for test projects."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def uv_manager(self) -> UVManager:
        """Create a UV manager instance using real UV."""
        # This should find the actual UV installation
        manager = UVManager()
        if not manager.is_available:
            pytest.skip("UV is not available - install UV to run these tests")
        return manager

    @pytest.fixture
    def sample_pyproject_toml(self) -> str:
        """Sample pyproject.toml content following UV documentation."""
        return """[project]
name = "test-project"
version = "0.1.0"
description = "Test project for UV integration"
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    "requests>=2.31.0",
    "click>=8.1.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "ruff>=0.1.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
"""

    def test_uv_is_available(self, uv_manager):
        """Test that UV is properly detected and available."""
        assert uv_manager.is_available
        assert uv_manager.uv_path is not None
        assert uv_manager.uv_path.exists()

    def test_uv_version_check(self, uv_manager):
        """Test UV version meets minimum requirements."""
        result = uv_manager.run_command(["--version"])
        assert result["success"]
        assert "uv" in result["stdout"]
        # Parse version from output like "uv 0.7.12 (dc3fd4647 2025-06-06)"
        parts = result["stdout"].strip().split()
        assert len(parts) >= 2
        version_str = parts[1]  # Version is the second part
        major, minor = version_str.split(".")[:2]
        assert int(major) > 0 or (int(major) == 0 and int(minor) >= 4)

    def test_init_new_project(self, uv_manager, temp_project_dir):
        """Test initializing a new Python project with UV."""
        project_name = "test-init-project"
        project_path = temp_project_dir / project_name

        # Use UV to init a new project
        result = uv_manager.run_command(["init", project_name], cwd=temp_project_dir)

        assert result["success"]
        assert project_path.exists()
        assert (project_path / "pyproject.toml").exists()
        assert (project_path / "README.md").exists()
        assert (project_path / ".python-version").exists()

        # Check pyproject.toml has correct structure
        import tomllib

        with open(project_path / "pyproject.toml", "rb") as f:
            pyproject = tomllib.load(f)

        assert "project" in pyproject
        assert pyproject["project"]["name"] == project_name
        assert "dependencies" in pyproject["project"]

    def test_create_venv_and_sync(self, uv_manager, temp_project_dir, sample_pyproject_toml):
        """Test creating virtual environment and syncing dependencies."""
        # Create a project with pyproject.toml
        project_path = temp_project_dir / "sync-test"
        project_path.mkdir()

        # Write pyproject.toml
        (project_path / "pyproject.toml").write_text(sample_pyproject_toml)
        (project_path / "README.md").write_text("# Test Project")

        # First, init the project to create .python-version and other UV files
        init_result = uv_manager.run_command(["init", "--no-workspace"], cwd=project_path)
        # It's OK if init says the project already exists

        # Create virtual environment
        venv_path = uv_manager.create_venv(project_path)
        assert venv_path.exists()
        assert (venv_path / "bin" / "python").exists() or (venv_path / "Scripts" / "python.exe").exists()

        # Generate lock file first
        lock_result = uv_manager.generate_lock_file(project_path)
        assert lock_result.exists()

        # Sync dependencies
        result = uv_manager.run_command(["sync"], cwd=project_path)
        assert result["success"], f"Sync failed with stderr: {result.get('stderr', '')}"

        # Check that dependencies were installed
        pip_list_result = uv_manager.run_command(["pip", "list"], cwd=project_path)
        assert pip_list_result["success"]
        assert "requests" in pip_list_result["stdout"]
        assert "click" in pip_list_result["stdout"]

    def test_add_and_remove_dependency(self, uv_manager, temp_project_dir):
        """Test adding and removing dependencies with UV."""
        # Init a new project
        project_name = "dep-test"
        project_path = temp_project_dir / project_name

        init_result = uv_manager.run_command(["init", project_name], cwd=temp_project_dir)
        assert init_result["success"]

        # Add a dependency
        add_result = uv_manager.add_dependency(project_path, "httpx>=0.25.0")
        assert add_result["success"]

        # Check it was added to pyproject.toml
        import tomllib

        with open(project_path / "pyproject.toml", "rb") as f:
            pyproject = tomllib.load(f)

        deps = pyproject["project"]["dependencies"]
        assert any("httpx" in dep for dep in deps)

        # Remove the dependency
        remove_result = uv_manager.remove_dependency(project_path, "httpx")
        assert remove_result["success"]

        # Check it was removed
        with open(project_path / "pyproject.toml", "rb") as f:
            pyproject = tomllib.load(f)

        deps = pyproject["project"].get("dependencies", [])
        assert not any("httpx" in dep for dep in deps)

    def test_build_project(self, uv_manager, temp_project_dir, sample_pyproject_toml):
        """Test building a Python project with UV."""
        # Create a project
        project_path = temp_project_dir / "build-test"
        project_path.mkdir()

        # Write project files
        (project_path / "pyproject.toml").write_text(sample_pyproject_toml)
        (project_path / "README.md").write_text("# Test Build Project")

        # Create source directory and module
        src_dir = project_path / "test_project"
        src_dir.mkdir()
        (src_dir / "__init__.py").write_text('__version__ = "0.1.0"')
        (src_dir / "main.py").write_text('''
def hello():
    """Say hello."""
    return "Hello from test project!"

if __name__ == "__main__":
    print(hello())
''')

        # Build the project
        build_result = uv_manager.run_command(["build"], cwd=project_path)
        assert build_result["success"]

        # Check that wheel was created
        dist_dir = project_path / "dist"
        assert dist_dir.exists()
        wheels = list(dist_dir.glob("*.whl"))
        assert len(wheels) == 1
        assert "test_project-0.1.0" in wheels[0].name

    def test_python_version_management(self, uv_manager, temp_project_dir):
        """Test Python version detection and pinning."""
        project_path = temp_project_dir / "version-test"
        project_path.mkdir()

        # Pin Python version
        pin_result = uv_manager.run_command(["python", "pin", "3.11"], cwd=project_path)
        assert pin_result["success"]

        # Check .python-version file
        python_version_file = project_path / ".python-version"
        assert python_version_file.exists()
        assert python_version_file.read_text().strip() == "3.11"

        # Detect Python version
        detected_version = uv_manager.detect_python_version(project_path)
        assert detected_version == "3.11"

    @pytest.mark.slow
    def test_clone_and_setup_real_github_repo(self, uv_manager, temp_project_dir):
        """Test cloning and setting up a real GitHub Python project."""
        # Use a small, simple Python project
        repo_url = "https://github.com/psf/peps.git"
        project_name = "peps"
        project_path = temp_project_dir / project_name

        # Clone the repository
        clone_result = subprocess.run(
            ["git", "clone", "--depth", "1", repo_url, str(project_path)], capture_output=True, text=True
        )
        if clone_result.returncode != 0:
            pytest.skip(f"Could not clone repo: {clone_result.stderr}")

        # Setup the project with UV
        setup_result = uv_manager.setup_project(
            project_path,
            install_deps=True,
            dev=False,  # Don't install dev deps for simpler test
        )

        # Check the steps that were completed
        completed_steps = [step["step"] for step in setup_result["steps"] if step["success"]]

        # At minimum, we should detect Python version
        assert "detect_python_version" in completed_steps or setup_result["success"]

        # If a venv was created, verify it exists
        if "create_venv" in completed_steps:
            venv_path = project_path / ".venv"
            assert venv_path.exists()

    def test_lock_file_generation(self, uv_manager, temp_project_dir, sample_pyproject_toml):
        """Test generating and using lock files for reproducible builds."""
        project_path = temp_project_dir / "lock-test"
        project_path.mkdir()

        # Write project files
        (project_path / "pyproject.toml").write_text(sample_pyproject_toml)
        (project_path / "README.md").write_text("# Lock Test")

        # Initialize the project first
        init_result = uv_manager.run_command(["init", "--no-workspace"], cwd=project_path)

        # Generate lock file
        lock_result = uv_manager.generate_lock_file(project_path)
        assert lock_result.exists()
        assert lock_result.name == "uv.lock"

        # Check lock file content
        lock_content = lock_result.read_text()
        # UV lock files have a specific format, check for package names
        assert 'name = "requests"' in lock_content or "requests" in lock_content
        assert 'name = "click"' in lock_content or "click" in lock_content

        # Create venv before syncing
        venv_path = uv_manager.create_venv(project_path)
        assert venv_path.exists()

        # Install from lock file
        sync_result = uv_manager.run_command(["sync", "--frozen"], cwd=project_path)
        assert sync_result["success"], f"Sync failed: {sync_result.get('stderr', '')}"
