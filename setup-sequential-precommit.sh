#!/usr/bin/env bash
# Setup script for sequential pre-commit execution

set -euo pipefail

echo "Setting up sequential pre-commit execution..."

# Backup current pre-commit config
if [ -f .pre-commit-config.yaml ]; then
    cp .pre-commit-config.yaml .pre-commit-config.yaml.backup
    echo "✅ Backed up current config to .pre-commit-config.yaml.backup"
fi

# Use sequential config
cp .pre-commit-config-sequential.yaml .pre-commit-config.yaml
echo "✅ Installed sequential pre-commit configuration"

# Create git hook that sets environment variables
cat > .git/hooks/pre-commit << 'EOF'
#!/usr/bin/env bash
# Pre-commit hook with resource management

# Set environment variables for sequential execution
export PRE_COMMIT_MAX_WORKERS=1
export PYTHONDONTWRITEBYTECODE=1
export UV_NO_CACHE=1

# Limit memory usage on macOS
if [[ "$OSTYPE" == "darwin"* ]]; then
    # Soft limit to prevent runaway processes
    ulimit -v 4194304  # 4GB virtual memory limit
fi

# Report configuration
echo "🔧 Pre-commit configured for sequential execution"
echo "   - Max workers: 1"
echo "   - Python bytecode: disabled"
echo "   - UV cache: disabled"
echo ""

# Run pre-commit
exec pre-commit run --from-ref HEAD~ --to-ref HEAD
EOF

chmod +x .git/hooks/pre-commit
echo "✅ Installed git pre-commit hook"

# Update shell configuration to set environment variables
echo ""
echo "To make sequential execution permanent, add these to your shell profile:"
echo ""
echo "export PRE_COMMIT_MAX_WORKERS=1"
echo "export PYTHONDONTWRITEBYTECODE=1"
echo ""

# Create alias for easy switching
echo "alias precommit-sequential='./.pre-commit-sequential.sh'" >> ~/.zshrc
echo "✅ Added 'precommit-sequential' alias"

echo ""
echo "Setup complete! Sequential pre-commit execution is now configured."
echo ""
echo "Usage:"
echo "  - Normal commits will use sequential execution automatically"
echo "  - To run manually: pre-commit run --all-files"
echo "  - To run with wrapper: ./.pre-commit-sequential.sh run --all-files"
echo "  - To restore parallel execution: cp .pre-commit-config.yaml.backup .pre-commit-config.yaml"
