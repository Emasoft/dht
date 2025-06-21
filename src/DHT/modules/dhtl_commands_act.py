#!/usr/bin/env python3

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Python replacement for dhtl_commands_act.sh
# - Implements act command for running GitHub Actions locally
# - Uses act tool for local CI/CD testing
# - Integrated with DHT command dispatcher
#

"""
DHT Act Commands Module.

Provides local GitHub Actions execution using act.
"""

import shutil
import subprocess

from .common_utils import find_project_root
from .dhtl_error_handling import log_debug, log_error, log_info, log_success, log_warning


def act_command(*args, **kwargs) -> int:
    """Run GitHub Actions locally with act."""
    log_info("🎬 Running GitHub Actions locally with act...")

    # Check if act is available
    if not shutil.which("act"):
        log_error("act is not installed")
        log_info("Install act:")
        log_info("  brew install act  # macOS")
        log_info("  curl -s https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash  # Linux")
        log_info("  choco install act-cli  # Windows")
        log_info("\nMore info: https://github.com/nektos/act")
        return 1

    # Find project root
    project_root = find_project_root()
    workflows_dir = project_root / ".github" / "workflows"

    if not workflows_dir.exists():
        log_error("No .github/workflows directory found")
        log_info("Create workflows with: dhtl workflows create <type>")
        return 1

    # Build act command
    act_cmd = ["act"]

    # Parse arguments
    event = None
    workflow = None
    job = None
    list_mode = False
    dryrun = False
    container_options = []

    i = 0
    while i < len(args):
        if args[i] in ["-l", "--list"]:
            list_mode = True
        elif args[i] in ["-n", "--dryrun"]:
            dryrun = True
        elif args[i] in ["-W", "--workflows"]:
            if i + 1 < len(args):
                workflow = args[i + 1]
                i += 1
        elif args[i] in ["-j", "--job"]:
            if i + 1 < len(args):
                job = args[i + 1]
                i += 1
        elif args[i] == "--container-architecture":
            if i + 1 < len(args):
                container_options.extend(["--container-architecture", args[i + 1]])
                i += 1
        elif args[i] == "-P":
            if i + 1 < len(args):
                container_options.extend(["-P", args[i + 1]])
                i += 1
        elif args[i] == "--secret-file":
            if i + 1 < len(args):
                container_options.extend(["--secret-file", args[i + 1]])
                i += 1
        elif not event and args[i] not in ["push", "pull_request", "workflow_dispatch", "schedule"]:
            # Unknown argument, pass it through
            act_cmd.append(args[i])
        elif not event:
            event = args[i]
        i += 1

    # Default event is push
    if not event and not list_mode:
        event = "push"

    # Add event to command
    if event:
        act_cmd.append(event)

    # Add options
    if list_mode:
        act_cmd.append("--list")
    if dryrun:
        act_cmd.append("--dryrun")
    if workflow:
        act_cmd.extend(["-W", workflow])
    if job:
        act_cmd.extend(["-j", job])

    # Add container options
    act_cmd.extend(container_options)

    # Check for Docker/Podman
    if not shutil.which("docker") and not shutil.which("podman"):
        log_warning("Docker/Podman not found - act requires a container runtime")

        # Try to use podman with act
        if shutil.which("podman"):
            log_info("Using podman as container runtime...")
            act_cmd.extend(["--container-daemon-socket", "/run/user/1000/podman/podman.sock"])

    # Show what we're doing
    if list_mode:
        log_info("Listing available actions...")
    elif dryrun:
        log_info(f"Dry run for event: {event}")
    else:
        log_info(f"Running actions for event: {event}")
        if workflow:
            log_info(f"Workflow: {workflow}")
        if job:
            log_info(f"Job: {job}")

    # Run act
    log_debug(f"Running: {' '.join(act_cmd)}")
    result = subprocess.run(act_cmd, cwd=project_root)

    if result.returncode == 0:
        if not list_mode and not dryrun:
            log_success("Actions completed successfully!")
    else:
        log_error("Actions failed")

        # Provide helpful hints
        if result.returncode == 125:
            log_info("\nHint: Error 125 usually means Docker/Podman issues")
            log_info("Try: docker system prune -a")
        elif result.returncode == 126:
            log_info("\nHint: Error 126 usually means permission issues")
            log_info("Try: sudo usermod -aG docker $USER")

    return result.returncode


# For backward compatibility
def placeholder_command(*args, **kwargs) -> int:
    """Placeholder command implementation."""
    return act_command(*args, **kwargs)


# Export command functions
__all__ = ["act_command", "placeholder_command"]
