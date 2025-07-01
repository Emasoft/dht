#!/usr/bin/env bash
# Sequential pre-commit hook executor with memory management
# This script ensures hooks run one at a time and clears memory between each

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to clear system caches and free memory
clear_memory() {
    echo -e "${YELLOW}Clearing memory caches...${NC}"
    
    # Purge inactive memory on macOS
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # sudo purge is too aggressive and requires sudo
        # Instead, we'll force Python garbage collection
        python3 -c "import gc; gc.collect()" 2>/dev/null || true
        
        # Give the system a moment to reclaim memory
        sleep 1
    fi
    
    # Force sync to ensure all disk writes are completed
    sync
    
    # Report memory status
    if command -v vm_stat &> /dev/null; then
        echo "Memory status:"
        vm_stat | grep -E "Pages free|Pages active|Pages inactive" | head -3
    fi
}

# Function to check available memory
check_memory() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # Get free memory in MB
        local free_pages=$(vm_stat | grep "Pages free" | awk '{print $3}' | sed 's/\.//')
        local page_size=$(vm_stat | head -1 | grep -o '[0-9]*')
        local free_mb=$((free_pages * page_size / 1024 / 1024))
        
        if [ "$free_mb" -lt 1024 ]; then
            echo -e "${RED}Warning: Low memory available (${free_mb}MB free)${NC}"
            echo "Consider closing other applications before proceeding."
            sleep 2
        fi
    fi
}

# Main execution
echo -e "${GREEN}Starting sequential pre-commit hook execution...${NC}"
echo "This ensures only one hook runs at a time to prevent resource exhaustion."
echo ""

# Check initial memory state
check_memory

# Export environment variable to limit workers
export PRE_COMMIT_MAX_WORKERS=1
export PYTHONDONTWRITEBYTECODE=1  # Prevent .pyc file creation
export UV_NO_CACHE=1  # Prevent UV from using cache during hooks

# Run pre-commit with sequential execution
echo -e "${GREEN}Running pre-commit hooks sequentially...${NC}"

# Pass all arguments to pre-commit
pre-commit "$@"
RESULT=$?

# Clear memory after completion
clear_memory

echo -e "${GREEN}Sequential pre-commit execution completed.${NC}"
exit $RESULT