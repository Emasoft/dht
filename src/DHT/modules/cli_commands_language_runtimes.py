#!/usr/bin/env python3
"""
cli_commands_language_runtimes.py - Language runtime CLI commands

This module contains CLI command definitions for language runtimes.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Extracted from cli_commands_registry.py to reduce file size
# - Contains language runtime commands (python, node, java, ruby, go, rust)
#

from typing import Any

LANGUAGE_RUNTIME_COMMANDS: dict[str, dict[str, Any]] = {
    'python': {
        'commands': {
            'version': 'python --version',
            'executable': 'python -c "import sys; print(sys.executable)"',
            'prefix': 'python -c "import sys; print(sys.prefix)"',
            'packages': 'python -m pip list --format=json',
        },
        'category': 'language_runtimes',
        'format': 'auto'
    },

    'python3': {
        'commands': {
            'version': 'python3 --version',
            'executable': 'python3 -c "import sys; print(sys.executable)"',
            'prefix': 'python3 -c "import sys; print(sys.prefix)"',
            'packages': 'python3 -m pip list --format=json',
        },
        'category': 'language_runtimes',
        'format': 'auto'
    },

    'node': {
        'commands': {
            'version': 'node --version',
            'npm_version': 'npm --version',
            'executable': 'node -p "process.execPath"',
            'modules': 'npm list -g --json --depth=0',
        },
        'category': 'language_runtimes',
        'format': 'auto'
    },

    'java': {
        'commands': {
            'version': 'java -version 2>&1',
            'home': 'java -XshowSettings:properties -version 2>&1 | grep "java.home"',
            'vendor': 'java -XshowSettings:properties -version 2>&1 | grep "java.vendor"',
        },
        'category': 'language_runtimes',
        'format': 'auto'
    },

    'ruby': {
        'commands': {
            'version': 'ruby --version',
            'gem_version': 'gem --version',
            'executable': 'ruby -e "puts RbConfig.ruby"',
        },
        'category': 'language_runtimes',
        'format': 'auto'
    },

    'go': {
        'commands': {
            'version': 'go version',
            'env': 'go env -json',
            'gopath': 'go env GOPATH',
            'goroot': 'go env GOROOT',
        },
        'category': 'language_runtimes',
        'format': 'auto'
    },

    'rust': {
        'commands': {
            'version': 'rustc --version',
            'toolchains': 'rustup toolchain list',
            'default_toolchain': 'rustup default',
        },
        'category': 'language_runtimes',
        'format': 'auto'
    },
}
