#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Initial implementation of system taxonomy module
# - Implements platform detection and normalization
# - Implements tool availability checking with platform-specific exclusions
# - Implements category filtering based on platform
# - Implements tool field retrieval
# - Defines comprehensive PRACTICAL_TAXONOMY with use-case driven categories
# - Defines PLATFORM_TOOLS mapping for platform-specific tools
# - Handles cross-platform tools and platform exclusions
# - Supports nested category structures for package managers
# 

"""
System taxonomy module for DHT.

This module provides a comprehensive categorization of development tools
organized by use-case. It handles platform-specific availability checking
and filtering to ensure only relevant tools are presented for each platform.

The taxonomy is designed to be:
- Use-case driven (organized by what developers need tools for)
- Platform-aware (knows which tools exist on which platforms)
- Atomic (every piece of information has a clear path)
- Extensible (easy to add new tools and categories)
"""

import platform
from typing import Dict, List, Any, Optional
import copy


def get_current_platform() -> str:
    """
    Get the current platform name, normalized to lowercase.
    
    Returns:
        str: Normalized platform name ('macos', 'linux', 'windows', etc.)
    """
    system = platform.system()
    
    # Normalize platform names
    if system == 'Darwin':
        return 'macos'
    elif system == 'Linux':
        return 'linux'
    elif system == 'Windows':
        return 'windows'
    else:
        # Return as-is but lowercase for unknown platforms
        return system.lower()


# Define platform-specific exclusions
PLATFORM_EXCLUSIONS = {
    'macos': {
        'apt', 'apt-get', 'yum', 'dnf', 'zypper', 'pacman',  # Linux package managers
        'msvc', 'wsl', 'choco', 'scoop', 'winget',  # Windows tools
    },
    'windows': {
        'brew', 'macports',  # macOS package managers
        'apt', 'apt-get', 'yum', 'dnf', 'zypper', 'pacman',  # Linux package managers
        'systemctl', 'systemd',  # Linux system tools
    },
    'linux': {
        'brew', 'macports',  # macOS package managers
        'msvc', 'choco', 'scoop', 'winget',  # Windows tools
        'wsl',  # Windows Subsystem for Linux
    },
}

# Define cross-platform tools that are available everywhere
CROSS_PLATFORM_TOOLS = {
    # Version control
    'git', 'hg', 'svn',
    
    # Language runtimes
    'python', 'python3', 'node', 'java', 'ruby', 'go', 'rust', 'dotnet',
    
    # Language package managers
    'pip', 'pip3', 'npm', 'yarn', 'pnpm', 'cargo', 'maven', 'gradle', 'bundler', 'gem',
    'poetry', 'pipenv', 'pdm', 'hatch', 'setuptools', 'twine',
    
    # Build tools
    'make', 'cmake', 'ninja', 'scons', 'bazel', 'buck', 'pants',
    
    # Compilers
    'gcc', 'g++', 'clang', 'clang++', 'rustc', 'javac',
    
    # Containers and virtualization
    'docker', 'podman', 'kubectl', 'helm', 'minikube', 'kind',
    
    # Cloud tools
    'aws', 'gcloud', 'az', 'terraform', 'ansible', 'puppet', 'chef',
    
    # Archive managers
    'tar', 'gzip', 'zip', '7z', 'rar',
    
    # Network tools
    'curl', 'wget', 'openssl', 'ssh', 'rsync', 'netcat', 'telnet',
    
    # Database clients
    'mysql', 'psql', 'redis-cli', 'mongo', 'sqlite3',
    
    # Testing tools
    'pytest', 'unittest', 'jest', 'mocha', 'jasmine', 'karma', 'selenium',
    
    # CI/CD tools
    'jenkins', 'travis', 'circleci', 'gitlab-runner', 'github', 'drone', 'tekton', 'argocd',
    
    # Other development tools
    'jq', 'yq', 'xmllint', 'pandoc', 'graphviz', 'plantuml',
}


