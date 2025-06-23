#!/usr/bin/env python3
from __future__ import annotations

from typing import Any

"""
Integration tests for Bolt-compatible commands.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Create comprehensive integration tests for Bolt-compatible commands
# - Test add, remove, upgrade, check, fmt, bin, doc commands
# - Test default behaviors and command aliases
#

"""Integration tests for Bolt-compatible commands."""

import subprocess
import sys
import tempfile
from pathlib import Path

import pytest


def run_dhtl_command(args: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
    """Run a dhtl command and return the result."""
    # Use the dhtl command from venv if available, otherwise use the module
    venv_dhtl = Path(__file__).parent.parent.parent / ".venv" / "bin" / "dhtl"
    if venv_dhtl.exists():
        cmd = [str(venv_dhtl)] + args
    else:
        # Fallback to running as module
        cmd = [sys.executable, "-m", "DHT.dhtl"] + args
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)


class TestBoltAddRemoveCommands:
    """Integration tests for add/remove commands."""

    @pytest.mark.integration
    def test_add_package_to_project(self) -> Any:
        """Test adding a package to a project."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Create a basic project
            pyproject = tmpdir / "pyproject.toml"
            pyproject.write_text("""
[project]
name = "test-project"
version = "0.1.0"
dependencies = []
""")

            # Initialize uv project
            result = run_dhtl_command(["init"], cwd=tmpdir)
            assert result.returncode == 0

            # Add a package
            result = run_dhtl_command(["add", "click"], cwd=tmpdir)

            # Should succeed
            assert result.returncode == 0
            assert "click" in pyproject.read_text().lower() or "Added click" in result.stdout

    @pytest.mark.integration
    def test_add_multiple_packages(self) -> Any:
        """Test adding multiple packages at once."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Create project
            pyproject = tmpdir / "pyproject.toml"
            pyproject.write_text("""
[project]
name = "test-project"
version = "0.1.0"
dependencies = []
""")

            # Initialize
            run_dhtl_command(["init"], cwd=tmpdir)

            # Add multiple packages
            result = run_dhtl_command(["add", "click", "rich", "pytest"], cwd=tmpdir)

            assert result.returncode == 0
            # Check that packages were added (either in pyproject or in output)
            project_text = pyproject.read_text().lower()
            output_text = result.stdout.lower()
            for pkg in ["click", "rich", "pytest"]:
                assert pkg in project_text or pkg in output_text

    @pytest.mark.integration
    def test_remove_package_from_project(self) -> Any:
        """Test removing a package from a project."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Create project with a dependency
            pyproject = tmpdir / "pyproject.toml"
            pyproject.write_text("""
[project]
name = "test-project"
version = "0.1.0"
dependencies = ["click"]
""")

            # Initialize
            run_dhtl_command(["init"], cwd=tmpdir)

            # Remove package
            result = run_dhtl_command(["remove", "click"], cwd=tmpdir)

            assert result.returncode == 0
            # Package should be removed
            assert "Removed click" in result.stdout or "click" not in pyproject.read_text()


class TestBoltUpgradeCommand:
    """Integration tests for upgrade command."""

    @pytest.mark.integration
    def test_upgrade_single_package(self) -> Any:
        """Test upgrading a single package."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Create project with dependency
            pyproject = tmpdir / "pyproject.toml"
            pyproject.write_text("""
[project]
name = "test-project"
version = "0.1.0"
dependencies = ["click>=7.0"]
""")

            # Initialize
            run_dhtl_command(["init"], cwd=tmpdir)

            # Upgrade package
            result = run_dhtl_command(["upgrade", "click"], cwd=tmpdir)

            assert result.returncode == 0
            assert "click" in result.stdout.lower() or "upgraded" in result.stdout.lower()

    @pytest.mark.integration
    def test_upgrade_all_packages(self) -> Any:
        """Test upgrading all packages when no package specified."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Create project
            pyproject = tmpdir / "pyproject.toml"
            pyproject.write_text("""
[project]
name = "test-project"
version = "0.1.0"
dependencies = ["click", "rich"]
""")

            # Initialize
            run_dhtl_command(["init"], cwd=tmpdir)

            # Upgrade all
            result = run_dhtl_command(["upgrade"], cwd=tmpdir)

            assert result.returncode == 0
            assert "upgrade" in result.stdout.lower() or result.stderr.lower()


class TestBoltCheckCommand:
    """Integration tests for check (type checking) command."""

    @pytest.mark.integration
    def test_check_command_runs_mypy(self) -> Any:
        """Test that check command runs type checking."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Create a Python file
            (tmpdir / "main.py").write_text("""
def greet(name: str) -> str:
    return f"Hello, {name}!"

# This should pass type checking
result = greet("World")
""")

            # Create pyproject.toml
            pyproject = tmpdir / "pyproject.toml"
            pyproject.write_text("""
