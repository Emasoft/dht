#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Python replacement for dhtl_error_handling.sh
# - Provides comprehensive error handling for DHT
# - Maintains all functionality from shell version
# - Adds Python-specific enhancements like proper exceptions
# 

"""
DHT Error Handling Module.

This module provides functions for improved error handling across all DHT modules.
Converted from shell to Python for the pure Python DHT implementation.
"""

import os
import sys
import logging
import subprocess
import tempfile
import atexit
import signal
import time
import traceback
from pathlib import Path
from typing import Optional, List, Dict, Any, Callable
from datetime import datetime
from enum import IntEnum


# Error types as an enum
class ErrorCode(IntEnum):
    """Standard error codes for DHT."""
    GENERAL = 1
    COMMAND_NOT_FOUND = 2
    MISSING_DEPENDENCY = 3
    INVALID_ARGUMENT = 4
    PERMISSION_DENIED = 5
    FILE_NOT_FOUND = 6
    NETWORK = 7
    TIMEOUT = 8
    RESOURCE_LIMIT = 9
    ENVIRONMENT = 10
    UNEXPECTED = 99


# Color codes for terminal output
class Colors:
    """ANSI color codes for terminal output."""
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    CYAN = '\033[36m'
    RESET = '\033[0m'
    
    @classmethod
    def disable(cls):
        """Disable colors for non-terminal output."""
        cls.RED = ''
        cls.GREEN = ''
        cls.YELLOW = ''
        cls.BLUE = ''
        cls.CYAN = ''
        cls.RESET = ''


# Check if output supports colors
if not sys.stdout.isatty():
    Colors.disable()


