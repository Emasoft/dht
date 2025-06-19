#!/usr/bin/env python3
"""
guardian_prefect.py - Prefect-based process management for DHT

This module replaces the shell-based guardian with a Prefect-based implementation
that provides better resource management, error handling, and task orchestration.
"""

import os
import shlex
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import psutil
import yaml
from prefect import flow, get_run_logger, task


@dataclass
class GuardianConfig:
    """Configuration for guardian process management."""
    memory_limit_mb: int = 2048
    timeout_seconds: int = 900
    check_interval: float = 1.0
    cpu_limit_percent: int | None = None


@dataclass
class GuardianResult:
    """Result from running a command with guardian."""
    return_code: int
    stdout: str
    stderr: str
    execution_time: float
    peak_memory_mb: float | None = None
    was_killed: bool = False
    kill_reason: str | None = None

    @property
    def success(self) -> bool:
        """Check if command executed successfully."""
        return self.return_code == 0

    @property
    def duration(self) -> float:
        """Alias for execution_time for compatibility."""
        return self.execution_time


class ResourceLimits:
    """Resource limits configuration for backward compatibility."""
    def __init__(self, memory_mb: int = 2048, cpu_percent: int = 80, timeout: int = 900):
        self.memory_mb = memory_mb
        self.cpu_percent = cpu_percent
        self.timeout = timeout


@task(
    name="check-resources",
    retries=2,
    retry_delay_seconds=5,
    description="Check available system resources"
)
def check_system_resources() -> dict[str, float]:
    """Check current system resource usage"""
    logger = get_run_logger()

    memory = psutil.virtual_memory()
    cpu_percent = psutil.cpu_percent(interval=1)

    resources = {
        "memory_available_mb": memory.available / (1024 * 1024),
        "memory_percent": memory.percent,
        "cpu_percent": cpu_percent,
        "disk_percent": psutil.disk_usage('/').percent
    }

    logger.info(f"System resources: {resources}")
    return resources


@task(
    name="validate-command",
    description="Validate command before execution"
)
def validate_command(cmd: str | list[str], limits: Any) -> bool:
    """Validate command and check if resources are available"""
    logger = get_run_logger()

    # Convert string command to list if needed
    if isinstance(cmd, str):
        cmd = cmd.split()

    # Check if command exists
    if not cmd:
        logger.error("Empty command provided")
        return False

    # Check available resources
    resources = check_system_resources()

    if resources["memory_available_mb"] < limits.memory_mb:
        logger.warning(f"Insufficient memory: {resources['memory_available_mb']:.2f}MB available, {limits.memory_mb}MB required")
        return False

    if resources["cpu_percent"] > limits.cpu_percent:
        logger.warning(f"High CPU usage: {resources['cpu_percent']:.1f}%")

    return True


@task(
    name="run-command",
    retries=3,
    retry_delay_seconds=10,
    description="Execute command with resource limits"
)
def run_command_with_limits(
    cmd: str | list[str],
    limits: Any | None = None,
    working_dir: Path | None = None,
    env: dict[str, str] | None = None
) -> dict[str, int | str | float]:
    """Run command with memory and timeout limits"""
    logger = get_run_logger()

    if limits is None:
        # Create default limits
        class DefaultLimits:
            memory_mb = 2048
            cpu_percent = 80
            timeout = 900
        limits = DefaultLimits()

    # Validate command
    if not validate_command(cmd, limits):
        raise ValueError(f"Command validation failed: {cmd}")

    # Convert string command to list if needed
    if isinstance(cmd, str):
        cmd_list = cmd.split()
    else:
        cmd_list = cmd

    logger.info(f"Executing command: {' '.join(cmd_list)}")
    logger.info(f"Limits: memory={limits.memory_mb}MB, timeout={limits.timeout}s")

    # Prepare environment
    cmd_env = os.environ.copy()
    if env:
        cmd_env.update(env)

    # Start time tracking
    start_time = time.time()

    try:
        # Run the command
        process = subprocess.Popen(
            cmd_list,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=working_dir,
            env=cmd_env,
            preexec_fn=os.setsid if sys.platform != "win32" else None
        )

        # Monitor process
        result = monitor_process(process, limits)

        end_time = time.time()
        duration = end_time - start_time

        result["duration"] = duration
        result["command"] = " ".join(cmd_list)

        if result["returncode"] != 0:
            logger.warning(f"Command failed with return code {result['returncode']}")
        else:
            logger.info(f"Command completed successfully in {duration:.2f}s")

        return result

    except Exception as e:
        logger.error(f"Error executing command: {e}")
        raise


