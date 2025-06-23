#!/usr/bin/env python3
"""
Core module main functionality.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

"""Core module main functionality."""

import sys
from pathlib import Path


def hello() -> str:
    """Simple hello world function."""
    print("🎯 Hello from demo-core package!")
    print(f"Running from: {Path(__file__).parent.parent}")
    return "Hello"


def info() -> None:
    """Display information about the core package."""
    print("📦 Demo Core Package Information")
    print("=" * 40)
    print(f"Python Version: {sys.version.split()[0]}")
    print(f"Package Location: {Path(__file__).parent.parent}")
    print(f"Module: {__name__}")
    print("Features:")
    print("  - Basic hello world functionality")
    print("  - Package information display")
    print("  - Foundation for other packages")
    return 0


if __name__ == "__main__":
    hello()
