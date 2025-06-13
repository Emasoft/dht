# DHT Edge Cases and Solutions

## Platform-Specific Challenges

### 1. Python Version Unavailable on Platform

**Problem**: User needs Python 3.11.7 but their system only has 3.11.5

**Solution Hierarchy**:
```python
def ensure_python_version(required_version):
    strategies = [
        # 1. UV Python (best - exact version)
        lambda: try_uv_python(required_version),
        
        # 2. Relaxed patch version (3.11.7 → 3.11.x)
        lambda: try_uv_python_minor(required_version),
        
        # 3. System Python if close enough
        lambda: try_system_python_compatible(required_version),
        
        # 4. Docker fallback
        lambda: create_docker_dev_env(required_version),
        
        # 5. Error with clear instructions
        lambda: show_python_install_guide(required_version)
    ]
    
    for strategy in strategies:
        if result := strategy():
            return result
```

**Docker Fallback Implementation**:
```bash
# .dht/docker/Dockerfile.dev
FROM python:3.11.7-slim
RUN pip install uv
WORKDIR /project
CMD ["/bin/bash"]

# Create alias for seamless usage
alias python="docker run --rm -v $PWD:/project dht-py3.11.7 python"
```

### 2. System Package Manager Conflicts

**Problem**: Package has different names across distros

**Advanced Mapping System**:
```python
PACKAGE_MAPPINGS = {
    'postgresql-client': {
        # Distro-specific
        'ubuntu:22.04': {'apt': 'postgresql-client-14'},
        'ubuntu:20.04': {'apt': 'postgresql-client-12'},
        'debian:11': {'apt': 'postgresql-client-13'},
        'debian:12': {'apt': 'postgresql-client-15'},
        
        # Fallback patterns
        'ubuntu:*': {'apt': 'postgresql-client'},
        'fedora:*': {'dnf': 'postgresql'},
        'arch:*': {'pacman': 'postgresql-libs'},
        
        # Special handling
        'alpine:*': {
            'apk': 'postgresql-client',
            'post_install': 'ln -s /usr/bin/psql /usr/local/bin/psql'
        }
    }
}
```

### 3. Corporate Proxy Environments

**Problem**: Behind corporate firewall with MITM proxy

**Solution**:
```python
class ProxyAwareDownloader:
    def detect_proxy_settings(self):
        # Check multiple sources
        proxies = {}
        
        # 1. Environment variables
        for key in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']:
            if value := os.environ.get(key):
                proxies[key.lower().split('_')[0]] = value
        
        # 2. System proxy (Windows)
        if platform.system() == 'Windows':
            import winreg
            # Read from registry
        
        # 3. Corporate config files
        corp_configs = [
            '/etc/corporate/proxy.conf',
            '~/.corporate/settings.ini',
            'C:\\ProgramData\\Corporate\\proxy.txt'
        ]
        
        return proxies
    
    def configure_tools_for_proxy(self, proxies):
        # Configure each tool
        configs = []
        
        # pip
        configs.append(f"pip config set global.proxy {proxies['http']}")
        
        # git
        configs.append(f"git config --global http.proxy {proxies['http']}")
        
        # npm (if needed)
        configs.append(f"npm config set proxy {proxies['http']}")
        
        # Corporate CA certificates
        if ca_bundle := self.find_corporate_ca_bundle():
            configs.append(f"export REQUESTS_CA_BUNDLE={ca_bundle}")
            configs.append(f"export SSL_CERT_FILE={ca_bundle}")
```

### 4. Containerized Development Environments

**Problem**: Running inside Docker/Podman/Dev Containers

**Detection and Adaptation**:
```python
def detect_container_environment():
    indicators = {
        'docker': [
            '/.dockerenv',
            '/proc/1/cgroup contains "docker"'
        ],
        'podman': [
            '/run/.containerenv',
            '/proc/1/cgroup contains "podman"'
        ],
        'wsl': [
            '/proc/version contains "Microsoft"'
        ],
        'codespaces': [
            'CODESPACES env var exists'
        ]
    }
    
    # Adapt behavior
    if in_container:
        # Don't try to install system packages
        # Use only user-space tools
        # Adjust paths for container FS
        pass
```

### 5. Air-Gapped Environments

**Problem**: No internet access

**Offline Mode**:
```bash
# Preparation (on internet-connected machine)
$ dhtl prepare-offline --output dht-offline-bundle.tar.gz

📦 Creating offline bundle...
✓ Downloading Python 3.11.7 installer
✓ Downloading all dependencies with wheels
✓ Including UV binary
✓ Packaging tools and configurations

# Transfer bundle to air-gapped machine

# Installation (offline)
$ dhtl setup --offline-bundle dht-offline-bundle.tar.gz

🔒 Running in offline mode...
✓ Extracting Python from bundle
✓ Installing from cached wheels
✓ No checksum validation (offline mode)
```

