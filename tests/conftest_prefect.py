#!/usr/bin/env python3
"""
Prefect-specific test configuration.

This module provides fixtures and configuration for tests that use Prefect,
ensuring proper cleanup of resources.
"""

import os
import signal
import subprocess
import time
from collections.abc import Generator

import pytest
from prefect.testing.utilities import prefect_test_harness


@pytest.fixture(scope="session")
def prefect_test_server() -> Generator[None, None, None]:
    """
    Session-scoped Prefect test server.

    This fixture starts a single Prefect test server for the entire test session,
    which is much more efficient than starting one per test and prevents
    resource leaks.
    """
    # Track the current process ID to avoid killing ourselves
    current_pid = os.getpid()

    # Clean up any existing Prefect processes before starting
    cleanup_prefect_processes(exclude_pid=current_pid)

    # Start the test harness
    with prefect_test_harness():
        yield

    # Clean up after tests
    cleanup_prefect_processes(exclude_pid=current_pid)


def cleanup_prefect_processes(exclude_pid: int | None = None) -> None:
    """
    Clean up any Prefect/uvicorn processes.

    Args:
        exclude_pid: Process ID to exclude from cleanup (usually the current process)
    """
    try:
        # Find uvicorn processes running Prefect
        result = subprocess.run(["pgrep", "-f", "uvicorn.*prefect"], capture_output=True, text=True, check=False)

        if result.returncode == 0:
            pids = result.stdout.strip().split("\n")
            for pid_str in pids:
                if pid_str:
                    try:
                        pid = int(pid_str)
                        # Don't kill ourselves or the excluded PID
                        if pid != os.getpid() and pid != exclude_pid:
                            os.kill(pid, signal.SIGTERM)
                            time.sleep(0.1)  # Give it time to shut down
                            try:
                                os.kill(pid, signal.SIGKILL)
                            except ProcessLookupError:
                                pass  # Already terminated
                    except (ValueError, ProcessLookupError):
                        pass
    except FileNotFoundError:
        # pgrep not available, try pkill
        try:
            subprocess.run(["pkill", "-f", "uvicorn.*prefect"], check=False)
        except Exception:
            pass
    except Exception:
        pass


def pytest_sessionfinish(session, exitstatus):
    """Clean up Prefect processes at the end of the test session."""
    cleanup_prefect_processes()


# Environment variable to enable Prefect test mode
os.environ["PREFECT_TEST_MODE"] = "1"
os.environ["PREFECT_HOME"] = "/tmp/prefect-test"
