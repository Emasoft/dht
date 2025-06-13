#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Initial implementation of CLI commands registry module
# - Defines CLI_COMMANDS dictionary with comprehensive tool commands
# - Implements get_platform_specific_commands function with platform filtering
# - Implements get_commands_by_category function with nested category support
# - Includes commands for all major development tools
# - Integrates with system_taxonomy module for platform checks
# - Supports command format specifications (json, auto, etc.)
# - Handles platform restrictions where applicable
# 

"""
CLI commands registry module for DHT.

This module provides a comprehensive registry of CLI commands for various
development tools. It includes:
- Command definitions for different operations (version, config, etc.)
- Category assignments matching the system taxonomy
- Format specifications for output parsing
- Platform restrictions for platform-specific tools

The registry is designed to be extensible and integrate with the system
taxonomy for platform-aware filtering.
"""

from typing import Dict, Any, Optional
from . import system_taxonomy


# Define the CLI commands registry
CLI_COMMANDS: Dict[str, Dict[str, Any]] = {
    # Version Control Tools
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
    
    # Language Runtimes
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
            'prefix': 'brew --prefix',
            'list': 'brew list --versions',
            'taps': 'brew tap',
            'config': 'brew config',
        },
        'category': 'package_managers.system.macos',
        'platforms': ['macos'],
        'format': 'auto'
    },
    
    'macports': {
        'commands': {
            'version': 'port version',
            'installed': 'port installed',
            'list': 'port list installed',
        },
        'category': 'package_managers.system.macos',
        'platforms': ['macos'],
        'format': 'auto'
    },
    
    'apt': {
        'commands': {
            'version': 'apt --version',
            'list': 'apt list --installed',
            'sources': 'apt-cache policy',
        },
        'category': 'package_managers.system.linux',
        'platforms': ['linux'],
        'format': 'auto'
    },
    
    'apt-get': {
        'commands': {
            'version': 'apt-get --version',
            'sources': 'apt-cache policy',
        },
        'category': 'package_managers.system.linux',
        'platforms': ['linux'],
        'format': 'auto'
    },
    
    'yum': {
        'commands': {
            'version': 'yum --version',
            'list': 'yum list installed',
            'repolist': 'yum repolist',
        },
        'category': 'package_managers.system.linux',
        'platforms': ['linux'],
        'format': 'auto'
    },
    
    'dnf': {
        'commands': {
            'version': 'dnf --version',
            'list': 'dnf list installed',
            'repolist': 'dnf repolist',
        },
        'category': 'package_managers.system.linux',
        'platforms': ['linux'],
        'format': 'auto'
    },
    
    'zypper': {
        'commands': {
            'version': 'zypper --version',
            'list': 'zypper se --installed-only',
            'repos': 'zypper repos',
        },
        'category': 'package_managers.system.linux',
        'platforms': ['linux'],
        'format': 'auto'
    },
    
    'pacman': {
        'commands': {
            'version': 'pacman --version',
            'list': 'pacman -Q',
            'info': 'pacman -Si',
        },
        'category': 'package_managers.system.linux',
        'platforms': ['linux'],
        'format': 'auto'
    },
    
    'choco': {
        'commands': {
            'version': 'choco --version',
            'list': 'choco list --local-only',
            'sources': 'choco source list',
        },
        'category': 'package_managers.system.windows',
        'platforms': ['windows'],
        'format': 'auto'
    },
    
    'scoop': {
        'commands': {
            'version': 'scoop --version',
            'list': 'scoop list',
            'buckets': 'scoop bucket list',
        },
        'category': 'package_managers.system.windows',
        'platforms': ['windows'],
        'format': 'auto'
    },
    
    'winget': {
        'commands': {
            'version': 'winget --version',
            'list': 'winget list',
            'sources': 'winget source list',
        },
        'category': 'package_managers.system.windows',
        'platforms': ['windows'],
        'format': 'auto'
    },
    
    # Build Tools
    'make': {
        'commands': {
            'version': 'make --version',
            'features': 'make -p -f/dev/null | grep FEATURES',
        },
        'category': 'build_tools',
        'format': 'auto'
    },
    
    'cmake': {
        'commands': {
            'version': 'cmake --version',
            'generators': 'cmake --help | grep "Generators"',
            'system_info': 'cmake --system-information',
        },
        'category': 'build_tools',
        'format': 'auto'
    },
    
    'ninja': {
        'commands': {
            'version': 'ninja --version',
        },
        'category': 'build_tools',
        'format': 'auto'
    },
    
    'bazel': {
        'commands': {
            'version': 'bazel --version',
            'info': 'bazel info',
        },
        'category': 'build_tools',
        'format': 'auto'
    },
    
    # Compilers
    'gcc': {
        'commands': {
            'version': 'gcc --version',
            'target': 'gcc -dumpmachine',
            'search_dirs': 'gcc -print-search-dirs',
        },
        'category': 'compilers',
        'format': 'auto'
    },
    
    'g++': {
        'commands': {
            'version': 'g++ --version',
            'target': 'g++ -dumpmachine',
            'search_dirs': 'g++ -print-search-dirs',
        },
        'category': 'compilers',
        'format': 'auto'
    },
    
    'clang': {
        'commands': {
            'version': 'clang --version',
            'target': 'clang -print-target-triple',
            'resource_dir': 'clang -print-resource-dir',
        },
        'category': 'compilers',
        'format': 'auto'
    },
    
    'clang++': {
        'commands': {
            'version': 'clang++ --version',
            'target': 'clang++ -print-target-triple',
            'resource_dir': 'clang++ -print-resource-dir',
        },
        'category': 'compilers',
        'format': 'auto'
    },
    
    'rustc': {
        'commands': {
            'version': 'rustc --version',
            'host': 'rustc --print host',
            'target_list': 'rustc --print target-list',
        },
        'category': 'compilers',
        'format': 'auto'
    },
    
    'javac': {
        'commands': {
            'version': 'javac -version 2>&1',
            'help': 'javac -help',
        },
        'category': 'compilers',
        'format': 'auto'
    },
    
    'msvc': {
        'commands': {
            'version': 'cl.exe 2>&1 | head -n 1',
            'help': 'cl.exe /? 2>&1',
        },
        'category': 'compilers',
        'platforms': ['windows'],
        'format': 'auto'
    },
    
    # Containers and Virtualization
    'docker': {
        'commands': {
            'version': 'docker --version',
            'info': 'docker info --format json',
            'system': 'docker system info',
            'images': 'docker images --format json',
            'ps': 'docker ps --format json',
        },
        'category': 'containers_virtualization',
        'format': 'json'
    },
    
    'podman': {
        'commands': {
            'version': 'podman --version',
            'info': 'podman info --format json',
            'images': 'podman images --format json',
        },
        'category': 'containers_virtualization',
        'format': 'json'
    },
    
    'kubectl': {
        'commands': {
            'version': 'kubectl version --client --output=json',
            'config': 'kubectl config view -o json',
            'contexts': 'kubectl config get-contexts',
        },
        'category': 'containers_virtualization',
        'format': 'json'
    },
    
    'helm': {
        'commands': {
            'version': 'helm version --short',
            'repo_list': 'helm repo list -o json',
            'list': 'helm list -A -o json',
        },
        'category': 'containers_virtualization',
        'format': 'json'
    },
    
    'minikube': {
        'commands': {
            'version': 'minikube version',
            'status': 'minikube status -o json',
            'profile_list': 'minikube profile list -o json',
        },
        'category': 'containers_virtualization',
        'format': 'json'
    },
    
    'kind': {
        'commands': {
            'version': 'kind --version',
            'clusters': 'kind get clusters',
        },
        'category': 'containers_virtualization',
        'format': 'auto'
    },
    
    'vagrant': {
        'commands': {
            'version': 'vagrant --version',
            'global_status': 'vagrant global-status',
            'plugin_list': 'vagrant plugin list',
        },
        'category': 'containers_virtualization',
        'format': 'auto'
    },
    
    # Cloud Tools
    'aws': {
        'commands': {
            'version': 'aws --version',
            'configure_list': 'aws configure list',
            'sts_identity': 'aws sts get-caller-identity',
        },
        'category': 'cloud_tools',
        'format': 'json'
    },
    
    'gcloud': {
        'commands': {
            'version': 'gcloud --version',
            'info': 'gcloud info --format=json',
            'config_list': 'gcloud config list --format=json',
        },
        'category': 'cloud_tools',
        'format': 'json'
    },
    
    'az': {
        'commands': {
            'version': 'az --version',
            'account_show': 'az account show',
            'config': 'az config show',
        },
        'category': 'cloud_tools',
        'format': 'json'
    },
    
    'terraform': {
        'commands': {
            'version': 'terraform version -json',
            'providers': 'terraform providers',
        },
        'category': 'cloud_tools',
        'format': 'json'
    },
    
    'ansible': {
        'commands': {
            'version': 'ansible --version',
            'config': 'ansible-config dump',
            'inventory': 'ansible-inventory --list',
        },
        'category': 'cloud_tools',
        'format': 'auto'
    },
    
    'puppet': {
        'commands': {
            'version': 'puppet --version',
            'config': 'puppet config print',
            'module_list': 'puppet module list',
        },
        'category': 'cloud_tools',
        'format': 'auto'
    },
    
    'chef': {
        'commands': {
            'version': 'chef --version',
            'config': 'chef config show',
        },
        'category': 'cloud_tools',
        'format': 'auto'
    },
    
    # Network Tools
    'curl': {
        'commands': {
            'version': 'curl --version',
            'help': 'curl --help',
        },
        'category': 'network_tools',
        'format': 'auto'
    },
    
    'wget': {
        'commands': {
            'version': 'wget --version',
            'help': 'wget --help',
        },
        'category': 'network_tools',
        'format': 'auto'
    },
    
    'openssl': {
        'commands': {
            'version': 'openssl version -a',
            'ciphers': 'openssl ciphers -v',
            'engines': 'openssl engine -v',
        },
        'category': 'network_tools',
        'format': 'auto'
    },
    
    'ssh': {
        'commands': {
            'version': 'ssh -V 2>&1',
            'config': 'ssh -G localhost',
        },
        'category': 'network_tools',
        'format': 'auto'
    },
    
    'rsync': {
        'commands': {
            'version': 'rsync --version',
            'help': 'rsync --help',
        },
        'category': 'network_tools',
        'format': 'auto'
    },
    
    'netcat': {
        'commands': {
            'version': 'nc -h 2>&1 | head -n 1',
            'help': 'nc -h 2>&1',
        },
        'category': 'network_tools',
        'format': 'auto'
    },
    
    'telnet': {
        'commands': {
            'version': 'telnet --version 2>&1 || echo "telnet installed"',
        },
        'category': 'network_tools',
        'format': 'auto'
    },
    
    # System Tools
    'systemctl': {
        'commands': {
            'version': 'systemctl --version',
            'status': 'systemctl status',
            'list_units': 'systemctl list-units --type=service',
        },
        'category': 'system_tools',
        'platforms': ['linux'],
        'format': 'auto'
    },
    
    'ps': {
        'commands': {
            'version': 'ps --version 2>&1',
            'aux': 'ps aux | head -n 5',
        },
        'category': 'system_tools',
        'format': 'auto'
    },
    
    'top': {
        'commands': {
            'version': 'top -v 2>&1 || top -h 2>&1 | head -n 1',
        },
        'category': 'system_tools',
        'format': 'auto'
    },
    
    'htop': {
        'commands': {
            'version': 'htop --version',
            'help': 'htop --help',
        },
        'category': 'system_tools',
        'format': 'auto'
    },
    
    'df': {
        'commands': {
            'version': 'df --version 2>&1 || df -h',
            'human': 'df -h',
        },
        'category': 'system_tools',
        'format': 'auto'
    },
    
    'du': {
        'commands': {
            'version': 'du --version 2>&1 || du -h .',
            'summary': 'du -sh .',
        },
        'category': 'system_tools',
        'format': 'auto'
    },
    
    'lsof': {
        'commands': {
            'version': 'lsof -v 2>&1 | head -n 1',
            'help': 'lsof -h 2>&1',
        },
        'category': 'system_tools',
        'format': 'auto'
    },
    
    'wsl': {
        'commands': {
            'version': 'wsl --version',
            'list': 'wsl --list --verbose',
            'status': 'wsl --status',
        },
        'category': 'system_tools',
        'platforms': ['windows'],
        'format': 'auto'
    },
    
    # Archive Managers
    'tar': {
        'commands': {
            'version': 'tar --version',
            'help': 'tar --help | head -n 20',
        },
        'category': 'system_tools',
        'format': 'auto'
    },
    
    'gzip': {
        'commands': {
            'version': 'gzip --version',
            'help': 'gzip --help 2>&1',
        },
        'category': 'system_tools',
        'format': 'auto'
    },
    
    'zip': {
        'commands': {
            'version': 'zip --version 2>&1 | head -n 2',
            'help': 'zip --help 2>&1 | head -n 20',
        },
        'category': 'system_tools',
        'format': 'auto'
    },
    
    'unzip': {
        'commands': {
            'version': 'unzip -v 2>&1 | head -n 1',
            'help': 'unzip -h 2>&1',
        },
        'category': 'system_tools',
        'format': 'auto'
    },
    
    '7z': {
        'commands': {
            'version': '7z | head -n 2',
            'info': '7z i',
        },
        'category': 'system_tools',
        'format': 'auto'
    },
    
    'rar': {
        'commands': {
            'version': 'rar | head -n 2',
            'help': 'rar -? | head -n 20',
        },
        'category': 'system_tools',
        'format': 'auto'
    },
    
    # Testing Tools
    'pytest': {
        'commands': {
            'version': 'pytest --version',
            'markers': 'pytest --markers',
            'fixtures': 'pytest --fixtures',
        },
        'category': 'build_tools',
        'format': 'auto'
    },
    
    'jest': {
        'commands': {
            'version': 'jest --version',
            'help': 'jest --help',
        },
        'category': 'build_tools',
        'format': 'auto'
    },
    
    'mocha': {
        'commands': {
            'version': 'mocha --version',
            'reporters': 'mocha --reporters',
        },
        'category': 'build_tools',
        'format': 'auto'
    },
    
    # Database Tools
    'mysql': {
        'commands': {
            'version': 'mysql --version',
            'help': 'mysql --help | head -n 20',
        },
        'category': 'system_tools',
        'format': 'auto'
    },
    
    'psql': {
        'commands': {
            'version': 'psql --version',
            'help': 'psql --help | head -n 20',
        },
        'category': 'system_tools',
        'format': 'auto'
    },
    
    'sqlite3': {
        'commands': {
            'version': 'sqlite3 --version',
            'help': 'sqlite3 -help | head -n 20',
        },
        'category': 'system_tools',
        'format': 'auto'
    },
    
    'redis-cli': {
        'commands': {
            'version': 'redis-cli --version',
            'info': 'redis-cli INFO server 2>&1',
        },
        'category': 'system_tools',
        'format': 'auto'
    },
    
    'mongo': {
        'commands': {
            'version': 'mongo --version',
            'help': 'mongo --help | head -n 20',
        },
        'category': 'system_tools',
        'format': 'auto'
    },
    
    # Text Processing
    'jq': {
        'commands': {
            'version': 'jq --version',
            'help': 'jq --help | head -n 20',
        },
        'category': 'system_tools',
        'format': 'auto'
    },
    
    'yq': {
        'commands': {
            'version': 'yq --version',
            'help': 'yq --help | head -n 20',
        },
        'category': 'system_tools',
        'format': 'auto'
    },
    
    'xmllint': {
        'commands': {
            'version': 'xmllint --version 2>&1',
            'help': 'xmllint --help 2>&1 | head -n 20',
        },
        'category': 'system_tools',
        'format': 'auto'
    },
    
    'pandoc': {
        'commands': {
            'version': 'pandoc --version',
            'list_input_formats': 'pandoc --list-input-formats',
            'list_output_formats': 'pandoc --list-output-formats',
        },
        'category': 'system_tools',
        'format': 'auto'
    },
    
    # Documentation Tools
    'sphinx': {
        'commands': {
            'version': 'sphinx-build --version',
            'help': 'sphinx-build --help | head -n 20',
        },
        'category': 'build_tools',
        'format': 'auto'
    },
    
    'mkdocs': {
        'commands': {
            'version': 'mkdocs --version',
            'help': 'mkdocs --help',
        },
        'category': 'build_tools',
        'format': 'auto'
    },
    
    'doxygen': {
        'commands': {
            'version': 'doxygen --version',
            'help': 'doxygen -h | head -n 20',
        },
        'category': 'build_tools',
        'format': 'auto'
    },
    
    'jekyll': {
        'commands': {
            'version': 'jekyll --version',
            'help': 'jekyll --help | head -n 20',
        },
        'category': 'build_tools',
        'format': 'auto'
    },
    
    'hugo': {
        'commands': {
            'version': 'hugo version',
            'env': 'hugo env',
        },
        'category': 'build_tools',
        'format': 'auto'
    },
    
    'graphviz': {
        'commands': {
            'version': 'dot -V 2>&1',
            'help': 'dot -? 2>&1',
        },
        'category': 'build_tools',
        'format': 'auto'
    },
    
    'plantuml': {
        'commands': {
            'version': 'plantuml -version',
            'help': 'plantuml -help',
        },
        'category': 'build_tools',
        'format': 'auto'
    },
    
    # CI/CD Tools
    'jenkins': {
        'commands': {
            'version': 'jenkins --version 2>&1 || echo "Jenkins CLI not installed"',
        },
        'category': 'cloud_tools',
        'format': 'auto'
    },
    
    'travis': {
        'commands': {
            'version': 'travis version',
            'help': 'travis help',
        },
        'category': 'cloud_tools',
        'format': 'auto'
    },
    
    'circleci': {
        'commands': {
            'version': 'circleci version',
            'config_validate': 'circleci config validate',
        },
        'category': 'cloud_tools',
        'format': 'auto'
    },
    
    'gitlab-runner': {
        'commands': {
            'version': 'gitlab-runner --version',
            'list': 'gitlab-runner list',
        },
        'category': 'cloud_tools',
        'format': 'auto'
    },
    
    'github': {
        'commands': {
            'version': 'gh --version',
            'auth_status': 'gh auth status',
            'config_list': 'gh config list',
        },
        'category': 'cloud_tools',
        'format': 'auto'
    },
    
    'drone': {
        'commands': {
            'version': 'drone --version',
            'info': 'drone info',
        },
        'category': 'cloud_tools',
        'format': 'auto'
    },
    
    'tekton': {
        'commands': {
            'version': 'tkn version',
            'pipeline_list': 'tkn pipeline list',
        },
        'category': 'cloud_tools',
        'format': 'auto'
    },
    
    'argocd': {
        'commands': {
            'version': 'argocd version --client',
            'app_list': 'argocd app list',
        },
        'category': 'cloud_tools',
        'format': 'auto'
    },
}


