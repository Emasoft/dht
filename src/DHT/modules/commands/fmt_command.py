#!/usr/bin/env python3

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
from typing import Any

from prefect import task

logger = logging.getLogger(__name__)


class FmtCommand:
    """Fmt command implementation."""

    def __init__(self):
        """Initialize fmt command."""
        self.logger = logging.getLogger(__name__)

    @task(
        name="fmt_command",
        description="Format code (alias for format)",
        tags=["dht", "fmt", "format"],
        retries=1,
        retry_delay_seconds=5,
    )
    def execute(self, **kwargs) -> dict[str, Any]:
        """
        Execute fmt command (delegates to format).

        Args:
            **kwargs: Arguments to pass to format command

        Returns:
            Result dictionary
        """
        # Import format command to avoid circular imports
        from ..utils import format_command as format_func

        self.logger.info("Running fmt command (delegating to format)")

        # Delegate to format with same arguments
        return format_func(**kwargs)


# Module-level function for command registry
def fmt_command(**kwargs) -> dict[str, Any]:
    """Execute fmt command."""
    cmd = FmtCommand()
    return cmd.execute(**kwargs)
