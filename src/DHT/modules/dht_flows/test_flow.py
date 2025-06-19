#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Initial implementation of test_command as a Prefect flow
# - Converted from dhtl_commands_2.sh shell script
# - Added parallel test discovery and execution with resource limits
#

"""
Test Command Flow - Prefect implementation of test execution.

This module replaces the shell script test_command() function
with a modern Prefect flow that provides better error handling,
parallel test discovery, and resource management.
"""

import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional, Dict, Any, List

from prefect import flow, task, get_run_logger

from ..guardian_prefect import GuardianConfig, run_with_guardian
from .restore_flow import find_project_root, detect_virtual_environment
from .utils import (
    get_venv_python_path,
    get_default_resource_limits
)


@task(name="check-test-resources", retries=2)
def check_test_resources() -> Dict[str, Any]:
    """
    Check system resources before running tests.
    
    Returns:
        Dictionary with resource availability information
    """
    logger = get_run_logger()
    
    try:
        import psutil
        
        # Get memory info
        vm = psutil.virtual_memory()
        available_mb = vm.available / (1024 * 1024)
        total_mb = vm.total / (1024 * 1024)
        
        # Get CPU info
        cpu_count = psutil.cpu_count(logical=False) or 1
        cpu_percent = psutil.cpu_percent(interval=0.1)
        
        # Check if we have enough resources
        min_memory_mb = 1024  # 1GB minimum
        has_resources = available_mb >= min_memory_mb
        
        result = {
            "has_resources": has_resources,
            "memory": {
                "available_mb": round(available_mb, 2),
                "total_mb": round(total_mb, 2),
                "percent_used": vm.percent
            },
            "cpu": {
                "count": cpu_count,
                "percent_used": cpu_percent
            }
        }
        
        if not has_resources:
            logger.warning(f"Low memory: {available_mb:.0f}MB available (minimum: {min_memory_mb}MB)")
        else:
            logger.info(f"Resources OK: {available_mb:.0f}MB memory, {cpu_count} CPUs")
        
        return result
        
    except ImportError:
        logger.warning("psutil not available, skipping resource check")
        return {"has_resources": True, "warning": "Could not check resources"}


@task(name="discover-tests")
def discover_tests(
    project_root: Path,
    test_pattern: Optional[str] = None
) -> Dict[str, Any]:
    """
    Discover tests in the project.
    
    Args:
        project_root: Project root directory
        test_pattern: Optional pattern to filter tests (pytest -k pattern)
        
    Returns:
        Dictionary with test discovery information
    """
    logger = get_run_logger()
    
    # Common test directories
    test_dirs = []
    for dirname in ["tests", "test", "testing"]:
        test_path = project_root / dirname
        if test_path.exists() and test_path.is_dir():
            test_dirs.append(test_path)
    
    # Also check for test files in src or project root
    test_files = list(project_root.glob("test_*.py"))
    test_files.extend(project_root.glob("*_test.py"))
    
    # Check for specific test frameworks
    has_pytest = (project_root / "pytest.ini").exists() or \
                 (project_root / "pyproject.toml").exists()
    has_unittest = any(f.name == "test_*.py" for f in test_files)
    
    # Count test files
    all_test_files = []
    for test_dir in test_dirs:
        all_test_files.extend(test_dir.rglob("test_*.py"))
        all_test_files.extend(test_dir.rglob("*_test.py"))
    all_test_files.extend(test_files)
    
    # Remove duplicates
    all_test_files = list(set(all_test_files))
    
    result = {
        "test_dirs": [str(d) for d in test_dirs],
        "test_files_count": len(all_test_files),
        "has_pytest": has_pytest,
        "has_unittest": has_unittest,
        "test_pattern": test_pattern,
        "framework": "pytest" if has_pytest else "unittest"
    }
    
    logger.info(f"Found {len(all_test_files)} test files in {len(test_dirs)} directories")
    logger.info(f"Test framework: {result['framework']}")
    
    return result


