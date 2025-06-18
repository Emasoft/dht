#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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

import sys
import logging
from typing import Dict, Callable, List, Optional, Any
from pathlib import Path

# Import command modules as we convert them
from .dhtl_commands import DHTLCommands
# from .dhtl_lint_commands import DHTLLintCommands  # To be created
# from .dhtl_test_commands import DHTLTestCommands  # To be created
# etc...

logger = logging.getLogger(__name__)


class CommandDispatcher:
    """Central command dispatcher for DHT."""
    
    def __init__(self):
        """Initialize the command dispatcher."""
        self.commands: Dict[str, Callable] = {}
        self.command_help: Dict[str, str] = {}
        
        # Initialize command modules
        self.dhtl_commands = DHTLCommands()
        
        # Register all commands
        self._register_commands()
    
    def _register_commands(self):
        """Register all available commands."""
        # Python-implemented commands from dhtl_commands.py
        self.register_command("init", self.dhtl_commands.init, 
                            "Initialize a new Python project")
        self.register_command("setup", self.dhtl_commands.setup,
                            "Setup project environment")
        self.register_command("build", self.dhtl_commands.build,
                            "Build Python package")
        self.register_command("sync", self.dhtl_commands.sync,
                            "Sync project dependencies")
        
        # Commands to be migrated from shell
        # self.register_command("lint", self.lint_command, "Lint code")
        # self.register_command("format", self.format_command, "Format code")
        # self.register_command("test", self.test_command, "Run tests")
        # self.register_command("coverage", self.coverage_command, "Run coverage")
        # self.register_command("commit", self.commit_command, "Create git commit")
        # self.register_command("publish", self.publish_command, "Publish package")
        # self.register_command("clean", self.clean_command, "Clean project")
        # self.register_command("env", self.env_command, "Show environment")
        # self.register_command("diagnostics", self.diagnostics_command, "Run diagnostics")
        # self.register_command("restore", self.restore_command, "Restore dependencies")
        # self.register_command("tag", self.tag_command, "Create git tag")
        # self.register_command("bump", self.bump_command, "Bump version")
        # self.register_command("clone", self.clone_command, "Clone repository")
        # self.register_command("fork", self.fork_command, "Fork repository")
        # self.register_command("guardian", self.guardian_command, "Manage process guardian")
        # self.register_command("workflows", self.workflows_command, "Manage workflows")
        # self.register_command("act", self.act_command, "Run GitHub Actions locally")
        # self.register_command("node", self.node_command, "Run node command")
        # self.register_command("python", self.python_command, "Run python command")
        # self.register_command("run", self.run_command, "Run command")
        # self.register_command("script", self.script_command, "Run script")
        # self.register_command("test_dht", self.test_dht_command, "Test DHT itself")
        # self.register_command("verify_dht", self.verify_dht_command, "Verify DHT")
        
        # Built-in commands
        self.register_command("help", self.show_help, "Show help")
        self.register_command("version", self.show_version, "Show version")
    
    def register_command(self, name: str, handler: Callable, help_text: str = ""):
        """Register a command with its handler."""
        self.commands[name] = handler
        self.command_help[name] = help_text
    
    def dispatch(self, command: str, args: List[str]) -> int:
        """Dispatch a command with arguments."""
        if command not in self.commands:
            print(f"❌ Error: Unknown command: {command}")
            self.show_help()
            return 1
        
        try:
            handler = self.commands[command]
            
            # For DHTLCommands methods, we need to parse args
            if hasattr(handler, '__self__') and isinstance(handler.__self__, DHTLCommands):
                # Parse arguments based on command
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
                # For other commands, pass args directly
                return handler(args)
                
        except KeyboardInterrupt:
            print("\n⚠️  Interrupted by user")
            return 130
        except Exception as e:
            logger.error(f"Command '{command}' failed: {e}", exc_info=True)
            print(f"❌ Error: {e}")
            return 1
    
    def _parse_command_args(self, command: str, args: List[str]) -> Dict[str, Any]:
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
            parser.add_argument("--no-dev", action="store_true", help="Skip dev dependencies")
            parser.add_argument("--editable", action="store_true", help="Install in editable mode")
            parser.add_argument("--upgrade", action="store_true", help="Upgrade dependencies")
            parser.add_argument("--force", action="store_true", help="Force reinstall")
            
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
    
    def show_help(self, args: List[str] = None) -> int:
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
    
    def show_version(self, args: List[str] = None) -> int:
        """Show version information."""
        from .. import __version__
        print(f"Development Helper Toolkit (DHT) v{__version__}")
        print("Pure Python implementation")
        return 0