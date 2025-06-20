# Workspace Commands in DHT

DHT provides comprehensive workspace support similar to Bolt, leveraging UV's workspace functionality to manage monorepos and multi-package projects.

## Overview

Workspace commands allow you to:
- Run scripts across all workspace members
- Execute shell commands in multiple packages
- Upgrade or remove dependencies workspace-wide
- Target specific workspace members
- Filter workspace members by patterns

## Command Reference

### Workspaces Commands (all members)

#### Run Scripts
```bash
# Run a script in all workspace members
dhtl workspaces run test
dhtl ws run test  # alias

# With additional arguments
dhtl ws run test --verbose --coverage
```

#### Execute Commands
```bash
# Execute shell command in all members
dhtl ws exec -- echo "Hello from workspace"
dhtl ws exec -- npm install
```

#### Upgrade Dependencies
```bash
# Upgrade packages across all members
dhtl ws upgrade requests
dhtl ws upgrade requests pytest numpy
```

#### Remove Dependencies
```bash
# Remove packages from all members
dhtl ws remove old-package
dhtl ws remove package1 package2
```

### Workspace Commands (specific member)

#### Target Specific Member
```bash
# Run script in specific workspace member
dhtl workspace frontend run build
dhtl w frontend run build  # alias

# Execute command in specific member
dhtl w backend exec -- make clean

# Upgrade in specific member
dhtl w shared upgrade typescript

# Remove from specific member
dhtl w app remove unused-dep
```

### Project Commands (root only)

```bash
# Run script in root project only
dhtl project run test
dhtl p run test  # alias
```

## Filtering Options

### Filter by Name Pattern
```bash
# Only run in packages matching pattern
dhtl ws run test --only "app-*"
dhtl ws run build --only "lib-*" "utils"

# Exclude packages matching pattern
dhtl ws run lint --ignore "test-*"
dhtl ws run deploy --ignore "dev-*" "staging-*"
```

### Filter by File System
```bash
# Only run in packages containing specific files
dhtl ws run test --only-fs "*.test.ts"
dhtl ws run build --only-fs "webpack.config.js"

# Exclude packages with specific files
dhtl ws run deploy --ignore-fs "*.dev.json"
```

### Combined Filters
```bash
# Complex filtering
dhtl ws run build \
  --only "app-*" \
  --ignore "app-test" \
  --only-fs "package.json" \
  --ignore-fs "skip-build"
```

## Workspace Configuration

Create a workspace by adding to your root `pyproject.toml`:

```toml
[tool.uv.workspace]
members = [
    "packages/*",
    "apps/*",
    "libs/shared",
]
exclude = [
    "packages/deprecated",
    "apps/experimental",
]
```

## Examples

### Example 1: Run Tests Across Workspace
```bash
# Run all tests
dhtl ws run pytest

# Run tests only in backend packages
dhtl ws run pytest --only "backend-*"

# Run tests with coverage
dhtl ws run pytest --coverage
```

### Example 2: Update Dependencies
```bash
# Upgrade React in all frontend packages
dhtl ws upgrade react react-dom --only "frontend-*"

# Remove old linting tools
dhtl ws remove tslint --only-fs "tslint.json"
```

### Example 3: Build Pipeline
```bash
# Clean all packages
dhtl ws exec -- rm -rf dist

# Build shared libraries first
dhtl ws run build --only "lib-*"

# Then build applications
dhtl ws run build --only "app-*"
```

### Example 4: Targeted Operations
```bash
# Deploy only the main app
dhtl w main-app run deploy

# Update types in shared library
dhtl w shared-types upgrade typescript @types/node

# Run specific app's tests
dhtl w backend run test:unit
```

## Implementation Details

1. **UV Integration**: All commands use UV's `--directory` flag to target specific workspace members
2. **Parallel Execution**: Commands run sequentially across members for consistency
3. **Error Handling**: Failed commands in one member don't stop execution in others
4. **Result Summary**: Each command shows success/failure count across all members

## Comparison with Bolt

| Bolt Command | DHT Command | Notes |
|--------------|-------------|-------|
| `bolt ws run test` | `dhtl ws run test` | Same behavior |
| `bolt ws exec -- cmd` | `dhtl ws exec -- cmd` | Same behavior |
| `bolt ws upgrade pkg` | `dhtl ws upgrade pkg` | Uses UV instead of Yarn |
| `bolt ws remove pkg` | `dhtl ws remove pkg` | Uses UV instead of Yarn |
| `bolt workspace pkg run` | `dhtl workspace pkg run` | Same behavior |
| `bolt project run` | `dhtl project run` | Same behavior |

## Best Practices

1. **Organize by Type**: Group similar packages (apps/*, libs/*, etc.)
2. **Use Patterns**: Leverage glob patterns for bulk operations
3. **Test Filters**: Use `--only` with dry runs first
4. **Version Control**: Commit lock files after upgrades
5. **CI/CD Integration**: Use workspace commands in build pipelines

## Troubleshooting

### Not in a UV workspace
Ensure your root `pyproject.toml` has a `[tool.uv.workspace]` section.

### Member not found
Check the exact member name with:
```bash
dhtl ws run echo "Running in \$PWD"
```

### Filter not matching
Patterns use shell-style globs:
- `*` matches any characters
- `?` matches single character
- `[abc]` matches any of a, b, c
