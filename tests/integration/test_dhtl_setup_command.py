#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Integration tests for dhtl setup command.

Tests the dhtl setup command using real UV and following TDD principles.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Initial test suite for dhtl setup command
# - Tests real UV setup functionality
# - Follows UV documentation best practices
# - No mocking - uses real commands
#

import pytest
import tempfile
import subprocess
import shutil
from pathlib import Path
from typing import Generator
import tomllib
import os

from DHT.modules.uv_manager import UVManager


class TestDhtlSetupCommand:
    """Test dhtl setup command implementation."""
    
    @pytest.fixture
    def temp_dir(self) -> Generator[Path, None, None]:
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    @pytest.fixture
    def uv_available(self) -> bool:
        """Check if UV is available."""
        return shutil.which("uv") is not None
    
    def test_setup_existing_project(self, temp_dir, uv_available):
        """Test setting up an existing Python project."""
        if not uv_available:
            pytest.skip("UV is not installed")
        
        project_path = temp_dir / "existing-project"
        project_path.mkdir()
        
        # Create a basic pyproject.toml
        pyproject_content = """[project]
name = "existing-project"
version = "0.1.0"
description = "Test project"
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
        (project_path / "pyproject.toml").write_text(pyproject_content)
        (project_path / "README.md").write_text("# Existing Project")
        
        # Create source directory
        src_dir = project_path / "existing_project"
        src_dir.mkdir()
        (src_dir / "__init__.py").write_text('__version__ = "0.1.0"')
        
        from DHT.modules.dhtl_commands import DhtlCommands
        commands = DhtlCommands()
        
        result = commands.setup(
            path=str(project_path)
        )
        
        # Verify the command succeeded
        assert result["success"] is True
        assert "Setup completed" in result["message"]
        
        # Verify virtual environment was created
        venv_path = project_path / ".venv"
        assert venv_path.exists()
        assert (venv_path / "bin" / "python").exists() or (venv_path / "Scripts" / "python.exe").exists()
        
        # Verify lock file was created
        assert (project_path / "uv.lock").exists()
        
        # Verify dependencies were installed
        assert "installed" in result
        assert result["installed"]["dependencies"] > 0
    
    def test_setup_with_dev_dependencies(self, temp_dir, uv_available):
        """Test setting up project with development dependencies."""
        if not uv_available:
            pytest.skip("UV is not installed")
        
        project_path = temp_dir / "dev-project"
        project_path.mkdir()
        
        # Create pyproject.toml with dev dependencies
        pyproject_content = """[project]
name = "dev-project"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = ["requests"]

[project.optional-dependencies]
dev = ["pytest", "ruff", "mypy"]
test = ["pytest-cov", "pytest-xdist"]
"""
        (project_path / "pyproject.toml").write_text(pyproject_content)
        
        from DHT.modules.dhtl_commands import DhtlCommands
        commands = DhtlCommands()
        
        result = commands.setup(
            path=str(project_path),
            dev=True  # Install dev dependencies
        )
        
        assert result["success"] is True
        
        # Verify dev dependencies were installed
        assert result["installed"]["dev_dependencies"] > 0
    
    def test_setup_from_requirements_txt(self, temp_dir, uv_available):
        """Test setting up project from requirements.txt."""
        if not uv_available:
            pytest.skip("UV is not installed")
        
        project_path = temp_dir / "legacy-project"
        project_path.mkdir()
        
        # Create requirements.txt
        requirements = """requests>=2.28.0
click>=8.0.0
pydantic>=2.0.0
# Development dependencies
pytest>=7.0.0
black>=23.0.0
"""
        (project_path / "requirements.txt").write_text(requirements)
        
        # Also create requirements-dev.txt
        requirements_dev = """pytest-cov>=4.0.0
mypy>=1.0.0
ruff>=0.1.0
"""
        (project_path / "requirements-dev.txt").write_text(requirements_dev)
        
        from DHT.modules.dhtl_commands import DhtlCommands
        commands = DhtlCommands()
        
        result = commands.setup(
            path=str(project_path),
            from_requirements=True
        )
        
        assert result["success"] is True
        
        # Verify pyproject.toml was created
        assert (project_path / "pyproject.toml").exists()
        
        # Verify dependencies were imported
        with open(project_path / "pyproject.toml", "rb") as f:
            pyproject = tomllib.load(f)
        
        deps = pyproject["project"]["dependencies"]
        assert any("requests" in dep for dep in deps)
        assert any("click" in dep for dep in deps)
    
    def test_setup_with_python_version(self, temp_dir, uv_available):
        """Test setting up project with specific Python version."""
        if not uv_available:
            pytest.skip("UV is not installed")
        
        project_path = temp_dir / "python-version-project"
        project_path.mkdir()
        
        # Create basic pyproject.toml
        pyproject_content = """[project]
