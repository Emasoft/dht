#!/usr/bin/env python3
"""
DHT Custom Exception Hierarchy.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE FILE:
# - Created centralized exception hierarchy for DHT
# - Replaces multiple empty exception classes scattered across modules
# - Provides meaningful error messages and context
# - Supports error codes for better debugging
#

"""
DHT Custom Exception Hierarchy.

Provides a comprehensive set of exceptions for all DHT modules,
replacing scattered empty exception classes with meaningful ones.
"""

from typing import Any, Dict


class DHTError(Exception):
    """Base exception for all DHT errors.

    Attributes:
        message: Error message
        error_code: Optional error code for categorization
        context: Optional context information
    """

    def __init__(self, message: str, error_code: str | None = None, context: dict[str, Any] | None = None) -> None:
        """Initialize DHT error.

        Args:
            message: Error message
            error_code: Optional error code
            context: Optional context dictionary
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.context = context or {}

    def __str__(self) -> str:
        """String representation of the error."""
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message


# Command-related exceptions
class CommandError(DHTError):
    """Base exception for command-related errors."""

    pass


class CommandNotFoundError(CommandError):
    """Raised when a command is not found."""

    def __init__(self, command_name: str) -> None:
        """Initialize command not found error."""
        super().__init__(f"Command '{command_name}' not found", error_code="CMD001", context={"command": command_name})


class CommandExecutionError(CommandError):
    """Raised when a command fails to execute."""

    def __init__(self, command_name: str, reason: str) -> None:
        """Initialize command execution error."""
        super().__init__(
            f"Command '{command_name}' failed: {reason}",
            error_code="CMD002",
            context={"command": command_name, "reason": reason},
        )


# Process/subprocess exceptions
class ProcessError(DHTError):
    """Base exception for process-related errors."""

    pass


class SubprocessError(ProcessError):
    """Raised when a subprocess fails."""

    def __init__(self, command: str, exit_code: int, stderr: str | None = None) -> None:
        """Initialize subprocess error."""
        message = f"Subprocess '{command}' failed with exit code {exit_code}"
        if stderr:
            message += f": {stderr}"
        super().__init__(
            message, error_code="PROC001", context={"command": command, "exit_code": exit_code, "stderr": stderr}
        )


class TimeoutError(ProcessError):
    """Raised when a process times out."""

    def __init__(self, command: str, timeout_seconds: int) -> None:
        """Initialize timeout error."""
        super().__init__(
            f"Process '{command}' timed out after {timeout_seconds} seconds",
            error_code="PROC002",
            context={"command": command, "timeout": timeout_seconds},
        )


# UV-related exceptions
class UVError(DHTError):
    """Base exception for UV package manager errors."""

    pass


class UVNotFoundError(UVError):
    """Raised when UV is not installed."""

    def __init__(self) -> None:
        """Initialize UV not found error."""
        super().__init__("UV package manager is not installed. Install from: https://astral.sh/uv", error_code="UV001")


class UVTaskError(UVError):
    """Raised when a UV task fails."""

    def __init__(self, task_name: str, reason: str) -> None:
        """Initialize UV task error."""
        super().__init__(
            f"UV task '{task_name}' failed: {reason}", error_code="UV002", context={"task": task_name, "reason": reason}
        )


# Docker-related exceptions
class DockerError(DHTError):
    """Base exception for Docker-related errors."""

    pass


class DockerNotFoundError(DockerError):
    """Raised when Docker is not installed."""

    def __init__(self) -> None:
        """Initialize Docker not found error."""
        super().__init__("Docker is not installed or not running", error_code="DOCK001")


class DockerBuildError(DockerError):
    """Raised when Docker build fails."""

    def __init__(self, image_name: str, reason: str) -> None:
        """Initialize Docker build error."""
        super().__init__(
            f"Failed to build Docker image '{image_name}': {reason}",
            error_code="DOCK002",
            context={"image": image_name, "reason": reason},
        )


# Environment-related exceptions
class EnvironmentError(DHTError):
    """Base exception for environment-related errors."""

    pass


class VirtualEnvError(EnvironmentError):
    """Raised when virtual environment operations fail."""

    def __init__(self, operation: str, reason: str) -> None:
        """Initialize virtual environment error."""
        super().__init__(
            f"Virtual environment {operation} failed: {reason}",
            error_code="ENV001",
            context={"operation": operation, "reason": reason},
        )


class PythonVersionError(EnvironmentError):
    """Raised when Python version requirements are not met."""

    def __init__(self, required: str, current: str) -> None:
        """Initialize Python version error."""
        super().__init__(
            f"Python {required} required, but {current} is installed",
            error_code="ENV002",
            context={"required": required, "current": current},
        )


# Configuration-related exceptions
class ConfigurationError(DHTError):
    """Base exception for configuration errors."""

    pass


class ConfigFileError(ConfigurationError):
    """Raised when configuration file operations fail."""

    def __init__(self, file_path: str, operation: str, reason: str) -> None:
        """Initialize config file error."""
        super().__init__(
            f"Failed to {operation} config file '{file_path}': {reason}",
            error_code="CFG001",
            context={"file": file_path, "operation": operation, "reason": reason},
        )


class InvalidConfigError(ConfigurationError):
    """Raised when configuration is invalid."""

    def __init__(self, config_name: str, reason: str) -> None:
        """Initialize invalid config error."""
        super().__init__(
            f"Invalid configuration '{config_name}': {reason}",
            error_code="CFG002",
            context={"config": config_name, "reason": reason},
        )


# Project-related exceptions
class ProjectError(DHTError):
    """Base exception for project-related errors."""

    pass


class ProjectNotFoundError(ProjectError):
    """Raised when project root cannot be found."""

    def __init__(self, search_path: str) -> None:
        """Initialize project not found error."""
        super().__init__(
            f"Could not find project root from {search_path}",
            error_code="PROJ001",
            context={"search_path": search_path},
        )


class ProjectTypeError(ProjectError):
    """Raised when project type cannot be determined."""

    def __init__(self, project_path: str) -> None:
        """Initialize project type error."""
        super().__init__(
            f"Cannot determine project type for {project_path}", error_code="PROJ002", context={"path": project_path}
        )


# Git-related exceptions
class GitError(DHTError):
    """Base exception for Git-related errors."""

    pass


class GitNotFoundError(GitError):
    """Raised when Git is not installed."""

    def __init__(self) -> None:
        """Initialize Git not found error."""
        super().__init__("Git is not installed", error_code="GIT001")


class GitRepositoryError(GitError):
    """Raised when Git repository operations fail."""

    def __init__(self, operation: str, reason: str) -> None:
        """Initialize Git repository error."""
        super().__init__(
            f"Git {operation} failed: {reason}", error_code="GIT002", context={"operation": operation, "reason": reason}
        )


# Import for typing


# Export all exceptions
__all__ = [
    # Base
    "DHTError",
    # Command
    "CommandError",
    "CommandNotFoundError",
    "CommandExecutionError",
    # Process
    "ProcessError",
    "SubprocessError",
    "TimeoutError",
    # UV
    "UVError",
    "UVNotFoundError",
    "UVTaskError",
    # Docker
    "DockerError",
    "DockerNotFoundError",
    "DockerBuildError",
    # Environment
    "EnvironmentError",
    "VirtualEnvError",
    "PythonVersionError",
    # Configuration
    "ConfigurationError",
    "ConfigFileError",
    "InvalidConfigError",
    # Project
    "ProjectError",
    "ProjectNotFoundError",
    "ProjectTypeError",
    # Git
    "GitError",
    "GitNotFoundError",
    "GitRepositoryError",
]
