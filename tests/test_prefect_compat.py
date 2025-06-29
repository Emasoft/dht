#!/usr/bin/env python3
"""
Test Prefect compatibility module.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE FILE:
# - Create tests for Prefect 3.x compatibility module
# - Test that visualization module is patched correctly
# - Test that task decorator works properly
#

"""Test Prefect compatibility module."""

from DHT.modules import prefect_compat


def test_prefect_version_detected():
    """Test that Prefect version is correctly detected."""
    assert hasattr(prefect_compat, "PREFECT_VERSION")
    assert isinstance(prefect_compat.PREFECT_VERSION, tuple)
    assert len(prefect_compat.PREFECT_VERSION) == 2


def test_visualization_module_exists():
    """Test that visualization module exists and has required functions."""
    # Import should not raise error
    from prefect.utilities.visualization import get_task_viz_tracker, task_input_kwargs, track_viz_task

    # Functions should be callable
    assert callable(get_task_viz_tracker)
    assert callable(track_viz_task)
    assert callable(task_input_kwargs)


def test_task_decorator_works():
    """Test that task decorator works correctly."""
    from DHT.modules.prefect_compat import task

    @task
    def test_function(x: int, y: int) -> int:
        """Test function with task decorator."""
        return x + y

    # Should be able to call the function
    result = test_function(2, 3)
    assert result == 5


def test_flow_decorator_available():
    """Test that flow decorator is available."""
    from DHT.modules.prefect_compat import flow

    @flow
    def test_flow():
        """Test flow function."""
        return "flow executed"

    # Should be able to call the flow
    result = test_flow()
    assert result == "flow executed"


def test_get_run_logger_available():
    """Test that get_run_logger is available."""
    from DHT.modules.prefect_compat import get_run_logger

    assert callable(get_run_logger)


def test_context_classes_available():
    """Test that context classes are available."""
    from DHT.modules.prefect_compat import FlowRunContext, TaskRunContext

    # Should be importable classes
    assert TaskRunContext is not None
    assert FlowRunContext is not None


def test_compatibility_with_dht_command():
    """Test that DHT commands work with Prefect compatibility."""
    from DHT.modules.commands.add_command import AddCommand

    # Should be able to instantiate command
    cmd = AddCommand()
    assert cmd is not None

    # The execute method should have task decorator applied
    assert hasattr(cmd.execute, "__wrapped__")  # Task decorator wraps the original function
