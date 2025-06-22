#!/usr/bin/env python3
"""
Comprehensive tests for workspace functionality.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Create comprehensive tests for workspace functionality
# - Verify all commands work correctly with WorkspaceBase
#

"""Comprehensive tests for workspace functionality."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from src.DHT.modules.commands.project_command import ProjectCommand
from src.DHT.modules.commands.workspace_command import WorkspaceCommand
from src.DHT.modules.commands.workspaces_command import WorkspacesCommand


class TestWorkspaceRefactoring:
    """Test refactored workspace functionality."""

    def test_timeout_is_30_minutes(self):
        """Verify timeout is set to 30 minutes as per CLAUDE.md."""
        from src.DHT.modules.commands.workspace_base import WorkspaceBase

        assert WorkspaceBase.DEFAULT_TIMEOUT == 1800  # 30 minutes

    def test_no_shell_injection(self):
        """Verify shell=False is used for security."""
        from src.DHT.modules.commands.workspace_base import WorkspaceBase

        base = WorkspaceBase()

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

            # Test execute_shell_in_directory
            base.execute_shell_in_directory(Path("/tmp"), ["echo", "test"])

            # Verify shell=False was used
            mock_run.assert_called_once()
            call_kwargs = mock_run.call_args[1]
            assert call_kwargs["shell"] is False

    def test_progress_indicators(self):
        """Verify progress indicators are shown."""
        from src.DHT.modules.commands.workspace_base import WorkspaceBase

        base = WorkspaceBase()
        members = [Path("/tmp/pkg1"), Path("/tmp/pkg2")]

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

            with patch.object(base.logger, "info") as mock_log:
                base.execute_in_members(members, "Testing", lambda p: ["echo", "test"])

                # Verify progress logs
                progress_logs = [
                    call for call in mock_log.call_args_list if "[1/2]" in str(call) or "[2/2]" in str(call)
                ]
                assert len(progress_logs) >= 2

    def test_package_validation(self):
        """Test package name validation."""
        from src.DHT.modules.commands.workspace_base import WorkspaceBase

        base = WorkspaceBase()

        # Valid packages
        is_valid, errors = base.validate_package_names(["requests", "pytest", "numpy"])
        assert is_valid is True
        assert errors == []

        # Invalid packages
        is_valid, errors = base.validate_package_names(
            [
                "",  # Empty
                "../malicious",  # Path traversal
                "-flag",  # Starts with dash
                "pkg/with/slash",  # Contains slash
            ]
        )
        assert is_valid is False
        assert len(errors) == 4

    def test_workspace_filtering(self):
        """Test workspace member filtering."""
        from src.DHT.modules.commands.workspace_base import WorkspaceBase

        base = WorkspaceBase()
        members = [
            Path("/workspace/frontend"),
            Path("/workspace/backend"),
            Path("/workspace/shared"),
            Path("/workspace/tests"),
        ]

        # Test name filtering with only
        filtered = base.filter_members_by_patterns(members, only=["*end"])
        assert len(filtered) == 2
        assert any("frontend" in str(m) for m in filtered)
        assert any("backend" in str(m) for m in filtered)

        # Test name filtering with ignore
        filtered = base.filter_members_by_patterns(members, ignore=["test*"])
        assert len(filtered) == 3
        assert not any("tests" in str(m) for m in filtered)

    def test_all_commands_use_workspace_base(self):
        """Verify all workspace commands inherit from WorkspaceBase."""
        from src.DHT.modules.commands.workspace_base import WorkspaceBase

        # Check inheritance
        assert issubclass(WorkspacesCommand, WorkspaceBase)
        assert issubclass(WorkspaceCommand, WorkspaceBase)
        assert issubclass(ProjectCommand, WorkspaceBase)

        # Check they have the base functionality
        for cmd_class in [WorkspacesCommand, WorkspaceCommand, ProjectCommand]:
            cmd = cmd_class()
            assert hasattr(cmd, "DEFAULT_TIMEOUT")
            assert hasattr(cmd, "find_workspace_root")
            assert hasattr(cmd, "execute_in_members")
            assert hasattr(cmd, "validate_package_names")


class TestWorkspaceCommandMessages:
    """Test that command messages are consistent."""

    @patch("subprocess.run")
    def test_consistent_success_messages(self, mock_run, tmp_path):
        """Verify success messages follow a consistent pattern."""
        mock_run.return_value = MagicMock(returncode=0, stdout="OK", stderr="")

        # Create workspace
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("""
[tool.uv.workspace]
members = ["pkg1"]
""")
        (tmp_path / "pkg1").mkdir()
        (tmp_path / "pkg1" / "pyproject.toml").write_text("[project]\nname = 'pkg1'")

        # Test workspaces command
        ws_cmd = WorkspacesCommand()
        with patch.object(Path, "cwd", return_value=tmp_path):
            result = ws_cmd.execute.fn(ws_cmd, subcommand="run", script="test")
            assert "completed:" in result["message"]
            assert "succeeded" in result["message"]
