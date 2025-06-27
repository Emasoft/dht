#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Run comprehensive tests in Docker and generate report."""

import subprocess
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE FILE:
# - Initial creation of Docker test runner script
# - Added comprehensive test execution and reporting
#

def run_docker_test(test_path: str, profile: str = "docker") -> Tuple[int, str, str]:
    """Run a test in Docker and return result."""
    cmd = [
        "docker", "run", "--rm",
        "-e", f"DHT_TEST_PROFILE={profile}",
        "dht:test-simple",
        "python", "-m", "pytest", "-v", "--tb=short",
        test_path
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr


def format_test_results(results: List[Dict[str, any]]) -> str:
    """Format test results into a nice table."""
    table = []
    table.append("┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━┓")
    table.append("┃ Test Suite                                           ┃ Passed ┃ Failed ┃ Skipped┃ Total    ┃")
    table.append("┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╋━━━━━━━━╋━━━━━━━━╋━━━━━━━━╋━━━━━━━━━━┫")
    
    total_passed = 0
    total_failed = 0
    total_skipped = 0
    total_tests = 0
    
    for result in results:
        passed = result.get("passed", 0)
        failed = result.get("failed", 0)
        skipped = result.get("skipped", 0)
        total = passed + failed + skipped
        
        total_passed += passed
        total_failed += failed
        total_skipped += skipped
        total_tests += total
        
        status = "✅" if failed == 0 else "❌"
        name = f"{status} {result['name']:<47}"
        
        table.append(f"┃ {name} ┃ {passed:>6} ┃ {failed:>6} ┃ {skipped:>6} ┃ {total:>8} ┃")
    
    table.append("┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╋━━━━━━━━╋━━━━━━━━╋━━━━━━━━╋━━━━━━━━━━┫")
    table.append(f"┃ {'TOTAL':<52} ┃ {total_passed:>6} ┃ {total_failed:>6} ┃ {total_skipped:>6} ┃ {total_tests:>8} ┃")
    table.append("┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┻━━━━━━━━┻━━━━━━━━┻━━━━━━━━┻━━━━━━━━━━┛")
    
    return "\n".join(table)


def parse_pytest_output(output: str) -> Dict[str, int]:
    """Parse pytest output to extract test counts."""
    result = {"passed": 0, "failed": 0, "skipped": 0}
    
    # Look for summary line
    for line in output.split("\n"):
        if "passed" in line or "failed" in line or "skipped" in line:
            parts = line.split()
            for i, part in enumerate(parts):
                if "passed" in part and i > 0:
                    result["passed"] = int(parts[i-1])
                elif "failed" in part and i > 0:
                    result["failed"] = int(parts[i-1])
                elif "skipped" in part and i > 0:
                    result["skipped"] = int(parts[i-1])
    
    return result


def main():
    """Run all tests in Docker."""
    print("🐋 Running DHT Tests in Docker Container")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # Test suites to run
    test_suites = [
        ("Unit Tests", "tests/unit/"),
        ("Integration Tests", "tests/integration/"),
        ("Shell Tests", "tests/test_dhtl_basic.sh"),
    ]
    
    results = []
    
    for name, path in test_suites:
        print(f"\n🔄 Running {name}...")
        returncode, stdout, stderr = run_docker_test(path)
        
        if returncode != 0 and "no tests" not in stdout:
            print(f"❌ {name} failed!")
            if stderr:
                print(f"Error: {stderr}")
        
        parsed = parse_pytest_output(stdout)
        parsed["name"] = name
        results.append(parsed)
    
    # Print results table
    print("\n" + format_test_results(results))
    
    # Run specific integration test
    print("\n🔄 Running GitHub Clone Integration Test...")
    returncode, stdout, stderr = run_docker_test(
        "tests/integration/test_github_clone_setup.py::TestGitHubCloneSetup::test_clone_and_setup_github_repo",
        profile="docker"
    )
    
    if returncode == 0:
        print("✅ GitHub clone and setup test passed!")
    else:
        print("❌ GitHub clone and setup test failed!")
        if stderr:
            print(f"Error: {stderr}")
    
    # Summary
    total_failed = sum(r.get("failed", 0) for r in results)
    if total_failed > 0:
        print(f"\n❌ Tests completed with {total_failed} failures")
        sys.exit(1)
    else:
        print("\n✅ All tests passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()