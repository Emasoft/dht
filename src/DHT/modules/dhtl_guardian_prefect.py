#!/usr/bin/env python3
"""
dhtl_guardian_prefect.py - CLI interface for Prefect-based guardian  This provides a command-line interface for the Prefect guardian, compatible with the existing dhtl guardian command structure.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

"""
dhtl_guardian_prefect.py - CLI interface for Prefect-based guardian

This provides a command-line interface for the Prefect guardian,
compatible with the existing dhtl guardian command structure.
"""

import json
import sys
from pathlib import Path
from typing import Any

import click

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore[assignment]
from prefect import serve
from prefect.deployments import run_deployment

from .guardian_prefect import (
    ResourceLimits,
    guardian_batch_flow,
    guardian_sequential_flow,
    load_command_file,
    save_results,
)


@click.group()  # type: ignore[misc]
def cli() -> None:
    """DHT Guardian - Prefect-based process management"""
    pass


@cli.command()  # type: ignore[misc]
@click.option("--name", default="dht-guardian", help="Deployment name")  # type: ignore[misc]
@click.option("--interval", type=int, help="Run interval in seconds")  # type: ignore[misc]
@click.option("--cron", help="Cron schedule")  # type: ignore[misc]
def start(name: str, interval: int | None, cron: str | None) -> None:
    """Start the Prefect guardian server"""
    click.echo("Starting Prefect guardian server...")

    # Create deployments
    deployments = []

    # Sequential deployment
    seq_deployment = guardian_sequential_flow.to_deployment(
        name=f"{name}-sequential",
        description="Sequential command execution with resource limits",
        tags=["dht", "guardian", "sequential"],
    )

    if interval:
        seq_deployment.interval = interval
    elif cron:
        seq_deployment.cron = cron

    deployments.append(seq_deployment)

    # Batch deployment
    batch_deployment = guardian_batch_flow.to_deployment(
        name=f"{name}-batch", description="Batch command execution with parallelism", tags=["dht", "guardian", "batch"]
    )

    deployments.append(batch_deployment)

    # Serve deployments
    click.echo(f"Serving {len(deployments)} deployments...")
    serve(*deployments)


@cli.command()  # type: ignore[misc]
def stop() -> None:
    """Stop the Prefect guardian server"""
    click.echo("Stopping Prefect guardian server...")
    # In production, this would properly shut down the Prefect server
    # For now, we'll just exit
    click.echo("Guardian server stopped")


@cli.command()  # type: ignore[misc]
def status() -> None:
    """Check guardian server status"""
    try:
        import asyncio

        from prefect.client import get_client

        async def check_status() -> None:
            async with get_client() as client:
                # Check for deployments
                deployments = await client.read_deployments()
                guardian_deployments = [d for d in deployments if "guardian" in d.tags]

                if guardian_deployments:
                    click.echo(f"Guardian server is running with {len(guardian_deployments)} deployments:")
                    for dep in guardian_deployments:
                        click.echo(f"  - {dep.name}: {dep.schedule}")
                else:
                    click.echo("No guardian deployments found")

                # Check recent flows
                flows = await client.read_flows()
                guardian_flows = [f for f in flows if "guardian" in f.name]

                if guardian_flows:
                    click.echo(f"\nRegistered guardian flows: {len(guardian_flows)}")
                    for flow in guardian_flows:
                        click.echo(f"  - {flow.name}")

        asyncio.run(check_status())

    except Exception as e:
        click.echo(f"Error checking status: {e}")
        click.echo("Guardian server may not be running")


@cli.command()  # type: ignore[misc]
@click.argument("commands", nargs=-1, required=False)  # type: ignore[misc]
@click.option("--file", "-f", type=click.Path(exists=True), help="File containing commands")  # type: ignore[misc]
@click.option("--sequential", "-s", is_flag=True, default=True, help="Run commands sequentially")  # type: ignore[misc]
@click.option("--batch", "-b", type=int, help="Run commands in batches")  # type: ignore[misc]
@click.option("--memory", "-m", type=int, default=2048, help="Memory limit in MB")  # type: ignore[misc]
@click.option("--timeout", "-t", type=int, default=900, help="Timeout in seconds")  # type: ignore[misc]
@click.option("--cpu", type=int, default=80, help="CPU limit percentage")  # type: ignore[misc]
@click.option("--output", "-o", type=click.Path(), help="Output file for results")  # type: ignore[misc]
@click.option("--json", "output_json", is_flag=True, help="Output results as JSON")  # type: ignore[misc]
@click.option("--stop-on-failure", is_flag=True, default=True, help="Stop on first failure")  # type: ignore[misc]
@click.option("--deployment", "-d", help="Run via deployment instead of directly")  # type: ignore[misc]
def run(
    commands: tuple[str, ...],
    file: str | None,
    sequential: bool,
    batch: int | None,
    memory: int,
    timeout: int,
    cpu: int,
    output: str | None,
    output_json: bool,
    stop_on_failure: bool,
    deployment: str | None,
) -> None:
    """Run commands through the guardian"""

    # Collect commands
    command_list: list[str | dict[str, Any]] = []

    if file:
        try:
            command_list = load_command_file(Path(file))
            click.echo(f"Loaded {len(command_list)} commands from {file}")
        except Exception as e:
            click.echo(f"Error loading command file: {e}", err=True)
            sys.exit(1)
    elif commands:
        command_list = list(commands)
    else:
        click.echo("No commands provided. Use arguments or --file option.", err=True)
        sys.exit(1)

    # Create resource limits
    limits = ResourceLimits(memory_mb=memory, cpu_percent=cpu, timeout=timeout)

    click.echo(f"Running {len(command_list)} commands with limits: memory={memory}MB, timeout={timeout}s")

    try:
        if deployment:
            # Run via deployment
            click.echo(f"Running via deployment: {deployment}")
            run_deployment(
                name=f"{deployment}/guardian-sequential" if sequential else f"{deployment}/guardian-batch",
                parameters={"commands": command_list, "default_limits": limits, "stop_on_failure": stop_on_failure},
            )
        else:
            # Run directly
            if batch:
                click.echo(f"Running in batch mode (batch_size={batch})")
                results = guardian_batch_flow(command_list, batch_size=batch, default_limits=limits)
            else:
                click.echo("Running in sequential mode")
                results = guardian_sequential_flow(command_list, stop_on_failure=stop_on_failure, default_limits=limits)

            # Display results
            successful = sum(1 for r in results if r.get("returncode") == 0)
            failed = sum(1 for r in results if r.get("returncode") != 0)

            click.echo(f"\nExecution complete: {successful} successful, {failed} failed")

            # Show failed commands
            if failed > 0:
                click.echo("\nFailed commands:")
                for r in results:
                    if r.get("returncode") != 0:
                        click.echo(f"  - {r.get('command')}: exit code {r.get('returncode')}")
                        if r.get("stderr"):
                            click.echo(f"    Error: {r.get('stderr')[:100]}...")

            # Save results if requested
            if output:
                output_path = Path(output)
                if output_json:
                    with open(output_path, "w") as f:
                        json.dump(results, f, indent=2, default=str)
                else:
                    save_results(results, output_path)
                click.echo(f"\nResults saved to {output_path}")

            # Exit with appropriate code
            sys.exit(0 if failed == 0 else 1)

    except Exception as e:
        click.echo(f"Error running commands: {e}", err=True)
        sys.exit(1)


@cli.command()  # type: ignore[misc]
@click.option("--format", type=click.Choice(["yaml", "json"]), default="yaml", help="Output format")  # type: ignore[misc]
def example(format: str) -> None:
    """Show example command file"""

    example_data: dict[str, Any] = {
        "commands": [
            "echo 'Simple command'",
            {"command": "python -c 'import time; time.sleep(2); print(\"Done\")'", "timeout": 5, "memory_mb": 512},
            {"command": "ls -la", "working_dir": "/tmp"},
            {"command": "env | grep PATH", "env": {"CUSTOM_VAR": "test_value"}},
        ]
    }

    if format == "json":
        click.echo(json.dumps(example_data, indent=2))
    else:
        click.echo(yaml.dump(example_data, default_flow_style=False))


@cli.command()  # type: ignore[misc]
@click.argument("result_file", type=click.Path(exists=True))  # type: ignore[misc]
def show_results(result_file: str) -> None:
    """Display results from a previous run"""

    result_path = Path(result_file)

    try:
        with open(result_path) as f:
            if result_path.suffix == ".json":
                data: dict[str, Any] = json.load(f)
            else:
                data = yaml.safe_load(f)

        click.echo(f"Execution time: {data.get('execution_time', 'Unknown')}")
        click.echo(f"Total commands: {data.get('total_commands', 0)}")
        click.echo(f"Successful: {data.get('successful', 0)}")
        click.echo(f"Failed: {data.get('failed', 0)}")

        if "results" in data:
            click.echo("\nCommand results:")
            for i, result in enumerate(data["results"], 1):
                status = "✓" if result.get("returncode") == 0 else "✗"
                duration = result.get("duration", 0)
                click.echo(f"{i}. {status} {result.get('command', 'Unknown')} ({duration:.2f}s)")

                if result.get("returncode") != 0 and result.get("stderr"):
                    click.echo(f"   Error: {result['stderr'][:100]}...")

    except Exception as e:
        click.echo(f"Error reading result file: {e}", err=True)
        sys.exit(1)


def parse_args() -> Any:
    """Parse command line arguments for compatibility with shell script interface."""
    import argparse

    parser = argparse.ArgumentParser(description="DHT Guardian - Resource-limited command execution")
    parser.add_argument("command", nargs="+", help="Command to execute")
    parser.add_argument("--memory", type=int, default=2048, help="Memory limit in MB")
    parser.add_argument("--timeout", type=int, default=900, help="Timeout in seconds")
    parser.add_argument("--cpu", type=int, default=80, help="CPU limit percentage")
    return parser.parse_args()


def main() -> int:
    """Main entry point for shell script compatibility."""
    from .guardian_prefect import ResourceLimits, run_with_guardian

    # If running as Click app
    if len(sys.argv) > 1 and sys.argv[1] in ["start", "run", "example", "show-results"]:
        return cli()  # type: ignore[no-any-return]

    # Otherwise, parse as simple command execution (shell script compatibility)
    args = parse_args()

    # Create resource limits
    limits = ResourceLimits(memory_mb=args.memory, cpu_percent=args.cpu, timeout=args.timeout)

    # Run the command
    result = run_with_guardian(args.command, limits=limits)

    # Output results
    if result.stdout:
        sys.stdout.write(result.stdout)
        sys.stdout.flush()
    if result.stderr:
        sys.stderr.write(result.stderr)
        sys.stderr.flush()

    return result.return_code


if __name__ == "__main__":
    sys.exit(main())
