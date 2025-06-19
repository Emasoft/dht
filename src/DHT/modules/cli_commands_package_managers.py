#!/usr/bin/env python3
"""
cli_commands_package_managers.py - Package manager CLI commands

This module contains CLI command definitions for package managers,
both language-specific and system package managers.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Extracted from cli_commands_registry.py to reduce file size
# - Contains language-specific package managers (pip, npm, cargo, etc.)
# - Contains system package managers (brew, apt, yum, etc.)
#

from typing import Any

PACKAGE_MANAGER_COMMANDS: dict[str, dict[str, Any]] = {
    # Package Managers - Language specific
    'pip': {
        'commands': {
            'version': 'pip --version',
            'list': 'pip list --format=json',
            'inspect': 'pip inspect --json',
            'config': 'pip config list',
        },
        'category': 'package_managers.language.python',
        'format': 'json'
    },

    'pip3': {
        'commands': {
            'version': 'pip3 --version',
            'list': 'pip3 list --format=json',
            'inspect': 'pip3 inspect',
            'config': 'pip3 config list',
        },
        'category': 'package_managers.language.python',
        'format': 'json'
    },

    'uv': {
        'commands': {
            'version': 'uv --version',
            'pip_list': 'uv pip list --format=json',
            'tool_list': 'uv tool list',
            'python_list': 'uv python list',
        },
        'category': 'package_managers.language.python',
        'format': 'auto'
    },

    'npm': {
        'commands': {
            'version': 'npm --version',
            'list': 'npm list -g --json',
            'config': 'npm config list --json',
            'registry': 'npm config get registry',
        },
        'category': 'package_managers.language.javascript',
        'format': 'json'
    },

    'yarn': {
        'commands': {
            'version': 'yarn --version',
            'list': 'yarn global list --json',
            'config': 'yarn config list',
        },
        'category': 'package_managers.language.javascript',
        'format': 'auto'
    },

    'pnpm': {
        'commands': {
            'version': 'pnpm --version',
            'list': 'pnpm list -g --json',
            'config': 'pnpm config list',
        },
        'category': 'package_managers.language.javascript',
        'format': 'json'
    },

    'cargo': {
        'commands': {
            'version': 'cargo --version',
            'installed': 'cargo install --list',
            'search_paths': 'cargo --list',
        },
        'category': 'package_managers.language.rust',
        'format': 'auto'
    },

    'gem': {
        'commands': {
            'version': 'gem --version',
            'list': 'gem list --local',
            'environment': 'gem environment',
        },
        'category': 'package_managers.language.ruby',
        'format': 'auto'
    },

    'bundler': {
        'commands': {
            'version': 'bundle --version',
            'config': 'bundle config',
            'list': 'bundle list',
        },
        'category': 'package_managers.language.ruby',
        'format': 'auto'
    },

    'maven': {
        'commands': {
            'version': 'mvn --version',
            'effective_pom': 'mvn help:effective-pom',
            'dependency_tree': 'mvn dependency:tree',
        },
        'category': 'package_managers.language.java',
        'format': 'auto'
    },

    'gradle': {
        'commands': {
            'version': 'gradle --version',
            'properties': 'gradle properties',
            'tasks': 'gradle tasks --all',
        },
        'category': 'package_managers.language.java',
        'format': 'auto'
    },

    # Package Managers - System
    'brew': {
        'commands': {
            'version': 'brew --version',
            'list': 'brew list --versions',
            'config': 'brew config',
            'prefix': 'brew --prefix',
            'tap_list': 'brew tap',
        },
        'category': 'package_managers.system',
        'platforms': ['macos', 'linux'],
        'format': 'auto'
    },

    'apt': {
        'commands': {
            'version': 'apt --version',
            'list': 'apt list --installed 2>/dev/null',
            'sources': 'apt-cache policy',
            'update_available': 'apt list --upgradable 2>/dev/null',
        },
        'category': 'package_managers.system',
        'platforms': ['linux'],
        'format': 'auto'
    },

    'apt-get': {
        'commands': {
            'version': 'apt-get --version',
            'update_check': 'apt-get check',
        },
        'category': 'package_managers.system',
        'platforms': ['linux'],
        'format': 'auto'
    },

    'dpkg': {
        'commands': {
            'version': 'dpkg --version',
            'list': 'dpkg -l',
            'architecture': 'dpkg --print-architecture',
        },
        'category': 'package_managers.system',
        'platforms': ['linux'],
        'format': 'auto'
    },

    'yum': {
        'commands': {
            'version': 'yum --version',
            'list': 'yum list installed',
            'repolist': 'yum repolist',
        },
        'category': 'package_managers.system',
        'platforms': ['linux'],
        'format': 'auto'
    },

    'dnf': {
        'commands': {
            'version': 'dnf --version',
            'list': 'dnf list installed',
            'repolist': 'dnf repolist',
        },
        'category': 'package_managers.system',
        'platforms': ['linux'],
        'format': 'auto'
    },

    'rpm': {
        'commands': {
            'version': 'rpm --version',
            'list': 'rpm -qa',
            'verify': 'rpm --verify --all',
        },
        'category': 'package_managers.system',
        'platforms': ['linux'],
        'format': 'auto'
    },

    'zypper': {
        'commands': {
            'version': 'zypper --version',
            'list': 'zypper packages --installed-only',
            'repos': 'zypper repos',
        },
        'category': 'package_managers.system',
        'platforms': ['linux'],
        'format': 'auto'
    },

    'pacman': {
        'commands': {
            'version': 'pacman --version',
            'list': 'pacman -Q',
            'info': 'pacman -Qi',
        },
        'category': 'package_managers.system',
        'platforms': ['linux'],
        'format': 'auto'
    },

    'snap': {
        'commands': {
            'version': 'snap version',
            'list': 'snap list',
            'services': 'snap services',
        },
        'category': 'package_managers.system',
        'platforms': ['linux'],
        'format': 'auto'
    },

    'flatpak': {
        'commands': {
            'version': 'flatpak --version',
            'list': 'flatpak list',
            'remotes': 'flatpak remotes',
        },
        'category': 'package_managers.system',
        'platforms': ['linux'],
        'format': 'auto'
    },

    'choco': {
        'commands': {
            'version': 'choco --version',
            'list': 'choco list --local-only',
            'sources': 'choco source list',
        },
        'category': 'package_managers.system',
        'platforms': ['windows'],
        'format': 'auto'
    },

    'scoop': {
        'commands': {
            'version': 'scoop --version',
            'list': 'scoop list',
            'buckets': 'scoop bucket list',
        },
        'category': 'package_managers.system',
        'platforms': ['windows'],
        'format': 'auto'
    },

    'winget': {
        'commands': {
            'version': 'winget --version',
            'list': 'winget list',
            'sources': 'winget source list',
        },
        'category': 'package_managers.system',
        'platforms': ['windows'],
        'format': 'auto'
    },
}
