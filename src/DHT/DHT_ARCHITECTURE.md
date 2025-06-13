# DHT Architecture and Repository Management

## Repository Management Strategy

### 1. Project Creation/Initialization

DHT will support multiple project initialization methods:

```bash
# Create new project from scratch
dhtl new <project-name> --type [app|library|cli|api|data-science]

# Initialize DHT in existing project
dhtl init

# Clone and setup from GitHub
dhtl clone <github-url>

# Fork and setup from GitHub
dhtl fork <github-url>

# Setup from tarball/zip
dhtl setup-from <archive-file>
```

### 2. Project Analysis Workflow

When DHT encounters a project, it follows this analysis sequence:

1. **Root Detection**: Find project root (presence of .git, pyproject.toml, setup.py)
2. **Project Type Inference**:
   - Check for framework markers (manage.py → Django, app.py → Flask, main.py → FastAPI)
   - Analyze imports and file structure
   - Detect CLI entry points, library exports, or application servers
3. **Dependency Analysis**:
   - Parse pyproject.toml, requirements*.txt, setup.py
   - Scan imports for undeclared dependencies
   - Detect system dependencies (C libraries, binaries)
4. **Environment Requirements**:
   - Python version from .python-version, pyproject.toml, or runtime.txt
   - Check for multi-language components (package.json, go.mod, Cargo.toml)
   - Identify required tools and services

### 3. .dhtconfig Design

The `.dhtconfig` file stores minimal, non-inferrable configuration:

```yaml
# .dhtconfig - DHT Configuration File
version: "1.0"

# Project metadata (only if not in pyproject.toml)
project:
  type: "web-api"  # Overrides auto-detection if needed
  
# Python configuration (only if special requirements)
python:
  # UV will handle version from .python-version or pyproject.toml
  # Only specify here if there are special constraints
  system_packages: ["libpq-dev", "gcc"]  # System deps not auto-detectable
  
# Multi-language support
languages:
  node:
    version: "18.x"  # If package.json doesn't specify
    package_manager: "pnpm"  # If not standard npm
  rust:
    toolchain: "stable"
    
# Docker configuration hints
docker:
  base_image_variant: "slim"  # Override default detection
  exposed_ports: [8000, 8080]  # If not detectable from code
  
# CI/CD preferences
ci:
  providers: ["github", "gitlab"]  # Which CI systems to generate for
  coverage_threshold: 80
  
# Development tools configuration
tools:
  formatter: "ruff"  # Override default black
  test_runner: "pytest"  # Override if using unittest
  
# Secrets hints (names only, never values)
required_secrets:
  - OPENAI_API_KEY
  - DATABASE_URL
  - REDIS_URL
```

Key principles:
- **Minimal**: Only store what can't be inferred
- **Portable**: YAML format, no platform-specific paths
- **Versioned**: Track config format version
- **Secure**: Never store actual secrets or credentials

### 4. Environment Regeneration Process

When setting up a project (clone/fork/extract), DHT will:

1. **Read .dhtconfig** (if exists)
2. **Analyze project** to fill in gaps
3. **Create virtual environment**:
   ```bash
   uv venv
   uv python pin <detected-version>
   ```
4. **Install dependencies**:
   ```bash
   uv sync  # If uv.lock exists
   uv pip install -r requirements.txt  # Fallback
   uv add --dev pytest mypy ruff  # DHT standard tools
   ```
5. **Setup additional languages** (if detected):
   ```bash
   # Node.js projects
   uv run npm install
   
   # Rust components
   uv run cargo build
   ```
6. **Configure git hooks**:
   ```bash
   pre-commit install  # If .pre-commit-config.yaml exists
   ```
7. **Generate missing configs**:
   - Create .gitignore if missing
   - Add GitHub workflows if not present
   - Setup pre-commit hooks
8. **Create .env template**:
   - List required environment variables
   - Source from global environment if available

### 5. Prefect Integration for Task Management

Replace the current guardian system with Prefect:

```python
# DHT/modules/task_manager.py
from prefect import flow, task
from prefect.task_runners import SequentialTaskRunner

@task
def setup_venv(project_path):
    """Create and configure virtual environment"""
    pass

@task
def install_dependencies(project_path):
    """Install project dependencies"""
    pass

@flow(task_runner=SequentialTaskRunner())  # max_concurrency=1 for safety
def setup_project_flow(project_path):
    """Complete project setup flow"""
    venv = setup_venv(project_path)
    deps = install_dependencies(project_path)
    # ... more tasks
```

Benefits:
- Robust task queuing and execution
- Progress tracking and logging
- Error handling and retries
- Background execution support

### 6. Python Version Compatibility Strategy

DHT running on Python 3.10 can manage 3.11+ projects because:

1. **UV handles Python versions independently**:
   ```bash
   # DHT runs on 3.10
   python --version  # 3.10.x
   
   # But can create 3.13 project env
   uv python install 3.13
   uv venv --python 3.13
   uv python pin 3.13
   ```

2. **Tool isolation**:
   - Build tools run inside project venv
   - DHT just orchestrates via `uv run`
   - No direct dependency conflicts

3. **Compatibility considerations**:
   - Use `subprocess` to run project commands
   - Parse outputs, don't import project code
   - Let UV handle version-specific features

4. **Future-proofing**:
   - Monitor for UV API changes
   - Test against new Python versions
   - Consider bumping DHT to 3.11 if needed for UV features

### 7. Basic DHT Actions Implementation Plan

#### Phase 1: Core Commands
1. `dhtl new` - Project creation with templates
2. `dhtl clone` - Smart clone with auto-setup
3. `dhtl dockerize` - Automatic Docker configuration
4. `dhtl addtask` - Task checklist management

#### Phase 2: Enhanced Detection
1. Framework detection module
2. Dependency inference engine
3. Multi-language support detection
4. CI/CD template selection

#### Phase 3: Advanced Features
1. Project health monitoring
2. Security scanning integration
3. Documentation generation
4. Performance profiling setup

### 8. Docker Implementation Strategy

The `dhtl dockerize` command will:

1. **Analyze project structure**:
   - Detect web frameworks and default ports
   - Find static files and media directories
   - Identify database connections

2. **Generate smart Dockerfile**:
   ```dockerfile
   # Multi-stage build
   FROM python:3.11-slim as builder
   # ... dependencies
   
   FROM python:3.11-slim
   # ... optimized runtime
   ```

3. **Create docker-compose.yml** if needed:
   - Add database services
   - Configure volumes
   - Set up networking

4. **Generate .dockerignore**:
   - Exclude venv, caches, logs
   - Keep source and configs

This architecture ensures DHT can handle any Python project intelligently while maintaining simplicity and automation.