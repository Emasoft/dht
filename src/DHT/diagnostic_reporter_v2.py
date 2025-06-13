#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Initial implementation of diagnostic_reporter_v2 module
# - Integrates with system_taxonomy and cli_commands_registry modules
# - Implements platform-aware command collection
# - Implements atomic information tree structure with predictable paths
# - Implements smart output parsing based on format hints
# - Implements filtering by categories and specific tools
# - Supports YAML and JSON output formats
# - Handles command failures gracefully
# - Preserves unparsed output as additional_info fields
# - Uses ThreadPoolExecutor for parallel command execution
# 

"""
Diagnostic Reporter V2 for DHT.

This module provides comprehensive system information collection using the
system taxonomy and CLI commands registry. It creates an atomic information
tree where every piece of data has a clear, predictable path.

Key features:
- Platform-aware command execution
- Smart output parsing based on format hints
- Atomic information tree structure
- Parallel command execution
- Graceful error handling
- Support for filtering by categories and tools
- YAML and JSON output formats
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import re
import socket
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from itertools import count
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Set

# Import our DHT modules
from DHT.modules import system_taxonomy
from DHT.modules import cli_commands_registry

# Try to import optional dependencies
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
    print("Warning: psutil not available. Some system info will be limited.", file=sys.stderr)

try:
    import distro
    HAS_DISTRO = True
except ImportError:
    HAS_DISTRO = False
    print("Warning: distro not available. Linux distribution info will be limited.", file=sys.stderr)

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False
    print("Warning: PyYAML not available. JSON output only.", file=sys.stderr)


# --------------------------------------------------------------------------- #
# Helpers                                                                     #
# --------------------------------------------------------------------------- #

def run_command(cmd: str, timeout: int = 30) -> Tuple[str, Optional[str]]:
    """
    Execute a command and return (stdout, error).
    
    Args:
        cmd: Command to execute
        timeout: Timeout in seconds
        
    Returns:
        tuple: (stdout, error) where error is None on success
    """
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True,
            text=True,
            timeout=timeout,
            env=os.environ.copy()
        )
        
        # Some commands output to stderr even on success
        if result.returncode != 0 and result.stderr.strip():
            return result.stdout.strip(), result.stderr.strip()
        
        return result.stdout.strip(), None
        
    except subprocess.TimeoutExpired:
        return "", f"Command timed out after {timeout} seconds"
    except Exception as exc:
        return "", str(exc)


def snake_case(s: str) -> str:
    """Convert string to snake_case."""
    # Replace common separators with underscore
    s = re.sub(r'[\s\-\.]+', '_', s.strip())
    # Remove special characters
    s = re.sub(r'[^\w]', '_', s)
    # Convert camelCase to snake_case
    s = re.sub(r'([a-z])([A-Z])', r'\1_\2', s)
    # Lowercase and remove duplicate underscores
    s = s.lower()
    s = re.sub(r'_+', '_', s)
    return s.strip('_')


def coerce_value(value: str) -> Any:
    """Try to convert string to appropriate type."""
    value = value.strip()
    
    # Boolean
    if value.lower() in ('true', 'false'):
        return value.lower() == 'true'
    
    # None/null
    if value.lower() in ('none', 'null', ''):
        return None
    
    # Number
    try:
        if '.' in value:
            return float(value)
        return int(value)
    except ValueError:
        pass
    
    # Keep as string
    return value


def extract_version(text: str) -> Optional[str]:
    """Extract version number from text."""
    # Common version patterns
    patterns = [
        r'(\d+\.\d+\.\d+(?:\.\d+)?)',  # 1.2.3 or 1.2.3.4
        r'version\s+(\d+\.\d+(?:\.\d+)?)',  # version 1.2 or version 1.2.3
        r'v(\d+\.\d+(?:\.\d+)?)',  # v1.2 or v1.2.3
        r'(\d+\.\d+)',  # 1.2
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
    
    return None


def parse_json_output(text: str) -> Tuple[Dict[str, Any], List[str]]:
    """Parse JSON output."""
    try:
        data = json.loads(text)
        return data if isinstance(data, dict) else {"data": data}, []
    except json.JSONDecodeError:
        return {}, [text]


def parse_yaml_output(text: str) -> Tuple[Dict[str, Any], List[str]]:
    """Parse YAML output."""
    if not HAS_YAML:
        return {}, [text]
    
    try:
        data = yaml.safe_load(text)
        return data if isinstance(data, dict) else {"data": data}, []
    except yaml.YAMLError:
        return {}, [text]


def parse_key_value_output(text: str) -> Tuple[Dict[str, Any], List[str]]:
    """Parse key-value pair output (key: value or key=value)."""
    parsed = {}
    unparsed = []
    
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        
        # Try key: value format
        if ':' in line:
            parts = line.split(':', 1)
            if len(parts) == 2:
                key = snake_case(parts[0])
                value = coerce_value(parts[1])
                parsed[key] = value
                continue
        
        # Try key=value format
        if '=' in line:
            parts = line.split('=', 1)
            if len(parts) == 2:
                key = snake_case(parts[0])
                value = coerce_value(parts[1])
                parsed[key] = value
                continue
        
        # Couldn't parse this line
        unparsed.append(line)
    
    return parsed, unparsed


def parse_auto_output(text: str) -> Tuple[Dict[str, Any], List[str]]:
    """Automatically detect and parse output format."""
    text = text.strip()
    if not text:
        return {}, []
    
    # Try JSON first
    if text.startswith(('{', '[')):
        parsed, unparsed = parse_json_output(text)
        if parsed:
            return parsed, unparsed
    
    # Try YAML
    if HAS_YAML and (':' in text or '-' in text.split('\n')[0]):
        parsed, unparsed = parse_yaml_output(text)
        if parsed:
            return parsed, unparsed
    
    # Try key-value pairs
    parsed, unparsed = parse_key_value_output(text)
    
    # If we got some parsed data, return it
    if parsed:
        return parsed, unparsed
    
    # Last resort: try to extract version
    version = extract_version(text)
    if version:
        return {"version": version}, [line for line in text.splitlines() if version not in line]
    
    # Nothing parsed
    return {}, text.splitlines()


def parse_command_output(text: str, format_hint: str = "auto") -> Tuple[Dict[str, Any], List[str]]:
    """
    Parse command output based on format hint.
    
    Args:
        text: Command output text
        format_hint: Format hint (json, yaml, auto, etc.)
        
    Returns:
        tuple: (parsed_dict, unparsed_lines)
    """
    if format_hint == "json":
        return parse_json_output(text)
    elif format_hint == "yaml":
        return parse_yaml_output(text)
    else:
        return parse_auto_output(text)


def add_unparsed_lines(data: Dict[str, Any], lines: List[str]) -> Dict[str, Any]:
    """Add unparsed lines as additional_info fields."""
    if not lines:
        return data
    
    for i, line in enumerate(lines, 1):
        data[f"additional_info_{i:04d}"] = line
    
    return data


# --------------------------------------------------------------------------- #
# System Information Collectors                                               #
# --------------------------------------------------------------------------- #

def collect_basic_system_info() -> Dict[str, Any]:
    """Collect basic system information."""
    uname = platform.uname()
    
    info = {
        "platform": system_taxonomy.get_current_platform(),
        "system": uname.system,
        "node": uname.node,
        "release": uname.release,
        "version": uname.version,
        "machine": uname.machine,
        "processor": uname.processor or "unknown",
        "python_version": platform.python_version(),
        "timestamp": datetime.now().isoformat(),
    }
    
    # Add distro info for Linux
    if HAS_DISTRO and info["platform"] == "linux":
        info["distribution"] = {
            "name": distro.name(),
            "version": distro.version(),
            "codename": distro.codename(),
            "like": distro.like(),
        }
    
    return info


def collect_psutil_info() -> Dict[str, Any]:
    """Collect system information using psutil if available."""
    if not HAS_PSUTIL:
        return {}
    
    info = {}
    
    # CPU info
    try:
        info["cpu"] = {
            "physical_cores": psutil.cpu_count(logical=False),
            "logical_cores": psutil.cpu_count(logical=True),
            "current_freq_mhz": psutil.cpu_freq().current if psutil.cpu_freq() else None,
            "max_freq_mhz": psutil.cpu_freq().max if psutil.cpu_freq() else None,
        }
    except Exception:
        pass
    
    # Memory info
    try:
        vm = psutil.virtual_memory()
        info["memory"] = {
            "total_mb": vm.total // (1024 * 1024),
            "available_mb": vm.available // (1024 * 1024),
            "used_mb": vm.used // (1024 * 1024),
            "percent": vm.percent,
        }
    except Exception:
        pass
    
    # Disk info
    try:
        disk = psutil.disk_usage('/')
        info["disk"] = {
            "total_gb": disk.total // (1024 * 1024 * 1024),
            "used_gb": disk.used // (1024 * 1024 * 1024),
            "free_gb": disk.free // (1024 * 1024 * 1024),
            "percent": disk.percent,
        }
    except Exception:
        pass
    
    # Network info
    try:
        info["network"] = {
            "hostname": socket.gethostname(),
            "fqdn": socket.getfqdn(),
        }
    except Exception:
        pass
    
    return info


# --------------------------------------------------------------------------- #
# Tool Information Collector                                                  #
# --------------------------------------------------------------------------- #

def check_tool_installed(tool_name: str) -> bool:
    """Check if a tool is installed by trying to run it with --version."""
    # For Python-based tools, check if they're importable modules first
    if tool_name in ('pip', 'pip3'):
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pip', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            pass
    
    # Try common version flags
    version_flags = ['--version', '-version', 'version', '--help', '-h']
    
    for flag in version_flags:
        try:
            result = subprocess.run(
                [tool_name, flag],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return True
        except Exception:
            continue
    
    return False


def collect_tool_info(tool_name: str, tool_spec: Dict[str, Any]) -> Dict[str, Any]:
    """
    Collect information for a single tool.
    
    Args:
        tool_name: Name of the tool
        tool_spec: Tool specification from CLI commands registry
        
    Returns:
        dict: Tool information including all command outputs
    """
    tool_info = {
        "is_installed": False,
        "category": tool_spec.get("category", "unknown"),
    }
    
    # Check if tool is installed
    if not check_tool_installed(tool_name):
        return tool_info
    
    tool_info["is_installed"] = True
    
    # Run all commands for this tool
    commands = tool_spec.get("commands", {})
    format_hint = tool_spec.get("format", "auto")
    
    for cmd_name, cmd in commands.items():
        stdout, error = run_command(cmd)
        
        if error:
            tool_info[cmd_name] = {"error": error}
        else:
            parsed, unparsed = parse_command_output(stdout, format_hint)
            
            # Store parsed data directly under command name
            if parsed:
                tool_info[cmd_name] = parsed
            
            # Add unparsed lines
            if unparsed:
                tool_info[cmd_name] = add_unparsed_lines(
                    tool_info.get(cmd_name, {}),
                    unparsed
                )
    
    return tool_info


def insert_into_tree(tree: Dict[str, Any], path: str, value: Any) -> None:
    """
    Insert a value into the tree at the specified path.
    
    Args:
        tree: The tree to insert into
        path: Dot-separated path (e.g., "tools.build_tools.cmake")
        value: Value to insert
    """
    parts = path.split('.')
    current = tree
    
    for part in parts[:-1]:
        if part not in current:
            current[part] = {}
        current = current[part]
    
    current[parts[-1]] = value


def collect_all_tools(
    categories: Optional[List[str]] = None,
    tools: Optional[List[str]] = None,
    platform_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Collect information for all tools or filtered subset.
    
    Args:
        categories: List of categories to include (None for all)
        tools: List of specific tools to include (None for all)
        platform_name: Platform to filter for (None for current)
        
    Returns:
        dict: Nested dictionary with tool information
    """
    if platform_name is None:
        platform_name = system_taxonomy.get_current_platform()
    
    # Get platform-specific commands
    commands = cli_commands_registry.get_platform_specific_commands(platform_name)
    
    # Filter by categories if specified
    if categories:
        filtered_commands = {}
        for cat in categories:
            cat_commands = cli_commands_registry.get_commands_by_category(cat)
            filtered_commands.update(cat_commands)
        commands = {k: v for k, v in commands.items() if k in filtered_commands}
    
    # Filter by specific tools if specified
    if tools:
        commands = {k: v for k, v in commands.items() if k in tools}
    
    # Collect tool information in parallel
    tool_results = {}
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        # Submit all tool collection tasks
        future_to_tool = {
            executor.submit(collect_tool_info, tool_name, tool_spec): (tool_name, tool_spec)
            for tool_name, tool_spec in commands.items()
        }
        
        # Collect results as they complete
        for future in as_completed(future_to_tool):
            tool_name, tool_spec = future_to_tool[future]
            try:
                tool_info = future.result()
                tool_results[tool_name] = tool_info
            except Exception as exc:
                tool_results[tool_name] = {
                    "is_installed": False,
                    "error": str(exc),
                    "category": tool_spec.get("category", "unknown"),
                }
    
    # Build the tree structure
    tree = {}
    
    for tool_name, tool_info in tool_results.items():
        category = tool_info.get("category", "unknown")
        
        # Create the path for this tool
        # Convert category paths like "package_managers.language.python" to proper tree structure
        if category.startswith("package_managers.language."):
            # Special handling for language package managers
            parts = category.split(".")
            lang = parts[2] if len(parts) > 2 else "unknown"
            path = f"tools.package_managers.language.{lang}.{tool_name}"
        elif category.startswith("package_managers.system."):
            # Special handling for system package managers
            parts = category.split(".")
            sys_type = parts[2] if len(parts) > 2 else "unknown"
            path = f"tools.package_managers.system.{tool_name}"
        else:
            # Standard category path
            path = f"tools.{category}.{tool_name}"
        
        # Remove category from tool info since it's encoded in the path
        tool_info_clean = {k: v for k, v in tool_info.items() if k != "category"}
        
        insert_into_tree(tree, path, tool_info_clean)
    
    return tree