name = "python-version-project"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = []
"""
        (project_path / "pyproject.toml").write_text(pyproject_content)
        
        from DHT.modules.dhtl_commands import DhtlCommands
        commands = DhtlCommands()
        
        result = commands.setup(
            path=str(project_path),
            python="3.11"  # Specific Python version
        )
        
        assert result["success"] is True
        
        # Verify .python-version was created
        assert (project_path / ".python-version").exists()
        python_version = (project_path / ".python-version").read_text().strip()
        assert python_version == "3.11"
    
    def test_setup_with_install_flags(self, temp_dir, uv_available):
        """Test setup with additional install flags."""
        if not uv_available:
            pytest.skip("UV is not installed")
        
        project_path = temp_dir / "flags-project"
        project_path.mkdir()
        
        pyproject_content = """[project]
name = "flags-project"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = ["requests", "httpx"]
"""
        (project_path / "pyproject.toml").write_text(pyproject_content)
        
        from DHT.modules.dhtl_commands import DhtlCommands
        commands = DhtlCommands()
        
        result = commands.setup(
            path=str(project_path),
            compile_bytecode=True,  # Compile Python files
            editable=True  # Install in editable mode
        )
        
        assert result["success"] is True
        assert result["options"]["compile_bytecode"] is True
        assert result["options"]["editable"] is True
    
    def test_setup_workspace_project(self, temp_dir, uv_available):
        """Test setting up a workspace with multiple packages."""
        if not uv_available:
            pytest.skip("UV is not installed")
        
        workspace_path = temp_dir / "workspace"
        workspace_path.mkdir()
        
        # Create workspace pyproject.toml
        workspace_pyproject = """[tool.uv.workspace]
members = ["packages/*"]
"""
        (workspace_path / "pyproject.toml").write_text(workspace_pyproject)
        
        # Create package A
        pkg_a = workspace_path / "packages" / "package-a"
        pkg_a.mkdir(parents=True)
        pkg_a_pyproject = """[project]
name = "package-a"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = []
"""
        (pkg_a / "pyproject.toml").write_text(pkg_a_pyproject)
        
        # Create package B
        pkg_b = workspace_path / "packages" / "package-b"
        pkg_b.mkdir(parents=True)
        pkg_b_pyproject = """[project]
name = "package-b"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = ["package-a"]

[tool.uv.sources]
package-a = { workspace = true }
"""
        (pkg_b / "pyproject.toml").write_text(pkg_b_pyproject)
        
        from DHT.modules.dhtl_commands import DhtlCommands
        commands = DhtlCommands()
        
        result = commands.setup(
            path=str(workspace_path),
            all_packages=True  # Install all workspace packages
        )
        
        assert result["success"] is True
        assert result["workspace"]["packages_installed"] == 2
    
    def test_setup_with_index_url(self, temp_dir, uv_available):
        """Test setup with custom package index."""
        if not uv_available:
            pytest.skip("UV is not installed")
        
        project_path = temp_dir / "custom-index-project"
        project_path.mkdir()
        
        pyproject_content = """[project]
name = "custom-index-project"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = ["requests"]
"""
        (project_path / "pyproject.toml").write_text(pyproject_content)
        
        from DHT.modules.dhtl_commands import DhtlCommands
        commands = DhtlCommands()
        
        # Note: Using default PyPI URL for testing
        result = commands.setup(
            path=str(project_path),
            index_url="https://pypi.org/simple"
        )
        
        assert result["success"] is True
        assert result["options"]["index_url"] == "https://pypi.org/simple"
    
    def test_setup_idempotent(self, temp_dir, uv_available):
        """Test that setup is idempotent (can be run multiple times)."""
        if not uv_available:
            pytest.skip("UV is not installed")
        
        project_path = temp_dir / "idempotent-project"
        project_path.mkdir()
        
        pyproject_content = """[project]
name = "idempotent-project"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = ["click"]
"""
        (project_path / "pyproject.toml").write_text(pyproject_content)
        
        from DHT.modules.dhtl_commands import DhtlCommands
        commands = DhtlCommands()
        
        # First setup
        result1 = commands.setup(path=str(project_path))
        assert result1["success"] is True
        
        # Second setup should also succeed
        result2 = commands.setup(path=str(project_path))
        assert result2["success"] is True
        assert "already set up" in result2["message"].lower() or "setup completed" in result2["message"].lower()
    
    def test_setup_with_pre_commit(self, temp_dir, uv_available):
        """Test setting up pre-commit hooks."""
        if not uv_available:
            pytest.skip("UV is not installed")
        
        project_path = temp_dir / "pre-commit-project"
        project_path.mkdir()
        
        pyproject_content = """[project]
name = "pre-commit-project"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = []

[project.optional-dependencies]
dev = ["pre-commit"]
"""
        (project_path / "pyproject.toml").write_text(pyproject_content)
        
        # Create .pre-commit-config.yaml
        pre_commit_config = """repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.0
    hooks:
      - id: ruff
      - id: ruff-format
"""
        (project_path / ".pre-commit-config.yaml").write_text(pre_commit_config)
        
        from DHT.modules.dhtl_commands import DhtlCommands
        commands = DhtlCommands()
        
        result = commands.setup(
            path=str(project_path),
            dev=True,
            install_pre_commit=True  # Install pre-commit hooks
        )
        
        assert result["success"] is True
        # Note: We can't easily verify git hooks were installed in test environment
        # but we can check the command tried to install them
        assert result["options"].get("install_pre_commit") is True