#!/usr/bin/env python3
"""
Integration tests for dhtl sync command.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

"""Integration tests for dhtl sync command."""

from pathlib import Path
from typing import Any

import pytest

from DHT.modules.dhtl_commands import DHTLCommands


class TestDHTLSyncCommand:
    """Test cases for dhtl sync command."""

    @pytest.fixture
    def commands(self) -> Any:
        """Create DHTLCommands instance."""
        return DHTLCommands()

    def test_sync_basic_project(self, commands, tmp_path) -> Any:
        """Test syncing dependencies for a basic project."""
        # Create project directory
        project_dir = tmp_path / "test-project"
        project_dir.mkdir()

        # Initialize project first
        init_result = commands.init(str(project_dir), python="3.11")
        assert init_result["success"]

        # Add some dependencies to pyproject.toml
        pyproject_path = project_dir / "pyproject.toml"
        content = pyproject_path.read_text()
        # Add requests as a dependency
        new_content = content.replace("dependencies = []", 'dependencies = ["requests>=2.28.0"]')
        pyproject_path.write_text(new_content)

        # Run sync
        result = commands.sync(str(project_dir))

        # Check result
        assert result["success"]
        assert "installed" in result
        assert result["installed"] > 0  # Should install requests and its deps
        assert "lock_file" in result
        assert Path(result["lock_file"]).exists()

    def test_sync_with_locked_dependencies(self, commands, tmp_path) -> Any:
        """Test syncing with locked dependencies."""
        # Create project
        project_dir = tmp_path / "locked-project"
        project_dir.mkdir()

        # Initialize and setup project
        init_result = commands.init(str(project_dir), python="3.11")
        assert init_result["success"]

        # First sync to create lock file
        result1 = commands.sync(str(project_dir))
        assert result1["success"]
        lock_file = Path(result1["lock_file"])
        assert lock_file.exists()

        # Record lock file modification time
        lock_mtime = lock_file.stat().st_mtime

        # Sync again with --locked flag
        result2 = commands.sync(str(project_dir), locked=True)
        assert result2["success"]

        # Lock file should not have been modified
        assert lock_file.stat().st_mtime == lock_mtime

    def test_sync_with_dev_dependencies(self, commands, tmp_path) -> Any:
        """Test syncing with development dependencies."""
        # Create project
        project_dir = tmp_path / "dev-project"
        project_dir.mkdir()

        # Initialize with dev dependencies
        init_result = commands.init(str(project_dir), python="3.11", package=True)
        assert init_result["success"]

        # Add dev dependencies to pyproject.toml
        pyproject_path = project_dir / "pyproject.toml"
        content = pyproject_path.read_text()
        # Add dev dependencies section if not exists
        if "[project.optional-dependencies]" not in content:
            content += """
[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "black>=23.0.0",
    "ruff>=0.1.0"
]
"""
            pyproject_path.write_text(content)

        # Sync with dev dependencies
        result = commands.sync(str(project_dir), dev=True)

        # Check result
        assert result["success"]
        assert result["installed"] > 3  # At least pytest, black, ruff + their deps
        assert result.get("dev_dependencies_installed", False)

    def test_sync_without_dev_dependencies(self, commands, tmp_path) -> Any:
        """Test syncing without development dependencies."""
        # Create project with dev deps
        project_dir = tmp_path / "no-dev-project"
        project_dir.mkdir()

        # Initialize
        init_result = commands.init(str(project_dir), python="3.11")
        assert init_result["success"]

        # Add both regular and dev dependencies
        pyproject_path = project_dir / "pyproject.toml"
        content = pyproject_path.read_text()
        content = content.replace("dependencies = []", 'dependencies = ["requests>=2.28.0"]')
        content += """
