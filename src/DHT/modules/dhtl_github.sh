#!/bin/bash
# GitHub CLI Integration Module
#
# This module provides functions for GitHub operations using the gh CLI tool.
# It handles authentication, cloning, forking, and other GitHub operations.

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

# Function to check if gh CLI is installed
gh_is_installed() {
    if command -v gh &> /dev/null; then
        return 0
    else
        return 1
    fi
}

# Function to install gh CLI
install_gh_cli() {
    echo "📦 Installing GitHub CLI (gh)..."
    
    if [[ "$PLATFORM" == "macos" ]]; then
        if command -v brew &> /dev/null; then
            echo "🔄 Installing gh using Homebrew..."
            brew install gh
        else
            echo "❌ Homebrew not found. Please install gh manually: https://cli.github.com/manual/installation"
            return 1
        fi
    elif [[ "$PLATFORM" == "linux" ]]; then
        if command -v apt-get &> /dev/null; then
            echo "🔄 Installing gh using apt..."
            curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
            echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
            sudo apt update
            sudo apt install gh -y
        elif command -v yum &> /dev/null; then
            echo "🔄 Installing gh using yum..."
            sudo yum install 'dnf-command(config-manager)'
            sudo yum config-manager --add-repo https://cli.github.com/packages/rpm/gh-cli.repo
            sudo yum install gh -y
        else
            echo "❌ No supported package manager found. Please install gh manually: https://cli.github.com/manual/installation"
            return 1
        fi
    elif [[ "$PLATFORM" == "windows_unix" || "$PLATFORM" == "windows" ]]; then
        if command -v scoop &> /dev/null; then
            echo "🔄 Installing gh using Scoop..."
            scoop install gh
        elif command -v choco &> /dev/null; then
            echo "🔄 Installing gh using Chocolatey..."
            choco install gh
        else
            echo "❌ No supported package manager found. Please install gh manually: https://cli.github.com/manual/installation"
            return 1
        fi
    else
        echo "❌ Unsupported platform: $PLATFORM. Please install gh manually: https://cli.github.com/manual/installation"
        return 1
    fi
    
    # Check if installation was successful
    if gh_is_installed; then
        echo "✅ GitHub CLI installed successfully."
        return 0
    else
        echo "❌ Failed to install GitHub CLI."
        return 1
    fi
}

# Function to check if gh is authenticated
gh_is_authenticated() {
    if gh auth status &>/dev/null; then
        return 0
    else
        return 1
    fi
}

# Function to authenticate with GitHub
gh_authenticate() {
    echo "🔐 Authenticating with GitHub..."
    
    if gh_is_authenticated; then
        echo "✅ Already authenticated with GitHub."
        return 0
    fi
    
    echo "📌 You need to authenticate with GitHub."
    echo "   This will open your browser for authentication."
    echo ""
    
    # Run gh auth login interactively
    gh auth login
    
    if gh_is_authenticated; then
        echo "✅ Successfully authenticated with GitHub."
        return 0
    else
        echo "❌ Failed to authenticate with GitHub."
        return 1
    fi
}

# Function to ensure gh is ready (installed and authenticated)
ensure_gh_ready() {
    # Check if gh is installed
    if ! gh_is_installed; then
        if ! install_gh_cli; then
            return 1
        fi
    fi
    
    # Check if authenticated
    if ! gh_is_authenticated; then
        if ! gh_authenticate; then
            return 1
        fi
    fi
    
    return 0
}

# Function to clone a repository using gh
gh_clone_repo() {
    local repo_url="$1"
    local target_dir="$2"
    
    if [[ -z "$repo_url" ]]; then
        echo "❌ Repository URL is required."
        return 1
    fi
    
    # Ensure gh is ready
    if ! ensure_gh_ready; then
        echo "❌ GitHub CLI is not ready."
        return 1
    fi
    
    # Extract owner/repo from URL
    local repo_spec
    if [[ "$repo_url" =~ github\.com[:/]([^/]+/[^/]+)(\.git)?$ ]]; then
        repo_spec="${BASH_REMATCH[1]}"
    elif [[ "$repo_url" =~ ^[^/]+/[^/]+$ ]]; then
        repo_spec="$repo_url"
    else
        echo "❌ Invalid GitHub repository URL: $repo_url"
        return 1
    fi
    
    echo "📥 Cloning $repo_spec..."
    
    # Clone the repository
    if [[ -n "$target_dir" ]]; then
        gh repo clone "$repo_spec" "$target_dir"
    else
        gh repo clone "$repo_spec"
    fi
    
    return $?
}

# Function to fork a repository using gh
gh_fork_repo() {
    local repo_url="$1"
    local clone_fork="${2:-true}"
    
    if [[ -z "$repo_url" ]]; then
        echo "❌ Repository URL is required."
        return 1
    fi
    
    # Ensure gh is ready
    if ! ensure_gh_ready; then
        echo "❌ GitHub CLI is not ready."
        return 1
    fi
    
    # Extract owner/repo from URL
    local repo_spec
    if [[ "$repo_url" =~ github\.com[:/]([^/]+/[^/]+)(\.git)?$ ]]; then
        repo_spec="${BASH_REMATCH[1]}"
    elif [[ "$repo_url" =~ ^[^/]+/[^/]+$ ]]; then
        repo_spec="$repo_url"
    else
        echo "❌ Invalid GitHub repository URL: $repo_url"
        return 1
    fi
    
    echo "🍴 Forking $repo_spec..."
    
    # Fork the repository
    if [[ "$clone_fork" == "true" ]]; then
        gh repo fork "$repo_spec" --clone
    else
        gh repo fork "$repo_spec"
    fi
    
    return $?
}

