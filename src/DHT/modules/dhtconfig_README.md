# DHT Configuration Module

## Overview

The `dhtconfig` module provides functionality to generate, parse, and validate `.dhtconfig` files. These files capture exact project requirements for deterministic environment regeneration across different platforms.

## Features

- **Automatic Generation**: Analyzes projects to generate comprehensive configuration
- **Schema Validation**: Validates configuration files against JSON Schema
- **Platform Support**: Handles platform-specific overrides for macOS, Linux, and Windows
- **Integration**: Works with diagnostic_reporter_v2 and project_analyzer modules
- **Multiple Formats**: Supports both YAML and JSON output formats

## Usage

### Generate Configuration

```python
from DHT.modules.dhtconfig import DHTConfig
from pathlib import Path

# Initialize handler
config_handler = DHTConfig()

# Generate config from project
config = config_handler.generate_from_project(
    Path("/path/to/project"),
    include_system_info=True,
    include_checksums=True
)

# Save to file
config_path = config_handler.save_config(
    config,
    Path("/path/to/project"),
    format="yaml"
)
```

### Load and Validate Configuration

```python
# Load existing config
config = config_handler.load_config(Path(".dhtconfig"))

# Validate against schema
is_valid, errors = config_handler.validate_config(config)
if not is_valid:
    print("Validation errors:", errors)
```

### Merge Platform-Specific Configuration

```python
# Merge platform overrides
merged_config = config_handler.merge_platform_config(
    config,
    platform_name="linux"  # or None for current platform
)
```

## CLI Interface

The module includes a CLI for common operations:

```bash
# Generate .dhtconfig for current directory
python -m DHT.modules.dhtconfig generate

# Generate for specific project with JSON output
python -m DHT.modules.dhtconfig generate /path/to/project --format json

# Validate existing config
python -m DHT.modules.dhtconfig validate .dhtconfig

# Show merged configuration for specific platform
python -m DHT.modules.dhtconfig show --platform linux
```

## Configuration Structure

The `.dhtconfig` file contains:

### Project Metadata
- Project name, type, and subtypes
- Generation timestamp and DHT version

### Python Environment
- Exact Python version (e.g., "3.11.6")
- Implementation (cpython/pypy)
- Virtual environment settings

### Dependencies
- Python packages with exact versions
- References to lock files
- System-level packages

### Tools
- Required tools (must be present)
- Optional tools (recommended)

### Build Configuration
- Pre/post install commands
- Build commands
- Test commands

### Environment Variables
- Required variables
- Optional variables with defaults

### Platform Overrides
- Platform-specific configurations
- Merged automatically based on current platform

### Validation
- File checksums for verification
- Tool behavior hashes

## Integration with DHT

The dhtconfig module integrates with:

1. **project_analyzer**: Analyzes project structure and dependencies
2. **diagnostic_reporter_v2**: Collects system information
3. **DHT regeneration**: Uses config to recreate environments

## Example .dhtconfig

See `.dhtconfig.example` in the project root for a complete example configuration file.

## Schema

The configuration schema is defined in `DHT/schemas/dhtconfig_schema.yaml` using JSON Schema draft-07.