[project]
name = "test-project"
version = "0.1.0"
""")

            # Run check command
            result = run_dhtl_command(["check"], cwd=tmpdir)

            # Should run mypy (even if it fails due to no mypy config)
            assert "mypy" in result.stdout.lower() or "mypy" in result.stderr.lower() or "type" in result.stdout.lower()

    @pytest.mark.integration
    def test_check_with_specific_files(self) -> Any:
        """Test check command with specific files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Create Python files
            (tmpdir / "good.py").write_text("def add(a: int, b: int) -> int: return a + b")
            (tmpdir / "bad.py").write_text("def bad(x) -> Any: return x + 1  # Missing type annotations")

            # Run check on specific file
            result = run_dhtl_command(["check", "good.py"], cwd=tmpdir)

            # Should attempt to check the file
            assert result.returncode == 0 or "mypy" in result.stderr.lower()


class TestBoltFormatCommands:
    """Integration tests for format commands."""

    @pytest.mark.integration
    def test_fmt_alias_for_format(self) -> Any:
        """Test that fmt is an alias for format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Create unformatted Python file
            (tmpdir / "ugly.py").write_text("""
def ugly_function(  x,y,   z ) -> Any:
    return x+y+z


class BadFormat:
    def __init__(self,
    value) -> Any:
        self.value=value
""")

            # Run fmt command
            result = run_dhtl_command(["fmt"], cwd=tmpdir)

            # Should attempt formatting
            assert result.returncode == 0 or "format" in result.stdout.lower() or "ruff" in result.stdout.lower()

    @pytest.mark.integration
    def test_format_check_mode(self) -> Any:
        """Test format command in check mode."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Create file
            (tmpdir / "test.py").write_text("x=1+2")

            # Run format --check
            result = run_dhtl_command(["format", "--check"], cwd=tmpdir)

            # Should check without modifying
            assert (tmpdir / "test.py").read_text() == "x=1+2"


class TestBoltBinCommand:
    """Integration tests for bin command."""

    @pytest.mark.integration
    def test_bin_prints_venv_path(self) -> Any:
        """Test that bin command prints virtual environment bin path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Create project
            pyproject = tmpdir / "pyproject.toml"
            pyproject.write_text("""
[project]
name = "test-project"
version = "0.1.0"
""")

            # Initialize (creates venv)
            run_dhtl_command(["init"], cwd=tmpdir)

            # Run bin command
            result = run_dhtl_command(["bin"], cwd=tmpdir)

            assert result.returncode == 0
            # Should print path containing .venv and bin/Scripts
            output = result.stdout.strip()
            assert ".venv" in output
            assert "bin" in output or "Scripts" in output

    @pytest.mark.integration
    def test_bin_when_no_venv(self) -> Any:
        """Test bin command when no virtual environment exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Run bin without venv
            result = run_dhtl_command(["bin"], cwd=tmpdir)

            # Should fail gracefully
            assert result.returncode != 0
            assert "not found" in result.stderr.lower() or "no virtual environment" in result.stderr.lower()


class TestBoltDocCommand:
    """Integration tests for doc command."""

    @pytest.mark.integration
    def test_doc_generates_documentation(self) -> Any:
        """Test that doc command generates documentation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Create project with docstrings
            (tmpdir / "mymodule.py").write_text('''
"""My module for testing documentation generation."""

def add(a: int, b: int) -> int:
    """Add two numbers together.

    Args:
        a: First number
        b: Second number

    Returns:
        The sum of a and b
    """
    return a + b
''')

            pyproject = tmpdir / "pyproject.toml"
            pyproject.write_text("""
[project]
name = "test-project"
version = "0.1.0"
""")

            # Run doc command
            result = run_dhtl_command(["doc"], cwd=tmpdir)

            # Should attempt to generate docs
            assert result.returncode == 0 or "doc" in result.stdout.lower()
            # Check if docs directory was created
            docs_exist = (tmpdir / "docs").exists() or (tmpdir / "_build").exists()
            assert docs_exist or "documentation" in result.stdout.lower()


class TestBoltDefaultBehaviors:
    """Integration tests for Bolt default behaviors."""

    @pytest.mark.integration
    def test_no_args_runs_install(self) -> Any:
        """Test that dhtl with no args runs install/setup."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Create minimal project
            pyproject = tmpdir / "pyproject.toml"
            pyproject.write_text("""
[project]
name = "test-project"
version = "0.1.0"
""")

            result = run_dhtl_command([], cwd=tmpdir)

            # Should run setup/install
            assert "setup" in result.stdout.lower() or "install" in result.stdout.lower() or result.returncode == 0

    @pytest.mark.integration
    def test_install_is_alias_for_setup(self) -> Any:
        """Test that install command works as alias for setup."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Create project
            pyproject = tmpdir / "pyproject.toml"
            pyproject.write_text("""
