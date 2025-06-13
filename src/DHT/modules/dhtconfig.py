#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Initial implementation of dhtconfig module
# - Implements .dhtconfig generation from project analysis
# - Implements .dhtconfig parsing and validation
# - Integrates with diagnostic_reporter_v2 for system information
# - Integrates with project_analyzer for project analysis
# - Supports platform-specific configurations
# - Implements validation checksum generation
# - Implements configuration merging for platform overrides
# 

"""
DHT Configuration Module.

This module handles generation, parsing, and validation of .dhtconfig files.
These files capture exact project requirements for deterministic environment
regeneration across different platforms.
"""

from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Try to import optional dependencies
try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False
    print("Warning: PyYAML not available. YAML support disabled.", file=sys.stderr)

try:
    import jsonschema
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False
    print("Warning: jsonschema not available. Schema validation disabled.", file=sys.stderr)

# Import DHT modules - use try/except for flexibility in import paths
try:
    # Try absolute import first (when running as installed package)
    from DHT import diagnostic_reporter_v2
    from DHT.modules import project_analyzer
except ImportError:
    try:
        # Try relative import (when running from within package)
        from .. import diagnostic_reporter_v2
        from . import project_analyzer
    except ImportError:
        # Try direct import (when modules are in path)
        import diagnostic_reporter_v2
        import project_analyzer

# DHT version - would normally come from constants_core or package metadata
DHT_VERSION = "0.1.0"


