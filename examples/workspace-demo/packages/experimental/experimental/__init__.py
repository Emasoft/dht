#!/usr/bin/env python3
"""
Demo Experimental Package - Experimental features.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

"""Demo Experimental Package - Experimental features."""

__version__ = "0.0.1"

from .analyzer import analyze
from .benchmark import run as benchmark_run

__all__ = ["analyze", "benchmark_run"]