[project.optional-dependencies]
dev = ["pytest>=7.0.0", "black>=23.0.0"]
"""
        pyproject_path.write_text(content)

        # Sync without dev (default)
        result = commands.sync(str(project_dir), no_dev=True)

        # Check result
        assert result["success"]
        # Should only install requests and deps, not pytest/black
        assert not result.get("dev_dependencies_installed", False)

    def test_sync_with_extras(self, commands, tmp_path) -> Any:
        """Test syncing with extra dependency groups."""
        # Create project
        project_dir = tmp_path / "extras-project"
        project_dir.mkdir()

        # Initialize
        init_result = commands.init(str(project_dir), python="3.11")
        assert init_result["success"]

        # Add extras to pyproject.toml
        pyproject_path = project_dir / "pyproject.toml"
        content = pyproject_path.read_text()
        content += """
[project.optional-dependencies]
test = ["pytest>=7.0.0", "pytest-cov>=4.0.0"]
docs = ["sphinx>=5.0.0", "sphinx-rtd-theme>=1.0.0"]
"""
        pyproject_path.write_text(content)

        # Sync with specific extras
        result = commands.sync(str(project_dir), extras=["test", "docs"])

        # Check result
        assert result["success"]
        assert result["installed"] > 4  # At least the 4 packages + deps
        assert "extras" in result
        assert set(result["extras"]) == {"test", "docs"}

    def test_sync_with_upgrade(self, commands, tmp_path) -> Any:
        """Test syncing with dependency upgrade."""
        # Create project
        project_dir = tmp_path / "upgrade-project"
        project_dir.mkdir()

        # Initialize with old dependency
        init_result = commands.init(str(project_dir), python="3.11")
        assert init_result["success"]

        # Add dependency with old version
        pyproject_path = project_dir / "pyproject.toml"
        content = pyproject_path.read_text()
        content = content.replace(
            "dependencies = []",
            'dependencies = ["requests>=2.20.0"]',  # Old version
        )
        pyproject_path.write_text(content)

        # First sync
        result1 = commands.sync(str(project_dir))
        assert result1["success"]

        # Sync with upgrade flag
        result2 = commands.sync(str(project_dir), upgrade=True)
        assert result2["success"]
        assert result2.get("upgraded", False)

    def test_sync_nonexistent_project(self, commands, tmp_path) -> Any:
        """Test syncing a nonexistent project."""
        # Try to sync nonexistent project
        fake_dir = tmp_path / "nonexistent"
        result = commands.sync(str(fake_dir))

        # Should fail
        assert not result["success"]
        assert "error" in result
        assert "not found" in result["error"].lower() or "does not exist" in result["error"].lower()

    def test_sync_project_without_pyproject(self, commands, tmp_path) -> Any:
        """Test syncing project without pyproject.toml."""
        # Create directory without pyproject.toml
        project_dir = tmp_path / "no-pyproject"
        project_dir.mkdir()

        # Try to sync
        result = commands.sync(str(project_dir))

        # Should fail
        assert not result["success"]
        assert "pyproject.toml" in result["error"]

    def test_sync_updates_lock_file(self, commands, tmp_path) -> Any:
        """Test that sync updates the lock file when dependencies change."""
        # Create and initialize project
        project_dir = tmp_path / "lock-update-test"
        project_dir.mkdir()
        init_result = commands.init(str(project_dir), python="3.11")
        assert init_result["success"]

        # First sync
        result1 = commands.sync(str(project_dir))
        assert result1["success"]
        lock_file = Path(result1["lock_file"])
        initial_content = lock_file.read_text()

        # Add a new dependency
        pyproject_path = project_dir / "pyproject.toml"
        content = pyproject_path.read_text()
        content = content.replace("dependencies = []", 'dependencies = ["click>=8.0.0"]')
        pyproject_path.write_text(content)

        # Sync again
        result2 = commands.sync(str(project_dir))
        assert result2["success"]

        # Lock file should have changed
        new_content = lock_file.read_text()
        assert new_content != initial_content
        assert "click" in new_content
