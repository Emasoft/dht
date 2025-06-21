#!/usr/bin/env python3

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Python replacement for dhtl_version.sh
# - Implements version management commands (tag, bump)
# - Uses git for tagging and bump-my-version for version bumping
# - Maintains compatibility with shell version
#

"""
DHT Version Management Module.

Provides version tagging and bumping functionality for projects.
"""

import os
import re
import shutil
import subprocess
from pathlib import Path

try:
    import tomllib  # Python 3.11+
except ImportError:
    import tomli as tomllib  # Python 3.10 and below
import json

from .common_utils import find_project_root
from .dhtl_error_handling import log_error, log_info, log_success, log_warning


def tag_command(*args, **kwargs) -> int:
    """Create a git tag for the current version."""
    log_info("🏷️  Creating git tag...")

    # Find project root
    project_root = find_project_root()

    # Check if git is available
    if not shutil.which("git"):
        log_error("git is not installed")
        return 1

    # Check if we're in a git repo
    git_dir = project_root / ".git"
    if not git_dir.exists():
        log_error("Not in a git repository")
        return 1

    # Change to project root
    os.chdir(project_root)

    # Parse arguments
    tag_name = None
    message = None
    push = False
    force = False

    i = 0
    while i < len(args):
        if args[i] in ["--name", "-n"]:
            if i + 1 < len(args):
                tag_name = args[i + 1]
                i += 1
        elif args[i] in ["--message", "-m"]:
            if i + 1 < len(args):
                message = args[i + 1]
                i += 1
        elif args[i] == "--push":
            push = True
        elif args[i] in ["--force", "-f"]:
            force = True
        i += 1

    # If no tag name provided, try to get version from project
    if not tag_name:
        version = get_project_version(project_root)
        if version:
            tag_name = f"v{version}"
            log_info(f"Using version from project: {tag_name}")
        else:
            log_error("No tag name provided and could not determine version from project")
            log_info("Use --name to specify tag name")
            return 1

    # Check if tag exists
    result = subprocess.run(["git", "tag", "-l", tag_name], capture_output=True, text=True)

    if result.stdout.strip():
        if not force:
            log_error(f"Tag {tag_name} already exists")
            log_info("Use --force to overwrite")
            return 1
        else:
            log_warning(f"Overwriting existing tag {tag_name}")
            # Delete existing tag
            subprocess.run(["git", "tag", "-d", tag_name])

    # Create tag
    tag_cmd = ["git", "tag"]

    if message:
        tag_cmd.extend(["-a", tag_name, "-m", message])
    else:
        tag_cmd.append(tag_name)

    result = subprocess.run(tag_cmd)

    if result.returncode == 0:
        log_success(f"Created tag: {tag_name}")

        # Push if requested
        if push:
            log_info("Pushing tag to remote...")
            result = subprocess.run(["git", "push", "origin", tag_name])
            if result.returncode == 0:
                log_success("Tag pushed successfully")
            else:
                log_error("Failed to push tag")
                return 1
    else:
        log_error("Failed to create tag")
        return 1

    return 0


def bump_command(*args, **kwargs) -> int:
    """Bump project version."""
    log_info("📈 Bumping project version...")

    # Find project root
    project_root = find_project_root()

    # Change to project root
    os.chdir(project_root)

    # Parse arguments
    part = "patch"  # default
    commit = True
    tag = True
    push = False

    # Check first argument for bump part
    if args and args[0] in ["major", "minor", "patch", "premajor", "preminor", "prepatch", "prerelease"]:
        part = args[0]
        args = args[1:]  # Remove part from args

    # Parse remaining arguments
    i = 0
    while i < len(args):
        if args[i] == "--no-commit":
            commit = False
        elif args[i] == "--no-tag":
            tag = False
        elif args[i] == "--push":
            push = True
        i += 1

    # Try to use bump-my-version if available
    if shutil.which("bump-my-version") or shutil.which("bump2version") or shutil.which("bumpversion"):
        # Determine which tool is available
        bump_cmd = None
        if shutil.which("bump-my-version"):
            bump_cmd = "bump-my-version"
        elif shutil.which("bump2version"):
            bump_cmd = "bump2version"
        else:
            bump_cmd = "bumpversion"

        log_info(f"Using {bump_cmd} to bump version...")

        cmd = [bump_cmd, part]

        if not commit:
            cmd.append("--no-commit")
        if not tag:
            cmd.append("--no-tag")

        result = subprocess.run(cmd)

        if result.returncode == 0:
            log_success(f"Version bumped ({part})")

            # Get new version
            new_version = get_project_version(project_root)
            if new_version:
                log_info(f"New version: {new_version}")

            # Push if requested
            if push and commit:
                log_info("Pushing changes...")
                subprocess.run(["git", "push"])
                if tag:
                    subprocess.run(["git", "push", "--tags"])
                log_success("Changes pushed")
        else:
            log_error("Failed to bump version")
            return 1
    else:
        # Manual version bumping
        log_info("No version bumping tool found, attempting manual bump...")

        # Get current version
        current_version = get_project_version(project_root)
        if not current_version:
            log_error("Could not determine current version")
            return 1

        log_info(f"Current version: {current_version}")

        # Parse version
        version_match = re.match(r"(\d+)\.(\d+)\.(\d+)(.*)", current_version)
        if not version_match:
            log_error(f"Invalid version format: {current_version}")
            return 1

        major = int(version_match.group(1))
        minor = int(version_match.group(2))
        patch = int(version_match.group(3))
        suffix = version_match.group(4)

        # Bump version
        if part == "major":
            major += 1
            minor = 0
            patch = 0
        elif part == "minor":
            minor += 1
            patch = 0
        elif part == "patch":
            patch += 1
        else:
            log_error(f"Manual bumping only supports major/minor/patch, not {part}")
            return 1

        new_version = f"{major}.{minor}.{patch}{suffix}"
        log_info(f"New version: {new_version}")

        # Update version in files
        if not update_version_in_files(project_root, current_version, new_version):
            return 1

        # Commit if requested
        if commit and shutil.which("git"):
            log_info("Committing version bump...")
            subprocess.run(["git", "add", "-A"])
            subprocess.run(["git", "commit", "-m", f"Bump version: {current_version} → {new_version}"])

            # Tag if requested
            if tag:
                tag_name = f"v{new_version}"
                subprocess.run(["git", "tag", tag_name])
                log_success(f"Created tag: {tag_name}")

        log_success(f"Version bumped to {new_version}")

    return 0


