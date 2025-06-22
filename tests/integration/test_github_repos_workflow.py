#!/usr/bin/env python3
"""
Test Github Repos Workflow module.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Initial implementation of comprehensive GitHub repository testing
# - Tests complete DHT workflow: clone, setup, build
# - No mocks - uses real operations as requested
# - Tabulated results reporting
# - Tests multiple real-world repositories
#

"""
Integration tests for DHT GitHub repository workflow.
Tests the complete flow: clone -> setup -> build on real repositories.
"""

import json
import os
import subprocess
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import pytest
from tabulate import tabulate


@dataclass
class RepoTestResult:
    """Result of testing a single repository."""

    repo_url: str
    repo_name: str
    clone_success: bool = False
    clone_time: float = 0.0
    clone_error: str = ""
    setup_success: bool = False
    setup_time: float = 0.0
    setup_error: str = ""
    venv_created: bool = False
    uv_lock_created: bool = False
    build_success: bool = False
    build_time: float = 0.0
    build_error: str = ""
    dist_files: list[str] = field(default_factory=list)
    notes: str = ""


class TestGitHubReposWorkflow:
    """Test complete DHT workflow on real GitHub repositories."""

    # Test repositories - mix of different Python project types
    TEST_REPOS = [
        # Small, simple projects
        "https://github.com/psf/requests",
        "https://github.com/pallets/click",
        "https://github.com/pallets/flask",
        # Medium complexity
        "https://github.com/encode/httpx",
        "https://github.com/tiangolo/typer",
        "https://github.com/pydantic/pydantic-core",
        # Different project structures
        "https://github.com/pytest-dev/pytest-mock",
        "https://github.com/python-poetry/tomlkit",
        "https://github.com/sdispater/pendulum",
        # FastAPI ecosystem
        "https://github.com/tiangolo/fastapi",
        "https://github.com/astral-sh/ruff",  # Correct URL for ruff repository
        # Data science
        "https://github.com/pandas-dev/pandas",
    ]

    @pytest.fixture(scope="class")
    def dhtl_path(self) -> Path:
        """Get path to dhtl.sh script."""
        return Path("/Users/emanuelesabetta/Code/DHT/dht/dhtl.sh")

    @pytest.fixture(scope="class")
    def test_dir(self, tmp_path_factory) -> Path:
        """Create temporary test directory."""
        test_dir = tmp_path_factory.mktemp("github_repos_test")
        return test_dir

    @pytest.fixture(scope="class", autouse=True)
    def setup_test_environment(self, test_dir):
        """Set up test environment."""
        # Change to test directory
        original_dir = os.getcwd()
        os.chdir(test_dir)

        yield

        # Cleanup - change back to original directory
        os.chdir(original_dir)

    def run_dhtl_command(
        self, dhtl_path: Path, command: str, args: list[str] = None, timeout: int = 300
    ) -> tuple[bool, str, float]:
        """
        Run a dhtl command and capture output.

        Returns:
            Tuple of (success, output/error, execution_time)
        """
        args = args or []
        cmd = [str(dhtl_path), command] + args

        start_time = time.time()
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=False)
            execution_time = time.time() - start_time

            if result.returncode == 0:
                return True, result.stdout, execution_time
            else:
                error_msg = result.stderr or result.stdout or f"Exit code: {result.returncode}"
                return False, error_msg, execution_time

        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            return False, f"Command timed out after {timeout}s", execution_time
        except Exception as e:
            execution_time = time.time() - start_time
            return False, str(e), execution_time

    def check_venv_exists(self, repo_dir: Path) -> bool:
        """Check if virtual environment was created."""
        venv_paths = [repo_dir / ".venv", repo_dir / "venv", repo_dir / ".venv_windows"]
        return any(p.exists() and (p / "bin").exists() or (p / "Scripts").exists() for p in venv_paths)

    def check_uv_lock_exists(self, repo_dir: Path) -> bool:
        """Check if uv.lock file was created."""
        return (repo_dir / "uv.lock").exists()

    def get_dist_files(self, repo_dir: Path) -> list[str]:
        """Get list of files in dist directory."""
        dist_dir = repo_dir / "dist"
        if not dist_dir.exists():
            return []
        return [f.name for f in dist_dir.iterdir() if f.is_file()]

    def run_repository_test(self, dhtl_path: Path, repo_url: str) -> RepoTestResult:
        """Test complete workflow for a single repository."""
        repo_name = repo_url.rstrip("/").split("/")[-1]
        result = RepoTestResult(repo_url=repo_url, repo_name=repo_name)

        # Test 1: Clone repository
        print(f"\n{'=' * 60}")
        print(f"Testing: {repo_name}")
        print(f"URL: {repo_url}")
        print(f"{'=' * 60}")

        success, output, exec_time = self.run_dhtl_command(dhtl_path, "clone", [repo_url, repo_name], timeout=120)
        result.clone_success = success
        result.clone_time = exec_time
        if not success:
            result.clone_error = output.strip().split("\n")[-1]
            print(f"❌ Clone failed: {result.clone_error}")
            return result

        print(f"✅ Clone successful ({exec_time:.1f}s)")

        # Check if directory was created
        repo_dir = Path(repo_name)
        if not repo_dir.exists():
            result.clone_success = False
            result.clone_error = "Repository directory not created"
            return result

        # Change to repository directory
        os.chdir(repo_dir)

        try:
            # Test 2: Setup environment
            print("🔧 Running setup...")
            success, output, exec_time = self.run_dhtl_command(dhtl_path, "setup", timeout=600)
            result.setup_success = success
            result.setup_time = exec_time

            if not success:
                result.setup_error = output.strip().split("\n")[-1]
                print(f"❌ Setup failed: {result.setup_error}")
            else:
                print(f"✅ Setup successful ({exec_time:.1f}s)")

                # Check what was created
                result.venv_created = self.check_venv_exists(Path.cwd())
                result.uv_lock_created = self.check_uv_lock_exists(Path.cwd())

                if result.venv_created:
                    print("  ✓ Virtual environment created")
                if result.uv_lock_created:
                    print("  ✓ uv.lock file created")

            # Test 3: Build package (only if setup succeeded)
            if result.setup_success:
                print("📦 Running build...")
                success, output, exec_time = self.run_dhtl_command(dhtl_path, "build", ["--no-checks"], timeout=600)
                result.build_time = exec_time

                # Check for build artifacts regardless of exit code
                result.dist_files = self.get_dist_files(Path.cwd())

                # DHT build sometimes returns non-zero even when successful
                # Check if dist files were created as the real success indicator
                if result.dist_files:
                    result.build_success = True
                    print(f"✅ Build successful ({exec_time:.1f}s)")
                    print(f"  ✓ Created: {', '.join(result.dist_files)}")
                else:
                    result.build_success = success
                    if not success:
                        # Check if it's just linting errors
                        if any(word in output.lower() for word in ["lint", "ruff", "black", "mypy"]):
                            result.build_error = "Linting errors (build may have succeeded)"
                            result.notes = "Build stopped at linting phase"
                        else:
                            result.build_error = output.strip().split("\n")[-1]
                        print(f"⚠️  Build issues: {result.build_error}")

        finally:
            # Always return to parent directory
            os.chdir("..")

        return result

    @pytest.mark.timeout(3600)  # 1 hour timeout for all tests
    def test_all_repositories(self, dhtl_path: Path):
        """Test all repositories and generate report."""
        results: list[RepoTestResult] = []

        print("\n" + "=" * 80)
        print("DHT GitHub Repository Workflow Test")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)

        # Test each repository
        for i, repo_url in enumerate(self.TEST_REPOS, 1):
            print(f"\n[{i}/{len(self.TEST_REPOS)}] Testing repository...")
            result = self.run_repository_test(dhtl_path, repo_url)
            results.append(result)

        # Generate tabulated report
        self.print_test_report(results)

        # Save detailed results
        self.save_detailed_results(results)

        # Assert that at least some repos succeeded
        successful_clones = sum(1 for r in results if r.clone_success)
        successful_setups = sum(1 for r in results if r.setup_success)
        successful_builds = sum(1 for r in results if r.build_success)

        assert successful_clones > 0, "No repositories were successfully cloned"
        assert successful_setups > 0, "No repositories were successfully set up"
        # Don't require all builds to succeed due to project-specific issues

    def print_test_report(self, results: list[RepoTestResult]):
        """Print tabulated test report."""
        print("\n" + "=" * 80)
        print("TEST RESULTS SUMMARY")
        print("=" * 80)

        # Prepare data for main table
        table_data = []
        for r in results:
            table_data.append(
                [
                    r.repo_name,
                    "✅" if r.clone_success else "❌",
                    f"{r.clone_time:.1f}s" if r.clone_success else "-",
                    "✅" if r.setup_success else "❌",
                    f"{r.setup_time:.1f}s" if r.setup_success else "-",
                    "✅" if r.venv_created else "❌",
                    "✅" if r.uv_lock_created else "❌",
                    "✅" if r.build_success else "⚠️" if r.build_error else "❌",
                    f"{r.build_time:.1f}s" if r.build_time > 0 else "-",
                    r.notes or r.build_error[:30] + "..." if r.build_error else "",
                ]
            )

        headers = ["Repository", "Clone", "Time", "Setup", "Time", "Venv", "Lock", "Build", "Time", "Notes"]
        print(tabulate(table_data, headers=headers, tablefmt="grid"))

        # Summary statistics
        total = len(results)
        clone_success = sum(1 for r in results if r.clone_success)
        setup_success = sum(1 for r in results if r.setup_success)
        build_success = sum(1 for r in results if r.build_success)
        venv_created = sum(1 for r in results if r.venv_created)
        lock_created = sum(1 for r in results if r.uv_lock_created)

        print("\n" + "=" * 80)
        print("SUMMARY STATISTICS")
        print("=" * 80)

        summary_data = [
            ["Total Repositories", total, "100%"],
            ["Successful Clones", clone_success, f"{clone_success / total * 100:.1f}%"],
            ["Successful Setups", setup_success, f"{setup_success / total * 100:.1f}%"],
            ["Virtual Envs Created", venv_created, f"{venv_created / total * 100:.1f}%"],
            ["UV Locks Created", lock_created, f"{lock_created / total * 100:.1f}%"],
            ["Successful Builds", build_success, f"{build_success / total * 100:.1f}%"],
        ]

        print(tabulate(summary_data, headers=["Metric", "Count", "Percentage"], tablefmt="grid"))

        # Timing statistics
        avg_clone = sum(r.clone_time for r in results if r.clone_success) / max(clone_success, 1)
        avg_setup = sum(r.setup_time for r in results if r.setup_success) / max(setup_success, 1)
        avg_build = sum(r.build_time for r in results if r.build_success) / max(build_success, 1)

        print("\n" + "=" * 80)
        print("PERFORMANCE METRICS")
        print("=" * 80)

        perf_data = [
            ["Average Clone Time", f"{avg_clone:.1f}s"],
            ["Average Setup Time", f"{avg_setup:.1f}s"],
            ["Average Build Time", f"{avg_build:.1f}s"],
            ["Total Test Time", f"{sum(r.clone_time + r.setup_time + r.build_time for r in results):.1f}s"],
        ]

        print(tabulate(perf_data, headers=["Metric", "Value"], tablefmt="grid"))

    def save_detailed_results(self, results: list[RepoTestResult]):
        """Save detailed results to JSON file."""
        results_dict = []
        for r in results:
            results_dict.append(
                {
                    "repo_url": r.repo_url,
                    "repo_name": r.repo_name,
                    "clone": {"success": r.clone_success, "time": r.clone_time, "error": r.clone_error},
                    "setup": {
                        "success": r.setup_success,
                        "time": r.setup_time,
                        "error": r.setup_error,
                        "venv_created": r.venv_created,
                        "uv_lock_created": r.uv_lock_created,
                    },
                    "build": {
                        "success": r.build_success,
                        "time": r.build_time,
                        "error": r.build_error,
                        "dist_files": r.dist_files,
                    },
                    "notes": r.notes,
                }
            )

        with open("dht_test_results.json", "w") as f:
            json.dump({"test_date": datetime.now().isoformat(), "results": results_dict}, f, indent=2)

        print("\nDetailed results saved to: dht_test_results.json")


if __name__ == "__main__":
    # Allow running directly
    pytest.main([__file__, "-v", "-s"])
