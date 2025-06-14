#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Custom pytest plugin for concise test reporting.
"""

import pytest
from typing import Dict, List, Tuple
from collections import defaultdict


class TestSummaryReporter:
    """Collects test results for summary table."""
    
    def __init__(self):
        self.results: Dict[str, List[Tuple[str, str, float]]] = defaultdict(list)
        self.errors: Dict[str, str] = {}
    
    def add_result(self, nodeid: str, outcome: str, duration: float, error: str = None):
        """Add a test result."""
        # Parse nodeid to get file and test name
        parts = nodeid.split("::")
        if len(parts) >= 2:
            file_path = parts[0]
            test_name = "::".join(parts[1:])
        else:
            file_path = nodeid
            test_name = "unknown"
        
        self.results[file_path].append((test_name, outcome, duration))
        if error:
            self.errors[nodeid] = error
    
    def print_summary(self):
        """Print summary table."""
        print("\n" + "="*100)
        print("📊 DHT Test Summary")
        print("="*100)
        
        # Summary stats
        total = passed = failed = skipped = 0
        
        # Detailed table header
        print(f"\n{'File':<50} {'Test':<40} {'Status':<10} {'Time':<10}")
        print("-" * 100)
        
        for file_path, tests in sorted(self.results.items()):
            # Shorten file path for display
            short_path = file_path.replace("tests/unit/", "").replace("tests/integration/", "")
            
            for test_name, outcome, duration in tests:
                # Count outcomes
                total += 1
                if outcome == "passed":
                    passed += 1
                    status = "✅ PASS"
                elif outcome == "failed":
                    failed += 1
                    status = "❌ FAIL"
                elif outcome == "skipped":
                    skipped += 1
                    status = "⏩ SKIP"
                else:
                    status = f"❓ {outcome}"
                
                # Format duration
                time_str = f"{duration:.2f}s" if duration < 10 else f"{duration:.1f}s"
                
                # Print row
                print(f"{short_path:<50} {test_name:<40} {status:<10} {time_str:<10}")
        
        # Summary
        print("-" * 100)
        print(f"Total Tests: {total}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"⏩ Skipped: {skipped}")
        print("="*100)
        
        # Write errors to log file
        if self.errors:
            with open("test_errors.log", "w") as f:
                f.write("TEST ERRORS LOG\n")
                f.write("=" * 80 + "\n\n")
                for nodeid, error in self.errors.items():
                    f.write(f"Test: {nodeid}\n")
                    f.write("-" * 80 + "\n")
                    f.write(error)
                    f.write("\n\n")
            print(f"\n⚠️  Detailed errors written to: test_errors.log")


# Global reporter instance
reporter = TestSummaryReporter()


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Hook to capture test results."""
    outcome = yield
    report = outcome.get_result()
    
    if report.when == "call":
        # Get test nodeid and outcome
        nodeid = report.nodeid
        outcome_str = report.outcome
        duration = report.duration
        
        # Capture error details
        error = None
        if report.failed:
            error = str(report.longrepr)
        
        reporter.add_result(nodeid, outcome_str, duration, error)


def pytest_sessionfinish(session, exitstatus):
    """Print summary at end of session."""
    reporter.print_summary()


# Pytest configuration options
def pytest_addoption(parser):
    """Add custom options."""
    parser.addoption(
        "--quiet-summary",
        action="store_true",
        default=False,
        help="Show only summary table without verbose output"
    )


def pytest_configure(config):
    """Configure pytest."""
    # Register our plugin
    config.pluginmanager.register(reporter, "test_summary_reporter")
    
    # Set quiet options if requested
    if config.getoption("--quiet-summary"):
        config.option.verbose = 0
        config.option.tb = "short"