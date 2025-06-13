#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Created act integration module for local GitHub Actions testing
# - Integrates with container build system for isolation
# - Supports both standalone act and gh extension
# - Provides deterministic CI/CD testing environment
# 

"""
Act integration for DHT - Run GitHub Actions locally.
Provides isolated, deterministic CI/CD testing environment.
"""

from pathlib import Path
from typing import Dict, List, Optional, Any
import subprocess
import json
import yaml
import os
from dataclasses import dataclass

from prefect import flow, task, get_run_logger
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

# Import container runner if available
try:
    from act_container_setup import ActContainerRunner
    HAS_CONTAINER_RUNNER = True
except ImportError:
    HAS_CONTAINER_RUNNER = False


@dataclass
class ActConfig:
    """Configuration for act runner."""
    runner_image: str = "catthehacker/ubuntu:act-latest"
    platform: str = "ubuntu-latest"
    container_runtime: str = "podman"  # Prefer podman for rootless
    use_gh_extension: bool = True
    artifact_server_path: Optional[str] = None
    cache_server_path: Optional[str] = None
    reuse_containers: bool = False
    bind_workdir: bool = True
    

class ActIntegration:
    """Integrates act with DHT for local GitHub Actions testing."""
    
    def __init__(self, project_path: Path):
        self.project_path = Path(project_path).resolve()
        self.workflows_path = self.project_path / ".github" / "workflows"
        self.venv_path = self.project_path / ".venv"
        self.act_config_path = self.venv_path / "dht-act"
        self.container_config = None
        
    def has_workflows(self) -> bool:
        """Check if project has GitHub workflows."""
        return self.workflows_path.exists() and any(
            f.suffix in ['.yml', '.yaml'] 
            for f in self.workflows_path.iterdir() 
            if f.is_file()
        )
    
    def get_workflows(self) -> List[Dict[str, Any]]:
        """Get list of workflows with their metadata."""
        workflows = []
        
        if not self.has_workflows():
            return workflows
        
        for workflow_file in sorted(self.workflows_path.glob("*.y*ml")):
            try:
                with open(workflow_file) as f:
                    workflow_data = yaml.safe_load(f)
                
                workflows.append({
                    "file": workflow_file.name,
                    "name": workflow_data.get("name", workflow_file.stem),
                    "on": workflow_data.get("on", {}),
                    "jobs": list(workflow_data.get("jobs", {}).keys()),
                    "path": str(workflow_file)
                })
            except Exception as e:
                workflows.append({
                    "file": workflow_file.name,
                    "name": workflow_file.stem,
                    "error": str(e)
                })
        
        return workflows
    
    def lint_workflows(self, use_docker: bool = False) -> Dict[str, Any]:
        """Lint GitHub Actions workflows using actionlint.
        
        Actionlint performs static analysis of workflow files to catch:
        - Syntax errors
        - Invalid action references
        - Type mismatches
        - Shell script issues (via shellcheck)
        
        This is different from 'act' which actually executes workflows.
        """
        results = {
            "has_actionlint": False,
            "workflows": {},
            "total_issues": 0,
            "summary": [],
            "method": "native" if not use_docker else "docker"
        }
        
        # Check if actionlint is available or use Docker
        if not use_docker:
            try:
                subprocess.run(
                    ["actionlint", "--version"],
                    capture_output=True,
                    check=True
                )
                results["has_actionlint"] = True
            except:
                # Try Docker as fallback
                if self._check_docker_available():
                    console.print("[yellow]⚠️  Actionlint not found locally[/yellow]")
                    console.print("[yellow]🐳 Using Docker image automatically...[/yellow]")
                    return self.lint_with_docker()
                else:
                    results["summary"].append("actionlint not found. Install with: brew install actionlint")
                    results["summary"].append("Or use Docker: docker run --rm -v $(pwd):/repo --workdir /repo rhysd/actionlint:latest")
                    return results
        
        if not self.has_workflows():
            results["summary"].append("No GitHub workflows found")
            return results
        
        # Run actionlint on all workflows
        try:
            if use_docker:
                # Use Docker to run actionlint
                cmd = [
                    "docker", "run", "--rm",
                    "-v", f"{self.project_path}:/repo",
                    "--workdir", "/repo",
                    "rhysd/actionlint:latest",
                    "-format", "{{json .}}"
                ]
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True
                )
                results["has_actionlint"] = True
            else:
                result = subprocess.run(
                    ["actionlint", "-format", "{{json .}}"],
                    cwd=str(self.project_path),
                    capture_output=True,
                    text=True
                )
            
            if result.stdout:
                # Parse each line as JSON (actionlint outputs one JSON per line)
                for line in result.stdout.strip().split('\n'):
                    if line:
                        try:
                            issue = json.loads(line)
                            filepath = issue.get("filepath", "")
                            filename = Path(filepath).name if filepath else "unknown"
                            
                            if filename not in results["workflows"]:
                                results["workflows"][filename] = []
                            
                            results["workflows"][filename].append({
                                "line": issue.get("line", 0),
                                "column": issue.get("column", 0),
                                "message": issue.get("message", ""),
                                "kind": issue.get("kind", "error")
                            })
                            results["total_issues"] += 1
                        except json.JSONDecodeError:
                            pass
            
            if results["total_issues"] == 0:
                results["summary"].append("✅ All workflows passed validation!")
            else:
                results["summary"].append(f"❌ Found {results['total_issues']} issue(s) in workflows")
                
        except Exception as e:
            results["summary"].append(f"Error running actionlint: {str(e)}")
        
        return results
    
    def _check_docker_available(self) -> bool:
        """Check if Docker is available."""
        try:
            result = subprocess.run(
                ["docker", "--version"],
                capture_output=True,
                check=True
            )
            return result.returncode == 0
        except:
            return False
    
    def lint_with_docker(self, tag: str = "latest", color: bool = True) -> Dict[str, Any]:
        """Run actionlint using official Docker image.
        
        This is the recommended way to run actionlint as it includes
        all dependencies (shellcheck, pyflakes) in the container.
        """
        results = {
            "method": "docker",
            "docker_tag": tag,
            "workflows": {},
            "total_issues": 0,
            "summary": []
        }
        
        if not self._check_docker_available():
            results["summary"].append("Docker not available")
            return results
        
        # Pull the official actionlint image
        image_name = f"rhysd/actionlint:{tag}"
        console.print(f"[yellow]🐳 Pulling {image_name}...[/yellow]")
        
        try:
            pull_result = subprocess.run(
                ["docker", "pull", image_name],
                capture_output=True,
                text=True
            )
            if pull_result.returncode != 0:
                results["summary"].append(f"Failed to pull Docker image: {pull_result.stderr}")
                return results
        except Exception as e:
            results["summary"].append(f"Error pulling Docker image: {str(e)}")
            return results
        
        # Run actionlint in Docker with proper volume mounting
        cmd = [
            "docker", "run", "--rm",
            "-v", f"{self.project_path}:/repo:ro",  # Read-only mount
            "--workdir", "/repo",
            image_name,
            "-format", "{{json .}}"
        ]
        
        if color:
            cmd.insert(-2, "-color")
        
        console.print(f"[yellow]🔍 Running actionlint in Docker...[/yellow]")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )
            
            # Process the output same as native actionlint
            if result.stdout:
                for line in result.stdout.strip().split('\n'):
                    if line:
                        try:
                            issue = json.loads(line)
                            filepath = issue.get("filepath", "")
                            filename = Path(filepath).name if filepath else "unknown"
                            
                            if filename not in results["workflows"]:
                                results["workflows"][filename] = []
                            
                            results["workflows"][filename].append({
                                "line": issue.get("line", 0),
                                "column": issue.get("column", 0),
                                "message": issue.get("message", ""),
                                "kind": issue.get("kind", "error")
                            })
                            results["total_issues"] += 1
                        except json.JSONDecodeError:
                            pass
            
            if results["total_issues"] == 0:
                results["summary"].append("✅ All workflows passed validation!")
            else:
                results["summary"].append(f"❌ Found {results['total_issues']} issue(s) in workflows")
                
        except Exception as e:
            results["summary"].append(f"Error running actionlint: {str(e)}")
        
        return results
    
    def check_act_available(self) -> Dict[str, bool]:
        """Check if act is available via various methods."""
        availability = {
            "gh_extension": False,
            "standalone_act": False,
            "container_act": False,
            "preferred_method": None
        }
        
        # Check gh extension
        try:
            result = subprocess.run(
                ["gh", "extension", "list"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0 and "nektos/gh-act" in result.stdout:
                availability["gh_extension"] = True
        except:
            pass
        
        # Check standalone act
        try:
            result = subprocess.run(
                ["act", "--version"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                availability["standalone_act"] = True
        except:
            pass
        
        # Check if we can run act in container
        from container_build_handler import ContainerBuildHandler
        handler = ContainerBuildHandler(self.project_path)
        if handler.detect_container_builder():
            availability["container_act"] = True
        
        # Determine preferred method
        if availability["gh_extension"]:
            availability["preferred_method"] = "gh_extension"
        elif availability["standalone_act"]:
            availability["preferred_method"] = "standalone"
        elif availability["container_act"]:
            availability["preferred_method"] = "container"
        
        return availability
    
    def install_gh_act_extension(self) -> bool:
        """Install the gh act extension."""
        try:
            result = subprocess.run(
                ["gh", "extension", "install", "https://github.com/nektos/gh-act"],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except:
            return False
    
    def setup_act_config(self, config: Optional[ActConfig] = None) -> Path:
        """Set up act configuration in project."""
        if config is None:
            config = ActConfig()
        
        self.act_config_path.mkdir(parents=True, exist_ok=True)
        
        # Create .actrc file with configuration
        actrc_content = f"""
# Act configuration for DHT
# Generated automatically - do not edit manually

# Container options
--container-architecture linux/amd64
--platform {config.platform}
--pull=false

# Use local project directory
--bind

# Container runtime
--container-daemon-socket unix://{self._get_container_socket(config.container_runtime)}

# Runner image
--image {config.runner_image}

# Artifact server (if configured)
{f'--artifact-server-path {config.artifact_server_path}' if config.artifact_server_path else '# No artifact server'}

# Cache server (if configured)  
{f'--cache-server-path {config.cache_server_path}' if config.cache_server_path else '# No cache server'}

# Reuse containers
{'--reuse' if config.reuse_containers else '# No container reuse'}
"""
        
        actrc_path = self.act_config_path / ".actrc"
        with open(actrc_path, "w") as f:
            f.write(actrc_content.strip())
        
        # Create secrets file template
        secrets_template = """
# GitHub Secrets for local testing
# Add your secrets here (DO NOT COMMIT!)
# Format: SECRET_NAME=secret_value

# Example:
# GITHUB_TOKEN=your_github_token
# NPM_TOKEN=your_npm_token
"""
        
        secrets_path = self.act_config_path / ".secrets"
        if not secrets_path.exists():
            with open(secrets_path, "w") as f:
                f.write(secrets_template.strip())
            # Make secrets file readable only by owner
            os.chmod(secrets_path, 0o600)
        
        # Create env file template
        env_template = """
# Environment variables for act
# These simulate GitHub Actions environment

GITHUB_ACTIONS=true
CI=true
GITHUB_WORKSPACE=/workspace
GITHUB_REPOSITORY_OWNER=local
GITHUB_REPOSITORY=local/project
"""
        
        env_path = self.act_config_path / ".env"
        if not env_path.exists():
            with open(env_path, "w") as f:
                f.write(env_template.strip())
        
        return actrc_path
    
    def _get_container_socket(self, runtime: str) -> str:
        """Get container runtime socket path."""
        sockets = {
            "docker": "/var/run/docker.sock",
            "podman": f"{os.environ.get('XDG_RUNTIME_DIR', '/tmp')}/podman/podman.sock",
            "buildah": f"{os.environ.get('XDG_RUNTIME_DIR', '/tmp')}/buildah/buildah.sock"
        }
        return sockets.get(runtime, "/var/run/docker.sock")
    
    def _get_container_act_command(self) -> List[str]:
        """Get command to run act inside a container."""
        runtime = ActConfig().container_runtime
        
        # Setup container configuration
        container_args = []
        
        # Basic container setup
        container_args.extend([
            runtime, "run", "--rm",
            "-v", f"{self.project_path}:/workspace:z",  # :z for SELinux compatibility
            "-v", f"{self.act_config_path}:/root/.config/act:z",
            "-w", "/workspace",
            "--network", "host",  # Allow network access
        ])
        
        # Add container runtime socket mount
        socket_path = self._get_container_socket(runtime)
        if os.path.exists(socket_path):
            container_args.extend(["-v", f"{socket_path}:{socket_path}"])
            
        # Add privileged mode for Docker-in-Docker
        container_args.append("--privileged")
        
        # Add environment variables
        container_args.extend([
            "-e", "DOCKER_HOST=unix:///var/run/docker.sock",
            "-e", "HOME=/root",
            "-e", "USER=root",
        ])
        
        # Use custom act container image with act pre-installed
        # Check if we have our custom image first
        if HAS_CONTAINER_RUNNER:
            custom_image = "dht-act:latest"
            try:
                check_result = subprocess.run(
                    [runtime, "image", "exists", custom_image],
                    capture_output=True
                )
                if check_result.returncode == 0:
                    container_args.append(custom_image)
                else:
                    container_args.append("nektos/act:latest")
            except:
                container_args.append("nektos/act:latest")
        else:
            container_args.append("nektos/act:latest")
        
        # The act command itself
        container_args.append("act")
        
        return container_args
    
    def setup_container_environment(self) -> Dict[str, Any]:
        """Set up container environment for act."""
        result = {
            "container_config_created": False,
            "act_image_available": False,
            "runtime_available": False
        }
        
        # Check container runtime
        from container_build_handler import ContainerBuildHandler
        handler = ContainerBuildHandler(self.project_path)
        runtime = handler.detect_container_builder()
        
        if runtime:
            result["runtime_available"] = True
            result["runtime"] = runtime
            
            # Pull act container image
            console.print(f"[yellow]🐳 Pulling act container image...[/yellow]")
            try:
                pull_result = subprocess.run(
                    [runtime, "pull", "nektos/act:latest"],
                    capture_output=True,
                    text=True
                )
                if pull_result.returncode == 0:
                    result["act_image_available"] = True
                    console.print("[green]✅ Act container image ready[/green]")
                else:
                    console.print("[red]❌ Failed to pull act image[/red]")
                    result["error"] = pull_result.stderr
            except Exception as e:
                result["error"] = str(e)
        
        # Create container configuration
        if runtime == "podman":
            # Setup podman-specific config
            podman_config_dir = self.act_config_path / "containers"
            podman_config_dir.mkdir(parents=True, exist_ok=True)
            
            # Create containers.conf for rootless operation
            containers_conf = podman_config_dir / "containers.conf"
            with open(containers_conf, "w") as f:
                f.write("""
[containers]
userns = "keep-id"
label = true
log_driver = "k8s-file"

[engine]
cgroup_manager = "cgroupfs"
events_logger = "file"
runtime = "crun"
""")
            
            result["container_config_created"] = True
            result["config_path"] = str(podman_config_dir)
        
        return result
    
    def get_act_command(self, event: str = "push", job: Optional[str] = None, use_container: bool = False) -> List[str]:
        """Get the act command to run."""
        availability = self.check_act_available()
        
        cmd = []
        
        # Force container mode if requested
        if use_container:
            cmd = self._get_container_act_command()
        # Use preferred method
        elif availability["preferred_method"] == "gh_extension":
            cmd = ["gh", "act"]
        elif availability["preferred_method"] == "standalone":
            cmd = ["act"]
        elif availability["preferred_method"] == "container":
            cmd = self._get_container_act_command()
        else:
            raise RuntimeError("No act runner available")
        
        # Add configuration file
        if (self.act_config_path / ".actrc").exists():
            cmd.extend(["--actrc", str(self.act_config_path / ".actrc")])
        
        # Add secrets if available
        secrets_file = self.act_config_path / ".secrets"
        if secrets_file.exists():
            cmd.extend(["--secret-file", str(secrets_file)])
        
        # Add env file
        env_file = self.act_config_path / ".env"
        if env_file.exists():
            cmd.extend(["--env-file", str(env_file)])
        
        # Add event
        cmd.append(event)
        
        # Add specific job if requested
        if job:
            cmd.extend(["-j", job])
        
        return cmd
    
    def list_workflows_and_jobs(self) -> Dict[str, Any]:
        """List all workflows and their jobs."""
        workflows = self.get_workflows()
        availability = self.check_act_available()
        
        return {
            "workflows": workflows,
            "act_available": availability,
            "total_workflows": len(workflows),
            "total_jobs": sum(len(w.get("jobs", [])) for w in workflows)
        }


@task(name="lint_workflows")
def lint_workflows_task(project_path: Path, use_docker: bool = False) -> Dict[str, Any]:
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
def check_act_setup(project_path: Path) -> Dict[str, Any]:
    """Check if act is set up for the project."""
    logger = get_run_logger()
    integration = ActIntegration(project_path)
    
    if not integration.has_workflows():
        logger.info("No GitHub workflows found")
        return {"has_workflows": False}
    
    logger.info(f"Found workflows in {integration.workflows_path}")
    
    availability = integration.check_act_available()
    workflows = integration.get_workflows()
    
    return {
        "has_workflows": True,
        "workflows": workflows,
        "act_availability": availability
    }


@task(name="setup_act_environment")
def setup_act_environment(project_path: Path, config: Optional[ActConfig] = None) -> str:
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
    job: Optional[str] = None,
    timeout: int = 1800,  # 30 minutes
    use_container: bool = False
) -> Dict[str, Any]:
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
                verbose=False
            )
            return result
        else:
            # Fallback to basic container setup
            container_setup = integration.setup_container_environment()
            if not container_setup.get("act_image_available"):
                return {
                    "success": False,
                    "error": "Failed to setup container environment",
                    "details": container_setup
                }
    
    # Get command
    try:
        cmd = integration.get_act_command(event, job, use_container)
    except RuntimeError as e:
        logger.error(str(e))
        return {"success": False, "error": str(e)}
    
    logger.info(f"Running: {' '.join(cmd)}")
    
    # Run the workflow
    try:
        result = subprocess.run(
            cmd,
            cwd=str(project_path),
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "command": " ".join(cmd)
        }
        
    except subprocess.TimeoutExpired:
        logger.error(f"Workflow timed out after {timeout} seconds")
        return {
            "success": False,
            "error": f"Timeout after {timeout} seconds"
        }


@flow(name="act_workflow")
def act_workflow_flow(
    project_path: str,
    event: str = "push",
    job: Optional[str] = None,
    setup_only: bool = False,
    lint_only: bool = False,
    use_container: bool = False
) -> Dict[str, Any]:
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
    
    console.print(Panel.fit(
        f"🎬 DHT Act Integration\n"
        f"📁 Project: {project_path.name}\n"
        f"🎯 Event: {event}\n\n"
        f"[dim]Act runs workflows locally, simulating GitHub Actions.\n"
        f"For syntax validation only, use --lint with actionlint.[/dim]",
        style="bold blue"
    ))
    
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
            workflow["file"],
            workflow.get("name", ""),
            ", ".join(triggers),
            ", ".join(workflow.get("jobs", []))
        )
    
    console.print(table)
    
    # Check act availability
    availability = setup_info["act_availability"]
    console.print("\n[yellow]🔧 Act availability:[/yellow]")
    console.print(f"  gh extension: {'✅' if availability['gh_extension'] else '❌'}")
    console.print(f"  standalone act: {'✅' if availability['standalone_act'] else '❌'}")
    console.print(f"  container act: {'✅' if availability['container_act'] else '❌'}")
    
    if use_container:
        console.print(f"\n[cyan]🐳 Container mode requested[/cyan]")
        if not availability['container_act']:
            console.print("[red]❌ No container runtime available![/red]")
            console.print("   Install Podman or Docker to use container mode")
            return {"success": False, "error": "Container runtime not available"}
    
    # Lint workflows with actionlint (static analysis - doesn't execute workflows)
    console.print(f"\n[yellow]🔍 Linting workflows with actionlint (static analysis)...[/yellow]")
    console.print("[dim]Note: This validates syntax but doesn't run workflows. Use 'dhtl act' to execute them.[/dim]")
    lint_results = lint_workflows_task(project_path)
    
    if lint_results["has_actionlint"]:
        if lint_results["total_issues"] > 0:
            console.print(f"\n[red]❌ Workflow validation failed![/red]")
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
            "lint_results": lint_results
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
    console.print(f"\n[yellow]📋 Setting up act environment...[/yellow]")
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
        use_container=args.container
    )
    
    # Exit with appropriate code
    import sys
    sys.exit(0 if result.get("success", False) else 1)


if __name__ == "__main__":
    main()