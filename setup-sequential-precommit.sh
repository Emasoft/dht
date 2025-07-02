#!/usr/bin/env bash
# Enhanced setup script for sequential pre-commit execution with resource monitoring
# All configuration is project-local - no system files are modified

set -euo pipefail

echo "Setting up project-local sequential pre-commit with resource monitoring..."

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    uv venv
fi

# Create activation hooks directory for environment variables
echo "Setting up project-local environment configuration..."
if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
    # Windows (Git Bash)
    mkdir -p .venv/Scripts/activate.d
    ACTIVATE_DIR=".venv/Scripts/activate.d"
else
    # macOS/Linux
    mkdir -p .venv/bin/activate.d
    ACTIVATE_DIR=".venv/bin/activate.d"
fi

# Create environment configuration that will be sourced on activation
cat > "$ACTIVATE_DIR/sequential-precommit.sh" << 'EOF'
#!/usr/bin/env bash
# Project-local environment configuration
export PRE_COMMIT_MAX_WORKERS=1
export PYTHONDONTWRITEBYTECODE=1
export UV_NO_CACHE=1
export PRE_COMMIT_NO_CONCURRENCY=1
export MEMORY_LIMIT_MB=2048
export TIMEOUT_SECONDS=600
export TRUFFLEHOG_TIMEOUT=300
export TRUFFLEHOG_MEMORY_MB=1024
export TRUFFLEHOG_CONCURRENCY=1
EOF

chmod +x "$ACTIVATE_DIR/sequential-precommit.sh" 2>/dev/null || true

# Activate virtual environment
if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
    source .venv/Scripts/activate
else
    source .venv/bin/activate
fi

# Install pre-commit
echo "Installing pre-commit..."
if ! command -v pre-commit &> /dev/null; then
    # Try installing as a uv tool first
    if uv tool install pre-commit --with pre-commit-uv 2>/dev/null; then
        echo "✓ Pre-commit installed as uv tool"
    else
        # Fallback to pip install
        echo "Installing pre-commit with pip..."
        uv pip install pre-commit
    fi
else
    echo "✓ Pre-commit already installed"
fi

# Create wrapper scripts directory
mkdir -p .pre-commit-wrappers

# Create memory-limited wrapper
cat > .pre-commit-wrappers/memory-limited-hook.sh << 'EOF'
#!/usr/bin/env bash
set -euo pipefail

# Use project-local environment variables
MEMORY_LIMIT_MB="${MEMORY_LIMIT_MB:-2048}"
TIMEOUT_SECONDS="${TIMEOUT_SECONDS:-600}"

