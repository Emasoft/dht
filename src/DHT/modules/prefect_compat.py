#!/usr/bin/env python3
"""
Prefect compatibility module for DHT.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE FILE:
# - Create compatibility layer for Prefect 3.x
# - Patch missing modules that were removed in Prefect 3.x
# - Ensure compatibility with both Prefect 2.x and 3.x
# - Simplified approach: patch at import time
#

"""
Prefect compatibility module.

This module provides compatibility patches for different versions of Prefect,
ensuring DHT works with both Prefect 2.x and 3.x.
"""

import sys
from typing import Any


def _patch_visualization_module() -> None:
    """Create and patch the visualization module with missing functions."""
    # First ensure the module structure exists
    try:
        import prefect.utilities.visualization

        viz_module = prefect.utilities.visualization
    except ImportError:
        # Create the module structure if it doesn't exist
        from types import ModuleType

        # Ensure prefect.utilities exists
        import prefect

        if not hasattr(prefect, "utilities"):
            utilities = ModuleType("prefect.utilities")
            sys.modules["prefect.utilities"] = utilities
            prefect.utilities = utilities

        # Create visualization module
        viz_module = ModuleType("prefect.utilities.visualization")
        sys.modules["prefect.utilities.visualization"] = viz_module
        prefect.utilities.visualization = viz_module

    # Add missing functions that Prefect 3.x task decorator expects
    if not hasattr(viz_module, "get_task_viz_tracker"):

        def get_task_viz_tracker() -> Any | None:
            """Mock function for backward compatibility."""
            return None

        viz_module.get_task_viz_tracker = get_task_viz_tracker

    if not hasattr(viz_module, "track_viz_task"):

        def track_viz_task(is_async: bool, task_name: str, parameters: dict[str, Any]) -> Any:
            """Mock function for backward compatibility."""

            class NoOpContext:
                def __enter__(self) -> "NoOpContext":
                    return self

                def __exit__(self, *args: Any) -> None:
                    pass

            return NoOpContext()

        viz_module.track_viz_task = track_viz_task

    if not hasattr(viz_module, "task_input_kwargs"):

        def task_input_kwargs(*args: Any, **kwargs: Any) -> dict[str, Any]:
            """Mock function for backward compatibility."""
            return kwargs

        viz_module.task_input_kwargs = task_input_kwargs


# Apply patches immediately when module is imported
_patch_visualization_module()


# Check Prefect version for reference
try:
    import prefect

    PREFECT_VERSION = tuple(int(x) for x in prefect.__version__.split(".")[:2])
except Exception:
    PREFECT_VERSION = (3, 0)


# Re-export common Prefect imports after patching
from prefect import flow, get_run_logger, task
from prefect.context import FlowRunContext, TaskRunContext

__all__ = ["task", "flow", "get_run_logger", "TaskRunContext", "FlowRunContext", "PREFECT_VERSION"]
