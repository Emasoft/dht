#!/usr/bin/env python3

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Create tests for workspace commands (workspaces, workspace, project)
# - Test all subcommands: run, exec, upgrade, remove
# - Test filtering options and aliases
#

"""Tests for workspace commands."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from src.DHT.modules.commands.workspace_command import WorkspaceCommand
from src.DHT.modules.commands.workspaces_command import WorkspacesCommand


class TestWorkspacesCommand:
    """Tests for workspaces command."""

    def test_detect_workspace_members_no_config(self, tmp_path):
        """Test workspace detection with no configuration."""
        cmd = WorkspacesCommand()
        members = cmd.detect_workspace_members(tmp_path)
        assert members == []

    def test_detect_workspace_members_with_config(self, tmp_path):
        """Test workspace detection with valid configuration."""
        # Create root pyproject.toml with workspace config
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("""
[tool.uv.workspace]
members = ["packages/*", "apps/app1"]
exclude = ["packages/excluded"]
""")

        # Create workspace members
        (tmp_path / "packages" / "pkg1").mkdir(parents=True)
        (tmp_path / "packages" / "pkg1" / "pyproject.toml").write_text("[project]\nname = 'pkg1'")

        (tmp_path / "packages" / "pkg2").mkdir(parents=True)
        (tmp_path / "packages" / "pkg2" / "pyproject.toml").write_text("[project]\nname = 'pkg2'")

        (tmp_path / "packages" / "excluded").mkdir(parents=True)
        (tmp_path / "packages" / "excluded" / "pyproject.toml").write_text("[project]\nname = 'excluded'")

        (tmp_path / "apps" / "app1").mkdir(parents=True)
        (tmp_path / "apps" / "app1" / "pyproject.toml").write_text("[project]\nname = 'app1'")

        cmd = WorkspacesCommand()
        members = cmd.detect_workspace_members(tmp_path)

        # Should include root + pkg1 + pkg2 + app1 but not excluded
        member_names = [m.name for m in members]
        assert len(members) == 4
        assert tmp_path.name in member_names  # root
        assert "pkg1" in member_names
        assert "pkg2" in member_names
        assert "app1" in member_names
        assert "excluded" not in member_names

    @patch("subprocess.run")
    def test_workspaces_run_subcommand(self, mock_run, tmp_path):
        """Test workspaces run subcommand."""
        # Setup mock
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Success"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        # Create a simple workspace
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("""
[tool.uv.workspace]
members = ["pkg1"]
""")
        (tmp_path / "pkg1").mkdir()
        (tmp_path / "pkg1" / "pyproject.toml").write_text("[project]\nname = 'pkg1'")

        # Test without Prefect decoration - call the underlying method directly
        cmd = WorkspacesCommand()
        with patch.object(Path, "cwd", return_value=tmp_path):
            # Get the underlying method if it's wrapped by Prefect
            execute_method = cmd.execute
            if hasattr(execute_method, "fn"):
                execute_method = execute_method.fn

            result = execute_method(cmd, subcommand="run", script="test", args=["--verbose"])

        assert result["success"] is True
        assert "Ran script in" in result["message"]
        assert result["members_count"] == 2  # root + pkg1

        # Verify subprocess calls
        assert mock_run.call_count == 2
        # Check that uv run was called with correct arguments
        calls = mock_run.call_args_list
        for call in calls:
            args = call[0][0]
            assert args[0] == "uv"
            assert args[1] == "run"
            assert "--directory" in args
            assert "test" in args
            assert "--verbose" in args

    @patch("subprocess.run")
    def test_workspaces_exec_subcommand(self, mock_run, tmp_path):
        """Test workspaces exec subcommand."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Output"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("""
[tool.uv.workspace]
members = ["pkg1"]
""")
        (tmp_path / "pkg1").mkdir()
        (tmp_path / "pkg1" / "pyproject.toml").write_text("[project]\nname = 'pkg1'")

        cmd = WorkspacesCommand()
        with patch.object(Path, "cwd", return_value=tmp_path):
            # Get the underlying method if it's wrapped by Prefect
            execute_method = cmd.execute
            if hasattr(execute_method, "fn"):
                execute_method = execute_method.fn
            result = execute_method(cmd, subcommand="exec", args=["echo", "hello"])

        assert result["success"] is True
        assert "Executed command in" in result["message"]

    @patch("subprocess.run")
    def test_workspaces_upgrade_subcommand(self, mock_run, tmp_path):
        """Test workspaces upgrade subcommand."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Upgraded"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("""
