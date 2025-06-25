#!/usr/bin/env python3
"""
Dhtl Guardian Command module.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Python replacement for dhtl_guardian_command.sh
# - Implements guardian command for process management
# - Uses Prefect-based guardian system
# - Integrated with DHT command dispatcher
#

"""
DHT Guardian Command Module.

Provides process management with resource limits using Prefect.
"""

import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore[assignment]

from .dhtl_error_handling import log_error, log_info, log_success, log_warning
from .guardian_prefect import (
    ResourceLimits,
    guardian_batch_flow,
    guardian_sequential_flow,
    load_command_file,
    save_results,
)


def guardian_command(args: list[str]) -> int:
    """Manage process guardian for resource-limited execution."""
    log_info("🛡️  Process Guardian Management")

    # Parse subcommand
    if not args:
        show_guardian_help()
        return 0

    subcommand = args[0]
    remaining_args = args[1:] if len(args) > 1 else []

    if subcommand == "run":
        return guardian_run(remaining_args)
    elif subcommand == "batch":
        return guardian_batch(remaining_args)
    elif subcommand == "config":
        return guardian_config(remaining_args)
    elif subcommand == "status":
        return guardian_status(remaining_args)
    else:
        log_error(f"Unknown guardian subcommand: {subcommand}")
        show_guardian_help()
        return 1


def show_guardian_help() -> None:
    """Show guardian command help."""
    print("""
Guardian Command - Process resource management

Usage: dhtl guardian <subcommand> [options]

Subcommands:
  run <command>       Run a single command with resource limits
  batch <file>        Run commands from file with resource management
  config              Show/set guardian configuration
  status              Show guardian status and resources

Run options:
  --memory <MB>       Memory limit in MB (default: 2048)
  --timeout <sec>     Timeout in seconds (default: 900)
  --cpu <percent>     CPU limit percentage (default: 100)

Batch options:
  --size <N>          Batch size for parallel execution (default: 5)
  --sequential        Run commands sequentially
  --stop-on-failure   Stop on first failure (sequential mode)

Examples:
  dhtl guardian run "python script.py" --memory 1024 --timeout 600
  dhtl guardian batch commands.yaml --size 10
  dhtl guardian config --set memory=4096
