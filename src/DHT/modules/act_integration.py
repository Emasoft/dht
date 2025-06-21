#!/usr/bin/env python3

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Created act integration module for local GitHub Actions testing
# - Integrates with container build system for isolation
# - Supports both standalone act and gh extension
# - Provides deterministic CI/CD testing environment
# - Refactored into smaller modules to reduce file size
#

"""
Act integration for DHT - Run GitHub Actions locally.
Provides isolated, deterministic CI/CD testing environment.
"""

import subprocess
from pathlib import Path
from typing import Any

from prefect import flow, get_run_logger, task
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from DHT.modules.act_command_builder import ActCommandBuilder
from DHT.modules.act_container_manager import ActContainerManager

# Import extracted modules
from DHT.modules.act_integration_models import ActCheckResult, ActConfig, WorkflowInfo
from DHT.modules.act_linter import ActLinter
from DHT.modules.act_setup_manager import ActSetupManager
from DHT.modules.act_workflow_manager import ActWorkflowManager

console = Console()

# Check if container runner is available
try:
    import importlib.util

    HAS_CONTAINER_RUNNER = importlib.util.find_spec("act_container_setup") is not None
except ImportError:
    HAS_CONTAINER_RUNNER = False


class ActIntegration:
    """Integrates act with DHT for local GitHub Actions testing."""

    def __init__(self, project_path: Path):
        self.project_path = Path(project_path).resolve()
        self.workflows_path = self.project_path / ".github" / "workflows"
        self.venv_path = self.project_path / ".venv"
        self.act_config_path = self.venv_path / "dht-act"
        self.container_config = None

        # Initialize helper classes
        self.workflow_manager = ActWorkflowManager(project_path)
        self.linter = ActLinter(project_path)
        self.setup_manager = ActSetupManager(project_path)
        self.container_manager = ActContainerManager(project_path)

    def has_workflows(self) -> bool:
        """Check if project has GitHub workflows."""
        return self.workflow_manager.has_workflows()

    def get_workflows(self) -> list[WorkflowInfo]:
        """Get list of workflows with their metadata."""
        return self.workflow_manager.get_workflows()

    def lint_workflows(self, use_docker: bool = False) -> dict[str, Any]:
        """Lint GitHub Actions workflows using actionlint.

        Actionlint performs static analysis of workflow files to catch:
        - Syntax errors
        - Invalid action references
        - Type mismatches
        - Shell script issues (via shellcheck)

        This is different from 'act' which actually executes workflows.
        """
        return self.linter.lint_workflows(use_docker=use_docker)

    def _check_docker_available(self) -> bool:
        """Check if Docker is available."""
        return self.linter._check_docker_available()

    def lint_with_docker(self, tag: str = "latest", color: bool = True) -> dict[str, Any]:
        """Run actionlint using official Docker image.

        This is the recommended way to run actionlint as it includes
        all dependencies (shellcheck, pyflakes) in the container.
        """
        return self.linter.lint_with_docker(tag=tag, color=color)

    def _parse_actionlint_output(self, output: str, results: dict[str, Any]) -> None:
        """Parse actionlint JSON output and update results."""
        return self.linter._parse_actionlint_output(output, results)

    def check_act_available(self) -> ActCheckResult:
        """Check if act is available via various methods."""
        result = self.setup_manager.check_act_available()
        # Convert to legacy format for compatibility
        return {
            "gh_extension": result.act_extension_installed,
            "standalone_act": result.standalone_act_available,
            "container_act": self.container_manager.setup_container_environment().runtime_available,
            "preferred_method": result.preferred_method,
        }

    def install_gh_act_extension(self) -> bool:
        """Install the gh act extension."""
        return self.setup_manager.install_gh_act_extension()

    def setup_act_config(self, config: ActConfig | None = None) -> Path:
        """Set up act configuration in project."""
        return self.setup_manager.setup_act_config(config)

    def _get_container_socket(self, runtime: str) -> str:
        """Get container runtime socket path."""
        return self.container_manager._get_container_socket(runtime)

    def _get_container_act_command(self) -> list[str]:
        """Get command to run act inside a container."""
        return self.container_manager._get_container_act_command(ActConfig())

    def setup_container_environment(self) -> dict[str, Any]:
        """Set up container environment for act."""
        container_result = self.container_manager.setup_container_environment()
        # Convert to legacy format for compatibility
        return {
            "container_config_created": container_result.success,
            "act_image_available": container_result.success,
            "runtime_available": container_result.runtime_available,
            "runtime": container_result.runtime,
            "error": container_result.error,
        }

    def get_act_command(self, event: str = "push", job: str | None = None, use_container: bool = False) -> list[str]:
        """Get the act command to run."""
        availability = self.check_act_available()
        config = ActConfig()
        builder = ActCommandBuilder(self.project_path, config)

        # Build command using command builder
        return builder.get_act_command(
            event=event, job=job, use_container=use_container, preferred_method=availability["preferred_method"]
        )

    def list_workflows_and_jobs(self) -> dict[str, Any]:
        """List all workflows and their jobs."""
        result = self.workflow_manager.list_workflows_and_jobs()
        result["act_available"] = self.check_act_available()
        return result