# --------------------------------------------------------------------------- #
# Main Reporter                                                               #
# --------------------------------------------------------------------------- #

def build_system_report(
    categories: Optional[List[str]] = None,
    tools: Optional[List[str]] = None,
    include_system_info: bool = True
) -> Dict[str, Any]:
    """
    Build a comprehensive system report.
    
    Args:
        categories: List of categories to include (None for all)
        tools: List of specific tools to include (None for all)
        include_system_info: Whether to include basic system information
        
    Returns:
        dict: Complete system report
    """
    report = {}
    
    # Add basic system information
    if include_system_info:
        report["system"] = collect_basic_system_info()
        
        # Add psutil info if available
        psutil_info = collect_psutil_info()
        if psutil_info:
            report["system"].update(psutil_info)
    
    # Collect tool information
    tool_tree = collect_all_tools(categories=categories, tools=tools)
    report.update(tool_tree)
    
    return report


# --------------------------------------------------------------------------- #
# CLI Interface                                                               #
# --------------------------------------------------------------------------- #

def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="DHT Diagnostic Reporter v2 - Comprehensive system information collector",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Collect all information
  %(prog)s
  
  # Output to specific file
  %(prog)s --output system_info.yaml
  
  # Filter by categories
  %(prog)s --categories build_tools compilers
  
  # Filter by specific tools
  %(prog)s --tools cmake gcc python3
  
  # JSON output
  %(prog)s --format json --output system_info.json
  
  # Exclude system info
  %(prog)s --no-system-info
