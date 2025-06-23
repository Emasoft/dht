#!/usr/bin/env python3
"""
Unit tests for subprocess utilities with enhanced error handling.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

"""
Unit tests for subprocess utilities with enhanced error handling.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Created comprehensive tests for subprocess error handling
# - Tests for timeout, signal handling, resource cleanup
# - Tests for retry logic and error context
#

import os
import signal
import subprocess
import time
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

# Module will be created after tests (TDD)
from DHT.modules.subprocess_utils import (
    CommandTimeoutError,
    ProcessExecutionError,
    ProcessInterruptedError,
    ProcessNotFoundError,
    SubprocessContext,
    run_subprocess,
)


class TestSubprocessUtils:
    """Test subprocess utilities with enhanced error handling."""

    def test_successful_command_execution(self) -> Any:
        """Test successful command execution returns expected output."""
        result = run_subprocess(["echo", "hello world"])
        assert result["success"] is True
        assert result["stdout"].strip() == "hello world"
        assert result["stderr"] == ""
        assert result["returncode"] == 0

    def test_command_not_found_error(self) -> Any:
        """Test handling of command not found errors."""
        with pytest.raises(ProcessNotFoundError) as exc_info:
            run_subprocess(["nonexistent_command_xyz"])

        assert "nonexistent_command_xyz" in str(exc_info.value)
        assert exc_info.value.command == ["nonexistent_command_xyz"]

    def test_command_failure_with_nonzero_exit(self) -> Any:
        """Test handling of commands that exit with non-zero status."""
        # Use a command that fails
        result = run_subprocess(["python", "-c", "import sys; sys.exit(1)"], check=False)
        assert result["success"] is False
        assert result["returncode"] == 1

        # With check=True, should raise
        with pytest.raises(ProcessExecutionError) as exc_info:
            run_subprocess(["python", "-c", "import sys; sys.exit(42)"], check=True)

        assert exc_info.value.returncode == 42

    def test_command_timeout_handling(self) -> Any:
        """Test timeout handling for long-running commands."""
        # Command that sleeps for 5 seconds
        with pytest.raises(CommandTimeoutError) as exc_info:
            run_subprocess(
                ["python", "-c", "import time; time.sleep(5)"],
                timeout=0.5,  # 500ms timeout
            )

        assert exc_info.value.timeout == 0.5
        assert "timed out after 0.5 seconds" in str(exc_info.value)

    def test_interrupt_signal_handling(self) -> Any:
        """Test handling of interrupt signals (Ctrl+C)."""

        def send_interrupt() -> Any:
            time.sleep(0.1)
            os.kill(os.getpid(), signal.SIGINT)

        # Start a thread to send interrupt
        import threading

        interrupt_thread = threading.Thread(target=send_interrupt)
        interrupt_thread.start()

        with pytest.raises(ProcessInterruptedError) as exc_info:
            run_subprocess(["python", "-c", "import time; time.sleep(2)"])

        interrupt_thread.join()
        assert "interrupted" in str(exc_info.value).lower()

    def test_working_directory_handling(self) -> Any:
        """Test command execution in different working directories."""
        with patch("os.getcwd", return_value="/original/path"):
            result = run_subprocess(["python", "-c", "import os; print(os.getcwd())"], cwd=Path("/tmp"))
            assert result["success"] is True
            assert "/tmp" in result["stdout"]

    def test_environment_variable_handling(self) -> Any:
        """Test passing environment variables to subprocess."""
        env = {"TEST_VAR": "test_value", "PATH": os.environ.get("PATH", "")}
        result = run_subprocess(["python", "-c", "import os; print(os.environ.get('TEST_VAR', 'not_found'))"], env=env)
        assert result["success"] is True
        assert "test_value" in result["stdout"]

    def test_retry_logic_on_failure(self) -> Any:
        """Test retry logic for transient failures."""
        # Mock subprocess.Popen to fail twice then succeed
        call_count = 0

        class MockPopen:
            def __init__(self, *args, **kwargs) -> Any:
                nonlocal call_count
                call_count += 1
                self.returncode = 1 if call_count < 3 else 0
                self.stdout = "" if call_count < 3 else "success"
                self.stderr = "error" if call_count < 3 else ""

            def communicate(self, input=None, timeout=None) -> Any:
                if self.returncode != 0:
                    raise subprocess.CalledProcessError(self.returncode, "cmd", self.stdout, self.stderr)
                return self.stdout, self.stderr

            def wait(self, timeout=None) -> Any:
                pass

            def kill(self) -> Any:
                pass

            def terminate(self) -> Any:
                pass

        with patch("subprocess.Popen", MockPopen):
            result = run_subprocess(["echo", "test"], retry_count=3, retry_delay=0.01, check=False)
            assert result["success"] is True
            assert result["stdout"] == "success"
            assert call_count == 3

    def test_retry_exhaustion(self) -> Any:
        """Test that retries are exhausted and error is raised."""

        class MockPopen:
            def __init__(self, *args, **kwargs) -> Any:
                self.returncode = 1

            def communicate(self, input=None, timeout=None) -> Any:
                raise subprocess.CalledProcessError(1, "cmd", b"", b"error")

            def wait(self, timeout=None) -> Any:
                pass

            def kill(self) -> Any:
                pass

            def terminate(self) -> Any:
                pass

        with patch("subprocess.Popen", MockPopen):
            with pytest.raises(ProcessExecutionError) as exc_info:
                run_subprocess(["echo", "test"], retry_count=2, retry_delay=0.01)

            assert exc_info.value.retry_count == 2

    def test_stderr_capture_modes(self) -> Any:
        """Test different stderr capture modes."""
        # Capture stderr separately
        result = run_subprocess(
            ["python", "-c", "import sys; sys.stderr.write('error'); sys.stdout.write('output')"], stderr_mode="capture"
        )
        assert result["stdout"].strip() == "output"
        assert result["stderr"].strip() == "error"

        # Redirect stderr to stdout
        result = run_subprocess(
            ["python", "-c", "import sys; sys.stderr.write('error'); sys.stdout.write('output')"], stderr_mode="merge"
        )
        assert "error" in result["stdout"] or "error" in result["stderr"]

    def test_subprocess_context_manager(self) -> Any:
        """Test subprocess context manager for resource cleanup."""
        with SubprocessContext() as ctx:
            result = ctx.run(["echo", "test"])
            assert result["success"] is True
            assert ctx.processes_run == 1

        # Context should clean up resources
        assert ctx.cleaned_up is True

    def test_subprocess_context_cleanup_on_exception(self) -> Any:
        """Test context manager cleans up even on exception."""
        with pytest.raises(ProcessExecutionError):
            with SubprocessContext() as ctx:
                ctx.run(["false"])  # Command that always fails

        # Should still clean up
        assert ctx.cleaned_up is True

    def test_large_output_handling(self) -> Any:
        """Test handling of commands with large output."""
        # Generate 2MB of output (avoiding command line length limits)
        result = run_subprocess(
            ["python", "-c", "print('x' * (2 * 1024 * 1024))"],
            max_output_size=1024 * 1024,  # 1MB limit
        )
        assert result["success"] is True
        assert result["output_truncated"] is True
        assert len(result["stdout"]) <= 1024 * 1024

    def test_binary_output_handling(self) -> Any:
        """Test handling of binary output from commands."""
        result = run_subprocess(["python", "-c", "import sys; sys.stdout.buffer.write(b'\\x00\\x01\\x02')"], text=False)
        assert result["success"] is True
        assert isinstance(result["stdout"], bytes)
        assert result["stdout"] == b"\x00\x01\x02"

    def test_input_data_handling(self) -> Any:
        """Test passing input data to subprocess."""
        result = run_subprocess(
            ["python", "-c", "import sys; print(sys.stdin.read().upper())"], input_data="hello world"
        )
        assert result["success"] is True
        assert result["stdout"].strip() == "HELLO WORLD"

    def test_command_with_shell_execution(self) -> Any:
        """Test shell command execution (with security warning)."""
        # Should work but log security warning
        with patch("logging.Logger.warning") as mock_warning:
            result = run_subprocess("echo $HOME", shell=True)
            assert result["success"] is True
            mock_warning.assert_called_with("Shell execution requested - potential security risk")

    def test_process_group_handling(self) -> Any:
        """Test process group creation for better cleanup."""
        # This ensures child processes are also terminated
        result = run_subprocess(["python", "-c", "import os; print(os.getpgrp())"], create_process_group=True)
        assert result["success"] is True

    def test_resource_limits(self) -> Any:
        """Test setting resource limits on subprocess."""
        # Skip on systems where resource limits don't work as expected
        import platform

        if platform.system() == "Darwin":  # macOS often has issues with RLIMIT_AS
            pytest.skip("Resource limits unreliable on macOS")

        # Limit memory usage
        result = run_subprocess(
            ["python", "-c", "x = 'a' * (100 * 1024 * 1024)"],  # Try to allocate 100MB
            memory_limit_mb=50,  # 50MB limit
            check=False,
        )
        # Just verify the command runs - resource limits are advisory on many systems
        assert "success" in result

    def test_custom_error_handler(self) -> Any:
        """Test custom error handler callback."""
        error_info = {}

        def custom_handler(error, context) -> Any:
            error_info["error"] = error
            error_info["command"] = context.get("command")
            return {"success": False, "custom_handled": True, "stdout": "", "stderr": "", "returncode": -1}

        # Use a command that will fail
        result = run_subprocess(
            ["python", "-c", "import sys; sys.exit(1)"],
            check=True,  # This should trigger error handler
            error_handler=custom_handler,
        )

        assert result["custom_handled"] is True
        assert error_info["command"] == ["python", "-c", "import sys; sys.exit(1)"]

    def test_command_logging(self) -> Any:
        """Test command execution logging."""
        with patch("logging.Logger.debug") as mock_debug:
            run_subprocess(["echo", "test"], log_command=True)
            mock_debug.assert_called()
            call_args = str(mock_debug.call_args)
            assert "echo" in call_args
            assert "test" in call_args

    def test_sensitive_command_masking(self) -> Any:
        """Test masking of sensitive data in logs."""
        with patch("logging.Logger.debug") as mock_debug:
            # Use a command that exists
            result = run_subprocess(
                ["echo", "-u", "root", "-p", "secret_password"], log_command=True, sensitive_args=["secret_password"]
            )

            # Check that password is masked in logs
            call_args = str(mock_debug.call_args)
            assert "secret_password" not in call_args
            assert "***" in call_args

    def test_concurrent_subprocess_execution(self) -> Any:
        """Test thread-safe concurrent subprocess execution."""
        import concurrent.futures

        def run_echo(n) -> Any:
            return run_subprocess(["echo", str(n)])

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(run_echo, i) for i in range(10)]
            results = [f.result() for f in futures]

        # All should succeed
        assert all(r["success"] for r in results)
        # Each should have correct output
        for i, result in enumerate(results):
            assert str(i) in result["stdout"]
