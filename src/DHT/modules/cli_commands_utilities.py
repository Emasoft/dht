#!/usr/bin/env python3
"""
cli_commands_utilities.py - Utility tool CLI commands  This module contains CLI command definitions for various utility tools including network tools, system tools, archive managers, testing tools, and more.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

"""
cli_commands_utilities.py - Utility tool CLI commands

This module contains CLI command definitions for various utility tools including
network tools, system tools, archive managers, testing tools, and more.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Extracted from cli_commands_registry.py to reduce file size
# - Contains network tools, system tools, archive managers
# - Contains testing tools, database tools, text processing tools
# - Contains documentation tools and CI/CD tools
#

from typing import Any

UTILITY_COMMANDS: dict[str, dict[str, Any]] = {
    # Network Tools
    "curl": {
        "commands": {
            "version": "curl --version",
            "help": "curl --help",
        },
        "category": "network_tools",
        "format": "auto",
    },
    "wget": {
        "commands": {
            "version": "wget --version",
            "help": "wget --help",
        },
        "category": "network_tools",
        "format": "auto",
    },
    "openssl": {
        "commands": {
            "version": "openssl version -a",
            "ciphers": "openssl ciphers -v",
            "engines": "openssl engine -v",
        },
        "category": "network_tools",
        "format": "auto",
    },
    "ssh": {
        "commands": {
            "version": "ssh -V 2>&1",
            "config": "ssh -G localhost",
        },
        "category": "network_tools",
        "format": "auto",
    },
    "rsync": {
        "commands": {
            "version": "rsync --version",
            "help": "rsync --help",
        },
        "category": "network_tools",
        "format": "auto",
    },
    "netcat": {
        "commands": {
            "version": "nc -h 2>&1 | head -n 1",
            "help": "nc -h 2>&1",
        },
        "category": "network_tools",
        "format": "auto",
    },
    "telnet": {
        "commands": {
            "version": 'telnet --version 2>&1 || echo "telnet installed"',
        },
        "category": "network_tools",
        "format": "auto",
    },
    # System Tools
    "systemctl": {
        "commands": {
            "version": "systemctl --version",
            "status": "systemctl status",
            "list_units": "systemctl list-units --type=service",
        },
        "category": "system_tools",
        "platforms": ["linux"],
        "format": "auto",
    },
    "ps": {
        "commands": {
            "version": "ps --version 2>&1",
            "aux": "ps aux | head -n 5",
        },
        "category": "system_tools",
        "format": "auto",
    },
    "top": {
        "commands": {
            "version": "top -v 2>&1 || top -h 2>&1 | head -n 1",
        },
        "category": "system_tools",
        "format": "auto",
    },
    "htop": {
        "commands": {
            "version": "htop --version",
            "help": "htop --help",
        },
        "category": "system_tools",
        "format": "auto",
    },
    "df": {
        "commands": {
            "version": "df --version 2>&1 || df -h",
            "human": "df -h",
        },
        "category": "system_tools",
        "format": "auto",
    },
    "du": {
        "commands": {
            "version": "du --version 2>&1 || du -h .",
            "summary": "du -sh .",
        },
        "category": "system_tools",
        "format": "auto",
    },
    "lsof": {
        "commands": {
            "version": "lsof -v 2>&1 | head -n 1",
            "help": "lsof -h 2>&1",
        },
        "category": "system_tools",
        "format": "auto",
    },
    "wsl": {
        "commands": {
            "version": "wsl --version",
            "list": "wsl --list --verbose",
            "status": "wsl --status",
        },
        "category": "system_tools",
        "platforms": ["windows"],
        "format": "auto",
    },
    # Archive Managers
    "tar": {
        "commands": {
            "version": "tar --version",
            "help": "tar --help | head -n 20",
        },
        "category": "system_tools",
        "format": "auto",
    },
    "gzip": {
        "commands": {
            "version": "gzip --version",
            "help": "gzip --help 2>&1",
        },
        "category": "system_tools",
        "format": "auto",
    },
    "zip": {
        "commands": {
            "version": "zip --version 2>&1 | head -n 2",
            "help": "zip --help 2>&1 | head -n 20",
        },
        "category": "system_tools",
        "format": "auto",
    },
    "unzip": {
        "commands": {
            "version": "unzip -v 2>&1 | head -n 1",
            "help": "unzip -h 2>&1",
        },
        "category": "system_tools",
        "format": "auto",
    },
    "7z": {
        "commands": {
            "version": "7z | head -n 2",
            "info": "7z i",
        },
        "category": "system_tools",
        "format": "auto",
    },
    "rar": {
        "commands": {
            "version": "rar | head -n 2",
            "help": "rar -? | head -n 20",
        },
        "category": "system_tools",
        "format": "auto",
    },
    # Testing Tools
    "pytest": {
        "commands": {
            "version": "pytest --version",
            "markers": "pytest --markers",
            "fixtures": "pytest --fixtures",
        },
        "category": "testing_tools",
        "format": "auto",
    },
    "unittest": {
        "commands": {
            "version": "python -m unittest --version",
            "help": "python -m unittest -h",
        },
        "category": "testing_tools",
        "format": "auto",
    },
    "coverage": {
        "commands": {
            "version": "coverage --version",
            "help": "coverage help",
        },
        "category": "testing_tools",
        "format": "auto",
    },
    # Database Tools
    "mysql": {
        "commands": {
            "version": "mysql --version",
            "help": "mysql --help | head -n 20",
        },
        "category": "database_tools",
        "format": "auto",
    },
    "psql": {
        "commands": {
            "version": "psql --version",
            "help": "psql --help | head -n 20",
        },
        "category": "database_tools",
        "format": "auto",
    },
    "mongod": {
        "commands": {
            "version": "mongod --version",
            "help": "mongod --help | head -n 20",
        },
        "category": "database_tools",
        "format": "auto",
    },
    "redis-cli": {
        "commands": {
            "version": "redis-cli --version",
            "help": "redis-cli --help",
        },
        "category": "database_tools",
        "format": "auto",
    },
    "sqlite3": {
        "commands": {
            "version": "sqlite3 --version",
            "help": "sqlite3 --help | head -n 20",
        },
        "category": "database_tools",
        "format": "auto",
    },
    # Text Processing
    "jq": {
        "commands": {
            "version": "jq --version",
            "help": "jq --help",
        },
        "category": "text_processing",
        "format": "auto",
    },
    "yq": {
        "commands": {
            "version": "yq --version",
            "help": "yq --help",
        },
        "category": "text_processing",
        "format": "auto",
    },
    "xmllint": {
        "commands": {
            "version": "xmllint --version 2>&1",
            "help": "xmllint --help 2>&1 | head -n 20",
        },
        "category": "text_processing",
        "format": "auto",
    },
    "pandoc": {
        "commands": {
            "version": "pandoc --version",
            "list_formats": "pandoc --list-output-formats",
        },
        "category": "text_processing",
        "format": "auto",
    },
    "pdflatex": {
        "commands": {
            "version": "pdflatex --version",
            "help": "pdflatex --help | head -n 20",
        },
        "category": "text_processing",
        "format": "auto",
    },
    # Documentation Tools
    "sphinx-build": {
        "commands": {
            "version": "sphinx-build --version",
            "help": "sphinx-build --help",
        },
        "category": "documentation_tools",
        "format": "auto",
    },
    "mkdocs": {
        "commands": {
            "version": "mkdocs --version",
            "help": "mkdocs --help",
        },
        "category": "documentation_tools",
        "format": "auto",
    },
    "doxygen": {
        "commands": {
            "version": "doxygen --version",
            "help": "doxygen --help | head -n 20",
        },
        "category": "documentation_tools",
        "format": "auto",
    },
    "asciidoctor": {
        "commands": {
            "version": "asciidoctor --version",
            "help": "asciidoctor --help",
        },
        "category": "documentation_tools",
        "format": "auto",
    },
    "yard": {
        "commands": {
            "version": "yard --version",
            "help": "yard --help",
        },
        "category": "documentation_tools",
        "format": "auto",
    },
    # CI/CD Tools
    "jenkins": {
        "commands": {
            "version": "jenkins --version 2>&1 || java -jar jenkins.war --version 2>&1",
            "help": 'jenkins --help 2>&1 || echo "Jenkins CLI"',
        },
        "category": "ci_cd_tools",
        "format": "auto",
    },
    "travis": {
        "commands": {
            "version": "travis version",
            "help": "travis help",
        },
        "category": "ci_cd_tools",
        "format": "auto",
    },
    "circleci": {
        "commands": {
            "version": "circleci version",
            "config_validate": "circleci config validate",
        },
        "category": "ci_cd_tools",
        "format": "auto",
    },
    "gitlab-runner": {
        "commands": {
            "version": "gitlab-runner --version",
            "list": "gitlab-runner list",
        },
        "category": "ci_cd_tools",
        "format": "auto",
    },
    "gh": {
        "commands": {
            "version": "gh --version",
            "auth_status": "gh auth status",
            "repo_view": "gh repo view --json name,description,url",
        },
        "category": "ci_cd_tools",
        "format": "auto",
    },
    "act": {
        "commands": {
            "version": "act --version",
            "list": "act -l",
        },
        "category": "ci_cd_tools",
        "format": "auto",
    },
}
