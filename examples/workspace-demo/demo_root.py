#!/usr/bin/env python3
"""
Root project demo script.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

"""Root project demo script."""

from pathlib import Path


def main():
    """Main function for root project demonstration."""
    print("🏠 Demo Root Project")
    print("=" * 40)

    print("\nThis is the root workspace project.")
    print("It orchestrates all workspace members:")
    print("  - packages/core")
    print("  - packages/utils")
    print("  - packages/experimental")
    print("  - apps/web")
    print("  - apps/cli")

    print(f"\nRoot location: {Path(__file__).parent}")
    print("\nUse workspace commands to run scripts across members!")

    return 0


if __name__ == "__main__":
    main()