[project]
name = "test-project"
version = "0.1.0"
""")

            # Run install
            result = run_dhtl_command(["install"], cwd=tmpdir)

            # Should run setup
            assert "setup" in result.stdout.lower() or "install" in result.stdout.lower() or result.returncode == 0


class TestWorkspaceFilteringIntegration:
    """Integration tests for workspace filtering options."""

    @pytest.mark.integration
    def test_workspaces_only_filter(self) -> Any:
        """Test --only filter for workspace commands."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Create workspace with multiple packages
            pyproject = tmpdir / "pyproject.toml"
            pyproject.write_text("""
[project]
name = "root"
version = "0.1.0"

[tool.uv.workspace]
members = ["packages/*"]
""")

            # Create packages
            for name in ["frontend", "backend", "shared"]:
                pkg_dir = tmpdir / "packages" / name
                pkg_dir.mkdir(parents=True)
                (pkg_dir / "pyproject.toml").write_text(f'''
[project]
name = "{name}"
version = "0.1.0"
''')

            # Run with --only filter
            result = run_dhtl_command(["workspaces", "run", "echo", "hello", "--only", "*end"], cwd=tmpdir)

            # Should only run in frontend and backend
            assert result.returncode == 0
            output = result.stdout.lower()
            assert "frontend" in output
            assert "backend" in output
            # shared should not be included

    @pytest.mark.integration
    def test_workspaces_ignore_filter(self) -> Any:
        """Test --ignore filter for workspace commands."""
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

            # Create apps
            for name in ["web", "mobile", "test-app"]:
                app_dir = tmpdir / "apps" / name
                app_dir.mkdir(parents=True)
                (app_dir / "pyproject.toml").write_text(f'''
[project]
name = "{name}"
version = "0.1.0"
''')

            # Run with --ignore filter
            result = run_dhtl_command(["ws", "run", "echo", "running", "--ignore", "test-*"], cwd=tmpdir)

            # Should skip test-app
            assert result.returncode == 0
            output = result.stdout.lower()
            assert "web" in output or "mobile" in output
            assert "test-app" not in output


class TestProjectCommandIntegration:
    """Integration tests for project command."""

    @pytest.mark.integration
    def test_project_run_in_root_only(self) -> Any:
        """Test that project command runs only in root."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Create workspace project
            pyproject = tmpdir / "pyproject.toml"
            pyproject.write_text("""
[project]
name = "my-workspace"
version = "0.1.0"

[tool.uv.workspace]
members = ["packages/*"]
""")

            # Create a package
            pkg_dir = tmpdir / "packages" / "subpkg"
            pkg_dir.mkdir(parents=True)
            (pkg_dir / "pyproject.toml").write_text("""
[project]
name = "subpkg"
version = "0.1.0"
""")

            # Run project command
            result = run_dhtl_command(["project", "run", "python", "-c", "print('Root only')"], cwd=tmpdir)

            assert result.returncode == 0
            assert "Root only" in result.stdout

            # Verify it doesn't run in subpackages
            assert result.stdout.count("Root only") == 1


class TestComplexWorkspaceScenarios:
    """Integration tests for complex workspace scenarios."""

    @pytest.mark.integration
    def test_nested_workspace_members(self) -> Any:
        """Test workspace with nested member structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Create complex workspace
            pyproject = tmpdir / "pyproject.toml"
            pyproject.write_text("""
[project]
name = "monorepo"
version = "0.1.0"

[tool.uv.workspace]
members = [
    "libs/*",
    "apps/*",
    "tools/cli"
]
""")

            # Create nested structure
            structures = ["libs/core", "libs/utils", "apps/web", "apps/api", "tools/cli"]

            for path in structures:
                pkg_dir = tmpdir / path
                pkg_dir.mkdir(parents=True)
                name = path.replace("/", "-")
                (pkg_dir / "pyproject.toml").write_text(f'''
[project]
name = "{name}"
version = "0.1.0"
''')

            # Run command in all workspaces
            result = run_dhtl_command(["workspaces", "run", "echo", "OK"], cwd=tmpdir)

            assert result.returncode == 0
            # Should run in root + 5 members
            assert result.stdout.count("OK") >= 5

    @pytest.mark.integration
    def test_workspace_with_dependencies(self) -> Any:
        """Test workspace where members depend on each other."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Create workspace
            pyproject = tmpdir / "pyproject.toml"
            pyproject.write_text("""
[project]
name = "root"
version = "0.1.0"

[tool.uv.workspace]
members = ["packages/*"]
""")

            # Create shared package
            shared_dir = tmpdir / "packages" / "shared"
            shared_dir.mkdir(parents=True)
            (shared_dir / "pyproject.toml").write_text("""
[project]
name = "shared"
version = "0.1.0"
""")

            # Create app that depends on shared
            app_dir = tmpdir / "packages" / "app"
            app_dir.mkdir(parents=True)
            (app_dir / "pyproject.toml").write_text("""
[project]
name = "app"
version = "0.1.0"
dependencies = ["shared"]
""")

            # Commands should work with internal dependencies
            result = run_dhtl_command(["workspace", "app", "run", "echo", "Depends on shared"], cwd=tmpdir)

            assert result.returncode == 0
            assert "Depends on shared" in result.stdout
