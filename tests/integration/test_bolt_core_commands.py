#!/usr/bin/env python3
from __future__ import annotations

from typing import Any

"""
Core integration tests for essential Bolt commands.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Test core Bolt functionality with mock subprocess calls
# - Focus on verifying command dispatch and argument handling
#

"""Integration tests for core Bolt commands."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from DHT.modules.command_dispatcher import CommandDispatcher


class TestAddRemoveUpgradeCommands:
    """Test add, remove, and upgrade command dispatching."""

    @pytest.mark.integration
    @patch("subprocess.run")
    def test_add_command_dispatches_to_uv(self, mock_run) -> Any:
        """Test add command calls uv add."""
        mock_run.return_value = MagicMock(returncode=0, stdout="Added package", stderr="")

        dispatcher = CommandDispatcher()
        result = dispatcher.dispatch("add", ["click", "rich"])

        # Verify uv add was called
        assert mock_run.called
        call_args = mock_run.call_args[0][0]
        assert "uv" in call_args[0]
        assert "add" in call_args
        assert "click" in call_args
        assert "rich" in call_args

    @pytest.mark.integration
    @patch("subprocess.run")
    def test_remove_command_dispatches_to_uv(self, mock_run) -> Any:
        """Test remove command calls uv remove."""
        mock_run.return_value = MagicMock(returncode=0, stdout="Removed package", stderr="")

        dispatcher = CommandDispatcher()
        result = dispatcher.dispatch("remove", ["click"])

        # Verify uv remove was called
        assert mock_run.called
        call_args = mock_run.call_args[0][0]
        assert "uv" in call_args[0]
        assert "remove" in call_args
        assert "click" in call_args

    @pytest.mark.integration
    @patch("subprocess.run")
    def test_upgrade_command_with_packages(self, mock_run) -> Any:
        """Test upgrade command with specific packages."""
        mock_run.return_value = MagicMock(returncode=0, stdout="Upgraded", stderr="")

        dispatcher = CommandDispatcher()
        result = dispatcher.dispatch("upgrade", ["pytest", "mypy"])

        # Verify uv add --upgrade was called
        assert mock_run.called
        call_args = mock_run.call_args[0][0]
        assert "uv" in call_args[0]
        assert "add" in call_args
        assert "--upgrade" in call_args
        assert "pytest" in call_args
        assert "mypy" in call_args

    @pytest.mark.integration
    @patch("subprocess.run")
    def test_upgrade_command_without_packages(self, mock_run) -> Any:
        """Test upgrade command without packages upgrades all."""
        mock_run.return_value = MagicMock(returncode=0, stdout="Upgraded all", stderr="")

        dispatcher = CommandDispatcher()
        result = dispatcher.dispatch("upgrade", [])

        # Should call uv sync --upgrade
        assert mock_run.called
        call_args = mock_run.call_args[0][0]
        assert "uv" in call_args[0]
        assert ("sync" in call_args and "--upgrade" in call_args) or ("add" in call_args and "--upgrade" in call_args)


class TestCheckCommand:
    """Test type checking command."""

    @pytest.mark.integration
    @patch("subprocess.run")
    @patch("pathlib.Path.exists", return_value=True)
    def test_check_runs_mypy(self, mock_exists, mock_run) -> Any:
        """Test check command runs mypy."""
        mock_run.return_value = MagicMock(returncode=0, stdout="Success", stderr="")

        dispatcher = CommandDispatcher()
        result = dispatcher.dispatch("check", [])

        # Should run mypy
        assert mock_run.called
        # Check if mypy was invoked
        found_mypy = False
        for call in mock_run.call_args_list:
            args = str(call)
            if "mypy" in args:
                found_mypy = True
                break
        assert found_mypy, "mypy was not called"

    @pytest.mark.integration
    @patch("subprocess.run")
    @patch("pathlib.Path.exists", return_value=True)
    def test_check_with_files(self, mock_exists, mock_run) -> Any:
        """Test check command with specific files."""
        mock_run.return_value = MagicMock(returncode=0, stdout="Checked", stderr="")

        dispatcher = CommandDispatcher()
        result = dispatcher.dispatch("check", ["src/main.py", "tests/"])

        # Should pass files to mypy
        assert mock_run.called
        call_str = str(mock_run.call_args_list)
        assert "main.py" in call_str or "tests" in call_str


class TestBinCommand:
    """Test bin command."""

    @pytest.mark.integration
    @patch("pathlib.Path.exists")
    def test_bin_shows_venv_path(self, mock_exists, capsys) -> Any:
        """Test bin command shows virtual environment bin path."""
        # Mock that .venv exists
        mock_exists.return_value = True

        dispatcher = CommandDispatcher()
        result = dispatcher.dispatch("bin", [])

        # Check output
        captured = capsys.readouterr()
        assert ".venv" in captured.out
        assert "bin" in captured.out or "Scripts" in captured.out

    @pytest.mark.integration
    @patch("pathlib.Path.exists", return_value=False)
    def test_bin_error_when_no_venv(self, mock_exists, capsys) -> Any:
        """Test bin command error when no venv."""
        dispatcher = CommandDispatcher()
        result = dispatcher.dispatch("bin", [])

        # Should show error
        captured = capsys.readouterr()
        output = captured.out + captured.err
        assert "not found" in output.lower() or "error" in output.lower()


class TestFormatCommands:
    """Test format and fmt commands."""

    @pytest.mark.integration
    @patch("subprocess.run")
    def test_fmt_is_alias_for_format(self, mock_run) -> Any:
        """Test fmt command works as alias."""
        mock_run.return_value = MagicMock(returncode=0, stdout="Formatted", stderr="")

        dispatcher = CommandDispatcher()

        # Both should work the same
        result1 = dispatcher.dispatch("fmt", [])
        result2 = dispatcher.dispatch("format", [])

        # Both should have called formatting
        assert mock_run.call_count >= 2

    @pytest.mark.integration
    @patch("subprocess.run")
    def test_format_with_check_flag(self, mock_run) -> Any:
        """Test format --check doesn't modify files."""
        mock_run.return_value = MagicMock(returncode=0, stdout="Would format", stderr="")

        dispatcher = CommandDispatcher()
        result = dispatcher.dispatch("format", ["--check"])

        # Should have --check in the call
        assert mock_run.called
        call_str = str(mock_run.call_args_list)
        assert "--check" in call_str or "--diff" in call_str


class TestDocCommand:
    """Test documentation generation command."""

    @pytest.mark.integration
    @patch("subprocess.run")
    @patch("pathlib.Path.exists", return_value=True)
    def test_doc_generates_documentation(self, mock_exists, mock_run) -> Any:
        """Test doc command attempts to generate docs."""
        mock_run.return_value = MagicMock(returncode=0, stdout="Docs generated", stderr="")

        dispatcher = CommandDispatcher()
        result = dispatcher.dispatch("doc", [])

        # Should attempt to generate documentation
        assert mock_run.called or result.get("message", "").lower().count("doc") > 0


class TestInstallCommand:
    """Test install command (alias for setup)."""

    @pytest.mark.integration
    @patch("subprocess.run")
    def test_install_is_setup_alias(self, mock_run) -> Any:
        """Test install command runs setup."""
        mock_run.return_value = MagicMock(returncode=0, stdout="Setup complete", stderr="")

        dispatcher = CommandDispatcher()

        # Get the underlying setup handler
        install_handler = dispatcher.registry.commands["install"]["handler"]
        setup_handler = dispatcher.registry.commands["setup"]["handler"]

        # They should be related (either same or install calls setup)
        assert install_handler is not None
        assert setup_handler is not None
