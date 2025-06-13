# DHT Deterministic Build System: Technical Rationale and Implementation

## Core Philosophy: Feature Parity Over Binary Identity

### Why Version-Based Validation Instead of Hash-Based

**Problem with Hashes**:
- `black==23.7.0` on macOS ARM64 has different binary hash than on Linux x86_64
- But they format code identically
- Hash validation would fail despite functional equivalence

**Our Approach**: Version + Behavior Validation
```python
class ToolValidator:
    def validate_tool(self, tool_name, required_version):
        """Validate tool by version AND behavior, not hash"""
        
        # Step 1: Version check
        installed_version = self.get_tool_version(tool_name)
        if not self.version_matches(installed_version, required_version):
            return False
        
        # Step 2: Behavior check (tool-specific)
        if tool_name == 'black':
            # Format a test file and compare output
            test_result = self.run_black_test()
            expected = self.get_expected_black_output(required_version)
            return test_result == expected
        
        elif tool_name == 'pytest':
            # Check key features are available
            return self.check_pytest_features(['--tb=short', '--strict-markers'])
        
        return True
```

**Rationale**: 
- Ensures functional equivalence across platforms
- Allows platform-optimized binaries while maintaining behavior
- Reduces false negatives from binary differences

## Critical Implementation Strategies

### 1. Tool Installation with Guaranteed Version Control

**Problem**: System tools may conflict or have wrong versions

**Solution**: Hierarchical Tool Management
```python
class DeterministicToolManager:
    def ensure_tool(self, tool_name, version, config):
        """Ensure tool is available with exact version"""
        
        # Priority order (most to least isolated)
        strategies = [
            # 1. UV tool with --from (completely isolated)
            lambda: self._install_uv_tool_isolated(tool_name, version),
            
            # 2. Install in venv if possible
            lambda: self._install_in_venv(tool_name, version),
            
            # 3. Use system tool ONLY if exact version match
            lambda: self._use_system_if_exact(tool_name, version),
            
            # 4. Fail explicitly (no fallbacks if --no-fallbacks)
            lambda: self._fail_with_instructions(tool_name, version)
        ]
        
        if config.get('no_fallbacks'):
            strategies = strategies[:2]  # Only isolated options
        
        for strategy in strategies:
            if result := strategy():
                # Validate behavior after installation
                if self._validate_tool_behavior(tool_name, version):
                    return result
                
        raise ToolInstallationError(f"Cannot provide {tool_name}=={version}")
    
    def _install_uv_tool_isolated(self, tool, version):
        """Install tool in isolated environment via UV"""
        # This ensures NO interference from system
        cmd = [
            'uv', 'tool', 'install',
            f'{tool}=={version}',
            '--force',  # Replace existing
            '--isolated'  # Don't use any caches
        ]
        
        if run_command(cmd).returncode == 0:
            # Create wrapper that explicitly uses this version
            self._create_versioned_wrapper(tool, version)
            return True
        return False
```

**Rationale**:
- Isolation prevents version conflicts
- Explicit version in command ensures reproducibility
- Wrapper scripts guarantee correct tool is invoked

### 2. Configuration Normalization Across Platforms

**Problem**: Same config file may behave differently on different platforms