@task(name="lint_workflows")
def lint_workflows_task(project_path: Path, use_docker: bool = False) -> dict[str, Any]:
    """Lint GitHub Actions workflows.

    This performs static analysis to catch errors before execution.
    Use 'act' to actually run the workflows.
    """
    logger = get_run_logger()
    integration = ActIntegration(project_path)

    logger.info("Linting GitHub Actions workflows (static analysis)...")
    lint_results = integration.lint_workflows(use_docker=use_docker)

    return lint_results


@task(name="check_act_setup")
def check_act_setup(project_path: Path) -> dict[str, Any]:
    """Check if act is set up for the project."""
    logger = get_run_logger()
    integration = ActIntegration(project_path)

    if not integration.has_workflows():
        logger.info("No GitHub workflows found")
        return {"has_workflows": False}

    logger.info(f"Found workflows in {integration.workflows_path}")

    availability = integration.check_act_available()
    workflows = integration.get_workflows()

    return {"has_workflows": True, "workflows": workflows, "act_availability": availability}


@task(name="setup_act_environment")
def setup_act_environment(project_path: Path, config: ActConfig | None = None) -> str:
    """Set up act environment for the project."""
    logger = get_run_logger()
    integration = ActIntegration(project_path)

    # Install gh extension if available and not installed
    availability = integration.check_act_available()
    if not availability["gh_extension"] and availability.get("gh_available"):
        logger.info("Installing gh act extension...")
        if integration.install_gh_act_extension():
            logger.info("✅ gh act extension installed")
        else:
            logger.warning("Failed to install gh act extension")

    # Setup configuration
    config_path = integration.setup_act_config(config)
    logger.info(f"Act configuration created at: {config_path}")

    return str(config_path)


@task(name="run_workflow")
def run_workflow(
    project_path: Path,
    event: str = "push",
    job: str | None = None,
    timeout: int = 1800,  # 30 minutes
    use_container: bool = False,
) -> dict[str, Any]:
    """Run a GitHub workflow locally with act."""
    logger = get_run_logger()
    integration = ActIntegration(project_path)

    # Setup container environment if requested
    if use_container:
        logger.info("Setting up container environment for act...")

        # Use enhanced container runner if available
        if HAS_CONTAINER_RUNNER:
            from act_container_setup import ActContainerRunner

            runner = ActContainerRunner(project_path)

            # Check for config files
            secrets_file = integration.act_config_path / ".secrets"
            env_file = integration.act_config_path / ".env"

            logger.info("Using enhanced container runner for isolated execution")
            result = runner.run_act(
                event=event,
                job=job,
                secrets_file=secrets_file if secrets_file.exists() else None,
                env_file=env_file if env_file.exists() else None,
                verbose=False,
            )
            return result
        else:
            # Fallback to basic container setup
            container_setup = integration.setup_container_environment()
            if not container_setup.get("act_image_available"):
                return {"success": False, "error": "Failed to setup container environment", "details": container_setup}

    # Get command
    try:
        cmd = integration.get_act_command(event, job, use_container)
    except RuntimeError as e:
        logger.error(str(e))
        return {"success": False, "error": str(e)}

    logger.info(f"Running: {' '.join(cmd)}")

    # Run the workflow
    try:
        result = subprocess.run(cmd, cwd=str(project_path), capture_output=True, text=True, timeout=timeout)

        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "command": " ".join(cmd),
        }

    except subprocess.TimeoutExpired:
        logger.error(f"Workflow timed out after {timeout} seconds")
        return {"success": False, "error": f"Timeout after {timeout} seconds"}


