#!/bin/bash
# UV Integration Module
#
# This module provides functions for UV integration.
# UV is used for Python package management, virtual environments, and running tools.

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

# Function to check if uv is available
uv_is_available() {
    local venv_dir="$1"
    local project_root="${2:-$PROJECT_ROOT}"
    
    if [ -z "$venv_dir" ]; then
        venv_dir=$(find_virtual_env "$project_root")
    fi
    
    # Check for UV in various locations
    if [ -f "$venv_dir/bin/uv" ]; then
        return 0  # uv found in venv
    elif command -v uv &> /dev/null; then
        return 0  # uv found in PATH
    else
        return 1  # uv not found
    fi
}

# Function to get the uv command to use
get_uv_command() {
    local venv_dir="$1"
    local project_root="${2:-$PROJECT_ROOT}"
    
    if [ -z "$venv_dir" ]; then
        venv_dir=$(find_virtual_env "$project_root")
    fi
    
    # Try to find uv in the virtualenv first, then fall back to global
    if [ -f "$venv_dir/bin/uv" ]; then
        echo "$venv_dir/bin/uv"
    elif command -v uv &> /dev/null; then
        echo "uv"
    else
        echo ""
        return 1
    fi
}

# Function to install uv if not already available
install_uv() {
    local venv_dir="$1"
    if [ -z "$venv_dir" ]; then
        venv_dir=$(find_virtual_env "$PROJECT_ROOT")
        if [ -z "$venv_dir" ]; then
            venv_dir="$PROJECT_ROOT/.venv"
        fi
    fi
    
    echo "🔄 Installing uv..."
    
    # Check if we can install globally first
    if ! command -v uv &> /dev/null; then
        echo "🔄 Installing uv globally as fallback..."
        curl -LsSf https://astral.sh/uv/install.sh | sh
    fi
    
    # Now try to install in the virtual environment if it exists
    if [ -d "$venv_dir" ]; then
        if [ -f "$venv_dir/bin/pip" ]; then
            echo "🔄 Installing uv in virtual environment using pip..."
            "$venv_dir/bin/pip" install uv
            if [ -f "$venv_dir/bin/uv" ]; then
                echo "✅ uv installed successfully in virtual environment."
                return 0
            fi
        fi
        
        # If global uv is available, use it to install in the venv
        if command -v uv &> /dev/null; then
            echo "🔄 Installing uv in virtual environment using global uv..."
            # Use pip install via uv to install uv in the venv
            uv pip install --target "$venv_dir/lib/python3.*/site-packages" uv
            if [ -f "$venv_dir/bin/uv" ]; then
                echo "✅ uv installed successfully in virtual environment."
                return 0
            fi
        fi
    fi
    
    if command -v uv &> /dev/null; then
        echo "✅ Global uv is available as fallback."
        return 0
    else
        echo "❌ Failed to install uv."
        return 1
    fi
}

# Function to create a virtual environment using uv
uv_create_venv() {
    local venv_dir="$1"
    local python_version="${2:-}"
    
    if [ -z "$venv_dir" ]; then
        echo "❌ ERROR: venv_dir is required for uv_create_venv."
        return 1
    fi
    
    # Get the uv command
    local UV_CMD=$(get_uv_command)
    if [ -z "$UV_CMD" ]; then
        # Try to install uv first
        install_uv
        UV_CMD=$(get_uv_command)
        if [ -z "$UV_CMD" ]; then
            echo "❌ uv is not available. Cannot create virtual environment."
            return 1
        fi
    fi
    
    # Create the virtual environment
    echo "🔄 Creating virtual environment at $venv_dir using uv..."
    if [ -n "$python_version" ]; then
        # Create with specific Python version
        "$UV_CMD" venv "$venv_dir" --python "$python_version"
    else
        # Create with default Python version
        "$UV_CMD" venv "$venv_dir"
    fi
    
    # Check if creation was successful
    if [ -d "$venv_dir" ] && [ -f "$venv_dir/bin/activate" ]; then
        echo "✅ Virtual environment created successfully."
        return 0
    else
        echo "❌ Failed to create virtual environment."
        return 1
    fi
}

