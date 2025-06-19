#!/usr/bin/env python3

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Initial Python command dispatcher to replace shell orchestrator
# - Provides command registry and dispatch functionality
# - Will replace dhtl_execute_command from shell scripts
#

"""
DHT Command Dispatcher - Pure Python implementation.

This module replaces the shell-based command orchestration system.
It provides a registry for all DHT commands and dispatches them appropriately.
"""

import logging
from typing import Any

# Import the command registry
from .command_registry import CommandRegistry
from .dhtl_commands import DHTLCommands

logger = logging.getLogger(__name__)


class CommandDispatcher:
    """Central command dispatcher for DHT."""

    def __init__(self):
        """Initialize the command dispatcher."""
        # Use the command registry
        self.registry = CommandRegistry()

        # For backward compatibility
        self.commands = {}
        self.command_help = {}

        # Populate from registry
        for name, cmd in self.registry.commands.items():
            self.commands[name] = cmd["handler"]
            self.command_help[name] = cmd["help"]

    def dispatch(self, command: str, args: list[str]) -> int:
        """Dispatch a command with arguments."""
        if command not in self.commands:
            print(f"❌ Error: Unknown command: {command}")
            self.show_help()
            return 1

        try:
            handler = self.commands[command]

            # Debug logging
            logger.debug(f"Handler type for {command}: {type(handler)}")
            logger.debug(f"Has fn: {hasattr(handler, 'fn')}")

            # Check if this is a Prefect Task
            if hasattr(handler, 'fn'):
                # It's a Prefect Task - we need to check the wrapped function
                wrapped_fn = handler.fn
                # Check if the wrapped function is from DHTLCommands
                logger.debug(f"Wrapped function: {wrapped_fn}")
                logger.debug(f"Has __qualname__: {hasattr(wrapped_fn, '__qualname__')}")
                if hasattr(wrapped_fn, '__qualname__'):
                    logger.debug(f"__qualname__: {wrapped_fn.__qualname__}")

                if hasattr(wrapped_fn, '__qualname__') and 'DHTLCommands' in wrapped_fn.__qualname__:
                    # Parse arguments for DHTLCommands methods
                    logger.debug("Handling as DHTLCommands Prefect task")
                    parsed_args = self._parse_command_args(command, args)
                    result = handler(**parsed_args)

                    # Handle result
                    if isinstance(result, dict):
                        if result.get("success", False):
                            return 0
                        else:
                            error_msg = result.get("error", "Command failed")
                            print(f"❌ Error: {error_msg}")
                            return 1
                    else:
                        return 0 if result else 1
                else:
                    # Other Prefect tasks
                    result = handler(args) if args else handler()
                    return 0 if result else 1
            # Check if this is a method that needs parsed arguments
            elif hasattr(handler, '__self__'):
                # This is a bound method
                if isinstance(handler.__self__, DHTLCommands):
                    # Parse arguments for DHTLCommands methods
                    parsed_args = self._parse_command_args(command, args)
                    result = handler(**parsed_args)

                    # Handle result
                    if isinstance(result, dict):
                        if result.get("success", False):
                            return 0
                        else:
                            error_msg = result.get("error", "Command failed")
                            print(f"❌ Error: {error_msg}")
                            return 1
                    else:
                        return 0 if result else 1
                else:
                    # Other bound methods - call with args list
                    return handler(args) if args else handler()
            else:
                # Regular functions
                # Check if function expects no arguments
                import inspect
                sig = inspect.signature(handler)
                if not sig.parameters:
                    # Function takes no arguments
                    return handler()
                else:
                    # Function takes arguments
                    return handler(args) if args else handler()

        except KeyboardInterrupt:
            print("\n⚠️  Interrupted by user")
            return 130
        except Exception as e:
            logger.error(f"Command '{command}' failed: {e}", exc_info=True)
            print(f"❌ Error: {e}")
            return 1

    def _parse_command_args(self, command: str, args: list[str]) -> dict[str, Any]:
        """Parse command line arguments for a command."""
        import argparse

        # Command-specific argument parsers
        if command == "init":
            parser = argparse.ArgumentParser(prog=f"dhtl {command}")
            parser.add_argument("path", nargs="?", default=".", help="Project path")
            parser.add_argument("--name", help="Project name")
            parser.add_argument("--python", default="3.11", help="Python version")
            parser.add_argument("--package", action="store_true", help="Create package structure")
            parser.add_argument("--no-package", action="store_true", help="Skip package structure")
            parser.add_argument("--lib", action="store_true", help="Create library project")
            parser.add_argument("--app", action="store_true", help="Create application project")
            parser.add_argument("--ci", action="store_true", help="Add CI/CD workflows")
            parser.add_argument("--pre-commit", action="store_true", help="Add pre-commit hooks")

        elif command == "setup":
            parser = argparse.ArgumentParser(prog=f"dhtl {command}")
            parser.add_argument("path", nargs="?", default=".", help="Project path")
            parser.add_argument("--python", help="Python version")
            parser.add_argument("--dev", action="store_true", help="Install dev dependencies")
            parser.add_argument("--from-requirements", action="store_true", help="Import from requirements.txt")
            parser.add_argument("--all-packages", action="store_true", help="Install all workspace packages")
            parser.add_argument("--compile-bytecode", action="store_true", help="Compile Python files to bytecode")
            parser.add_argument("--editable", action="store_true", help="Install in editable mode")
            parser.add_argument("--index-url", help="Custom package index URL")
            parser.add_argument("--install-pre-commit", action="store_true", help="Install pre-commit hooks")

        elif command == "build":
            parser = argparse.ArgumentParser(prog=f"dhtl {command}")
            parser.add_argument("path", nargs="?", default=".", help="Project path")
            parser.add_argument("--wheel", action="store_true", help="Build wheel only")
            parser.add_argument("--sdist", action="store_true", help="Build source distribution only")
            parser.add_argument("--no-checks", action="store_true", help="Skip pre-build checks")
            parser.add_argument("--out-dir", help="Output directory")

        elif command == "sync":
            parser = argparse.ArgumentParser(prog=f"dhtl {command}")
            parser.add_argument("path", nargs="?", default=".", help="Project path")
            parser.add_argument("--locked", action="store_true", help="Use locked dependencies")
            parser.add_argument("--dev", action="store_true", help="Include dev dependencies")
            parser.add_argument("--no-dev", action="store_true", help="Exclude dev dependencies")
            parser.add_argument("--extras", nargs="*", help="Extra dependency groups")
            parser.add_argument("--upgrade", action="store_true", help="Upgrade dependencies")

        else:
            # Default parser
            parser = argparse.ArgumentParser(prog=f"dhtl {command}")
            parser.add_argument("args", nargs="*", help="Command arguments")

        # Parse arguments
        parsed = parser.parse_args(args)
        return vars(parsed)

    def show_help(self, args: list[str] = None) -> int:
        """Show help message."""
        print("Development Helper Toolkit (DHT)")
        print("================================")
        print("\nUsage: dhtl <command> [options]")
        print("\nAvailable commands:")

        # Group commands by category
        categories = {
            "Project Management": ["init", "setup", "clean"],
            "Development": ["build", "sync", "test", "lint", "format", "coverage"],
            "Version Control": ["commit", "tag", "bump", "clone", "fork"],
            "Deployment": ["publish", "workflows"],
            "Utilities": ["env", "diagnostics", "restore", "guardian"],
            "Help": ["help", "version"]
        }

        for category, cmds in categories.items():
            print(f"\n{category}:")
            for cmd in cmds:
                if cmd in self.command_help:
                    print(f"  {cmd:<15} {self.command_help[cmd]}")

        print("\nFor command-specific help: dhtl <command> --help")
        return 0

    def show_version(self, args: list[str] = None) -> int:
        """Show version information."""
        from .. import __version__
        print(f"Development Helper Toolkit (DHT) v{__version__}")
        print("Pure Python implementation")
        return 0