@flow(name="act_workflow")
def act_workflow_flow(
    project_path: str,
    event: str = "push",
    job: str | None = None,
    setup_only: bool = False,
    lint_only: bool = False,
    use_container: bool = False,
) -> dict[str, Any]:
    """
    Run GitHub Actions locally using act.

    Args:
        project_path: Path to the project
        event: GitHub event to simulate (push, pull_request, etc.)
        job: Specific job to run (optional)
        setup_only: Only setup, don't run workflows
        lint_only: Only lint workflows, don't run them
        use_container: Run act inside a container for isolation

    Returns:
        Dictionary with results
    """
    logger = get_run_logger()
    project_path = Path(project_path).resolve()

    console.print(
        Panel.fit(
            f"🎬 DHT Act Integration\n"
            f"📁 Project: {project_path.name}\n"
            f"🎯 Event: {event}\n\n"
            f"[dim]Act runs workflows locally, simulating GitHub Actions.\n"
            f"For syntax validation only, use --lint with actionlint.[/dim]",
            style="bold blue",
        )
    )

    # Check setup
    console.print("\n[yellow]🔍 Checking GitHub Actions setup...[/yellow]")
    setup_info = check_act_setup(project_path)

    if not setup_info["has_workflows"]:
        console.print("[yellow]ℹ️  No GitHub workflows found in .github/workflows/[/yellow]")
        return {"success": True, "message": "No workflows to run"}

    # Display workflows
    table = Table(title="GitHub Workflows", show_header=True)
    table.add_column("File", style="cyan")
    table.add_column("Name", style="white")
    table.add_column("Triggers", style="green")
    table.add_column("Jobs", style="yellow")

    for workflow in setup_info["workflows"]:
        triggers = []
        if isinstance(workflow.get("on"), dict):
            triggers = list(workflow["on"].keys())
        elif isinstance(workflow.get("on"), list):
            triggers = workflow["on"]
        elif isinstance(workflow.get("on"), str):
            triggers = [workflow["on"]]

        table.add_row(
            workflow["file"], workflow.get("name", ""), ", ".join(triggers), ", ".join(workflow.get("jobs", []))
        )

    console.print(table)

    # Check act availability
    availability = setup_info["act_availability"]
    console.print("\n[yellow]🔧 Act availability:[/yellow]")
    console.print(f"  gh extension: {'✅' if availability['gh_extension'] else '❌'}")
    console.print(f"  standalone act: {'✅' if availability['standalone_act'] else '❌'}")
    console.print(f"  container act: {'✅' if availability['container_act'] else '❌'}")

    if use_container:
        console.print("\n[cyan]🐳 Container mode requested[/cyan]")
        if not availability["container_act"]:
            console.print("[red]❌ No container runtime available![/red]")
            console.print("   Install Podman or Docker to use container mode")
            return {"success": False, "error": "Container runtime not available"}

    # Lint workflows with actionlint (static analysis - doesn't execute workflows)
    console.print("\n[yellow]🔍 Linting workflows with actionlint (static analysis)...[/yellow]")
    console.print("[dim]Note: This validates syntax but doesn't run workflows. Use 'dhtl act' to execute them.[/dim]")
    lint_results = lint_workflows_task(project_path)

    if lint_results["has_actionlint"]:
        if lint_results["total_issues"] > 0:
            console.print("\n[red]❌ Workflow validation failed![/red]")
            console.print(f"Found {lint_results['total_issues']} issue(s):\n")

            for workflow, issues in lint_results["workflows"].items():
                console.print(f"[yellow]{workflow}:[/yellow]")
                for issue in issues:
                    console.print(f"  Line {issue['line']}, Col {issue['column']}: {issue['message']}")
                console.print()
        else:
            console.print("[green]✅ All workflows passed validation![/green]")
    else:
        console.print("[yellow]⚠️  actionlint not available[/yellow]")
        console.print("   Install with: brew install actionlint")

    if lint_only:
        return {
            "success": lint_results["total_issues"] == 0 if lint_results["has_actionlint"] else True,
            "lint_results": lint_results,
        }

    # Check act availability for running workflows
    if not availability["preferred_method"]:
        console.print("\n[red]❌ No act runner available![/red]")
        console.print("\nInstall act using one of these methods:")
        console.print("  1. gh extension install https://github.com/nektos/gh-act")
        console.print("  2. brew install act")
        console.print("  3. Install Podman/Docker for container-based act")
        return {"success": False, "error": "No act runner available"}

    # Setup environment
    console.print("\n[yellow]📋 Setting up act environment...[/yellow]")
    config_path = setup_act_environment(project_path)
    console.print(f"✅ Configuration created at: {config_path}")

    if setup_only:
        console.print("\n[green]✅ Act setup complete![/green]")
        return {"success": True, "config_path": config_path}

    # Run workflow
    console.print(f"\n[cyan]🚀 Running workflow for event: {event}[/cyan]")
    if job:
        console.print(f"   Specific job: {job}")
    if use_container:
        console.print("   Mode: Container-isolated execution")
        if HAS_CONTAINER_RUNNER:
            console.print("   Using: Enhanced container runner")

    result = run_workflow(project_path, event, job, use_container=use_container)

    if result["success"]:
        console.print("\n[green]✅ Workflow completed successfully![/green]")
        if result.get("stdout"):
            console.print("\n[dim]Output:[/dim]")
            console.print(Panel(result["stdout"][-1000:], title="Act Output (last 1000 chars)"))
    else:
        console.print("\n[red]❌ Workflow failed![/red]")
        if result.get("error"):
            console.print(f"Error: {result['error']}")
        if result.get("stderr"):
            console.print(Panel(result["stderr"][-1000:], title="Error Output (last 1000 chars)", style="red"))

    return result


