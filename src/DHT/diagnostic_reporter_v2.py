#!/usr/bin/env python3
from __future__ import annotations

"""
Diagnostic Reporter V2 module.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

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
# - Refactored into smaller modules to comply with 10KB file size limit
# - Delegates to specialized collector and parser modules
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

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Import our DHT modules
from DHT.modules import cli_commands_registry, system_taxonomy

# Import our refactored modules
from .diagnostic_system_info import collect_basic_system_info, collect_psutil_info
from .diagnostic_tool_collector import collect_all_tools

# Try to import optional dependencies
try:
    import yaml

    HAS_YAML = True
except ImportError:
    HAS_YAML = False
    print("Warning: PyYAML not available. JSON output only.", file=sys.stderr)


# --------------------------------------------------------------------------- #
# Main Reporter                                                               #
# --------------------------------------------------------------------------- #


def build_system_report(
    categories: list[str] | None = None, tools: list[str] | None = None, include_system_info: bool = True
) -> dict[str, Any]:
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


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="DHT Diagnostic Reporter V2 - Comprehensive system information collection",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Full system report
  %(prog)s

  # Only show build tools
  %(prog)s --categories build_tools

  # Only show specific tools
  %(prog)s --tools git docker python

  # List available categories
  %(prog)s --list-categories

  # List all available tools
  %(prog)s --list-tools

  # Save as YAML
  %(prog)s --output system-report.yaml

  # Save as JSON
  %(prog)s --format json --output system-report.json
        """,
    )

    parser.add_argument(
        "--categories",
        nargs="+",
        help="Tool categories to include (e.g., build_tools version_control)",
    )

    parser.add_argument(
        "--tools",
        nargs="+",
        help="Specific tools to check (e.g., git docker python)",
    )

    parser.add_argument(
        "--no-system-info",
        action="store_true",
        help="Exclude basic system information",
    )

    parser.add_argument(
        "--format",
        choices=["json", "yaml"],
        default="yaml" if HAS_YAML else "json",
        help="Output format (default: yaml if available, else json)",
    )

    parser.add_argument(
        "--output",
        "-o",
        help="Output file (default: stdout)",
    )

    parser.add_argument(
        "--list-categories",
        action="store_true",
        help="List available tool categories",
    )

    parser.add_argument(
        "--list-tools",
        action="store_true",
        help="List all available tools",
    )

    return parser.parse_args(argv)


def list_categories() -> None:
    """List all available tool categories."""
    print("Available tool categories:")
    print()

    # Get all categories from taxonomy
    categories = system_taxonomy.get_all_tool_categories()

    # Group by top-level category
    grouped: dict[str, list[str]] = {}
    for cat in sorted(categories):
        parts = cat.split(".")
        top_level = parts[0]
        if top_level not in grouped:
            grouped[top_level] = []
        grouped[top_level].append(cat)

    # Display grouped categories
    for top_level, cats in sorted(grouped.items()):
        print(f"  {top_level}:")
        for cat in cats:
            if cat != top_level:
                print(f"    - {cat}")
            else:
                print(f"    - {cat} (all)")
        print()


def list_tools() -> None:
    """List all available tools."""
    print("Available tools:")
    print()

    # Get all commands
    all_commands = cli_commands_registry.get_all_commands()

    # Group by category
    by_category: dict[str, list[str]] = {}
    for tool_name, spec in sorted(all_commands.items()):
        category = spec.get("category", "uncategorized")
        if category not in by_category:
            by_category[category] = []
        by_category[category].append(tool_name)

    # Display by category
    for category in sorted(by_category.keys()):
        print(f"  {category}:")
        for tool in sorted(by_category[category]):
            print(f"    - {tool}")
        print()


def main(argv: list[str] | None = None) -> None:
    """Main entry point."""
    args = parse_args(argv)

    # Handle list commands
    if args.list_categories:
        list_categories()
        return

    if args.list_tools:
        list_tools()
        return

    # Build the report
    report = build_system_report(
        categories=args.categories,
        tools=args.tools,
        include_system_info=not args.no_system_info,
    )

    # Add metadata
    report["_metadata"] = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "generator": "dht-diagnostic-reporter-v2",
        "filters": {
            "categories": args.categories or "all",
            "tools": args.tools or "all",
            "include_system_info": not args.no_system_info,
        },
    }

    # Format output
    if args.format == "yaml" and HAS_YAML:
        output = yaml.dump(report, default_flow_style=False, sort_keys=False)
    else:
        output = json.dumps(report, indent=2, sort_keys=False)

    # Write output
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(output)
        print(f"Report saved to: {output_path}")
    else:
        print(output)


if __name__ == "__main__":
    main()
