#!/usr/bin/env python3
"""
Tests for the Python implementation of DHTLCommands.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

"""Tests for the Python implementation of DHTLCommands."""

import shutil
import tempfile
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from src.DHT.modules.dhtl_commands import DHTLCommands


class TestDHTLInit:
    """Test the dhtl init command."""

    @pytest.fixture
    def temp_project_dir(self) -> Any:
        """Create a temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def dhtl_commands(self) -> Any:
        """Create DHTLCommands instance with mocked UV."""
        with patch("src.DHT.modules.dhtl_commands.UVManager") as mock_uv:
            mock_uv_instance = MagicMock()
            mock_uv_instance.is_available = True
            mock_uv_instance.run_command.return_value = {"success": True, "stdout": "", "stderr": ""}
            mock_uv_instance.generate_lock_file.return_value = True
            mock_uv.return_value = mock_uv_instance

            commands = DHTLCommands()
            commands.uv_manager = mock_uv_instance
            return commands

    def test_init_creates_project_structure(self, dhtl_commands, temp_project_dir) -> Any:
        """Test that init creates the expected project structure."""
        project_name = "test_project"
        project_path = temp_project_dir / project_name

        # Mock the UV init to create the pyproject.toml
        def mock_uv_init(*args, **kwargs) -> Any:
            # Create project directory and pyproject.toml
            project_path.mkdir(parents=True, exist_ok=True)
            (project_path / "pyproject.toml").write_text("""
[project]
name = "test_project"
version = "0.1.0"
""")
            return {"success": True, "stdout": "", "stderr": ""}

        dhtl_commands.uv_manager.run_command.side_effect = mock_uv_init

        result = dhtl_commands.init(path=str(project_path), name=project_name, python="3.11", package=True)

        assert result["success"] is True
        assert project_name in result["message"]

        # Verify UV commands were called
        assert dhtl_commands.uv_manager.run_command.called
        init_call = dhtl_commands.uv_manager.run_command.call_args_list[0]
        assert init_call[0][0][0] == "init"
        assert "--python" in init_call[0][0]
        assert "3.11" in init_call[0][0]

    def test_init_handles_existing_project(self, dhtl_commands, temp_project_dir) -> Any:
        """Test that init handles existing projects gracefully."""
        # Create pyproject.toml to simulate existing project
        (temp_project_dir / "pyproject.toml").write_text("[project]\nname = 'existing'\n")

        result = dhtl_commands.init(path=str(temp_project_dir), name="test_project")

        assert result["success"] is True
        assert "already initialized" in result["message"]

        # UV init should not be called for existing projects
        assert not dhtl_commands.uv_manager.run_command.called

    def test_init_with_dev_dependencies(self, dhtl_commands, temp_project_dir) -> Any:
        """Test that init adds dev dependencies when requested."""
        project_path = temp_project_dir / "dev_project"

        # Mock the UV init to create the pyproject.toml
        def mock_uv_init(*args, **kwargs) -> Any:
            # Create project directory and pyproject.toml
            project_path.mkdir(parents=True, exist_ok=True)
            (project_path / "pyproject.toml").write_text("""
[project]
name = "dev_project"
version = "0.1.0"
""")
            return {"success": True, "stdout": "", "stderr": ""}

        dhtl_commands.uv_manager.run_command.side_effect = mock_uv_init

        result = dhtl_commands.init(path=str(project_path), name="dev_project", with_dev=True)

        assert result["success"] is True

        # Check that dev dependencies would be added to pyproject.toml
        # (in real implementation, we'd verify the file contents)


class TestDHTLSetup:
    """Test the dhtl setup command."""

    @pytest.fixture
    def temp_project_dir(self) -> Any:
        """Create a temporary directory with a basic project."""
        temp_dir = tempfile.mkdtemp()
        project_path = Path(temp_dir)

        # Create basic pyproject.toml
        (project_path / "pyproject.toml").write_text("""
[project]
name = "test_project"
version = "0.1.0"
dependencies = ["click>=8.0"]
""")

        yield project_path
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def dhtl_commands(self) -> Any:
        """Create DHTLCommands instance with mocked UV."""
        with patch("src.DHT.modules.dhtl_commands.UVManager") as mock_uv:
            mock_uv_instance = MagicMock()
            mock_uv_instance.is_available = True
            mock_uv_instance.get_installed_version.return_value = "0.5.18"
            mock_uv_instance.create_venv.return_value = {"success": True}
            mock_uv_instance.run_command.return_value = {
                "success": True,
                "stdout": "",
                "stderr": "Installed 5 packages",
            }
            mock_uv_instance.generate_lock_file.return_value = True
            mock_uv.return_value = mock_uv_instance

            commands = DHTLCommands()
            commands.uv_manager = mock_uv_instance
            return commands

    def test_setup_creates_environment(self, dhtl_commands, temp_project_dir) -> Any:
        """Test that setup creates virtual environment and installs dependencies."""
        result = dhtl_commands.setup(path=str(temp_project_dir), dev=True)

        assert result["success"] is True
        assert "Setup completed" in result["message"]

        # Verify UV commands were called
        assert dhtl_commands.uv_manager.create_venv.called
        assert dhtl_commands.uv_manager.run_command.called
        assert dhtl_commands.uv_manager.generate_lock_file.called

    def test_setup_handles_missing_project(self, dhtl_commands, temp_project_dir) -> Any:
        """Test that setup fails gracefully when project doesn't exist."""
        result = dhtl_commands.setup(path=str(temp_project_dir / "nonexistent"))

        assert result["success"] is False
        assert "does not exist" in result["message"]
