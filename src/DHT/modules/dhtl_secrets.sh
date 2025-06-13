#!/bin/bash
# dhtl_secrets.sh - Secrets Management module for DHT Launcher
# Handles detection, local sourcing, and GitHub checks for required secrets.

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


# Function to check for required secrets and instruct user if missing
# This is the canonical implementation.
check_and_instruct_secrets() {
    local target_dir="$1"
    echo "🔑 Checking for required secrets..."

    # Define required secrets based on project context
    local required_secrets=()
    local search_paths=("$target_dir/tests" "$target_dir/src" "$target_dir/DHT" "$target_dir/.github/workflows")

    # Use find and grep -q for efficiency. -print -quit stops after first match.
    if find "${search_paths[@]}" -type f -exec grep -q -E 'os\.environ\.get\(["'\'']OPENROUTER_API_KEY["'\'']\)' {} \; -print -quit 2>/dev/null | grep -q .; then
        required_secrets+=("OPENROUTER_API_KEY")
    fi
    if find "${search_paths[@]}" -type f -exec grep -q -E 'twine upload|PYPI_API_TOKEN' {} \; -print -quit 2>/dev/null | grep -q .; then
         required_secrets+=("PYPI_API_TOKEN")
    fi
    if find "${search_paths[@]}" -type f -exec grep -q -E 'codecov|CODECOV_TOKEN' {} \; -print -quit 2>/dev/null | grep -q .; then
         required_secrets+=("CODECOV_TOKEN") # Note: Renamed from CODECOV_API_TOKEN for consistency with Codecov tool
    fi
    if command -v gh &>/dev/null || find "$target_dir/.github/workflows" -type f -exec grep -q -E 'secrets\.GITHUB_TOKEN' {} \; -print -quit 2>/dev/null | grep -q .; then
         # GITHUB_TOKEN is usually automatically provided in Actions, but might be needed locally for 'gh'
         required_secrets+=("GITHUB_TOKEN")
    fi

    # Add more checks here based on project dependencies or configurations if needed

    # Remove duplicates
    required_secrets=($(echo "${required_secrets[@]}" | tr ' ' '\n' | sort -u | tr '\n' ' '))

    if [[ ${#required_secrets[@]} -eq 0 ]]; then
        echo "✅ No specific secrets identified as required for this project based on common patterns."
        return 0
    fi

    echo "ℹ️ Required secrets identified (based on common usage patterns): ${required_secrets[*]}"

    local missing_global_secrets=()
    local secrets_to_add_to_env=() # Secrets found globally to potentially add to .env
    local env_file="$target_dir/.env" # File to store secrets for local sourcing

    # Check global environment for secrets
    for secret in "${required_secrets[@]}"; do
        # Use printenv for a potentially more reliable check than ${!secret} in all shells
        if ! printenv "$secret" > /dev/null; then
            missing_global_secrets+=("$secret")
        else
            # Secret found globally, check if it needs to be added/updated in .env
            local secret_value
            secret_value=$(printenv "$secret")
            local escaped_value
            # More robust escaping for various special characters
            escaped_value=$(printf '%s\n' "$secret_value" | sed -e 's/\\/\\\\/g' -e 's/'"'"'/'"'"'\\'"'"''"'"'/g' -e 's/"/\\"/g')
            local export_line="export $secret='$escaped_value'"

            # Check if the variable is already defined in .env
            if [[ -f "$env_file" ]] && grep -q -E "^export ${secret}=" "$env_file"; then
                 # Variable exists in .env, don't overwrite automatically
                 # Optionally, could compare values and prompt user if different
                 : # No action needed, preserve user's local .env setting
            else
                 # Variable not in .env, add it
                 secrets_to_add_to_env+=("$export_line")
            fi
        fi
    done

    # Handle missing secrets
    if [[ ${#missing_global_secrets[@]} -gt 0 ]]; then
        echo "⚠️ The following required secrets are not set in your global environment:" >&2
        for secret in "${missing_global_secrets[@]}"; do
            echo "   - $secret" >&2
        done
        echo "   Please set them globally (e.g., in ~/.zshrc, ~/.bashrc) or locally in the '$env_file' file." >&2
        echo "   The virtual environment activation will automatically source '$env_file' if it exists." >&2
        echo "   Example line for .env file:" >&2
        echo "   export OPENROUTER_API_KEY='your_key_here'" >&2
        # Do not fail setup, but warn user
    fi

    # Create or update the .env file for local sourcing
    if [[ ${#secrets_to_add_to_env[@]} -gt 0 ]]; then
        echo "📝 Adding detected global secrets to $env_file for local use (existing variables in .env preserved)..."
        # Append new secrets to the .env file
        printf "%s\n" "${secrets_to_add_to_env[@]}" >> "$env_file"
        # Ensure .env is in .gitignore
        if [[ -f "$target_dir/.gitignore" ]] && ! grep -q -E "^/?\.env$" "$target_dir/.gitignore"; then
             echo "/.env" >> "$target_dir/.gitignore"
        elif [[ ! -f "$target_dir/.gitignore" ]]; then
             echo "/.env" > "$target_dir/.gitignore"
        fi
        echo "✅ Secrets sourced from global environment added/updated in $env_file."
        echo "   These will be available when the virtual environment is activated."
    elif [[ -f "$env_file" ]]; then
         echo "ℹ️ $env_file exists. No new secrets detected in global environment to add."
    else
         echo "ℹ️ No required secrets detected in global environment. $env_file not created/updated."
    fi


    # Check GitHub repository secrets (if gh is available and in a git repo)
    if command -v gh &>/dev/null && git -C "$target_dir" rev-parse --is-inside-work-tree &> /dev/null; then
        echo "🔄 Checking GitHub repository secrets..."
        local repo_name
        repo_name=$(gh repo view --json nameWithOwner --jq .nameWithOwner 2>/dev/null)
        if [[ -n "$repo_name" ]]; then
            local missing_gh_secrets=()
            local existing_gh_secrets
            # Fetch secrets list, handle potential errors
            existing_gh_secrets=$(gh secret list -R "$repo_name" --json name --jq '.[].name' 2>/dev/null || echo "ERROR_FETCHING_SECRETS")

            if [[ "$existing_gh_secrets" == "ERROR_FETCHING_SECRETS" ]]; then
                 echo "⚠️ Could not fetch secrets list from GitHub repository '$repo_name'. Skipping check." >&2
                 echo "   Ensure you have permissions and 'gh' CLI is authenticated." >&2
            else
                for secret in "${required_secrets[@]}"; do
                     # GITHUB_TOKEN is usually automatically available in Actions, don't check for it as a repo secret
                     if [[ "$secret" == "GITHUB_TOKEN" ]]; then continue; fi

                     # Check if secret exists in the list
                     if ! echo "$existing_gh_secrets" | grep -q "^${secret}$"; then
                         missing_gh_secrets+=("$secret")
                     fi
                done

                if [[ ${#missing_gh_secrets[@]} -gt 0 ]]; then
                    echo "⚠️ The following required secrets are MISSING in your GitHub repository secrets ('$repo_name'):" >&2
                     for secret in "${missing_gh_secrets[@]}"; do
                        echo "   - $secret" >&2
                    done
                    echo "   These are likely needed for GitHub Actions workflows (e.g., tests, publishing)." >&2
                    echo "   Please add them using the GitHub UI or the 'gh' CLI:" >&2
                    echo "   Example: gh secret set $secret --repo $repo_name --body \"\$(printenv ${secret})\"" >&2
                    echo "   (Ensure the corresponding variable is set in your local environment first)" >&2
                else
                    echo "✅ All required secrets appear to be set in the GitHub repository ('$repo_name')."
                fi
            fi
        else
             echo "⚠️ Could not determine GitHub repository name. Skipping GitHub secrets check." >&2
        fi
    else
         echo "ℹ️ GitHub CLI not available or not in a git repo. Skipping GitHub secrets check."
    fi

    return 0
}