def get_project_version(project_root: Path) -> str | None:
    """Get the current project version."""
    # Try pyproject.toml first
    pyproject_path = project_root / "pyproject.toml"
    if pyproject_path.exists():
        try:
            with open(pyproject_path, "rb") as f:
                data = tomllib.load(f)

            # Try [project] section
            if "project" in data and "version" in data["project"]:
                return data["project"]["version"]

            # Try [tool.poetry] section
            if "tool" in data and "poetry" in data["tool"] and "version" in data["tool"]["poetry"]:
                return data["tool"]["poetry"]["version"]
        except Exception as e:
            log_warning(f"Could not parse pyproject.toml: {e}")

    # Try package.json
    package_json = project_root / "package.json"
    if package_json.exists():
        try:
            with open(package_json) as f:
                data = json.load(f)
            if "version" in data:
                return data["version"]
        except Exception as e:
            log_warning(f"Could not parse package.json: {e}")

    # Try __version__.py or _version.py
    for version_file in ["__version__.py", "_version.py", "version.py"]:
        for search_dir in [project_root, project_root / "src", project_root / "lib"]:
            version_path = search_dir / version_file
            if version_path.exists():
                try:
                    content = version_path.read_text()
                    match = re.search(r"__version__\s*=\s*['\"]([^'\"]+)['\"]", content)
                    if match:
                        return match.group(1)
                except Exception:
                    pass

    return None


def update_version_in_files(project_root: Path, old_version: str, new_version: str) -> bool:
    """Update version in project files."""
    updated_files = []

    # Update pyproject.toml
    pyproject_path = project_root / "pyproject.toml"
    if pyproject_path.exists():
        try:
            content = pyproject_path.read_text()
            new_content = content.replace(f'version = "{old_version}"', f'version = "{new_version}"')
            if new_content != content:
                pyproject_path.write_text(new_content)
                updated_files.append("pyproject.toml")
        except Exception as e:
            log_error(f"Failed to update pyproject.toml: {e}")
            return False

    # Update package.json
    package_json = project_root / "package.json"
    if package_json.exists():
        try:
            content = package_json.read_text()
            new_content = content.replace(f'"version": "{old_version}"', f'"version": "{new_version}"')
            if new_content != content:
                package_json.write_text(new_content)
                updated_files.append("package.json")
        except Exception as e:
            log_error(f"Failed to update package.json: {e}")
            return False

    # Update version files
    for version_file in ["__version__.py", "_version.py", "version.py"]:
        for search_dir in [project_root, project_root / "src", project_root / "lib"]:
            version_path = search_dir / version_file
            if version_path.exists():
                try:
                    content = version_path.read_text()
                    new_content = re.sub(
                        r"__version__\s*=\s*['\"][^'\"]+['\"]", f'__version__ = "{new_version}"', content
                    )
                    if new_content != content:
                        version_path.write_text(new_content)
                        updated_files.append(str(version_path.relative_to(project_root)))
                except Exception as e:
                    log_error(f"Failed to update {version_path}: {e}")
                    return False

    if updated_files:
        log_success(f"Updated version in: {', '.join(updated_files)}")
        return True
    else:
        log_warning("No files were updated")
        return True


# For backward compatibility
def placeholder_function():
    """Placeholder function."""
    log_warning("Use tag_command or bump_command instead")
    return True
