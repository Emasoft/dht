#!/bin/bash
# Standalone Commands Module
#
# This module provides standalone python and node commands for DHT.

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

# Python command
python_command() {
    log_info "🐍 Running Python script with resource management..."

    # Get the script and arguments
    local script_args=("$@")

    # Ensure process guardian is running
    ensure_process_guardian

    # Get the Python interpreter path using the canonical function
    local python_interpreter
    python_interpreter=$(get_python_cmd)
    if [[ -z "$python_interpreter" ]]; then
        log_error "Python interpreter not found. Cannot execute Python script." $ERR_COMMAND_NOT_FOUND
        return $ERR_COMMAND_NOT_FOUND
    fi
    log_debug "Using Python interpreter: $python_interpreter"

    # Run the script with guardian
    run_with_guardian "$python_interpreter" "python" "$PYTHON_MEM_LIMIT" "${script_args[@]}"
    return $?
}

# Node command
node_command() {
    log_info "🟢 Running Node.js script with resource management..."

    # Get the script and arguments
    local script_args=("$@")

    # Ensure process guardian is running
    ensure_process_guardian

    # Find the Node.js interpreter
    if ! command -v node &> /dev/null; then
        log_error "Node.js not found. Please install Node.js." $ERR_COMMAND_NOT_FOUND
        return $ERR_COMMAND_NOT_FOUND
    fi

    # Run the script with guardian
    run_with_guardian "node" "node" "$NODE_MEM_LIMIT" "${script_args[@]}"
    return $?
}

# Run command (generic command runner)
run_command() {
    log_info "🚀 Running command with resource management..."

    # Get the command and arguments
    local cmd="$1"
    shift
    local cmd_args=("$@")

    # Ensure process guardian is running
    ensure_process_guardian

    # Check if the command exists
    if ! command -v "$cmd" &> /dev/null; then
        log_error "Command not found: $cmd" $ERR_COMMAND_NOT_FOUND
        return $ERR_COMMAND_NOT_FOUND
    fi

    # Determine the process type
    local process_type="other"
    case "$cmd" in
        python|python3|python2)
            process_type="python"
            ;;
        node|npm|npx)
            process_type="node"
            ;;
        pip|uv)
            process_type="python"
            ;;
        *)
            process_type="other"
            ;;
    esac

    # Determine memory limit based on process type
    local mem_limit="$DEFAULT_MEM_LIMIT"
    if [ "$process_type" = "python" ]; then
        mem_limit="$PYTHON_MEM_LIMIT"
    elif [ "$process_type" = "node" ]; then
        mem_limit="$NODE_MEM_LIMIT"
    fi

    # Run the command with guardian
    run_with_guardian "$cmd" "$process_type" "$mem_limit" "${cmd_args[@]}"
    return $?
}

# Script command - runs scripts from DHT/scripts directory
script_command() {
    local script_name="$1"
    shift
    local script_args=("$@")
    local scripts_dir="$DHT_DIR/scripts"

    if [[ -z "$script_name" ]]; then
        log_info "Available helper scripts in $scripts_dir:"
        ls -1 "$scripts_dir" | sed 's/\.[^.]*$//' # List names without extensions
        return 0
    fi

    # Find the script (try .sh, .py, .bat)
    local script_path=""
    if [[ -f "$scripts_dir/$script_name.sh" ]]; then
        script_path="$scripts_dir/$script_name.sh"
    elif [[ -f "$scripts_dir/$script_name.py" ]]; then
        script_path="$scripts_dir/$script_name.py"
    elif [[ -f "$scripts_dir/$script_name.bat" ]]; then
        script_path="$scripts_dir/$script_name.bat"
    elif [[ -f "$scripts_dir/$script_name" ]]; then # Allow running without extension
        script_path="$scripts_dir/$script_name"
    else
        log_error "Script not found in $scripts_dir: $script_name" $ERR_FILE_NOT_FOUND
        return $ERR_FILE_NOT_FOUND
    fi

    # Ensure the script is executable if it's a shell script
    if [[ "$script_path" == *.sh && ! -x "$script_path" ]]; then
        chmod +x "$script_path"
    fi

    log_info "⚙️ Running script: $script_name"
    log_debug "Script path: $script_path"
    log_debug "Arguments: ${script_args[*]}"

    # Determine how to run based on extension
    if [[ "$script_path" == *.py ]]; then
        local python_interpreter_for_script
        python_interpreter_for_script=$(get_python_cmd)
        if [[ -z "$python_interpreter_for_script" ]]; then
            log_error "Python interpreter not found. Cannot execute Python script '$script_name'." $ERR_COMMAND_NOT_FOUND
            return $ERR_COMMAND_NOT_FOUND
        fi
        run_with_guardian "$python_interpreter_for_script" "python" "$PYTHON_MEM_LIMIT" "$script_path" "${script_args[@]}"
    elif [[ "$script_path" == *.bat ]]; then
        # Running .bat directly might not work well in bash, try cmd if available
        if command -v cmd &>/dev/null; then
             run_with_guardian cmd "/c" "$script_path" "${script_args[@]}"
        else
             log_error "Cannot execute .bat script: 'cmd' not found." $ERR_COMMAND_NOT_FOUND
             return $ERR_COMMAND_NOT_FOUND
        fi
    else # Assume shell script or other executable
        run_with_guardian "$script_path" "script" "$DEFAULT_MEM_LIMIT" "${script_args[@]}"
    fi

    return $?
}
