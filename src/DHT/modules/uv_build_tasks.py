#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
uv_build_tasks.py - Build tasks for UV

This module contains Prefect tasks for building Python projects with UV.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Extracted from uv_prefect_tasks.py to reduce file size
# - Contains project build tasks
#

from __future__ import annotations

from pathlib import Path
from typing import Dict, Any, Optional

from prefect import task

from DHT.modules.guardian_prefect import run_with_guardian, ResourceLimits
from DHT.modules.uv_task_models import (
    BUILD_TIMEOUT, RETRY_DELAYS, UV_MEMORY_LIMITS,
    UVTaskError
)
from DHT.modules.uv_task_utils import get_logger, find_uv_executable


@task(
    name="build_project",
    description="Build Python project",
    retries=2,
    retry_delay_seconds=RETRY_DELAYS,
)
def build_project(
    project_path: Path,
    output_dir: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Build Python project using UV.
    
    Args:
        project_path: Project root directory
        output_dir: Output directory for built artifacts
        
    Returns:
        Build result information
    """
    logger = get_logger()
    
    uv_path = find_uv_executable()
    if not uv_path:
        raise UVTaskError("UV not found")
    
    project_path = Path(project_path)
    
    args = [str(uv_path), "build"]
    
    if output_dir:
        args.extend(["--out-dir", str(output_dir)])
    
    result = run_with_guardian(
        command=args,
        limits=ResourceLimits(memory_mb=UV_MEMORY_LIMITS["build_project"], timeout=BUILD_TIMEOUT),
        cwd=str(project_path)
    )
    
    # Determine output directory
    build_dir = output_dir or project_path / "dist"
    
    return {
        "success": result.return_code == 0,
        "output": result.stdout if result.return_code == 0 else result.stderr,
        "artifacts": [str(f) for f in build_dir.glob("*")] if result.return_code == 0 else []
    }