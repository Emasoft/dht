# UV Integration Strategy for DHT

## Overview

UV is a modern, ultra-fast Python package and project manager written in Rust. It provides comprehensive tooling for Python environment management, dependency resolution, and project lifecycle management. This document outlines how DHT will leverage UV to provide intelligent, deterministic project configuration.

## UV Key Features Relevant to DHT

### 1. Python Version Management
- **Automatic Python Downloads**: UV can download and install specific Python versions
- **Version Pinning**: `.python-version` files for project-specific Python versions
- **Multiple Python Support**: Can manage multiple Python installations simultaneously
- **Platform Independence**: Works consistently across macOS, Linux, and Windows

### 2. Virtual Environment Management
- **Fast Creation**: UV creates virtual environments 10-100x faster than traditional tools
- **Automatic Activation**: Can detect and use project virtual environments
- **Isolated Environments**: Complete isolation from system Python

### 3. Dependency Resolution
- **Lock Files**: `uv.lock` provides deterministic dependency resolution
- **Resolution Caching**: Caches dependency metadata for fast resolution
- **Conflict Resolution**: Advanced solver for complex dependency graphs
- **Platform-Specific Resolution**: Can resolve for different platforms/Python versions

### 4. Project Management
- **Project Initialization**: `uv init` creates standardized project structure
- **Build System**: Integrated build backend for Python packages
- **Script Running**: `uv run` executes scripts in proper environment
- **Tool Management**: `uv tool` for managing CLI tools in isolation

## DHT Integration Strategy

### Phase 1: Core UV Integration (Immediate)

#### 1.1 Environment Detection and Setup
```python
class UVEnvironmentManager:
    """Manages Python environments using UV."""

    def detect_python_version(self, project_path: Path) -> str:
        """Detect required Python version from project files."""
        # Check .python-version
        # Check pyproject.toml requires-python
        # Check setup.py python_requires
        # Return specific version or constraint

    def ensure_python_available(self, version: str) -> Path:
        """Ensure Python version is available, installing if needed."""
        # Use uv python install if version not found
        # Return path to Python executable

    def create_environment(self, project_path: Path, python_version: str):
        """Create UV-managed virtual environment."""
        # uv venv --python {version}
        # Store environment metadata
```

#### 1.2 Dependency Management
```python
class UVDependencyManager:
    """Manages dependencies using UV."""

    def analyze_dependencies(self, project_path: Path) -> Dict[str, Any]:
        """Analyze project dependencies."""
        # Parse requirements.txt, pyproject.toml, etc.
        # Identify dependency groups (runtime, dev, test)
        # Detect version conflicts

    def install_dependencies(self, project_path: Path, groups: List[str] = None):
        """Install dependencies using UV."""
        # uv sync for lock file
        # uv pip install for requirements
        # Handle optional dependency groups

    def generate_lock_file(self, project_path: Path):
        """Generate deterministic lock file."""
        # uv lock to create uv.lock
        # Captures exact versions for reproducibility
```

### Phase 2: Intelligent Configuration (Next Sprint)

#### 2.1 Project Type Detection
```python
class ProjectTypeDetector:
    """Detect project type and configure accordingly."""

    PROJECT_PATTERNS = {
        "django": {
            "files": ["manage.py", "settings.py"],
            "imports": ["django"],
            "uv_config": {
                "dev_dependencies": ["django-debug-toolbar", "django-extensions"],
                "scripts": {
                    "dev": "python manage.py runserver",
                    "test": "python manage.py test",
                    "migrate": "python manage.py migrate"
                }
            }
        },
        "fastapi": {
            "files": ["main.py", "app.py"],
            "imports": ["fastapi"],
            "uv_config": {
                "dev_dependencies": ["pytest-asyncio", "httpx"],
                "scripts": {
                    "dev": "uvicorn main:app --reload",
                    "test": "pytest",
                    "prod": "uvicorn main:app --host 0.0.0.0"
                }
            }
        },
        # More patterns...
    }

    def detect_and_configure(self, project_path: Path):
        """Detect project type and apply UV configuration."""
        # Use project analyzer results
        # Match against patterns
        # Generate appropriate pyproject.toml sections
        # Create useful script shortcuts
```

#### 2.2 Cross-Project Dependency Resolution
```python
class CrossProjectResolver:
    """Resolve dependencies across multiple related projects."""

    def analyze_workspace(self, workspace_path: Path) -> Dict[str, Any]:
        """Analyze multi-project workspace."""
        # Detect monorepo structure
        # Find shared dependencies
        # Identify version conflicts

    def create_workspace_lock(self, workspace_path: Path):
        """Create unified lock for workspace."""
        # UV workspace support (future feature)
        # Coordinate versions across projects
```

### Phase 3: Advanced Features (Future)

#### 3.1 Platform-Specific Builds
```python
class PlatformBuilder:
    """Build for specific platforms using UV."""

    def build_for_platform(self, project_path: Path, platform: str):
        """Build project for specific platform."""
        # Use UV's platform resolution
        # Generate platform-specific lock files
        # Handle binary dependencies
```

