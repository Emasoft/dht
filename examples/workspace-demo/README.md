# DHT Workspace Demo

This example demonstrates DHT's workspace functionality for managing monorepos with multiple interdependent packages.

## Structure

```
workspace-demo/
├── pyproject.toml          # Root workspace configuration
├── demo_root.py            # Root project script
├── packages/               # Shared libraries
│   ├── core/               # Core functionality (demo-core)
│   ├── utils/              # Utility functions (demo-utils)
│   ├── experimental/       # Experimental features (demo-experimental)
│   ├── shared-utils/       # Legacy utils package
│   └── api-client/         # Legacy API client
└── apps/                   # Applications
    ├── web/                # Web application (demo-web)
    ├── cli/                # CLI application (demo-cli)
    ├── web-app/            # Legacy web app
    └── cli-tool/           # Legacy CLI tool
```

## Package Dependencies

- **demo-core**: Base package with no dependencies
- **demo-utils**: Depends on demo-core
- **demo-experimental**: Depends on demo-core, demo-utils, and numpy
- **demo-web**: Depends on demo-core, demo-utils, and flask
- **demo-cli**: Depends on all packages plus click and rich

## Quick Demo

Try these commands to see the workspace in action:

```bash
# First, setup the workspace
cd examples/workspace-demo
dhtl setup

# Run the root project demo
dhtl project run demo-root

# Run scripts in all workspace members
dhtl workspaces run --list    # See all available scripts

# Run hello from core in all packages that have it
dhtl workspaces run core-hello

# Run specific package scripts
dhtl workspace core run core-info
dhtl workspace utils run utils-format
dhtl workspace experimental run exp-analyze
dhtl workspace web run web-serve
dhtl workspace cli run demo-cli
```

## Workspace Commands Examples

### 1. Running Scripts Across All Members

```bash
# List all available scripts in the workspace
dhtl workspaces run --list
dhtl ws run --list  # short alias

# Run a script that exists in multiple packages
dhtl ws run test           # Runs 'test' in all packages that define it
dhtl ws run lint           # Runs 'lint' in all packages that define it
dhtl ws run build          # Runs 'build' in all packages that define it

# Run Python modules directly
dhtl ws run -m pytest      # Run pytest in all packages
dhtl ws run -m mypy .      # Run mypy in all packages
```

### 2. Executing Shell Commands

```bash
# Execute shell commands in all workspace directories
dhtl ws exec -- echo "Package: \$PWD"
dhtl ws exec -- ls -la
dhtl ws exec -- rm -rf dist build
dhtl ws exec -- git status
```

### 3. Working with Specific Workspace Members

```bash
# Run scripts in a specific package
dhtl workspace core run core-hello
dhtl w core run core-info         # using alias

dhtl workspace utils run utils-validate
dhtl w experimental run exp-benchmark

# Execute commands in specific package directory
dhtl w web exec -- pwd
dhtl w cli exec -- ls src/
```

### 4. Running Only in Root Project

```bash
# Run root project scripts (ignoring workspace members)
dhtl project run demo-root
dhtl p run test           # alias
dhtl p run lint
dhtl p run build
```

### 5. Filtering with --only and --ignore

```bash
# Run only in packages matching a pattern
dhtl ws run test --only "demo-*"           # All demo packages
dhtl ws run build --only "packages/*"      # Only packages directory
dhtl ws run serve --only "apps/*"          # Only apps directory
dhtl ws run test --only "*/core"           # Only core package

# Exclude packages matching a pattern
dhtl ws run test --ignore "experimental"   # Skip experimental
dhtl ws run lint --ignore "apps/*"         # Skip all apps
dhtl ws run build --ignore "*-legacy"      # Skip legacy packages
```

### 6. Package Management Operations

```bash
# Add a package to all workspace members
dhtl ws add requests
dhtl ws add --dev pytest     # Add as dev dependency

# Add to specific members only
dhtl ws add numpy --only "experimental"
dhtl ws add flask --only "apps/web"

# Remove packages
dhtl ws remove old-package
dhtl ws remove pytest --dev

# Upgrade packages
dhtl ws upgrade requests
dhtl ws upgrade --all        # Upgrade all packages
```