# Function to sync dependencies using uv
uv_sync() {
    local project_dir="$1"
    if [ -z "$project_dir" ]; then
        project_dir="$PROJECT_ROOT"
    fi
    
    # Get the venv directory for this project
    local venv_dir=$(find_virtual_env "$project_dir")
    
    # Get the uv command  
    local UV_CMD=$(get_uv_command "$venv_dir" "$project_dir")
    if [ -z "$UV_CMD" ]; then
        echo "❌ uv is not available. Cannot sync dependencies."
        return 1
    fi
    
    # Save current directory
    local original_dir=$(pwd)
    
    # Change to project directory (uv commands work relative to CWD)
    cd "$project_dir" || {
        echo "❌ Failed to change to project directory: $project_dir"
        return 1
    }
    
    # Check if uv.lock exists
    if [ -f "uv.lock" ]; then
        echo "🔄 Syncing dependencies from uv.lock..."
        if [ -n "$venv_dir" ]; then
            # Run with venv activated
            PATH="$venv_dir/bin:$PATH" VIRTUAL_ENV="$venv_dir" "$UV_CMD" sync
        else
            "$UV_CMD" sync
        fi
        local result=$?
    else
        echo "⚠️ No uv.lock file found. Generating one..."
        
        # Check if pyproject.toml exists
        if [ -f "pyproject.toml" ]; then
            echo "🔄 Generating uv.lock from pyproject.toml..."
            if [ -n "$venv_dir" ]; then
                PATH="$venv_dir/bin:$PATH" VIRTUAL_ENV="$venv_dir" "$UV_CMD" lock
            else
                "$UV_CMD" lock
            fi
            
            if [ $? -ne 0 ]; then
                echo "❌ Failed to generate uv.lock."
                cd "$original_dir"
                return 1
            fi
            
            echo "🔄 Syncing dependencies..."
            if [ -n "$venv_dir" ]; then
                PATH="$venv_dir/bin:$PATH" VIRTUAL_ENV="$venv_dir" "$UV_CMD" sync
            else
                "$UV_CMD" sync
            fi
            local result=$?
        else
            echo "❌ No pyproject.toml found. Cannot generate uv.lock."
            cd "$original_dir"
            return 1
        fi
    fi
    
    # Return to original directory
    cd "$original_dir"
    return ${result:-0}
}

# Function to install a package using uv
uv_pip_install() {
    local package="$1"
    local options="${2:-}"
    local project_dir="${3:-$PROJECT_ROOT}"
    
    if [ -z "$package" ]; then
        echo "❌ ERROR: package is required for uv_pip_install."
        return 1
    fi
    
    # Get the venv directory for this project
    local venv_dir=$(find_virtual_env "$project_dir")
    
    # Get the uv command
    local UV_CMD=$(get_uv_command "$venv_dir" "$project_dir")
    if [ -z "$UV_CMD" ]; then
        echo "❌ uv is not available. Cannot install package."
        return 1
    fi
    
    # Save current directory
    local original_dir=$(pwd)
    
    # Change to project directory
    cd "$project_dir" || {
        echo "❌ Failed to change to project directory: $project_dir"
        return 1
    }
    
    # Install the package
    echo "🔄 Installing $package using uv..."
    if [ -n "$venv_dir" ]; then
        # Run with venv activated
        PATH="$venv_dir/bin:$PATH" VIRTUAL_ENV="$venv_dir" "$UV_CMD" pip install $options "$package"
    else
        "$UV_CMD" pip install $options "$package"
    fi
    local result=$?
    
    # Return to original directory
    cd "$original_dir"
    return $result
}

