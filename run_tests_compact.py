#!/usr/bin/env python3
"""
Compact test runner for DHT - reduces output to avoid token limits.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

"""
Compact test runner for DHT - reduces output to avoid token limits.
"""

import os
import subprocess
import sys
from pathlib import Path


def run_tests_compact(test_path=None, pattern=None):
    """Run tests with minimal output."""
    # Base pytest command
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "-q",  # Quiet
        "--tb=line",  # One line tracebacks
        "--no-header",  # No header
        "--disable-warnings",  # No warnings
        "-v",  # Verbose (to get test names)
        "--co",  # Collect only first
    ]

    # Add test path if specified
    if test_path:
        cmd.append(test_path)

    # Add pattern if specified
    if pattern:
        cmd.extend(["-k", pattern])

    # Set environment to reduce Prefect logging
    env = os.environ.copy()
    env["PREFECT_LOGGING_LEVEL"] = "ERROR"
    env["PYTHONWARNINGS"] = "ignore"

    print("Running tests with compact output...")
    print("-" * 80)

    # Run tests
    result = subprocess.run(cmd, env=env, capture_output=False)

    # Check if error log exists
    error_log = Path("test_errors.log")
    if error_log.exists() and error_log.stat().st_size > 0:
        print(f"\n⚠️  Test errors logged to: {error_log}")
        print("First 10 lines of errors:")
        print("-" * 80)
        with open(error_log) as f:
            for i, line in enumerate(f):
                if i >= 10:
                    print("... (see test_errors.log for full details)")
                    break
                print(line.rstrip())

    return result.returncode


if __name__ == "__main__":
    # Parse simple command line args
    test_path = None
    pattern = None

    args = sys.argv[1:]
    if args:
        if "-k" in args:
            idx = args.index("-k")
            if idx + 1 < len(args):
                pattern = args[idx + 1]
                args = args[:idx] + args[idx + 2 :]

        if args:
            test_path = args[0]

    sys.exit(run_tests_compact(test_path, pattern))
