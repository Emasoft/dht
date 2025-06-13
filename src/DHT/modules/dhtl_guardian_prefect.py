#!/usr/bin/env python3
"""
dhtl_guardian_prefect.py - CLI interface for Prefect-based guardian

This provides a command-line interface for the Prefect guardian,
compatible with the existing dhtl guardian command structure.
"""

import click
import sys
import os
from pathlib import Path
from typing import Optional, List
import yaml
import json
from datetime import datetime

from prefect import serve
from prefect.deployments import run_deployment
from .guardian_prefect import (
    guardian_sequential_flow,
    guardian_batch_flow,
    ResourceLimits,
    load_command_file,
    save_results
)


@click.group()
def cli():
    """DHT Guardian - Prefect-based process management"""
    pass


@cli.command()
@click.option('--name', default='dht-guardian', help='Deployment name')
@click.option('--interval', type=int, help='Run interval in seconds')
@click.option('--cron', help='Cron schedule')
def start(name: str, interval: Optional[int], cron: Optional[str]):
    """Start the Prefect guardian server"""
    click.echo(f"Starting Prefect guardian server...")
    
    # Create deployments
    deployments = []
    
    # Sequential deployment
    seq_deployment = guardian_sequential_flow.to_deployment(
        name=f"{name}-sequential",
        description="Sequential command execution with resource limits",
        tags=["dht", "guardian", "sequential"]
    )
    
    if interval:
        seq_deployment.interval = interval
    elif cron:
        seq_deployment.cron = cron
    
    deployments.append(seq_deployment)
    
    # Batch deployment
    batch_deployment = guardian_batch_flow.to_deployment(
        name=f"{name}-batch",
        description="Batch command execution with parallelism",
        tags=["dht", "guardian", "batch"]
    )
    
    deployments.append(batch_deployment)
    
    # Serve deployments
    click.echo(f"Serving {len(deployments)} deployments...")
    serve(*deployments)


@cli.command()
def stop():
    """Stop the Prefect guardian server"""
    click.echo("Stopping Prefect guardian server...")
    # In production, this would properly shut down the Prefect server
    # For now, we'll just exit
    click.echo("Guardian server stopped")


@cli.command()
def status():
    """Check guardian server status"""
    try:
        from prefect.client import get_client
        import asyncio
        
        async def check_status():
            async with get_client() as client:
                # Check for deployments
                deployments = await client.read_deployments()
                guardian_deployments = [d for d in deployments if 'guardian' in d.tags]
                
                if guardian_deployments:
                    click.echo(f"Guardian server is running with {len(guardian_deployments)} deployments:")
                    for dep in guardian_deployments:
                        click.echo(f"  - {dep.name}: {dep.schedule}")
                else:
                    click.echo("No guardian deployments found")
                
                # Check recent flows
                flows = await client.read_flows()
                guardian_flows = [f for f in flows if 'guardian' in f.name]
                
                if guardian_flows:
                    click.echo(f"\nRegistered guardian flows: {len(guardian_flows)}")
                    for flow in guardian_flows:
                        click.echo(f"  - {flow.name}")
        
        asyncio.run(check_status())
        
    except Exception as e:
        click.echo(f"Error checking status: {e}")
        click.echo("Guardian server may not be running")


