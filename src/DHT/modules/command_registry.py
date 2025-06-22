#!/usr/bin/env python3
"""
DHT Command Registry.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Central registry for all DHT commands
# - Maps command names to their implementations
# - Replaces shell-based command dispatch
#

"""
DHT Command Registry.

Central registry that maps all DHT commands to their Python implementations.
"""

from collections.abc import Callable
from typing import Any


class CommandRegistry:
    """Registry for all DHT commands."""

    def __init__(self):
        """Initialize the command registry."""
        self.commands: dict[str, dict[str, Any]] = {}
        self._register_all_commands()

    def _register_all_commands(self):
        """Register all available commands."""
        # Import all command implementations
        # Import new modular commands
        from .commands import (
            add_command,
            bin_command,
            check_command,
            doc_command,
            fmt_command,
            install_command,
            project_command,
            remove_command,
            upgrade_command,
            workspace_command,
            workspaces_command,
        )
        from .dhtl_commands import DHTLCommands
        from .dhtl_utils import lint_command
        from .utils import format_command

        # Create command instance
        dhtl_cmds = DHTLCommands()

        # Core commands
        self.register("init", dhtl_cmds.init, "Initialize a new Python project")
        self.register("setup", dhtl_cmds.setup, "Setup project environment")
        self.register("build", dhtl_cmds.build, "Build Python package")
        self.register("sync", dhtl_cmds.sync, "Sync project dependencies")

        # New modular commands and aliases
        self.register("install", install_command, "Install project dependencies (alias for setup)")
        self.register("add", add_command, "Add dependencies to the project")
        self.register("remove", remove_command, "Remove dependencies from the project")
        self.register("upgrade", upgrade_command, "Upgrade dependencies")
        self.register("fmt", fmt_command, "Format code (alias for format)")
        self.register("check", check_command, "Type check Python code")
        self.register("doc", doc_command, "Generate project documentation")
        self.register("bin", bin_command, "Print executable files installation folder")

        # Workspace commands
        self.register("workspaces", workspaces_command, "Run commands across workspace members")
        self.register("ws", workspaces_command, "Run commands across workspace members (alias)")
        self.register("workspace", workspace_command, "Run command in specific workspace member")
        self.register("w", workspace_command, "Run command in specific workspace member (alias)")
        self.register("project", project_command, "Run command in root project only")
        self.register("p", project_command, "Run command in root project only (alias)")

        # Linting and formatting
        self.register("lint", lint_command, "Lint code")
        self.register("format", format_command, "Format code")

        # Test commands (from dhtl_commands_2.py)
        self.register("test", self._test_command, "Run project tests")

        # Coverage commands (from dhtl_commands_5.py)
        self.register("coverage", self._coverage_command, "Run code coverage")

        # Commit commands (from dhtl_commands_6.py)
        self.register("commit", self._commit_command, "Create git commit")

        # Build/publish commands (from dhtl_commands_7.py)
        self.register("publish", self._publish_command, "Publish package")

        # Container deployment commands
        self.register(
            "deploy_project_in_container", dhtl_cmds.deploy_project_in_container, "Deploy project in Docker container"
        )

        # Clean commands (from dhtl_commands_8.py)
        self.register("clean", self._clean_command, "Clean project")

        # Environment commands
        self.register("env", self._env_command, "Show environment")

        # Diagnostics
        self.register("diagnostics", self._diagnostics_command, "Run diagnostics")

        # Restore commands (from dhtl_commands_1.py)
        self.register("restore", self._restore_command, "Restore dependencies")

        # Version commands
        self.register("tag", self._tag_command, "Create git tag")
        self.register("bump", self._bump_command, "Bump version")

        # GitHub commands
        self.register("clone", self._clone_command, "Clone repository")
        self.register("fork", self._fork_command, "Fork repository")

        # Guardian commands
        self.register("guardian", self._guardian_command, "Manage process guardian")

        # Workflow commands
        self.register("workflows", self._workflows_command, "Manage workflows")
        self.register("act", self._act_command, "Run GitHub Actions locally")

        # Standalone commands
        self.register("node", self._node_command, "Run node command")
        self.register("python", self._python_command, "Run python command")
        self.register("run", self._run_command, "Run command")
        self.register("script", self._script_command, "Run script")

        # Test commands
        self.register("test_dht", self._test_dht_command, "Test DHT itself")
        self.register("verify_dht", self._verify_dht_command, "Verify DHT")

        # Built-in commands
        self.register("help", self._help_command, "Show help")
        self.register("version", self._version_command, "Show version")

    def register(self, name: str, handler: Callable, help_text: str = ""):
        """Register a command."""
        self.commands[name] = {"handler": handler, "help": help_text}

    def get_command(self, name: str) -> dict[str, Any] | None:
        """Get a command by name."""
        return self.commands.get(name)

    def list_commands(self) -> dict[str, str]:
        """List all available commands with their help text."""
        return {name: cmd["help"] for name, cmd in self.commands.items()}

    # Placeholder implementations for commands
    # These will be replaced with actual implementations from the converted modules

    def _test_command(self, *args, **kwargs) -> int:
        """Run tests."""
        from .dhtl_commands_2 import test_command

        return test_command(*args, **kwargs)

    def _coverage_command(self, *args, **kwargs) -> int:
        """Run coverage."""
        from .dhtl_commands_5 import coverage_command

        return coverage_command(*args, **kwargs)

    def _commit_command(self, *args, **kwargs) -> int:
        """Create commit."""
        from .dhtl_commands_6 import commit_command

        return commit_command(*args, **kwargs)

    def _publish_command(self, *args, **kwargs) -> int:
        """Publish package."""
        from .dhtl_commands_7 import publish_command

        return publish_command(*args, **kwargs)

    def _clean_command(self, *args, **kwargs) -> int:
        """Clean project."""
        from .dhtl_commands_8 import clean_command

        return clean_command(*args, **kwargs)

    def _env_command(self, *args, **kwargs) -> int:
        """Show environment."""
        from .dhtl_environment_2 import env_command

        return env_command(*args, **kwargs)

    def _diagnostics_command(self, *args, **kwargs) -> int:
        """Run diagnostics."""
        from .dhtl_diagnostics import diagnostics_command

        return diagnostics_command(*args, **kwargs)

    def _restore_command(self, *args, **kwargs) -> int:
        """Restore dependencies."""
        from .dhtl_commands_1 import restore_command

        return restore_command(*args, **kwargs)

    def _tag_command(self, *args, **kwargs) -> int:
        """Create tag."""
        from .dhtl_version import tag_command

        return tag_command(*args, **kwargs)

    def _bump_command(self, *args, **kwargs) -> int:
        """Bump version."""
        from .dhtl_version import bump_command

        return bump_command(*args, **kwargs)

    def _clone_command(self, *args, **kwargs) -> int:
        """Clone repository."""
        from .dhtl_github import clone_command

        return clone_command(*args, **kwargs)

    def _fork_command(self, *args, **kwargs) -> int:
        """Fork repository."""
        from .dhtl_github import fork_command

        return fork_command(*args, **kwargs)

    def _guardian_command(self, *args, **kwargs) -> int:
        """Manage guardian."""
        from .dhtl_guardian_command import guardian_command

        return guardian_command(*args, **kwargs)

    def _workflows_command(self, *args, **kwargs) -> int:
        """Manage workflows."""
        from .dhtl_commands_workflows import workflows_command

        return workflows_command(*args, **kwargs)

    def _act_command(self, *args, **kwargs) -> int:
        """Run GitHub Actions locally."""
        from .dhtl_commands_act import act_command

        return act_command(*args, **kwargs)

    def _node_command(self, args=None, **kwargs) -> int:
        """Run node."""
        from .dhtl_commands_standalone import node_command

        return node_command(args, **kwargs)

    def _python_command(self, args=None, **kwargs) -> int:
        """Run python."""
        from .dhtl_commands_standalone import python_command

        return python_command(args, **kwargs)

    def _run_command(self, args=None, **kwargs) -> int:
        """Run command."""
        from .dhtl_commands_standalone import run_command

        return run_command(args, **kwargs)

    def _script_command(self, args=None, **kwargs) -> int:
        """Run script."""
        from .dhtl_commands_standalone import script_command

        return script_command(args, **kwargs)

    def _test_dht_command(self, *args, **kwargs) -> int:
        """Test DHT."""
        from .dhtl_test import test_dht_command

        return test_dht_command(*args, **kwargs)

    def _verify_dht_command(self, *args, **kwargs) -> int:
        """Verify DHT."""
        from .dhtl_test import verify_dht_command

        return verify_dht_command(*args, **kwargs)

    def _help_command(self, *args, **kwargs) -> int:
        """Show help."""
        print("Development Helper Toolkit (DHT)")
        print("================================")
        print("\nUsage: dhtl <command> [options]")
        print("\nAvailable commands:")

        # Group commands by category
        categories = {
            "Project Management": ["init", "setup", "clean"],
            "Development": ["build", "sync", "test", "lint", "format", "coverage"],
            "Version Control": ["commit", "tag", "bump", "clone", "fork"],
            "Deployment": ["publish", "deploy_project_in_container", "workflows"],
            "Utilities": ["env", "diagnostics", "restore", "guardian"],
            "Help": ["help", "version"],
        }

        for category, cmds in categories.items():
            print(f"\n{category}:")
            for cmd in cmds:
                if cmd in self.commands:
                    print(f"  {cmd:<15} {self.commands[cmd]['help']}")

        print("\nFor command-specific help: dhtl <command> --help")
        return 0

    def _version_command(self, *args, **kwargs) -> int:
        """Show version."""
        print("Development Helper Toolkit (DHT) v1.0.0")
        print("Pure Python implementation")
        return 0