def monitor_process(process: subprocess.Popen, limits: Any) -> dict[str, int | str | float]:
    """Monitor a running process for resource usage and timeout"""
    logger = get_run_logger()
    start_time = time.time()
    peak_memory_mb = 0.0

    try:
        # Create a Process object for monitoring
        psutil_process = psutil.Process(process.pid)

        while process.poll() is None:
            # Check timeout
            elapsed = time.time() - start_time
            if elapsed > limits.timeout:
                logger.error(f"Process timeout after {elapsed:.2f}s")
                kill_process_tree(process.pid)
                stdout, stderr = process.communicate()
                return {
                    "returncode": -1,
                    "stdout": stdout,
                    "stderr": f"Process killed due to timeout ({limits.timeout}s)",
                    "killed": True,
                    "reason": "timeout",
                    "peak_memory_mb": peak_memory_mb
                }

            # Check memory usage
            try:
                memory_info = psutil_process.memory_info()
                memory_mb = memory_info.rss / (1024 * 1024)
                peak_memory_mb = max(peak_memory_mb, memory_mb)

                if memory_mb > limits.memory_mb:
                    logger.error(f"Process exceeded memory limit: {memory_mb:.2f}MB > {limits.memory_mb}MB")
                    kill_process_tree(process.pid)
                    stdout, stderr = process.communicate()
                    return {
                        "returncode": -1,
                        "stdout": stdout,
                        "stderr": f"Process killed due to memory limit ({limits.memory_mb}MB)",
                        "killed": True,
                        "reason": "memory",
                        "peak_memory_mb": peak_memory_mb
                    }
            except psutil.NoSuchProcess:
                # Process might have ended
                break

            time.sleep(0.1)

        # Get final output
        stdout, stderr = process.communicate()

        return {
            "returncode": process.returncode,
            "stdout": stdout,
            "stderr": stderr,
            "killed": False,
            "reason": None,
            "peak_memory_mb": peak_memory_mb
        }

    except Exception as e:
        logger.error(f"Error monitoring process: {e}")
        # Try to clean up
        try:
            kill_process_tree(process.pid)
        except Exception:
            pass
        raise


def kill_process_tree(pid: int):
    """Kill a process and all its children"""
    try:
        parent = psutil.Process(pid)
        children = parent.children(recursive=True)

        # Kill children first
        for child in children:
            try:
                child.kill()
            except psutil.NoSuchProcess:
                pass

        # Kill parent
        parent.kill()

        # Wait for processes to die
        gone, alive = psutil.wait_procs([parent] + children, timeout=5)

        # Force kill any remaining
        for p in alive:
            try:
                p.kill()
            except psutil.NoSuchProcess:
                pass

    except psutil.NoSuchProcess:
        pass


def run_with_guardian(
    command: list[str],
    limits: Any | None = None,  # 'ResourceLimits' type for compatibility
    config: GuardianConfig | None = None,
    cwd: str | None = None,
    env: dict[str, str] | None = None
) -> GuardianResult:
    """
    Run a command with guardian resource limits.

    This is a simplified synchronous interface to the guardian system
    that's compatible with the existing DHT flows.

    Args:
        command: Command to run as list of strings
        config: Guardian configuration
        cwd: Working directory
        env: Environment variables

    Returns:
        GuardianResult with execution details
    """
    # Handle both old ResourceLimits and new GuardianConfig for compatibility
    if limits is None and config is None:
        config = GuardianConfig()

    if config is not None:
        # Convert GuardianConfig to internal format
        memory_mb = config.memory_limit_mb
        cpu_percent = config.cpu_limit_percent or 100
        timeout = config.timeout_seconds
    else:
        # Use ResourceLimits directly
        memory_mb = limits.memory_mb
        cpu_percent = limits.cpu_percent
        timeout = limits.timeout

    # Join command for shell execution with proper escaping
    if isinstance(command, list):
        cmd_str = " ".join(shlex.quote(part) for part in command)
    else:
        cmd_str = command

    # Create a ResourceLimits object for the task
    task_limits = ResourceLimits(memory_mb, cpu_percent, timeout)

    # Use existing task function
    result = run_command_with_limits(
        cmd=cmd_str,
        limits=task_limits,
        working_dir=cwd,
        env=env
    )

    # Convert to GuardianResult
    return GuardianResult(
        return_code=result["returncode"],
        stdout=result.get("stdout", ""),
        stderr=result.get("stderr", ""),
        execution_time=result.get("duration", 0.0),
        peak_memory_mb=result.get("peak_memory_mb"),
        was_killed=result.get("killed", False),
        kill_reason=result.get("reason")
    )


@flow(
    name="guardian-sequential",
    description="Run commands sequentially with resource management"
)
def guardian_sequential_flow(
    commands: list[str | dict[str, any]],
    stop_on_failure: bool = True,
    default_limits: Any | None = None
) -> list[dict[str, int | str | float]]:
    """Process commands sequentially with resource management"""
    logger = get_run_logger()
    logger.info(f"Starting sequential execution of {len(commands)} commands")

    if default_limits is None:
        # Create default limits
        class DefaultLimits:
            memory_mb = 2048
            cpu_percent = 80
            timeout = 900
        default_limits = DefaultLimits()

    results = []

    for i, cmd in enumerate(commands):
        logger.info(f"Processing command {i+1}/{len(commands)}")

        # Parse command configuration
        if isinstance(cmd, dict):
            command = cmd.get("command")
            limits = ResourceLimits(
                memory_mb=cmd.get("memory_mb", default_limits.memory_mb),
                cpu_percent=cmd.get("cpu_percent", default_limits.cpu_percent),
                timeout=cmd.get("timeout", default_limits.timeout)
            )
            working_dir = cmd.get("working_dir")
            env = cmd.get("env")
        else:
            command = cmd
            limits = default_limits
            working_dir = None
            env = None

        try:
            result = run_command_with_limits(
                command,
                limits=limits,
                working_dir=working_dir,
                env=env
            )
            results.append(result)

            if stop_on_failure and result["returncode"] != 0:
                logger.error("Command failed, stopping execution")
                break

        except Exception as e:
            logger.error(f"Error executing command: {e}")
            error_result = {
                "command": str(command),
                "returncode": -1,
                "stdout": "",
                "stderr": str(e),
                "error": True
            }
            results.append(error_result)

            if stop_on_failure:
                break

    logger.info(f"Completed {len(results)}/{len(commands)} commands")
    return results


