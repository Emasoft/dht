# Implementation Milestone 1: Basic Regeneration

## Goal
Implement a working `dhtl regenerate` command that can recreate a Python environment from .dhtconfig

## Success Criteria
- [ ] Can regenerate exact Python version environment
- [ ] Restores all pip dependencies with correct versions
- [ ] Works on Mac and Linux (Windows in v2)
- [ ] Validates regenerated environment matches original

## Implementation Steps

### Step 1: Create .dhtconfig Parser (Day 1)

```bash
# In dhtl_config.sh
parse_dhtconfig() {
    # Use yq or python for YAML parsing
    if command -v yq >/dev/null 2>&1; then
        PYTHON_VERSION=$(yq '.python.version' .dhtconfig)
        LOCK_STRATEGY=$(yq '.dependencies.strategy' .dhtconfig)
    else
        # Fallback to Python
        PYTHON_VERSION=$(python -c "
import yaml
with open('.dhtconfig') as f:
    config = yaml.safe_load(f)
    print(config['python']['version'])
        ")
    fi
}
```

### Step 2: Implement Python Version Management (Day 2-3)

```bash
# In dhtl_python_manager.sh
ensure_python_version() {
    local required="$1"

    # Strategy 1: UV Python
    if uv python list | grep -q "$required"; then
        echo "Python $required already available"
    else
        echo "Installing Python $required..."
        uv python install "$required"
    fi

    # Create venv with specific version
    uv venv --python "$required" .venv
}
```

### Step 3: Dependency Installation with Validation (Day 4-5)

```bash
# In dhtl_deps.sh
install_with_checksum() {
    # Install from lock file
    uv sync --locked

    # Generate checksum
    local checksum=$(generate_checksum)

    # Validate if expected checksum exists
    if [[ -n "$EXPECTED_CHECKSUM" ]]; then
        if [[ "$checksum" != "$EXPECTED_CHECKSUM" ]]; then
            echo "Warning: Checksum mismatch"
            show_diff_report
        fi
    fi
}
```

### Step 4: Platform Detection and Mapping (Day 6-7)

```python
# In DHT/modules/platform_mapper.py
PLATFORM_MAPPINGS = {
    'postgresql': {
        'darwin': {'brew': 'postgresql@14'},
        'ubuntu': {'apt': 'libpq-dev'},
        'fedora': {'dnf': 'postgresql-devel'}
    }
}

def get_platform_package(generic_name, platform):
    """Map generic package name to platform-specific name"""
    return PLATFORM_MAPPINGS.get(generic_name, {}).get(platform)
```

### Step 5: Create Regenerate Command (Day 8-9)

```bash
# In dhtl_commands_9.sh
regenerate_command() {
    echo "🔄 Regenerating environment from .dhtconfig..."

    # Parse config
    parse_dhtconfig || die "Failed to parse .dhtconfig"

    # Install Python
    ensure_python_version "$PYTHON_VERSION" || die "Failed to install Python"

    # Install system deps
    install_platform_deps || warn "Some system deps may be missing"

    # Install Python deps
    install_with_checksum || die "Failed to install dependencies"

    # Validate
    validate_environment || warn "Environment validation failed"

    echo "✅ Environment regenerated successfully!"
}
```

### Step 6: Add Clone/Fork Commands (Day 10)

```bash
# In dhtl_commands_9.sh
clone_command() {
    local url="$1"

    # Clone repo
    gh repo clone "$url" || git clone "$url"

    # Enter directory
    cd "$(basename "$url" .git)"

    # Regenerate
    regenerate_command
}
```

## Testing Plan

### Test 1: Basic Regeneration
```bash
# Create test project
mkdir test-project && cd test-project
echo "print('hello')" > main.py
dhtl setup  # Creates .dhtconfig

# Remove venv
rm -rf .venv

# Test regeneration
dhtl regenerate
source .venv/bin/activate
python --version  # Should match exactly
```

### Test 2: Cross-Platform
```bash
# Test on Mac
docker run -v $PWD:/project python:3.10 bash -c "
cd /project &&
./dhtl.sh regenerate
"

# Test on Ubuntu
docker run -v $PWD:/project ubuntu:22.04 bash -c "
cd /project &&
./dhtl.sh regenerate
"
```

### Test 3: Clone Workflow
```bash
# Push test project
git init && git add . && git commit -m "test"
gh repo create test-dht-project --public --push

# Clone on different machine
dhtl clone username/test-dht-project
# Should automatically setup environment
```

## Configuration Examples

### Minimal .dhtconfig
```yaml
version: "1.0"
python:
  version: "3.11.7"
dependencies:
  strategy: "uv"
```

### Complex .dhtconfig
```yaml
version: "1.0"
python:
  version: "3.11.7"
dependencies:
  strategy: "uv"
  lock_files: ["uv.lock"]
platform_deps:
  darwin:
    brew: ["postgresql@14"]
  linux:
    apt: ["libpq-dev"]
validation:
  venv_checksum: "sha256:abc123..."
```

## Error Handling

### Common Errors and Solutions

1. **Python Version Unavailable**
   ```bash
   if ! uv python install "$version"; then
       echo "Trying pyenv..."
       try_pyenv "$version" ||
       echo "Please install Python $version manually"
   fi
   ```

2. **Lock File Missing**
   ```bash
   if [[ ! -f "uv.lock" ]]; then
       echo "No lock file found, generating..."
       uv pip compile requirements.in -o requirements.lock
   fi
   ```

3. **System Dependencies**
   ```bash
   if ! command -v pg_config; then
       echo "PostgreSQL client libraries missing"
       show_install_instructions
   fi
   ```

## Deliverables

1. **New shell modules**:
   - `dhtl_config.sh` - Config parsing
   - `dhtl_python_manager.sh` - Python version management
   - `dhtl_platform.sh` - Platform detection/mapping

2. **Updated modules**:
   - `dhtl_commands_9.sh` - Add regenerate/clone/fork commands
   - `dhtl_uv.sh` - Enhance UV integration

3. **Python helpers**:
   - `platform_mapper.py` - Platform package mappings
   - `checksum_validator.py` - Environment validation

4. **Documentation**:
   - Updated README with regeneration workflow
   - Migration guide for existing projects

## Next Milestone Preview

Milestone 2 will add:
- Windows support via Git Bash/WSL
- Docker fallback for unsupported platforms
- Binary tool management (node, rust, etc.)
- Advanced validation reporting
- Performance optimizations