[tool.uv.workspace]
members = ["pkg1"]
""")
        (tmp_path / "pkg1").mkdir()
        (tmp_path / "pkg1" / "pyproject.toml").write_text("[project]\nname = 'pkg1'")

        cmd = WorkspacesCommand()
        with patch.object(Path, "cwd", return_value=tmp_path):
            # Get the underlying method if it's wrapped by Prefect
            execute_method = cmd.execute
            if hasattr(execute_method, "fn"):
                execute_method = execute_method.fn
            result = execute_method(cmd, subcommand="upgrade", script="requests", args=["pytest"])

        assert result["success"] is True
        assert "Upgraded packages in" in result["message"]

        # Verify uv add --upgrade was called
        assert mock_run.call_count == 2
        for call in mock_run.call_args_list:
            args = call[0][0]
            assert args[0] == "uv"
            assert args[1] == "add"
            assert "--upgrade" in args
            assert "requests" in args
            assert "pytest" in args

    @patch("subprocess.run")
    def test_workspaces_remove_subcommand(self, mock_run, tmp_path):
        """Test workspaces remove subcommand."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Removed"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("""
[tool.uv.workspace]
members = ["pkg1"]
""")
        (tmp_path / "pkg1").mkdir()
        (tmp_path / "pkg1" / "pyproject.toml").write_text("[project]\nname = 'pkg1'")

        cmd = WorkspacesCommand()
        with patch.object(Path, "cwd", return_value=tmp_path):
            # Get the underlying method if it's wrapped by Prefect
            execute_method = cmd.execute
            if hasattr(execute_method, "fn"):
                execute_method = execute_method.fn
            result = execute_method(cmd, subcommand="remove", script="requests")

        assert result["success"] is True
        assert "Removed packages from" in result["message"]

        # Verify uv remove was called
        assert mock_run.call_count == 2
        for call in mock_run.call_args_list:
            args = call[0][0]
            assert args[0] == "uv"
            assert args[1] == "remove"
            assert "requests" in args

    def test_workspaces_filter_by_name(self, tmp_path):
        """Test filtering workspace members by name."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("""
[tool.uv.workspace]
members = ["packages/*"]
""")

        # Create multiple packages
        for name in ["foo", "bar", "foobar"]:
            pkg_dir = tmp_path / "packages" / name
            pkg_dir.mkdir(parents=True)
            (pkg_dir / "pyproject.toml").write_text(f"[project]\nname = '{name}'")

        cmd = WorkspacesCommand()
        members = cmd.detect_workspace_members(tmp_path)

        # Test pattern matching
        assert cmd._match_pattern("foo", "foo*")
        assert cmd._match_pattern("foobar", "foo*")
        assert not cmd._match_pattern("bar", "foo*")

    def test_workspaces_no_workspace(self, tmp_path):
        """Test error when not in a workspace."""
        cmd = WorkspacesCommand()
        with patch.object(Path, "cwd", return_value=tmp_path):
            # Get the underlying method if it's wrapped by Prefect
            execute_method = cmd.execute
            if hasattr(execute_method, "fn"):
                execute_method = execute_method.fn
            result = execute_method(cmd, subcommand="run", script="test")

        assert result["success"] is False
        assert "Not in a UV workspace" in result["error"]


class TestWorkspaceCommand:
    """Tests for single workspace command."""

    @patch("subprocess.run")
    def test_workspace_run_specific_member(self, mock_run, tmp_path):
        """Test running command in specific workspace member."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Success"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        # Create workspace with multiple members
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("""
[tool.uv.workspace]
members = ["packages/*"]
""")

        for name in ["pkg1", "pkg2"]:
            pkg_dir = tmp_path / "packages" / name
            pkg_dir.mkdir(parents=True)
            (pkg_dir / "pyproject.toml").write_text(f"[project]\nname = '{name}'")

        cmd = WorkspaceCommand()
        with patch.object(Path, "cwd", return_value=tmp_path):
            with patch("src.DHT.modules.commands.workspace_command.WorkspacesCommand") as mock_ws:
                mock_ws_instance = mock_ws.return_value
                mock_ws_instance.detect_workspace_members.return_value = [
                    tmp_path,
                    tmp_path / "packages" / "pkg1",
                    tmp_path / "packages" / "pkg2",
                ]
                # Get the underlying method if it's wrapped by Prefect
                execute_method = cmd.execute
                if hasattr(execute_method, "fn"):
                    execute_method = execute_method.fn
                result = execute_method(cmd, name="pkg1", subcommand="run", script="test")

        assert result["success"] is True
        assert "Command executed in pkg1" in result["message"]

        # Verify correct directory was used
        args = mock_run.call_args[0][0]
        assert "--directory" in args
        dir_idx = args.index("--directory")
        assert "pkg1" in args[dir_idx + 1]

    def test_workspace_member_not_found(self, tmp_path):
        """Test error when workspace member not found."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("""
