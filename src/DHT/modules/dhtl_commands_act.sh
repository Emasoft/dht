#!/bin/bash
# dhtl_commands_act.sh - Act integration commands for DHT
#
# This file contains functions for running GitHub Actions locally using act.
# It integrates with the Python act_integration module.

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

# ===== Act Command =====

act_command() {
    local event="${1:-push}"
    local job="$2"
    local list_only=false
    local setup_only=false
    local use_container=false
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -l|--list)
                list_only=true
                shift
                ;;
            --setup-only)
                setup_only=true
                shift
                ;;
            -c|--container)
                use_container=true
                shift
                ;;
            -e|--event)
                event="$2"
                shift 2
                ;;
            -j|--job)
                job="$2"
                shift 2
                ;;
            -h|--help)
                echo "Usage: dhtl act [OPTIONS] [EVENT] [JOB]"
                echo ""
                echo "Run GitHub Actions locally using act"
                echo ""
                echo "Arguments:"
                echo "  EVENT    GitHub event to simulate (default: push)"
                echo "  JOB      Specific job to run (optional)"
                echo ""
                echo "Options:"
                echo "  -l, --list        List workflows and exit"
                echo "  --setup-only      Only setup act environment"
                echo "  -c, --container   Run act inside a container for isolation"
                echo "  -e, --event       Specify event (push, pull_request, etc.)"
                echo "  -j, --job         Run specific job"
                echo "  -h, --help        Show this help message"
                echo ""
                echo "Examples:"
                echo "  dhtl act                    # Run default push event"
                echo "  dhtl act pull_request       # Run pull_request event"
                echo "  dhtl act -j test            # Run specific 'test' job"
                echo "  dhtl act --list             # List all workflows"
                echo "  dhtl act -c                 # Run in container for isolation"
                return 0
                ;;
            *)
                # If not a flag, treat as event
                if [[ -z "$event" && ! "$1" =~ ^- ]]; then
                    event="$1"
                elif [[ -z "$job" && ! "$1" =~ ^- ]]; then
                    job="$1"
                fi
                shift
                ;;
        esac
    done
    
    # Get project root
    PROJECT_ROOT=$(find_project_root)
    if [ -z "$PROJECT_ROOT" ]; then
        echo "❌ ERROR: Not in a project directory."
        return 1
    fi
    
    # Build Python command
    local py_cmd="$PYTHON_CMD $DHT_DIR/modules/act_integration.py \"$PROJECT_ROOT\""
    
    if [ "$list_only" = true ]; then
        py_cmd="$py_cmd --list"
    else
        py_cmd="$py_cmd --event \"$event\""
        
        if [ -n "$job" ]; then
            py_cmd="$py_cmd --job \"$job\""
        fi
        
        if [ "$setup_only" = true ]; then
            py_cmd="$py_cmd --setup-only"
        fi
        
        if [ "$use_container" = true ]; then
            py_cmd="$py_cmd --container"
        fi
    fi
    
    # Run the Python act integration
    echo "🎬 DHT Act Integration"
    echo "📁 Project: $(basename "$PROJECT_ROOT")"
    echo ""
    
    # Use process guardian for Python execution
    ensure_process_guardian
    run_with_guardian $py_cmd "act" "$PYTHON_MEM_LIMIT"
    
    return $?
}

# ===== CI/CD Test Command =====

cicd_test_command() {
    echo "🧪 Testing CI/CD Pipeline Locally"
    echo ""
    
    # This is an alias for act with common CI/CD testing options
    act_command "$@"
}

# ===== Workflow Command =====

workflow_command() {
    local action="${1:-list}"
    shift
    
    case "$action" in
        list)
            act_command --list
            ;;
        run)
            act_command "$@"
            ;;
        test)
            # Test all workflows
            echo "🔄 Testing all GitHub workflows..."
            act_command push
            if [ $? -eq 0 ]; then
                echo "✅ Push workflow passed"
            fi
            
            act_command pull_request
            if [ $? -eq 0 ]; then
                echo "✅ Pull request workflow passed"
            fi
            ;;
        setup)
            act_command --setup-only
            ;;
        *)
            echo "Unknown workflow action: $action"
            echo "Available actions: list, run, test, setup"
            return 1
            ;;
    esac
}

# ===== GH Act Extension Check =====

check_gh_act_extension() {
    if command -v gh &> /dev/null; then
        # Check if act extension is installed
        if gh extension list 2>/dev/null | grep -q "nektos/gh-act"; then
            echo "✅ gh act extension is installed"
            return 0
        else
            echo "ℹ️  gh act extension not installed"
            echo "   Install with: gh extension install https://github.com/nektos/gh-act"
            return 1
        fi
    else
        echo "⚠️  GitHub CLI (gh) not installed"
        return 2
    fi
}

# ===== Act Installation Helper =====

install_act_command() {
    echo "📦 Installing act for local GitHub Actions testing..."
    echo ""
    
    # Check platform
    case "$(uname -s)" in
        Darwin)
            if command -v brew &> /dev/null; then
                echo "🍺 Installing act with Homebrew..."
                brew install act
            else
                echo "❌ Homebrew not found. Install from: https://brew.sh"
                return 1
            fi
            ;;
        Linux)
            echo "🐧 Installing act for Linux..."
            curl -s https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash
            ;;
        *)
            echo "❌ Unsupported platform. Visit: https://github.com/nektos/act"
            return 1
            ;;
    esac
    
    # Also install gh extension if gh is available
    if command -v gh &> /dev/null; then
        echo ""
        echo "🔄 Installing gh act extension..."
        gh extension install https://github.com/nektos/gh-act
    fi
    
    echo ""
    echo "✅ Act installation complete!"
    echo "   Run 'dhtl act' to test your GitHub workflows locally"
    
    return 0
}