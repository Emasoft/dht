#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Run comprehensive dhtl action tests in Docker containers."""

import subprocess
import sys
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE FILE:
# - Initial creation of dhtl action test runner
# - Runs tests in both LOCAL and REMOTE profiles
# - Provides detailed test coverage report
#


class DHTLActionTestRunner:
    """Runner for comprehensive dhtl action tests."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.test_files = [
            "tests/docker/test_all_dhtl_actions.py",
            "tests/docker/test_dhtl_commands_complete.py",
        ]
        self.results = {}
    
    def run_tests_in_profile(self, profile: str) -> Dict[str, any]:
        """Run all dhtl action tests in a specific profile."""
        print(f"\n{'='*80}")
        print(f"🧪 Running DHTL Action Tests - {profile.upper()} Profile")
        print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*80}\n")
        
        # Build Docker command
        docker_cmd = [
            "docker", "run", "--rm",
            "-v", f"{self.project_root}:/app:ro",
            "-e", f"DHT_TEST_PROFILE={profile}",
            "-e", "DHT_IN_DOCKER=1",
            "-e", "DHT_TEST_MODE=1",
            "-e", "PYTHONPATH=/app/src:/app",
            "dht:test-simple",
            "python", "-m", "pytest", "-v", "--tb=short",
        ]
        
        # Add test files
        docker_cmd.extend(self.test_files)
        
        # Add profile-specific options
        if profile == "remote":
            docker_cmd.extend(["-m", "not slow", "--maxfail=5"])
        
        # Run tests
        start_time = datetime.now()
        result = subprocess.run(docker_cmd, capture_output=True, text=True)
        duration = (datetime.now() - start_time).total_seconds()
        
        # Parse results
        output = result.stdout
        passed = output.count(" PASSED")
        failed = output.count(" FAILED")
        skipped = output.count(" SKIPPED")
        
        return {
            "profile": profile,
            "returncode": result.returncode,
            "duration": duration,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "total": passed + failed + skipped,
            "output": output,
            "errors": result.stderr
        }
    
    def run_test_categories(self) -> None:
        """Run tests by category."""
        categories = {
            "Project Management": "TestDHTLProjectManagement",
            "Development": "TestDHTLDevelopment",
            "Version Control": "TestDHTLVersionControl",
            "Deployment": "TestDHTLDeployment",
            "Utilities": "TestDHTLUtilities",
            "Special Commands": "TestDHTLSpecialCommands",
            "Integration": "TestDHTLIntegration",
            "Edge Cases": "TestDHTLEdgeCases",
        }
        
        print("\n📊 Running Tests by Category")
        print("="*60)
        
        for category, test_class in categories.items():
            print(f"\n🔄 Testing {category}...")
            
            cmd = [
                "docker", "run", "--rm",
                "-v", f"{self.project_root}:/app:ro",
                "-e", "DHT_TEST_PROFILE=docker",
                "-e", "DHT_IN_DOCKER=1",
                "dht:test-simple",
                "python", "-m", "pytest", "-v", "-k", test_class,
                "tests/docker/test_all_dhtl_actions.py"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                passed = result.stdout.count(" PASSED")
                print(f"  ✅ {category}: {passed} tests passed")
            else:
                failed = result.stdout.count(" FAILED")
                print(f"  ❌ {category}: {failed} tests failed")
    
    def generate_coverage_report(self) -> None:
        """Generate a coverage report of tested commands."""
        print("\n📋 DHTL Command Coverage Report")
        print("="*60)
        
        # All dhtl commands from registry
        all_commands = [
            # Project Management
            "init", "setup", "clean",
            # Development
            "build", "test", "lint", "format", "coverage", "sync",
            # Dependencies
            "install", "add", "remove", "upgrade", "restore",
            # Version Control
            "commit", "tag", "bump",
            # GitHub
            "clone", "fork",
            # Deployment
            "publish", "docker", "workflows", "act", "deploy_project_in_container",
            # Workspace
            "workspace", "workspaces", "project",
            # Utilities
            "env", "diagnostics", "guardian",
            # Special
            "help", "version", "node", "python", "run", "script",
            # Testing
            "test_dht", "verify_dht",
            # Aliases
            "fmt", "check", "doc", "bin", "ws", "w", "p"
        ]
        
        # Commands tested (based on test file content)
        tested_commands = {
            "init", "setup", "clean", "build", "test", "lint", "format",
            "coverage", "sync", "restore", "commit", "tag", "bump",
            "publish", "docker", "workflows", "env", "diagnostics",
            "help", "version", "python", "run", "clone"
        }
        
        # Calculate coverage
        total = len(set(all_commands))
        tested = len(tested_commands)
        coverage = (tested / total) * 100
        
        print(f"\nTotal Commands: {total}")
        print(f"Tested Commands: {tested}")
        print(f"Coverage: {coverage:.1f}%")
        
        # Show untested commands
        untested = set(all_commands) - tested_commands
        if untested:
            print(f"\n⚠️  Untested Commands ({len(untested)}):")
            for cmd in sorted(untested):
                print(f"  - {cmd}")
    
    def print_summary(self, results: List[Dict]) -> None:
        """Print test summary."""
        print("\n" + "="*80)
        print("📊 DHTL ACTION TEST SUMMARY")
        print("="*80)
        
        print("\n┏━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━┓")
        print("┃ Profile  ┃ Passed ┃ Failed ┃ Skipped ┃ Total    ┃ Duration  ┃ Status   ┃")
        print("┣━━━━━━━━━━╋━━━━━━━━╋━━━━━━━━╋━━━━━━━━━╋━━━━━━━━━━╋━━━━━━━━━━━╋━━━━━━━━━━┫")
        
        for result in results:
            status = "✅ PASS" if result["returncode"] == 0 else "❌ FAIL"
            duration = f"{result['duration']:.2f}s"
            
            print(f"┃ {result['profile'].upper():<8} ┃ {result['passed']:>6} ┃ "
                  f"{result['failed']:>6} ┃ {result['skipped']:>7} ┃ "
                  f"{result['total']:>8} ┃ {duration:>9} ┃ {status:<8} ┃")
        
        print("┗━━━━━━━━━━┻━━━━━━━━┻━━━━━━━━┻━━━━━━━━━┻━━━━━━━━━━┻━━━━━━━━━━━┻━━━━━━━━━━┛")
        
        # Overall status
        all_passed = all(r["returncode"] == 0 for r in results)
        if all_passed:
            print("\n✅ All dhtl action tests passed!")
        else:
            print("\n❌ Some dhtl action tests failed!")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Run comprehensive dhtl action tests")
    parser.add_argument(
        "--profile",
        choices=["local", "remote", "both", "categories"],
        default="both",
        help="Test profile to run"
    )
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Show command coverage report"
    )
    
    args = parser.parse_args()
    runner = DHTLActionTestRunner()
    
    results = []
    
    if args.profile == "categories":
        runner.run_test_categories()
    elif args.profile == "both":
        results.append(runner.run_tests_in_profile("local"))
        results.append(runner.run_tests_in_profile("remote"))
        runner.print_summary(results)
    else:
        result = runner.run_tests_in_profile(args.profile)
        results.append(result)
        runner.print_summary(results)
    
    if args.coverage:
        runner.generate_coverage_report()
    
    # Exit with appropriate code
    if results:
        sys.exit(0 if all(r["returncode"] == 0 for r in results) else 1)


if __name__ == "__main__":
    main()