@task(name="prepare-test-command")
def prepare_test_command(
    project_root: Path,
    venv_path: Path,
    discovery_info: Dict[str, Any],
    verbose: bool = False,
    coverage: bool = False,
    parallel: bool = False,
    timeout: Optional[int] = None
) -> List[str]:
    """
    Prepare the test command based on discovery information.
    
    Args:
        project_root: Project root directory
        venv_path: Virtual environment path
        discovery_info: Test discovery information
        verbose: Enable verbose output
        coverage: Enable coverage reporting
        parallel: Enable parallel test execution
        timeout: Test timeout in seconds
        
    Returns:
        List of command parts
    """
    logger = get_run_logger()
    
    # Base python command
    try:
        python_path = get_venv_python_path(venv_path)
    except FileNotFoundError:
        raise RuntimeError("Python executable not found in virtual environment")
    
    cmd_parts = [str(python_path), "-m"]
    
    if discovery_info["framework"] == "pytest":
        # Use pytest
        if coverage:
            cmd_parts.extend(["coverage", "run", "-m", "pytest"])
        else:
            cmd_parts.append("pytest")
        
        # Add options
        if verbose:
            cmd_parts.append("-v")
        else:
            cmd_parts.append("-q")
        
        # Add pattern filter
        if discovery_info.get("test_pattern"):
            cmd_parts.extend(["-k", discovery_info["test_pattern"]])
        
        # Add parallel execution
        if parallel:
            cmd_parts.extend(["-n", "auto"])
        
        # Add timeout
        if timeout:
            cmd_parts.extend(["--timeout", str(timeout)])
        
        # Add test directories or current directory
        if discovery_info["test_dirs"]:
            cmd_parts.extend(discovery_info["test_dirs"])
        else:
            cmd_parts.append(".")
            
    else:
        # Use unittest
        cmd_parts.append("unittest")
        
        if verbose:
            cmd_parts.append("-v")
        
        cmd_parts.append("discover")
        
        # Add test directories
        if discovery_info["test_dirs"]:
            cmd_parts.extend(["-s", discovery_info["test_dirs"][0]])
        
        # Add pattern
        if discovery_info.get("test_pattern"):
            cmd_parts.extend(["-p", f"*{discovery_info['test_pattern']}*.py"])
    
    logger.info(f"Test command: {' '.join(cmd_parts)}")
    return cmd_parts


@task(name="run-tests")
def run_tests(
    cmd_parts: List[str],
    project_root: Path,
    memory_limit_mb: Optional[int] = None,
    timeout_seconds: int = 900  # 15 minutes default
) -> Dict[str, Any]:
    """
    Run tests with resource limits.
    
    Args:
        cmd_parts: Command parts to execute
        project_root: Project root directory
        memory_limit_mb: Memory limit in MB
        timeout_seconds: Timeout in seconds
        
    Returns:
        Test execution results
    """
    logger = get_run_logger()
    
    default_limits = get_default_resource_limits()
    guardian_config = GuardianConfig(
        memory_limit_mb=memory_limit_mb or default_limits["memory_limit_mb"],
        timeout_seconds=timeout_seconds,
        check_interval=1.0
    )
    
    start_time = time.time()
    
    result = run_with_guardian(
        cmd_parts,
        config=guardian_config,
        cwd=str(project_root)
    )
    
    execution_time = time.time() - start_time
    
    # Parse test output
    test_summary = parse_test_output(result.stdout, result.stderr)
    
    return {
        "success": result.return_code == 0,
        "return_code": result.return_code,
        "execution_time": execution_time,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "summary": test_summary,
        "resource_info": {
            "memory_limit_mb": memory_limit_mb,
            "peak_memory_mb": result.peak_memory_mb
        }
    }


@task(name="parse-test-output")
def parse_test_output(stdout: str, stderr: str) -> Dict[str, Any]:
    """
    Parse test output to extract summary information.
    
    Args:
        stdout: Standard output from test run
        stderr: Standard error from test run
        
    Returns:
        Dictionary with test summary
    """
    output = stdout + "\n" + stderr
    summary = {
        "total": 0,
        "passed": 0,
        "failed": 0,
        "skipped": 0,
        "errors": 0,
        "warnings": 0
    }
    
    # Try to parse pytest output
    pytest_pattern = r"(\d+) passed(?:, (\d+) skipped)?(?:, (\d+) failed)?(?:, (\d+) error)?"
    match = re.search(pytest_pattern, output)
    if match:
        summary["passed"] = int(match.group(1) or 0)
        summary["skipped"] = int(match.group(2) or 0)
        summary["failed"] = int(match.group(3) or 0)
        summary["errors"] = int(match.group(4) or 0)
        summary["total"] = sum([summary["passed"], summary["failed"], 
                               summary["skipped"], summary["errors"]])
        return summary
    
    # Try to parse unittest output
    unittest_pattern = r"Ran (\d+) tests?"
    match = re.search(unittest_pattern, output)
    if match:
        summary["total"] = int(match.group(1))
        
        if "FAILED" in output:
            fail_match = re.search(r"FAILED \((?:failures=(\d+))?(?:, )?(?:errors=(\d+))?\)", output)
            if fail_match:
                summary["failed"] = int(fail_match.group(1) or 0)
                summary["errors"] = int(fail_match.group(2) or 0)
        
        if "OK" in output and not summary["failed"] and not summary["errors"]:
            summary["passed"] = summary["total"]
    
    return summary


