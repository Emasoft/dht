# DHT Setup and Regeneration Technical Plan

## Overview

This document provides a comprehensive technical plan for DHT's setup and regeneration process, ensuring deterministic environment creation across all platforms and user configurations.

## Core Principles

1. **Information Hierarchy**: Gather data from most specific (project files) to most general (system configuration)
2. **Minimal Storage**: Only store in .dhtconfig what cannot be reliably inferred
3. **Deterministic Resolution**: Same inputs always produce identical environments
4. **Platform Abstraction**: Hide platform differences behind intelligent mappings
5. **Migration Support**: Gracefully handle existing projects with different technology stacks

## Phase 1: Information Collection and Analysis

### 1.1 Project File Analysis

#### Step 1: Project Root Detection
```python
def find_project_root(start_path="."):
    """Find project root by looking for markers in priority order"""
    markers = [
        ".git",                    # Git repository
        "pyproject.toml",          # Modern Python project
        "setup.py",                # Legacy Python project
        "setup.cfg",               # Alternative Python config
        "requirements.txt",        # Basic Python project
        "package.json",            # Node.js component
        "Cargo.toml",              # Rust component
        "go.mod",                  # Go component
        "CMakeLists.txt",          # C++ component
        "Makefile",                # Generic build
    ]

    # Walk up directory tree looking for markers
    current = Path(start_path).resolve()
    while current != current.parent:
        for marker in markers:
            if (current / marker).exists():
                return current
        current = current.parent

    return Path(start_path).resolve()  # Default to start path
```

#### Step 2: Parse Python Configuration Files
```python
class ProjectConfigParser:
    def parse_pyproject_toml(self, path):
        """Extract all relevant information from pyproject.toml"""
        with open(path, 'rb') as f:
            data = tomli.load(f)

        config = {
            'project_name': data.get('project', {}).get('name'),
            'version': data.get('project', {}).get('version'),
            'python_requires': data.get('project', {}).get('requires-python'),
            'dependencies': data.get('project', {}).get('dependencies', []),
            'optional_dependencies': data.get('project', {}).get('optional-dependencies', {}),
            'build_system': data.get('build-system', {}).get('build-backend'),
            'tools': {}
        }

        # Extract tool configurations
        for tool in ['pytest', 'mypy', 'ruff', 'black', 'isort', 'coverage']:
            if tool in data.get('tool', {}):
                config['tools'][tool] = data['tool'][tool]

        return config

    def parse_setup_py(self, path):
        """Parse setup.py using AST to avoid execution"""
        with open(path) as f:
            tree = ast.parse(f.read())

        # Extract setup() call arguments
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and getattr(node.func, 'id', None) == 'setup':
                return self._extract_setup_args(node)

        return {}

    def parse_requirements(self, path):
        """Parse requirements.txt with support for -r includes"""
        requirements = []

        with open(path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if line.startswith('-r '):
                        # Recursively parse included file
                        include_path = Path(path).parent / line[3:]
                        requirements.extend(self.parse_requirements(include_path))
                    else:
                        requirements.append(line)

        return requirements
```

#### Step 3: Detect Project Type and Framework
```python
class ProjectTypeDetector:
    def detect(self, project_root):
        """Detect project type and framework through heuristics"""
        indicators = {
            'django': ['manage.py', 'django', 'settings.py', 'wsgi.py'],
            'flask': ['app.py', 'flask', 'application.py'],
            'fastapi': ['main.py', 'fastapi', 'uvicorn'],
            'streamlit': ['streamlit', '.streamlit/'],
            'jupyter': ['*.ipynb', 'jupyter'],
            'cli': ['click', 'typer', 'argparse', '__main__.py'],
            'library': ['__init__.py', 'no main.py', 'no app.py'],
            'data-science': ['pandas', 'numpy', 'scikit-learn', 'tensorflow', 'torch'],
        }

        detected_types = []

        # Check file presence
        for type_name, markers in indicators.items():
            score = 0
            for marker in markers:
                if '*' in marker:
                    # Glob pattern
                    if list(project_root.glob(marker)):
                        score += 1
                elif (project_root / marker).exists():
                    score += 1
                elif self._check_import(project_root, marker):
                    score += 1

            if score >= len(markers) / 2:
                detected_types.append((type_name, score))

        # Return highest scoring type
        if detected_types:
            return max(detected_types, key=lambda x: x[1])[0]

        return 'generic'
```

#### Step 4: Import Analysis for Dependency Inference
```python
class ImportAnalyzer:
    def __init__(self):
        self.stdlib_modules = set(sys.stdlib_module_names)
        self.import_to_package = {
            'cv2': 'opencv-python',
            'sklearn': 'scikit-learn',
            'PIL': 'Pillow',
            'yaml': 'PyYAML',
            # ... comprehensive mapping
        }

    def analyze_imports(self, project_root):
        """Analyze all Python files to find imports"""
        imports = set()

        for py_file in project_root.rglob('*.py'):
            if '.venv' in str(py_file) or '__pycache__' in str(py_file):
                continue

            try:
                with open(py_file) as f:
                    tree = ast.parse(f.read())

                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for name in node.names:
                            imports.add(name.name.split('.')[0])
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            imports.add(node.module.split('.')[0])
            except:
                continue

        # Filter out stdlib and local modules
        external_imports = imports - self.stdlib_modules

        # Map to package names
        packages = set()
        for imp in external_imports:
            package = self.import_to_package.get(imp, imp)
            packages.add(package)

        return packages
```

