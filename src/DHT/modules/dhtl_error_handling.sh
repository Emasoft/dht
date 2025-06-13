#!/bin/bash
# Error Handling Module
#
# This module provides functions for improved error handling across all DHT modules.

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

# Error types
declare -r ERR_GENERAL=1
declare -r ERR_COMMAND_NOT_FOUND=2
declare -r ERR_MISSING_DEPENDENCY=3
declare -r ERR_INVALID_ARGUMENT=4
declare -r ERR_PERMISSION_DENIED=5
declare -r ERR_FILE_NOT_FOUND=6
declare -r ERR_NETWORK=7
declare -r ERR_TIMEOUT=8
declare -r ERR_RESOURCE_LIMIT=9
declare -r ERR_ENVIRONMENT=10
declare -r ERR_UNEXPECTED=99

# Function to log an error message
log_error() {
    local error_message="$1"
    local error_code="${2:-$ERR_GENERAL}"
    local stack_trace=false

    # Check if stack trace is requested
    if [[ "$3" == "stack_trace" ]]; then
        stack_trace=true
    fi

    # Red error message with emoji
    echo -e "\033[31m❌ ERROR: $error_message\033[0m" >&2

    # Show stack trace if requested
    if [[ "$stack_trace" = true ]]; then
        echo "Stack trace:" >&2
        local i=0
        while caller $i >/dev/null 2>&1; do
            caller $i | awk '{print "  at " $2 ":" $1 " (" $3 ")"}' >&2
            i=$((i + 1))
        done
    fi

    # Log to file if logging is enabled
    if [[ -n "${DHT_LOG_FILE:-}" ]]; then
        mkdir -p "$(dirname "$DHT_LOG_FILE")"
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] [ERROR] [$error_code] $error_message" >> "$DHT_LOG_FILE"

        if [[ "$stack_trace" = true ]]; then
            echo "Stack trace:" >> "$DHT_LOG_FILE"
            local i=0
            while caller $i >/dev/null 2>&1; do
                caller $i | awk '{print "  at " $2 ":" $1 " (" $3 ")"}' >> "$DHT_LOG_FILE"
                i=$((i + 1))
            done
        fi
    fi

    return $error_code
}

# Function to log a warning message
log_warning() {
    local warning_message="$1"

    # Yellow warning message with emoji
    echo -e "\033[33m⚠️ WARNING: $warning_message\033[0m" >&2

    # Log to file if logging is enabled
    if [[ -n "${DHT_LOG_FILE:-}" ]]; then
        mkdir -p "$(dirname "$DHT_LOG_FILE")"
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] [WARNING] $warning_message" >> "$DHT_LOG_FILE"
    fi

    return 0
}

# Function to log an info message
log_info() {
    local info_message="$1"

    # Only show info messages if not in quiet mode
    if [[ "${QUIET_MODE:-false}" != "true" ]]; then
        # Blue info message with emoji
        echo -e "\033[34m🔄 $info_message\033[0m"
    fi

    # Log to file if logging is enabled
    if [[ -n "${DHT_LOG_FILE:-}" ]]; then
        mkdir -p "$(dirname "$DHT_LOG_FILE")"
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] [INFO] $info_message" >> "$DHT_LOG_FILE"
    fi

    return 0
}

# Function to log a success message
log_success() {
    local success_message="$1"

    # Green success message with emoji
    echo -e "\033[32m✅ $success_message\033[0m"

    # Log to file if logging is enabled
    if [[ -n "${DHT_LOG_FILE:-}" ]]; then
        mkdir -p "$(dirname "$DHT_LOG_FILE")"
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] [SUCCESS] $success_message" >> "$DHT_LOG_FILE"
    fi

    return 0
}

# Function to log a debug message
log_debug() {
    local debug_message="$1"

    # Only show debug messages in debug mode
    if [[ "${DEBUG_MODE:-false}" == "true" ]]; then
        # Cyan debug message with emoji
        echo -e "\033[36m🐞 DEBUG: $debug_message\033[0m"
    fi

    # Log to file if logging is enabled
    if [[ -n "${DHT_LOG_FILE:-}" ]]; then
        mkdir -p "$(dirname "$DHT_LOG_FILE")"
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] [DEBUG] $debug_message" >> "$DHT_LOG_FILE"
    fi

    return 0
}

