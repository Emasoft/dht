# DHT Environment Regeneration Plan

## Core Concept: Deterministic Environment Recreation

The goal is to ensure that `dhtl regenerate` produces identical development environments across all platforms, making `dhtl clone/fork` truly seamless.

## 1. Enhanced .dhtconfig Structure

```yaml
# .dhtconfig v2.0 - Deterministic Environment Specification
version: "2.0"
dht_version: "0.1.0"  # Minimum DHT version required

# Environment fingerprint for validation
fingerprint:
  created_at: "2024-12-06T10:00:00Z"
  created_by: "DHT/0.1.0"
  platform: "darwin-arm64"  # Original platform for reference

# Python environment specification
python:
  version: "3.11.7"  # Exact version, not range
  implementation: "cpython"  # cpython, pypy, etc.
  
# Lock file strategy
dependencies:
  strategy: "uv"  # uv, pip-tools, poetry
  lock_files:
    - "uv.lock"           # Primary lock file
    - "requirements.lock" # Fallback
  hash_validation: true   # Verify package hashes
  
# Platform-specific dependencies
platform_deps:
  darwin:
    brew: ["postgresql@14", "redis"]
    system: []
  linux:
    apt: ["libpq-dev", "redis-server"]
    yum: ["postgresql-devel", "redis"]
  windows:
    choco: ["postgresql14", "redis-64"]
    
# Binary dependencies with versions
binaries:
  required:
    - name: "node"
      version: "18.17.0"
      installer: "uv tool"  # or nvm, system
    - name: "rust"
      version: "1.70.0"
      installer: "rustup"
      
# Development tools specification
tools:
  # Exact versions for reproducibility
  pytest: "7.4.0"
  mypy: "1.5.0"
  ruff: "0.1.0"
  black: "23.7.0"
  pre-commit: "3.3.3"
  
# Environment variables (structure only)
env_template:
  required:
    - DATABASE_URL
    - REDIS_URL
  optional:
    - DEBUG
    - LOG_LEVEL
    
# Git configuration
git:
  hooks:
    pre_commit: true
    commit_msg: true
  lfs: false
  submodules: []
  
# Validation checksums
validation:
  venv_checksum: "sha256:abcd1234..."  # Hash of installed packages
  config_checksum: "sha256:efgh5678..." # Hash of all config files
```

## 2. The Regeneration Process

### Phase 1: Environment Analysis (during `dhtl setup`)

```bash
# When user runs initial setup
dhtl setup
```

DHT will:

1. **Capture Complete Environment State**:
   ```python
   def capture_environment_state():
       state = {
           'python_version': get_exact_python_version(),
           'installed_packages': get_all_installed_with_hashes(),
           'system_packages': detect_system_dependencies(),
           'binary_tools': scan_required_binaries(),
           'env_vars': extract_required_env_vars(),
       }
       return state
   ```

2. **Generate Lock Files**:
   ```bash
   # Create comprehensive lock files
   uv pip compile requirements.in -o requirements.lock
   uv lock  # Creates uv.lock with exact versions
   
   # Capture tool versions
   dhtl freeze-tools > .dht/tools.lock
   ```

3. **Create Platform Mapping**:
   ```python
   def create_platform_mapping():
       # Map generic deps to platform-specific packages
       mappings = {
           'postgresql-client': {
               'darwin': 'postgresql@14',
               'ubuntu': 'libpq-dev',
               'centos': 'postgresql-devel',
               'windows': 'postgresql14'
           }
       }
       return mappings
   ```

### Phase 2: Environment Regeneration (during `dhtl regenerate`)

```bash
# When someone clones and regenerates
dhtl regenerate
```

The regeneration follows this deterministic sequence:

1. **Validate DHT Version**:
   ```python
   def check_dht_compatibility():
       required = parse_dhtconfig()['dht_version']
       current = get_dht_version()
       if not is_compatible(current, required):
           prompt_dht_upgrade()
   ```

2. **Install Exact Python Version**:
   ```bash
   # Use UV to install exact Python version
   uv python install 3.11.7
   uv venv --python 3.11.7
   
   # Verify installation
   python --version | verify_exact_match "3.11.7"
   ```

