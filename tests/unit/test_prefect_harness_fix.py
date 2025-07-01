#!/usr/bin/env python3
"""
Fixed Prefect test harness implementation.

This module provides a proper implementation of Prefect test setup
that ensures servers are properly cleaned up after tests.
"""

import os
import signal
import time
from collections.abc import Generator
from contextlib import contextmanager

import pytest
from prefect.testing.utilities import prefect_test_harness


@contextmanager
def safe_prefect_test_harness() -> Generator[None, None, None]:
    """
    A safer version of prefect_test_harness that ensures cleanup.

    This context manager wraps the Prefect test harness and ensures
    that any spawned processes are properly cleaned up, even if the
    test fails or is interrupted.
    """
    # Track PIDs of any processes we spawn
    child_pids = set()
    original_fork = os.fork if hasattr(os, "fork") else None

    def tracking_fork() -> int:
        """Fork wrapper that tracks child PIDs."""
        pid = original_fork() if original_fork else -1
        if pid == 0:
            # We're in the child process
            pass
        else:
            # We're in the parent, track the child
            child_pids.add(pid)
        return pid

    # Temporarily replace fork to track processes
    if original_fork:
        os.fork = tracking_fork

    try:
        # Use the regular prefect test harness
        with prefect_test_harness():
            yield
    finally:
        # Restore original fork
        if original_fork:
            os.fork = original_fork

        # Clean up any child processes
        for pid in child_pids:
            try:
                os.kill(pid, signal.SIGTERM)
                # Give it a moment to terminate gracefully
                time.sleep(0.1)
                # Force kill if still running
                os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                # Process already terminated
                pass
            except Exception:
                # Ignore other errors during cleanup
                pass


@pytest.fixture(scope="session")
def prefect_test_session() -> Generator[None, None, None]:
    """
    Session-scoped Prefect test harness.

    This fixture starts a single Prefect test server for the entire test session,
    rather than starting a new one for each test. This is much more efficient
    and prevents resource leaks.
    """
    with safe_prefect_test_harness():
        yield


@pytest.fixture
def prefect_test_function(prefect_test_session: None) -> None:
    """
    Function-scoped fixture that depends on the session fixture.

    Use this in individual tests that need Prefect.
    """
    # The session fixture handles everything
    pass


def cleanup_stray_prefect_processes() -> None:
    """
    Clean up any stray Prefect/uvicorn processes.

    This function can be called to clean up processes that may have been
    left behind by previous test runs.
    """
    import subprocess

    # Find and kill uvicorn processes running Prefect
    try:
        result = subprocess.run(["pgrep", "-f", "uvicorn.*prefect"], capture_output=True, text=True)
        if result.returncode == 0:
            pids = result.stdout.strip().split("\n")
            for pid in pids:
                if pid:
                    try:
                        os.kill(int(pid), signal.SIGTERM)
                        time.sleep(0.1)
                        os.kill(int(pid), signal.SIGKILL)
                    except (ProcessLookupError, ValueError):
                        pass
    except Exception:
        # If pgrep doesn't exist or fails, try pkill
        try:
            subprocess.run(["pkill", "-f", "uvicorn.*prefect"], check=False)
        except Exception:
            pass
