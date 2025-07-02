#!/usr/bin/env bash
# Setup script for sequential pre-commit execution
# Configures environment and installs hooks with resource protection

set -euo pipefail

echo "Setting up sequential pre-commit execution..."

# Colors for output
if [[ -t 1 ]]; then
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    RED='\033[0;31m'
    NC='\033[0m'
else
    GREEN=''
    YELLOW=''
    RED=''
    NC=''
fi

# Check if in git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo -e "${RED}Error: Not in a git repository${NC}"
    exit 1
fi

# Set up environment variables
echo -e "${YELLOW}Configuring environment variables...${NC}"

# Add to shell profile if not already present
add_to_profile() {
    local var_name="$1"
    local var_value="$2"
    local profile_file="$3"

    if ! grep -q "export $var_name=" "$profile_file" 2>/dev/null; then
        echo "export $var_name=$var_value" >> "$profile_file"
        echo "  Added $var_name to $profile_file"
    else
        echo "  $var_name already configured in $profile_file"
    fi
}

# Determine shell profile
if [ -n "${BASH_VERSION:-}" ]; then
    PROFILE_FILE="$HOME/.bashrc"
elif [ -n "${ZSH_VERSION:-}" ]; then
    PROFILE_FILE="$HOME/.zshrc"
else
    PROFILE_FILE="$HOME/.profile"
fi

# Add environment variables
add_to_profile "PRE_COMMIT_MAX_WORKERS" "1" "$PROFILE_FILE"
add_to_profile "PYTHONDONTWRITEBYTECODE" "1" "$PROFILE_FILE"
add_to_profile "UV_NO_CACHE" "1" "$PROFILE_FILE"
add_to_profile "PRE_COMMIT_NO_CONCURRENCY" "1" "$PROFILE_FILE"

# Export for current session
export PRE_COMMIT_MAX_WORKERS=1
export PYTHONDONTWRITEBYTECODE=1
export UV_NO_CACHE=1
export PRE_COMMIT_NO_CONCURRENCY=1

# Create wrapper directory
echo -e "${YELLOW}Creating wrapper scripts directory...${NC}"
mkdir -p .pre-commit-wrappers

# Check if wrappers exist
if [ ! -f ".pre-commit-wrappers/memory-limited-hook.sh" ]; then
    echo -e "${RED}Error: Wrapper scripts not found in .pre-commit-wrappers/${NC}"
    echo "Please ensure memory-limited-hook.sh and trufflehog-limited.sh exist"
    exit 1
fi

# Make wrappers executable
chmod +x .pre-commit-wrappers/*.sh

# Install pre-commit if not installed
if ! command -v pre-commit &> /dev/null; then
    echo -e "${YELLOW}Installing pre-commit...${NC}"
    if command -v uv &> /dev/null; then
        uv tool install pre-commit --with pre-commit-uv
    else
        pip install pre-commit
    fi
fi

# Install git hooks
echo -e "${YELLOW}Installing pre-commit hooks...${NC}"
pre-commit install --install-hooks
pre-commit install --hook-type commit-msg

# Create custom git hook for additional protection
echo -e "${YELLOW}Creating custom git pre-commit hook...${NC}"
cat > .git/hooks/pre-commit << 'EOF'
#!/usr/bin/env bash
# Custom pre-commit hook with sequential execution

# Ensure sequential execution
export PRE_COMMIT_MAX_WORKERS=1
export PYTHONDONTWRITEBYTECODE=1

# Check memory before running
if [[ "$OSTYPE" == "darwin"* ]]; then
    FREE_MB=$(vm_stat | grep "Pages free" | awk '{print $3}' | sed 's/\.//')
    PAGE_SIZE=$(pagesize 2>/dev/null || echo 16384)
    FREE_MB=$((FREE_MB * PAGE_SIZE / 1024 / 1024))
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    FREE_MB=$(free -m | awk 'NR==2{print $4}')
fi

if [ "${FREE_MB:-1024}" -lt 512 ]; then
    echo "Warning: Low memory available (${FREE_MB}MB). Consider closing other applications."
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Run pre-commit
exec pre-commit run
EOF

chmod +x .git/hooks/pre-commit

# Verify installation
echo -e "${YELLOW}Verifying installation...${NC}"

# Check environment variables
echo "Environment variables:"
echo "  PRE_COMMIT_MAX_WORKERS=${PRE_COMMIT_MAX_WORKERS}"
echo "  PYTHONDONTWRITEBYTECODE=${PYTHONDONTWRITEBYTECODE}"

# Check pre-commit config
if [ -f ".pre-commit-config.yaml" ]; then
    echo -e "${GREEN}✓ Pre-commit configuration found${NC}"

    # Count hooks with require_serial
    SERIAL_HOOKS=$(grep -c "require_serial: true" .pre-commit-config.yaml 2>/dev/null || echo 0)
    echo "  Sequential hooks configured: $SERIAL_HOOKS"
else
    echo -e "${RED}✗ No .pre-commit-config.yaml found${NC}"
fi

# Test pre-commit
echo -e "${YELLOW}Testing pre-commit installation...${NC}"
if pre-commit --version > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Pre-commit is working${NC}"
    pre-commit --version
else
    echo -e "${RED}✗ Pre-commit not working properly${NC}"
fi

echo
echo -e "${GREEN}Sequential pre-commit setup complete!${NC}"
echo
echo "To manually run pre-commit:"
echo "  pre-commit run                    # On staged files"
echo "  pre-commit run --all-files        # On all files"
echo "  pre-commit run <hook-id> --all-files  # Specific hook"
echo
echo "To skip hooks temporarily:"
echo "  SKIP=mypy,deptry git commit -m 'message'"
echo
echo -e "${YELLOW}Note: Restart your shell or run 'source $PROFILE_FILE' to load environment variables${NC}"