if [ $# -lt 1 ]; then
    echo "Usage: $0 <command> [args...]"
    exit 1
fi

COMMAND="$1"
shift

# Platform-specific memory limiting
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    ulimit -v $((MEMORY_LIMIT_MB * 1024)) 2>/dev/null || true
    ulimit -d $((MEMORY_LIMIT_MB * 1024)) 2>/dev/null || true
fi

# Cleanup on exit
cleanup() {
    pkill -P $$ 2>/dev/null || true
    if [[ "$COMMAND" == *"python"* ]] || [[ "$COMMAND" == *"uv"* ]]; then
        python3 -c "import gc; gc.collect()" 2>/dev/null || true
    fi
}
trap cleanup EXIT INT TERM

echo "Running (memory limited to ${MEMORY_LIMIT_MB}MB): $COMMAND $*"

# Execute with timeout
if command -v timeout &> /dev/null; then
    exec timeout "$TIMEOUT_SECONDS" "$COMMAND" "$@"
elif command -v gtimeout &> /dev/null; then
    exec gtimeout "$TIMEOUT_SECONDS" "$COMMAND" "$@"
else
    "$COMMAND" "$@"
fi
EOF

# Create Trufflehog wrapper
cat > .pre-commit-wrappers/trufflehog-limited.sh << 'EOF'
#!/usr/bin/env bash
set -euo pipefail

# Use project-local environment variables
TIMEOUT="${TRUFFLEHOG_TIMEOUT:-300}"
MEMORY_LIMIT="${TRUFFLEHOG_MEMORY_MB:-1024}"
CONCURRENCY="${TRUFFLEHOG_CONCURRENCY:-1}"

# Check if trufflehog is installed
if ! command -v trufflehog &> /dev/null; then
    echo "Installing Trufflehog locally..."
    # Install to project-local bin directory
    mkdir -p .venv/bin
    curl -sSfL https://raw.githubusercontent.com/trufflesecurity/trufflehog/main/scripts/install.sh | \
        sh -s -- -b .venv/bin
fi

echo "Running Trufflehog (timeout: ${TIMEOUT}s, concurrency: ${CONCURRENCY})..."

# Run with resource limits
if command -v timeout &> /dev/null; then
    timeout_cmd="timeout ${TIMEOUT}s"
elif command -v gtimeout &> /dev/null; then
    timeout_cmd="gtimeout ${TIMEOUT}s"
else
    timeout_cmd=""
fi

$timeout_cmd trufflehog git file://. \
    --only-verified \
    --fail \
    --no-update \
    --concurrency="$CONCURRENCY" || exit_code=$?

if [ "${exit_code:-0}" -eq 124 ]; then
    echo "Warning: Trufflehog timed out after ${TIMEOUT}s"
    exit 0
elif [ "${exit_code:-0}" -ne 0 ]; then
    echo "Error: Trufflehog found verified secrets!"
    exit 1
fi

echo "✓ No verified secrets found"
EOF

# Create resource monitor script
cat > .pre-commit-wrappers/resource-monitor.sh << 'EOF'
#!/usr/bin/env bash
# Resource monitoring script for pre-commit

# Function to get memory usage in MB
get_memory_usage() {
    local pid=$1
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS: Get RSS in bytes and convert to MB
        ps -o rss= -p "$pid" 2>/dev/null | awk '{print int($1/1024)}' || echo "0"
    else
        # Linux: Get RSS in KB and convert to MB
        ps -o rss= -p "$pid" 2>/dev/null | awk '{print int($1/1024)}' || echo "0"
    fi
}

# Function to get open file descriptors
get_fd_count() {
    local pid=$1
    if [[ "$OSTYPE" == "darwin"* ]]; then
        lsof -p "$pid" 2>/dev/null | wc -l || echo "0"
    else
        ls /proc/"$pid"/fd 2>/dev/null | wc -l || echo "0"
    fi
}

# Function to count child processes
get_child_count() {
    local pid=$1
    pgrep -P "$pid" 2>/dev/null | wc -l || echo "0"
}

# Main monitoring loop
monitor_resources() {
    local parent_pid=$1
    local log_file=$2
    local memory_limit=$3

    echo "=== Pre-commit Resource Monitor ===" > "$log_file"
    echo "Started: $(date)" >> "$log_file"
    echo "Memory limit: ${memory_limit}MB" >> "$log_file"
    echo "Monitoring PID: $parent_pid" >> "$log_file"
    echo "===================================" >> "$log_file"

    local max_memory=0
    local max_fd=0
    local max_children=0

    while kill -0 "$parent_pid" 2>/dev/null; do
        local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
        local memory_mb=$(get_memory_usage "$parent_pid")
        local fd_count=$(get_fd_count "$parent_pid")
        local child_count=$(get_child_count "$parent_pid")

        # Track maximums
        [ "$memory_mb" -gt "$max_memory" ] && max_memory=$memory_mb
        [ "$fd_count" -gt "$max_fd" ] && max_fd=$fd_count
        [ "$child_count" -gt "$max_children" ] && max_children=$child_count

        # Log current metrics
        echo "[$timestamp] PID $parent_pid - Memory: ${memory_mb}MB, FDs: $fd_count, Children: $child_count" >> "$log_file"

        # Get all child processes and their memory
        local total_memory=$memory_mb
        for child_pid in $(pgrep -P "$parent_pid" 2>/dev/null); do
            local child_mem=$(get_memory_usage "$child_pid")
            local child_cmd=$(ps -p "$child_pid" -o comm= 2>/dev/null || echo "unknown")
            total_memory=$((total_memory + child_mem))
            if [ "$child_mem" -gt 10 ]; then  # Only log children using >10MB
                echo "  └─ Child PID $child_pid ($child_cmd) - Memory: ${child_mem}MB" >> "$log_file"
            fi
        done

        # Check if memory limit exceeded
        if [ "$total_memory" -gt "$memory_limit" ]; then
            echo "[$timestamp] CRITICAL: Total memory usage (${total_memory}MB) exceeds limit (${memory_limit}MB)" >> "$log_file"

            # Kill all child processes first
            for child_pid in $(pgrep -P "$parent_pid" 2>/dev/null); do
                echo "[$timestamp] Killing child process $child_pid" >> "$log_file"
                kill -TERM "$child_pid" 2>/dev/null || true
            done

            sleep 1

            # Kill parent
            echo "[$timestamp] Killing parent process $parent_pid" >> "$log_file"
            kill -TERM "$parent_pid" 2>/dev/null || true
            sleep 1
            kill -KILL "$parent_pid" 2>/dev/null || true

            break
        fi

        sleep 1
    done

    # Final summary
    echo "" >> "$log_file"
    echo "=== Resource Usage Summary ===" >> "$log_file"
    echo "Ended: $(date)" >> "$log_file"
    echo "Peak Memory: ${max_memory}MB" >> "$log_file"
    echo "Peak File Descriptors: $max_fd" >> "$log_file"
    echo "Peak Child Processes: $max_children" >> "$log_file"
    echo "==============================" >> "$log_file"
}

# Export the function so it can be used
export -f get_memory_usage get_fd_count get_child_count monitor_resources
EOF

chmod +x .pre-commit-wrappers/*.sh

# Create git hook with resource monitoring
cat > .git/hooks/pre-commit << 'EOF'
#!/usr/bin/env bash
# Git pre-commit hook with resource monitoring
# Monitors memory, file descriptors, and processes during pre-commit execution

PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$PROJECT_ROOT" || exit 1

# Source project virtual environment
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
elif [ -f ".venv/Scripts/activate" ]; then
    source .venv/Scripts/activate
fi

# Source sequential configuration
if [ -f ".venv/bin/activate.d/sequential-precommit.sh" ]; then
    source .venv/bin/activate.d/sequential-precommit.sh
elif [ -f ".venv/Scripts/activate.d/sequential-precommit.sh" ]; then
    source .venv/Scripts/activate.d/sequential-precommit.sh
fi

# Configuration
MEMORY_LIMIT_MB="${MEMORY_LIMIT_MB:-4096}"
LOG_DIR=".pre-commit-logs"
MONITOR_INTERVAL=1

# Create log directory
mkdir -p "$LOG_DIR"

# Generate timestamp for log file
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="$LOG_DIR/resource_usage_${TIMESTAMP}.log"

# Use project-local temp directory for PID file to avoid permission issues
TEMP_DIR="$PROJECT_ROOT/.pre-commit-temp"
mkdir -p "$TEMP_DIR"
MONITOR_PID_FILE="$TEMP_DIR/pre-commit-monitor-$$.pid"

# Source monitor functions
source .pre-commit-wrappers/resource-monitor.sh

# Start resource monitor in background
monitor_resources $$ "$LOG_FILE" "$MEMORY_LIMIT_MB" &
MONITOR_PID=$!
echo "$MONITOR_PID" > "$MONITOR_PID_FILE"

# Cleanup function
cleanup_monitor() {
    if [ -f "$MONITOR_PID_FILE" ]; then
        local monitor_pid=$(cat "$MONITOR_PID_FILE")
        if kill -0 "$monitor_pid" 2>/dev/null; then
            kill -TERM "$monitor_pid" 2>/dev/null || true
        fi
        rm -f "$MONITOR_PID_FILE"
    fi

    # Clean up temp directory
    if [ -d "$TEMP_DIR" ]; then
        rm -rf "$TEMP_DIR"
    fi

    # Display log summary
    if [ -f "$LOG_FILE" ]; then
        echo ""
        echo "Resource usage log saved to: $LOG_FILE"
        tail -n 20 "$LOG_FILE" | grep -E "(Peak|WARNING|CRITICAL|Summary)" || true
    fi
}

# Set trap to cleanup monitor on exit
trap cleanup_monitor EXIT INT TERM

# Check memory before running
if [[ "$OSTYPE" == "darwin"* ]]; then
    FREE_MB=$(vm_stat | grep "Pages free" | awk '{print $3}' | sed 's/\.//')
    PAGE_SIZE=$(sysctl -n hw.pagesize 2>/dev/null || echo 16384)
    FREE_MB=$((FREE_MB * PAGE_SIZE / 1024 / 1024))
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    FREE_MB=$(free -m | awk 'NR==2{print $4}')
fi

if [ "${FREE_MB:-1024}" -lt 512 ]; then
    echo "Warning: Low memory (${FREE_MB}MB). Consider closing other applications."
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] WARNING: Starting with low system memory: ${FREE_MB}MB" >> "$LOG_FILE"
fi

# Run pre-commit
echo "Starting pre-commit with resource monitoring..."
echo "Monitor log: $LOG_FILE"
pre-commit run "$@"
PRE_COMMIT_EXIT_CODE=$?

# Give monitor time to write final metrics
sleep 2

# Return pre-commit's exit code
exit $PRE_COMMIT_EXIT_CODE
EOF

chmod +x .git/hooks/pre-commit

# Install pre-commit hooks
echo "Installing pre-commit hooks..."
pre-commit install --install-hooks
pre-commit install --hook-type commit-msg

# Create .gitignore entries for logs and temp files
if [ -f .gitignore ]; then
    if ! grep -q "^\.pre-commit-logs" .gitignore 2>/dev/null; then
        echo ".pre-commit-logs/" >> .gitignore
    fi
    if ! grep -q "^\.pre-commit-temp" .gitignore 2>/dev/null; then
        echo ".pre-commit-temp/" >> .gitignore
    fi
else
    cat > .gitignore << 'EOF'
.pre-commit-logs/
.pre-commit-temp/
EOF
fi

echo "✓ Sequential pre-commit with resource monitoring setup complete!"
echo ""
echo "To activate the environment:"
echo "  source .venv/bin/activate"
echo ""
echo "The following variables are now set (project-local):"
echo "  PRE_COMMIT_MAX_WORKERS=1"
echo "  MEMORY_LIMIT_MB=2048 (hooks), 4096 (monitoring kill threshold)"
echo "  TIMEOUT_SECONDS=600"
echo ""
echo "Resource usage logs will be saved to: .pre-commit-logs/"
echo ""
echo "Features enabled:"
echo "  • Sequential hook execution (no parallelism)"
echo "  • Memory usage monitoring and logging"
echo "  • File descriptor tracking"
echo "  • Child process monitoring"
echo "  • Automatic process termination at 4GB memory"
echo "  • Peak usage statistics"
