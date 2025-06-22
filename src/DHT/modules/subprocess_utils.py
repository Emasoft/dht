#!/usr/bin/env python3
"""
subprocess_utils.py - Enhanced subprocess handling with comprehensive error management  This module provides robust subprocess execution with: - Detailed error handling and custom exceptions - Timeout management with proper cleanup - Signal handling (interrupts) - Retry logic for transient failures - Resource limit enforcement

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

"""
subprocess_utils.py - Enhanced subprocess handling with comprehensive error management

This module provides robust subprocess execution with:
- Detailed error handling and custom exceptions
- Timeout management with proper cleanup
- Signal handling (interrupts)
- Retry logic for transient failures
- Resource limit enforcement
- Output size limits
- Sensitive data masking in logs
- Process group management for cleanup
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Created comprehensive subprocess utilities with enhanced error handling
# - Added custom exception types for different error scenarios
# - Implemented retry logic, timeout handling, and resource limits
# - Added context manager for proper resource cleanup
# - Included security features like sensitive data masking
#

from __future__ import annotations

import logging
import os
import signal
import subprocess
import sys
import threading
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

# Configure logging
logger = logging.getLogger(__name__)


class ProcessError(Exception):
    """Base exception for subprocess errors."""

    def __init__(self, message: str, command: list[str], **kwargs):
        """Initialize process error with command context."""
        super().__init__(message)
        self.command = command
        self.cwd = kwargs.get("cwd")
        self.env = kwargs.get("env")
        self.details = kwargs


class ProcessNotFoundError(ProcessError):
    """Raised when command/executable is not found."""

    pass


class ProcessExecutionError(ProcessError):
    """Raised when process exits with non-zero status."""

    def __init__(self, message: str, command: list[str], returncode: int, **kwargs):
        """Initialize with return code."""
        super().__init__(message, command, **kwargs)
        self.returncode = returncode
        self.stdout = kwargs.get("stdout", "")
        self.stderr = kwargs.get("stderr", "")
        self.retry_count = kwargs.get("retry_count", 0)


class CommandTimeoutError(ProcessError):
    """Raised when command execution times out."""

    def __init__(self, message: str, command: list[str], timeout: float, **kwargs):
        """Initialize with timeout value."""
        super().__init__(message, command, **kwargs)
        self.timeout = timeout


class ProcessInterruptedError(ProcessError):
    """Raised when process is interrupted by signal."""

    def __init__(self, message: str, command: list[str], signal_num: int, **kwargs):
        """Initialize with signal number."""
        super().__init__(message, command, **kwargs)
        self.signal_num = signal_num


class SubprocessContext:
    """Context manager for subprocess execution with cleanup."""

    def __init__(self):
        """Initialize context manager."""
        self.processes_run = 0
        self.cleaned_up = False
        self._active_processes: list[subprocess.Popen] = []
        self._lock = threading.Lock()

    def __enter__(self):
        """Enter context."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context and cleanup resources."""
        self.cleanup()
        return False

    def run(self, command: list[str], **kwargs) -> dict[str, Any]:
        """Run command within context."""
        self.processes_run += 1
        return run_subprocess(command, context=self, **kwargs)

    def register_process(self, process: subprocess.Popen):
        """Register a process for tracking."""
        with self._lock:
            self._active_processes.append(process)

    def unregister_process(self, process: subprocess.Popen):
        """Unregister a process."""
        with self._lock:
            if process in self._active_processes:
                self._active_processes.remove(process)

    def cleanup(self):
        """Cleanup all active processes."""
        with self._lock:
            for process in self._active_processes:
                try:
                    # Try graceful termination first
                    process.terminate()
                    try:
                        process.wait(timeout=2)
                    except subprocess.TimeoutExpired:
                        # Force kill if needed
                        process.kill()
                        process.wait()
                except Exception as e:
                    logger.warning(f"Error cleaning up process: {e}")

            self._active_processes.clear()
            self.cleaned_up = True


def mask_sensitive_args(command: list[str], sensitive_args: list[str]) -> list[str]:
    """Mask sensitive arguments in command for logging."""
    masked_command = []
    for arg in command:
        if arg in sensitive_args:
            masked_command.append("***")
        else:
            # Also check if arg contains sensitive data
            masked_arg = arg
            for sensitive in sensitive_args:
                if sensitive in arg:
                    masked_arg = arg.replace(sensitive, "***")
            masked_command.append(masked_arg)
    return masked_command