### 1.2 System Environment Analysis

#### Step 5: Comprehensive System Information Gathering
```python
class SystemAnalyzer:
    def analyze(self):
        """Gather comprehensive system information"""
        return {
            'platform': {
                'system': platform.system(),
                'release': platform.release(),
                'version': platform.version(),
                'machine': platform.machine(),
                'processor': platform.processor(),
                'python_implementation': platform.python_implementation(),
            },
            'python': {
                'version': sys.version,
                'executable': sys.executable,
                'prefix': sys.prefix,
                'available_versions': self._find_python_versions(),
            },
            'package_managers': {
                'pip': self._check_tool('pip', '--version'),
                'uv': self._check_tool('uv', '--version'),
                'poetry': self._check_tool('poetry', '--version'),
                'pipenv': self._check_tool('pipenv', '--version'),
                'conda': self._check_tool('conda', '--version'),
            },
            'system_package_managers': self._detect_system_package_managers(),
            'development_tools': self._detect_dev_tools(),
            'environment_variables': self._get_relevant_env_vars(),
            'paths': {
                'PATH': os.environ.get('PATH', '').split(os.pathsep),
                'PYTHONPATH': os.environ.get('PYTHONPATH', '').split(os.pathsep),
            }
        }

    def _find_python_versions(self):
        """Find all available Python versions"""
        versions = {}

        # Check common Python locations
        possible_pythons = ['python', 'python3'] + [f'python3.{i}' for i in range(6, 15)]

        for py_cmd in possible_pythons:
            try:
                result = subprocess.run([py_cmd, '--version'],
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    version = result.stdout.strip().split()[-1]
                    versions[py_cmd] = version
            except:
                pass

        # Check pyenv
        if shutil.which('pyenv'):
            try:
                result = subprocess.run(['pyenv', 'versions', '--bare'],
                                      capture_output=True, text=True)
                for version in result.stdout.strip().split('\n'):
                    versions[f'pyenv:{version}'] = version
            except:
                pass

        # Check UV python list
        if shutil.which('uv'):
            try:
                result = subprocess.run(['uv', 'python', 'list'],
                                      capture_output=True, text=True)
                # Parse UV output
                for line in result.stdout.strip().split('\n'):
                    if 'Python' in line:
                        # Extract version from UV format
                        parts = line.split()
                        if len(parts) >= 2:
                            versions[f'uv:{parts[1]}'] = parts[1]
            except:
                pass

        return versions

    def _detect_system_package_managers(self):
        """Detect available system package managers"""
        managers = {}

        checks = {
            'apt': ['apt', '--version'],
            'yum': ['yum', '--version'],
            'dnf': ['dnf', '--version'],
            'brew': ['brew', '--version'],
            'choco': ['choco', '--version'],
            'scoop': ['scoop', '--version'],
            'pacman': ['pacman', '--version'],
            'zypper': ['zypper', '--version'],
        }

        for name, cmd in checks.items():
            if shutil.which(cmd[0]):
                try:
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    if result.returncode == 0:
                        managers[name] = result.stdout.strip().split('\n')[0]
                except:
                    pass

        return managers

    def _detect_dev_tools(self):
        """Detect installed development tools"""
        tools = {}

        # Compilers and build tools
        compiler_checks = {
            'gcc': ['gcc', '--version'],
            'clang': ['clang', '--version'],
            'cl': ['cl'],  # MSVC
            'make': ['make', '--version'],
            'cmake': ['cmake', '--version'],
            'ninja': ['ninja', '--version'],
            'cargo': ['cargo', '--version'],
            'go': ['go', 'version'],
            'node': ['node', '--version'],
            'npm': ['npm', '--version'],
            'yarn': ['yarn', '--version'],
            'pnpm': ['pnpm', '--version'],
        }

        # Node version managers
        node_managers = {
            'nvm': self._check_nvm,
            'n': ['n', '--version'],
            'fnm': ['fnm', '--version'],
            'volta': ['volta', '--version'],
            'asdf': ['asdf', '--version'],
        }

        for name, cmd in {**compiler_checks, **node_managers}.items():
            if callable(cmd):
                tools[name] = cmd()
            elif shutil.which(cmd[0]):
                try:
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    if result.returncode == 0:
                        tools[name] = result.stdout.strip().split('\n')[0]
                except:
                    pass

        return tools

    def _check_nvm(self):
        """Special check for nvm which is a shell function"""
        nvm_dir = os.environ.get('NVM_DIR', os.path.expanduser('~/.nvm'))
        if os.path.exists(nvm_dir):
            return f"installed at {nvm_dir}"
        return None
```