# Function to check for required commands
check_command() {
    local command_name="$1"
    local error_message="${2:-Command '$command_name' not found}"

    if ! command -v "$command_name" >/dev/null 2>&1; then
        log_error "$error_message" $ERR_COMMAND_NOT_FOUND
        return $ERR_COMMAND_NOT_FOUND
    fi

    return 0
}

# Function to check if a required dependency is available
check_dependency() {
    local dependency="$1"
    local error_message="${2:-Dependency '$dependency' not found}"

    case "$dependency" in
        python|python3)
            # Check Python
            if ! command -v python3 >/dev/null 2>&1 && ! command -v python >/dev/null 2>&1; then
                log_error "$error_message" $ERR_MISSING_DEPENDENCY
                return $ERR_MISSING_DEPENDENCY
            fi
            ;;
        node|nodejs)
            # Check Node.js
            if ! command -v node >/dev/null 2>&1; then
                log_error "$error_message" $ERR_MISSING_DEPENDENCY
                return $ERR_MISSING_DEPENDENCY
            fi
            ;;
        git)
            # Check Git
            if ! command -v git &> /dev/null 2>&1; then
                log_error "$error_message" $ERR_MISSING_DEPENDENCY
                return $ERR_MISSING_DEPENDENCY
            fi
            ;;
        uv)
            # Check UV
            if ! command -v uv &> /dev/null; then
                log_error "$error_message" $ERR_MISSING_DEPENDENCY
                return $ERR_MISSING_DEPENDENCY
            fi
            ;;
        *)
            # Generic dependency check
            if ! command -v "$dependency" >/dev/null 2>&1; then
                log_error "$error_message" $ERR_MISSING_DEPENDENCY
                return $ERR_MISSING_DEPENDENCY
            fi
            ;;
    esac

    return 0
}

# Function to validate arguments
validate_argument() {
    local argument="$1"
    local pattern="$2"
    local error_message="${3:-Invalid argument: '$argument'}"

    if ! [[ "$argument" =~ $pattern ]]; then
        log_error "$error_message" $ERR_INVALID_ARGUMENT
        return $ERR_INVALID_ARGUMENT
    fi

    return 0
}

# Function to check if a file exists
check_file() {
    local file_path="$1"
    local error_message="${2:-File not found: '$file_path'}"

    if [[ ! -f "$file_path" ]]; then
        log_error "$error_message" $ERR_FILE_NOT_FOUND
        return $ERR_FILE_NOT_FOUND
    fi

    return 0
}

# Function to check if a directory exists
check_directory() {
    local dir_path="$1"
    local error_message="${2:-Directory not found: '$dir_path'}"

    if [[ ! -d "$dir_path" ]]; then
        log_error "$error_message" $ERR_FILE_NOT_FOUND
        return $ERR_FILE_NOT_FOUND
    fi

    return 0
}

# Function to check if a file is readable
check_readable() {
    local file_path="$1"
    local error_message="${2:-File not readable: '$file_path'}"

    if [[ ! -r "$file_path" ]]; then
        log_error "$error_message" $ERR_PERMISSION_DENIED
        return $ERR_PERMISSION_DENIED
    fi

    return 0
}

# Function to check if a file is writable
check_writable() {
    local file_path="$1"
    local error_message="${2:-File not writable: '$file_path'}"

    if [[ ! -w "$file_path" ]]; then
        log_error "$error_message" $ERR_PERMISSION_DENIED
        return $ERR_PERMISSION_DENIED
    fi

    return 0
}

# Function to check if a directory is writable
check_directory_writable() {
    local dir_path="$1"
    local error_message="${2:-Directory not writable: '$dir_path'}"

    if [[ ! -d "$dir_path" || ! -w "$dir_path" ]]; then
        log_error "$error_message" $ERR_PERMISSION_DENIED
        return $ERR_PERMISSION_DENIED
    fi

    return 0
}

# Function to check if we're in a Git repository
check_git_repository() {
    local repo_path="${1:-.}"
    local error_message="${2:-Not a Git repository: '$repo_path'}"

    if ! git -C "$repo_path" rev-parse --git-dir >/dev/null 2>&1; then
        log_error "$error_message" $ERR_ENVIRONMENT
        return $ERR_ENVIRONMENT
    fi

    return 0
}

