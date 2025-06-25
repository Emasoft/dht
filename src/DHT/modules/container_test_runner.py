#!/usr/bin/env python3
"""
Container Test Runner Module.  Executes tests within Docker containers and formats results for pytest, Playwright, and Puppeteer test frameworks.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

"""
Container Test Runner Module.

Executes tests within Docker containers and formats results
for pytest, Playwright, and Puppeteer test frameworks.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Initial implementation of ContainerTestRunner class
# - Implements test execution for pytest, Playwright, and Puppeteer
# - Implements result parsing and formatting
# - Adds table formatting for test results
# - Adds support for coverage reporting
#

import logging
import re
from enum import Enum
from pathlib import Path
from typing import Any

from prefect import task
from tabulate import tabulate

from .docker_manager import DockerError, DockerManager


class TestFramework(Enum):
    """Enumeration of supported test frameworks."""

    PYTEST = "pytest"
    PLAYWRIGHT = "playwright"
    PUPPETEER = "puppeteer"


class ContainerTestRunner:
    """Runs tests in Docker containers and formats results."""

    def __init__(self) -> None:
        """Initialize ContainerTestRunner."""
        self.logger = logging.getLogger(__name__)
        self.docker_manager = DockerManager()

    @task  # type: ignore[misc]
    def run_all_tests(self, container_name: str, frameworks: list[TestFramework] | None = None) -> dict[str, Any]:
        """
        Run all tests in container.

        Args:
            container_name: Name of container to run tests in
            frameworks: List of frameworks to test with

        Returns:
            Combined test results
        """
        if frameworks is None:
            frameworks = [TestFramework.PYTEST]  # Default to pytest

        all_results = {}

        for framework in frameworks:
            self.logger.info(f"Running {framework.value} tests...")

            if framework == TestFramework.PYTEST:
                results = self.run_pytest(container_name)
            elif framework == TestFramework.PLAYWRIGHT:
                results = self.run_playwright(container_name)
            elif framework == TestFramework.PUPPETEER:
                results = self.run_puppeteer(container_name)
            else:
                self.logger.warning(f"Unknown framework: {framework}")
                continue
            all_results[framework.value] = results

        return all_results

    @task  # type: ignore[misc]
    def run_pytest(
        self, container_name: str, test_path: str | None = None, verbose: bool = True, coverage: bool = True
    ) -> dict[str, Any]:
        """
        Run pytest in container.

        Args:
            container_name: Container name
            test_path: Specific test path
            verbose: Verbose output
            coverage: Run with coverage

        Returns:
            Test results
        """
        # Build pytest command
        cmd = ["uv", "run", "pytest"]

        if verbose:
            cmd.append("-v")

        cmd.extend(["--tb=short", "--color=yes"])

        if coverage:
            cmd.extend(["--cov=.", "--cov-report=term-missing"])

        if test_path:
            cmd.append(test_path)

        try:
            # Execute pytest
            exit_code, output = self.docker_manager.exec_command(container_name, cmd, workdir="/app")

            # Parse results
            results = self._parse_pytest_output(output)
            results["exit_code"] = exit_code

            if exit_code != 0 and "error" not in results:
                results["error_output"] = output

            return results

        except DockerError as e:
            self.logger.error(f"Failed to run pytest: {e}")
            return {"error": str(e), "exit_code": 1, "total": 0, "passed": 0, "failed": 0, "skipped": 0}

    @task  # type: ignore[misc]
    def run_playwright(
        self, container_name: str, test_path: str | None = None, browser: str = "chromium"
    ) -> dict[str, Any]:
        """
        Run Playwright tests in container.

        Args:
            container_name: Container name
            test_path: Specific test path
            browser: Browser to use

        Returns:
            Test results
        """
        try:
            # First install browsers if needed
            self.logger.info("Installing Playwright browsers...")
            exit_code, output = self.docker_manager.exec_command(
                container_name, ["uv", "run", "playwright", "install", browser], workdir="/app"
            )

            if exit_code != 0:
                self.logger.warning(f"Browser installation failed: {output}")

            # Run Playwright tests
            cmd = ["uv", "run", "pytest"]

            if test_path:
                cmd.append(test_path)
            else:
                # Default to e2e test directory
                cmd.extend(["tests/e2e", "-v"])

            # Add Playwright specific options
            cmd.extend(["--browser", browser])

            exit_code, output = self.docker_manager.exec_command(container_name, cmd, workdir="/app")

            # Parse results
            results = self._parse_playwright_output(output)
            results["exit_code"] = exit_code
            results["browser"] = browser

            return results

        except DockerError as e:
            self.logger.error(f"Failed to run Playwright: {e}")
            return {"error": str(e), "exit_code": 1, "total": 0, "passed": 0, "failed": 0, "browser": browser}

    @task  # type: ignore[misc]
    def run_puppeteer(self, container_name: str, test_path: str | None = None) -> dict[str, Any]:
        """
        Run Puppeteer tests in container.

        Args:
            container_name: Container name
            test_path: Specific test path

        Returns:
            Test results
        """
        try:
            # Run Puppeteer tests
            cmd = ["uv", "run", "python", "-m", "pytest"]

            if test_path:
                cmd.append(test_path)
            else:
                # Default to puppeteer test directory
                cmd.extend(["tests/puppeteer", "-v"])

            exit_code, output = self.docker_manager.exec_command(
                container_name, cmd, workdir="/app", environment={"PUPPETEER_SKIP_CHROMIUM_DOWNLOAD": "true"}
            )

            # Parse results
            results = self._parse_pytest_output(output)  # Puppeteer uses pytest
            results["exit_code"] = exit_code
            results["framework"] = "puppeteer"

            return results

        except DockerError as e:
            self.logger.error(f"Failed to run Puppeteer: {e}")
            return {"error": str(e), "exit_code": 1, "total": 0, "passed": 0, "failed": 0, "framework": "puppeteer"}

    def _parse_pytest_output(self, output: str) -> dict[str, Any]:
        """Parse pytest output to extract results."""
        results = {"total": 0, "passed": 0, "failed": 0, "skipped": 0, "errors": 0, "tests": {}, "coverage": None}

        # Parse test results
        # Look for summary line like "3 passed, 1 failed, 1 skipped"
        summary_pattern = r"(\d+)\s+passed|(\d+)\s+failed|(\d+)\s+skipped|(\d+)\s+error"

        for match in re.finditer(summary_pattern, output):
            if match.group(1):  # passed
                results["passed"] = int(match.group(1))
            elif match.group(2):  # failed
                results["failed"] = int(match.group(2))
            elif match.group(3):  # skipped
                results["skipped"] = int(match.group(3))
            elif match.group(4):  # errors
                results["errors"] = int(match.group(4))

        total = int(results.get("passed", 0)) + int(results.get("failed", 0)) + int(results.get("skipped", 0)) + int(results.get("errors", 0))
        results["total"] = total

        # Parse individual test results
        test_pattern = r"([\w/]+\.py)::([\w_]+)(?:\[[\w-]+\])?\s+(PASSED|FAILED|SKIPPED|ERROR)"

        for match in re.finditer(test_pattern, output):
            test_file = match.group(1)
            test_name = match.group(2)
            status = match.group(3).lower()

            test_key = f"{test_file}::{test_name}"
            if "tests" not in results:
                results["tests"] = {}
            results["tests"][test_name] = status

        # Parse coverage if present
        coverage_pattern = r"TOTAL\s+\d+\s+\d+\s+(\d+%)"
        coverage_match = re.search(coverage_pattern, output)
        if coverage_match:
            results["coverage"] = coverage_match.group(1)

        return results

    def _parse_playwright_output(self, output: str) -> dict[str, Any]:
        """Parse Playwright test output."""
        # Playwright output format may vary
        # Try to parse pytest-style output first
        results = self._parse_pytest_output(output)

        # Also look for Playwright specific patterns
        # "3 passed (5.2s)"
        pw_pattern = r"(\d+)\s+passed\s*\([\d.]+s\)"
        pw_match = re.search(pw_pattern, output)

        if pw_match and results["total"] == 0:
            results["passed"] = int(pw_match.group(1))
            results["total"] = results["passed"]

        return results

    def format_results_table(self, all_results: dict[TestFramework, dict[str, Any]]) -> str:
        """
        Format test results as a nice table.

        Args:
            all_results: Results from all test frameworks

        Returns:
            Formatted table string
        """
        # Prepare data for table
        table_data = []

        framework_names = {
            TestFramework.PYTEST: "Unit Tests (pytest)",
            TestFramework.PLAYWRIGHT: "E2E Tests (Playwright)",
            TestFramework.PUPPETEER: "UI Tests (Puppeteer)",
        }

        for framework, results in all_results.items():
            if "error" in results:
                row = [
                    framework_names.get(framework, framework.value),
                    "ERROR",
                    "-",
                    "-",
                    results.get("error", "Unknown error")[:50],
                ]
            else:
                row = [
                    framework_names.get(framework, framework.value),
                    results.get("total", 0),
                    results.get("passed", 0),
                    results.get("failed", 0),
                    results.get("skipped", 0),
                ]

            table_data.append(row)

        # Add total row
        total_tests = sum(r.get("total", 0) for r in all_results.values() if "error" not in r)
        total_passed = sum(r.get("passed", 0) for r in all_results.values() if "error" not in r)
        total_failed = sum(r.get("failed", 0) for r in all_results.values() if "error" not in r)
        total_skipped = sum(r.get("skipped", 0) for r in all_results.values() if "error" not in r)

        table_data.append(["─" * 25, "─" * 7, "─" * 8, "─" * 8, "─" * 8])
        table_data.append(["TOTAL", total_tests, total_passed, total_failed, total_skipped])

        # Format as table
        headers = ["Test Suite", "Total", "Passed", "Failed", "Skipped"]
        table = tabulate(table_data, headers=headers, tablefmt="grid", numalign="right", stralign="left")

        # Add emoji indicators
        if total_failed > 0:
            status = "❌ Tests Failed"
        elif total_tests == 0:
            status = "⚠️  No Tests Found"
        else:
            status = "✅ All Tests Passed"

        # Add coverage info if available
        coverage_info = ""
        for framework, results in all_results.items():
            if results.get("coverage"):
                coverage_info += f"\n📊 Coverage ({framework.value}): {results['coverage']}"

        return f"\n{status}\n\n{table}{coverage_info}\n"

    def format_detailed_results(self, all_results: dict[TestFramework, dict[str, Any]]) -> str:
        """
        Format detailed test results.

        Args:
            all_results: Results from all test frameworks

        Returns:
            Detailed results string
        """
        output = []

        for framework, results in all_results.items():
            output.append(f"\n{'=' * 60}")
            output.append(f"{framework.value.upper()} RESULTS")
            output.append(f"{'=' * 60}")

            if "error" in results:
                output.append(f"❌ ERROR: {results['error']}")
                if "error_output" in results:
                    output.append("\nError Output:")
                    output.append(results["error_output"][:500])  # Limit output
            else:
                # Summary
                output.append(f"Total: {results.get('total', 0)}")
                output.append(f"Passed: {results.get('passed', 0)} ✅")
                output.append(f"Failed: {results.get('failed', 0)} ❌")
                output.append(f"Skipped: {results.get('skipped', 0)} ⏩")

                if results.get("coverage"):
                    output.append(f"Coverage: {results['coverage']} 📊")

                # Failed tests
                if results.get("tests"):
                    failed_tests = [name for name, status in results["tests"].items() if status == "failed"]

                    if failed_tests:
                        output.append("\nFailed Tests:")
                        for test in failed_tests[:10]:  # Limit to 10
                            output.append(f"  - {test}")

                        if len(failed_tests) > 10:
                            output.append(f"  ... and {len(failed_tests) - 10} more")

        return "\n".join(output)

    def save_results(self, all_results: dict[TestFramework, dict[str, Any]], output_path: Path) -> None:
        """
        Save test results to file.

        Args:
            all_results: Test results
            output_path: Path to save results
        """
        import json

        # Convert enum keys to strings for JSON serialization
        json_results = {framework.value: results for framework, results in all_results.items()}

        with open(output_path, "w") as f:
            json.dump(json_results, f, indent=2)

        self.logger.info(f"Test results saved to: {output_path}")
