#!/usr/bin/env python3
"""
Pytest configuration to reduce output verbosity.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

"""
Pytest configuration to reduce output verbosity.
"""

import logging
import os
import warnings

# Reduce all logging to ERROR level
logging.getLogger().setLevel(logging.ERROR)
logging.getLogger("prefect").setLevel(logging.ERROR)
logging.getLogger("prefect.flow_runs").setLevel(logging.ERROR)
logging.getLogger("prefect.task_runs").setLevel(logging.ERROR)
logging.getLogger("prefect.engine").setLevel(logging.ERROR)
logging.getLogger("httpx").setLevel(logging.ERROR)
logging.getLogger("httpcore").setLevel(logging.ERROR)

# Disable warnings
warnings.filterwarnings("ignore")

# Set environment variables to reduce verbosity
os.environ["PREFECT_LOGGING_LEVEL"] = "ERROR"
os.environ["PREFECT_LOGGING_TO_API_ENABLED"] = "False"
os.environ["PREFECT_API_REQUEST_TIMEOUT"] = "30"
os.environ["PYTHONWARNINGS"] = "ignore"


# Pytest hooks to reduce output
def pytest_configure(config):
    """Configure pytest for minimal output."""
    # Override verbosity settings
    config.option.verbose = -1  # Minimal verbosity
    config.option.tb = "no"  # No tracebacks
    config.option.showlocals = False
    config.option.showcapture = "no"

    # Disable output capturing to reduce memory usage
    config.option.capture = "no"


def pytest_collection_modifyitems(session, config, items):
    """Modify test collection to add markers."""
    # Mark all tests as no-capture to reduce output
    for item in items:
        item.add_marker("no_capture")


# Hook to suppress output from specific tests
def pytest_runtest_setup(item):
    """Setup test to minimize output."""
    # Suppress stdout/stderr for all tests
    if hasattr(item, "capfd"):
        item.capfd = None
