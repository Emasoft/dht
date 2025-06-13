#!/bin/bash
# dhtl_commands_workflows.sh - GitHub workflows commands for DHT
#
# This file contains functions for working with GitHub Actions workflows.
# Replaces the ambiguous 'act' command with clearer workflow subcommands.

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

# ===== Main Workflows Command =====

workflows_command() {
    local subcommand="${1:-help}"
    shift
    
    case "$subcommand" in
        lint)
            workflows_lint_command "$@"
            ;;
        run)
            workflows_run_command "$@"
            ;;
        run-in-container|run_in_container)
            workflows_run_in_container_command "$@"
            ;;
        list)
            workflows_list_command "$@"
            ;;
        setup)
            workflows_setup_command "$@"
            ;;
        test)
            workflows_test_command "$@"
            ;;
        help|--help|-h)
            workflows_help_command
            ;;
        *)
            echo "Unknown workflows subcommand: $subcommand"
            echo ""
            workflows_help_command
            return 1
            ;;
    esac
}

# ===== Workflows Lint Command =====

workflows_lint_command() {
    local use_docker=false
    local docker_tag="latest"
    local color=true
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --docker)
                use_docker=true
                shift
                ;;
            --docker-tag)
                docker_tag="$2"
                shift 2
                ;;
            --no-color)
                color=false
                shift
                ;;
            -h|--help)
                echo "Usage: dhtl workflows lint [OPTIONS]"
                echo ""
                echo "Lint GitHub Actions workflows for syntax errors"
                echo ""
                echo "Options:"
                echo "  --docker          Use actionlint Docker image"
                echo "  --docker-tag TAG  Docker image tag (default: latest)"
                echo "  --no-color        Disable colored output"
                echo "  -h, --help        Show this help message"
                echo ""
                echo "Examples:"
                echo "  dhtl workflows lint                 # Use local actionlint"
                echo "  dhtl workflows lint --docker        # Use Docker image"
                echo ""
                echo "Note: This performs static analysis only."
                echo "      Use 'dhtl workflows run' to execute workflows."
                return 0
                ;;
            *)
                echo "Unknown option: $1"
                return 1
                ;;
        esac
    done
    
    # Get project root
    PROJECT_ROOT=$(find_project_root)
    if [ -z "$PROJECT_ROOT" ]; then
        echo "❌ ERROR: Not in a project directory."
        return 1
    fi
    
    echo "🔍 Linting GitHub Actions workflows..."
    echo "📁 Project: $(basename "$PROJECT_ROOT")"
    echo ""
    
    # Check for workflows
    if [ ! -d "$PROJECT_ROOT/.github/workflows" ]; then
        echo "ℹ️  No workflows found in .github/workflows/"
        return 0
    fi
    
    # Count workflow files
    workflow_count=$(find "$PROJECT_ROOT/.github/workflows" -name "*.yml" -o -name "*.yaml" | wc -l | tr -d ' ')
    echo "Found $workflow_count workflow file(s)"
    echo ""
    
    if [ "$use_docker" = true ]; then
        echo "🐳 Using actionlint Docker image (rhysd/actionlint:$docker_tag)"
        
        # Check if Docker is available
        if ! command -v docker &> /dev/null; then
            echo "❌ Docker not found. Install Docker or use local actionlint."
            return 1
        fi
        
        # Pull image if needed
        echo "Pulling Docker image..."
        docker pull "rhysd/actionlint:$docker_tag" || {
            echo "❌ Failed to pull Docker image"
            return 1
        }
        
        # Run actionlint in Docker
        docker_cmd="docker run --rm -v \"$PROJECT_ROOT:/repo\" --workdir /repo rhysd/actionlint:$docker_tag"
        
        if [ "$color" = true ]; then
            docker_cmd="$docker_cmd -color"
        fi
        
        eval $docker_cmd
    else
        # Use local actionlint
        if ! command -v actionlint &> /dev/null; then
            echo "❌ actionlint not found locally."
            echo ""
            echo "Install options:"
            echo "  1. brew install actionlint"
            echo "  2. Use Docker: dhtl workflows lint --docker"
            return 1
        fi
        
        # Run local actionlint
        cd "$PROJECT_ROOT"
        if [ "$color" = true ]; then
            actionlint -color
        else
            actionlint
        fi
    fi
    
    return $?
}

# ===== Workflows Run Command =====

