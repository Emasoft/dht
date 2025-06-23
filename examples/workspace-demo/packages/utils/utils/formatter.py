#!/usr/bin/env python3
"""
Text formatting utilities.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

"""Text formatting utilities."""

from pathlib import Path

from core import hello as core_hello


def format_text() -> int:
    """Format text with various styles."""
    print("🎨 Text Formatter from demo-utils")
    print("-" * 40)

    # Show integration with core
    print("\nCalling core functionality:")
    core_hello()

    print("\nFormatting examples:")
    print("  UPPERCASE: HELLO WORLD")
    print("  lowercase: hello world")
    print("  Title Case: Hello World")
    print("  snake_case: hello_world")
    print("  kebab-case: hello-world")

    print(f"\nRunning from: {Path(__file__).parent.parent}")
    return 0


if __name__ == "__main__":
    format_text()