### 1.3 User Configuration Analysis

#### Step 6: Parse User Dotfiles and Global Configurations
```python
class UserConfigAnalyzer:
    def analyze(self):
        """Analyze user configuration files"""
        home = Path.home()

        configs = {
            'git': self._parse_gitconfig(),
            'npm': self._parse_npmrc(),
            'pip': self._parse_pip_conf(),
            'pypi': self._parse_pypirc(),
            'shell': self._detect_shell_config(),
            'editor': self._detect_editor(),
            'tools': {}
        }

        # Check tool-specific configs
        tool_configs = {
            '.pylintrc': 'pylint',
            '.flake8': 'flake8',
            '.mypy.ini': 'mypy',
            '.black': 'black',
            '.isort.cfg': 'isort',
            '.pre-commit-config.yaml': 'pre-commit',
        }

        for config_file, tool in tool_configs.items():
            for location in [Path.cwd(), home]:
                config_path = location / config_file
                if config_path.exists():
                    configs['tools'][tool] = str(config_path)

        return configs

    def _parse_gitconfig(self):
        """Parse git configuration"""
        try:
            result = subprocess.run(['git', 'config', '--list'],
                                  capture_output=True, text=True)
            if result.returncode == 0:
                config = {}
                for line in result.stdout.strip().split('\n'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        config[key] = value
                return config
        except:
            pass
        return {}
```

## Phase 2: Migration and Standardization

### 2.1 Technology Stack Migration

#### Step 7: Package Manager Migration
```python
class PackageManagerMigrator:
    def migrate_to_uv(self, project_root, current_manager):
        """Migrate from any package manager to UV"""
        migrations = {
            'pip': self._migrate_from_pip,
            'poetry': self._migrate_from_poetry,
            'pipenv': self._migrate_from_pipenv,
            'conda': self._migrate_from_conda,
        }

        if current_manager in migrations:
            return migrations[current_manager](project_root)

        return self._migrate_from_pip(project_root)  # Default

    def _migrate_from_pip(self, project_root):
        """Migrate from pip to UV"""
        steps = []

        # Check for requirements files
        req_files = ['requirements.txt', 'requirements-dev.txt',
                     'requirements-test.txt', 'requirements-prod.txt']

        existing_reqs = [f for f in req_files if (project_root / f).exists()]

        if existing_reqs:
            # Create pyproject.toml if missing
            if not (project_root / 'pyproject.toml').exists():
                steps.append({
                    'action': 'create_pyproject_toml',
                    'reason': 'Modern Python packaging standard',
                    'command': self._create_minimal_pyproject_toml
                })

            # Convert requirements to dependencies
            steps.append({
                'action': 'convert_requirements',
                'files': existing_reqs,
                'command': lambda: self._convert_requirements_to_pyproject(project_root, existing_reqs)
            })

        # Create UV lock file
        steps.append({
            'action': 'create_uv_lock',
            'command': lambda: subprocess.run(['uv', 'lock'], cwd=project_root)
        })

        return steps

    def _migrate_from_poetry(self, project_root):
        """Migrate from Poetry to UV"""
        steps = []

        if (project_root / 'poetry.lock').exists():
            # Export requirements
            steps.append({
                'action': 'export_poetry_requirements',
                'command': lambda: subprocess.run([
                    'poetry', 'export', '-f', 'requirements.txt',
                    '-o', 'requirements.txt', '--without-hashes'
                ], cwd=project_root)
            })

            # Convert pyproject.toml poetry section to standard
            steps.append({
                'action': 'convert_poetry_pyproject',
                'command': lambda: self._convert_poetry_pyproject(project_root)
            })

        return steps
```

#### Step 8: Test Framework Migration
```python
class TestFrameworkMigrator:
    def migrate_to_pytest(self, project_root):
        """Migrate from unittest or nose to pytest"""
        test_files = list(project_root.rglob('test*.py')) + \
                    list(project_root.rglob('*_test.py'))

        migration_plan = {
            'files_to_convert': [],
            'new_files': [],
            'configuration': {}
        }

        for test_file in test_files:
            if self._uses_unittest(test_file):
                migration_plan['files_to_convert'].append({
                    'file': test_file,
                    'changes': self._analyze_unittest_file(test_file)
                })

        # Create pytest.ini or add to pyproject.toml
        migration_plan['configuration'] = {
            'pytest.ini': self._generate_pytest_config(project_root),
            'pyproject.toml': {
                'tool.pytest.ini_options': {
                    'testpaths': ['tests'],
                    'python_files': ['test_*.py', '*_test.py'],
                    'python_functions': ['test_*'],
                    'addopts': '-v --tb=short --strict-markers'
                }
            }
        }

        return migration_plan

    def _uses_unittest(self, file_path):
        """Check if file uses unittest"""
        try:
            with open(file_path) as f:
                content = f.read()
                return 'import unittest' in content or 'from unittest' in content
        except:
            return False

    def _analyze_unittest_file(self, file_path):
        """Analyze unittest file for conversion"""
        changes = []

        # Common conversions
        conversions = {
            'self.assertEqual': 'assert',
            'self.assertTrue': 'assert',
            'self.assertFalse': 'assert not',
            'self.assertIn': 'assert ... in ...',
            'self.assertRaises': 'pytest.raises',
            'setUp': 'setup_method',
            'tearDown': 'teardown_method',
            'TestCase': '# Remove TestCase inheritance',
        }

        with open(file_path) as f:
            content = f.read()

        for old, new in conversions.items():
            if old in content:
                changes.append(f"Convert {old} to {new}")

        return changes
```

