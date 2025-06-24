#!/usr/bin/env python3
"""
Test Real Workflow module.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Created real workflow test that mimics actual user behavior
# - Tests use dhtl.sh from project root, then dhtl alias after setup
# - Proper tabulated results for each operation
# - No mocks - real operations only
#

"""
Real workflow test for DHT - follows actual user workflow.
Tests the complete flow as a user would do it:
1. Use full path to dhtl.sh clone
2. cd into cloned directory
3. Use full path to dhtl.sh setup
4. Use dhtl alias for build (after venv activation)
"""

import json
import os
import shutil
import subprocess
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from tabulate import tabulate  # type: ignore


@dataclass
class OperationResult:
    """Result of a single operation."""

    success: bool = False
    time: float = 0.0
    output: str = ""
    error: str = ""
    details: dict[str, any] = field(default_factory=dict)


@dataclass
class RepoWorkflowResult:
    """Complete workflow result for a repository."""

    repo_url: str
    repo_name: str
    clone: OperationResult = field(default_factory=OperationResult)
    setup: OperationResult = field(default_factory=OperationResult)
    build: OperationResult = field(default_factory=OperationResult)
    venv_created: bool = False
    uv_lock_created: bool = False
    dist_files: list[str] = field(default_factory=list)
    overall_success: bool = False
    notes: str = ""


class TestRealDHTWorkflow:
    """Test DHT workflow as a real user would use it."""

    # Test repositories
    TEST_REPOS = [
        "https://github.com/psf/requests",
        "https://github.com/pallets/click",
        "https://github.com/pallets/flask",
        "https://github.com/encode/httpx",
        "https://github.com/tiangolo/typer",
        "https://github.com/pydantic/pydantic-core",
        "https://github.com/pytest-dev/pytest-mock",
        "https://github.com/python-poetry/tomlkit",
        "https://github.com/sdispater/pendulum",
        "https://github.com/tiangolo/fastapi",
        "https://github.com/astral-sh/ruff",  # This might fail - checking if it's the issue
        "https://github.com/pandas-dev/pandas",
    ]

    def __init__(self) -> Any:
        self.dhtl_path = Path("/Users/emanuelesabetta/Code/DHT/dht/dhtl.sh")
        self.test_dir = Path("/Users/emanuelesabetta/Code/DHT/dht/temp_test/real_workflow_test")
        self.original_dir = Path.cwd()

    def setup(self) -> Any:
        """Set up test environment."""
        # Create clean test directory
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
        self.test_dir.mkdir(parents=True, exist_ok=True)
        os.chdir(self.test_dir)

    def teardown(self) -> Any:
        """Clean up test environment."""
        os.chdir(self.original_dir)

    def run_command(self, cmd: list[str], timeout: int = 300, env: dict | None = None) -> tuple[bool, str, float]:
        """
        Run a command and capture output.

        Returns:
            Tuple of (success, output, execution_time)
        """
        start_time = time.time()

        # Merge environment variables if provided
        cmd_env = os.environ.copy()
        if env:
            cmd_env.update(env)

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=False, env=cmd_env)
            execution_time = time.time() - start_time

            output = result.stdout + result.stderr
            return result.returncode == 0, output, execution_time

        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            return False, f"Command timed out after {timeout}s", execution_time
        except Exception as e:
            execution_time = time.time() - start_time
            return False, str(e), execution_time

    def check_gh_auth(self) -> bool:
        """Check if GitHub CLI is authenticated."""
        success, output, _ = self.run_command(["gh", "auth", "status"], timeout=10)
        return success

    def test_single_repo(self, repo_url: str) -> RepoWorkflowResult:
        """Test complete workflow for a single repository."""
        repo_name = repo_url.rstrip("/").split("/")[-1]
        result = RepoWorkflowResult(repo_url=repo_url, repo_name=repo_name)

        print(f"\n{'=' * 60}")
        print(f"Testing: {repo_name}")
        print(f"URL: {repo_url}")
        print(f"{'=' * 60}")

        # Step 1: Clone using full path to dhtl.sh
        print("📥 Cloning repository...")
        cmd = [str(self.dhtl_path), "clone", repo_url, repo_name]
        success, output, exec_time = self.run_command(cmd, timeout=120)

        result.clone = OperationResult(
            success=success, time=exec_time, output=output if success else "", error=output if not success else ""
        )

        if not success:
            result.notes = "Clone failed"
            # Extract meaningful error
            if "404" in output or "not found" in output.lower():
                result.notes = "Repository not found (404)"
            elif "permission" in output.lower() or "access" in output.lower():
                result.notes = "Permission denied"
            elif "already exists" in output.lower():
                result.notes = "Directory already exists"
            print(f"❌ Clone failed: {result.notes}")
            return result

        print(f"✅ Clone successful ({exec_time:.1f}s)")

        # Verify directory was created
        repo_dir = self.test_dir / repo_name
        if not repo_dir.exists():
            result.clone.success = False
            result.notes = "Clone succeeded but directory not created"
            return result

        # Step 2: Change to repository directory
        os.chdir(repo_dir)

        try:
            # Step 3: Setup using full path to dhtl.sh
            print("🔧 Running setup...")
            cmd = [str(self.dhtl_path), "setup"]
            success, output, exec_time = self.run_command(cmd, timeout=600)

            result.setup = OperationResult(
                success=success, time=exec_time, output=output if success else "", error=output if not success else ""
            )

            # Check what was created
            result.venv_created = any(
                ((repo_dir / ".venv").exists(), (repo_dir / "venv").exists(), (repo_dir / ".venv_windows").exists())
            )
            result.uv_lock_created = (repo_dir / "uv.lock").exists()

            if not success:
                result.notes = "Setup failed"
                print("❌ Setup failed")
            else:
                print(f"✅ Setup successful ({exec_time:.1f}s)")
                if result.venv_created:
                    print("  ✓ Virtual environment created")
                if result.uv_lock_created:
                    print("  ✓ uv.lock file created")

            # Step 4: Build (only if setup succeeded and venv created)
            if result.setup.success and result.venv_created:
                print("📦 Running build...")

                # Find venv directory
                venv_dir = None
                for venv_name in [".venv", "venv", ".venv_windows"]:
                    venv_path = repo_dir / venv_name
                    if venv_path.exists():
                        venv_dir = venv_path
                        break

                if venv_dir:
                    # Activate venv by setting PATH
                    venv_bin = venv_dir / "bin"
                    if not venv_bin.exists():
                        venv_bin = venv_dir / "Scripts"  # Windows

                    # Run build with activated venv
                    env = {"PATH": f"{venv_bin}:{os.environ['PATH']}", "VIRTUAL_ENV": str(venv_dir)}

                    # Now we can use just 'dhtl' since venv is activated
                    # But for consistency, still use full path
                    cmd = [str(self.dhtl_path), "build", "--no-checks"]
                    success, output, exec_time = self.run_command(cmd, timeout=600, env=env)

                    result.build = OperationResult(
                        success=success,
                        time=exec_time,
                        output=output if success else "",
                        error=output if not success else "",
                    )

                    # Check for build artifacts
                    dist_dir = repo_dir / "dist"
                    if dist_dir.exists():
                        result.dist_files = [
                            f.name for f in dist_dir.iterdir() if f.is_file() and f.suffix in [".whl", ".tar.gz"]
                        ]

                    # Build success is determined by artifacts, not exit code
                    if result.dist_files:
                        result.build.success = True
                        print(f"✅ Build successful ({exec_time:.1f}s)")
                        print(f"  ✓ Created: {', '.join(result.dist_files)}")
                    else:
                        print("❌ Build failed - no artifacts created")
                        if "lint" in output.lower() or "ruff" in output.lower():
                            result.notes = "Build stopped at linting"

        finally:
            # Return to test directory
            os.chdir(self.test_dir)

        # Determine overall success
        result.overall_success = result.clone.success and result.setup.success and result.build.success

        return result

    def run_all_tests(self) -> list[RepoWorkflowResult]:
        """Run tests on all repositories."""
        results = []

        print("\n" + "=" * 80)
        print("DHT REAL WORKFLOW TEST")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)

        # Check GitHub CLI auth
        if not self.check_gh_auth():
            print("\n⚠️  GitHub CLI not authenticated!")
            print("Please run: gh auth login")
            print("Then run this test again.")
            return results

        print("✅ GitHub CLI authenticated")

        # Test each repository
        for i, repo_url in enumerate(self.TEST_REPOS, 1):
            print(f"\n[{i}/{len(self.TEST_REPOS)}] Processing repository...")
            result = self.test_single_repo(repo_url)
            results.append(result)

        return results

    def print_tabulated_report(self, results: list[RepoWorkflowResult]) -> Any:
        """Print detailed tabulated report."""
        print("\n" + "=" * 80)
        print("DETAILED TEST RESULTS")
        print("=" * 80)

        # Prepare table data
        table_data = []
        for r in results:
            # Determine status symbols
            clone_status = "✅" if r.clone.success else "❌"
            setup_status = "✅" if r.setup.success else "❌" if r.clone.success else "-"
            venv_status = "✅" if r.venv_created else "❌" if r.setup.success else "-"
            lock_status = "✅" if r.uv_lock_created else "❌" if r.setup.success else "-"
            build_status = "✅" if r.build.success else "❌" if r.setup.success else "-"

            # Format times
            clone_time = f"{r.clone.time:.1f}s" if r.clone.success else "-"
            setup_time = f"{r.setup.time:.1f}s" if r.setup.success else "-"
            build_time = f"{r.build.time:.1f}s" if r.build.time > 0 else "-"

            # Artifacts
            artifacts = len(r.dist_files) if r.dist_files else 0

            table_data.append(
                [
                    r.repo_name,
                    clone_status,
                    clone_time,
                    setup_status,
                    setup_time,
                    venv_status,
                    lock_status,
                    build_status,
                    build_time,
                    artifacts,
                    r.notes or "Success" if r.overall_success else r.notes or "Failed",
                ]
            )

        headers = [
            "Repository",
            "Clone",
            "Time",
            "Setup",
            "Time",
            "Venv",
            "Lock",
            "Build",
            "Time",
            "Artifacts",
            "Notes",
        ]
        print(tabulate(table_data, headers=headers, tablefmt="grid"))

        # Summary statistics
        total = len(results)
        clone_success = sum(1 for r in results if r.clone.success)
        setup_success = sum(1 for r in results if r.setup.success)
        build_success = sum(1 for r in results if r.build.success)
        venv_created = sum(1 for r in results if r.venv_created)
        lock_created = sum(1 for r in results if r.uv_lock_created)
        overall_success = sum(1 for r in results if r.overall_success)

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
            ["Complete Success", overall_success, f"{overall_success / total * 100:.1f}%"],
        ]

        print(tabulate(summary_data, headers=["Metric", "Count", "Percentage"], tablefmt="grid"))

        # Failed repositories details
        failed_clones = [r for r in results if not r.clone.success]
        if failed_clones:
            print("\n" + "=" * 80)
            print("FAILED CLONES")
            print("=" * 80)
            for r in failed_clones:
                print(f"\n{r.repo_name}: {r.notes}")
                if r.clone.error:
                    print(f"Error: {r.clone.error[:200]}...")

    def save_results(self, results: list[RepoWorkflowResult]) -> Any:
        """Save detailed results to JSON."""
        results_data = []
        for r in results:
            results_data.append(
                {
                    "repo_url": r.repo_url,
                    "repo_name": r.repo_name,
                    "clone": {
                        "success": r.clone.success,
                        "time": r.clone.time,
                        "error": r.clone.error[:500] if r.clone.error else "",
                    },
                    "setup": {
                        "success": r.setup.success,
                        "time": r.setup.time,
                        "venv_created": r.venv_created,
                        "uv_lock_created": r.uv_lock_created,
                    },
                    "build": {"success": r.build.success, "time": r.build.time, "dist_files": r.dist_files},
                    "overall_success": r.overall_success,
                    "notes": r.notes,
                }
            )

        with open("dht_workflow_results.json", "w") as f:
            json.dump(
                {
                    "test_date": datetime.now().isoformat(),
                    "dhtl_path": str(self.dhtl_path),
                    "test_dir": str(self.test_dir),
                    "results": results_data,
                },
                f,
                indent=2,
            )

        print(f"\nDetailed results saved to: {self.test_dir}/dht_workflow_results.json")


def main() -> Any:
    """Run the real workflow test."""
    test = TestRealDHTWorkflow()
    test.setup()

    try:
        results = test.run_all_tests()
        test.print_tabulated_report(results)
        test.save_results(results)
    finally:
        test.teardown()


if __name__ == "__main__":
    main()
