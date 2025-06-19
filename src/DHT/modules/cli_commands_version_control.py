#!/usr/bin/env python3
"""
cli_commands_version_control.py - Version control CLI commands

This module contains CLI command definitions for version control tools.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Extracted from cli_commands_registry.py to reduce file size
# - Contains version control tool commands (git, hg, svn)
#

from typing import Any

VERSION_CONTROL_COMMANDS: dict[str, dict[str, Any]] = {
    'git': {
        'commands': {
            'version': 'git --version',
            'config_user_name': 'git config --global user.name',
            'config_user_email': 'git config --global user.email',
            'remote_origin': 'git remote get-url origin 2>&1',
            'current_branch': 'git rev-parse --abbrev-ref HEAD 2>&1',
            'status': 'git status --porcelain',
        },
        'category': 'version_control',
        'format': 'auto'
    },

    'hg': {
        'commands': {
            'version': 'hg --version',
            'config': 'hg config',
            'paths': 'hg paths',
        },
        'category': 'version_control',
        'format': 'auto'
    },

    'svn': {
        'commands': {
            'version': 'svn --version --quiet',
            'info': 'svn info',
        },
        'category': 'version_control',
        'format': 'auto'
    },
}
