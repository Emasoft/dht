#!/usr/bin/env python3

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Initial test file for Bolt compatibility commands
# - Tests for command aliases and new commands
# - Tests for workspace functionality
#

"""
Test Bolt compatibility features in DHT.

Tests that DHT commands work like Bolt commands for easy transition.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from DHT.modules.command_dispatcher import CommandDispatcher
from DHT.modules.command_registry import CommandRegistry


class TestBoltCommandAliases:
    """Test Bolt command aliases work correctly."""

    def setup_method(self):
        """Set up test fixtures."""
        self.dispatcher = CommandDispatcher()
        self.registry = CommandRegistry()

    def test_install_alias_for_setup(self):
        """Test that 'dhtl install' works as alias for 'dhtl setup'."""
        # Ensure 'install' command exists
        assert "install" in self.registry.commands

        # Check that install is properly registered
        install_help = self.registry.commands["install"]["help"]
        assert "alias for setup" in install_help.lower()

    def test_add_command_exists(self):
        """Test that 'dhtl add [package]' command exists."""
        assert "add" in self.registry.commands
        assert self.registry.commands["add"]["help"] == "Add dependencies to the project"

    def test_remove_command_exists(self):
        """Test that 'dhtl remove [package]' command exists."""
        assert "remove" in self.registry.commands
        assert self.registry.commands["remove"]["help"] == "Remove dependencies from the project"

    def test_upgrade_command_exists(self):
        """Test that 'dhtl upgrade [package]' command exists."""
        assert "upgrade" in self.registry.commands
        assert self.registry.commands["upgrade"]["help"] == "Upgrade dependencies"

    def test_fmt_alias_for_format(self):
        """Test that 'dhtl fmt' works as alias for 'dhtl format'."""
        assert "fmt" in self.registry.commands
        # Check that fmt is properly registered as an alias
        fmt_help = self.registry.commands["fmt"]["help"]
        assert "alias for format" in fmt_help.lower()

    def test_check_command_exists(self):
        """Test that 'dhtl check' command exists for type checking."""
        assert "check" in self.registry.commands
        assert self.registry.commands["check"]["help"] == "Type check Python code"

    def test_doc_command_exists(self):
        """Test that 'dhtl doc' command exists."""
        assert "doc" in self.registry.commands
        assert self.registry.commands["doc"]["help"] == "Generate project documentation"

    def test_bin_command_exists(self):
        """Test that 'dhtl bin' command exists."""
        assert "bin" in self.registry.commands
        assert self.registry.commands["bin"]["help"] == "Print executable files installation folder"


class TestBoltWorkspaceCommands:
    """Test Bolt workspace commands."""

    def setup_method(self):
        """Set up test fixtures."""
        self.dispatcher = CommandDispatcher()
        self.registry = CommandRegistry()

    def test_workspaces_command_exists(self):
        """Test that 'dhtl workspaces' command exists."""
        assert "workspaces" in self.registry.commands
        assert "ws" in self.registry.commands  # Short alias

    def test_workspace_run_subcommand(self):
        """Test 'dhtl workspaces run [script]' functionality."""
        # This will be implemented to run script in all workspace members
        pass

    def test_workspace_exec_subcommand(self):
        """Test 'dhtl ws exec -- [cmd]' functionality."""
        # This will be implemented to execute command in all workspace members
        pass

    def test_workspace_filtering_options(self):
        """Test workspace filtering options like --only and --ignore."""
        # Test that filtering options work correctly
        pass

    def test_specific_workspace_targeting(self):
        """Test 'dhtl workspace [name] run [script]' functionality."""
        assert "workspace" in self.registry.commands
        assert "w" in self.registry.commands  # Short alias

    def test_project_command_exists(self):
        """Test that 'dhtl project' command exists."""
        assert "project" in self.registry.commands
        assert "p" in self.registry.commands  # Short alias


class TestBoltDefaultBehavior:
    """Test Bolt default behaviors."""

    def setup_method(self):
        """Set up test fixtures."""
        self.dispatcher = CommandDispatcher()

    @patch("DHT.modules.command_dispatcher.CommandDispatcher.dispatch")
    def test_no_args_defaults_to_install(self, mock_dispatch):
        """Test that 'dhtl' with no args defaults to 'dhtl install'."""
        # When main() is called with no command, it should run 'install'
        # This will be implemented in dhtl.py main function
        pass

    @patch("DHT.modules.command_dispatcher.CommandDispatcher.dispatch")
    def test_unknown_command_defaults_to_run(self, mock_dispatch):
        """Test that unknown commands default to 'dhtl run [command]'."""
        # When an unknown command is given, it should be passed to 'run'
        # This will be implemented in command_dispatcher.py
        pass


class TestBoltCommandImplementations:
    """Test implementations of new Bolt-compatible commands."""

    def test_add_command_calls_uv_add(self):
        """Test that 'dhtl add numpy' calls 'uv add numpy'."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="Added numpy and pandas")

            dispatcher = CommandDispatcher()
            result = dispatcher.dispatch("add", ["numpy", "pandas"])

            # Verify uv add was called with correct packages
            # Find the call that contains 'uv add'
            uv_add_called = False
            for call in mock_run.call_args_list:
                args = call[0][0] if call[0] else []
                if isinstance(args, list) and len(args) >= 2 and args[0] == "uv" and args[1] == "add":
                    uv_add_called = True
                    assert "numpy" in args
                    assert "pandas" in args
                    break
            assert uv_add_called, "uv add command was not called"

    def test_remove_command_calls_uv_remove(self):
        """Test that 'dhtl remove numpy' calls 'uv remove numpy'."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="Removed numpy")

            dispatcher = CommandDispatcher()
            result = dispatcher.dispatch("remove", ["numpy"])

            # Verify uv remove was called
            # Find the call that contains 'uv remove'
            uv_remove_called = False
            for call in mock_run.call_args_list:
                args = call[0][0] if call[0] else []
                if isinstance(args, list) and len(args) >= 2 and args[0] == "uv" and args[1] == "remove":
                    uv_remove_called = True
                    assert "numpy" in args
                    break
            assert uv_remove_called, "uv remove command was not called"
        args = mock_run.call_args[0][0]
        assert args[0] == "uv"
        assert args[1] == "remove"
        assert "numpy" in args

    @patch("subprocess.run")
    def test_upgrade_command_calls_uv_add_upgrade(self, mock_run):
        """Test that 'dhtl upgrade numpy' calls 'uv add --upgrade numpy'."""
        mock_run.return_value = MagicMock(returncode=0)

        dispatcher = CommandDispatcher()
        result = dispatcher.dispatch("upgrade", ["numpy"])

        # Verify uv add --upgrade was called
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert args[0] == "uv"
        assert args[1] == "add"
        assert "--upgrade" in args
        assert "numpy" in args

    @patch("subprocess.run")
    def test_check_command_calls_mypy(self, mock_run):
        """Test that 'dhtl check' calls mypy for type checking."""
        mock_run.return_value = MagicMock(returncode=0)

        dispatcher = CommandDispatcher()
        result = dispatcher.dispatch("check", [])

        # Verify mypy was called
        mock_run.assert_called()
        # Check that mypy was called in the subprocess
        call_found = False
        for call_args in mock_run.call_args_list:
            args = call_args[0][0]
            if "mypy" in str(args):
                call_found = True
                break
        assert call_found

    def test_bin_command_prints_venv_bin_path(self, capsys):
        """Test that 'dhtl bin' prints the venv bin directory."""
        dispatcher = CommandDispatcher()

        with patch("pathlib.Path.exists", return_value=True):
            result = dispatcher.dispatch("bin", [])

        captured = capsys.readouterr()
        # Should print something like .venv/bin or .venv/Scripts
        assert ".venv" in captured.out
        assert "bin" in captured.out or "Scripts" in captured.out


class TestWorkspaceDetection:
    """Test workspace detection and iteration."""

    def test_detect_workspace_from_pyproject(self, tmp_path):
        """Test detection of UV workspace from pyproject.toml."""
        # Create a workspace pyproject.toml
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("""
[tool.uv.workspace]
members = ["packages/*"]
""")

        # Create package directories
        (tmp_path / "packages" / "pkg1").mkdir(parents=True)
        (tmp_path / "packages" / "pkg2").mkdir(parents=True)

        # Test workspace detection
        # This will be implemented in workspace module
        pass

    def test_iterate_workspace_members(self, tmp_path):
        """Test iteration over workspace members."""
        # Set up workspace structure
        # Test that we can iterate over all members
        pass
