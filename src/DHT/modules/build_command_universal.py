#!/usr/bin/env python3

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Created universal build command using Prefect
# - Integrates with universal_build_detector
# - Replaces old bash-based build with Prefect flows
#

"""
Universal build command for DHT using Prefect.
"""

import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from act_integration import ActIntegration
from prefect import flow, get_run_logger, task
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from universal_build_detector import UniversalBuildDetector

console = Console()


@task(name="detect_build_config")  # type: ignore[misc]
def detect_build_config(project_path: Path) -> dict[str, Any]:
    """Detect build configuration for the project."""
    logger = get_run_logger()
    logger.info(f"Detecting build configuration for: {project_path}")

    detector = UniversalBuildDetector(project_path)
    summary = detector.get_build_summary()

    return summary


@task(name="run_pre_build_commands")  # type: ignore[misc]
def run_pre_build_commands(commands: list[str], project_path: Path) -> bool:
    """Run pre-build commands like dependency installation."""
    logger = get_run_logger()

    for cmd in commands:
        logger.info(f"Running pre-build: {cmd}")
        try:
            result = subprocess.run(cmd, shell=True, cwd=str(project_path), capture_output=True, text=True, timeout=300)
            if result.returncode != 0:
                logger.error(f"Pre-build command failed: {cmd}")
                logger.error(result.stderr)
                return False
        except subprocess.TimeoutExpired:
            logger.error(f"Pre-build command timed out: {cmd}")
            return False

    return True


@task(name="run_build_commands")  # type: ignore[misc]
def run_build_commands(commands: list[str], project_path: Path) -> dict[str, Any]:
    """Run the actual build commands."""
    logger = get_run_logger()

    results = []

    for cmd in commands:
        logger.info(f"Running build: {cmd}")
        console.print(f"[cyan]🔨 Executing:[/cyan] {cmd}")

        start_time = time.time()
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                cwd=str(project_path),
                capture_output=True,
                text=True,
                timeout=900,  # 15 minutes for complex builds
            )
            duration = time.time() - start_time

            results.append(
                {
                    "command": cmd,
                    "success": result.returncode == 0,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "duration": duration,
                }
            )

            if result.returncode != 0:
                logger.error(f"Build command failed: {cmd}")
                console.print(f"[red]❌ Build failed:[/red] {cmd}")
                if result.stderr:
                    console.print(Panel(result.stderr, title="Error Output", style="red"))
                break
            else:
                console.print(f"[green]✅ Success[/green] ({duration:.1f}s)")

        except subprocess.TimeoutExpired:
            logger.error(f"Build command timed out: {cmd}")
            results.append(
                {
                    "command": cmd,
                    "success": False,
                    "stdout": "",
                    "stderr": "Command timed out after 900 seconds",
                    "duration": 900,
                }
            )
            break

    return {"all_success": all(r["success"] for r in results), "results": results}


@task(name="check_artifacts")  # type: ignore[misc]
def check_artifacts(artifacts_path: str | None, project_path: Path) -> list[str]:
    """Check what artifacts were created."""
    if not artifacts_path:
        return []

    artifacts_dir = project_path / artifacts_path
    if not artifacts_dir.exists():
        return []

    artifacts = []
    for item in artifacts_dir.rglob("*"):
        if item.is_file():
            # Get relative path from project root
            rel_path = item.relative_to(project_path)
            artifacts.append(str(rel_path))

    return sorted(artifacts)


