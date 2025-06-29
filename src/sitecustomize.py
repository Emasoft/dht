#!/usr/bin/env python3
"""
Site customization module for DHT.

This module is automatically imported by Python at startup if it's in the PYTHONPATH.
We use it to apply Prefect 3.x compatibility patches before any other imports.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

# Apply Prefect compatibility patches early
try:
    import DHT.modules.prefect_compat  # noqa: F401
except ImportError:
    # If DHT modules aren't available yet, that's fine
    # The compatibility module will be imported later
    pass