"""
    )
    
    parser.add_argument(
        "--output", "-o",
        default="system_diagnostic.yaml",
        help="Output file path (default: system_diagnostic.yaml)"
    )
    
    parser.add_argument(
        "--format", "-f",
        choices=["yaml", "json"],
        default="yaml",
        help="Output format (default: yaml)"
    )
    
    parser.add_argument(
        "--categories", "-c",
        nargs="+",
        help="Filter by categories (e.g., build_tools compilers)"
    )
    
    parser.add_argument(
        "--tools", "-t",
        nargs="+",
        help="Filter by specific tools (e.g., cmake gcc python3)"
    )
    
    parser.add_argument(
        "--list-categories",
        action="store_true",
        help="List available categories and exit"
    )
    
    parser.add_argument(
        "--list-tools",
        action="store_true",
        help="List available tools and exit"
    )
    
    parser.add_argument(
        "--no-system-info",
        action="store_true",
        help="Exclude basic system information"
    )
    
    parser.add_argument(
        "--platform",
        choices=["macos", "linux", "windows"],
        help="Override platform detection"
    )
    
    return parser.parse_args(argv)


def list_categories() -> None:
    """List all available categories."""
    categories = set()
    
    for tool_spec in cli_commands_registry.CLI_COMMANDS.values():
        category = tool_spec.get("category", "")
        if category:
            # Add main category
            main_cat = category.split(".")[0]
            categories.add(main_cat)
            
            # Add full category path
            categories.add(category)
    
    print("Available categories:")
    for cat in sorted(categories):
        print(f"  {cat}")


def list_tools() -> None:
    """List all available tools."""
    platform_name = system_taxonomy.get_current_platform()
    commands = cli_commands_registry.get_platform_specific_commands(platform_name)
    
    print(f"Available tools for {platform_name}:")
    
    # Group by category
    by_category = {}
    for tool_name, tool_spec in commands.items():
        category = tool_spec.get("category", "unknown")
        if category not in by_category:
            by_category[category] = []
        by_category[category].append(tool_name)
    
    # Print grouped tools
    for category in sorted(by_category.keys()):
        print(f"\n{category}:")
        for tool in sorted(by_category[category]):
            print(f"  {tool}")


def main(argv: Optional[List[str]] = None) -> None:
    """Main entry point."""
    args = parse_args(argv)
    
    # Handle list commands
    if args.list_categories:
        list_categories()
        return
    
    if args.list_tools:
        list_tools()
        return
    
    # Override platform if specified
    if args.platform:
        # Temporarily override the platform detection
        original_platform = system_taxonomy.get_current_platform
        system_taxonomy.get_current_platform = lambda: args.platform
    
    try:
        # Build the report
        print("Collecting system information...")
        report = build_system_report(
            categories=args.categories,
            tools=args.tools,
            include_system_info=not args.no_system_info
        )
        
        # Save the report
        output_path = Path(args.output)
        
        if args.format == "json":
            output_path.write_text(
                json.dumps(report, indent=2, sort_keys=False, default=str)
            )
        else:
            if not HAS_YAML:
                print("Warning: PyYAML not available, falling back to JSON format", file=sys.stderr)
                output_path = output_path.with_suffix('.json')
                output_path.write_text(
                    json.dumps(report, indent=2, sort_keys=False, default=str)
                )
            else:
                with open(output_path, 'w') as f:
                    yaml.dump(
                        report,
                        f,
                        default_flow_style=False,
                        sort_keys=False,
                        allow_unicode=True,
                        width=120
                    )
        
        print(f"System diagnostic written to {output_path}")
        
        # Print summary
        if "tools" in report:
            tool_count = sum(
                1 for cat_data in report["tools"].values()
                if isinstance(cat_data, dict)
                for tool_data in cat_data.values()
                if isinstance(tool_data, dict) and tool_data.get("is_installed", False)
            )
            print(f"Found {tool_count} installed tools")
    
    finally:
        # Restore original platform detection if overridden
        if args.platform:
            system_taxonomy.get_current_platform = original_platform


if __name__ == "__main__":
    main()