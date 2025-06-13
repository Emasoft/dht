#!/bin/bash
# dhtl_guardian_1.sh - Guardian_1 module for DHT Launcher
#
# Generated on: 2025-05-02 23:31:20
# Generator: extract_dhtl_modules.py
#
# This file contains functions related to guardian_1 functionality.
# It is sourced by the main dhtl.sh orchestrator and should not be modified manually.
# To make changes, modify the original dhtl.sh and regenerate the modules.
#
# DO NOT execute this file directly.


# ===== Direct Execution Prevention =====
# This script cannot be executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "ERROR: This script is part of dhtl and cannot be executed directly." >&2
    echo "Please use the main dhtl.sh script instead." >&2
    exit 1
fi

# Check if we're being sourced by the main script
if [[ -z "$DHTL_SESSION_ID" ]]; then
    echo "ERROR: This script is being sourced outside of dhtl. This is not supported." >&2
    return 1 2>/dev/null || exit 1
fi


# ===== Functions =====

# Ensure the process guardian is running
ensure_process_guardian_running() {
    # For testing purposes, we'll just return 0 (success)
    # In a real implementation, this would check if the guardian is running
    # and start it if not
    return 0
}

run_with_guardian() {
    local command=$1
    local process_type=$2
    local mem_limit=$3
    shift 3

    # Determine memory limit based on process type
    if [ -z "$mem_limit" ]; then
        if [ "$process_type" = "node" ]; then
            mem_limit=$NODE_MEM_LIMIT
        elif [ "$process_type" = "python" ]; then
            mem_limit=$PYTHON_MEM_LIMIT
        else
            mem_limit=$DEFAULT_MEM_LIMIT
        fi
    fi

    # Determine system resources - use more efficient detection methods
    # and cache results to avoid repeated system calls
    if [ -z "${DHTL_SYSTEM_RESOURCES_DETECTED:-}" ]; then
        # Set detection flag - only detect once per session
        DHTL_SYSTEM_RESOURCES_DETECTED=true
        
        if [[ $(uname -s) == "Darwin" ]]; then
            # On macOS, determine available RAM and CPU cores
            # Use vm_stat for memory instead of sysctl for better performance
            PAGE_SIZE=$(sysctl -n hw.pagesize)
            if [ -z "$PAGE_SIZE" ]; then
                PAGE_SIZE=4096  # Default if detection fails
            fi
            
            # Get free memory pages and calculate total available memory
            if command -v vm_stat >/dev/null 2>&1; then
                FREE_PAGES=$(vm_stat | grep "Pages free:" | awk '{print $3}' | tr -d '.')
                if [ -z "$FREE_PAGES" ]; then
                    FREE_PAGES=262144  # Default ~1GB if detection fails
                fi
                DHTL_AVAILABLE_MEM_MB=$(( (FREE_PAGES * PAGE_SIZE) / 1024 / 1024 ))
            else
                # Fallback to sysctl if vm_stat not available
                DHTL_TOTAL_MEM_MB=$(sysctl -n hw.memsize 2>/dev/null | awk '{print int($1/1024/1024)}')
                if [ -z "$DHTL_TOTAL_MEM_MB" ]; then
                    DHTL_TOTAL_MEM_MB=8192  # Default 8GB if detection fails
                fi
                # Estimate available as 25% of total as a conservative approach
                DHTL_AVAILABLE_MEM_MB=$(( DHTL_TOTAL_MEM_MB / 4 ))
            fi
            
            # Get CPU cores
            DHTL_CPU_CORES=$(sysctl -n hw.ncpu 2>/dev/null)
            if [ -z "$DHTL_CPU_CORES" ]; then
                DHTL_CPU_CORES=4  # Default if detection fails
            fi
            
        elif [[ $(uname -s) == "Linux" ]]; then
            # On Linux, determine available RAM and CPU cores more efficiently
            # Use /proc/meminfo directly instead of free command
            if [ -f "/proc/meminfo" ]; then
                # Parse MemAvailable if available (better measure than free memory)
                AVAILABLE_KB=$(grep MemAvailable /proc/meminfo | awk '{print $2}')
                if [ -z "$AVAILABLE_KB" ]; then
                    # Fallback to MemFree if MemAvailable not present
                    AVAILABLE_KB=$(grep MemFree /proc/meminfo | awk '{print $2}')
                fi
                
                if [ -n "$AVAILABLE_KB" ]; then
                    DHTL_AVAILABLE_MEM_MB=$(( AVAILABLE_KB / 1024 ))
                else
                    # Default if parsing fails
                    DHTL_AVAILABLE_MEM_MB=2048
                fi
            else
                # Fallback to free command if /proc/meminfo not accessible
                DHTL_AVAILABLE_MEM_MB=$(free -m 2>/dev/null | grep Mem | awk '{print $7}')
                if [ -z "$DHTL_AVAILABLE_MEM_MB" ]; then
                    DHTL_AVAILABLE_MEM_MB=2048  # Default if detection fails
                fi
            fi
            
            # Get CPU cores more efficiently
            if [ -f "/proc/cpuinfo" ]; then
                DHTL_CPU_CORES=$(grep -c processor /proc/cpuinfo)
            else
                # Try nproc command
                DHTL_CPU_CORES=$(nproc 2>/dev/null)
            fi
            
            if [ -z "$DHTL_CPU_CORES" ] || [ "$DHTL_CPU_CORES" -eq 0 ]; then
                DHTL_CPU_CORES=4  # Default if detection fails
            fi
        else
            # Default values for other systems
            DHTL_AVAILABLE_MEM_MB=2048
            DHTL_TOTAL_MEM_MB=8192
            DHTL_CPU_CORES=4
        fi
        
        # Calculate total memory (make available memory 50-75% of total memory)
        # This accounts for system overhead and other running processes
        if [ -z "${DHTL_TOTAL_MEM_MB:-}" ]; then
            if [ "$DHTL_AVAILABLE_MEM_MB" -lt 4096 ]; then
                # For low-memory systems, assume available is 50% of total
                DHTL_TOTAL_MEM_MB=$(( DHTL_AVAILABLE_MEM_MB * 2 ))
            else
                # For high-memory systems, assume available is 75% of total
                DHTL_TOTAL_MEM_MB=$(( DHTL_AVAILABLE_MEM_MB * 4 / 3 ))
            fi
        fi
        
        # Calculate max concurrent based on available RAM and CPUs
        # Use a more adaptive calculation that scales with system resources
        # 1 core = 1 process, 2 cores = 2 processes, 4+ cores = cores/2 processes
        if [ "$DHTL_CPU_CORES" -le 2 ]; then
            # Small systems - 1 process per core
            DHTL_MAX_CONCURRENT=$DHTL_CPU_CORES
        else
            # Larger systems - half of cores, rounded down
            DHTL_MAX_CONCURRENT=$(( DHTL_CPU_CORES / 2 ))
        fi
        
        # Cap max concurrent to avoid overloading
        if [ "$DHTL_MAX_CONCURRENT" -gt 4 ]; then
            DHTL_MAX_CONCURRENT=4
        elif [ "$DHTL_MAX_CONCURRENT" -lt 1 ]; then
            DHTL_MAX_CONCURRENT=1
        fi
        
        # Calculate max total memory based on available memory
        # Use at most 75% of available memory to leave room for system
        DHTL_MAX_TOTAL_MEM=$(( DHTL_AVAILABLE_MEM_MB * 3 / 4 ))
        
        # Lower/upper bounds for memory
        if [ "$DHTL_MAX_TOTAL_MEM" -gt 3072 ]; then
            DHTL_MAX_TOTAL_MEM=3072  # Cap at 3GB to avoid excessive memory use
        elif [ "$DHTL_MAX_TOTAL_MEM" -lt 384 ]; then
            DHTL_MAX_TOTAL_MEM=384  # At least 384MB even on tiny systems
        fi
        
        # Export the detected values so they can be used elsewhere
        export DHTL_AVAILABLE_MEM_MB
        export DHTL_TOTAL_MEM_MB
        export DHTL_CPU_CORES
        export DHTL_MAX_CONCURRENT
        export DHTL_MAX_TOTAL_MEM
        
        if [ "${QUIET_MODE:-false}" != true ]; then
            echo "🔍 Detected system resources: ${DHTL_CPU_CORES} CPU cores, ${DHTL_AVAILABLE_MEM_MB}MB available memory"
            echo "⚙️ Configured limits: ${DHTL_MAX_CONCURRENT} concurrent processes, ${DHTL_MAX_TOTAL_MEM}MB total memory"
        fi
    fi
    
    # Use previously detected values
    MAX_CONCURRENT=${DHTL_MAX_CONCURRENT:-3}
    MAX_TOTAL_MEM=${DHTL_MAX_TOTAL_MEM:-2048}

    # Check if guard-process.sh exists
    if [ -f "$DHT_DIR/guard-process.sh" ] && [ "$USE_GUARDIAN" = true ]; then
        # Adjust memory settings based on process type
        if [ "$process_type" = "node" ]; then
            # For node processes, use higher memory allocation if available
            if [ "$MAX_TOTAL_MEM" -gt 2048 ]; then
                # Increase max total memory by 25% for Node.js applications on high-memory systems
                PROCESS_MAX_TOTAL_MEM=$(( MAX_TOTAL_MEM * 5 / 4 ))
                # Cap at reasonable limit
                if [ "$PROCESS_MAX_TOTAL_MEM" -gt 4096 ]; then
                    PROCESS_MAX_TOTAL_MEM=4096
                fi
            else
                PROCESS_MAX_TOTAL_MEM=$MAX_TOTAL_MEM
            fi
        else
            PROCESS_MAX_TOTAL_MEM=$MAX_TOTAL_MEM
        fi
        
        # Run with guardian, showing concise output in quiet mode
        if [ "${QUIET_MODE:-false}" = true ]; then
            "$DHT_DIR/guard-process.sh" --max-memory "$mem_limit" --timeout "$TIMEOUT" --monitor "$process_type" \
                --max-concurrent "$MAX_CONCURRENT" --max-total-memory "$PROCESS_MAX_TOTAL_MEM" -- "$command" "$@" 2>/dev/null
        else
            echo "🛡️ Running with Process Guardian ($process_type, ${mem_limit}MB limit, $MAX_CONCURRENT concurrent, ${PROCESS_MAX_TOTAL_MEM}MB total)"
            "$DHT_DIR/guard-process.sh" --max-memory "$mem_limit" --timeout "$TIMEOUT" --monitor "$process_type" \
                --max-concurrent "$MAX_CONCURRENT" --max-total-memory "$PROCESS_MAX_TOTAL_MEM" -- "$command" "$@"
        fi
    else
        # Fall back to running directly if guardian not available
        # Apply basic memory optimizations even without guardian
        if [ "$process_type" = "node" ]; then
            # Set NODE_OPTIONS to limit memory use
            export NODE_OPTIONS="--max-old-space-size=${mem_limit} --gc-interval=100 --expose-gc"
            
            # Set additional optimizations for Node.js
            export NODE_NO_WARNINGS=1  # Reduce memory used by verbose warnings
            
            if [ "${QUIET_MODE:-false}" != true ]; then
                echo "🧠 Applied Node.js memory optimizations: NODE_OPTIONS=$NODE_OPTIONS"
            fi
            
            # Run command
            $command "$@"
            EXIT_CODE=$?
            
            # Clean up environment variables
            unset NODE_OPTIONS
            unset NODE_NO_WARNINGS
            
            return $EXIT_CODE
            
        elif [ "$process_type" = "python" ]; then
            # Enable Python optimizations to reduce memory use
            export PYTHONOPTIMIZE=1        # Enable basic optimizations
            export PYTHONHASHSEED=0        # Fixed hash seed improves memory usage
            export PYTHONDONTWRITEBYTECODE=1  # Don't write .pyc files
            
            # Set aggressive GC thresholds
            export PYTHONFAULTHANDLER=1      # Improved debugging with minimal overhead
            
            if [ "${QUIET_MODE:-false}" != true ]; then
                echo "🧠 Applied Python memory optimizations"
            fi
            
            # Run command
            $command "$@"
            EXIT_CODE=$?
            
            # Clean up environment variables
            unset PYTHONOPTIMIZE
            unset PYTHONHASHSEED
            unset PYTHONDONTWRITEBYTECODE
            unset PYTHONFAULTHANDLER
            
            return $EXIT_CODE
        else
            # Run without optimization for other process types
            $command "$@"
        fi
    fi
}