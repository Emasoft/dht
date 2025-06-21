#!/usr/bin/env python3
"""
Quiet test runner that produces minimal output to avoid token limits.
"""

import os
import re
import subprocess
import sys
from collections import defaultdict


def main():
    """Run tests with compact table output."""
    args = sys.argv[1:] if len(sys.argv) > 1 else []

    # Set quiet environment
    env = os.environ.copy()
    env["PREFECT_LOGGING_LEVEL"] = "ERROR"
    env["PYTHONWARNINGS"] = "ignore"

    # Run pytest with custom output processing
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "-v",  # Need verbose to get test names
        "--tb=no",  # No tracebacks
        "--no-header",  # No header
        "--disable-warnings",  # No warnings
        "--color=no",  # No color codes
    ] + args

    print("Running tests...")
    print("=" * 80)

    # Run and capture output
    proc = subprocess.run(cmd, capture_output=True, text=True, env=env)

    # Parse output
    results = defaultdict(list)
    current_file = ""
    passed = failed = skipped = 0

    # Process stdout and stderr
    all_output = proc.stdout + "\n" + proc.stderr

    for line in all_output.split("\n"):
        # Skip empty lines and prefect logs
        if not line.strip() or "prefect" in line.lower() or "INFO" in line or "ERROR" in line:
            continue

        # Match test result lines
        if " PASSED" in line or " FAILED" in line or " SKIPPED" in line:
            # Extract test info
            match = re.match(r"(.*?)::(.*?)\s+(PASSED|FAILED|SKIPPED)", line)
            if match:
                file_path = match.group(1).strip()
                test_name = match.group(2).strip()
                status = match.group(3).strip()

                # Shorten path
                if "tests/unit/" in file_path:
                    file_path = file_path.split("tests/unit/")[1]
                elif "tests/integration/" in file_path:
                    file_path = file_path.split("tests/integration/")[1]

                # Count results
                if status == "PASSED":
                    passed += 1
                    status_symbol = "✅"
                elif status == "FAILED":
                    failed += 1
                    status_symbol = "❌"
                else:
                    skipped += 1
                    status_symbol = "⏩"

                results[file_path].append((test_name, status_symbol))

    # Print results table
    if results:
        print(f"\n{'File':<50} {'Test':<50} {'Status':<10}")
        print("-" * 110)

        for file_path in sorted(results.keys()):
            for test_name, status in results[file_path]:
                # Truncate long names
                if len(test_name) > 48:
                    test_name = test_name[:45] + "..."
                print(f"{file_path:<50} {test_name:<50} {status:<10}")

    # Summary
    total = passed + failed + skipped
    print("\n" + "=" * 80)
    print("📊 Test Summary")
    print("=" * 80)
    print(f"Total: {total} | ✅ Pass: {passed} | ❌ Fail: {failed} | ⏩ Skip: {skipped}")

    if failed > 0:
        print("\n⚠️  Run pytest with -v --tb=short for error details")

    return proc.returncode


if __name__ == "__main__":
    sys.exit(main())