def main():
    """CLI interface for act integration."""
    import argparse

    parser = argparse.ArgumentParser(description="DHT Act Integration - Run GitHub Actions locally")
    parser.add_argument("path", nargs="?", default=".", help="Project path")
    parser.add_argument("-e", "--event", default="push", help="GitHub event to simulate")
    parser.add_argument("-j", "--job", help="Specific job to run")
    parser.add_argument("--setup-only", action="store_true", help="Only setup, don't run")
    parser.add_argument("-l", "--list", action="store_true", help="List workflows and exit")
    parser.add_argument("--lint", action="store_true", help="Lint workflows with actionlint")
    parser.add_argument("-c", "--container", action="store_true", help="Run act inside a container")

    args = parser.parse_args()

    project_path = Path(args.path).resolve()
    integration = ActIntegration(project_path)

    if args.list:
        # List workflows
        info = integration.list_workflows_and_jobs()

        if not info["workflows"]:
            print("No GitHub workflows found")
            return

        print(f"\nGitHub Workflows in {project_path.name}:")
        print("=" * 60)

        for workflow in info["workflows"]:
            print(f"\n📄 {workflow['file']}")
            if workflow.get("name"):
                print(f"   Name: {workflow['name']}")
            if workflow.get("on"):
                print(f"   Triggers: {workflow['on']}")
            if workflow.get("jobs"):
                print(f"   Jobs: {', '.join(workflow['jobs'])}")
            if workflow.get("error"):
                print(f"   ⚠️  Error: {workflow['error']}")

        print(f"\nTotal: {info['total_workflows']} workflows, {info['total_jobs']} jobs")
        return

    # Run the flow
    result = act_workflow_flow(
        project_path=str(project_path),
        event=args.event,
        job=args.job,
        setup_only=args.setup_only,
        lint_only=args.lint,
        use_container=args.container,
    )

    # Exit with appropriate code
    import sys

    sys.exit(0 if result.get("success", False) else 1)


if __name__ == "__main__":
    main()
