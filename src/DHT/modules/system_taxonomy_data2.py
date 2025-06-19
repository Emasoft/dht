#!/usr/bin/env python3
"""
system_taxonomy_data2.py - Additional taxonomy data structures (part 2)
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Extracted from system_taxonomy.py to reduce file size
# - Contains additional PRACTICAL_TAXONOMY categories
#

from __future__ import annotations

# Additional taxonomy categories
PRACTICAL_TAXONOMY_PART2 = {
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

# Export public API
__all__ = ["PRACTICAL_TAXONOMY_PART2"]
