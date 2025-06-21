#!/usr/bin/env python3
"""
uv_script_tasks.py - Script execution tasks for UV

This module contains Prefect tasks for running Python scripts with UV.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Extracted from uv_prefect_tasks.py to reduce file size
# - Contains Python script execution tasks
#

from __future__ import annotations

from pathlib import Path
from typing import Any

from prefect import task

from DHT.modules.guardian_prefect import ResourceLimits, run_with_guardian
from DHT.modules.uv_task_models import DEFAULT_TIMEOUT, RETRY_DELAYS, UVTaskError
from DHT.modules.uv_task_utils import find_uv_executable, get_logger


@task(
    name="run_python_script",
    description="Run a Python script in the project environment",
    retries=2,
    retry_delay_seconds=RETRY_DELAYS,
)
def run_python_script(
    project_path: Path,
    script: str,
    args: list[str] | None = None,
    timeout: int = DEFAULT_TIMEOUT,
    memory_mb: int = 2048,
) -> dict[str, Any]:
    """
    Run a Python script in the project environment.

    Args:
        project_path: Project root directory
        script: Script to run (file or module)
        args: Additional arguments for the script
        timeout: Timeout in seconds
        memory_mb: Memory limit in MB

    Returns:
        Execution result
    """
    logger = get_logger()

    uv_path = find_uv_executable()
    if not uv_path:
        raise UVTaskError("UV not found")

    project_path = Path(project_path)

    cmd_args = [str(uv_path), "run"]

    if script.endswith(".py"):
        cmd_args.extend(["python", script])
    else:
        cmd_args.extend(["python", "-m", script])

    if args:
        cmd_args.extend(args)

    result = run_with_guardian(
        command=cmd_args, limits=ResourceLimits(memory_mb=memory_mb, timeout=timeout), cwd=str(project_path)
    )

    return {
        "success": result.return_code == 0,
        "script": script,
        "output": result.stdout,
        "error": result.stderr,
        "duration": result.execution_time,
        "peak_memory_mb": result.peak_memory_mb,
    }
