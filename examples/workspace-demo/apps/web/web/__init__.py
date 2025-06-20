#!/usr/bin/env python3
"""Demo Web Application."""

__version__ = "0.1.0"

from .app import dev_server, serve

__all__ = ["serve", "dev_server"]
