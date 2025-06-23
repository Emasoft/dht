#!/usr/bin/env python3
"""
Simple test runner with compact output to avoid token limits.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

"""
Simple test runner with compact output to avoid token limits.
"""

import re
import subprocess
import sys
import time


def main() -> None:
    """Run tests with formatted output."""
    args = sys.argv[1:] if len(sys.argv) > 1 else []

    # First, collect test names
    collect_cmd = [sys.executable, "-m", "pytest", "--collect-only", "-q"] + args

    print("Collecting tests...")
    result = subprocess.run(collect_cmd, capture_output=True, text=True)

    # Parse test count from different pytest output formats
    test_count = 0
    lines = result.stdout.split("\n") + result.stderr.split("\n")
    for line in lines:
        # Look for different patterns
        if " selected" in line and " deselected" not in line:
            match = re.search(r"(\d+)\s+selected", line)
            if match:
                test_count = int(match.group(1))
                break
        elif " test" in line and " collected" in line:
            match = re.search(r"collected\s+(\d+)\s+item", line)
            if match:
                test_count = int(match.group(1))
                break

    print(f"Found {test_count} tests")
    print("=" * 80)

    # Now run tests with minimal output
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "-v",  # Need verbose to get test names
        "--tb=line",  # Single line tracebacks
        "--no-header",  # No header
        "--disable-warnings",  # No warnings
    ] + args

    # Run tests and capture output
    start_time = time.time()
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

    # Parse output in real-time
    passed = failed = skipped = 0
    test_results = []
    current_file = ""

    if proc.stdout:
        for line in proc.stdout:
            line = line.strip()

            # Skip empty lines and noise
            if not line or line.startswith("=") or "platform" in line:
                continue

            # Parse test results
            if "::" in line and (" PASSED" in line or " FAILED" in line or " SKIPPED" in line):
                # Extract test info
                parts = line.split("::")
                if len(parts) >= 2:
                    file_path = parts[0].strip()
                    test_parts = parts[1].split(" ")
                    test_name = test_parts[0].strip()

                    # Get status
                    if "PASSED" in line:
                        status = "✅ PASS"
                        passed += 1
                    elif "FAILED" in line:
                        status = "❌ FAIL"
                        failed += 1
                    elif "SKIPPED" in line:
                        status = "⏩ SKIP"
                        skipped += 1
                    else:
                        status = "❓ ???"

                    # Shorten file path
                    short_path = file_path.replace("tests/unit/", "").replace("tests/integration/", "")

                    if short_path != current_file:
                        if current_file:
                            print()  # Blank line between files
                        current_file = short_path
                        print(f"\n📁 {short_path}")
                        print("-" * 80)

                    # Print result
                    print(f"  {test_name:<60} {status}")

                    # Store for summary
                    test_results.append((short_path, test_name, status))

    proc.wait()
    duration = time.time() - start_time

    # Print summary
    print("\n" + "=" * 80)
    print("📊 DHT Test Summary")
    print("=" * 80)
    print(f"Total Tests: {passed + failed + skipped}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"⏩ Skipped: {skipped}")
    print(f"⏱️  Duration: {duration:.2f}s")
    print("=" * 80)

    # If there were failures, save to log
    if failed > 0:
        print("\n⚠️  Run with pytest -v for detailed error messages")

    return


if __name__ == "__main__":
    main()
