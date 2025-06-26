#!/usr/bin/env python3
"""
Fmt command for DHT.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Create fmt command module (alias for format)
# - Follows one-command-per-module pattern
# - Integrates with Prefect runner
#

"""
Fmt command for DHT.

This is an alias for the format command, providing familiar syntax
for users coming from other development tools.
"""

import logging
from typing import Any, cast

from prefect import task

logger = logging.getLogger(__name__)


class FmtCommand:
    """Fmt command implementation."""

    def __init__(self) -> None:
        """Initialize fmt command."""
        self.logger = logging.getLogger(__name__)

    @task(
        name="fmt_command",
        description="Format code (alias for format)",
        tags=["dht", "fmt", "format"],
        retries=1,
        retry_delay_seconds=5,
    )
    def execute(self, **kwargs: Any) -> dict[str, Any]:
        """
        Execute fmt command (delegates to format).

        Args:
            **kwargs: Arguments to pass to format command

        Returns:
            Result dictionary
        """
        # Import format command to avoid circular imports
        from ..utils import FormatCommand

        self.logger.info("Running fmt command (delegating to format)")

        # Create format command instance and run it
        format_cmd = FormatCommand()
        result_code = format_cmd.run()

        # Convert result to dictionary format
        success = result_code == 0
        return {
            "success": success,
            "message": "Code formatted successfully" if success else "Formatting failed",
            "return_code": result_code,
        }


# Module-level function for command registry
def fmt_command(**kwargs: Any) -> dict[str, Any]:
    """Execute fmt command."""
    cmd = FmtCommand()
    return cast(dict[str, Any], cmd.execute(**kwargs))