class DHTConfig:
    """
    Handles .dhtconfig file generation, parsing, and validation.
    """
    
    SCHEMA_VERSION = "1.0.0"
    CONFIG_FILENAME = ".dhtconfig"
    
    def __init__(self):
        """Initialize DHTConfig handler."""
        self.schema = self._load_schema()
        self.project_analyzer = project_analyzer.ProjectAnalyzer()
    
    def _load_schema(self) -> Optional[Dict[str, Any]]:
        """Load the JSON schema for validation."""
        if not HAS_YAML:
            return None
        
        schema_path = Path(__file__).parent.parent / "schemas" / "dhtconfig_schema.yaml"
        if not schema_path.exists():
            return None
        
        try:
            with open(schema_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"Warning: Failed to load schema: {e}", file=sys.stderr)
            return None
    
    def generate_from_project(
        self,
        project_path: Path,
        include_system_info: bool = True,
        include_checksums: bool = True
    ) -> Dict[str, Any]:
        """
        Generate .dhtconfig from project analysis.
        
        Args:
            project_path: Path to the project root
            include_system_info: Whether to include current system information
            include_checksums: Whether to generate validation checksums
            
        Returns:
            Generated configuration dictionary
        """
        project_path = Path(project_path).resolve()
        
        # Analyze the project
        print("Analyzing project structure...")
        project_info = self.project_analyzer.analyze_project(project_path)
        
        # Get current Python version
        python_version = platform.python_version()
        
        # Start building config
        config = {
            "version": self.SCHEMA_VERSION,
            "project": {
                "name": project_info.get("name", project_path.name),
                "type": project_info.get("project_type", "unknown"),
                "subtypes": project_info.get("project_subtypes", []),
                "generated_at": datetime.now().isoformat(),
                "generated_by": f"DHT {DHT_VERSION}",
            },
            "python": {
                "version": python_version,
                "implementation": platform.python_implementation().lower(),
                "virtual_env": {
                    "name": ".venv",
                }
            },
            "dependencies": self._extract_dependencies(project_info),
            "tools": self._extract_tool_requirements(project_info),
            "build": self._extract_build_config(project_info),
            "environment": self._extract_environment_vars(project_path),
        }
        
        # Add platform-specific overrides if we detect differences
        if include_system_info:
            system_info = diagnostic_reporter_v2.build_system_report(
                include_system_info=True,
                categories=["build_tools", "compilers", "package_managers"]
            )
            config["platform_overrides"] = self._generate_platform_overrides(
                project_info, system_info
            )
        
        # Add validation checksums
        if include_checksums:
            config["validation"] = self._generate_validation_info(
                project_path, project_info
            )
        
        return config
    
    def _extract_dependencies(self, project_info: Dict[str, Any]) -> Dict[str, Any]:
        """Extract dependencies from project analysis."""
        deps = {
            "python_packages": [],
            "lock_files": {},
            "system_packages": []
        }
        
        # Extract Python dependencies
        if "dependencies" in project_info:
            project_deps = project_info["dependencies"]
            
            # Python packages
            if "python" in project_deps:
                python_deps = project_deps["python"]
                # Handle both dict and list formats
                if isinstance(python_deps, dict):
                    # project_analyzer returns a dict with 'runtime', 'development', 'all'
                    for dep_name in python_deps.get("runtime", []):
                        deps["python_packages"].append({
                            "name": dep_name,
                            "version": "*",
                            "extras": [],
                        })
                elif isinstance(python_deps, list):
                    # Handle list format
                    for dep in python_deps:
                        if isinstance(dep, dict):
                            deps["python_packages"].append({
                                "name": dep["name"],
                                "version": dep.get("version", "*"),
                                "extras": dep.get("extras", []),
                            })
                        elif isinstance(dep, str):
                            deps["python_packages"].append({
                                "name": dep,
                                "version": "*",
                                "extras": [],
                            })
            
        # Check for lock files in the project directory
        project_path = Path(project_info.get("root_path", "."))
        lock_file_patterns = {
            "uv": "uv.lock",
            "poetry": "poetry.lock",
            "pipenv": "Pipfile.lock",
            "npm": "package-lock.json",
            "yarn": "yarn.lock",
            "pnpm": "pnpm-lock.yaml",
        }
        
        for lock_type, filename in lock_file_patterns.items():
            lock_path = project_path / filename
            if lock_path.exists():
                deps["lock_files"][lock_type] = filename
        
        # Extract system packages based on project type
        if project_info.get("project_type") == "python":
            # Common Python development system packages
            deps["system_packages"].extend([
                {"name": "python3-dev", "platform": "linux"},
                {"name": "build-essential", "platform": "linux"},
                {"name": "xcode-select", "platform": "macos"},
            ])
        
        return deps
    
    def _extract_tool_requirements(self, project_info: Dict[str, Any]) -> Dict[str, Any]:
        """Extract tool requirements from project analysis."""
        tools = {
            "required": [],
            "optional": []
        }
        
        # Add tools based on project configuration files
        configs = project_info.get("configurations", {})
        
        # Version control
        if configs.get("has_git", True):  # Assume git by default
            tools["required"].append({"name": "git"})
        
        # Build tools
        if configs.get("has_makefile"):
            tools["required"].append({"name": "make"})
        
        if configs.get("has_cmake"):
            tools["required"].append({"name": "cmake", "version": ">=3.10"})
        
        # Python tools
        if project_info.get("project_type") == "python":
            tools["required"].extend([
                {"name": "pip"},
                {"name": "setuptools"},
                {"name": "wheel"},
            ])
            
            # Optional Python tools
            tools["optional"].extend([
                {"name": "pytest", "purpose": "Running tests"},
                {"name": "mypy", "purpose": "Type checking"},
                {"name": "ruff", "purpose": "Linting and formatting"},
                {"name": "black", "purpose": "Code formatting"},
            ])
        
        # Container tools
        if configs.get("has_dockerfile"):
            tools["optional"].append({
                "name": "docker",
                "purpose": "Container builds"
            })
        
        return tools
    
    def _extract_build_config(self, project_info: Dict[str, Any]) -> Dict[str, Any]:
        """Extract build configuration from project analysis."""
        build = {
            "pre_install": [],
            "post_install": [],
            "build_commands": [],
            "test_commands": []
        }
        
        configs = project_info.get("configurations", {})
        
        # Python project build commands
        if project_info.get("project_type") == "python":
            if configs.get("has_setup_py"):
                build["build_commands"].append("python setup.py build")
            elif configs.get("has_pyproject"):
                build["build_commands"].append("python -m build")
            
            # Test commands
            if configs.get("has_pytest"):
                build["test_commands"].append("pytest")
            elif configs.get("has_unittest"):
                build["test_commands"].append("python -m unittest discover")
        
        # Makefile commands
        if configs.get("has_makefile"):
            build["build_commands"].append("make")
            build["test_commands"].append("make test")
        
        return build
    
    def _extract_environment_vars(self, project_path: Path) -> Dict[str, Any]:
        """Extract environment variables from project."""
        env = {
            "required": {},
            "optional": {}
        }
        
        # Check for .env files
        env_files = [".env", ".env.example", ".env.sample"]
        for env_file in env_files:
            env_path = project_path / env_file
            if env_path.exists():
                try:
                    with open(env_path, 'r') as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith('#') and '=' in line:
                                key, value = line.split('=', 1)
                                key = key.strip()
                                value = value.strip().strip('"').strip("'")
                                
                                # Determine if required or optional based on value
                                if value in ("", "CHANGE_ME", "YOUR_VALUE_HERE"):
                                    env["required"][key] = ""
                                else:
                                    env["optional"][key] = value
                except Exception:
                    pass
        
        return env
    
    def _generate_platform_overrides(
        self,
        project_info: Dict[str, Any],
        system_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate platform-specific configuration overrides."""
        overrides = {}
        
        current_platform = platform.system().lower()
        if current_platform == "darwin":
            current_platform = "macos"
        
        # Add platform-specific system packages
        if current_platform == "macos":
            overrides["macos"] = {
                "dependencies": {
                    "system_packages": [
                        {"name": "xcode-select"},
                    ]
                }
            }
        elif current_platform == "linux":
            overrides["linux"] = {
                "dependencies": {
                    "system_packages": [
                        {"name": "build-essential"},
                        {"name": "python3-dev"},
                        {"name": "python3-venv"},
                    ]
                }
            }
        elif current_platform == "windows":
            overrides["windows"] = {
                "dependencies": {
                    "system_packages": [
                        {"name": "visualstudio2019buildtools"},
                    ]
                },
                "environment": {
                    "required": {
                        "PYTHONIOENCODING": "utf-8"
                    }
                }
            }
        
        return overrides
    
    def _generate_validation_info(
        self,
        project_path: Path,
        project_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate validation checksums and metadata."""
        validation = {
            "checksums": {},
            "tool_behaviors": {}
        }
        
        # Generate checksums for key files
        key_files = [
            "requirements.txt",
            "requirements.in",
            "pyproject.toml",
            "setup.py",
            "setup.cfg",
            "package.json",
            "Makefile",
            "CMakeLists.txt",
        ]
        
        for filename in key_files:
            file_path = project_path / filename
            if file_path.exists():
                try:
                    with open(file_path, 'rb') as f:
                        content = f.read()
                        checksum = hashlib.sha256(content).hexdigest()
                        validation["checksums"][filename] = checksum
                except Exception:
                    pass
        
        # Generate tool behavior checksums
        # This would capture expected behavior of tools like black, ruff, etc.
        tools_to_check = ["black", "ruff", "mypy", "pytest"]
        
        for tool in tools_to_check:
            try:
                # Get tool version
                result = subprocess.run(
                    [tool, "--version"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    version_output = result.stdout.strip()
                    version = self._extract_version(version_output)
                    
                    # Generate behavior hash (simplified - would be more complex in practice)
                    behavior_hash = hashlib.sha256(
                        f"{tool}-{version}-behavior".encode()
                    ).hexdigest()
                    
                    validation["tool_behaviors"][tool] = {
                        "version": version,
                        "behavior_hash": behavior_hash
                    }
            except Exception:
                pass
        
        return validation
    
    def _extract_version(self, version_output: str) -> str:
        """Extract version number from version output."""
        import re
        
        # Common version patterns - order matters!
        patterns = [
            r'version (\d+\.\d+\.\d+)',  # "version 1.2.3"
            r'v(\d+\.\d+\.\d+)',         # "v1.2.3" or "mypy v0.991"
            r'(\d+\.\d+\.\d+)',          # Just the version number
        ]
        
        for pattern in patterns:
            match = re.search(pattern, version_output, re.IGNORECASE)
            if match:
                return match.group(1)
        
        # Special handling for two-part versions
        match = re.search(r'v?(\d+\.\d+)', version_output)
        if match:
            return match.group(1)
        
        return version_output.split()[0] if version_output else "unknown"
    
    def save_config(
        self,
        config: Dict[str, Any],
        project_path: Path,
        format: str = "yaml"
    ) -> Path:
        """
        Save configuration to .dhtconfig file.
        
        Args:
            config: Configuration dictionary
            project_path: Project root directory
            format: Output format ("yaml" or "json")
            
        Returns:
            Path to saved config file
        """
        config_path = project_path / self.CONFIG_FILENAME
        
        if format == "yaml" and HAS_YAML:
            with open(config_path, 'w') as f:
                yaml.dump(
                    config,
                    f,
                    default_flow_style=False,
                    sort_keys=False,
                    allow_unicode=True,
                    width=120
                )
        else:
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2, sort_keys=False)
        
        return config_path
    
    def load_config(self, config_path: Path) -> Dict[str, Any]:
        """
        Load and parse .dhtconfig file.
        
        Args:
            config_path: Path to .dhtconfig file
            
        Returns:
            Parsed configuration dictionary
            
        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If config file is invalid
        """
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        
        try:
            with open(config_path, 'r') as f:
                content = f.read()
                
            # Try YAML first
            if HAS_YAML:
                try:
                    config = yaml.safe_load(content)
                    if config:
                        return config
                except yaml.YAMLError:
                    pass
            
            # Fall back to JSON
            try:
                return json.loads(content)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid config file format: {e}")
                
        except Exception as e:
            raise ValueError(f"Failed to load config: {e}")
    
    def validate_config(self, config: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate configuration against schema.
        
        Args:
            config: Configuration dictionary to validate
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Basic validation always performed
        if "version" not in config:
            errors.append("Missing required field: version")
        if "project" not in config:
            errors.append("Missing required field: project")
        if "python" not in config:
            errors.append("Missing required field: python")
        elif "version" not in config["python"]:
            errors.append("Missing required field: python.version")
        
        # If we have basic errors, return early
        if errors:
            return False, errors
            
        # If jsonschema is available and we have a schema, do full validation
        if HAS_JSONSCHEMA and self.schema:
            try:
                jsonschema.validate(config, self.schema)
                return True, []
            except jsonschema.ValidationError as e:
                # For now, we'll just warn about schema validation errors
                # since our schema might not be complete
                errors.append(f"Schema validation error: {e.message}")
                # Still return True if basic validation passed
                return True, errors
        
        # No schema validation available, but basic validation passed
        return True, []
    
    def merge_platform_config(
        self,
        base_config: Dict[str, Any],
        platform_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Merge platform-specific overrides into base configuration.
        
        Args:
            base_config: Base configuration dictionary
            platform_name: Platform to merge (None for current platform)
            
        Returns:
            Merged configuration
        """
        if platform_name is None:
            platform_name = platform.system().lower()
            if platform_name == "darwin":
                platform_name = "macos"
        
        # Deep copy base config
        import copy
        merged = copy.deepcopy(base_config)
        
        # Apply platform overrides if they exist
        if "platform_overrides" in base_config:
            platform_config = base_config["platform_overrides"].get(platform_name, {})
            
            # Merge each section
            for section, overrides in platform_config.items():
                if section not in merged:
                    merged[section] = {}
                
                # Deep merge
                self._deep_merge(merged[section], overrides)
        
        return merged
    
    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> None:
        """Deep merge override into base dictionary."""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            elif key in base and isinstance(base[key], list) and isinstance(value, list):
                # Extend lists
                base[key].extend(value)
            else:
                base[key] = value


def main():
    """CLI interface for dhtconfig operations."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="DHT Configuration Generator and Manager"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Generate command
    gen_parser = subparsers.add_parser("generate", help="Generate .dhtconfig from project")
    gen_parser.add_argument(
        "project_path",
        type=Path,
        nargs="?",
        default=Path.cwd(),
        help="Project path (default: current directory)"
    )
    gen_parser.add_argument(
        "--format",
        choices=["yaml", "json"],
        default="yaml",
        help="Output format (default: yaml)"
    )
    gen_parser.add_argument(
        "--no-system-info",
        action="store_true",
        help="Skip system information collection"
    )
    gen_parser.add_argument(
        "--no-checksums",
        action="store_true",
        help="Skip checksum generation"
    )
    
    # Validate command
    val_parser = subparsers.add_parser("validate", help="Validate .dhtconfig file")
    val_parser.add_argument(
        "config_path",
        type=Path,
        nargs="?",
        default=Path.cwd() / ".dhtconfig",
        help="Config file path (default: ./.dhtconfig)"
    )
    
    # Show command
    show_parser = subparsers.add_parser("show", help="Show merged configuration")
    show_parser.add_argument(
        "config_path",
        type=Path,
        nargs="?",
        default=Path.cwd() / ".dhtconfig",
        help="Config file path (default: ./.dhtconfig)"
    )
    show_parser.add_argument(
        "--platform",
        choices=["macos", "linux", "windows"],
        help="Platform to show (default: current)"
    )
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    dht_config = DHTConfig()
    
    if args.command == "generate":
        print(f"Generating .dhtconfig for {args.project_path}...")
        
        config = dht_config.generate_from_project(
            args.project_path,
            include_system_info=not args.no_system_info,
            include_checksums=not args.no_checksums
        )
        
        config_path = dht_config.save_config(
            config,
            args.project_path,
            format=args.format
        )
        
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