#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cli_commands_build_tools.py - Build tools and compiler CLI commands

This module contains CLI command definitions for build tools and compilers.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Extracted from cli_commands_registry.py to reduce file size
# - Contains build tools (make, cmake, ninja, bazel)
# - Contains compilers (gcc, clang, rustc, javac, msvc)
#

from typing import Dict, Any


BUILD_TOOLS_COMMANDS: Dict[str, Dict[str, Any]] = {
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
}