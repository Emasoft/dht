#!/usr/bin/env python3
"""
DHT Project Initialization Module.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE FILE:
# - Replaced placeholder with full implementation
# - Integrated with Prefect flows for project initialization
# - Supports both new project creation and existing project setup
# - Added interactive prompts for missing information
#

"""
DHT Project Initialization Module.

Provides commands for initializing new projects and setting up existing ones.
"""

from pathlib import Path
from typing import Any

from .dhtl_error_handling import log_error, log_info
from .flows.project_init_flow import initialize_project_flow
from .flows.project_setup_flow import setup_project_flow


def init_command(*args: Any, **kwargs: Any) -> int:
    """Initialize a new Python project with DHT.

    Args:
        *args: Command arguments
        **kwargs: Command options

    Returns:
        Exit code (0 for success)
    """
    # Parse arguments
    project_name = None
    description = "A new Python project"
    author_name = None
    author_email = None
    license_type = "MIT"
    python_version = "3.10"
    use_uv = True

    # Get project name from args
    if args and len(args) > 0:
        project_name = str(args[0])

    # Parse options
    if "--description" in args:
        idx = args.index("--description")
        if idx + 1 < len(args):
            description = args[idx + 1]

    if "--author" in args:
        idx = args.index("--author")
        if idx + 1 < len(args):
            author_name = args[idx + 1]

    if "--email" in args:
        idx = args.index("--email")
        if idx + 1 < len(args):
            author_email = args[idx + 1]

    if "--license" in args:
        idx = args.index("--license")
        if idx + 1 < len(args):
            license_type = args[idx + 1].upper()

    if "--python" in args:
        idx = args.index("--python")
        if idx + 1 < len(args):
            python_version = args[idx + 1]

    if "--no-uv" in args:
        use_uv = False

    # Interactive mode if no project name
    if not project_name:
        try:
            project_name = input("Project name: ").strip()
            if not project_name:
                log_error("Project name is required")
                return 1
        except (KeyboardInterrupt, EOFError):
            print("\nCancelled")
            return 1

    # Validate project name
    if not project_name.replace("-", "").replace("_", "").isalnum():
        log_error("Project name must contain only letters, numbers, hyphens, and underscores")
        return 1

    # Get current directory
    current_dir = Path.cwd()

    try:
        # Run the initialization flow
        success = initialize_project_flow(
            project_path=current_dir,
            project_name=project_name,
            description=description,
            author_name=author_name,
            author_email=author_email,
            license_type=license_type,
            python_version=python_version,
            use_uv=use_uv,
        )

        return 0 if success else 1

    except Exception as e:
        log_error(f"Failed to initialize project: {e}")
        return 1


def setup_command(*args: Any, **kwargs: Any) -> int:
    """Setup DHT for an existing project.

    Args:
        *args: Command arguments
        **kwargs: Command options

    Returns:
        Exit code (0 for success)
    """
    # Parse options
    project_path = None
    force = False

    if "--path" in args:
        idx = args.index("--path")
        if idx + 1 < len(args):
            project_path = Path(args[idx + 1])

    if "--force" in args or "-f" in args:
        force = True

    try:
        # Run the setup flow
        success = setup_project_flow(project_path=project_path, force=force)

        return 0 if success else 1

    except Exception as e:
        log_error(f"Failed to setup project: {e}")
        return 1


# For backward compatibility
def placeholder_function() -> Any:
    """Placeholder function for backward compatibility."""
    log_info("Use 'dhtl init <project_name>' to create a new project")
    log_info("Use 'dhtl setup' to setup DHT for an existing project")
    return 0


# Export functions
__all__ = ["init_command", "setup_command", "placeholder_function"]