@flow(name="universal_build")  # type: ignore[misc]
def universal_build_flow(project_path: str, skip_checks: bool = False, verbose: bool = False) -> dict[str, Any]:
    """
    Universal build flow for any project type.

    Args:
        project_path: Path to the project
        skip_checks: Skip pre-build checks (linting, etc.)
        verbose: Show detailed output

    Returns:
        Dictionary with build results
    """
    logger = get_run_logger()
    project_path = Path(project_path).resolve()

    console.print(Panel.fit(f"🏗️  DHT Universal Build System\n📁 Project: {project_path.name}", style="bold blue"))

    # 1. Detect build configuration
    console.print("\n[yellow]🔍 Detecting project type...[/yellow]")
    config = detect_build_config(project_path)

    if not config["can_build"]:
        # No build needed
        console.print(f"\n[yellow]ℹ️  {config['reason']}[/yellow]")

        if config.get("suggestions"):
            console.print("\n[dim]Suggestions:[/dim]")
            for suggestion in config["suggestions"]:
                console.print(f"  [dim]•[/dim] {suggestion}")

        return {"success": True, "can_build": False, "reason": config["reason"]}

    # 2. Display build plan
    console.print("\n[green]✅ Build configuration detected![/green]")

    table = Table(title="Build Configuration", show_header=True)
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="white")

    table.add_row("Project Type", config["project_type"])
    table.add_row("Build Tool", config["build_tool"])
    table.add_row("Commands", "\n".join(config["build_commands"]))
    if config.get("artifacts_path"):
        table.add_row("Output", config["artifacts_path"])

    console.print(table)

    # 3. Run pre-build commands if any
    pre_commands = config.get("pre_build_commands", [])
    if pre_commands and not skip_checks:
        console.print("\n[yellow]📋 Running pre-build steps...[/yellow]")
        success = run_pre_build_commands(pre_commands, project_path)
        if not success:
            return {"success": False, "error": "Pre-build commands failed"}

    # 4. Clean previous artifacts
    if config.get("artifacts_path"):
        artifacts_dir = project_path / config["artifacts_path"]
        if artifacts_dir.exists():
            console.print(f"\n[yellow]🧹 Cleaning {config['artifacts_path']}...[/yellow]")
            import shutil

            shutil.rmtree(artifacts_dir)

    # 5. Run build commands
    console.print("\n[cyan]🔨 Building project...[/cyan]")
    build_results = run_build_commands(config["build_commands"], project_path)

    if not build_results["all_success"]:
        return {"success": False, "error": "Build failed", "details": build_results["results"]}

    # 6. Check artifacts
    artifacts = []
    if config.get("artifacts_path"):
        console.print("\n[yellow]📦 Checking build artifacts...[/yellow]")
        artifacts = check_artifacts(config["artifacts_path"], project_path)

        if artifacts:
            console.print("\n[green]✅ Build artifacts created:[/green]")
            for artifact in artifacts:
                console.print(f"  📦 {artifact}")
        else:
            console.print(f"\n[yellow]⚠️  No artifacts found in {config['artifacts_path']}[/yellow]")

    # 7. Summary
    total_duration = sum(r["duration"] for r in build_results["results"])

    console.print(
        Panel.fit(
            f"[green]✅ Build completed successfully![/green]\n"
            f"⏱️  Total time: {total_duration:.1f}s\n"
            f"📦 Artifacts: {len(artifacts)}",
            style="bold green",
        )
    )

    # 8. Check for GitHub Actions workflows
    act_integration = ActIntegration(project_path)
    if act_integration.has_workflows():
        console.print("\n[yellow]🎬 GitHub Actions detected![/yellow]")
        workflows = act_integration.get_workflows()
        console.print(f"Found {len(workflows)} workflow(s):")
        for workflow in workflows[:3]:  # Show first 3
            console.print(f"  • {workflow['name']} ({workflow['file']})")

        console.print("\n💡 [dim]Tip: Use [bold]dhtl act[/bold] to test workflows locally[/dim]")

    return {
        "success": True,
        "project_type": config["project_type"],
        "build_tool": config["build_tool"],
        "duration": total_duration,
        "artifacts": artifacts,
        "artifacts_count": len(artifacts),
        "has_workflows": act_integration.has_workflows(),
    }


def main() -> None:
    """CLI interface for universal build."""
    import argparse

    parser = argparse.ArgumentParser(description="DHT Universal Build")
    parser.add_argument("path", nargs="?", default=".", help="Project path")
    parser.add_argument("--no-checks", action="store_true", help="Skip pre-build checks")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()

    # Run the build flow
    result = universal_build_flow(project_path=args.path, skip_checks=args.no_checks, verbose=args.verbose)

    # Exit with appropriate code
    sys.exit(0 if result["success"] else 1)


if __name__ == "__main__":
    main()
