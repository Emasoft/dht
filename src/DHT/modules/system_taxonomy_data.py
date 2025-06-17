#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
system_taxonomy_data.py - Taxonomy data structures for DHT
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Extracted from system_taxonomy.py to reduce file size
# - Contains the PRACTICAL_TAXONOMY data structure
#

from __future__ import annotations

# Practical taxonomy of development tools organized by use case
PRACTICAL_TAXONOMY = {
    'version_control': {
        'description': 'Source code management and version control systems',
        'tools': {
            'git': ['version', 'config.user.name', 'config.user.email', 'remote.origin.url', 'branch.current'],
            'hg': ['version', 'config.username', 'paths.default'],
            'svn': ['version', 'info.url', 'info.revision'],
        }
    },
    
    'language_runtimes': {
        'description': 'Programming language interpreters and runtimes',
        'tools': {
            'python': ['version', 'executable', 'prefix', 'packages'],
            'python3': ['version', 'executable', 'prefix', 'packages'],
            'node': ['version', 'npm_version', 'executable'],
            'java': ['version', 'vendor', 'home'],
            'ruby': ['version', 'gem_version', 'executable'],
            'go': ['version', 'gopath', 'goroot'],
            'rust': ['version', 'default_toolchain'],
            'php': ['version', 'ini_path', 'extensions'],
            'perl': ['version', 'executable', 'inc'],
            'dotnet': ['version', 'sdks', 'runtimes'],
        }
    },
    
    'package_managers': {
        'description': 'Tools for managing software packages and dependencies',
        'categories': {
            'system': {
                'description': 'Operating system package managers',
                'tools': {
                    'brew': ['version', 'prefix', 'cellar', 'taps'],
                    'macports': ['version', 'prefix', 'installed'],
                    'apt': ['version', 'sources', 'installed'],
                    'apt-get': ['version', 'sources', 'installed'],
                    'yum': ['version', 'repos', 'installed'],
                    'dnf': ['version', 'repos', 'installed'],
                    'zypper': ['version', 'repos', 'installed'],
                    'pacman': ['version', 'repos', 'installed'],
                    'choco': ['version', 'sources', 'installed'],
                    'scoop': ['version', 'buckets', 'installed'],
                    'winget': ['version', 'sources', 'installed'],
                }
            },
            'language': {
                'description': 'Language-specific package managers',
                'python': ['pip', 'pip3', 'pipenv', 'poetry', 'conda', 'mamba', 'pdm', 'hatch'],
                'javascript': ['npm', 'yarn', 'pnpm', 'bower'],
                'ruby': ['gem', 'bundler'],
                'rust': ['cargo'],
                'go': ['go_get', 'go_mod'],
                'java': ['maven', 'gradle', 'ant'],
                'dotnet': ['nuget', 'paket'],
                'php': ['composer', 'pear'],
                'perl': ['cpan', 'cpanm'],
            }
        }
    },
    
    'build_tools': {
        'description': 'Project building and compilation orchestration tools',
        'tools': {
            'make': ['version', 'features'],
            'cmake': ['version', 'generators', 'system_information'],
            'ninja': ['version'],
            'autotools': ['autoconf_version', 'automake_version', 'libtool_version'],
            'scons': ['version', 'python_version'],
            'bazel': ['version', 'release'],
            'buck': ['version'],
            'pants': ['version'],
            'gradle': ['version', 'java_version', 'daemon_status'],
            'maven': ['version', 'java_version', 'home'],
            'ant': ['version', 'java_version', 'home'],
            'meson': ['version'],
            'waf': ['version'],
        }
    },
    
    'compilers': {
        'description': 'Code compilation tools for various languages',
        'tools': {
            'gcc': ['version', 'target', 'configured_with'],
            'g++': ['version', 'target', 'configured_with'],
            'clang': ['version', 'target', 'default_target'],
            'clang++': ['version', 'target', 'default_target'],
            'msvc': ['version', 'tools_version', 'windows_sdk_version'],
            'rustc': ['version', 'host', 'release'],
            'go': ['version', 'goroot', 'gopath'],
            'javac': ['version', 'source_version', 'target_version'],
            'tsc': ['version'],
            'swiftc': ['version', 'target'],
        }
    },
    
    'containers_virtualization': {
        'description': 'Container and virtualization technologies',
        'tools': {
            'docker': ['version', 'server_version', 'storage_driver', 'daemon_running'],
            'podman': ['version', 'remote_version', 'storage_driver'],
            'containerd': ['version', 'revision'],
            'lxc': ['version', 'lxcpath'],
            'lxd': ['version', 'storage_backend'],
            'vagrant': ['version', 'plugins'],
            'virtualbox': ['version', 'extension_packs'],
            'vmware': ['version', 'license_status'],
            'qemu': ['version', 'targets'],
            'kvm': ['version', 'capabilities'],
            'kubectl': ['client_version', 'server_version', 'context'],
            'minikube': ['version', 'kubernetes_version', 'driver'],
            'kind': ['version'],
            'helm': ['version', 'repositories'],
            'docker-compose': ['version'],
            'kompose': ['version'],
            'skaffold': ['version'],
            'buildah': ['version'],
            'runc': ['version', 'spec_version'],
        }
    },
    
    'cloud_tools': {
        'description': 'Cloud platform CLIs and infrastructure tools',
        'tools': {
            'aws': ['cli_version', 'configured_profiles', 'default_region'],
            'gcloud': ['version', 'active_project', 'active_account'],
            'az': ['version', 'active_subscription', 'cloud'],
            'doctl': ['version', 'active_context'],
            'terraform': ['version'],
            'terragrunt': ['version', 'terraform_version'],
            'packer': ['version'],
            'ansible': ['version', 'python_version', 'inventory'],
            'puppet': ['version', 'environment'],
            'chef': ['version', 'cookbook_path'],
            'saltstack': ['version', 'master'],
            'consul': ['version', 'datacenter'],
            'vault': ['version', 'address'],
            'nomad': ['version', 'region'],
        }
    },
}

# Export public API
__all__ = ["PRACTICAL_TAXONOMY"]