# Function to run a tool using uv
uv_tool_run() {
    local tool_name="$1"
    shift
    
    if [ -z "$tool_name" ]; then
        echo "❌ ERROR: tool_name is required for uv_tool_run."
        return 1
    fi
    
    # Get the uv command
    local UV_CMD=$(get_uv_command)
    if [ -z "$UV_CMD" ]; then
        echo "❌ uv is not available. Cannot run tool."
        return 1
    fi
    
    # Run the tool
    echo "🔄 Running $tool_name using uv tool run..."
    "$UV_CMD" tool run "$tool_name" "$@"
    return $?
}

# Function to install a tool using uv
uv_tool_install() {
    local tool_name="$1"
    
    if [ -z "$tool_name" ]; then
        echo "❌ ERROR: tool_name is required for uv_tool_install."
        return 1
    fi
    
    # Get the uv command
    local UV_CMD=$(get_uv_command)
    if [ -z "$UV_CMD" ]; then
        echo "❌ uv is not available. Cannot install tool."
        return 1
    fi
    
    # Check if tool is already installed
    if "$UV_CMD" tool list 2>/dev/null | grep -q "$tool_name"; then
        echo "✅ $tool_name is already installed."
        return 0
    fi
    
    # Install the tool
    echo "🔄 Installing $tool_name using uv tool install..."
    "$UV_CMD" tool install "$tool_name"
    return $?
}

# Function to build a package using uv
uv_build() {
    local project_dir="$1"
    if [ -z "$project_dir" ]; then
        project_dir="$PROJECT_ROOT"
    fi
    
    # Get the uv command
    local UV_CMD=$(get_uv_command)
    if [ -z "$UV_CMD" ]; then
        echo "❌ uv is not available. Cannot build package."
        return 1
    fi
    
    # Check if pyproject.toml exists
    if [ ! -f "$project_dir/pyproject.toml" ]; then
        echo "❌ No pyproject.toml found. Cannot build package."
        return 1
    fi
    
    # Build the package
    echo "🔄 Building package using uv..."
    "$UV_CMD" build
    return $?
}

# Main UV command function
uv_command() {
    local subcommand="${1:-help}"
    shift || true
    
    case "$subcommand" in
        setup)
            # Set up UV for the project
            install_uv
            ;;
        venv)
            # Create a virtual environment
            uv_create_venv "$PROJECT_ROOT/.venv" "$@"
            ;;
        sync)
            # Sync dependencies
            uv_sync "$PROJECT_ROOT"
            ;;
        install)
            # Install a package
            uv_pip_install "$@"
            ;;
        tool)
            # Run a tool subcommand
            local tool_cmd="${1:-list}"
            shift || true
            case "$tool_cmd" in
                run)
                    # Run a tool
                    uv_tool_run "$@"
                    ;;
                install)
                    # Install a tool
                    uv_tool_install "$@"
                    ;;
                list)
                    # List installed tools
                    local UV_CMD=$(get_uv_command)
                    if [ -n "$UV_CMD" ]; then
                        "$UV_CMD" tool list
                    else
                        echo "❌ uv is not available. Cannot list tools."
                        return 1
                    fi
                    ;;
                *)
                    echo "❌ Unknown uv tool subcommand: $tool_cmd"
                    echo "Available subcommands: run, install, list"
                    return 1
                    ;;
            esac
            ;;
        build)
            # Build the package
            uv_build "$PROJECT_ROOT"
            ;;
        help)
            # Show help
            echo "UV Command Usage:"
            echo "  dhtl uv [subcommand] [options]"
            echo ""
            echo "Subcommands:"
            echo "  setup       - Set up UV for the project"
            echo "  venv        - Create a virtual environment"
            echo "  sync        - Sync dependencies from lock file"
            echo "  install     - Install a package"
            echo "  tool run    - Run a tool"
            echo "  tool install - Install a tool"
            echo "  tool list   - List installed tools"
            echo "  build       - Build the package"
            echo "  help        - Show this help message"
            ;;
        *)
            echo "❌ Unknown uv subcommand: $subcommand"
            echo "Run 'dhtl uv help' for usage information."
            return 1
            ;;
    esac
}