# Function to create a new repository using gh
gh_create_repo() {
    local repo_name="$1"
    local visibility="${2:-private}"
    local description="$3"
    
    if [[ -z "$repo_name" ]]; then
        echo "❌ Repository name is required."
        return 1
    fi
    
    # Ensure gh is ready
    if ! ensure_gh_ready; then
        echo "❌ GitHub CLI is not ready."
        return 1
    fi
    
    echo "📝 Creating repository $repo_name..."
    
    # Build command
    local cmd="gh repo create \"$repo_name\" --$visibility"
    
    if [[ -n "$description" ]]; then
        cmd="$cmd --description \"$description\""
    fi
    
    # Create the repository
    eval "$cmd"
    
    return $?
}

# Function to clone or fork based on permissions
gh_smart_clone() {
    local repo_url="$1"
    local target_dir="$2"
    local prefer_fork="${3:-false}"
    
    if [[ -z "$repo_url" ]]; then
        echo "❌ Repository URL is required."
        return 1
    fi
    
    # Ensure gh is ready
    if ! ensure_gh_ready; then
        echo "❌ GitHub CLI is not ready."
        return 1
    fi
    
    # Extract owner/repo from URL
    local repo_spec
    if [[ "$repo_url" =~ github\.com[:/]([^/]+/[^/]+)(\.git)?$ ]]; then
        repo_spec="${BASH_REMATCH[1]}"
    elif [[ "$repo_url" =~ ^[^/]+/[^/]+$ ]]; then
        repo_spec="$repo_url"
    else
        echo "❌ Invalid GitHub repository URL: $repo_url"
        return 1
    fi
    
    # Get current user
    local current_user=$(gh api user --jq .login)
    local repo_owner="${repo_spec%%/*}"
    
    # Decide whether to clone or fork
    if [[ "$repo_owner" == "$current_user" ]]; then
        # Own repository, just clone
        echo "📥 Cloning your own repository..."
        gh_clone_repo "$repo_url" "$target_dir"
    elif [[ "$prefer_fork" == "true" ]]; then
        # Fork and clone
        echo "🍴 Forking and cloning repository..."
        gh_fork_repo "$repo_url" true
    else
        # Just clone
        echo "📥 Cloning repository..."
        gh_clone_repo "$repo_url" "$target_dir"
    fi
    
    return $?
}

# Function to check repository status
gh_repo_status() {
    local repo_dir="${1:-$PWD}"
    
    # Ensure gh is ready
    if ! ensure_gh_ready; then
        echo "❌ GitHub CLI is not ready."
        return 1
    fi
    
    # Change to repo directory
    local original_dir=$(pwd)
    cd "$repo_dir" || {
        echo "❌ Failed to change to repository directory: $repo_dir"
        return 1
    }
    
    # Check if it's a git repository
    if ! git rev-parse --git-dir &>/dev/null; then
        echo "❌ Not a git repository: $repo_dir"
        cd "$original_dir"
        return 1
    fi
    
    # Get repository info
    echo "📊 Repository Status:"
    echo ""
    
    # Use gh to get repo info
    if gh repo view --json name,owner,description,defaultBranch,isPrivate,isFork,parent &>/dev/null; then
        gh repo view --json name,owner,description,defaultBranch,isPrivate,isFork,parent | jq -r '
            "Repository: \(.owner.login)/\(.name)",
            "Description: \(.description // "No description")",
            "Default Branch: \(.defaultBranch)",
            "Private: \(.isPrivate)",
            "Fork: \(.isFork)",
            if .isFork then "Parent: \(.parent.owner.login)/\(.parent.name)" else empty end
        '
    else
        echo "⚠️  Not a GitHub repository or no remote configured."
        git remote -v
    fi
    
    echo ""
    echo "Git Status:"
    git status --short
    
    cd "$original_dir"
    return 0
}

# Clone command that uses gh for GitHub repos
clone_command() {
    local repo_url="$1"
    local target_dir="$2"
    
    if [[ -z "$repo_url" ]]; then
        echo "❌ Repository URL is required."
        echo "Usage: dhtl clone <repository-url> [target-directory]"
        return 1
    fi
    
    # Check if it's a GitHub URL
    if [[ "$repo_url" =~ github\.com ]]; then
        echo "🐙 Detected GitHub repository. Using GitHub CLI..."
        gh_smart_clone "$repo_url" "$target_dir" false
    else
        echo "📥 Cloning non-GitHub repository..."
        if [[ -n "$target_dir" ]]; then
            git clone "$repo_url" "$target_dir"
        else
            git clone "$repo_url"
        fi
    fi
    
    return $?
}

# Fork command that uses gh
fork_command() {
    local repo_url="$1"
    
    if [[ -z "$repo_url" ]]; then
        echo "❌ Repository URL is required."
        echo "Usage: dhtl fork <repository-url>"
        return 1
    fi
    
    # Check if it's a GitHub URL
    if [[ "$repo_url" =~ github\.com ]]; then
        gh_fork_repo "$repo_url" true
    else
        echo "❌ Fork is only supported for GitHub repositories."
        return 1
    fi
    
    return $?
}