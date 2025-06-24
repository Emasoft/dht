#!/usr/bin/env python3
"""
Run all tests and generate a comprehensive summary.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

"""Run all tests and generate a comprehensive summary."""

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


def run_pytest_json(test_path: str | Path) -> dict[str, Any] | None:
    """Run pytest and get JSON output."""
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        test_path,
        "--json-report",
        "--json-report-file=/tmp/pytest_report.json",
        "--tb=short",
        "-v",
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    # Try to load JSON report
    try:
        with open("/tmp/pytest_report.json") as f:
            return json.load(f)  # type: ignore[no-any-return]
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def run_tests_summary() -> int:
    """Run all tests and generate summary."""
    test_dir = Path("DHT/tests/unit")

    # Run pytest with simple output
    cmd = [sys.executable, "-m", "pytest", str(test_dir), "-v", "--tb=short", "-q"]

    print("Running all unit tests...")
    result = subprocess.run(cmd, capture_output=True, text=True)

    # Parse output
    lines = result.stdout.split("\n")

    # Extract summary
    passed = 0
    failed = 0
    errors = 0
    skipped = 0

    for line in lines:
        if " passed" in line and " failed" in line:
            parts = line.split()
            for i, part in enumerate(parts):
                if part == "passed":
                    passed = int(parts[i - 1])
                elif part == "failed":
                    failed = int(parts[i - 1])
                elif part == "error" or part == "errors":
                    errors = int(parts[i - 1])
                elif part == "skipped":
                    skipped = int(parts[i - 1])

    # Print detailed summary
    print("\n" + "=" * 80)
    print("DHT TEST RESULTS SUMMARY")
    print("=" * 80)
    print(f"\nTotal Tests Run: {passed + failed + errors + skipped}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"🚫 Errors: {errors}")
    print(f"⏩ Skipped: {skipped}")

    # Extract failed tests
    if failed > 0 or errors > 0:
        print("\n" + "-" * 80)
        print("FAILED/ERROR TESTS:")
        print("-" * 80)

        in_failed_section = False
        for line in lines:
            if "FAILED" in line or "ERROR" in line:
                if "::" in line:
                    print(f"  • {line.strip()}")

    # Show import errors
    if "ImportError" in result.stdout or "ModuleNotFoundError" in result.stdout:
        print("\n" + "-" * 80)
        print("IMPORT ISSUES:")
        print("-" * 80)

        for line in lines:
            if "ImportError" in line or "ModuleNotFoundError" in line:
                print(f"  • {line.strip()}")

    print("\n" + "=" * 80)

    # Return exit code
    return 0 if failed == 0 and errors == 0 else 1


if __name__ == "__main__":
    sys.exit(run_tests_summary())