workflows_run_command() {
    local event="${1:-push}"
    local job=""
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -e|--event)
                event="$2"
                shift 2
                ;;
            -j|--job)
                job="$2"
                shift 2
                ;;
            -h|--help)
                echo "Usage: dhtl workflows run [OPTIONS] [EVENT]"
                echo ""
                echo "Run GitHub Actions workflows locally using act"
                echo ""
                echo "Arguments:"
                echo "  EVENT             GitHub event to simulate (default: push)"
                echo ""
                echo "Options:"
                echo "  -e, --event       Specify event type"
                echo "  -j, --job         Run specific job"
                echo "  -h, --help        Show this help message"
                echo ""
                echo "Examples:"
                echo "  dhtl workflows run                  # Run push event"
                echo "  dhtl workflows run pull_request     # Run PR event"
                echo "  dhtl workflows run -j test          # Run specific job"
                return 0
                ;;
            *)
                if [[ ! "$1" =~ ^- ]]; then
                    event="$1"
                fi
                shift
                ;;
        esac
    done
    
    # Call the act integration
    echo "🚀 Running GitHub Actions workflows locally..."
    act_command "$event" "$job"
}

# ===== Workflows Run in Container Command =====

workflows_run_in_container_command() {
    local event="${1:-push}"
    local job=""
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -e|--event)
                event="$2"
                shift 2
                ;;
            -j|--job)
                job="$2"
                shift 2
                ;;
            -h|--help)
                echo "Usage: dhtl workflows run-in-container [OPTIONS] [EVENT]"
                echo ""
                echo "Run workflows in isolated container environment"
                echo ""
                echo "This provides the most accurate CI/CD simulation by"
                echo "running act inside a container with all dependencies."
                echo ""
                echo "Arguments:"
                echo "  EVENT             GitHub event to simulate (default: push)"
                echo ""
                echo "Options:"
                echo "  -e, --event       Specify event type"
                echo "  -j, --job         Run specific job"
                echo "  -h, --help        Show this help message"
                echo ""
                echo "Examples:"
                echo "  dhtl workflows run-in-container"
                echo "  dhtl workflows run-in-container pull_request"
                return 0
                ;;
            *)
                if [[ ! "$1" =~ ^- ]]; then
                    event="$1"
                fi
                shift
                ;;
        esac
    done
    
    # Call act with container flag
    echo "🐳 Running workflows in container-isolated environment..."
    act_command --container "$event" "$job"
}

# ===== Workflows List Command =====

workflows_list_command() {
    echo "📋 Listing GitHub Actions workflows..."
    act_command --list
}

# ===== Workflows Setup Command =====

workflows_setup_command() {
    echo "🔧 Setting up GitHub Actions environment..."
    act_command --setup-only
}

# ===== Workflows Test Command =====

workflows_test_command() {
    echo "🧪 Testing all GitHub Actions workflows..."
    echo ""
    
    # First lint the workflows
    echo "Step 1: Linting workflows for syntax errors..."
    echo "─────────────────────────────────────────────"
    workflows_lint_command
    
    if [ $? -ne 0 ]; then
        echo ""
        echo "❌ Workflow linting failed. Fix syntax errors before running."
        return 1
    fi
    
    echo ""
    echo "Step 2: Running workflows locally..."
    echo "────────────────────────────────────"
    
    # Test push event
    echo ""
    echo "Testing push event..."
    workflows_run_command push
    
    # Test pull_request event
    echo ""
    echo "Testing pull_request event..."
    workflows_run_command pull_request
    
    echo ""
    echo "✅ Workflow testing complete!"
}

# ===== Workflows Help Command =====

workflows_help_command() {
    cat << EOF
Usage: dhtl workflows <subcommand> [options]

Manage and test GitHub Actions workflows

Subcommands:
  lint               Validate workflow syntax with actionlint
  run                Execute workflows locally with act
  run-in-container   Execute workflows in isolated container
  list               List all workflows and jobs
  setup              Setup act environment
  test               Lint and run all workflows
  help               Show this help message

Examples:
  dhtl workflows lint                    # Check syntax errors
  dhtl workflows lint --docker           # Use actionlint Docker image
  dhtl workflows run                     # Run push event
  dhtl workflows run pull_request        # Run PR event
  dhtl workflows run-in-container        # Run in isolation
  dhtl workflows test                    # Full test suite

Understanding the tools:
  • actionlint: Static analysis, finds syntax errors (fast)
  • act: Executes workflows, runs actual commands (slower)

Best practice workflow:
  1. dhtl workflows lint     # Check syntax first
  2. dhtl workflows run      # Then test execution
EOF
}

# ===== Legacy act command (for compatibility) =====

act_command() {
    echo "⚠️  'dhtl act' is deprecated. Use the new commands:"
    echo "  • dhtl workflows lint     - Check syntax with actionlint"
    echo "  • dhtl workflows run      - Execute with act"
    echo "  • dhtl workflows run-in-container - Run in isolation"
    echo ""
    echo "Forwarding to 'dhtl workflows run' for compatibility..."
    echo ""
    
    # Forward to the Python act integration for now
    local py_cmd="$PYTHON_CMD $DHT_DIR/modules/act_integration.py \"$PROJECT_ROOT\" $@"
    ensure_process_guardian
    run_with_guardian $py_cmd "act" "$PYTHON_MEM_LIMIT"
}