def get_platform_specific_commands(platform: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
    """
    Get commands filtered by platform.
    
    Args:
        platform: Platform to filter for (uses current platform if None or empty)
        
    Returns:
        dict: Filtered commands for the specified platform
    """
    # Handle empty string or None
    if not platform:
        platform = system_taxonomy.get_current_platform()
    
    filtered_commands = {}
    
    for cmd_name, cmd_def in CLI_COMMANDS.items():
        # Check if command has platform restrictions
        if 'platforms' in cmd_def:
            # If platform is restricted, check if current platform is allowed
            if platform in cmd_def['platforms']:
                filtered_commands[cmd_name] = cmd_def
        else:
            # No platform restrictions, check with system taxonomy
            if system_taxonomy.is_tool_available_on_platform(cmd_name, platform):
                filtered_commands[cmd_name] = cmd_def
    
    return filtered_commands


def get_commands_by_category(category: Optional[str]) -> Dict[str, Dict[str, Any]]:
    """
    Get commands filtered by category (supports partial matches).
    
    Args:
        category: Category to filter by (supports nested categories)
        
    Returns:
        dict: Commands matching the category
    """
    # Handle None category
    if category is None:
        return {}
    
    filtered_commands = {}
    
    for cmd_name, cmd_def in CLI_COMMANDS.items():
        cmd_category = cmd_def.get('category', '')
        
        # Check for exact match or if command category starts with requested category
        if cmd_category == category or cmd_category.startswith(category + '.'):
            filtered_commands[cmd_name] = cmd_def
        # Also check if requested category is a subcategory of command category
        elif category.startswith(cmd_category + '.'):
            filtered_commands[cmd_name] = cmd_def
    
    return filtered_commands