# Function to check if the working directory is clean
check_git_clean() {
    local repo_path="${1:-.}"
    local error_message="${2:-Git working directory not clean: '$repo_path'}"

    if ! git -C "$repo_path" diff-index --quiet HEAD --; then
        log_error "$error_message" $ERR_ENVIRONMENT
        return $ERR_ENVIRONMENT
    fi

    return 0
}

# Function to check if a Python module is available
check_python_module() {
    local module_name="$1"
    local error_message="${2:-Python module '$module_name' not found}"
    local python_cmd="${3:-$PYTHON_CMD}"

    if ! "$python_cmd" -c "import $module_name" >/dev/null 2>&1; then
        log_error "$error_message" $ERR_MISSING_DEPENDENCY
        return $ERR_MISSING_DEPENDENCY
    fi

    return 0
}

# Function to check if a Node.js module is available
check_node_module() {
    local module_name="$1"
    local error_message="${2:-Node.js module '$module_name' not found}"

    if ! node -e "require('$module_name')" >/dev/null 2>&1; then
        log_error "$error_message" $ERR_MISSING_DEPENDENCY
        return $ERR_MISSING_DEPENDENCY
    fi

    return 0
}

# Function to check network connectivity
check_network() {
    local host="${1:-google.com}"
    local error_message="${2:-Network connectivity issue, cannot connect to '$host'}"

    if ! ping -c 1 -W 2 "$host" >/dev/null 2>&1; then
        log_error "$error_message" $ERR_NETWORK
        return $ERR_NETWORK
    fi

    return 0
}

# Function to run a command with timeout
run_with_timeout() {
    local timeout="$1"
    local command="$2"
    shift 2
    local args=("$@")

    # Use timeout command if available
    if command -v timeout >/dev/null 2>&1; then
        timeout "$timeout" "$command" "${args[@]}"
        return $?
    else
        # Fallback to manual timeout with background process
        local pid
        local exit_code=0

        # Run command in background
        "$command" "${args[@]}" &
        pid=$!

        # Wait for command to complete or timeout
        local count=0
        while [[ $count -lt $timeout ]]; do
            if ! kill -0 "$pid" 2>/dev/null; then
                # Process completed
                wait "$pid"
                exit_code=$?
                break
            fi
            sleep 1
            count=$((count + 1))
        done

        # If process is still running after timeout, kill it
        if kill -0 "$pid" 2>/dev/null; then
            kill -TERM "$pid" 2>/dev/null
            sleep 1
            if kill -0 "$pid" 2>/dev/null; then
                kill -KILL "$pid" 2>/dev/null
            fi
            log_error "Command timed out after $timeout seconds" $ERR_TIMEOUT
            exit_code=$ERR_TIMEOUT
        fi

        return $exit_code
    fi
}

# Function to handle exit cleanly
handle_exit() {
    local exit_code="$1"
    local message="${2:-}"

    # Clean up temporary files
    if [[ -n "${DHTL_TEMP_FILES:-}" ]]; then
        for temp_file in "${DHTL_TEMP_FILES[@]}"; do
            if [[ -f "$temp_file" ]]; then
                rm -f "$temp_file"
            fi
        done
    fi

    # If a message was provided, log it
    if [[ -n "$message" ]]; then
        if [[ $exit_code -eq 0 ]]; then
            log_success "$message"
        else
            log_error "$message" $exit_code
        fi
    fi

    exit $exit_code
}

# Set up a trap to clean up on exit
trap 'handle_exit $? "Exiting due to interrupt"' INT TERM

# Function to add a temporary file to the cleanup list
add_temp_file() {
    local temp_file="$1"

    if [[ -z "${DHTL_TEMP_FILES:-}" ]]; then
        DHTL_TEMP_FILES=()
    fi

    DHTL_TEMP_FILES+=("$temp_file")
}

# Function to create a temporary file that will be cleaned up on exit
create_temp_file() {
    local prefix="${1:-dhtl}"
    local suffix="${2:-}"

    local temp_file
    temp_file=$(mktemp -t "${prefix}.XXXXXX${suffix}")
    add_temp_file "$temp_file"
    echo "$temp_file"
}

# Function to create a temporary directory that will be cleaned up on exit
create_temp_dir() {
    local prefix="${1:-dhtl}"

    local temp_dir
    temp_dir=$(mktemp -d -t "${prefix}.XXXXXX")
    add_temp_file "$temp_dir"
    echo "$temp_dir"
}