**Solution**: Platform-Agnostic Configuration Generator
```python
class ConfigNormalizer:
    def generate_tool_config(self, tool_name, project_type):
        """Generate configs that work identically across platforms"""
        
        if tool_name == 'pytest':
            return self._pytest_config(project_type)
        elif tool_name == 'mypy':
            return self._mypy_config(project_type)
        elif tool_name == 'ruff':
            return self._ruff_config(project_type)
    
    def _pytest_config(self, project_type):
        """Generate pytest config with platform normalization"""
        config = {
            'tool.pytest.ini_options': {
                # Force consistent behavior
                'testpaths': ['tests'],  # Explicit paths
                'python_files': ['test_*.py', '*_test.py'],
                'python_classes': ['Test*'],
                'python_functions': ['test_*'],
                
                # Disable platform-specific features
                'addopts': ' '.join([
                    '-v',
                    '--tb=short',  # Consistent traceback format
                    '--strict-markers',  # Fail on undefined markers
                    '--strict-config',  # Fail on config errors
                    '-p no:cacheprovider',  # Disable cache (non-deterministic)
                    '--import-mode=importlib',  # Consistent imports
                ]),
                
                # Platform-agnostic paths
                'cache_dir': '.pytest_cache',  # Relative, not system
                
                # Deterministic test order
                'junit_family': 'xunit2',
                'junit_logging': 'all',
                'junit_log_passing_tests': True
            }
        }
        
        # Add project-type specific settings
        if project_type == 'django':
            config['tool.pytest.ini_options']['DJANGO_SETTINGS_MODULE'] = 'settings.test'
            config['tool.pytest.ini_options']['addopts'] += ' --reuse-db'
        
        return config
    
    def _mypy_config(self, project_type):
        """Generate mypy config ensuring cross-platform consistency"""
        return {
            'tool.mypy': {
                # Explicit behavior settings
                'python_version': '3.11',  # Target version, not system
                'platform': 'linux',  # Check against Linux (most restrictive)
                'mypy_path': '$MYPY_CONFIG_FILE_DIR',  # Relative paths
                
                # Strict settings for consistency
                'warn_return_any': True,
                'warn_unused_configs': True,
                'disallow_untyped_defs': True,
                'no_implicit_reexport': True,
                'strict_optional': True,
                
                # Disable platform-specific checks
                'warn_no_return': False,  # Can vary by platform
                
                # Explicit cache location
                'cache_dir': '.mypy_cache',
                'sqlite_cache': False,  # Use filesystem cache
                
                # Ignore system packages
                'follow_imports': 'normal',
                'ignore_missing_imports': True,
            }
        }
```

**Rationale**:
- Explicit settings override platform defaults
- Relative paths ensure portability
- Disabled features that vary by platform
- Consistent cache locations avoid conflicts

### 3. Virtual Environment Tool Management

**Problem**: Global vs venv tools can cause conflicts

**Solution**: Intelligent Tool Resolution
```python
class VenvToolManager:
    def setup_venv_tools(self, venv_path, required_tools):
        """Ensure all tools are available in venv with correct versions"""
        
        for tool, version in required_tools.items():
            self._ensure_tool_in_venv(venv_path, tool, version)
    
    def _ensure_tool_in_venv(self, venv_path, tool, version):
        """Install tool in venv or create wrapper to correct version"""
        
        venv_bin = venv_path / 'bin'
        tool_path = venv_bin / tool
        
        # Check if tool exists in venv
        if tool_path.exists():
            current_version = self._get_tool_version(tool_path)
            if current_version == version:
                return  # Already correct
        
        # Strategy 1: Install directly in venv (for Python tools)
        if self._is_python_tool(tool):
            pip = venv_bin / 'pip'
            run_command([
                str(pip), 'install', 
                f'{tool}=={version}',
                '--force-reinstall',  # Ensure exact version
                '--no-deps'  # Avoid dependency conflicts
            ])
            
            # Install dependencies separately for control
            deps = self._get_tool_dependencies(tool, version)
            if deps:
                run_command([str(pip), 'install'] + deps)
        
        # Strategy 2: Create wrapper to UV tool (for binary tools)
        else:
            wrapper_content = f'''#!/bin/bash
# Auto-generated wrapper for {tool} v{version}
# This ensures consistent version across platforms

# Check if UV tool exists with correct version
if ! uv tool list | grep -q "{tool}.*{version}"; then
    echo "Installing {tool} v{version}..."
    uv tool install {tool}=={version} --force
fi

# Run with explicit version
exec uv tool run --from {tool}=={version} {tool} "$@"
'''
            
            tool_path.write_text(wrapper_content)
            tool_path.chmod(0o755)
            
        # Validate tool works correctly
        self._validate_tool_installation(tool_path, version)
```

