#!/usr/bin/env python3
"""
Check command for DHT.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Create check command module for type checking
# - Runs mypy for Python type checking
# - Integrates with Prefect runner
#

"""
Check command for DHT.

Provides type checking functionality using mypy,
separate from the broader lint command.
"""

import logging
import subprocess
from pathlib import Path
from typing import Any, cast

from ..prefect_compat import task

logger = logging.getLogger(__name__)


class CheckCommand:
    """Check command implementation."""

    def __init__(self) -> None:
        """Initialize check command."""
        self.logger = logging.getLogger(__name__)

    @task(
        name="check_command",
        description="Type check Python code",
        tags=["dht", "check", "typecheck", "mypy"],
        retries=1,
        retry_delay_seconds=5,
    )
    def execute(self, path: str = ".", strict: bool = True, **kwargs: Any) -> dict[str, Any]:
        """
        Execute check command for type checking.

        Args:
            path: Path to check (default: current directory)
            strict: Use strict mode
            **kwargs: Additional arguments

        Returns:
            Result dictionary
        """
        project_path = Path(path).resolve()

        if not project_path.exists():
            return {"success": False, "error": f"Path does not exist: {project_path}"}

        self.logger.info(f"Type checking: {project_path}")

        # Build mypy command
        cmd = ["uv", "run", "mypy"]

        if strict:
            cmd.append("--strict")

        # Add common mypy flags
        cmd.extend(
            [
                "--show-error-context",
                "--pretty",
                "--install-types",
                "--non-interactive",
                "--show-error-codes",
                "--show-error-code-links",
                "--no-error-summary",
            ]
        )

        # Add the path to check
        cmd.append(str(project_path))

        # Set column width for better output
        env = {"COLUMNS": "400"}

        try:
            # Execute mypy
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,  # Don't raise on non-zero exit
                timeout=600,  # 10 minutes timeout
                env={**subprocess.os.environ, **env},  # type: ignore[attr-defined]
            )

            # Mypy returns 0 for success, 1 for errors found, 2 for issues
            if result.returncode == 0:
                self.logger.info("Type check passed")
                return {"success": True, "message": "Type check passed", "output": result.stdout}
            elif result.returncode == 1:
                self.logger.warning("Type errors found")
                return {
                    "success": False,
                    "error": "Type errors found",
                    "output": result.stdout,
                    "returncode": result.returncode,
                }
            else:
                self.logger.error(f"Mypy failed with code {result.returncode}")
                return {
                    "success": False,
                    "error": f"Mypy failed with code {result.returncode}",
                    "output": result.stderr or result.stdout,
                    "returncode": result.returncode,
                }

        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Type check timed out after 10 minutes"}
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            return {"success": False, "error": str(e)}


# Module-level function for command registry
def check_command(**kwargs: Any) -> dict[str, Any]:
    """Execute check command."""
    cmd = CheckCommand()
    return cast(dict[str, Any], cmd.execute(**kwargs))
