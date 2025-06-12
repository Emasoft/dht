#!/bin/bash
# DHT Environment Regeneration - Proof of Concept
# This demonstrates the core logic for dhtl regenerate command

# ===== Direct Execution Prevention =====
# This script cannot be executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "ERROR: This script is part of a modular system and cannot be executed directly." >&2
    echo "Please use the orchestrator script instead." >&2
    exit 1
fi

set -euo pipefail

# Source required modules
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/dhtl_utils.sh"
source "${SCRIPT_DIR}/dhtl_uv.sh"
source "${SCRIPT_DIR}/dhtl_diagnostics.sh"

# Constants
DHTCONFIG_FILE=".dhtconfig"
DHT_STATE_DIR=".dht"
VALIDATION_REPORT="${DHT_STATE_DIR}/validation_report.json"

#######################################
# Parse .dhtconfig file
# Returns: Sets global variables with config values
#######################################
parse_dhtconfig() {
    if [[ ! -f "$DHTCONFIG_FILE" ]]; then
        echo "Error: No .dhtconfig found. Run 'dhtl setup' first."
        return 1
    fi
    
    # For POC, we'll parse key values manually
    # In production, use proper YAML parser
    PYTHON_VERSION=$(grep -A1 "python:" "$DHTCONFIG_FILE" | grep "version:" | cut -d'"' -f2)
    DHT_VERSION=$(grep "dht_version:" "$DHTCONFIG_FILE" | cut -d'"' -f2)
    LOCK_STRATEGY=$(grep -A1 "dependencies:" "$DHTCONFIG_FILE" | grep "strategy:" | cut -d'"' -f2)
    
    export PYTHON_VERSION DHT_VERSION LOCK_STRATEGY
}

#######################################
# Install exact Python version using UV
#######################################
install_python_version() {
    local required_version="$1"
    
    echo "Installing Python ${required_version}..."
    
    # Install Python version via UV
    if ! uv python install "${required_version}"; then
        echo "Warning: Could not install Python ${required_version} via UV"
        echo "Trying alternative methods..."
        
        # Try pyenv if available
        if command -v pyenv >/dev/null 2>&1; then
            pyenv install -s "${required_version}"
            pyenv local "${required_version}"
        else
            echo "Error: Cannot provide Python ${required_version}"
            return 1
        fi
    fi
    
    # Create venv with specific Python version
    uv venv --python "${required_version}"
    
    # Verify version matches exactly
    local actual_version
    actual_version=$(.venv/bin/python --version | cut -d' ' -f2)
    
    if [[ "$actual_version" != "$required_version" ]]; then
        echo "Error: Python version mismatch. Expected ${required_version}, got ${actual_version}"
        return 1
    fi
    
    echo "✓ Python ${required_version} environment created"
}

#######################################
# Install platform-specific dependencies
#######################################
install_platform_deps() {
    local platform
    platform=$(detect_platform)
    
    echo "Installing platform-specific dependencies for ${platform}..."
    
    # Parse platform deps from .dhtconfig
    # For POC, using hardcoded examples
    case "$platform" in
        darwin)
            if command -v brew >/dev/null 2>&1; then
                # Check if deps are listed in .dhtconfig
                local deps=("postgresql@14" "redis")
                for dep in "${deps[@]}"; do
                    if ! brew list "$dep" >/dev/null 2>&1; then
                        brew install "$dep"
                    fi
                done
            fi
            ;;
        linux)
            if command -v apt-get >/dev/null 2>&1; then
                local deps=("libpq-dev" "redis-server")
                sudo apt-get update
                sudo apt-get install -y "${deps[@]}"
            elif command -v yum >/dev/null 2>&1; then
                local deps=("postgresql-devel" "redis")
                sudo yum install -y "${deps[@]}"
            fi
            ;;
        windows)
            if command -v choco >/dev/null 2>&1; then
                local deps=("postgresql14" "redis-64")
                choco install -y "${deps[@]}"
            fi
            ;;
    esac
    
    echo "✓ Platform dependencies installed"
}

