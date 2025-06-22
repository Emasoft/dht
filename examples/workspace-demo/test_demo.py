#!/usr/bin/env python3
"""
Test script to verify workspace demo functionality.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

"""Test script to verify workspace demo functionality."""

import sys
from pathlib import Path

# Add packages to path for testing
packages_dir = Path(__file__).parent / "packages"
for pkg in ["core", "utils", "experimental"]:
    sys.path.insert(0, str(packages_dir / pkg))

# Test imports
try:
    from core import hello, info
    from experimental import analyze, benchmark_run
    from utils import format_text, validate

    print("✅ All package imports successful!")
    # Show that all imports worked (to satisfy ruff)
    all_funcs = [hello, info, analyze, benchmark_run, format_text, validate]
    print(f"  - Imported {len(all_funcs)} functions successfully")

    # Test functions
    print("\n1. Testing core.hello():")
    hello()

    print("\n2. Testing utils.validate():")
    validate()

    print("\n3. Testing cross-package dependencies:")
    format_text()  # This calls core.hello internally

    print("\n✅ All tests passed! The workspace is properly configured.")

except ImportError as e:
    print(f"❌ Import error: {e}")
    print("\nMake sure to run 'dhtl setup' first to install dependencies.")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