@task(name="generate-coverage-report")
def generate_coverage_report(
    project_root: Path,
    venv_path: Path
) -> Dict[str, Any]:
    """
    Generate coverage report if coverage was enabled.
    
    Args:
        project_root: Project root directory
        venv_path: Virtual environment path
        
    Returns:
        Coverage report information
    """
    logger = get_run_logger()
    
    try:
        python_path = get_venv_python_path(venv_path)
    except FileNotFoundError:
        return {"has_coverage": False, "error": "Python not found"}
    
    # Check if coverage data exists
    coverage_file = project_root / ".coverage"
    if not coverage_file.exists():
        return {"has_coverage": False}
    
    # Generate report
    cmd = [str(python_path), "-m", "coverage", "report"]
    result = subprocess.run(
        cmd,
        cwd=str(project_root),
        capture_output=True,
        text=True
    )
    
    # Parse coverage percentage
    coverage_percent = None
    for line in result.stdout.split("\n"):
        if "TOTAL" in line:
            parts = line.split()
            if len(parts) >= 4:
                try:
                    coverage_percent = int(parts[-1].rstrip("%"))
                except ValueError:
                    pass
    
    return {
        "has_coverage": True,
        "coverage_percent": coverage_percent,
        "report": result.stdout
    }


@flow(
    name="test-command",
    description="Run project tests with resource management",
    retries=1
)
def test_command_flow(
    project_path: Optional[str] = None,
    test_pattern: Optional[str] = None,
    verbose: bool = False,
    coverage: bool = False,
    parallel: bool = False,
    timeout: Optional[int] = None,
    memory_limit_mb: int = 2048
) -> Dict[str, Any]:
    """
    Main flow for running project tests.
    
    This flow:
    1. Checks system resources
    2. Finds project root and virtual environment
    3. Discovers tests
    4. Runs tests with resource limits
    5. Optionally generates coverage report
    
    Args:
        project_path: Optional project path
        test_pattern: Optional pattern to filter tests
        verbose: Enable verbose output
        coverage: Enable coverage reporting
        parallel: Enable parallel test execution
        timeout: Test timeout in seconds
        memory_limit_mb: Memory limit for test execution
        
    Returns:
        Dictionary with test results
    """
    logger = get_run_logger()
    logger.info("Starting test execution flow")
    
    # Check resources
    resources = check_test_resources()
    if not resources.get("has_resources", True):
        logger.warning("System resources are limited, tests may run slowly")
    
    # Find project root
    start_path = Path(project_path) if project_path else None
    project_root = find_project_root(start_path)
    
    # Detect virtual environment
    venv_exists, venv_path = detect_virtual_environment(project_root)
    if not venv_exists:
        raise RuntimeError("No virtual environment found. Run 'dhtl restore' first.")
    
    # Discover tests
    discovery_info = discover_tests(project_root, test_pattern)
    
    if discovery_info["test_files_count"] == 0:
        logger.warning("No test files found")
        return {
            "success": True,
            "message": "No tests found to run",
            "discovery": discovery_info
        }
    
    # Prepare test command
    cmd_parts = prepare_test_command(
        project_root=project_root,
        venv_path=venv_path,
        discovery_info=discovery_info,
        verbose=verbose,
        coverage=coverage,
        parallel=parallel,
        timeout=timeout
    )
    
    # Run tests
    test_result = run_tests(
        cmd_parts=cmd_parts,
        project_root=project_root,
        memory_limit_mb=memory_limit_mb,
        timeout_seconds=timeout or 900
    )
    
    # Generate coverage report if requested
    coverage_info = {}
    if coverage:
        coverage_info = generate_coverage_report(project_root, venv_path)
    
    # Compile final results
    final_result = {
        "success": test_result["success"],
        "project_root": str(project_root),
        "resources": resources,
        "discovery": discovery_info,
        "test_result": test_result,
        "coverage": coverage_info
    }
    
    # Log summary
    summary = test_result["summary"]
    if test_result["success"]:
        logger.info(f"✅ Tests passed! {summary['passed']}/{summary['total']} tests successful")
        if coverage_info.get("coverage_percent"):
            logger.info(f"   Coverage: {coverage_info['coverage_percent']}%")
    else:
        logger.error(f"❌ Tests failed! {summary['failed']} failures, {summary['errors']} errors")
        logger.error(f"   Total: {summary['total']} tests")
    
    logger.info(f"   Execution time: {test_result['execution_time']:.2f}s")
    
    return final_result


# Aliases for backward compatibility
# run_tests = test_command_flow  # Not needed - run_tests is already defined above
detect_test_framework = prepare_test_command  
run_pytest = run_tests
detect_test_command = prepare_test_command
execute_test_command = run_tests


# CLI interface for backwards compatibility
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run project tests")
    parser.add_argument("--project-path", help="Project path")
    parser.add_argument("-k", "--pattern", help="Test pattern filter")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--coverage", action="store_true", help="Enable coverage")
    parser.add_argument("--parallel", action="store_true", help="Run tests in parallel")
    parser.add_argument("--timeout", type=int, help="Test timeout in seconds")
    parser.add_argument("--memory-limit", type=int, default=2048, help="Memory limit in MB")
    
    args = parser.parse_args()
    
    result = test_command_flow(
        project_path=args.project_path,
        test_pattern=args.pattern,
        verbose=args.verbose,
        coverage=args.coverage,
        parallel=args.parallel,
        timeout=args.timeout,
        memory_limit_mb=args.memory_limit
    )
    
    sys.exit(0 if result["success"] else 1)