#######################################
# Restore exact dependencies with validation
#######################################
restore_dependencies_exact() {
    echo "Restoring dependencies..."
    
    # Activate venv
    source .venv/bin/activate
    
    # Use lock file based on strategy
    case "$LOCK_STRATEGY" in
        uv)
            if [[ -f "uv.lock" ]]; then
                echo "Using uv.lock for dependency installation..."
                uv sync --locked
            else
                echo "Error: uv.lock not found"
                return 1
            fi
            ;;
        pip-tools)
            if [[ -f "requirements.lock" ]]; then
                echo "Using requirements.lock..."
                uv pip install -r requirements.lock --require-hashes
            else
                echo "Error: requirements.lock not found"
                return 1
            fi
            ;;
    esac
    
    # Install DHT standard tools with exact versions
    local tools=(
        "pytest==7.4.0"
        "mypy==1.5.0"
        "ruff==0.1.0"
        "black==23.7.0"
        "pre-commit==3.3.3"
    )
    
    echo "Installing development tools..."
    uv pip install "${tools[@]}"
    
    echo "✓ Dependencies restored"
}

#######################################
# Generate environment checksum
#######################################
generate_env_checksum() {
    local checksum
    
    # Create comprehensive environment snapshot
    {
        # Python packages with versions
        .venv/bin/pip freeze | sort
        
        # Python version
        .venv/bin/python --version
        
        # System info
        uname -a
        
        # Tool versions
        for tool in pytest mypy ruff black; do
            if command -v "$tool" >/dev/null 2>&1; then
                echo "$tool: $($tool --version 2>&1 | head -1)"
            fi
        done
    } | sha256sum | cut -d' ' -f1
}

#######################################
# Validate regenerated environment
#######################################
validate_environment() {
    echo "Validating environment..."
    
    local current_checksum
    current_checksum=$(generate_env_checksum)
    
    # Get expected checksum from .dhtconfig
    local expected_checksum
    expected_checksum=$(grep "venv_checksum:" "$DHTCONFIG_FILE" | cut -d'"' -f2)
    
    if [[ -z "$expected_checksum" ]]; then
        echo "Warning: No validation checksum in .dhtconfig"
        echo "Current environment checksum: ${current_checksum}"
        return 0
    fi
    
    if [[ "$current_checksum" == "$expected_checksum" ]]; then
        echo "✓ Environment validated: checksums match"
        return 0
    else
        echo "Warning: Environment checksum mismatch"
        echo "Expected: ${expected_checksum}"
        echo "Current:  ${current_checksum}"
        
        # Generate detailed diff report
        generate_validation_report
        
        return 1
    fi
}

#######################################
# Generate validation report
#######################################
generate_validation_report() {
    mkdir -p "$DHT_STATE_DIR"
    
    cat > "$VALIDATION_REPORT" <<EOF
{
    "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
    "platform": "$(detect_platform)",
    "python_version": "$(.venv/bin/python --version | cut -d' ' -f2)",
    "package_count": $(pip freeze | wc -l),
    "validation_status": "mismatch",
    "suggestions": [
        "Check if all system dependencies are installed",
        "Verify Python version matches exactly",
        "Run 'dhtl diagnose-env' for detailed analysis"
    ]
}
EOF
    
    echo "Validation report saved to: $VALIDATION_REPORT"
}

