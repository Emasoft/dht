#!/usr/bin/env python3
"""
Experimental benchmark module.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

"""Experimental benchmark module."""

import time
from pathlib import Path


def run():
    """Run performance benchmarks."""
    print("⚡ Experimental Benchmark Suite")
    print("=" * 40)

    benchmarks = [
        ("String concatenation", lambda: "".join(["a"] * 1000)),
        ("List comprehension", lambda: [i**2 for i in range(1000)]),
        ("Dictionary creation", lambda: {i: i**2 for i in range(100)}),
    ]

    for name, func in benchmarks:
        start = time.perf_counter()
        func()
        elapsed = time.perf_counter() - start
        print(f"{name}: {elapsed * 1000:.3f}ms")

    print(f"\nRunning from: {Path(__file__).parent.parent}")
    print("\n🏁 Benchmarks complete!")
    return 0


if __name__ == "__main__":
    run()