3. **Platform-Specific Setup**:
   ```python
   def install_platform_dependencies():
       platform = detect_platform()
       deps = parse_dhtconfig()['platform_deps'][platform]
       
       if platform == 'darwin':
           run_command(['brew', 'install'] + deps['brew'])
       elif platform == 'linux':
           if shutil.which('apt'):
               run_command(['sudo', 'apt', 'install', '-y'] + deps['apt'])
           elif shutil.which('yum'):
               run_command(['sudo', 'yum', 'install', '-y'] + deps['yum'])
       elif platform == 'windows':
           run_command(['choco', 'install', '-y'] + deps['choco'])
   ```

4. **Restore Exact Dependencies**:
   ```bash
   # Use lock files with hash verification
   uv sync --locked --require-hashes
   
   # Verify installation matches checksum
   dhtl verify-environment --checksum ${validation.venv_checksum}
   ```

5. **Install Binary Tools**:
   ```python
   def install_binary_tools():
       for tool in parse_dhtconfig()['binaries']['required']:
           if tool['installer'] == 'uv tool':
               run_command(['uv', 'tool', 'install', 
                          f"{tool['name']}=={tool['version']}"])
           elif tool['installer'] == 'rustup':
               install_rust_toolchain(tool['version'])
   ```

6. **Configure Development Environment**:
   ```bash
   # Install exact tool versions
   uv pip install pytest==7.4.0 mypy==1.5.0 ruff==0.1.0
   
   # Setup git hooks
   pre-commit install
   
   # Create .env template
   dhtl generate-env-template
   ```

## 3. The Clone/Fork Workflow

### `dhtl clone <url>` Implementation:

```python
def dhtl_clone(url):
    # 1. Use gh CLI to clone
    repo_name = extract_repo_name(url)
    run_command(['gh', 'repo', 'clone', url])
    
    # 2. Change to repo directory
    os.chdir(repo_name)
    
    # 3. Run regeneration
    dhtl_regenerate()
    
    # 4. Show status
    print(f"✓ Cloned {repo_name}")
    print(f"✓ Python {python_version} environment created")
    print(f"✓ All dependencies installed")
    print(f"✓ Development tools configured")
    show_missing_env_vars()
```

### `dhtl fork <url>` Implementation:

```python
def dhtl_fork(url):
    # 1. Fork using gh CLI
    run_command(['gh', 'repo', 'fork', url, '--clone'])
    
    # 2. Get local directory name
    repo_name = extract_repo_name(url)
    os.chdir(repo_name)
    
    # 3. Run regeneration
    dhtl_regenerate()
    
    # 4. Setup upstream
    run_command(['git', 'remote', 'add', 'upstream', url])
    
    print(f"✓ Forked and cloned {repo_name}")
    print(f"✓ Environment regenerated successfully")
```

## 4. Ensuring Cross-Platform Reproducibility

### A. Python Version Management

```python
def ensure_python_version(required_version):
    # Try multiple strategies
    strategies = [
        lambda: use_uv_python(required_version),        # Best: UV python
        lambda: use_pyenv(required_version),             # Good: pyenv
        lambda: use_system_python(required_version),     # OK: system
        lambda: use_docker_fallback(required_version),   # Fallback: Docker
    ]
    
    for strategy in strategies:
        if strategy():
            return True
    
    raise EnvironmentError(f"Cannot provide Python {required_version}")
```

### B. Package Installation Verification

```python
def verify_package_installation():
    # Generate current environment checksum
    current_checksum = generate_venv_checksum()
    
    # Compare with expected
    expected_checksum = parse_dhtconfig()['validation']['venv_checksum']
    
    if current_checksum != expected_checksum:
        # Try to diagnose differences
        diagnose_environment_differences()
        
        # Offer fixes
        if prompt_user("Try automatic fix?"):
            fix_environment_differences()
```

### C. Platform Abstraction Layer