@flow(
    name="guardian-batch",
    description="Run commands in parallel batches"
)
def guardian_batch_flow(
    commands: list[str | dict[str, any]],
    batch_size: int = 5,
    default_limits: Any | None = None
) -> list[dict[str, int | str | float]]:
    """Process commands in parallel batches"""
    logger = get_run_logger()
    logger.info(f"Starting batch execution of {len(commands)} commands (batch_size={batch_size})")

    if default_limits is None:
        # Create default limits
        class DefaultLimits:
            memory_mb = 2048
            cpu_percent = 80
            timeout = 900
        default_limits = DefaultLimits()

    results = []

    # Process commands in batches
    for i in range(0, len(commands), batch_size):
        batch = commands[i:i + batch_size]
        logger.info(f"Processing batch {i//batch_size + 1} ({len(batch)} commands)")

        # Submit batch tasks
        batch_futures = []
        for cmd in batch:
            # Parse command configuration
            if isinstance(cmd, dict):
                command = cmd.get("command")
                class CustomLimits:
                    def __init__(self, memory_mb, cpu_percent, timeout):
                        self.memory_mb = memory_mb
                        self.cpu_percent = cpu_percent
                        self.timeout = timeout

                limits = CustomLimits(
                    memory_mb=cmd.get("memory_mb", default_limits.memory_mb),
                    cpu_percent=cmd.get("cpu_percent", default_limits.cpu_percent),
                    timeout=cmd.get("timeout", default_limits.timeout)
                )
                working_dir = cmd.get("working_dir")
                env = cmd.get("env")
            else:
                command = cmd
                limits = default_limits
                working_dir = None
                env = None

            future = run_command_with_limits.submit(
                command,
                limits=limits,
                working_dir=working_dir,
                env=env
            )
            batch_futures.append(future)

        # Wait for batch to complete
        for future in batch_futures:
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                logger.error(f"Error in batch execution: {e}")
                error_result = {
                    "command": "unknown",
                    "returncode": -1,
                    "stdout": "",
                    "stderr": str(e),
                    "error": True
                }
                results.append(error_result)

    logger.info(f"Completed batch execution: {len(results)} results")
    return results


@task(
    name="save-results",
    description="Save execution results to file"
)
def save_results(results: list[dict], output_path: Path):
    """Save execution results to YAML file"""
    logger = get_run_logger()

    # Prepare results for YAML
    output_data = {
        "execution_time": datetime.now().isoformat(),
        "total_commands": len(results),
        "successful": sum(1 for r in results if r.get("returncode") == 0),
        "failed": sum(1 for r in results if r.get("returncode") != 0),
        "results": results
    }

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save to YAML
    with open(output_path, 'w') as f:
        yaml.dump(output_data, f, default_flow_style=False, sort_keys=False)

    logger.info(f"Results saved to {output_path}")


def load_command_file(file_path: Path) -> list[str | dict]:
    """Load commands from a YAML or text file"""
    if not file_path.exists():
        raise FileNotFoundError(f"Command file not found: {file_path}")

    if file_path.suffix in ['.yaml', '.yml']:
        with open(file_path) as f:
            data = yaml.safe_load(f)
            if isinstance(data, dict) and 'commands' in data:
                return data['commands']
            elif isinstance(data, list):
                return data
            else:
                raise ValueError("Invalid YAML format: expected 'commands' key or list")
    else:
        # Plain text file with one command per line
        with open(file_path) as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]


# Export public API
__all__ = [
    'GuardianConfig',
    'GuardianResult',
    'ResourceLimits',
    'check_system_resources',
    'validate_command',
    'run_command_with_limits',
    'monitor_process',
    'run_with_guardian',
    'guardian_sequential_flow',
    'guardian_batch_flow',
    'save_results',
    'load_command_file',
]


if __name__ == "__main__":
    # Example usage
    example_commands = [
        "echo 'Hello from Prefect Guardian'",
        {"command": "sleep 2", "timeout": 5},
        {"command": "python -c 'print(\"Python test\")'", "memory_mb": 512},
        "date"
    ]

    # Run sequential flow
    results = guardian_sequential_flow(example_commands)

    # Save results
    output_path = Path(".dht") / "guardian_results.yaml"
    save_results(results, output_path)
