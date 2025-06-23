#!/usr/bin/env python3
from __future__ import annotations

"""
System taxonomy constants module for DHT.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Extracted from system_taxonomy.py to reduce file size
# - Contains platform exclusions, cross-platform tools, and platform-specific tools
# - Fixed import order - moved __future__ import to the top
#

"""
System taxonomy constants module for DHT.

This module contains platform-specific exclusions and tool lists used by the system taxonomy.
"""

# Define platform-specific exclusions
PLATFORM_EXCLUSIONS = {
    "macos": {
        "apt",
        "apt-get",
        "yum",
        "dnf",
        "zypper",
        "pacman",  # Linux package managers
        "msvc",
        "wsl",
        "choco",
        "scoop",
        "winget",  # Windows tools
    },
    "windows": {
        "brew",
        "macports",  # macOS package managers
        "apt",
        "apt-get",
        "yum",
        "dnf",
        "zypper",
        "pacman",  # Linux package managers
        "systemctl",
        "systemd",  # Linux system tools
    },
    "linux": {
        "brew",
        "macports",  # macOS package managers
        "msvc",
        "choco",
        "scoop",
        "winget",  # Windows tools
        "wsl",  # Windows Subsystem for Linux
    },
}

# Define cross-platform tools that are available everywhere
CROSS_PLATFORM_TOOLS = {
    # Version control
    "git",
    "hg",
    "svn",
    # Language runtimes
    "python",
    "python3",
    "node",
    "java",
    "ruby",
    "go",
    "rust",
    "dotnet",
    # Language package managers
    "pip",
    "pip3",
    "npm",
    "yarn",
    "pnpm",
    "cargo",
    "maven",
    "gradle",
    "bundler",
    "gem",
    "poetry",
    "pipenv",
    "pdm",
    "hatch",
    "setuptools",
    "twine",
    # Build tools
    "make",
    "cmake",
    "ninja",
    "scons",
    "bazel",
    "buck",
    "pants",
    # Compilers
    "gcc",
    "g++",
    "clang",
    "clang++",
    "rustc",
    "javac",
    # Containers and virtualization
    "docker",
    "podman",
    "kubectl",
    "helm",
    "minikube",
    "kind",
    # Cloud tools
    "aws",
    "gcloud",
    "az",
    "terraform",
    "ansible",
    "puppet",
    "chef",
    # Archive managers
    "tar",
    "gzip",
    "zip",
    "7z",
    "rar",
    # Network tools
    "curl",
    "wget",
    "openssl",
    "ssh",
    "rsync",
    "netcat",
    "telnet",
    # Database clients
    "mysql",
    "psql",
    "redis-cli",
    "mongo",
    "sqlite3",
    # Testing tools
    "pytest",
    "unittest",
    "jest",
    "mocha",
    "jasmine",
    "karma",
    "selenium",
    # CI/CD tools
    "jenkins",
    "travis",
    "circleci",
    "gitlab-runner",
    "github",
    "drone",
    "tekton",
    "argocd",
    # Other development tools
    "jq",
    "yq",
    "xmllint",
    "pandoc",
    "graphviz",
    "plantuml",
}

# Platform-specific tools mapping
PLATFORM_TOOLS = {
    "macos": {
        "package_managers": ["brew", "macports"],
        "compilers": ["clang", "clang++", "gcc", "g++", "swiftc"],
        "archive_managers": ["tar", "gzip", "bzip2", "zip", "unzip"],
        "system_tools": ["launchctl", "dscl", "diskutil", "system_profiler"],
    },
    "linux": {
        "package_managers": ["apt", "apt-get", "yum", "dnf", "zypper", "pacman", "snap", "flatpak"],
        "compilers": ["gcc", "g++", "clang", "clang++"],
        "archive_managers": ["tar", "gzip", "bzip2", "xz", "zip", "unzip"],
        "system_tools": ["systemctl", "systemd", "service", "cron", "at"],
    },
    "windows": {
        "package_managers": ["choco", "scoop", "winget"],
        "compilers": ["msvc", "gcc", "g++", "clang", "clang++"],
        "archive_managers": ["7z", "zip", "rar"],
        "system_tools": ["wsl", "powershell", "cmd"],
    },
}

# Export public API
__all__ = ["PLATFORM_EXCLUSIONS", "CROSS_PLATFORM_TOOLS", "PLATFORM_TOOLS"]
