# Git Hooks and Pre-commit Templates

This directory contains Git hook templates and pre-commit configuration templates that DHT can use when setting up projects.

## Files

### Git Hook Templates
- `*.sample` - Standard Git hook samples
- `bump_version.sh` - Version bumping hook
- `check_dhtl_alias.sh` - Check for DHT alias setup
- `setupGitHooks.js` - JavaScript utility for setting up hooks

### Pre-commit Template
- `.pre-commit-config.yaml` - Template pre-commit configuration

## Important Note

The `.pre-commit-config.yaml` file contains template placeholders like `{REPO_NAME}` that are meant to be replaced when DHT generates pre-commit configuration for a specific project.

This is NOT the pre-commit configuration for DHT itself. DHT's own pre-commit config (if any) would be at the repository root.