**Rationale**:
- Venv tools are isolated from system
- Wrappers ensure version consistency
- Validation confirms functionality
- No reliance on system tool versions

### 4. Automatic Dependency Discovery and Generation

**Problem**: Missing dependencies cause platform-specific failures

**Solution**: Comprehensive Dependency Analysis
```python
class DependencyAnalyzer:
    def generate_requirements(self, project_root):
        """Generate complete requirements from code analysis"""
        
        # Multiple detection strategies
        discovered = {
            'imports': self._analyze_imports(project_root),
            'setup_py': self._parse_setup_py(project_root),
            'pyproject': self._parse_pyproject_toml(project_root),
            'requirements': self._parse_requirements_files(project_root),
            'dynamic': self._dynamic_analysis(project_root)
        }
        
        # Merge and resolve conflicts
        final_deps = self._merge_dependencies(discovered)
        
        # Add system dependency mappings
        final_deps = self._add_system_dependencies(final_deps)
        
        return final_deps
    
    def _analyze_imports(self, project_root):
        """Deep import analysis with context understanding"""
        imports = set()
        import_context = {}
        
        for py_file in project_root.rglob('*.py'):
            if '.venv' in str(py_file):
                continue
                
            try:
                tree = ast.parse(py_file.read_text())
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            module = alias.name.split('.')[0]
                            imports.add(module)
                            import_context[module] = self._get_usage_context(tree, module)
                    
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            module = node.module.split('.')[0]
                            imports.add(module)
                            import_context[module] = self._get_usage_context(tree, module)
                
                # Check for dynamic imports
                for node in ast.walk(tree):
                    if isinstance(node, ast.Call):
                        if getattr(node.func, 'id', None) == '__import__':
                            # Handle __import__('module')
                            if node.args and isinstance(node.args[0], ast.Str):
                                imports.add(node.args[0].s)
                
            except Exception as e:
                logger.warning(f"Failed to parse {py_file}: {e}")
        
        # Map imports to packages with version constraints
        requirements = []
        for imp in imports:
            if imp in STDLIB_MODULES:
                continue
                
            package_info = self._resolve_import_to_package(imp, import_context.get(imp))
            if package_info:
                requirements.append(package_info)
        
        return requirements
    
    def _get_usage_context(self, tree, module):
        """Understand how module is used to infer version needs"""
        context = {
            'features_used': set(),
            'version_hints': []
        }
        
        # Example: Detect FastAPI features to determine minimum version
        if module == 'fastapi':
            for node in ast.walk(tree):
                if isinstance(node, ast.Attribute):
                    if node.attr == 'WebSocket':
                        context['features_used'].add('websocket')
                        context['version_hints'].append('>=0.61.0')  # WebSocket added
                    elif node.attr == 'BackgroundTasks':
                        context['features_used'].add('background')
                        context['version_hints'].append('>=0.62.0')
        
        return context
    
    def _dynamic_analysis(self, project_root):
        """Run code in sandbox to detect runtime dependencies"""
        sandbox_deps = set()
        
        # Create isolated environment
        with tempfile.TemporaryDirectory() as sandbox:
            # Copy minimal code
            sandbox_path = Path(sandbox)
            
            # Run with import hooks
            hook_script = '''
import sys
import builtins

original_import = builtins.__import__
imported_modules = set()

def tracking_import(name, *args, **kwargs):
    imported_modules.add(name.split('.')[0])
    return original_import(name, *args, **kwargs)

builtins.__import__ = tracking_import

# Run user code here
try:
    from {module} import *
except Exception:
    pass

# Output discoveries
for module in imported_modules:
    print(f"IMPORT:{module}")
'''
            
            # Run for each module
            for module in self._find_importable_modules(project_root):
                result = run_command([
                    sys.executable, '-c', 
                    hook_script.format(module=module)
                ], cwd=sandbox_path, capture_output=True)
                
                for line in result.stdout.splitlines():
                    if line.startswith('IMPORT:'):
                        sandbox_deps.add(line[7:])
        
        return sandbox_deps
```