[tool.uv.workspace]
members = ["packages/*"]
""")

        cmd = WorkspaceCommand()
        with patch.object(Path, "cwd", return_value=tmp_path):
            with patch("src.DHT.modules.commands.workspace_command.WorkspacesCommand") as mock_ws:
                mock_ws_instance = mock_ws.return_value
                mock_ws_instance.detect_workspace_members.return_value = [tmp_path]
                # Get the underlying method if it's wrapped by Prefect
                execute_method = cmd.execute
                if hasattr(execute_method, "fn"):
                    execute_method = execute_method.fn
                result = execute_method(cmd, name="nonexistent", subcommand="run", script="test")

        assert result["success"] is False
        assert "not found" in result["error"]

    @patch("subprocess.run")
    def test_workspace_upgrade_in_member(self, mock_run, tmp_path):
        """Test upgrading packages in specific member."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Upgraded"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("""
[tool.uv.workspace]
members = ["pkg1"]
""")
        (tmp_path / "pkg1").mkdir()
        (tmp_path / "pkg1" / "pyproject.toml").write_text("[project]\nname = 'pkg1'")

        cmd = WorkspaceCommand()
        with patch.object(Path, "cwd", return_value=tmp_path):
            with patch("src.DHT.modules.commands.workspace_command.WorkspacesCommand") as mock_ws:
                mock_ws_instance = mock_ws.return_value
                mock_ws_instance.detect_workspace_members.return_value = [tmp_path, tmp_path / "pkg1"]
                # Get the underlying method if it's wrapped by Prefect
                execute_method = cmd.execute
                if hasattr(execute_method, "fn"):
                    execute_method = execute_method.fn
                result = execute_method(cmd, name="pkg1", subcommand="upgrade", script="requests")

        assert result["success"] is True
        args = mock_run.call_args[0][0]
        assert args[0] == "uv"
        assert args[1] == "add"
        assert "--upgrade" in args
        assert "requests" in args

    @patch("subprocess.run")
    def test_workspace_remove_from_member(self, mock_run, tmp_path):
        """Test removing packages from specific member."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Removed"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("""
[tool.uv.workspace]
members = ["pkg1"]
""")
        (tmp_path / "pkg1").mkdir()
        (tmp_path / "pkg1" / "pyproject.toml").write_text("[project]\nname = 'pkg1'")

        cmd = WorkspaceCommand()
        with patch.object(Path, "cwd", return_value=tmp_path):
            with patch("src.DHT.modules.commands.workspace_command.WorkspacesCommand") as mock_ws:
                mock_ws_instance = mock_ws.return_value
                mock_ws_instance.detect_workspace_members.return_value = [tmp_path, tmp_path / "pkg1"]
                # Get the underlying method if it's wrapped by Prefect
                execute_method = cmd.execute
                if hasattr(execute_method, "fn"):
                    execute_method = execute_method.fn
                result = execute_method(cmd, name="pkg1", subcommand="remove", script="requests", args=["pytest"])

        assert result["success"] is True
        args = mock_run.call_args[0][0]
        assert args[0] == "uv"
        assert args[1] == "remove"
        assert "requests" in args
        assert "pytest" in args


class TestCommandDispatcherWorkspaces:
    """Test command dispatcher handling of workspace commands."""

    def test_parse_workspaces_args(self):
        """Test parsing workspaces command arguments."""
        from src.DHT.modules.command_dispatcher import CommandDispatcher

        dispatcher = CommandDispatcher()

        # Test run subcommand
        args = dispatcher._parse_command_args("workspaces", ["run", "test", "--only", "pkg*"])
        assert args["subcommand"] == "run"
        assert args["script"] == "test"
        assert args["only"] == ["pkg*"]

        # Test upgrade subcommand
        args = dispatcher._parse_command_args("ws", ["upgrade", "requests", "pytest"])
        assert args["subcommand"] == "upgrade"
        assert args["script"] == "requests"
        assert args["args"] == ["pytest"]

        # Test exec with filters
        args = dispatcher._parse_command_args(
            "workspaces", ["exec", "echo", "hello", "--ignore", "test*", "--only-fs", "*.py"]
        )
        assert args["subcommand"] == "exec"
        assert args["script"] == "echo"
        assert args["args"] == ["hello"]
        assert args["ignore"] == ["test*"]
        assert args["only_fs"] == ["*.py"]

    def test_parse_workspace_args(self):
        """Test parsing workspace command arguments."""
        from src.DHT.modules.command_dispatcher import CommandDispatcher

        dispatcher = CommandDispatcher()

        # Test single workspace run
        args = dispatcher._parse_command_args("workspace", ["my-pkg", "run", "test"])
        assert args["name"] == "my-pkg"
        assert args["subcommand"] == "run"
        assert args["script"] == "test"

        # Test upgrade with multiple packages
        args = dispatcher._parse_command_args("w", ["frontend", "upgrade", "react", "typescript"])
        assert args["name"] == "frontend"
        assert args["subcommand"] == "upgrade"
        assert args["script"] == "react"
        assert args["args"] == ["typescript"]