### 2.2 Tool Standardization

#### Step 9: Development Tool Configuration
```python
class ToolStandardizer:
    def standardize_tools(self, project_root, project_type):
        """Ensure standard tool configuration"""

        # Base tools for all projects
        base_tools = {
            'pytest': '>=7.4.0',
            'pytest-cov': '>=4.1.0',
            'mypy': '>=1.5.0',
            'ruff': '>=0.1.0',
            'black': '>=23.7.0',
            'pre-commit': '>=3.3.3',
        }

        # Type-specific tools
        type_tools = {
            'django': {
                'django-debug-toolbar': '*',
                'django-extensions': '*',
                'pytest-django': '>=4.5.0',
            },
            'fastapi': {
                'pytest-asyncio': '>=0.21.0',
                'httpx': '>=0.24.0',
            },
            'data-science': {
                'jupyter': '>=1.0.0',
                'nbqa': '>=1.7.0',
                'notebook': '>=7.0.0',
            }
        }

        tools = {**base_tools, **type_tools.get(project_type, {})}

        # Configure each tool
        configurations = {
            'ruff': self._configure_ruff(project_root),
            'mypy': self._configure_mypy(project_root),
            'black': self._configure_black(project_root),
            'pytest': self._configure_pytest(project_root),
            'pre-commit': self._configure_precommit(project_root),
        }

        return tools, configurations

    def _configure_ruff(self, project_root):
        """Generate ruff configuration"""
        return {
            'pyproject.toml': {
                'tool.ruff': {
                    'line-length': 88,
                    'target-version': 'py310',
                    'select': ['E', 'F', 'I', 'N', 'UP', 'B', 'C4', 'DTZ', 'T10', 'ISC', 'ICN', 'PIE', 'PT', 'RET', 'SIM', 'TID', 'TCH', 'PD', 'PGH', 'PL', 'RSE', 'RUF'],
                    'ignore': ['E501'],  # Line length handled by formatter
                    'unfixable': ['B'],  # Don't auto-fix potential bugs
                }
            }
        }

    def _configure_precommit(self, project_root):
        """Generate pre-commit configuration"""
        return {
            '.pre-commit-config.yaml': '''
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-merge-conflict

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.5.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]

  - repo: https://github.com/shellcheck-py/shellcheck-py
    rev: v0.9.0.6
    hooks:
      - id: shellcheck
        args: [--severity=error]  # Only fail on errors, not warnings
'''
        }
```

## Phase 3: Environment Creation

### 3.1 Deterministic Environment Setup

#### Step 10: Create Virtual Environment with Exact Python Version
```python
class EnvironmentCreator:
    def create_deterministic_venv(self, project_root, python_version):
        """Create virtual environment with exact Python version"""

        # Step 1: Ensure Python version is available
        python_path = self._ensure_python_version(python_version)

        # Step 2: Create virtual environment
        venv_path = project_root / '.venv'

        if venv_path.exists():
            # Verify existing venv Python version
            existing_version = self._get_venv_python_version(venv_path)
            if existing_version != python_version:
                print(f"Removing incompatible venv (Python {existing_version})")
                shutil.rmtree(venv_path)

        # Use UV to create venv with specific Python
        subprocess.run([
            'uv', 'venv',
            '--python', python_version,
            str(venv_path)
        ], check=True)

        # Step 3: Install base tools
        self._install_base_tools(venv_path)

        return venv_path

    def _ensure_python_version(self, version):
        """Ensure specific Python version is available"""
        # First, check if UV has it
        result = subprocess.run(
            ['uv', 'python', 'list'],
            capture_output=True,
            text=True
        )

        if version in result.stdout:
            return f"python{version}"

        # Install via UV
        print(f"Installing Python {version} via UV...")
        subprocess.run(['uv', 'python', 'install', version], check=True)

        return f"python{version}"

    def _install_base_tools(self, venv_path):
        """Install DHT base tools in venv"""
        pip = venv_path / 'bin' / 'pip'

        # Base tools that should be in every DHT-managed environment
        base_packages = [
            'uv>=0.1.0',  # UV in venv for complete isolation
            'pip>=23.0',
            'setuptools>=68.0',
            'wheel>=0.41.0',
        ]

        subprocess.run([
            str(pip), 'install', '--upgrade'
        ] + base_packages, check=True)
```