**Rationale**:
- Multiple detection methods catch all dependencies
- Context analysis determines version requirements
- Dynamic analysis catches runtime dependencies
- System dependency mapping prevents platform issues

### 5. Deterministic Test Environment Creation

**Problem**: Tests pass locally but fail in CI due to environment differences

**Solution**: Sandboxed Test Environments
```python
class TestEnvironmentManager:
    def create_test_sandbox(self, test_config):
        """Create identical test environment across platforms"""
        
        sandbox = {
            'env_vars': self._normalize_env_vars(),
            'temp_dirs': self._create_temp_structure(),
            'network': self._setup_network_mocking(),
            'filesystem': self._setup_fs_sandbox(),
            'time': self._setup_time_control(),
            'random': self._setup_deterministic_random()
        }
        
        return TestSandbox(sandbox)
    
    def _normalize_env_vars(self):
        """Create consistent environment variables"""
        # Start with minimal, controlled environment
        base_env = {
            'PATH': '/usr/bin:/bin',  # Minimal PATH
            'HOME': '/tmp/test_home',
            'TEMP': '/tmp/test_temp',
            'TMP': '/tmp/test_temp',
            'TMPDIR': '/tmp/test_temp',
            'PYTHONHASHSEED': '0',  # Deterministic hashing
            'PYTHONDONTWRITEBYTECODE': '1',  # No .pyc files
            'PYTHONUNBUFFERED': '1',  # Consistent output
            'LC_ALL': 'C.UTF-8',  # Consistent locale
            'LANG': 'C.UTF-8',
            'TZ': 'UTC',  # Consistent timezone
        }
        
        # Add project-specific vars
        if project_env := self._get_project_env():
            base_env.update(project_env)
        
        return base_env
    
    def _setup_network_mocking(self):
        """Ensure network calls are deterministic"""
        return {
            'dns_resolution': {
                'localhost': '127.0.0.1',
                'test.local': '127.0.0.1'
            },
            'blocked_domains': ['*'],  # Block all external
            'allowed_domains': ['localhost', '127.0.0.1'],
            'mock_responses': self._load_mock_responses()
        }
    
    def _setup_fs_sandbox(self):
        """Create isolated filesystem for tests"""
        sandbox_root = Path(tempfile.mkdtemp(prefix='dht_test_'))
        
        # Standard directory structure
        dirs = [
            'home',
            'tmp',
            'var/log',
            'etc',
            'data'
        ]
        
        for dir_path in dirs:
            (sandbox_root / dir_path).mkdir(parents=True)
        
        # Platform-specific paths
        if platform.system() == 'Windows':
            # Create Windows-style paths
            (sandbox_root / 'Users/TestUser').mkdir(parents=True)
            (sandbox_root / 'ProgramData').mkdir(parents=True)
        
        return sandbox_root
    
    def _setup_deterministic_random(self):
        """Ensure random operations are reproducible"""
        import random
        import numpy as np
        
        # Fixed seeds
        random.seed(42)
        np.random.seed(42)
        
        # Monkeypatch time-based seeds
        original_time = time.time
        time.time = lambda: 1234567890.0
        
        return {
            'random_seed': 42,
            'numpy_seed': 42,
            'time_seed': 1234567890.0
        }

class TestSandbox:
    def __init__(self, config):
        self.config = config
        
    def __enter__(self):
        """Activate sandbox"""
        # Save current state
        self._saved_state = {
            'env': os.environ.copy(),
            'cwd': os.getcwd(),
            'sys_path': sys.path.copy()
        }
        
        # Apply sandbox
        os.environ.clear()
        os.environ.update(self.config['env_vars'])
        os.chdir(self.config['filesystem'])
        
        # Mock network
        self._apply_network_mocks()
        
        return self
    
    def __exit__(self, *args):
        """Restore original state"""
        os.environ.clear()
        os.environ.update(self._saved_state['env'])
        os.chdir(self._saved_state['cwd'])
        sys.path[:] = self._saved_state['sys_path']
        
        # Cleanup
        shutil.rmtree(self.config['filesystem'])
```

