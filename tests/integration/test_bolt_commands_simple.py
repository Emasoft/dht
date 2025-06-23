#!/usr/bin/env python3
from __future__ import annotations

from typing import Any

"""
Simple integration tests for Bolt commands existence.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Create simple tests to verify Bolt commands are registered
# - Focus on command existence rather than full functionality
#

"""Simple integration tests for Bolt commands."""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from DHT.modules.command_registry import CommandRegistry


class TestBoltCommandsExist:
    """Test that all Bolt-compatible commands are registered."""

    def setup_method(self) -> Any:
        """Set up test fixtures."""
        self.registry = CommandRegistry()

    def test_core_bolt_commands_registered(self) -> Any:
        """Test that core Bolt commands are registered."""
        expected_commands = [
            "add",  # Add dependencies
            "remove",  # Remove dependencies
            "upgrade",  # Upgrade dependencies
            "install",  # Alias for setup
            "fmt",  # Alias for format
            "check",  # Type checking
            "doc",  # Documentation generation
            "bin",  # Show bin directory
        ]

        for cmd in expected_commands:
            assert cmd in self.registry.commands, f"Command '{cmd}' not registered"

    def test_workspace_commands_registered(self) -> Any:
        """Test that workspace commands are registered."""
        workspace_commands = [
            "workspaces",  # Run in all workspaces
            "ws",  # Short alias for workspaces
            "workspace",  # Run in specific workspace
            "w",  # Short alias for workspace
            "project",  # Run in root only
            "p",  # Short alias for project
        ]

        for cmd in workspace_commands:
            assert cmd in self.registry.commands, f"Command '{cmd}' not registered"

    def test_command_help_strings(self) -> Any:
        """Test that commands have appropriate help strings."""
        # Check specific help strings
        assert self.registry.commands["add"]["help"] == "Add dependencies to the project"
        assert self.registry.commands["remove"]["help"] == "Remove dependencies from the project"
        assert self.registry.commands["upgrade"]["help"] == "Upgrade dependencies"
        assert self.registry.commands["check"]["help"] == "Type check Python code"
        assert self.registry.commands["doc"]["help"] == "Generate project documentation"
        assert self.registry.commands["bin"]["help"] == "Print executable files installation folder"

    def test_aliases_point_to_correct_commands(self) -> Any:
        """Test that command aliases work correctly."""
        # fmt should be alias for format
        assert "format" in self.registry.commands["fmt"]["help"].lower()

        # install should be alias for setup
        assert "setup" in self.registry.commands["install"]["help"].lower()

        # ws should be alias for workspaces
        assert "alias" in self.registry.commands["ws"]["help"].lower()

        # w should be alias for workspace
        assert "alias" in self.registry.commands["w"]["help"].lower()

        # p should be alias for project
        assert "alias" in self.registry.commands["p"]["help"].lower()


class TestBoltCommandHandlers:
    """Test that Bolt commands have proper handlers."""

    def setup_method(self) -> Any:
        """Set up test fixtures."""
        self.registry = CommandRegistry()

    def test_add_command_handler(self) -> Any:
        """Test add command has proper handler."""
        assert "handler" in self.registry.commands["add"]
        handler = self.registry.commands["add"]["handler"]
        assert callable(handler)

    def test_remove_command_handler(self) -> Any:
        """Test remove command has proper handler."""
        assert "handler" in self.registry.commands["remove"]
        handler = self.registry.commands["remove"]["handler"]
        assert callable(handler)

    def test_upgrade_command_handler(self) -> Any:
        """Test upgrade command has proper handler."""
        assert "handler" in self.registry.commands["upgrade"]
        handler = self.registry.commands["upgrade"]["handler"]
        assert callable(handler)

    def test_check_command_handler(self) -> Any:
        """Test check command has proper handler."""
        assert "handler" in self.registry.commands["check"]
        handler = self.registry.commands["check"]["handler"]
        assert callable(handler)

    def test_bin_command_handler(self) -> Any:
        """Test bin command has proper handler."""
        assert "handler" in self.registry.commands["bin"]
        handler = self.registry.commands["bin"]["handler"]
        assert callable(handler)

    def test_workspace_command_handlers(self) -> Any:
        """Test workspace commands have proper handlers."""
        workspace_cmds = ["workspaces", "workspace", "project"]

        for cmd in workspace_cmds:
            assert "handler" in self.registry.commands[cmd]
            handler = self.registry.commands[cmd]["handler"]
            assert callable(handler)