@cli.command()
@click.argument('commands', nargs=-1, required=False)
@click.option('--file', '-f', type=click.Path(exists=True), help='File containing commands')
@click.option('--sequential', '-s', is_flag=True, default=True, help='Run commands sequentially')
@click.option('--batch', '-b', type=int, help='Run commands in batches')
@click.option('--memory', '-m', type=int, default=2048, help='Memory limit in MB')
@click.option('--timeout', '-t', type=int, default=900, help='Timeout in seconds')
@click.option('--cpu', type=int, default=80, help='CPU limit percentage')
@click.option('--output', '-o', type=click.Path(), help='Output file for results')
@click.option('--json', 'output_json', is_flag=True, help='Output results as JSON')
@click.option('--stop-on-failure', is_flag=True, default=True, help='Stop on first failure')
@click.option('--deployment', '-d', help='Run via deployment instead of directly')
def run(
    commands: tuple,
    file: Optional[str],
    sequential: bool,
    batch: Optional[int],
    memory: int,
    timeout: int,
    cpu: int,
    output: Optional[str],
    output_json: bool,
    stop_on_failure: bool,
    deployment: Optional[str]
):
    """Run commands through the guardian"""
    
    # Collect commands
    command_list = []
    
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
    limits = ResourceLimits(
        memory_mb=memory,
        cpu_percent=cpu,
        timeout=timeout
    )
    
    click.echo(f"Running {len(command_list)} commands with limits: memory={memory}MB, timeout={timeout}s")
    
    try:
        if deployment:
            # Run via deployment
            click.echo(f"Running via deployment: {deployment}")
            run_deployment(
                name=f"{deployment}/guardian-sequential" if sequential else f"{deployment}/guardian-batch",
                parameters={
                    "commands": command_list,
                    "default_limits": limits,
                    "stop_on_failure": stop_on_failure
                }
            )
        else:
            # Run directly
            if batch:
                click.echo(f"Running in batch mode (batch_size={batch})")
                results = guardian_batch_flow(
                    command_list,
                    batch_size=batch,
                    default_limits=limits
                )
            else:
                click.echo("Running in sequential mode")
                results = guardian_sequential_flow(
                    command_list,
                    stop_on_failure=stop_on_failure,
                    default_limits=limits
                )
            
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
                    with open(output_path, 'w') as f:
                        json.dump(results, f, indent=2, default=str)
                else:
                    save_results(results, output_path)
                click.echo(f"\nResults saved to {output_path}")
            
            # Exit with appropriate code
            sys.exit(0 if failed == 0 else 1)
            
    except Exception as e:
        click.echo(f"Error running commands: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--format', type=click.Choice(['yaml', 'json']), default='yaml', help='Output format')
def example(format: str):
    """Show example command file"""
    
    example_data = {
        "commands": [
            "echo 'Simple command'",
            {
                "command": "python -c 'import time; time.sleep(2); print(\"Done\")'",
                "timeout": 5,
                "memory_mb": 512
            },
            {
                "command": "ls -la",
                "working_dir": "/tmp"
            },
            {
                "command": "env | grep PATH",
                "env": {
                    "CUSTOM_VAR": "test_value"
                }
            }
        ]
    }
    
    if format == 'json':
        click.echo(json.dumps(example_data, indent=2))
    else:
        click.echo(yaml.dump(example_data, default_flow_style=False))


@cli.command()
@click.argument('result_file', type=click.Path(exists=True))
def show_results(result_file: str):
    """Display results from a previous run"""
    
    result_path = Path(result_file)
    
    try:
        with open(result_path, 'r') as f:
            if result_path.suffix == '.json':
                data = json.load(f)
            else:
                data = yaml.safe_load(f)
        
        click.echo(f"Execution time: {data.get('execution_time', 'Unknown')}")
        click.echo(f"Total commands: {data.get('total_commands', 0)}")
        click.echo(f"Successful: {data.get('successful', 0)}")
        click.echo(f"Failed: {data.get('failed', 0)}")
        
        if 'results' in data:
            click.echo("\nCommand results:")
            for i, result in enumerate(data['results'], 1):
                status = "✓" if result.get('returncode') == 0 else "✗"
                duration = result.get('duration', 0)
                click.echo(f"{i}. {status} {result.get('command', 'Unknown')} ({duration:.2f}s)")
                
                if result.get('returncode') != 0 and result.get('stderr'):
                    click.echo(f"   Error: {result['stderr'][:100]}...")
                    
    except Exception as e:
        click.echo(f"Error reading result file: {e}", err=True)
        sys.exit(1)


def parse_args():
    """Parse command line arguments for compatibility with shell script interface."""
    import argparse
    parser = argparse.ArgumentParser(description='DHT Guardian - Resource-limited command execution')
    parser.add_argument('command', nargs='+', help='Command to execute')
    parser.add_argument('--memory', type=int, default=2048, help='Memory limit in MB')
    parser.add_argument('--timeout', type=int, default=900, help='Timeout in seconds')
    parser.add_argument('--cpu', type=int, default=80, help='CPU limit percentage')
    return parser.parse_args()


def main():
    """Main entry point for shell script compatibility."""
    from .guardian_prefect import run_with_guardian, ResourceLimits, GuardianResult
    
    # If running as Click app
    if len(sys.argv) > 1 and sys.argv[1] in ['start', 'run', 'example', 'show-results']:
        return cli()
    
    # Otherwise, parse as simple command execution (shell script compatibility)
    args = parse_args()
    
    # Create resource limits
    limits = ResourceLimits(
        memory_mb=args.memory,
        cpu_percent=args.cpu,
        timeout=args.timeout
    )
    
    # Run the command
    result = run_with_guardian(args.command, limits=limits)
    
    # Output results
    if result.stdout:
        print(result.stdout, end='')
    if result.stderr:
        print(result.stderr, file=sys.stderr, end='')
    
    return result.return_code


if __name__ == "__main__":
    sys.exit(main())