```python
class PlatformAdapter:
    def __init__(self, platform):
        self.platform = platform
        
    def install_system_package(self, generic_name):
        # Map generic name to platform-specific
        mapping = load_platform_mappings()
        specific_name = mapping[generic_name][self.platform]
        
        # Use appropriate package manager
        if self.platform == 'darwin':
            return self._install_via_brew(specific_name)
        elif self.platform in ['ubuntu', 'debian']:
            return self._install_via_apt(specific_name)
        # ... etc
```

## 5. Handling Edge Cases

### A. Missing System Dependencies

```python
def handle_missing_system_deps():
    missing = detect_missing_system_deps()
    
    if missing:
        print("Missing system dependencies detected:")
        for dep in missing:
            print(f"  - {dep}")
        
        if is_container_environment():
            generate_dockerfile_snippet(missing)
        else:
            show_install_instructions(missing)
```

### B. Binary Tool Conflicts

```python
def resolve_binary_conflicts():
    # Isolate tools in venv
    for tool in get_required_tools():
        if has_system_conflict(tool):
            install_in_venv_bin(tool)
            create_venv_wrapper(tool)
```

### C. Lock File Conflicts

```python
def merge_lock_files():
    # If multiple lock files exist, merge intelligently
    primary_lock = load_uv_lock()
    requirements_lock = load_requirements_lock()
    
    # UV lock takes precedence
    merged = merge_with_resolution(primary_lock, requirements_lock)
    
    # Validate merged result
    validate_no_conflicts(merged)
```

## 6. Validation and Testing

### A. Environment Validation Command

```bash
dhtl validate-env
```

This command will:
1. Check Python version matches exactly
2. Verify all packages with correct versions
3. Confirm system dependencies present
4. Validate tool versions
5. Check git hooks configured
6. Display comprehensive report

### B. Continuous Validation

```python
def add_validation_hook():
    # Add post-activation hook to venv
    hook_script = """
    # Validate environment on activation
    if command -v dhtl >/dev/null 2>&1; then
        dhtl validate-env --quiet || echo "Warning: Environment drift detected"
    fi
    """
    add_to_venv_activate(hook_script)
```

## 7. Implementation Priorities

### Phase 1: Core Regeneration (Week 1-2)
1. Implement enhanced .dhtconfig format
2. Build `dhtl regenerate` command
3. Add Python version management via UV
4. Create checksum validation

### Phase 2: Platform Support (Week 3-4)
1. Implement platform detection
2. Build package mapping system
3. Add system dependency installation
4. Create Docker fallback option

### Phase 3: Clone/Fork Integration (Week 5)
1. Implement `dhtl clone` command
2. Implement `dhtl fork` command
3. Add progress reporting
4. Create error recovery

### Phase 4: Validation & Testing (Week 6)
1. Build validation framework
2. Add continuous validation
3. Create test suite
4. Document edge cases

## 8. Example User Flow

```bash
# Original developer
$ cd myproject
$ dhtl setup
✓ Python 3.11.7 environment created
✓ Dependencies locked (uv.lock)
✓ .dhtconfig generated
✓ Environment fingerprint: sha256:abcd1234...

$ git add .dhtconfig uv.lock
$ git commit -m "Add DHT configuration"
$ git push

# New developer on different platform
$ dhtl clone https://github.com/user/myproject
✓ Repository cloned
✓ Python 3.11.7 installed via UV
✓ Platform: ubuntu-22.04 (detected)
✓ System packages installed: libpq-dev, redis-server
✓ Python packages restored from uv.lock
✓ Development tools installed: pytest==7.4.0, mypy==1.5.0
✓ Git hooks configured
✓ Environment validated: sha256:abcd1234... ✓ MATCH

$ dhtl validate-env
✓ Python version: 3.11.7 (exact match)
✓ Packages: 127 installed, all verified
✓ Tools: all present with correct versions
✓ Configuration: matches original exactly

Environment successfully regenerated!
Missing environment variables:
  - DATABASE_URL (required)
  - REDIS_URL (required)
  
Run 'dhtl env-setup' for instructions.
```

This plan ensures true reproducibility across platforms by:
1. Capturing exact versions and checksums
2. Using UV for deterministic Python management
3. Mapping platform-specific dependencies
4. Validating the regenerated environment
5. Providing clear feedback and recovery options