**Rationale**:
- Identical starting conditions eliminate variance
- Network mocking prevents external dependencies
- Filesystem isolation prevents side effects
- Deterministic randomness ensures reproducibility

### 6. Strict Mode: No Fallbacks

**Problem**: Fallbacks can hide configuration issues

**Solution**: Explicit Failure with Clear Recovery
```python
class StrictModeManager:
    def __init__(self, no_fallbacks=False):
        self.no_fallbacks = no_fallbacks
    
    def ensure_requirement(self, requirement, context):
        """Ensure requirement is met or fail explicitly"""
        
        if self.no_fallbacks:
            # Try primary strategy only
            if not self._try_primary_strategy(requirement):
                raise StrictModeError(
                    f"Cannot satisfy {requirement} without fallbacks\n"
                    f"Context: {context}\n"
                    f"Solutions:\n"
                    f"1. Install {requirement} manually\n"
                    f"2. Run without --no-fallbacks\n"
                    f"3. Add to .dhtconfig for automatic installation"
                )
        else:
            # Try all strategies
            return self._try_all_strategies(requirement)
    
    def validate_environment(self, expected, actual):
        """Strict validation with no compromises"""
        
        differences = []
        
        # Check Python version (exact)
        if expected['python'] != actual['python']:
            differences.append({
                'type': 'python_version',
                'expected': expected['python'],
                'actual': actual['python'],
                'severity': 'critical'
            })
        
        # Check every package version
        for pkg, expected_version in expected['packages'].items():
            actual_version = actual['packages'].get(pkg)
            
            if not actual_version:
                differences.append({
                    'type': 'missing_package',
                    'package': pkg,
                    'expected': expected_version,
                    'severity': 'critical'
                })
            elif actual_version != expected_version:
                differences.append({
                    'type': 'version_mismatch',
                    'package': pkg,
                    'expected': expected_version,
                    'actual': actual_version,
                    'severity': 'critical' if self.no_fallbacks else 'warning'
                })
        
        if differences and self.no_fallbacks:
            self._generate_strict_error_report(differences)
            raise StrictModeError("Environment validation failed in strict mode")
        
        return differences
```

**Rationale**:
- Explicit failures catch problems early
- Clear error messages guide resolution
- Opt-in strictness for sensitive projects
- No silent degradation

## Platform-Specific Normalization

### Path Handling Across Platforms

```python
class PathNormalizer:
    def normalize_path(self, path, context='data'):
        """Convert paths to work on all platforms"""
        
        path = Path(path)
        
        # Use forward slashes in configs (works everywhere)
        if context == 'config':
            return path.as_posix()
        
        # Use Path objects in code
        elif context == 'code':
            return path
        
        # Special handling for Windows
        elif platform.system() == 'Windows':
            # Avoid path length issues
            if len(str(path)) > 260:
                # Use short path
                import ctypes
                buf = ctypes.create_unicode_buffer(260)
                ctypes.windll.kernel32.GetShortPathNameW(str(path), buf, 260)
                return Path(buf.value)
        
        return path
    
    def create_platform_agnostic_script(self, script_content):
        """Generate scripts that work on all platforms"""
        
        # Use Python for complex scripts (always available)
        py_script = f'''#!/usr/bin/env python3
import sys
import os
import subprocess

def main():
{textwrap.indent(script_content, '    ')}

if __name__ == '__main__':
    main()
'''
        
        # Create platform-specific wrappers
        if platform.system() == 'Windows':
            bat_wrapper = f'''@echo off
python "%~dp0{script_name}.py" %*
'''
            return {'py': py_script, 'bat': bat_wrapper}
        else:
            sh_wrapper = f'''#!/bin/bash
exec python "$(dirname "$0")/{script_name}.py" "$@"
'''
            return {'py': py_script, 'sh': sh_wrapper}
```

### Compiler and Build Tool Normalization

