# DHT Atomic Information Structure

This document describes the practical, use-case driven atomic information structure implemented in the enhanced diagnostic reporter.

## Key Improvements

1. **Platform-Aware**: Automatically skips tools that don't exist on your platform
2. **Use-Case Driven**: Categories based on what developers actually need to find
3. **Atomic Access**: Every piece of information has a clear path (e.g., `tools.build_tools.cmake.version`)
4. **Practical Categories**: No abstract categories like "productivity" - everything is organized by actual use

## Information Hierarchy

### System Information
```yaml
system:
  platform: "macos|linux|windows"
  os: "Darwin|Linux|Windows"
  release: "23.4.0"
  version: "Darwin Kernel Version..."
  architecture: "arm64|x86_64"
  processor: "Apple M1|Intel Core i7"
  hostname: "my-machine"
  fqdn: "my-machine.local"
  cpu:
    physical_cores: 8
    logical_cores: 16
    current_freq_mhz: 2400
    load_average: [1.5, 2.0, 1.8]
  memory:
    total_mb: 16384
    available_mb: 8192
    used_percent: 50.0
  boot_time: "2024-01-01T10:00:00"
  python:
    version: "3.11.7"
    implementation: "CPython"
    executable: "/usr/local/bin/python3"
```

### Network Information
```yaml
network:
  interfaces:
    en0:
      ipv4: ["192.168.1.100"]
      ipv6: ["fe80::1"]
      mac: ["00:11:22:33:44:55"]
  internet_access: true
  hostname: "my-machine"
  default_gateway: "192.168.1.1"
```

### Filesystem Information
```yaml
filesystem:
  filesystems:
    - device: "/dev/disk1s1"
      mountpoint: "/"
      fstype: "apfs"
      total_gb: 500
      used_gb: 250
      free_gb: 250
      percent_used: 50.0
  working_directory: "/Users/user/projects"
  home_directory: "/Users/user"
  temp_directory: "/tmp"
```

### Tools Information (Atomic Structure)

#### Version Control
```yaml
tools:
  version_control:
    git:
      is_installed: true
      version: "2.43.0"
      config_user_name: "John Doe"
      config_user_email: "john@example.com"
      config_core_editor: "vim"
      user_info_user_name: "John Doe"
      user_info_user_email: "john@example.com"
```

#### Language Runtimes
```yaml
tools:
  language_runtimes:
    python:
      is_installed: true
      version: "3.11.7"
      executable_path: "/usr/local/bin/python3"
      sys_path: ["/usr/local/lib/python3.11", "..."]
      site_packages: "/usr/local/lib/python3.11/site-packages"
      venv_active: false
      pip_version: "23.3.1"

    node:
      is_installed: true
      version: "20.10.0"
      npm_version: "10.2.3"
      executable_path: "/usr/local/bin/node"
      global_modules: "/usr/local/lib/node_modules"
      config:
        registry: "https://registry.npmjs.org/"
        prefix: "/usr/local"

    rust:
      is_installed: true
      version: "1.75.0"
      cargo_version: "1.75.0"
      toolchain: "stable-aarch64-apple-darwin"
      installed_targets: ["wasm32-unknown-unknown", "x86_64-apple-darwin"]
```

#### Package Managers
```yaml
tools:
  package_managers:
    system:
      macos:
        brew:
          is_installed: true
          version: "4.2.0"
          prefix: "/opt/homebrew"
          installed_count: 234
          tap_list: ["homebrew/core", "homebrew/cask"]

    language:
      python:
        pip:
          is_installed: true
          version: "23.3.1"
          config_global_index_url: "https://pypi.org/simple"
          inspect: {...}  # Full pip inspect output

        conda:
          is_installed: true
          version: "23.11.0"
          info: {...}  # Full conda info
          envs: ["base", "ml-project", "web-dev"]

        uv:
          is_installed: true
          version: "0.1.5"
          pip_version: "0.1.5"

      javascript:
        npm:
          is_installed: true
          version: "10.2.3"
          config: {...}  # Full npm config
          global_packages: {...}
```