#### Step 11: Install Dependencies with Lock File
```python
class DependencyInstaller:
    def install_locked_dependencies(self, project_root, venv_path):
        """Install dependencies exactly as specified in lock files"""

        # Activate venv for UV
        env = os.environ.copy()
        env['VIRTUAL_ENV'] = str(venv_path)

        # Step 1: Use UV lock file if available
        if (project_root / 'uv.lock').exists():
            print("Installing from uv.lock...")
            subprocess.run(
                ['uv', 'sync', '--frozen'],
                cwd=project_root,
                env=env,
                check=True
            )
            return True

        # Step 2: Fall back to requirements.lock or requirements.txt
        lock_files = [
            'requirements.lock',
            'requirements-lock.txt',
            'requirements.txt'
        ]

        for lock_file in lock_files:
            if (project_root / lock_file).exists():
                print(f"Installing from {lock_file}...")

                # Use --require-hashes if .lock file
                args = ['uv', 'pip', 'install', '-r', lock_file]
                if '.lock' in lock_file:
                    args.append('--require-hashes')

                subprocess.run(
                    args,
                    cwd=project_root,
                    env=env,
                    check=True
                )
                return True

        return False

    def generate_lock_file(self, project_root):
        """Generate lock file from current dependencies"""
        print("Generating uv.lock file...")
        subprocess.run(['uv', 'lock'], cwd=project_root, check=True)
```

### 3.2 Platform-Specific Setup

#### Step 12: Install System Dependencies
```python
class SystemDependencyManager:
    def __init__(self):
        self.package_mappings = {
            'postgresql-client': {
                'darwin': {'brew': 'postgresql@14'},
                'ubuntu': {'apt': 'libpq-dev'},
                'debian': {'apt': 'libpq-dev'},
                'fedora': {'dnf': 'postgresql-devel'},
                'centos': {'yum': 'postgresql-devel'},
                'arch': {'pacman': 'postgresql-libs'},
                'windows': {'choco': 'postgresql14'},
            },
            'mysql-client': {
                'darwin': {'brew': 'mysql-client'},
                'ubuntu': {'apt': 'libmysqlclient-dev'},
                'fedora': {'dnf': 'mysql-devel'},
                'windows': {'choco': 'mysql'},
            },
            'redis': {
                'darwin': {'brew': 'redis'},
                'ubuntu': {'apt': 'redis-server'},
                'fedora': {'dnf': 'redis'},
                'windows': {'choco': 'redis-64'},
            },
            # ... more mappings
        }

    def install_system_dependencies(self, dependencies, platform_info):
        """Install platform-specific system dependencies"""
        os_type = platform_info['system'].lower()
        os_dist = self._get_distribution(platform_info)

        installed = []
        failed = []

        for dep in dependencies:
            if dep in self.package_mappings:
                mapping = self.package_mappings[dep].get(os_dist) or \
                         self.package_mappings[dep].get(os_type)

                if mapping:
                    success = self._install_package(mapping)
                    if success:
                        installed.append(dep)
                    else:
                        failed.append(dep)
                else:
                    failed.append(f"{dep} (no mapping for {os_dist})")

        return installed, failed

    def _install_package(self, mapping):
        """Install package using appropriate package manager"""
        for manager, package in mapping.items():
            if manager == 'brew' and shutil.which('brew'):
                return self._run_install(['brew', 'install', package])
            elif manager == 'apt' and shutil.which('apt'):
                return self._run_install(['sudo', 'apt', 'install', '-y', package])
            # ... other package managers

        return False
```

#### Step 13: Configure Development Tools
```python
class DevToolConfigurator:
    def configure_venv_tools(self, venv_path, project_root):
        """Configure development tools within venv"""

        # Step 1: Install tools as UV tools (isolated environments)
        tools_to_install = [
            ('ruff', '>=0.1.0'),
            ('mypy', '>=1.5.0'),
            ('black', '>=23.7.0'),
            ('pytest', '>=7.4.0'),
            ('pre-commit', '>=3.3.3'),
        ]

        for tool, version in tools_to_install:
            self._install_uv_tool(tool, version, venv_path)

        # Step 2: Create wrapper scripts in venv/bin
        self._create_tool_wrappers(venv_path, tools_to_install)

        # Step 3: Configure git hooks
        if (project_root / '.git').exists():
            self._setup_git_hooks(venv_path, project_root)

    def _install_uv_tool(self, tool, version, venv_path):
        """Install tool using UV's tool management"""
        # UV tools are installed in isolated environments
        subprocess.run([
            'uv', 'tool', 'install',
            f'{tool}{version}',
            '--force'  # Ensure we get the exact version
        ], check=True)

    def _create_tool_wrappers(self, venv_path, tools):
        """Create wrapper scripts that use UV tools"""
        bin_dir = venv_path / 'bin'

        wrapper_template = '''#!/bin/bash
# Auto-generated wrapper for {tool}
exec uv tool run {tool} "$@"
'''

        for tool, _ in tools:
            wrapper_path = bin_dir / tool
            wrapper_path.write_text(wrapper_template.format(tool=tool))
            wrapper_path.chmod(0o755)
```

## Phase 4: Configuration Generation

