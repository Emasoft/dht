#!/usr/bin/env python3
"""
Validation utilities.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

"""Validation utilities."""

import re
from pathlib import Path


def validate() -> bool:
    """Validate various data formats."""
    print("✅ Validator from demo-utils")
    print("-" * 40)

    # Example validations
    email = "user@example.com"
    phone = "+1-555-123-4567"

    print(f"Email validation for '{email}': ", end="")
    if re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email):
        print("VALID ✓")
    else:
        print("INVALID ✗")

    print(f"Phone validation for '{phone}': ", end="")
    if re.match(r"^\+?[\d\s\-\(\)]+$", phone):
        print("VALID ✓")
    else:
        print("INVALID ✗")

    print(f"\nRunning from: {Path(__file__).parent.parent}")
    return False


if __name__ == "__main__":
    validate()
