#!/usr/bin/env python3

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Create integration tests for workspace commands
# - Test end-to-end functionality without mocking
#

"""Integration tests for workspace commands."""

import subprocess
import tempfile
from pathlib import Path

import pytest


class TestWorkspaceIntegration:
    """Integration tests for workspace commands."""

    @pytest.mark.integration
    def test_workspaces_run_integration(self):
        """Test workspaces run command end-to-end."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Create a workspace project
            pyproject = tmpdir / "pyproject.toml"
            pyproject.write_text("""
[project]
name = "test-workspace"
version = "0.1.0"

[tool.uv.workspace]
members = ["packages/*"]
""")

            # Create a package
            pkg_dir = tmpdir / "packages" / "pkg1"
            pkg_dir.mkdir(parents=True)
            (pkg_dir / "pyproject.toml").write_text("""
[project]
name = "pkg1"
version = "0.1.0"

[project.scripts]
hello = "echo 'Hello from pkg1'"
""")

            # Run the workspaces command
            result = subprocess.run(
                ["python", "-m", "dhtl", "workspaces", "run", "python", "--version"],
                cwd=tmpdir,
                capture_output=True,
                text=True,
            )

            # Should succeed and show Python version from each member
            assert result.returncode == 0
            assert "Python" in result.stdout or "Python" in result.stderr

    @pytest.mark.integration
    def test_workspace_single_member_integration(self):
        """Test workspace command for single member."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Create workspace
            pyproject = tmpdir / "pyproject.toml"
            pyproject.write_text("""
[project]
name = "root"
version = "0.1.0"

[tool.uv.workspace]
members = ["apps/*"]
""")

            # Create app
            app_dir = tmpdir / "apps" / "myapp"
            app_dir.mkdir(parents=True)
            (app_dir / "pyproject.toml").write_text("""
[project]
name = "myapp"
version = "0.1.0"
""")

            # Run command in specific workspace
            result = subprocess.run(
                ["python", "-m", "dhtl", "workspace", "myapp", "run", "python", "-c", "print('Hello from myapp')"],
                cwd=tmpdir,
                capture_output=True,
                text=True,
            )

            # Should succeed
            assert result.returncode == 0
            assert "Hello from myapp" in result.stdout

    @pytest.mark.integration
    def test_project_command_integration(self):
        """Test project command runs only in root."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Create simple project
            pyproject = tmpdir / "pyproject.toml"
            pyproject.write_text("""
[project]
name = "myproject"
version = "0.1.0"
""")

            # Run project command
            result = subprocess.run(
                ["python", "-m", "dhtl", "project", "run", "python", "-c", "print('Root project')"],
                cwd=tmpdir,
                capture_output=True,
                text=True,
            )

            # Should succeed
            assert result.returncode == 0
            assert "Root project" in result.stdout