### 4.1 Generate .dhtconfig

#### Step 14: Create Minimal .dhtconfig
```python
class DHTConfigGenerator:
    def generate(self, collected_info):
        """Generate minimal .dhtconfig with only non-inferrable information"""

        config = {
            'version': '2.0',
            'dht_version': get_dht_version(),
            'fingerprint': {
                'created_at': datetime.utcnow().isoformat() + 'Z',
                'created_by': f'DHT/{get_dht_version()}',
                'platform': f"{platform.system().lower()}-{platform.machine()}",
            }
        }

        # Only add Python version if it can't be inferred from pyproject.toml
        if not collected_info['project'].get('python_requires'):
            config['python'] = {
                'version': collected_info['python']['exact_version']
            }

        # Only add system deps that aren't standard
        non_standard_deps = self._identify_non_standard_deps(collected_info)
        if non_standard_deps:
            config['platform_deps'] = non_standard_deps

        # Add validation checksums
        config['validation'] = {
            'venv_checksum': self._generate_venv_checksum(collected_info),
            'config_checksum': self._generate_config_checksum(collected_info),
        }

        # Only add tools if non-standard versions required
        non_standard_tools = self._identify_non_standard_tools(collected_info)
        if non_standard_tools:
            config['tools'] = non_standard_tools

        return config

    def _identify_non_standard_deps(self, info):
        """Identify system dependencies that can't be inferred"""
        # Standard deps that can be inferred from Python packages
        inferrable_deps = {
            'psycopg2': ['postgresql-client'],
            'mysqlclient': ['mysql-client'],
            'pillow': ['libjpeg', 'libpng'],
            # ... more mappings
        }

        required_system_deps = info.get('system_dependencies', [])
        non_inferrable = []

        for dep in required_system_deps:
            is_inferrable = False
            for py_pkg, sys_deps in inferrable_deps.items():
                if dep in sys_deps and py_pkg in info['project']['dependencies']:
                    is_inferrable = True
                    break

            if not is_inferrable:
                non_inferrable.append(dep)

        if non_inferrable:
            return self._create_platform_dep_mapping(non_inferrable)

        return None
```

### 4.2 Environment Validation

#### Step 15: Generate and Verify Environment Checksum
```python
class EnvironmentValidator:
    def generate_checksum(self, venv_path, project_root):
        """Generate deterministic checksum of environment"""

        components = []

        # 1. Python version (exact)
        python_exe = venv_path / 'bin' / 'python'
        result = subprocess.run(
            [str(python_exe), '--version'],
            capture_output=True,
            text=True
        )
        components.append(f"python:{result.stdout.strip()}")

        # 2. Installed packages with versions and hashes
        result = subprocess.run(
            [str(venv_path / 'bin' / 'pip'), 'freeze', '--all'],
            capture_output=True,
            text=True
        )
        packages = sorted(result.stdout.strip().split('\n'))
        components.extend(packages)

        # 3. Package hashes (for extra security)
        result = subprocess.run(
            [str(venv_path / 'bin' / 'pip'), 'show', '-f'] +
            [pkg.split('==')[0] for pkg in packages if '==' in pkg],
            capture_output=True,
            text=True
        )

        # Extract file hashes
        for line in result.stdout.split('\n'):
            if line.strip().endswith('.py'):
                file_path = venv_path / 'lib' / line.strip()
                if file_path.exists():
                    components.append(f"file:{self._hash_file(file_path)}")

        # 4. Tool configurations
        config_files = [
            'pyproject.toml',
            'setup.cfg',
            '.pre-commit-config.yaml',
            'pytest.ini',
            '.flake8',
            'mypy.ini',
        ]

        for config_file in config_files:
            config_path = project_root / config_file
            if config_path.exists():
                components.append(f"config:{config_file}:{self._hash_file(config_path)}")

        # Generate final checksum
        combined = '\n'.join(components)
        return hashlib.sha256(combined.encode()).hexdigest()

    def validate_environment(self, venv_path, project_root, expected_checksum):
        """Validate environment matches expected checksum"""
        current_checksum = self.generate_checksum(venv_path, project_root)

        if current_checksum == expected_checksum:
            return True, "Environment validated successfully"

        # Generate detailed diff report
        diff_report = self._generate_diff_report(
            venv_path,
            project_root,
            expected_checksum,
            current_checksum
        )

        return False, diff_report
```

## Phase 5: Regeneration Process

### 5.1 Complete Regeneration Flow

