#!/bin/bash
# Environment module

# ===== Direct Execution Prevention =====
# This script cannot be executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "ERROR: This script is part of a modular system and cannot be executed directly." >&2
    echo "Please use the orchestrator script instead." >&2
    exit 1
fi

detect_active_venv() {
    if [[ -n "$VIRTUAL_ENV" ]]; then
        echo "$VIRTUAL_ENV"
    elif [[ -n "$CONDA_PREFIX" ]]; then
        echo "$CONDA_PREFIX"
    else
        echo ""
    fi
}

find_virtual_env() {
    local project_root="$1"
    local env_name=""
    
    # Check common venv locations
    for dir in ".venv" "venv" "env" ".env"; do
        if [[ -d "$project_root/$dir" && -f "$project_root/$dir/bin/activate" ]]; then
            env_name="$project_root/$dir"
            break
        fi
    done
    
    # If no venv found, look for conda environments
    if [[ -z "$env_name" && -n "$CONDA_PREFIX" ]]; then
        # Check if current conda env is project-specific
        if [[ "$CONDA_PREFIX" == *"$project_root"* ]]; then
            env_name="$CONDA_PREFIX"
        fi
    fi
    
    echo "$env_name"
}

# Function to ensure venv is activated for the current project
ensure_venv_activated() {
    local project_root="${1:-$PROJECT_ROOT}"
    local venv_dir=$(find_virtual_env "$project_root")
    
    # If no venv found, return error
    if [[ -z "$venv_dir" ]]; then
        return 1
    fi
    
    # Check if already in the correct venv
    if [[ -n "$VIRTUAL_ENV" && "$VIRTUAL_ENV" == "$venv_dir" ]]; then
        return 0
    fi
    
    # If in a different venv, we need to handle this carefully
    # For now, we'll just set the environment variables
    # This is safer than sourcing activate scripts in subshells
    export VIRTUAL_ENV="$venv_dir"
    export PATH="$venv_dir/bin:$PATH"
    
    # Unset PYTHONHOME if set
    unset PYTHONHOME
    
    return 0
}

# Function to run command in project venv
run_in_venv() {
    local project_root="${1:-$PROJECT_ROOT}"
    shift  # Remove first argument
    local venv_dir=$(find_virtual_env "$project_root")
    
    if [[ -z "$venv_dir" ]]; then
        # No venv, run command as-is
        "$@"
        return $?
    fi
    
    # Run command with venv's PATH prepended
    PATH="$venv_dir/bin:$PATH" VIRTUAL_ENV="$venv_dir" "$@"
    return $?
}

# NOTE: env_command removed. Canonical version is in dhtl_environment_2.sh
# NOTE: setup_command removed. Canonical version is in dhtl_init.sh
# NOTE: setup_environment removed. Canonical logic is in dhtl_init.sh (setup_uv).
# NOTE: venv_command removed. Redundant with 'dhtl setup' (which calls setup_command from dhtl_init.sh).