#### 3.2 Reproducible Environments
```python
class EnvironmentReproducer:
    """Reproduce exact environments across machines."""

    def capture_environment(self, project_path: Path) -> Dict[str, Any]:
        """Capture complete environment state."""
        # Python version
        # All dependencies with hashes
        # System dependencies (for DHT to handle)
        # Environment variables

    def reproduce_environment(self, project_path: Path, state: Dict[str, Any]):
        """Reproduce environment from captured state."""
        # Install exact Python version
        # Install dependencies from lock
        # Verify checksums
        # Report any discrepancies
```

## Implementation Plan

### Step 1: UV Wrapper Module (Week 1)
Create `dht/modules/uv_manager.py`:
```python
class UVManager:
    """Central UV integration for DHT."""

    def __init__(self):
        self.uv_path = self._find_uv_executable()
        self._verify_uv_version()

    def run_command(self, args: List[str], cwd: Path = None) -> Dict[str, Any]:
        """Run UV command and parse output."""
        # Execute UV with proper error handling
        # Parse JSON output when available
        # Return structured results
```

### Step 2: Project Configuration Generator (Week 2)
Create `dht/modules/project_configurator.py`:
```python
class ProjectConfigurator:
    """Generate UV-compatible project configuration."""

    def generate_pyproject_toml(self, analysis: Dict[str, Any]) -> str:
        """Generate pyproject.toml from project analysis."""
        # Create [project] section
        # Add dependencies
        # Add UV-specific configuration
        # Add useful scripts
```

### Step 3: Integration with DHT Commands (Week 3)
Update existing DHT commands:
```bash
# dhtl setup - Now uses UV
- Detects Python version requirement
- Downloads Python if needed via UV
- Creates virtual environment with UV
- Installs dependencies with UV

# dhtl restore - Reproducible environments
- Reads uv.lock
- Installs exact Python version
- Restores exact dependencies
- Validates environment integrity

# New: dhtl dockerize
- Generates Dockerfile using UV
- Multi-stage build for minimal images
- Handles compiled dependencies
```

## Benefits of UV Integration

### 1. Speed
- 10-100x faster than pip for dependency resolution
- Parallel downloads and installations
- Aggressive caching reduces redundant work

### 2. Determinism
- Lock files ensure exact same versions everywhere
- Platform-specific resolution when needed
- Consistent Python version management

### 3. Simplicity
- Single tool for Python versions, virtual environments, and packages
- No need for pyenv, virtualenv, pip-tools separately
- Consistent commands across platforms

### 4. Modern Python Packaging
- Native pyproject.toml support
- PEP 517/518 compliance
- Built-in build backend

## DHT Commands Enhanced by UV

### Existing Commands - Enhanced
```bash
dhtl setup          # Now 10x faster with UV
dhtl restore        # Truly deterministic with uv.lock
dhtl test          # Runs in UV-managed environment
dhtl build         # Uses UV's build backend
```

### New Commands - UV Powered
```bash
dhtl env create    # Create environment for any Python version
dhtl env list      # List all UV-managed environments
dhtl deps add      # Add dependency and update lock
dhtl deps sync     # Sync environment with lock file
dhtl deps outdated # Check for outdated dependencies
dhtl python pin    # Pin Python version for project
dhtl run <script>  # Run script in project environment
```

## Error Handling and Edge Cases

### 1. UV Not Available
```python
if not self.uv_available:
    # Fall back to traditional tools
    # Warn about reduced functionality
    # Suggest UV installation
```

### 2. Python Version Not Available
```python
try:
    self.ensure_python_version(version)
except PythonVersionNotFound:
    # Attempt to download via UV
    # If fails, provide clear instructions
    # Suggest alternatives (Docker, system package)
```

### 3. Dependency Conflicts
```python
try:
    self.resolve_dependencies()
except DependencyConflict as e:
    # Parse UV's conflict explanation
    # Provide actionable suggestions
    # Offer to relax constraints
```

## Testing Strategy

### 1. Unit Tests
- Mock UV commands
- Test parsing of UV output
- Verify configuration generation

### 2. Integration Tests
- Test with real UV installation
- Multiple Python versions
- Complex dependency scenarios

### 3. Cross-Platform Tests
- Windows, macOS, Linux
- Different Python versions
- Various project types

## Migration Path for Existing Projects

### 1. Analyze Current Setup
- Detect existing virtual environments
- Parse requirements files
- Identify Python version

### 2. Generate UV Configuration
- Create pyproject.toml if missing
- Generate uv.lock from requirements
- Add helpful script shortcuts

### 3. Provide Migration Commands
```bash
dhtl migrate-to-uv  # Automated migration
dhtl validate-env   # Verify environment matches
```

## Future Enhancements

### 1. Workspace Support
- When UV adds workspace features
- Coordinate multiple projects
- Shared dependency management

### 2. Binary Package Optimization
- Pre-built wheels caching
- Platform-specific optimizations
- Reduced Docker image sizes

### 3. CI/CD Integration
- GitHub Actions with UV
- Cached UV installations
- Matrix testing across versions

## Conclusion

UV integration will make DHT significantly faster, more reliable, and easier to use. By leveraging UV's modern approach to Python packaging, DHT can provide truly deterministic, cross-platform project setup and management. The phased approach allows immediate benefits while building toward advanced features.
