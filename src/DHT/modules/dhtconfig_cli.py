#!/usr/bin/env python3
from __future__ import annotations

"""
dhtconfig_cli.py - CLI interface for DHT configuration

This module provides the command-line interface for dhtconfig operations.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Extracted from dhtconfig.py to reduce file size
# - Contains CLI main() function and argument parsing
#


import argparse
import json
import sys
from pathlib import Path

from DHT.modules.dhtconfig import DHTConfig
from DHT.modules.dhtconfig_models import HAS_YAML

if HAS_YAML:
    import yaml


def main() -> None:
    """CLI interface for dhtconfig operations."""
    parser = argparse.ArgumentParser(description="DHT Configuration Generator and Manager")

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Generate command
    gen_parser = subparsers.add_parser("generate", help="Generate .dhtconfig from project")
    gen_parser.add_argument(
        "project_path", type=Path, nargs="?", default=Path.cwd(), help="Project path (default: current directory)"
    )
    gen_parser.add_argument("--format", choices=["yaml", "json"], default="yaml", help="Output format (default: yaml)")
    gen_parser.add_argument("--no-system-info", action="store_true", help="Skip system information collection")
    gen_parser.add_argument("--no-checksums", action="store_true", help="Skip checksum generation")

    # Validate command
    val_parser = subparsers.add_parser("validate", help="Validate .dhtconfig file")
    val_parser.add_argument(
        "config_path",
        type=Path,
        nargs="?",
        default=Path.cwd() / ".dhtconfig",
        help="Config file path (default: ./.dhtconfig)",
    )

    # Show command
    show_parser = subparsers.add_parser("show", help="Show merged configuration")
    show_parser.add_argument(
        "config_path",
        type=Path,
        nargs="?",
        default=Path.cwd() / ".dhtconfig",
        help="Config file path (default: ./.dhtconfig)",
    )
    show_parser.add_argument(
        "--platform", choices=["macos", "linux", "windows"], help="Platform to show (default: current)"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    dht_config = DHTConfig()

    if args.command == "generate":
        print(f"Generating .dhtconfig for {args.project_path}...")

        config = dht_config.generate_from_project(
            args.project_path, include_system_info=not args.no_system_info, include_checksums=not args.no_checksums
        )

        config_path = dht_config.save_config(config, args.project_path, format=args.format)

        print(f"Configuration saved to: {config_path}")

    elif args.command == "validate":
        try:
            config = dht_config.load_config(args.config_path)
            is_valid, errors = dht_config.validate_config(config)

            if is_valid:
                print("✓ Configuration is valid")
            else:
                print("✗ Configuration validation failed:")
                for error in errors:
                    print(f"  - {error}")
                sys.exit(1)

        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)

    elif args.command == "show":
        try:
            config = dht_config.load_config(args.config_path)
            merged = dht_config.merge_platform_config(config, args.platform)

            # Remove platform_overrides from display
            merged.pop("platform_overrides", None)

            if HAS_YAML:
                print(yaml.dump(merged, default_flow_style=False, sort_keys=False))
            else:
                print(json.dumps(merged, indent=2, sort_keys=False))

        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()