### 6. Permission Issues

**Problem**: Can't install system packages without sudo

**User-Space Alternatives**:
```python
USERSPACE_ALTERNATIVES = {
    'postgresql-client': {
        'method': 'binary_download',
        'url': 'https://get.enterprisedb.com/postgresql/postgresql-{version}-linux-x64-binaries.tar.gz',
        'install': 'extract_to_venv_bin'
    },
    'redis': {
        'method': 'compile_from_source',
        'url': 'https://download.redis.io/redis-stable.tar.gz',
        'install': 'make PREFIX=$VIRTUAL_ENV install'
    },
    'nodejs': {
        'method': 'portable_binary',
        'url': 'https://nodejs.org/dist/v{version}/node-v{version}-linux-x64.tar.xz',
        'install': 'extract_and_symlink'
    }
}
```

### 7. Conflicting Global Tools

**Problem**: System has incompatible global versions

**Isolation Strategy**:
```bash
# Create completely isolated environment
$ dhtl setup --isolate

🔒 Creating isolated environment...
✓ Installing UV in .venv/bin (not using system UV)
✓ All tools installed in .venv (no system tools used)
✓ Created .venv/bin/activate.isolated with cleaned PATH
✓ Even git/curl/wget wrapped to use bundled versions

# Extreme isolation for problematic systems
$ dhtl setup --isolate=container

🐳 Creating container-based isolation...
✓ Building minimal container with just Python
✓ Mounting project as volume
✓ All commands run inside container
✓ Transparent to user (aliases created)
```

### 8. Version Conflicts in Monorepo

**Problem**: Different services need different Python versions

**Multi-Environment Support**:
```yaml
# .dhtconfig for monorepo
version: "2.0"
environments:
  default:
    python: "3.11.7"
    
  services/legacy-api:
    python: "3.8.17"  # Old service
    dependencies:
      strategy: "requirements"  # Not yet on UV
      
  services/ml-service:
    python: "3.10.12"  # TensorFlow compatibility
    platform_deps:
      linux:
        apt: ["libcudnn8", "cuda-toolkit-11-8"]
        
  services/web-app:
    python: "3.12.0"  # Latest features
    languages:
      node: "20.10.0"  # Frontend build
```

**Usage**:
```bash
# Setup all environments
$ dhtl setup --all-environments

# Or specific service
$ cd services/ml-service
$ dhtl setup  # Uses ml-service config

# Or explicitly
$ dhtl setup --env services/legacy-api
```

### 9. Package Registry Issues

**Problem**: PyPI is blocked/slow, need corporate registry

**Registry Configuration**:
```python
def configure_package_registry():
    # Check for corporate config
    registries = {
        'pypi': {
            'index-url': 'https://pypi.org/simple',
            'trusted-host': None
        }
    }
    
    # Corporate registry detection
    if corp_registry := detect_corporate_registry():
        registries['corporate'] = {
            'index-url': corp_registry['url'],
            'trusted-host': corp_registry['host'],
            'username': get_keyring('corp_registry_user'),
            'password': get_keyring('corp_registry_pass')
        }
    
    # Geographic optimization
    if country := detect_country():
        if mirror := COUNTRY_MIRRORS.get(country):
            registries['mirror'] = mirror
    
    # Configure UV and pip
    config_commands = []
    if 'corporate' in registries:
        config_commands.extend([
            f"uv pip config set index-url {registries['corporate']['index-url']}",
            f"pip config set global.index-url {registries['corporate']['index-url']}"
        ])
```

### 10. Binary Dependencies

**Problem**: Python package needs compiled C extension

**Build Environment Setup**:
```python
class BinaryDependencyHandler:
    def handle_binary_deps(self, package):
        if package == 'psycopg2':
            return self.install_psycopg2_binary()
        elif package == 'pillow':
            return self.install_pillow_deps()
        elif package.needs_rust():
            return self.setup_rust_toolchain()
    
    def install_psycopg2_binary(self):
        # Prefer binary wheel
        try:
            run("uv pip install psycopg2-binary")
        except:
            # Need PostgreSQL dev files
            if not self.has_pg_config():
                self.install_pg_dev_files()
            run("uv pip install psycopg2 --no-binary psycopg2")
    
    def setup_rust_toolchain(self):
        # For packages like cryptography, orjson
        if not shutil.which('cargo'):
            # Install Rust in venv
            rust_installer = download('https://sh.rustup.rs')
            run(f"sh {rust_installer} -y --profile minimal --prefix {venv_path}")
```