#######################################
# Main regenerate command
#######################################
regenerate_command() {
    echo "🔄 DHT Environment Regeneration"
    echo "================================"
    
    # Step 1: Parse configuration
    if ! parse_dhtconfig; then
        return 1
    fi
    
    # Step 2: Check DHT version compatibility
    echo "Checking DHT version compatibility..."
    
    # Get current DHT version
    CURRENT_DHT_VERSION=""
    if command -v dhtl >/dev/null 2>&1; then
        CURRENT_DHT_VERSION=$(dhtl version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
    fi
    
    if [[ -z "$CURRENT_DHT_VERSION" ]]; then
        echo "Warning: Could not determine current DHT version"
    elif [[ "$CURRENT_DHT_VERSION" != "$DHT_VERSION" ]]; then
        echo "Warning: DHT version mismatch"
        echo "  Expected: $DHT_VERSION"
        echo "  Current:  $CURRENT_DHT_VERSION"
        echo ""
        echo "This may cause compatibility issues. Continue anyway? (y/N)"
        read -r response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            echo "Aborted."
            return 1
        fi
    else
        echo "✓ DHT version $DHT_VERSION is compatible"
    fi
    
    # Step 3: Install exact Python version
    if ! install_python_version "$PYTHON_VERSION"; then
        return 1
    fi
    
    # Step 4: Install platform dependencies
    if ! install_platform_deps; then
        echo "Warning: Some platform dependencies may be missing"
    fi
    
    # Step 5: Restore exact dependencies
    if ! restore_dependencies_exact; then
        return 1
    fi
    
    # Step 6: Configure git hooks
    if [[ -f ".pre-commit-config.yaml" ]] && command -v pre-commit >/dev/null 2>&1; then
        echo "Installing git hooks..."
        pre-commit install
    fi
    
    # Step 7: Create .env template
    if [[ ! -f ".env" ]]; then
        echo "Creating .env template..."
        create_env_template
    fi
    
    # Step 8: Validate environment
    validate_environment
    
    # Step 9: Show summary
    echo ""
    echo "🎉 Environment regeneration complete!"
    echo ""
    echo "Python version: ${PYTHON_VERSION}"
    echo "Platform: $(detect_platform)"
    echo "Lock strategy: ${LOCK_STRATEGY}"
    echo ""
    echo "To activate the environment:"
    echo "  source .venv/bin/activate"
    echo ""
    
    # Check for missing env vars
    check_missing_env_vars
}

#######################################
# Clone command with regeneration
#######################################
clone_command() {
    local url="$1"
    
    if [[ -z "$url" ]]; then
        echo "Usage: dhtl clone <repository-url>"
        return 1
    fi
    
    # Extract repo name
    local repo_name
    repo_name=$(basename "$url" .git)
    
    echo "Cloning repository..."
    if ! gh repo clone "$url"; then
        # Fallback to git clone
        git clone "$url"
    fi
    
    # Change to repo directory
    cd "$repo_name" || return 1
    
    # Run regeneration
    regenerate_command
}

#######################################
# Fork command with regeneration
#######################################
fork_command() {
    local url="$1"
    
    if [[ -z "$url" ]]; then
        echo "Usage: dhtl fork <repository-url>"
        return 1
    fi
    
    echo "Forking repository..."
    if ! gh repo fork "$url" --clone; then
        echo "Error: Failed to fork repository"
        return 1
    fi
    
    # Extract repo name
    local repo_name
    repo_name=$(basename "$url" .git)
    
    # Change to repo directory
    cd "$repo_name" || return 1
    
    # Add upstream remote
    git remote add upstream "$url"
    
    # Run regeneration
    regenerate_command
}

#######################################
# Helper functions
#######################################
detect_platform() {
    case "$OSTYPE" in
        darwin*) echo "darwin" ;;
        linux*) echo "linux" ;;
        msys*|cygwin*) echo "windows" ;;
        *) echo "unknown" ;;
    esac
}

create_env_template() {
    cat > .env.template <<'EOF'
# Required environment variables
DATABASE_URL=
REDIS_URL=

# Optional environment variables
DEBUG=false
LOG_LEVEL=info

# Add your secrets here (never commit actual values)
OPENAI_API_KEY=
EOF
    
    echo "Created .env.template"
}

check_missing_env_vars() {
    local required_vars=("DATABASE_URL" "REDIS_URL")
    local missing=()
    
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var:-}" ]]; then
            missing+=("$var")
        fi
    done
    
    if [[ ${#missing[@]} -gt 0 ]]; then
        echo "⚠️  Missing required environment variables:"
        printf "   - %s\n" "${missing[@]}"
        echo ""
        echo "See .env.template for guidance"
    fi
}

# Make functions available when sourced
export -f regenerate_command clone_command fork_command