#### Step 16: Implement dhtl regenerate Command
```python
class EnvironmentRegenerator:
    def regenerate(self, project_root):
        """Complete environment regeneration from .dhtconfig"""

        # Step 1: Load .dhtconfig
        config_path = project_root / '.dhtconfig'
        if not config_path.exists():
            raise FileNotFoundError("No .dhtconfig found. Run 'dhtl setup' first.")

        with open(config_path) as f:
            config = yaml.safe_load(f)

        # Step 2: Validate DHT version compatibility
        self._check_dht_compatibility(config)

        # Step 3: Collect current system info
        system_info = SystemAnalyzer().analyze()

        # Step 4: Determine Python version
        python_version = self._determine_python_version(config, project_root)

        # Step 5: Create virtual environment
        print(f"Creating virtual environment with Python {python_version}...")
        venv_path = EnvironmentCreator().create_deterministic_venv(
            project_root,
            python_version
        )

        # Step 6: Install system dependencies
        if 'platform_deps' in config:
            print("Installing platform-specific dependencies...")
            platform_key = system_info['platform']['system'].lower()
            if platform_key in config['platform_deps']:
                SystemDependencyManager().install_system_dependencies(
                    config['platform_deps'][platform_key],
                    system_info['platform']
                )

        # Step 7: Install Python dependencies
        print("Installing Python dependencies...")
        DependencyInstaller().install_locked_dependencies(project_root, venv_path)

        # Step 8: Configure development tools
        print("Configuring development tools...")
        DevToolConfigurator().configure_venv_tools(venv_path, project_root)

        # Step 9: Setup additional languages if needed
        if 'languages' in config:
            self._setup_additional_languages(config['languages'], venv_path)

        # Step 10: Validate regenerated environment
        if 'validation' in config and 'venv_checksum' in config['validation']:
            print("Validating environment...")
            validator = EnvironmentValidator()
            is_valid, report = validator.validate_environment(
                venv_path,
                project_root,
                config['validation']['venv_checksum']
            )

            if not is_valid:
                print(f"Warning: Environment validation failed:\n{report}")
                if not self._prompt_continue():
                    raise EnvironmentError("Environment validation failed")

        # Step 11: Create activation script with checks
        self._create_activation_script(venv_path, project_root)

        print("\n✅ Environment regeneration complete!")
        print(f"Activate with: source {venv_path}/bin/activate")

        return True

    def _setup_additional_languages(self, languages, venv_path):
        """Setup additional language runtimes in venv"""
        for lang, spec in languages.items():
            if lang == 'node':
                self._setup_node(spec, venv_path)
            elif lang == 'rust':
                self._setup_rust(spec, venv_path)
            elif lang == 'go':
                self._setup_go(spec, venv_path)

    def _setup_node(self, spec, venv_path):
        """Setup Node.js in venv using UV tools or other methods"""
        version = spec.get('version', 'latest')
        installer = spec.get('installer', 'uv tool')

        if installer == 'uv tool':
            # Install node via UV tool
            subprocess.run([
                'uv', 'tool', 'install',
                f'node@{version}',
                '--force'
            ])

            # Create wrapper in venv
            wrapper = venv_path / 'bin' / 'node'
            wrapper.write_text('#!/bin/bash\nexec uv tool run node "$@"\n')
            wrapper.chmod(0o755)
```

### 5.2 Smart Clone and Fork

#### Step 17: Implement dhtl clone and fork Commands
```python
class SmartCloner:
    def clone(self, url, target_dir=None):
        """Clone repository and regenerate environment"""

        # Step 1: Parse repository URL
        repo_info = self._parse_repo_url(url)

        if not target_dir:
            target_dir = repo_info['name']

        # Step 2: Clone repository
        print(f"Cloning {repo_info['full_name']}...")

        if shutil.which('gh') and 'github.com' in url:
            # Use GitHub CLI for better authentication
            subprocess.run(['gh', 'repo', 'clone', url, target_dir], check=True)
        else:
            # Fallback to git
            subprocess.run(['git', 'clone', url, target_dir], check=True)

        # Step 3: Enter directory
        project_root = Path(target_dir).resolve()
        os.chdir(project_root)

        # Step 4: Check for .dhtconfig
        if (project_root / '.dhtconfig').exists():
            print("\nFound .dhtconfig, regenerating environment...")
            EnvironmentRegenerator().regenerate(project_root)
        else:
            print("\nNo .dhtconfig found, running initial setup...")
            self._run_initial_setup(project_root)

        # Step 5: Show status
        self._show_project_status(project_root)

        return project_root

    def fork(self, url, target_dir=None):
        """Fork repository and regenerate environment"""

        # Step 1: Fork using gh CLI
        print(f"Forking repository...")
        result = subprocess.run(
            ['gh', 'repo', 'fork', url, '--clone=false'],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            raise RuntimeError(f"Failed to fork: {result.stderr}")

        # Extract forked repo URL from output
        fork_url = self._extract_fork_url(result.stdout)

        # Step 2: Clone the fork
        project_root = self.clone(fork_url, target_dir)

        # Step 3: Add upstream remote
        subprocess.run([
            'git', 'remote', 'add', 'upstream', url
        ], cwd=project_root, check=True)

        print(f"\nAdded upstream remote: {url}")

        return project_root
```

## Phase 6: Continuous Validation

### 6.1 Post-Activation Validation

