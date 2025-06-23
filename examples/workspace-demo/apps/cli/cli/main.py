#!/usr/bin/env python3
"""
CLI application using workspace packages.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

"""CLI application using workspace packages."""

from pathlib import Path
from typing import Any

from core import hello, info
from experimental import analyze, benchmark_run
from utils import format_text, validate


def cli() -> Any:
    """Main CLI entry point."""
    print("🖥️  Demo CLI Application")
    print("=" * 50)

    commands = {
        "1": ("Show core info", info),
        "2": ("Format text", format_text),
        "3": ("Validate data", validate),
        "4": ("Run analysis", analyze),
        "5": ("Run benchmarks", benchmark_run),
        "6": ("Say hello", hello),
    }

    print("\nAvailable commands:")
    for key, (desc, _) in commands.items():
        print(f"  {key}. {desc}")
    print("  q. Quit")

    print(f"\nRunning from: {Path(__file__).parent.parent}")

    while True:
        choice = input("\nSelect command (or 'q' to quit): ").strip().lower()

        if choice == "q":
            print("\n👋 Goodbye!")
            break

        if choice in commands:
            print()
            _, func = commands[choice]
            func()
        else:
            print("❌ Invalid choice. Please try again.")

    return 0


if __name__ == "__main__":
    cli()