#### Build Tools
```yaml
tools:
  build_tools:
    make:
      is_installed: true
      version: "3.81"
      features_make_version: "3.81"

    cmake:
      is_installed: true
      version: "3.28.1"
      system_info_cmake_version: "3.28.1"
      system_info_cmake_generator: "Unix Makefiles"
      system_info_c_compiler: "/usr/bin/clang"
      system_info_cxx_compiler: "/usr/bin/clang++"
```

#### Compilers
```yaml
tools:
  compilers:
    gcc:
      is_installed: true
      version: "13.2.0"
      target: "aarch64-apple-darwin23"
      search_dirs_install: "/opt/homebrew/Cellar/gcc/13.2.0"

    clang:
      is_installed: true
      version: "15.0.0"
      target: "arm64-apple-darwin23.4.0"
```

#### Container & Virtualization
```yaml
tools:
  containers_virtualization:
    docker:
      is_installed: true
      version: "24.0.7"
      info:
        ServerVersion: "24.0.7"
        StorageDriver: "overlay2"
        CgroupDriver: "cgroupfs"
        DockerRootDir: "/var/lib/docker"
      compose_version: "2.23.3"

    kubectl:
      is_installed: true
      version: "1.29.0"
      context: "docker-desktop"
      contexts: ["docker-desktop", "minikube", "prod-cluster"]
```

#### Cloud Tools
```yaml
tools:
  cloud_tools:
    aws:
      is_installed: true
      version: "2.15.0"
      configure_list_profile: "default"
      configure_list_region: "us-east-1"
      profiles: ["default", "production", "staging"]

    terraform:
      is_installed: true
      version: "1.6.6"
      providers: ["aws", "google", "kubernetes"]
```

#### Archive Managers
```yaml
tools:
  archive_managers:
    tar:
      is_installed: true
      version: "3.5.3"
      help_formats: "gzip, bzip2, xz, lzip"

    zip:
      is_installed: true
      version: "3.0"
```

#### Network Tools
```yaml
tools:
  network_tools:
    curl:
      is_installed: true
      version: "8.5.0"
      protocols: "dict file ftp ftps gopher gophers http https"
      features: "AsynchDNS GSS-API HSTS HTTP2 HTTPS-proxy IPv6"

    openssl:
      is_installed: true
      version: "3.2.0"
```

## Benefits of This Structure

1. **Fast Lookups**: Need to check if Docker is installed? → `tools.containers_virtualization.docker.is_installed`
2. **Version Checking**: Need CMake version? → `tools.build_tools.cmake.version`
3. **Dependency Detection**: Need Python packages? → `tools.package_managers.language.python.pip.inspect`
4. **Platform-Specific**: On macOS? Only `brew` shows up, not `apt` or `yum`
5. **Grouped by Use**: All archive tools together, all compilers together, etc.

## Usage Examples

```python
# Check if a build tool is available
if report['tools']['build_tools']['cmake']['is_installed']:
    cmake_version = report['tools']['build_tools']['cmake']['version']

# Get all installed package managers
pkg_managers = report['tools']['package_managers']['language']['python']
for manager, info in pkg_managers.items():
    if info.get('is_installed'):
        print(f"{manager}: {info.get('version')}")

# Check container runtime
docker = report['tools']['containers_virtualization'].get('docker', {})
if docker.get('is_installed'):
    storage_driver = docker['info']['StorageDriver']
```

## Extending the System

To add a new tool:

1. Add it to `cli_commands_registry.py`:
```python
"new_tool": {
    "commands": {
        "version": "new_tool --version",
        "config": "new_tool config list",
    },
    "category": "appropriate_category"
}
```

2. The system automatically:
   - Checks if it's installed
   - Runs all commands
   - Parses output (JSON, version numbers, key-value pairs)
   - Places it in the correct category
   - Makes it available at the atomic path