#### Step 18: Create Activation Hooks
```python
class ActivationHookGenerator:
    def create_hooks(self, venv_path, project_root):
        """Create post-activation hooks for continuous validation"""

        # Create custom activation script
        activate_script = venv_path / 'bin' / 'activate.dht'

        hook_content = f'''#!/bin/bash
# DHT-enhanced activation script

# Source original activate
source "{venv_path}/bin/activate"

# DHT post-activation checks
if command -v dhtl >/dev/null 2>&1; then
    # Quick validation
    if ! dhtl validate-env --quick --quiet; then
        echo "⚠️  Warning: Environment may have drifted from .dhtconfig"
        echo "   Run 'dhtl validate-env' for details"
    fi

    # Check for missing env vars
    if [ -f .env.template ]; then
        while IFS= read -r line; do
            if [[ $line =~ ^([A-Z_]+)= ]]; then
                var_name="${{BASH_REMATCH[1]}}"
                if [ -z "${{!var_name}}" ]; then
                    echo "⚠️  Missing env var: $var_name"
                fi
            fi
        done < .env.template
    fi

    # Show project status
    echo "📁 Project: $(basename "{project_root}")"
    echo "🐍 Python: $(python --version 2>&1 | cut -d' ' -f2)"
    echo "📦 Packages: $(pip list --format=freeze | wc -l) installed"
fi

# Set DHT-specific environment variables
export DHT_PROJECT_ROOT="{project_root}"
export DHT_VENV_PATH="{venv_path}"
export DHT_MANAGED="true"

# Add project scripts to PATH
if [ -d "{project_root}/scripts" ]; then
    export PATH="{project_root}/scripts:$PATH"
fi
'''

        activate_script.write_text(hook_content)
        activate_script.chmod(0o755)

        # Create deactivation hook
        self._create_deactivation_hook(venv_path)
```

### 6.2 Validation Commands

#### Step 19: Implement Validation Commands
```python
class ValidationCommands:
    def validate_env(self, quick=False, quiet=False):
        """Validate current environment against .dhtconfig"""

        project_root = Path.cwd()
        config_path = project_root / '.dhtconfig'

        if not config_path.exists():
            if not quiet:
                print("No .dhtconfig found")
            return True

        with open(config_path) as f:
            config = yaml.safe_load(f)

        validation_results = {
            'python_version': self._validate_python_version(config),
            'dependencies': self._validate_dependencies(config) if not quick else None,
            'system_deps': self._validate_system_deps(config),
            'tools': self._validate_tools(config),
            'checksums': self._validate_checksums(config) if not quick else None,
        }

        # Generate report
        if not quiet:
            self._print_validation_report(validation_results)

        # Return True if all validations passed
        return all(
            result.get('valid', True)
            for result in validation_results.values()
            if result is not None
        )

    def fix_env(self):
        """Attempt to fix environment discrepancies"""

        print("🔧 Attempting to fix environment...")

        # Re-run regeneration with --fix flag
        fixer = EnvironmentFixer()
        issues = fixer.detect_issues()

        for issue in issues:
            print(f"\n📍 Fixing: {issue['description']}")

            if issue['type'] == 'missing_package':
                fixer.install_missing_package(issue['package'])
            elif issue['type'] == 'wrong_version':
                fixer.fix_package_version(issue['package'], issue['expected'])
            elif issue['type'] == 'missing_system_dep':
                fixer.install_system_dep(issue['dependency'])
            elif issue['type'] == 'missing_tool':
                fixer.install_tool(issue['tool'])

        # Validate again
        if self.validate_env(quiet=True):
            print("\n✅ Environment fixed successfully!")
        else:
            print("\n⚠️  Some issues could not be fixed automatically")
            print("Run 'dhtl regenerate --force' for complete rebuild")
```

## Implementation Priority Matrix

### Critical Path (Must Have - Week 1-2)
1. Project configuration parser (pyproject.toml, requirements.txt)
2. Python version management via UV
3. Basic .dhtconfig generation and parsing
4. Dependency installation with lock files
5. Environment checksum generation and validation
6. Basic regenerate command

### Important Features (Should Have - Week 3-4)
1. System dependency detection and installation
2. Import analysis for dependency inference
3. Project type detection (Django, Flask, etc.)
4. Development tool standardization
5. Clone/fork commands with auto-regeneration
6. Migration helpers (pip→uv, unittest→pytest)

### Nice to Have (Could Have - Week 5-6)
1. Multi-language support (Node, Rust, Go)
2. Advanced validation reporting
3. Continuous validation hooks
4. Docker fallback for unsupported platforms
5. Package manager wrappers in venv
6. Fix-env command

### Future Enhancements (Won't Have - Post v1.0)
1. Machine learning for better inference
2. Cloud-based environment caching
3. Team environment synchronization
4. Performance optimizations
5. GUI for environment management

## Success Metrics

1. **Reproducibility**: 100% identical environments across platforms
2. **Speed**: < 2 minutes from clone to ready environment
3. **Reliability**: < 0.1% failure rate on supported platforms
4. **Coverage**: Support 95% of Python projects without modification
5. **User Satisfaction**: < 5 commands to fully setup any project

This comprehensive plan ensures DHT can create truly deterministic, portable Python development environments across all platforms.
