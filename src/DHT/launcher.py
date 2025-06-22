#!/usr/bin/env python3
"""
DHT Launcher Class.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Extracted DHTLauncher class from dhtl.py for modularity
# - Reduced size of main entry point file
# - Follows CLAUDE.md modularity guidelines
#

"""
DHT Launcher Class.

Main launcher class that coordinates between shell modules and Python.
"""

import logging
import os
import platform
import shutil
import time
from pathlib import Path

try:
    from .colors import Colors
except ImportError:
    from colors import Colors


class DHTLauncher:
    """Main launcher class for DHT."""

    def __init__(self) -> None:
        """Initialize the DHT launcher."""
        # Set up logging
        self.logger = logging.getLogger(__name__)

        # Basic configuration
        self.version = "1.0.0"
        self.session_id = f"{int(time.time())}_{os.getpid()}"

        # Detect environment - we're now inside the DHT package
        self.dht_dir = Path(__file__).parent.resolve()  # DHT package directory
        self.dhtl_dir = self.dht_dir.parent.parent  # Go up to project root
        self.modules_dir = self.dht_dir / "modules"
        self.cache_dir = self.dht_dir / ".dht_cache"

        # Platform detection
        self.platform = self._detect_platform()
        self.python_cmd = self._detect_python()

        # Project detection
        self.project_root = self._find_project_root()
        self.default_venv_dir = self.project_root / ".venv"

        # Resource limits
        self.default_mem_limit = 2048  # MB
        self.node_mem_limit = 2048  # MB
        self.python_mem_limit = 2048  # MB
        self.timeout = 900  # 15 minutes

        # Command options
        self.use_guardian = True
        self.quiet_mode = False
        self.debug_mode = False

        # Color support detection
        if not Colors.supports_color():
            Colors.disable()

    def _detect_platform(self) -> str:
        """Detect the current platform."""
        system = platform.system().lower()
        if system == "darwin":
            return "macos"
        elif system == "linux":
            return "linux"
        elif system == "windows":
            # Check if running in Git Bash/MSYS/Cygwin
            if os.environ.get("MSYSTEM") or shutil.which("bash"):
                return "windows_unix"
            return "windows"
        elif "bsd" in system:
            return "bsd"
        else:
            return "unknown"

    def _detect_python(self) -> str:
        """Detect the Python command to use."""
        # Try python3 first, then python
        for cmd in ["python3", "python"]:
            if shutil.which(cmd):
                return cmd
        return "python3"  # Fallback

    def _find_project_root(self, start_dir: Path | None = None) -> Path:
        """Find the project root directory."""
        if start_dir is None:
            start_dir = Path.cwd()

        current = start_dir.resolve()

        # Project markers to look for
        markers = [
            ".git",
            "package.json",
            "pyproject.toml",
            "setup.py",
            "Cargo.toml",
            "go.mod",
            "pom.xml",
            "build.gradle",
            "Gemfile",
            "composer.json",
            ".dhtconfig",
        ]

        # Traverse up looking for markers
        while current != current.parent:
            for marker in markers:
                if (current / marker).exists():
                    return current
            current = current.parent

        # If no project root found, use current directory
        return Path.cwd()

    def setup_python_environment(self) -> None:
        """Set up environment variables for Python modules."""
        # Set environment variables that Python modules might need
        os.environ["PROJECT_ROOT"] = str(self.project_root)
        os.environ["DEFAULT_VENV_DIR"] = str(self.default_venv_dir)
        os.environ["PLATFORM"] = self.platform
        os.environ["PYTHON_CMD"] = self.python_cmd
        os.environ["DEFAULT_MEM_LIMIT"] = str(self.default_mem_limit)
        os.environ["PYTHON_MEM_LIMIT"] = str(self.python_mem_limit)
        os.environ["QUIET_MODE"] = "1" if self.quiet_mode else "0"
        os.environ["DEBUG_MODE"] = "true" if self.debug_mode else "false"

    def display_banner(self) -> None:
        """Display the DHT banner."""
        if self.quiet_mode:
            return

        print(f"{Colors.CYAN}╔═════════════════════════════════════════════════════════╗{Colors.ENDC}")
        print(f"{Colors.CYAN}║           Development Helper Toolkit Launcher           ║{Colors.ENDC}")
        print(f"{Colors.CYAN}╚═════════════════════════════════════════════════════════╝{Colors.ENDC}")
        print()

    def display_help(self) -> None:
        """Display help message."""
        print(
            f"{Colors.CYAN}╔════════════════════════════════════════════════════════════════════════════╗{Colors.ENDC}"
        )
        print(
            f"{Colors.CYAN}║              Development Helper Toolkit Launcher (DHTL) v{self.version}             ║{Colors.ENDC}"
        )
        print(
            f"{Colors.CYAN}╚════════════════════════════════════════════════════════════════════════════╝{Colors.ENDC}"
        )
        print(
            f"\nUsage: {Colors.BOLD}./dhtl.py [command] [options]{Colors.ENDC}  (or 'dhtl [command]' if installed via pip)"
        )
        print("\nThis is the main orchestrator for the DHT toolkit.\n")
        print(f"{Colors.BOLD}Available commands:{Colors.ENDC}")
        print("  help, --help     Show this help message")
        print("  version          Show version information")
        print("  setup            Set up/update DHT for the current project")
        print("  init             Initialize DHT in a new project")
        print("  env              Display environment information")
        print("  diagnostics      Run diagnostics and generate a report")
        print("  lint             Run code linters")
        print("  format           Format source code")
        print("  test             Run project tests")
        print("  test_dht         Run DHT toolkit's own tests")
        print("  build            Build the project")
        print("  clean            Clean DHT caches and temporary files")
        print("  restore          Restore project dependencies")
        print("  workflows        Manage GitHub Actions workflows")
        print("  guardian         Manage the process guardian")
        print("  clone <url>      Clone a repository (uses GitHub CLI for GitHub repos)")
        print("  fork <url>       Fork a GitHub repository")
        print("  bump <type>      Bump version (patch/minor/major)")
        print("  tag <name>       Create a git tag")
        print("\n...and more. Use 'dhtl help' after setup for the full list.")
        print(f"\n{Colors.BOLD}Global Options:{Colors.ENDC}")
        print("  --no-guardian    Disable process guardian for this command")
        print("  --quiet          Reduce output verbosity")
        print("  --debug          Enable debug mode")
        print()

    def run_command(self, command: str, args: list[str]) -> int:
        """Run a DHT command."""
        # Set up Python environment
        self.setup_python_environment()

        # Try Python command dispatcher
        try:
            from .modules.command_dispatcher import CommandDispatcher
        except ImportError:
            # Try absolute import when running as script
            try:
                from modules.command_dispatcher import CommandDispatcher
            except ImportError as e:
                # Fallback if command dispatcher not available
                self.logger.warning(f"Command dispatcher not available: {e}")
                print("❌ Error: Command system not available")
                return 1

        dispatcher = CommandDispatcher()
        # Let dispatcher handle all commands including help/version
        return dispatcher.dispatch(command, args)