### 7. Advanced Filtering Examples

```bash
# Combine multiple filters
dhtl ws run test --only "packages/*" --ignore "*/experimental"

# Run different scripts based on package type
dhtl ws run build --only "packages/*"
dhtl ws run serve --only "apps/*"
dhtl ws run benchmark --only "*/experimental"

# Use workspace-specific scripts
dhtl ws run core-hello        # Runs only where defined
dhtl ws run web-dev          # Runs only in web app
dhtl ws run exp-analyze      # Runs only in experimental
```

## Setup Instructions

1. Navigate to this directory:
   ```bash
   cd examples/workspace-demo
   ```

2. Initialize the workspace:
   ```bash
   dhtl setup
   ```

3. Install dependencies:
   ```bash
   dhtl ws sync    # Sync all workspace dependencies
   ```

4. Try the demo commands above!

## Command Reference

### Workspace Commands (dhtl workspaces / ws)
- `dhtl workspaces run <script>` - Run script in all members
- `dhtl ws run --list` - List all available scripts
- `dhtl ws exec -- <command>` - Execute shell command in all members
- `dhtl ws add <package>` - Add dependency to all members
- `dhtl ws remove <package>` - Remove dependency from all members
- `dhtl ws upgrade <package>` - Upgrade dependency in all members
- `dhtl ws sync` - Sync dependencies for all members

### Single Workspace Commands (dhtl workspace / w)
- `dhtl workspace <name> run <script>` - Run script in specific member
- `dhtl w <name> exec -- <command>` - Execute command in specific member
- `dhtl w <name> add <package>` - Add dependency to specific member
- `dhtl w <name> sync` - Sync dependencies for specific member

### Project Commands (dhtl project / p)
- `dhtl project run <script>` - Run script in root only
- `dhtl p exec -- <command>` - Execute command in root only
- `dhtl p add <package>` - Add dependency to root only

### Filter Options
- `--only <pattern>` - Include only matching members
- `--ignore <pattern>` - Exclude matching members
- `--dev` - Work with dev dependencies
- `-m <module>` - Run as Python module

## Bolt-Compatible Commands

DHT provides Bolt-compatible commands for easy migration:

### Core Commands
- `dhtl add <package>` - Add a dependency (alias for `uv add`)
- `dhtl remove <package>` - Remove a dependency (alias for `uv remove`)
- `dhtl upgrade <package>` - Upgrade dependencies (alias for `uv add --upgrade`)
- `dhtl install` - Install dependencies (alias for `setup`)
- `dhtl fmt` - Format code (alias for `format`)
- `dhtl check` - Type check with mypy
- `dhtl doc` - Generate documentation
- `dhtl bin` - Show virtual environment bin directory

### Examples
```bash
# Add dependencies
dhtl add click rich
dhtl add --dev pytest mypy

# Remove dependencies
dhtl remove old-package

# Upgrade dependencies
dhtl upgrade requests
dhtl upgrade  # Upgrade all

# Format and check code
dhtl fmt
dhtl check

# Show bin directory
dhtl bin
```

## Workspace Structure Benefits

1. **Monorepo Management**: All related packages in one repository
2. **Shared Dependencies**: Workspace packages can depend on each other
3. **Consistent Tooling**: Same commands work across all packages
4. **Atomic Changes**: Update multiple packages in one commit
5. **Fast Operations**: UV's speed makes workspace operations quick
6. **Flexible Filtering**: Target specific packages with patterns

## Troubleshooting

If you encounter issues:

1. Ensure you're in the workspace root directory
2. Check that `dhtl setup` completed successfully
3. Verify UV is installed: `uv --version`
4. Check workspace members are detected: `dhtl ws run --list`
5. For script issues, check the pyproject.toml files

## Next Steps

- Modify the demo packages to see how changes propagate
- Add new workspace members by creating directories with pyproject.toml
- Try building and testing all packages at once
- Experiment with cross-package imports and dependencies
