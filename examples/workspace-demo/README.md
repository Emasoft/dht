# DHT Workspace Demo

This example demonstrates DHT's Bolt-compatible workspace functionality for managing monorepos.

## Structure

```
workspace-demo/
├── pyproject.toml          # Root workspace configuration
├── packages/               # Shared libraries
│   ├── shared-utils/       # Utility functions
│   └── api-client/         # API client library
└── apps/                   # Applications
    ├── web-app/            # FastAPI web application
    └── cli-tool/           # Click-based CLI tool
```

## Workspace Commands Examples

### Run commands across all workspace members

```bash
# Run tests in all packages
dhtl ws run test

# Build all packages
dhtl ws run build

# Lint all code
dhtl ws run lint
```

### Execute shell commands

```bash
# Clean all build artifacts
dhtl ws exec -- rm -rf dist build

# Check Python version in each package
dhtl ws exec -- python --version
```

### Manage dependencies

```bash
# Upgrade a dependency across all packages
dhtl ws upgrade requests

# Remove unused dependencies
dhtl ws remove old-package
```

### Filter by package patterns

```bash
# Run tests only in apps
dhtl ws run test --only "app-*"

# Build only packages (not apps)
dhtl ws run build --only "packages/*"

# Deploy only web-app
dhtl ws run deploy --only "web-app"
```

### Target specific members

```bash
# Run dev server for web-app
dhtl workspace web-app run dev
dhtl w web-app run dev  # alias

# Generate code in api-client
dhtl w api-client run generate

# Package the CLI tool
dhtl w cli-tool run package
```

### Root project only

```bash
# Run root project tests
dhtl project run test
dhtl p run test  # alias
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

3. Try the commands above!

## Comparison with Bolt

| Bolt | DHT | Description |
|------|-----|-------------|
| `bolt ws run test` | `dhtl ws run test` | Run tests in all packages |
| `bolt ws exec -- cmd` | `dhtl ws exec -- cmd` | Execute command in all packages |
| `bolt workspace pkg run` | `dhtl workspace pkg run` | Run in specific package |
| `bolt project run` | `dhtl project run` | Run in root only |

## Benefits

1. **Monorepo Management**: Easily manage multiple related packages
2. **Consistent Commands**: Same commands work across all packages
3. **Bulk Operations**: Update dependencies everywhere at once
4. **Flexible Filtering**: Target specific packages with patterns
5. **UV Speed**: Fast dependency resolution and installation