def set_resource_limits(memory_limit_mb: int | None = None):
    """Set resource limits for subprocess."""
    if not memory_limit_mb:
        return

    try:
        import resource

        # Convert MB to bytes
        memory_bytes = memory_limit_mb * 1024 * 1024

        # Get current limits
        soft, hard = resource.getrlimit(resource.RLIMIT_AS)

        # Set memory limit (not exceeding hard limit)
        new_limit = min(memory_bytes, hard)
        resource.setrlimit(resource.RLIMIT_AS, (new_limit, hard))
    except ImportError:
        logger.warning("Resource module not available (Windows?), skipping memory limits")
    except Exception as e:
        logger.warning(f"Failed to set resource limits: {e}")


def run_subprocess(
    command: list[str] | str,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    timeout: float | None = None,
    check: bool = True,
    capture_output: bool = True,
    text: bool = True,
    input_data: str | None = None,
    shell: bool = False,
    stderr_mode: str = "capture",  # "capture", "merge", "discard"
    retry_count: int = 0,
    retry_delay: float = 1.0,
    max_output_size: int | None = None,
    create_process_group: bool = False,
    memory_limit_mb: int | None = None,
    error_handler: Callable | None = None,
    log_command: bool = True,
    sensitive_args: list[str] | None = None,
    context: SubprocessContext | None = None,
) -> dict[str, Any]:
    """
    Run subprocess with enhanced error handling.

    Args:
        command: Command to run (list or string if shell=True)
        cwd: Working directory
        env: Environment variables
        timeout: Timeout in seconds
        check: Raise exception on non-zero exit
        capture_output: Capture stdout/stderr
        text: Return text instead of bytes
        input_data: Data to send to stdin
        shell: Execute through shell (security risk!)
        stderr_mode: How to handle stderr ("capture", "merge", "discard")
        retry_count: Number of retries on failure
        retry_delay: Delay between retries in seconds
        max_output_size: Maximum output size in bytes
        create_process_group: Create new process group
        memory_limit_mb: Memory limit in megabytes
        error_handler: Custom error handler function
        log_command: Log command execution
        sensitive_args: Arguments to mask in logs
        context: Subprocess context for resource management

    Returns:
        Dict with execution results

    Raises:
        Various ProcessError subclasses on failure
    """
    # Validate inputs
    if shell and not isinstance(command, str):
        raise ValueError("Shell commands must be strings")
    if not shell and isinstance(command, str):
        raise ValueError("Non-shell commands must be lists")

    # Security warning for shell execution
    if shell:
        logger.warning("Shell execution requested - potential security risk")

    # Log command (with masking)
    if log_command:
        if sensitive_args and isinstance(command, list):
            logged_command = mask_sensitive_args(command, sensitive_args)
        else:
            logged_command = command
        logger.debug(f"Running command: {logged_command}")
        if cwd:
            logger.debug(f"Working directory: {cwd}")

    # Setup stderr handling
    stderr_setting = subprocess.STDOUT if stderr_mode == "merge" else subprocess.PIPE
    if stderr_mode == "discard":
        stderr_setting = subprocess.DEVNULL

    # Prepare environment
    process_env = env if env is not None else os.environ.copy()

    # Attempt execution with retries
    last_error = None
    for attempt in range(retry_count + 1):
        try:
            # Setup process options
            popen_kwargs = {
                "cwd": cwd,
                "env": process_env,
                "stdout": subprocess.PIPE if capture_output else None,
                "stderr": stderr_setting if capture_output else None,
                "text": text,
                "shell": shell,
            }

            # Add process group creation for better cleanup
            if create_process_group and hasattr(os, "setpgrp"):
                popen_kwargs["preexec_fn"] = os.setpgrp
            elif create_process_group and sys.platform == "win32":
                popen_kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP

            # Set resource limits if specified
            if memory_limit_mb and hasattr(os, "setpgrp"):
                popen_kwargs["preexec_fn"] = lambda: set_resource_limits(memory_limit_mb)

            # Handle input data
            if input_data:
                popen_kwargs["stdin"] = subprocess.PIPE

            # Create process
            process = subprocess.Popen(command, **popen_kwargs)

            # Register with context if provided
            if context:
                context.register_process(process)

            try:
                # Communicate with timeout
                if input_data:
                    if text:
                        # When text=True, communicate expects str input
                        comm_input = input_data if isinstance(input_data, str) else input_data.decode()
                    else:
                        # When text=False, communicate expects bytes input
                        comm_input = input_data if isinstance(input_data, bytes) else input_data.encode()
                else:
                    comm_input = None

                stdout, stderr = process.communicate(input=comm_input, timeout=timeout)

                # Handle large output truncation
                output_truncated = False
                if max_output_size and stdout and len(stdout) > max_output_size:
                    stdout = stdout[:max_output_size]
                    output_truncated = True

                # Build result
                result = {
                    "stdout": stdout if stdout is not None else "",
                    "stderr": stderr if stderr is not None else "",
                    "returncode": process.returncode,
                    "success": process.returncode == 0,
                    "output_truncated": output_truncated,
                    "attempt": attempt + 1,
                    "command": command,
                }

                # Check for failure
                if check and process.returncode != 0:
                    raise subprocess.CalledProcessError(process.returncode, command, stdout, stderr)

                # Success - return result
                return result

            except subprocess.TimeoutExpired:
                # Kill the process
                process.kill()
                process.wait()
                raise CommandTimeoutError(
                    f"Command timed out after {timeout} seconds",
                    command if isinstance(command, list) else [command],
                    timeout,
                    cwd=cwd,
                )

            except KeyboardInterrupt:
                # Handle interrupt
                process.terminate()
                process.wait()
                raise ProcessInterruptedError(
                    "Process interrupted by user",
                    command if isinstance(command, list) else [command],
                    signal.SIGINT,
                    cwd=cwd,
                )

            finally:
                # Unregister from context
                if context:
                    context.unregister_process(process)

        except subprocess.CalledProcessError as e:
            last_error = ProcessExecutionError(
                f"Command failed with exit code {e.returncode}",
                command if isinstance(command, list) else [command],
                e.returncode,
                stdout=e.stdout if hasattr(e, "stdout") else "",
                stderr=e.stderr if hasattr(e, "stderr") else "",
                cwd=cwd,
                retry_count=attempt,
            )

            # Use custom error handler if provided
            if error_handler:
                return error_handler(last_error, {"command": command, "attempt": attempt})

            # Retry if attempts remain
            if attempt < retry_count:
                logger.warning(f"Command failed (attempt {attempt + 1}/{retry_count + 1}), retrying...")
                time.sleep(retry_delay)
                continue

            # No more retries
            if check:
                raise last_error
            else:
                return {
                    "stdout": last_error.stdout,
                    "stderr": last_error.stderr,
                    "returncode": last_error.returncode,
                    "success": False,
                    "error": str(last_error),
                    "attempt": attempt + 1,
                }

        except FileNotFoundError as e:
            last_error = ProcessNotFoundError(
                f"Command not found: {command[0] if isinstance(command, list) else command.split()[0]}",
                command if isinstance(command, list) else [command],
                cwd=cwd,
            )

            # Use custom error handler if provided
            if error_handler:
                return error_handler(last_error, {"command": command, "attempt": attempt})

            raise last_error

        except (CommandTimeoutError, ProcessInterruptedError):
            # Re-raise these without retry
            raise

        except Exception as e:
            # Unexpected error
            logger.error(f"Unexpected error running command: {e}")

            if error_handler:
                return error_handler(e, {"command": command, "attempt": attempt})

            raise ProcessError(
                f"Unexpected error: {str(e)}",
                command if isinstance(command, list) else [command],
                cwd=cwd,
                error_type=type(e).__name__,
            )

    # Should not reach here
    raise last_error or ProcessError(
        "Command execution failed", command if isinstance(command, list) else [command], cwd=cwd
    )


# Convenience functions
def run_command(command: list[str], **kwargs) -> dict[str, Any]:
    """Convenience function for running commands with defaults."""
    return run_subprocess(command, **kwargs)


def run_shell_command(command: str, **kwargs) -> dict[str, Any]:
    """Convenience function for running shell commands."""
    return run_subprocess(command, shell=True, **kwargs)


def check_command_exists(command: str) -> bool:
    """Check if a command exists in PATH."""
    try:
        result = run_subprocess(["which", command], check=False, log_command=False)
        return result["success"]
    except ProcessNotFoundError:
        # 'which' itself not found (Windows?)
        try:
            result = run_subprocess(["where", command], check=False, log_command=False)
            return result["success"]
        except ProcessNotFoundError:
            return False


__all__ = [
    "ProcessError",
    "ProcessNotFoundError",
    "ProcessExecutionError",
    "CommandTimeoutError",
    "ProcessInterruptedError",
    "SubprocessContext",
    "run_subprocess",
    "run_command",
    "run_shell_command",
    "check_command_exists",
]