class DHTErrorHandler:
    """Main error handler class for DHT."""
    
    def __init__(self):
        """Initialize the error handler."""
        self.temp_files: List[str] = []
        self.temp_dirs: List[str] = []
        self.log_file = os.environ.get('DHT_LOG_FILE')
        self.quiet_mode = os.environ.get('QUIET_MODE', 'false').lower() == 'true'
        self.debug_mode = os.environ.get('DEBUG_MODE', 'false').lower() == 'true'
        
        # Set up cleanup handlers
        atexit.register(self._cleanup)
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # Set up file logging if enabled
        if self.log_file:
            log_dir = Path(self.log_file).parent
            log_dir.mkdir(parents=True, exist_ok=True)
    
    def log_error(self, message: str, code: ErrorCode = ErrorCode.GENERAL, 
                  stack_trace: bool = False) -> int:
        """Log an error message."""
        # Print to stderr with color
        print(f"{Colors.RED}❌ ERROR: {message}{Colors.RESET}", file=sys.stderr)
        
        # Show stack trace if requested
        if stack_trace:
            print("Stack trace:", file=sys.stderr)
            traceback.print_stack(file=sys.stderr)
        
        # Log to file if enabled
        if self.log_file:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            with open(self.log_file, 'a') as f:
                f.write(f"[{timestamp}] [ERROR] [{code}] {message}\n")
                if stack_trace:
                    f.write("Stack trace:\n")
                    traceback.print_stack(file=f)
        
        return code
    
    def log_warning(self, message: str) -> int:
        """Log a warning message."""
        # Print to stderr with color
        print(f"{Colors.YELLOW}⚠️  WARNING: {message}{Colors.RESET}", file=sys.stderr)
        
        # Log to file if enabled
        if self.log_file:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            with open(self.log_file, 'a') as f:
                f.write(f"[{timestamp}] [WARNING] {message}\n")
        
        return 0
    
    def log_info(self, message: str) -> int:
        """Log an info message."""
        # Only show if not in quiet mode
        if not self.quiet_mode:
            print(f"{Colors.BLUE}🔄 {message}{Colors.RESET}")
        
        # Log to file if enabled
        if self.log_file:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            with open(self.log_file, 'a') as f:
                f.write(f"[{timestamp}] [INFO] {message}\n")
        
        return 0
    
    def log_success(self, message: str) -> int:
        """Log a success message."""
        print(f"{Colors.GREEN}✅ {message}{Colors.RESET}")
        
        # Log to file if enabled
        if self.log_file:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            with open(self.log_file, 'a') as f:
                f.write(f"[{timestamp}] [SUCCESS] {message}\n")
        
        return 0
    
    def log_debug(self, message: str) -> int:
        """Log a debug message."""
        # Only show in debug mode
        if self.debug_mode:
            print(f"{Colors.CYAN}🐞 DEBUG: {message}{Colors.RESET}")
        
        # Log to file if enabled
        if self.log_file:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            with open(self.log_file, 'a') as f:
                f.write(f"[{timestamp}] [DEBUG] {message}\n")
        
        return 0
    
    def check_command(self, command_name: str, 
                      error_message: Optional[str] = None) -> int:
        """Check if a command is available."""
        import shutil
        
        if error_message is None:
            error_message = f"Command '{command_name}' not found"
        
        if not shutil.which(command_name):
            return self.log_error(error_message, ErrorCode.COMMAND_NOT_FOUND)
        
        return 0
    
    def check_dependency(self, dependency: str, 
                         error_message: Optional[str] = None) -> int:
        """Check if a required dependency is available."""
        import shutil
        
        if error_message is None:
            error_message = f"Dependency '{dependency}' not found"
        
        # Special handling for specific dependencies
        if dependency in ["python", "python3"]:
            if not shutil.which("python3") and not shutil.which("python"):
                return self.log_error(error_message, ErrorCode.MISSING_DEPENDENCY)
        elif dependency in ["node", "nodejs"]:
            if not shutil.which("node"):
                return self.log_error(error_message, ErrorCode.MISSING_DEPENDENCY)
        elif dependency == "git":
            if not shutil.which("git"):
                return self.log_error(error_message, ErrorCode.MISSING_DEPENDENCY)
        elif dependency == "uv":
            if not shutil.which("uv"):
                return self.log_error(error_message, ErrorCode.MISSING_DEPENDENCY)
        else:
            # Generic dependency check
            if not shutil.which(dependency):
                return self.log_error(error_message, ErrorCode.MISSING_DEPENDENCY)
        
        return 0
    
    def validate_argument(self, argument: str, pattern: str, 
                          error_message: Optional[str] = None) -> int:
        """Validate an argument against a pattern."""
        import re
        
        if error_message is None:
            error_message = f"Invalid argument: '{argument}'"
        
        if not re.match(pattern, argument):
            return self.log_error(error_message, ErrorCode.INVALID_ARGUMENT)
        
        return 0
    
    def check_file(self, file_path: str, 
                   error_message: Optional[str] = None) -> int:
        """Check if a file exists."""
        if error_message is None:
            error_message = f"File not found: '{file_path}'"
        
        if not Path(file_path).is_file():
            return self.log_error(error_message, ErrorCode.FILE_NOT_FOUND)
        
        return 0
    
    def check_directory(self, dir_path: str, 
                        error_message: Optional[str] = None) -> int:
        """Check if a directory exists."""
        if error_message is None:
            error_message = f"Directory not found: '{dir_path}'"
        
        if not Path(dir_path).is_dir():
            return self.log_error(error_message, ErrorCode.FILE_NOT_FOUND)
        
        return 0
    
    def check_readable(self, file_path: str, 
                       error_message: Optional[str] = None) -> int:
        """Check if a file is readable."""
        if error_message is None:
            error_message = f"File not readable: '{file_path}'"
        
        path = Path(file_path)
        if not path.exists() or not os.access(path, os.R_OK):
            return self.log_error(error_message, ErrorCode.PERMISSION_DENIED)
        
        return 0
    
    def check_writable(self, file_path: str, 
                       error_message: Optional[str] = None) -> int:
        """Check if a file is writable."""
        if error_message is None:
            error_message = f"File not writable: '{file_path}'"
        
        path = Path(file_path)
        if not path.exists() or not os.access(path, os.W_OK):
            return self.log_error(error_message, ErrorCode.PERMISSION_DENIED)
        
        return 0
    
    def check_directory_writable(self, dir_path: str, 
                                 error_message: Optional[str] = None) -> int:
        """Check if a directory is writable."""
        if error_message is None:
            error_message = f"Directory not writable: '{dir_path}'"
        
        path = Path(dir_path)
        if not path.is_dir() or not os.access(path, os.W_OK):
            return self.log_error(error_message, ErrorCode.PERMISSION_DENIED)
        
        return 0
    
    def check_git_repository(self, repo_path: str = ".", 
                             error_message: Optional[str] = None) -> int:
        """Check if we're in a Git repository."""
        if error_message is None:
            error_message = f"Not a Git repository: '{repo_path}'"
        
        try:
            result = subprocess.run(
                ["git", "-C", repo_path, "rev-parse", "--git-dir"],
                capture_output=True,
                check=False
            )
            if result.returncode != 0:
                return self.log_error(error_message, ErrorCode.ENVIRONMENT)
        except Exception:
            return self.log_error(error_message, ErrorCode.ENVIRONMENT)
        
        return 0
    
    def check_git_clean(self, repo_path: str = ".", 
                        error_message: Optional[str] = None) -> int:
        """Check if the working directory is clean."""
        if error_message is None:
            error_message = f"Git working directory not clean: '{repo_path}'"
        
        try:
            result = subprocess.run(
                ["git", "-C", repo_path, "diff-index", "--quiet", "HEAD", "--"],
                capture_output=True,
                check=False
            )
            if result.returncode != 0:
                return self.log_error(error_message, ErrorCode.ENVIRONMENT)
        except Exception:
            return self.log_error(error_message, ErrorCode.ENVIRONMENT)
        
        return 0
    
    def check_python_module(self, module_name: str, 
                            error_message: Optional[str] = None,
                            python_cmd: Optional[str] = None) -> int:
        """Check if a Python module is available."""
        if error_message is None:
            error_message = f"Python module '{module_name}' not found"
        
        if python_cmd is None:
            python_cmd = sys.executable
        
        try:
            result = subprocess.run(
                [python_cmd, "-c", f"import {module_name}"],
                capture_output=True,
                check=False
            )
            if result.returncode != 0:
                return self.log_error(error_message, ErrorCode.MISSING_DEPENDENCY)
        except Exception:
            return self.log_error(error_message, ErrorCode.MISSING_DEPENDENCY)
        
        return 0
    
    def check_node_module(self, module_name: str, 
                          error_message: Optional[str] = None) -> int:
        """Check if a Node.js module is available."""
        if error_message is None:
            error_message = f"Node.js module '{module_name}' not found"
        
        try:
            result = subprocess.run(
                ["node", "-e", f"require('{module_name}')"],
                capture_output=True,
                check=False
            )
            if result.returncode != 0:
                return self.log_error(error_message, ErrorCode.MISSING_DEPENDENCY)
        except Exception:
            return self.log_error(error_message, ErrorCode.MISSING_DEPENDENCY)
        
        return 0
    
    def check_network(self, host: str = "google.com", 
                      error_message: Optional[str] = None) -> int:
        """Check network connectivity."""
        if error_message is None:
            error_message = f"Network connectivity issue, cannot connect to '{host}'"
        
        try:
            # Use platform-appropriate ping command
            if sys.platform == "win32":
                cmd = ["ping", "-n", "1", "-w", "2000", host]
            else:
                cmd = ["ping", "-c", "1", "-W", "2", host]
            
            result = subprocess.run(cmd, capture_output=True, check=False)
            if result.returncode != 0:
                return self.log_error(error_message, ErrorCode.NETWORK)
        except Exception:
            return self.log_error(error_message, ErrorCode.NETWORK)
        
        return 0
    
    def run_with_timeout(self, timeout: int, command: List[str]) -> int:
        """Run a command with timeout."""
        try:
            result = subprocess.run(
                command,
                timeout=timeout,
                capture_output=False,
                check=False
            )
            return result.returncode
        except subprocess.TimeoutExpired:
            self.log_error(f"Command timed out after {timeout} seconds", 
                           ErrorCode.TIMEOUT)
            return ErrorCode.TIMEOUT
        except Exception as e:
            self.log_error(f"Error running command: {e}", ErrorCode.UNEXPECTED)
            return ErrorCode.UNEXPECTED
    
    def handle_exit(self, exit_code: int, message: Optional[str] = None) -> None:
        """Handle exit cleanly."""
        # Clean up will be done by atexit handler
        
        # If a message was provided, log it
        if message:
            if exit_code == 0:
                self.log_success(message)
            else:
                self.log_error(message, exit_code)
        
        sys.exit(exit_code)
    
    def add_temp_file(self, temp_file: str) -> None:
        """Add a temporary file to the cleanup list."""
        self.temp_files.append(temp_file)
    
    def add_temp_dir(self, temp_dir: str) -> None:
        """Add a temporary directory to the cleanup list."""
        self.temp_dirs.append(temp_dir)
    
    def create_temp_file(self, prefix: str = "dhtl", suffix: str = "") -> str:
        """Create a temporary file that will be cleaned up on exit."""
        fd, temp_file = tempfile.mkstemp(prefix=prefix, suffix=suffix)
        os.close(fd)  # Close the file descriptor
        self.add_temp_file(temp_file)
        return temp_file
    
    def create_temp_dir(self, prefix: str = "dhtl") -> str:
        """Create a temporary directory that will be cleaned up on exit."""
        temp_dir = tempfile.mkdtemp(prefix=prefix)
        self.add_temp_dir(temp_dir)
        return temp_dir
    
    def _cleanup(self) -> None:
        """Clean up temporary files and directories."""
        # Clean up files
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
            except Exception:
                pass  # Ignore errors during cleanup
        
        # Clean up directories
        for temp_dir in self.temp_dirs:
            try:
                if os.path.exists(temp_dir):
                    import shutil
                    shutil.rmtree(temp_dir)
            except Exception:
                pass  # Ignore errors during cleanup
    
    def _signal_handler(self, signum: int, frame: Any) -> None:
        """Handle signals for clean exit."""
        self.handle_exit(130 if signum == signal.SIGINT else 1, 
                         "Exiting due to interrupt")


# Global instance for convenience
_error_handler = DHTErrorHandler()

# Export convenience functions
log_error = _error_handler.log_error
log_warning = _error_handler.log_warning
log_info = _error_handler.log_info
log_success = _error_handler.log_success
log_debug = _error_handler.log_debug
check_command = _error_handler.check_command
check_dependency = _error_handler.check_dependency
validate_argument = _error_handler.validate_argument
check_file = _error_handler.check_file
check_directory = _error_handler.check_directory
check_readable = _error_handler.check_readable
check_writable = _error_handler.check_writable
check_directory_writable = _error_handler.check_directory_writable
check_git_repository = _error_handler.check_git_repository
check_git_clean = _error_handler.check_git_clean
check_python_module = _error_handler.check_python_module
check_node_module = _error_handler.check_node_module
check_network = _error_handler.check_network
run_with_timeout = _error_handler.run_with_timeout
handle_exit = _error_handler.handle_exit
add_temp_file = _error_handler.add_temp_file
add_temp_dir = _error_handler.add_temp_dir
create_temp_file = _error_handler.create_temp_file
create_temp_dir = _error_handler.create_temp_dir