""")


def guardian_run(args: list[str]) -> int:
    """Run a single command with resource limits."""
    if not args:
        log_error("No command provided")
        log_info("Usage: dhtl guardian run <command> [options]")
        return 1

    # Parse command and options
    command = args[0]
    memory_mb = 2048
    timeout = 900
    cpu_percent = 100

    i = 1
    while i < len(args):
        if args[i] == "--memory" and i + 1 < len(args):
            try:
                memory_mb = int(args[i + 1])
                i += 1
            except ValueError:
                log_error(f"Invalid memory value: {args[i + 1]}")
                return 1
        elif args[i] == "--timeout" and i + 1 < len(args):
            try:
                timeout = int(args[i + 1])
                i += 1
            except ValueError:
                log_error(f"Invalid timeout value: {args[i + 1]}")
                return 1
        elif args[i] == "--cpu" and i + 1 < len(args):
            try:
                cpu_percent = int(args[i + 1])
                i += 1
            except ValueError:
                log_error(f"Invalid CPU value: {args[i + 1]}")
                return 1
        i += 1

    log_info("Running command with guardian protection:")
    log_info(f"  Command: {command}")
    log_info(f"  Memory: {memory_mb}MB")
    log_info(f"  Timeout: {timeout}s")
    log_info(f"  CPU: {cpu_percent}%")

    # Create limits
    limits = ResourceLimits(memory_mb, cpu_percent, timeout)

    # Run with guardian
    results = guardian_sequential_flow(commands=[command], stop_on_failure=True, default_limits=limits)

    if results and results[0]["returncode"] == 0:
        log_success("Command completed successfully")
        if results[0].get("stdout"):
            print(results[0]["stdout"])
        return 0
    else:
        log_error("Command failed")
        if results and results[0].get("stderr"):
            print(results[0]["stderr"], file=sys.stderr)
        return 1


def guardian_batch(args: list[str]) -> int:
    """Run commands from file with resource management."""
    if not args:
        log_error("No command file provided")
        log_info("Usage: dhtl guardian batch <file> [options]")
        return 1

    command_file = Path(args[0])
    if not command_file.exists():
        log_error(f"Command file not found: {command_file}")
        return 1

    # Parse options
    batch_size = 5
    sequential = False
    stop_on_failure = False
    memory_mb = 2048
    timeout = 900
    cpu_percent = 100

    i = 1
    while i < len(args):
        if args[i] == "--size" and i + 1 < len(args):
            try:
                batch_size = int(args[i + 1])
                i += 1
            except ValueError:
                log_error(f"Invalid batch size: {args[i + 1]}")
                return 1
        elif args[i] == "--sequential":
            sequential = True
        elif args[i] == "--stop-on-failure":
            stop_on_failure = True
        elif args[i] == "--memory" and i + 1 < len(args):
            memory_mb = int(args[i + 1])
            i += 1
        elif args[i] == "--timeout" and i + 1 < len(args):
            timeout = int(args[i + 1])
            i += 1
        elif args[i] == "--cpu" and i + 1 < len(args):
            cpu_percent = int(args[i + 1])
            i += 1
        i += 1

    # Load commands
    try:
        commands = load_command_file(command_file)
        log_info(f"Loaded {len(commands)} commands from {command_file}")
    except Exception as e:
        log_error(f"Failed to load commands: {e}")
        return 1

    # Create default limits
    limits = ResourceLimits(memory_mb, cpu_percent, timeout)

    # Run commands
    if sequential:
        log_info("Running commands sequentially...")
        results = guardian_sequential_flow(commands=commands, stop_on_failure=stop_on_failure, default_limits=limits)
    else:
        log_info(f"Running commands in batches of {batch_size}...")
        results = guardian_batch_flow(commands=commands, batch_size=batch_size, default_limits=limits)

    # Save results
    output_path = Path(".dht") / "guardian_results.yaml"
    save_results(results, output_path)

    # Summary
    successful = sum(1 for r in results if r.get("returncode") == 0)
    failed = len(results) - successful

    log_info("\nExecution Summary:")
    log_info(f"  Total: {len(results)}")
    log_success(f"  Successful: {successful}")
    if failed > 0:
        log_error(f"  Failed: {failed}")

    return 0 if failed == 0 else 1


def guardian_config(args: list[str]) -> int:
    """Show or set guardian configuration."""
    config_path = Path.home() / ".config" / "dht" / "guardian.yaml"

    # Parse options
    set_values = {}
    show_only = True

    i = 0
    while i < len(args):
        if args[i] == "--set" and i + 1 < len(args):
            # Parse key=value
            try:
                key, value = args[i + 1].split("=", 1)
                if key in ["memory", "timeout", "cpu"]:
                    set_values[key] = int(value)
                    show_only = False
                else:
                    log_error(f"Unknown config key: {key}")
                    return 1
            except ValueError:
                log_error(f"Invalid format: {args[i + 1]} (use key=value)")
                return 1
            i += 1
        i += 1

    # Load existing config
    config: dict[str, Any] = {}
    if config_path.exists():
        try:
            with open(config_path) as f:
                config = yaml.safe_load(f) or {}
        except Exception as e:
            log_warning(f"Could not load config: {e}")

    # Update config if needed
    if not show_only:
        config.update(set_values)

        # Save config
        config_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(config_path, "w") as f:
                yaml.dump(config, f, default_flow_style=False)
            log_success(f"Configuration saved to {config_path}")
        except Exception as e:
            log_error(f"Failed to save config: {e}")
            return 1

    # Show config
    log_info("Guardian Configuration:")
    log_info(f"  Memory limit: {config.get('memory', 2048)}MB")
    log_info(f"  Timeout: {config.get('timeout', 900)}s")
    log_info(f"  CPU limit: {config.get('cpu', 100)}%")

    return 0


def guardian_status(args: list[str]) -> int:
    """Show guardian status and system resources."""
    log_info("🛡️  Guardian Status")
    log_info("=" * 50)

    # Check system resources
    try:
        import psutil

        # Memory
        memory = psutil.virtual_memory()
        log_info("\n📊 Memory:")
        log_info(f"  Total: {memory.total / (1024**3):.1f}GB")
        log_info(f"  Available: {memory.available / (1024**3):.1f}GB ({100 - memory.percent:.1f}%)")
        log_info(f"  Used: {memory.used / (1024**3):.1f}GB ({memory.percent:.1f}%)")

        # CPU
        cpu_count = psutil.cpu_count()
        cpu_percent = psutil.cpu_percent(interval=1)
        log_info("\n💻 CPU:")
        log_info(f"  Cores: {cpu_count}")
        log_info(f"  Usage: {cpu_percent:.1f}%")

        # Disk
        disk = psutil.disk_usage("/")
        log_info("\n💾 Disk:")
        log_info(f"  Total: {disk.total / (1024**3):.1f}GB")
        log_info(f"  Free: {disk.free / (1024**3):.1f}GB ({100 - disk.percent:.1f}%)")

    except ImportError:
        log_warning("psutil not available - cannot show system resources")
        log_info("Install psutil: uv pip install psutil")

    # Check for recent results
    results_path = Path(".dht") / "guardian_results.yaml"
    if results_path.exists():
        try:
            with open(results_path) as f:
                data = yaml.safe_load(f)

            log_info("\n📄 Last Execution:")
            log_info(f"  Time: {data.get('execution_time', 'Unknown')}")
            log_info(f"  Commands: {data.get('total_commands', 0)}")
            log_info(f"  Successful: {data.get('successful', 0)}")
            log_info(f"  Failed: {data.get('failed', 0)}")
        except Exception:
            pass

    return 0


# For backward compatibility
def placeholder_command(*args: Any, **kwargs: Any) -> int:
    """Placeholder command implementation."""
    return guardian_command(*args, **kwargs)


# Export command functions
__all__ = ["guardian_command", "placeholder_command"]