### 11. Network File Systems

**Problem**: .venv on NFS/SMB is slow

**Performance Optimization**:
```python
def optimize_for_network_fs():
    # Detect network FS
    if is_network_filesystem('.'):
        # Option 1: Local cache
        local_venv = Path.home() / '.dht' / 'cache' / project_hash()
        
        # Create venv on local disk
        create_venv(local_venv)
        
        # Symlink to project
        (project_root / '.venv').symlink_to(local_venv)
        
        # Option 2: Byte-compile optimization
        run("python -m compileall -j 0 .venv")
        
        # Option 3: Zip site-packages
        create_zipapp(".venv/lib/python3.11/site-packages")
```

### 12. Long Path Issues (Windows)

**Problem**: Windows path length limitations

**Solutions**:
```python
def handle_windows_long_paths():
    # 1. Enable long path support
    if platform.system() == 'Windows':
        # Check if already enabled
        import winreg
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                           r"SYSTEM\CurrentControlSet\Control\FileSystem")
        value = winreg.QueryValueEx(key, "LongPathsEnabled")[0]
        
        if not value:
            print("⚠️  Long path support not enabled")
            print("Run as admin: reg add ... /v LongPathsEnabled /d 1")
    
    # 2. Use short paths for venv
    venv_path = Path("~/.dht/v/" + short_hash(project_path))
    
    # 3. Junction instead of symlink
    if len(str(project_path / '.venv')) > 150:
        run(f"mklink /J .venv {venv_path}")
```

## Migration Edge Cases

### Complex Requirements Files

**Problem**: Requirements with git URLs, local paths, extras

```python
def parse_complex_requirements(req_file):
    """Handle all requirement formats"""
    parsers = [
        parse_standard_requirement,      # package==1.0.0
        parse_git_requirement,          # git+https://...
        parse_local_requirement,        # file:///path/to/package
        parse_editable_requirement,     # -e ./local-package
        parse_extras_requirement,       # package[extra1,extra2]
        parse_environment_markers,      # package; python_version >= "3.8"
        parse_index_url_requirement,    # -i https://custom.index/
    ]
    
    requirements = []
    for line in req_file:
        for parser in parsers:
            if result := parser(line):
                requirements.append(result)
                break
```

### Test Discovery Complexity

**Problem**: Mixed test frameworks, custom test runners

```python
def discover_test_configuration():
    """Detect all test configurations"""
    
    configs = {
        'frameworks': [],
        'patterns': [],
        'runners': [],
        'fixtures': []
    }
    
    # Check for test frameworks
    if has_pytest_tests():
        configs['frameworks'].append('pytest')
    if has_unittest_tests():
        configs['frameworks'].append('unittest')
    if has_nose_tests():
        configs['frameworks'].append('nose')
    if has_doctest_tests():
        configs['frameworks'].append('doctest')
    
    # Django special case
    if is_django_project():
        configs['runners'].append('python manage.py test')
        configs['fixtures'].append('django.test.TestCase')
    
    # Custom test commands
    if makefile_has_test():
        configs['runners'].append('make test')
    if tox_ini_exists():
        configs['runners'].append('tox')
    
    return configs
```

## Recovery Procedures

### Corrupted Virtual Environment

```bash
$ dhtl diagnose

🔍 Diagnosing environment issues...
❌ Virtual environment corrupted:
   - Missing pip
   - Broken symlinks detected
   - Package metadata inconsistent

🔧 Suggested fixes:
1. Quick fix: dhtl fix-env
2. Clean rebuild: dhtl regenerate --force
3. Manual fix: Follow steps below...

$ dhtl fix-env --deep

🔧 Deep environment repair...
✓ Backing up current package list
✓ Removing corrupted .venv
✓ Rebuilding from .dhtconfig
✓ Reinstalling packages from backup
✓ Validating installation
✅ Environment repaired!
```

### Partial Setup Failure

```python
class SetupRecovery:
    def __init__(self):
        self.checkpoint_file = '.dht/setup-progress.json'
    
    def save_checkpoint(self, step, data):
        """Save progress after each major step"""
        checkpoints = self.load_checkpoints()
        checkpoints[step] = {
            'timestamp': datetime.now().isoformat(),
            'data': data,
            'status': 'completed'
        }
        self.write_checkpoints(checkpoints)
    
    def recover_from_failure(self):
        """Resume from last successful step"""
        checkpoints = self.load_checkpoints()
        last_successful = self.find_last_successful(checkpoints)
        
        print(f"🔄 Resuming from: {last_successful}")
        return self.resume_from_step(last_successful)
```

This comprehensive edge case handling ensures DHT works reliably in any environment, no matter how challenging or unusual.