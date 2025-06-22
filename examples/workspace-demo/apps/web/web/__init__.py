#!/usr/bin/env python3
"""
Demo Web Application.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

"""Demo Web Application."""

__version__ = "0.1.0"

from .app import dev_server, serve

__all__ = ["serve", "dev_server"]
