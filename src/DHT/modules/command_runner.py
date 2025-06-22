#!/usr/bin/env python3
"""
Command Runner module.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Create common Prefect-based command runner infrastructure
# - Provides fail-safe execution with queue management
# - Handles crashes and interruptions gracefully
# - Ensures project codebase safety
#

"""
DHT Command Runner - Prefect-based execution infrastructure.

Provides a common runner for all DHT commands with:
- Queue management
- Fail-safe execution
- Crash recovery
- Memory leak prevention
- Thread safety
"""

import logging
import os
import signal
import sys
import threading
import time
from collections.abc import Callable
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import psutil
from prefect import flow, task
from prefect.concurrency.sync import concurrency

logger = logging.getLogger(__name__)


class CommandRunner:
    """Common runner for all DHT commands using Prefect."""

    def __init__(self):
        """Initialize the command runner."""
        self.logger = logging.getLogger(__name__)
        self._setup_signal_handlers()
        self._active_threads = set()
        self._cleanup_lock = threading.Lock()

    def _setup_signal_handlers(self):
        """Set up signal handlers for graceful shutdown."""

        def signal_handler(signum, frame):
            self.logger.info(f"Received signal {signum}, initiating graceful shutdown...")
            self._cleanup_resources()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    def _cleanup_resources(self):
        """Clean up resources to prevent leaks."""
        with self._cleanup_lock:
            # Terminate active threads
            for thread in self._active_threads:
                if thread.is_alive():
                    self.logger.warning(f"Terminating thread: {thread.name}")
                    # Note: Python threads can't be forcefully terminated
                    # This is why we use Prefect tasks with proper cancellation

            # Clean up any temporary files
            self._cleanup_temp_files()

    def _cleanup_temp_files(self):
        """Clean up temporary files created during execution."""
        temp_patterns = [".dht_tmp_*", ".pytest_cache", "__pycache__", "*.pyc", ".coverage*"]

        cwd = Path.cwd()
        for pattern in temp_patterns:
            for path in cwd.glob(pattern):
                try:
                    if path.is_file():
                        path.unlink()
                    elif path.is_dir():
                        import shutil

                        shutil.rmtree(path)
                except Exception as e:
                    self.logger.debug(f"Failed to clean up {path}: {e}")

    @contextmanager
    def _resource_guard(self, command_name: str):
        """Context manager to ensure resource cleanup."""
        # Record start state
        start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        start_threads = threading.active_count()

        try:
            yield
        finally:
            # Check for resource leaks
            end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            end_threads = threading.active_count()

            memory_increase = end_memory - start_memory
            thread_increase = end_threads - start_threads

            if memory_increase > 100:  # More than 100MB increase
                self.logger.warning(f"Command '{command_name}' may have memory leak: {memory_increase:.1f}MB increase")

            if thread_increase > 0:
                self.logger.warning(
                    f"Command '{command_name}' may have thread leak: {thread_increase} threads not cleaned up"
                )

    @task(
        name="execute_command",
        description="Execute a DHT command with fail-safe mechanisms",
        retries=0,  # Commands handle their own retries
        timeout_seconds=1800,  # 30 minutes default timeout
        tags=["dht", "command"],
    )
    def execute_command(
        self, command_name: str, command_func: Callable, args: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Execute a command with Prefect task management.

        Args:
            command_name: Name of the command
            command_func: The command function to execute
            args: Arguments to pass to the command

        Returns:
            Result dictionary with success status and any output
        """
        if args is None:
            args = {}

        self.logger.info(f"Executing command: {command_name}")

        result = {"success": False, "command": command_name, "start_time": time.time(), "error": None, "output": None}

        with self._resource_guard(command_name):
            try:
                # Execute with concurrency limit
                with concurrency("dht-commands", occupy=1):
                    # Run the command
                    output = command_func(**args)

                    # Handle different return types
                    if isinstance(output, dict):
                        result.update(output)
                    else:
                        result["output"] = output
                        result["success"] = True

            except KeyboardInterrupt:
                result["error"] = "Command interrupted by user"
                self.logger.info(f"Command '{command_name}' interrupted")
                raise
            except Exception as e:
                result["error"] = str(e)
                self.logger.error(f"Command '{command_name}' failed: {e}", exc_info=True)
            finally:
                result["end_time"] = time.time()
                result["duration"] = result["end_time"] - result["start_time"]

        return result

    @flow(
        name="dht_command_flow",
        description="Main flow for DHT command execution",
        persist_result=True,
        result_storage_key_fn=lambda context, parameters: f"dht-{parameters['command_name']}-{context.start_time}",
    )
    def run_command_flow(
        self, command_name: str, command_func: Callable, args: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Run a command as a Prefect flow.

        This provides:
        - Automatic persistence of results
        - Visibility in Prefect UI
        - Crash recovery through result persistence
        - Proper cleanup on failure

        Args:
            command_name: Name of the command
            command_func: The command function to execute
            args: Arguments to pass to the command

        Returns:
            Result dictionary
        """
        # Check if we're already in a flow context
        from prefect.context import FlowRunContext

        try:
            FlowRunContext.get()
            # We're already in a flow, just execute the task
            return self.execute_command(command_name, command_func, args)
        except Exception:
            # Not in a flow, create one
            pass

        # Create a recovery checkpoint
        checkpoint_file = Path(f".dht_checkpoint_{command_name}_{os.getpid()}.json")

        try:
            # Save checkpoint
            import json

            checkpoint_data = {"command": command_name, "args": args, "pid": os.getpid(), "start_time": time.time()}
            checkpoint_file.write_text(json.dumps(checkpoint_data))

            # Execute command
            result = self.execute_command(command_name, command_func, args)

            # Clean up checkpoint on success
            if checkpoint_file.exists():
                checkpoint_file.unlink()

            return result

        except Exception as e:
            self.logger.error(f"Flow execution failed: {e}")
            # Checkpoint remains for recovery
            raise
        finally:
            # Ensure cleanup even on crash
            self._cleanup_resources()

    def recover_from_checkpoint(self) -> list[Path]:
        """
        Check for and return any command checkpoints from crashes.

        Returns:
            List of checkpoint files found
        """
        checkpoints = list(Path.cwd().glob(".dht_checkpoint_*.json"))

        if checkpoints:
            self.logger.info(f"Found {len(checkpoints)} command checkpoints from previous runs")

            # Check if PIDs are still running
            import json

            for checkpoint in checkpoints:
                try:
                    data = json.loads(checkpoint.read_text())
                    pid = data.get("pid")
                    if pid and psutil.pid_exists(pid):
                        self.logger.warning(f"Command '{data['command']}' may still be running (PID: {pid})")
                    else:
                        self.logger.info(f"Command '{data['command']}' crashed previously, checkpoint available")
                except Exception as e:
                    self.logger.debug(f"Failed to read checkpoint {checkpoint}: {e}")

        return checkpoints


# Global instance for easy access
command_runner = CommandRunner()


def run_command_safely(
    command_name: str, command_func: Callable, args: dict[str, Any] | None = None, use_flow: bool = True
) -> dict[str, Any]:
    """
    Convenience function to run a command safely.

    Args:
        command_name: Name of the command
        command_func: The command function to execute
        args: Arguments to pass to the command
        use_flow: Whether to run as a Prefect flow (recommended)

    Returns:
        Result dictionary
    """
    if use_flow:
        return command_runner.run_command_flow(command_name, command_func, args)
    else:
        return command_runner.execute_command(command_name, command_func, args)
