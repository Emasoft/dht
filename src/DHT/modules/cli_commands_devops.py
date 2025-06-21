#!/usr/bin/env python3
"""
cli_commands_devops.py - DevOps tool CLI commands

This module contains CLI command definitions for containers, virtualization,
and cloud tools.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Extracted from cli_commands_registry.py to reduce file size
# - Contains containers and virtualization tools (docker, kubectl, vagrant)
# - Contains cloud tools (aws, gcloud, terraform, ansible)
#

from typing import Any

DEVOPS_COMMANDS: dict[str, dict[str, Any]] = {
    # Containers and Virtualization
    "docker": {
        "commands": {
            "version": "docker --version",
            "info": "docker info --format json",
            "system": "docker system info",
            "images": "docker images --format json",
            "ps": "docker ps --format json",
        },
        "category": "containers_virtualization",
        "format": "json",
    },
    "podman": {
        "commands": {
            "version": "podman --version",
            "info": "podman info --format json",
            "images": "podman images --format json",
        },
        "category": "containers_virtualization",
        "format": "json",
    },
    "kubectl": {
        "commands": {
            "version": "kubectl version --client --output=json",
            "config": "kubectl config view -o json",
            "contexts": "kubectl config get-contexts",
        },
        "category": "containers_virtualization",
        "format": "json",
    },
    "helm": {
        "commands": {
            "version": "helm version --short",
            "repo_list": "helm repo list -o json",
            "list": "helm list -A -o json",
        },
        "category": "containers_virtualization",
        "format": "json",
    },
    "minikube": {
        "commands": {
            "version": "minikube version",
            "status": "minikube status -o json",
            "profile_list": "minikube profile list -o json",
        },
        "category": "containers_virtualization",
        "format": "json",
    },
    "kind": {
        "commands": {
            "version": "kind --version",
            "clusters": "kind get clusters",
        },
        "category": "containers_virtualization",
        "format": "auto",
    },
    "vagrant": {
        "commands": {
            "version": "vagrant --version",
            "global_status": "vagrant global-status",
            "plugin_list": "vagrant plugin list",
        },
        "category": "containers_virtualization",
        "format": "auto",
    },
    # Cloud Tools
    "aws": {
        "commands": {
            "version": "aws --version",
            "configure_list": "aws configure list",
            "sts_identity": "aws sts get-caller-identity",
        },
        "category": "cloud_tools",
        "format": "json",
    },
    "gcloud": {
        "commands": {
            "version": "gcloud --version",
            "info": "gcloud info --format=json",
            "config_list": "gcloud config list --format=json",
        },
        "category": "cloud_tools",
        "format": "json",
    },
    "az": {
        "commands": {
            "version": "az --version",
            "account_show": "az account show",
            "config": "az config show",
        },
        "category": "cloud_tools",
        "format": "json",
    },
    "terraform": {
        "commands": {
            "version": "terraform version -json",
            "providers": "terraform providers",
        },
        "category": "cloud_tools",
        "format": "json",
    },
    "ansible": {
        "commands": {
            "version": "ansible --version",
            "config": "ansible-config dump",
            "inventory": "ansible-inventory --list",
        },
        "category": "cloud_tools",
        "format": "auto",
    },
    "puppet": {
        "commands": {
            "version": "puppet --version",
            "config": "puppet config print",
            "module_list": "puppet module list",
        },
        "category": "cloud_tools",
        "format": "auto",
    },
    "chef": {
        "commands": {
            "version": "chef --version",
            "config": "chef config show",
        },
        "category": "cloud_tools",
        "format": "auto",
    },
}
