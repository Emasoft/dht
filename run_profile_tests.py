#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Run profile-specific tests in Docker containers."""

import subprocess
import sys
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE FILE:
# - Initial creation of profile test runner
# - Added LOCAL and REMOTE profile execution
# - Added comparison mode to run both profiles
#


class ProfileTestRunner:
    """Run tests with different profiles in Docker."""

    def __init__(self):
        self.project_root = Path(__file__).parent
        self.results: Dict[str, Dict] = {}

    def run_docker_compose_service(self, service: str, compose_file: str = "docker-compose.profiles.yml") -> Tuple[int, str, str]:
        """Run a docker-compose service."""
        cmd = [
            "docker", "compose",
            "-f", compose_file,
            "run", "--rm",
            service
        ]
        
        print(f"🐋 Running service: {service}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode, result.stdout, result.stderr

    def run_profile_tests(self, profile: str) -> Dict[str, any]:
        """Run tests for a specific profile."""
        print(f"\n{'='*80}")
        print(f"🔧 Running tests with {profile.upper()} profile")
        print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*80}\n")

        service_name = f"dht-test-{profile}"
        start_time = datetime.now()
        
        # Run the tests
        returncode, stdout, stderr = self.run_docker_compose_service(service_name)
        
        duration = (datetime.now() - start_time).total_seconds()
        
        # Parse results
        passed = stdout.count(" passed")
        failed = stdout.count(" failed")
        skipped = stdout.count(" skipped")
        
        result = {
            "profile": profile,
            "returncode": returncode,
            "duration": duration,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "total": passed + failed + skipped,
            "success": returncode == 0,
            "output": stdout,
            "errors": stderr
        }
        
        self.results[profile] = result
        return result

    def run_comparison(self) -> None:
        """Run tests in both profiles and compare results."""
        print("\n🔄 Running profile comparison tests...")
        
        # Run comparison service
        returncode, stdout, stderr = self.run_docker_compose_service("dht-test-compare")
        
        if returncode == 0:
            print("✅ Profile comparison completed successfully")
        else:
            print("❌ Profile comparison failed")
            if stderr:
                print(f"Error: {stderr}")

    def print_summary(self) -> None:
        """Print summary of test results."""
        if not self.results:
            return
        
        print("\n" + "="*80)
        print("📊 PROFILE TEST SUMMARY")
        print("="*80)
        
        # Create comparison table
        print("\n┏━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━┓")
        print("┃ Profile  ┃ Passed ┃ Failed ┃ Skipped ┃ Total    ┃ Duration  ┃ Status   ┃")
        print("┣━━━━━━━━━━╋━━━━━━━━╋━━━━━━━━╋━━━━━━━━━╋━━━━━━━━━━╋━━━━━━━━━━━╋━━━━━━━━━━┫")
        
        for profile, result in self.results.items():
            status = "✅ PASS" if result["success"] else "❌ FAIL"
            duration = f"{result['duration']:.2f}s"
            
            print(f"┃ {profile.upper():<8} ┃ {result['passed']:>6} ┃ {result['failed']:>6} ┃ "
                  f"{result['skipped']:>7} ┃ {result['total']:>8} ┃ {duration:>9} ┃ {status:<8} ┃")
        
        print("┗━━━━━━━━━━┻━━━━━━━━┻━━━━━━━━┻━━━━━━━━━┻━━━━━━━━━━┻━━━━━━━━━━━┻━━━━━━━━━━┛")
        
        # Profile differences
        if len(self.results) == 2:
            self.print_profile_differences()

    def print_profile_differences(self) -> None:
        """Print differences between LOCAL and REMOTE profiles."""
        if "local" not in self.results or "remote" not in self.results:
            return
        
        local = self.results["local"]
        remote = self.results["remote"]
        
        print("\n📈 PROFILE DIFFERENCES:")
        print(f"• Test Coverage: LOCAL ran {local['total']} tests, REMOTE ran {remote['total']} tests")
        print(f"• Skipped Tests: LOCAL skipped {local['skipped']}, REMOTE skipped {remote['skipped']}")
        print(f"• Execution Time: LOCAL took {local['duration']:.2f}s, REMOTE took {remote['duration']:.2f}s")
        
        time_diff = local['duration'] - remote['duration']
        if time_diff > 0:
            print(f"• Speed: REMOTE was {time_diff:.2f}s faster ({(time_diff/local['duration']*100):.1f}% improvement)")
        
        coverage_diff = local['total'] - local['skipped'] - (remote['total'] - remote['skipped'])
        if coverage_diff > 0:
            print(f"• Coverage: LOCAL ran {coverage_diff} more actual tests")

    def run_development_shell(self, profile: str = "local") -> None:
        """Start an interactive development shell."""
        service = "dht-dev-local" if profile == "local" else "dht-ci-runner"
        print(f"\n🐚 Starting {profile.upper()} development shell...")
        
        cmd = [
            "docker", "compose",
            "-f", "docker-compose.profiles.yml",
            "run", "--rm",
            service
        ]
        
        subprocess.run(cmd)

    def cleanup(self) -> None:
        """Clean up Docker resources."""
        print("\n🧹 Cleaning up Docker resources...")
        
        cmd = [
            "docker", "compose",
            "-f", "docker-compose.profiles.yml",
            "down", "-v"
        ]
        
        subprocess.run(cmd, capture_output=True)
        print("✅ Cleanup completed")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Run DHT tests with different profiles")
    parser.add_argument(
        "profile",
        choices=["local", "remote", "both", "compare", "shell"],
        help="Profile to test (or 'both' to test all profiles)"
    )
    parser.add_argument(
        "--no-cleanup",
        action="store_true",
        help="Don't clean up Docker resources after tests"
    )
    
    args = parser.parse_args()
    runner = ProfileTestRunner()
    
    try:
        if args.profile == "shell":
            runner.run_development_shell()
        elif args.profile == "compare":
            runner.run_comparison()
        elif args.profile == "both":
            # Run both profiles
            runner.run_profile_tests("local")
            runner.run_profile_tests("remote")
            runner.print_summary()
        else:
            # Run single profile
            result = runner.run_profile_tests(args.profile)
            runner.print_summary()
            
            # Exit with test result code
            sys.exit(0 if result["success"] else 1)
    
    finally:
        if not args.no_cleanup and args.profile != "shell":
            runner.cleanup()


if __name__ == "__main__":
    main()