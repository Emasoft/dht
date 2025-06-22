#!/usr/bin/env python3
"""
uv_manager_script.py - Script execution for UV Manager  This module contains functionality for running Python scripts with UV.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

"""
uv_manager_script.py - Script execution for UV Manager

This module contains functionality for running Python scripts with UV.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Extracted from uv_manager.py to reduce file size
# - Contains script execution functionality
#

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from prefect import task


class ScriptExecutor:
    """Manages script execution for UV."""

    def __init__(self, run_command_func):
        """
        Initialize script executor.

        Args:
            run_command_func: Function to run UV commands
        """
        self.logger = logging.getLogger(__name__)
        self.run_command = run_command_func

    @task
    def run_script(self, project_path: Path, script: str, args: list[str] | None = None) -> dict[str, Any]:
        """
        Run a Python script in the project environment.

        Args:
            project_path: Project root directory
            script: Script to run (file or module)
            args: Additional arguments for the script

        Returns:
            Execution result
        """
        project_path = Path(project_path)

        cmd_args = ["run"]

        if script.endswith(".py"):
            cmd_args.extend(["python", script])
        else:
            cmd_args.extend(["python", "-m", script])

        if args:
            cmd_args.extend(args)

        result = self.run_command(cmd_args, cwd=project_path)

        return {"success": result["success"], "script": script, "output": result["stdout"], "error": result["stderr"]}
