#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Extracted DHTLauncher class from dhtl.py for modularity
# - Reduced size of main entry point file
# - Follows CLAUDE.md modularity guidelines
# 

"""
DHT Launcher Class.

Main launcher class that coordinates between shell modules and Python.
"""

import os
import sys
import platform
import subprocess
import time
import shutil
import tempfile
from pathlib import Path
from typing import Optional, List, Dict

try:
    from .colors import Colors
except ImportError:
    from colors import Colors


class DHTLauncher:
    """Main launcher class for DHT."""
    
    def __init__(self):
        """Initialize the DHT launcher."""
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
        self.node_mem_limit = 2048     # MB
        self.python_mem_limit = 2048   # MB
        self.timeout = 900             # 15 minutes
        
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
    
    def _find_project_root(self, start_dir: Optional[Path] = None) -> Path:
        """Find the project root directory."""
        if start_dir is None:
            start_dir = Path.cwd()
        
        current = start_dir.resolve()
        
        # Project markers to look for
        markers = [
            ".git", "package.json", "pyproject.toml", "setup.py",
            "Cargo.toml", "go.mod", "pom.xml", "build.gradle",
            "Gemfile", "composer.json", ".dhtconfig"
        ]
        
        # Traverse up looking for markers
        while current != current.parent:
            for marker in markers:
                if (current / marker).exists():
                    return current
            current = current.parent
        
        # If no project root found, use current directory
        return Path.cwd()
    
    def _setup_environment(self):
        """Set up environment variables for shell modules."""
        env = os.environ.copy()
        
        # Core paths
        env["DHTL_DIR"] = str(self.dhtl_dir)
        env["DHT_DIR"] = str(self.dht_dir)
        env["MODULES_DIR"] = str(self.modules_dir)
        env["CACHE_DIR"] = str(self.cache_dir)
        env["PROJECT_ROOT"] = str(self.project_root)
        env["DEFAULT_VENV_DIR"] = str(self.default_venv_dir)
        
        # Version and session
        env["DHTL_VERSION"] = self.version
        env["DHTL_SESSION_ID"] = self.session_id
        
        # Platform and Python
        env["PLATFORM"] = self.platform
        env["PYTHON_CMD"] = self.python_cmd
        
        # Resource limits
        env["DEFAULT_MEM_LIMIT"] = str(self.default_mem_limit)
        env["NODE_MEM_LIMIT"] = str(self.node_mem_limit)
        env["PYTHON_MEM_LIMIT"] = str(self.python_mem_limit)
        env["TIMEOUT"] = str(self.timeout)
        
        # Guardian and mode settings
        env["USE_GUARDIAN"] = "true" if self.use_guardian else "false"
        env["QUIET_MODE"] = "1" if self.quiet_mode else "0"
        env["DEBUG_MODE"] = "true" if self.debug_mode else "false"
        
        # Critical flags for modules
        env["DHTL_SKIP_ENV_SETUP"] = "1"
        env["SKIP_ENV_CHECK"] = "1"
        env["IN_DHTL"] = "1"
        
        # Disable guardian if requested
        if not self.use_guardian:
            env["DISABLE_GUARDIAN"] = "1"
        
        return env
    
    def display_banner(self):
        """Display the DHT banner."""
        if self.quiet_mode:
            return
        
        print(f"{Colors.CYAN}╔═════════════════════════════════════════════════════════╗{Colors.ENDC}")
        print(f"{Colors.CYAN}║           Development Helper Toolkit Launcher           ║{Colors.ENDC}")
        print(f"{Colors.CYAN}╚═════════════════════════════════════════════════════════╝{Colors.ENDC}")
        print()
    
    def display_help(self):
        """Display help message."""
        print(f"{Colors.CYAN}╔════════════════════════════════════════════════════════════════════════════╗{Colors.ENDC}")
        print(f"{Colors.CYAN}║              Development Helper Toolkit Launcher (DHTL) v{self.version}             ║{Colors.ENDC}")
        print(f"{Colors.CYAN}╚════════════════════════════════════════════════════════════════════════════╝{Colors.ENDC}")
        print(f"\nUsage: {Colors.BOLD}./dhtl.py [command] [options]{Colors.ENDC}  (or 'dhtl [command]' if installed via pip)")
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
    
    def check_shell_available(self) -> bool:
        """Check if bash is available for running shell scripts."""
        bash_path = shutil.which("bash")
        if not bash_path:
            print(f"{Colors.RED}❌ Error: bash not found!{Colors.ENDC}")
            print("\nDHT requires bash to run its shell modules.")
            
            if self.platform == "windows":
                print("\nOn Windows, you can install bash via:")
                print("  • Git for Windows: https://git-scm.com/download/win")
                print("  • WSL (Windows Subsystem for Linux)")
                print("  • MSYS2: https://www.msys2.org/")
            elif self.platform == "macos":
                print("\nBash should be available on macOS by default.")
                print("Please check your PATH environment variable.")
            else:
                print("\nPlease install bash using your system's package manager.")
            
            return False
        
        if self.debug_mode:
            print(f"Found bash at: {bash_path}")
        
        return True
    
    def execute_shell_command(self, script: str, args: List[str], env: Dict[str, str]) -> int:
        """Execute a shell script with arguments."""
        # Construct the command
        if self.platform == "windows" and not self.platform == "windows_unix":
            # Pure Windows - need to explicitly call bash
            cmd = ["bash", str(script)] + args
        else:
            # Unix-like systems
            cmd = [str(script)] + args
        
        if self.debug_mode:
            print(f"{Colors.YELLOW}🔄 Executing: {' '.join(cmd)}{Colors.ENDC}")
        
        try:
            # Run the command
            process = subprocess.Popen(
                cmd, env=env, stdout=None, stderr=None, cwd=str(self.project_root)
            )
            
            # Wait for completion
            return_code = process.wait()
            
            if self.debug_mode:
                print(f"Command exited with code: {return_code}")
            
            return return_code
            
        except FileNotFoundError:
            print(f"{Colors.RED}❌ Error: Script not found: {script}{Colors.ENDC}")
            return 1
        except PermissionError:
            print(f"{Colors.RED}❌ Error: Permission denied executing: {script}{Colors.ENDC}")
            print("Try: chmod +x " + str(script))
            return 1
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}Interrupted by user{Colors.ENDC}")
            return 130
        except Exception as e:
            print(f"{Colors.RED}❌ Error executing command: {e}{Colors.ENDC}")
            return 1
    
    def run_command(self, command: str, args: List[str]) -> int:
        """Run a DHT command."""
        # Set up environment
        env = self._setup_environment()
        
        # Special handling for built-in commands
        if command in ["help", "--help", "-h"]:
            self.display_help()
            return 0
        
        if command in ["version", "--version", "-v"]:
            print(f"Development Helper Toolkit Launcher (DHTL) v{self.version}")
            return 0
        
        # For all other commands, delegate to shell orchestrator
        wrapper_content = f"""#!/bin/bash
set -e

# Export environment variables
{chr(10).join(f'export {k}="{v}"' for k, v in env.items())}

# Source the orchestrator
source "{self.modules_dir}/orchestrator.sh"

# Check if function exists
declare -f -F dhtl_execute_command > /dev/null
if [ $? -eq 0 ]; then
    # Execute the command
    dhtl_execute_command "{command}" {' '.join(f'"{arg}"' for arg in args)}
else
    echo "❌ Error: Command dispatcher not available"
    exit 1
fi
"""
        
        # Write wrapper to a temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
            f.write(wrapper_content)
            wrapper_path = f.name
        
        try:
            # Make wrapper executable
            os.chmod(wrapper_path, 0o755)
            
            # Execute the wrapper
            return self.execute_shell_command(wrapper_path, [], env)
            
        finally:
            # Clean up
            try:
                os.unlink(wrapper_path)
            except:
                pass