```python
class BuildToolNormalizer:
    def setup_c_compiler(self, project_root):
        """Ensure C compiler works identically across platforms"""
        
        compiler_config = {
            'compiler': self._detect_best_compiler(),
            'flags': self._get_portable_flags(),
            'include_paths': self._normalize_include_paths(),
            'lib_paths': self._normalize_lib_paths()
        }
        
        # Create portable build script
        self._create_build_wrapper(compiler_config)
        
        return compiler_config
    
    def _detect_best_compiler(self):
        """Choose compiler that's most portable"""
        
        # Prefer clang (most consistent across platforms)
        if shutil.which('clang'):
            return {
                'cc': 'clang',
                'cxx': 'clang++',
                'flags': ['-std=c11', '-std=c++17']
            }
        
        # Platform-specific fallbacks
        if platform.system() == 'Windows':
            # Use MinGW for consistency with Unix
            if shutil.which('gcc'):
                return {
                    'cc': 'gcc',
                    'cxx': 'g++',
                    'flags': ['-std=c11', '-std=c++17']
                }
        
        # Default to system compiler
        return {
            'cc': os.environ.get('CC', 'cc'),
            'cxx': os.environ.get('CXX', 'c++'),
            'flags': []
        }
    
    def _get_portable_flags(self):
        """Compiler flags that work everywhere"""
        return [
            '-Wall',  # All warnings
            '-Wextra',  # Extra warnings
            '-pedantic',  # Strict standard compliance
            '-O2',  # Consistent optimization
            '-fPIC',  # Position independent code
            '-march=x86-64',  # Baseline architecture
            '-mtune=generic',  # Generic tuning
        ]
```

## Validation and Verification

### Multi-Level Validation Strategy

```python
class EnvironmentValidator:
    def validate_complete_environment(self, project_root):
        """Comprehensive validation ensuring identical behavior"""
        
        validations = {
            'level1_versions': self._validate_versions(),
            'level2_behavior': self._validate_behavior(),
            'level3_output': self._validate_output(),
            'level4_integration': self._validate_integration()
        }
        
        return ValidationReport(validations)
    
    def _validate_versions(self):
        """Check all tool and package versions"""
        results = {}
        
        for tool in REQUIRED_TOOLS:
            version = get_tool_version(tool)
            expected = get_expected_version(tool)
            results[tool] = version == expected
        
        return results
    
    def _validate_behavior(self):
        """Check tools behave identically"""
        results = {}
        
        # Test black formatting
        test_code = "x=1+2\ny=3+4\n"
        formatted = run_tool('black', '-c', test_code)
        expected = "x = 1 + 2\ny = 3 + 4\n"
        results['black_format'] = formatted == expected
        
        # Test pytest discovery
        test_discovery = run_tool('pytest', '--collect-only', '-q')
        results['pytest_discovery'] = 'collected' in test_discovery
        
        return results
    
    def _validate_output(self):
        """Check build outputs are identical"""
        results = {}
        
        # Build test package
        run_command(['python', 'setup.py', 'bdist_wheel'])
        
        # Check wheel contents
        wheel_file = next(Path('dist').glob('*.whl'))
        with zipfile.ZipFile(wheel_file) as zf:
            contents = sorted(zf.namelist())
            
        expected_contents = self._get_expected_wheel_contents()
        results['wheel_contents'] = contents == expected_contents
        
        return results
```

## Conclusion

This approach ensures true deterministic builds by:

1. **Version-based validation** with behavior testing (not just hashes)
2. **Isolated tool installation** preventing version conflicts
3. **Normalized configurations** working identically across platforms
4. **Comprehensive dependency discovery** catching all requirements
5. **Sandboxed test environments** eliminating platform variance
6. **Strict mode** for zero-tolerance validation
7. **Multi-level verification** ensuring functional equivalence

The key insight: **Identical behavior matters more than identical binaries**. By focusing on functional equivalence and providing tools to achieve it, DHT ensures that code written on any platform will build and run identically everywhere else.