def is_tool_available_on_platform(tool: str, platform_name: str) -> bool:
    """
    Check if a tool is available on a specific platform.
    
    Args:
        tool: Name of the tool to check
        platform_name: Platform to check availability for
        
    Returns:
        bool: True if tool is available on platform, False otherwise
    """
    # Empty platform or unknown platform - default to available
    if not platform_name:
        return True
    
    # Check if tool is in platform exclusions
    exclusions = PLATFORM_EXCLUSIONS.get(platform_name, set())
    if tool in exclusions:
        return False
    
    # Cross-platform tools are available everywhere
    if tool in CROSS_PLATFORM_TOOLS:
        return True
    
    # Default to available (for tools not explicitly excluded)
    return True


def get_relevant_categories(platform_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Get categories filtered for the specified platform.
    
    Args:
        platform_name: Platform to filter for (uses current platform if None)
        
    Returns:
        dict: Filtered taxonomy with only platform-relevant tools
    """
    if platform_name is None:
        platform_name = get_current_platform()
    
    # Deep copy the taxonomy to avoid modifying the original
    filtered_taxonomy = copy.deepcopy(PRACTICAL_TAXONOMY)
    
    # Filter each category
    for category_name, category_info in filtered_taxonomy.items():
        if 'tools' in category_info:
            # Filter direct tools
            filtered_tools = {}
            for tool_name, tool_fields in category_info['tools'].items():
                if is_tool_available_on_platform(tool_name, platform_name):
                    filtered_tools[tool_name] = tool_fields
            category_info['tools'] = filtered_tools
        
        elif 'categories' in category_info:
            # Handle nested categories (like package_managers)
            if category_name == 'package_managers':
                # Special handling for package managers
                filtered_subcategories = {}
                
                # System package managers
                if 'system' in category_info['categories']:
                    system_cat = category_info['categories']['system']
                    filtered_system_tools = {}
                    for tool_name, tool_fields in system_cat['tools'].items():
                        if is_tool_available_on_platform(tool_name, platform_name):
                            filtered_system_tools[tool_name] = tool_fields
                    
                    if filtered_system_tools:  # Only include if there are tools
                        filtered_subcategories['system'] = {
                            'description': system_cat['description'],
                            'tools': filtered_system_tools
                        }
                
                # Language package managers - include all since they're cross-platform
                if 'language' in category_info['categories']:
                    language_cat = category_info['categories']['language']
                    # Language category has a different structure (languages as keys)
                    # Just include it as-is since language package managers are cross-platform
                    filtered_subcategories['language'] = language_cat
                
                category_info['categories'] = filtered_subcategories
    
    return filtered_taxonomy


def get_tool_fields(category: str, tool: str) -> List[str]:
    """
    Get the fields available for a specific tool in a category.
    
    Args:
        category: Category name
        tool: Tool name
        
    Returns:
        list: List of field names for the tool, or empty list if not found
    """
    if category not in PRACTICAL_TAXONOMY:
        return []
    
    category_info = PRACTICAL_TAXONOMY[category]
    
    # Check direct tools
    if 'tools' in category_info and tool in category_info['tools']:
        return category_info['tools'][tool]
    
    # Handle nested categories (search through subcategories)
    if 'categories' in category_info:
        for subcategory_name, subcategory_info in category_info['categories'].items():
            if 'tools' in subcategory_info and tool in subcategory_info['tools']:
                return subcategory_info['tools'][tool]
            
            # Special handling for language package managers
            # They are stored as lists under language names, not in a tools dict
            if subcategory_name == 'language' and isinstance(subcategory_info, dict):
                for lang, pm_list in subcategory_info.items():
                    if lang != 'description' and isinstance(pm_list, list) and tool in pm_list:
                        # Return standard fields for language package managers
                        return ['version', 'list', 'install', 'uninstall']
    
    return []


# Define the practical taxonomy
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
    
    'ci_cd_tools': {
        'description': 'Continuous Integration and Deployment tools',
        'tools': {
            'jenkins': ['version', 'url', 'jobs'],
            'travis': ['version', 'endpoint'],
            'circleci': ['cli_version', 'host'],
            'gitlab-runner': ['version', 'executor'],
            'github': ['cli_version'],
            'buildkite': ['version', 'endpoint'],
            'drone': ['cli_version', 'server_version'],
            'tekton': ['cli_version', 'pipelines'],
            'argocd': ['cli_version', 'server_version'],
            'flux': ['version'],
            'spinnaker': ['version', 'gate_endpoint'],
        }
    },
    
    'testing_tools': {
        'description': 'Testing frameworks and test runners',
        'tools': {
            'pytest': ['version', 'plugins'],
            'unittest': ['version'],
            'nose': ['version', 'plugins'],
            'tox': ['version', 'envlist'],
            'nox': ['version'],
            'jest': ['version', 'projects'],
            'mocha': ['version', 'reporters'],
            'jasmine': ['version'],
            'karma': ['version', 'browsers'],
            'protractor': ['version', 'selenium_version'],
            'cypress': ['version', 'browser_versions'],
            'selenium': ['version', 'drivers'],
            'playwright': ['version', 'browsers'],
            'puppeteer': ['version', 'chromium_version'],
            'testcafe': ['version'],
            'junit': ['version'],
            'testng': ['version'],
            'rspec': ['version'],
            'minitest': ['version'],
            'cucumber': ['version'],
            'behave': ['version'],
            'robot': ['version', 'python_version'],
        }
    },
    
    'database_tools': {
        'description': 'Database clients and management tools',
        'tools': {
            'mysql': ['client_version', 'server_version', 'socket'],
            'psql': ['client_version', 'server_version', 'database'],
            'sqlite3': ['version', 'compile_options'],
            'redis-cli': ['version', 'server_version'],
            'mongo': ['version', 'server_version', 'storage_engine'],
            'cqlsh': ['version', 'cassandra_version'],
            'influx': ['version', 'server_version'],
            'cockroach': ['version'],
            'mssql': ['tools_version', 'server_version'],
        }
    },
    
    'monitoring_tools': {
        'description': 'System and application monitoring tools',
        'tools': {
            'htop': ['features'],
            'top': ['version'],
            'btop': ['version'],
            'glances': ['version', 'exports'],
            'iotop': ['features'],
            'nethogs': ['features'],
            'prometheus': ['version', 'storage_path'],
            'grafana': ['version', 'database'],
            'nagios': ['version', 'config_dir'],
            'zabbix': ['version', 'database_type'],
            'datadog': ['version', 'integrations'],
            'newrelic': ['version', 'apps'],
        }
    },
    
    'network_tools': {
        'description': 'Network connectivity and debugging tools',
        'tools': {
            'curl': ['version', 'protocols', 'features'],
            'wget': ['version', 'protocols', 'features'],
            'netcat': ['version', 'features'],
            'telnet': ['version'],
            'ssh': ['version', 'supported_ciphers'],
            'openssl': ['version', 'library_version', 'engines'],
            'nmap': ['version', 'scripts'],
            'tcpdump': ['version', 'libpcap_version'],
            'wireshark': ['version', 'plugins'],
            'iperf': ['version'],
            'dig': ['version'],
            'nslookup': ['version'],
            'traceroute': ['version'],
            'mtr': ['version', 'features'],
            'socat': ['version', 'features'],
            'rsync': ['version', 'capabilities'],
        }
    },
    
    'security_tools': {
        'description': 'Security scanning and analysis tools',
        'tools': {
            'openssl': ['version', 'library_version', 'fips_mode'],
            'gpg': ['version', 'home'],
            'ssh-keygen': ['version', 'supported_types'],
            'lynis': ['version', 'tests'],
            'tripwire': ['version', 'policy'],
            'aide': ['version', 'database'],
            'rkhunter': ['version', 'database_version'],
            'chkrootkit': ['version'],
            'clamav': ['version', 'database_version'],
            'fail2ban': ['version', 'jails'],
            'ossec': ['version', 'rules'],
            'snort': ['version', 'rules_version'],
            'suricata': ['version', 'rules_version'],
        }
    },
    
    'text_processing': {
        'description': 'Text manipulation and processing utilities',
        'tools': {
            'awk': ['version', 'variant'],
            'sed': ['version', 'variant'],
            'grep': ['version', 'pcre_support'],
            'ripgrep': ['version', 'features'],
            'ag': ['version', 'features'],
            'jq': ['version'],
            'yq': ['version', 'backend'],
            'xmllint': ['version', 'catalog'],
            'xsltproc': ['version', 'extensions'],
            'pandoc': ['version', 'input_formats', 'output_formats'],
        }
    },
    
    'documentation_tools': {
        'description': 'Documentation generation and processing tools',
        'tools': {
            'sphinx': ['version', 'extensions'],
            'mkdocs': ['version', 'themes'],
            'doxygen': ['version'],
            'asciidoc': ['version'],
            'jekyll': ['version', 'plugins'],
            'hugo': ['version', 'extended'],
            'gitbook': ['version'],
            'slate': ['version'],
            'swagger': ['version'],
            'redoc': ['version'],
            'graphviz': ['version', 'layout_engines'],
            'plantuml': ['version', 'java_version'],
            'mermaid': ['version'],
        }
    },
    
    'ide_editors': {
        'description': 'Integrated Development Environments and text editors',
        'tools': {
            'vim': ['version', 'features', 'runtime'],
            'nvim': ['version', 'features', 'runtime'],
            'emacs': ['version', 'features'],
            'nano': ['version'],
            'code': ['version', 'extensions'],
            'atom': ['version', 'packages'],
            'sublime': ['version', 'packages'],
            'intellij': ['version', 'plugins'],
            'eclipse': ['version', 'plugins'],
            'netbeans': ['version', 'plugins'],
            'xcode': ['version', 'sdks'],
            'android-studio': ['version', 'sdk_version'],
        }
    },
    
    'archive_managers': {
        'description': 'File compression and archive management tools',
        'tools': {
            'tar': ['version', 'formats'],
            'gzip': ['version'],
            'bzip2': ['version'],
            'xz': ['version', 'check_types'],
            'zip': ['version'],
            'unzip': ['info'],
            '7z': ['version', 'formats'],
            'rar': ['version'],
            'p7zip': ['version', 'formats'],
            'lz4': ['version'],
            'zstd': ['version', 'strategies'],
        }
    },
    
    'system_tools': {
        'description': 'System administration and management utilities',
        'tools': {
            'systemctl': ['version', 'state'],
            'systemd': ['version', 'features'],
            'service': ['version'],
            'cron': ['version', 'jobs'],
            'at': ['version', 'queue'],
            'ps': ['version', 'format_options'],
            'kill': ['version'],
            'df': ['version', 'filesystems'],
            'du': ['version'],
            'mount': ['version', 'filesystems'],
            'fdisk': ['version'],
            'parted': ['version'],
            'lsof': ['version'],
            'strace': ['version', 'syscalls'],
            'ltrace': ['version'],
            'gdb': ['version', 'python_support'],
            'lldb': ['version', 'python_support'],
            'valgrind': ['version', 'tools'],
            'perf': ['version', 'events'],
        }
    },
    
    'hardware_info': {
        'description': 'Hardware information and diagnostics tools',
        'tools': {
            'lscpu': ['version'],
            'lspci': ['version', 'database'],
            'lsusb': ['version', 'database'],
            'lshw': ['version'],
            'dmidecode': ['version'],
            'smartctl': ['version'],
            'hdparm': ['version'],
            'sensors': ['version', 'chips'],
            'nvidia-smi': ['version', 'driver_version'],
            'amdgpu-info': ['version'],
            'intel_gpu_top': ['version'],
        }
    },
}


# Platform-specific tools mapping
PLATFORM_TOOLS = {
    'macos': {
        'package_managers': ['brew', 'macports'],
        'compilers': ['clang', 'clang++', 'gcc', 'g++', 'swiftc'],
        'archive_managers': ['tar', 'gzip', 'bzip2', 'zip', 'unzip'],
        'system_tools': ['launchctl', 'dscl', 'diskutil', 'system_profiler'],
    },
    'linux': {
        'package_managers': ['apt', 'apt-get', 'yum', 'dnf', 'zypper', 'pacman', 'snap', 'flatpak'],
        'compilers': ['gcc', 'g++', 'clang', 'clang++'],
        'archive_managers': ['tar', 'gzip', 'bzip2', 'xz', 'zip', 'unzip'],
        'system_tools': ['systemctl', 'systemd', 'service', 'cron', 'at'],
    },
    'windows': {
        'package_managers': ['choco', 'scoop', 'winget'],
        'compilers': ['msvc', 'gcc', 'g++', 'clang', 'clang++'],
        'archive_managers': ['7z', 'zip', 'rar'],
        'system_tools': ['wsl', 'powershell', 'cmd'],
    },
}