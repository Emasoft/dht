# DHT Platform Normalization Guide

## Core Challenge: Platform Differences That Break Builds

### 1. File System Differences

**Problems**:
- Path separators: `\` (Windows) vs `/` (Unix)
- Case sensitivity: macOS (insensitive), Linux (sensitive), Windows (insensitive)
- Path length limits: 260 chars (Windows) vs 4096 (Linux)
- Reserved names: CON, PRN, AUX (Windows)

**DHT Solution**:
```python
class FileSystemNormalizer:
    def normalize_path(self, path: str, context: str = 'runtime') -> str:
        """Normalize paths for cross-platform compatibility"""

        # Always use Path objects internally
        path_obj = Path(path)

        # Context-specific handling
        if context == 'config':
            # Use forward slashes in all config files
            return path_obj.as_posix()

        elif context == 'script':
            # Use Path.resolve() for absolute paths
            return str(path_obj.resolve())

        elif context == 'relative':
            # Always relative to project root
            try:
                return str(path_obj.relative_to(self.project_root))
            except ValueError:
                return str(path_obj)

        # Handle Windows special cases
        if platform.system() == 'Windows':
            # Check for reserved names
            name = path_obj.name.upper()
            if name in ['CON', 'PRN', 'AUX', 'NUL'] or \
               any(name.startswith(f'{x}{i}') for x in ['COM', 'LPT'] for i in range(1, 10)):
                # Append underscore to reserved names
                path_obj = path_obj.with_name(f"{path_obj.name}_")

            # Handle long paths
            str_path = str(path_obj)
            if len(str_path) > 260:
                # Use extended path syntax
                if not str_path.startswith('\\\\?\\'):
                    return f'\\\\?\\{path_obj.resolve()}'

        return str(path_obj)

    def create_file_safely(self, path: str, content: str) -> Path:
        """Create file handling platform differences"""

        path = self.normalize_path(path)
        path_obj = Path(path)

        # Ensure parent directory exists
        path_obj.parent.mkdir(parents=True, exist_ok=True)

        # Write with consistent encoding and line endings
        with open(path_obj, 'w', encoding='utf-8', newline='\n') as f:
            f.write(content)

        # Set consistent permissions (Unix only)
        if platform.system() != 'Windows':
            path_obj.chmod(0o644)  # rw-r--r--

        return path_obj
```

**Rationale**:
- Path objects handle separators automatically
- Forward slashes work everywhere in configs
- Extended paths handle Windows limitations
- Consistent line endings prevent Git issues

### 2. Line Ending Normalization

**Problems**:
- Windows: CRLF (`\r\n`)
- Unix/Mac: LF (`\n`)
- Git autocrlf can cause inconsistencies

**DHT Solution**:
```python
class LineEndingNormalizer:
    def __init__(self):
        self.gitattributes_content = '''# DHT Line Ending Normalization
* text=auto eol=lf
*.py text eol=lf
*.sh text eol=lf
*.yml text eol=lf
*.yaml text eol=lf
*.json text eol=lf
*.md text eol=lf
*.txt text eol=lf
*.cfg text eol=lf
*.ini text eol=lf
*.toml text eol=lf

# Binary files
*.pyc binary
*.pyo binary
*.pyd binary
*.so binary
*.dylib binary
*.dll binary
*.exe binary
*.whl binary
*.gz binary
*.zip binary
*.tar binary
'''

    def setup_line_endings(self, project_root: Path):
        """Configure consistent line endings"""

        # Create .gitattributes
        gitattributes = project_root / '.gitattributes'
        gitattributes.write_text(self.gitattributes_content, encoding='utf-8', newline='\n')

        # Configure Git
        subprocess.run(['git', 'config', 'core.autocrlf', 'false'], cwd=project_root)
        subprocess.run(['git', 'config', 'core.eol', 'lf'], cwd=project_root)

        # Normalize existing files
        self.normalize_existing_files(project_root)

    def normalize_existing_files(self, project_root: Path):
        """Convert all text files to LF"""

        text_extensions = {'.py', '.sh', '.yml', '.yaml', '.json', '.md', '.txt', '.cfg', '.ini', '.toml'}

        for file_path in project_root.rglob('*'):
            if file_path.is_file() and file_path.suffix in text_extensions:
                # Skip if in .git or .venv
                if '.git' in file_path.parts or '.venv' in file_path.parts:
                    continue

                # Read and normalize
                try:
                    content = file_path.read_text(encoding='utf-8')
                    # Convert to LF
                    content = content.replace('\r\n', '\n').replace('\r', '\n')
                    # Write back with LF
                    file_path.write_text(content, encoding='utf-8', newline='\n')
                except Exception as e:
                    print(f"Warning: Could not normalize {file_path}: {e}")
```

**Rationale**:
- LF works everywhere (Git Bash on Windows handles it)
- .gitattributes ensures consistency
- Binary files excluded from conversion
- One-time normalization fixes existing files

### 3. Shell Command Portability

**Problems**:
- Different shells: bash, zsh, cmd, PowerShell
- Command availability: `grep` vs `findstr`
- Path separators in commands
- Environment variable syntax: `$VAR` vs `%VAR%`

**DHT Solution**:
```python
class ShellCommandNormalizer:
    def create_portable_command(self, command: str, args: list) -> list:
        """Create command that works on all platforms"""

        # Map common commands to platform equivalents
        command_map = {
            'rm': {
                'windows': ['del', '/f', '/q'] if len(args) == 1 else ['rmdir', '/s', '/q'],
                'unix': ['rm', '-rf']
            },
            'cp': {
                'windows': ['copy'] if os.path.isfile(args[0]) else ['xcopy', '/e', '/i', '/q'],
                'unix': ['cp', '-r']
            },
            'mv': {
                'windows': ['move'],
                'unix': ['mv']
            },
            'cat': {
                'windows': ['type'],
                'unix': ['cat']
            },
            'grep': {
                'windows': ['findstr'],
                'unix': ['grep']
            },
            'which': {
                'windows': ['where'],
                'unix': ['which']
            }
        }

        # Get platform-specific command
        platform_type = 'windows' if platform.system() == 'Windows' else 'unix'

        if command in command_map:
            base_cmd = command_map[command][platform_type]
        else:
            base_cmd = [command]

        # Normalize paths in arguments
        normalized_args = []
        for arg in args:
            if os.path.exists(arg) or '/' in arg or '\\' in arg:
                # It's likely a path
                normalized_args.append(self.normalize_path(arg))
            else:
                normalized_args.append(arg)

        return base_cmd + normalized_args

    def create_portable_script(self, commands: list, script_name: str) -> dict:
        """Generate scripts that work on all platforms"""

        # Python script (universal)
        py_script = '''#!/usr/bin/env python3
import subprocess
import sys
import os
from pathlib import Path

commands = {commands}

def run_command(cmd):
    """Run command with proper shell handling"""
    # Use shell=False for security and consistency
    result = subprocess.run(
        cmd,
        shell=False,
        capture_output=True,
        text=True,
        env=os.environ.copy()
    )

    print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)

    return result.returncode

def main():
    for cmd in commands:
        print(f"Running: {{' '.join(cmd)}}")
        code = run_command(cmd)
        if code != 0:
            print(f"Command failed with code {{code}}")
            sys.exit(code)

if __name__ == "__main__":
    main()
'''.format(commands=repr(commands))

        # Platform wrappers
        scripts = {f'{script_name}.py': py_script}

        if platform.system() == 'Windows':
            scripts[f'{script_name}.bat'] = f'''@echo off
python "%~dp0{script_name}.py" %*
'''
        else:
            scripts[f'{script_name}.sh'] = f'''#!/bin/bash
exec python "$(dirname "$0")/{script_name}.py" "$@"
'''

        return scripts
```

**Rationale**:
- Python scripts work identically everywhere
- Command mapping handles platform differences
- Path normalization prevents separator issues
- No shell interpretation avoids syntax differences

### 4. Environment Variable Management

**Problems**:
- Syntax differences: `$VAR` vs `%VAR%`
- Path separator: `:` vs `;`
- Case sensitivity of variable names
- System-specific variables

**DHT Solution**:
```python
class EnvironmentNormalizer:
    def __init__(self):
        self.path_sep = ';' if platform.system() == 'Windows' else ':'

    def normalize_environment(self) -> dict:
        """Create normalized environment for all platforms"""

        # Start with minimal base
        base_env = {
            'PYTHONUNBUFFERED': '1',
            'PYTHONDONTWRITEBYTECODE': '1',
            'PYTHONHASHSEED': '0',
            'PIP_DISABLE_PIP_VERSION_CHECK': '1',
            'PIP_NO_CACHE_DIR': '1',
            'UV_NO_CACHE': '1',
            'NO_COLOR': '1',  # Disable color output for consistency
            'FORCE_COLOR': '0',
            'COLUMNS': '80',  # Fixed terminal width
            'LINES': '24',    # Fixed terminal height
        }

        # Normalize PATH
        path_entries = []

        # Add venv first
        venv_bin = '.venv/Scripts' if platform.system() == 'Windows' else '.venv/bin'
        path_entries.append(str(Path(venv_bin).resolve()))

        # Add system paths
        system_paths = self._get_minimal_system_paths()
        path_entries.extend(system_paths)

        base_env['PATH'] = self.path_sep.join(path_entries)

        # Platform-specific additions
        if platform.system() == 'Windows':
            base_env['PATHEXT'] = '.COM;.EXE;.BAT;.CMD;.PY'
            base_env['COMSPEC'] = 'C:\\Windows\\System32\\cmd.exe'
        else:
            base_env['SHELL'] = '/bin/bash'
            base_env['LC_ALL'] = 'C.UTF-8'
            base_env['LANG'] = 'C.UTF-8'

        return base_env

    def create_activation_script(self, venv_path: Path) -> dict:
        """Create consistent activation scripts"""

        scripts = {}

        # Unix activation
        scripts['activate.sh'] = f'''#!/bin/bash
# DHT Normalized Activation Script

# Save original environment
export DHT_ORIGINAL_PATH="$PATH"
export DHT_ORIGINAL_PS1="$PS1"

# Activate venv
export VIRTUAL_ENV="{venv_path.resolve()}"
export PATH="{venv_path}/bin:$PATH"
export PS1="(dht) $PS1"

# Set consistent environment
export PYTHONUNBUFFERED=1
export PYTHONDONTWRITEBYTECODE=1
export PYTHONHASHSEED=0

# Platform normalization
export LC_ALL=C.UTF-8
export LANG=C.UTF-8

# DHT-specific
export DHT_ACTIVE=1
export DHT_PROJECT_ROOT="{venv_path.parent}"

# Deactivate function
deactivate() {{
    export PATH="$DHT_ORIGINAL_PATH"
    export PS1="$DHT_ORIGINAL_PS1"
    unset VIRTUAL_ENV DHT_ACTIVE DHT_PROJECT_ROOT
    unset -f deactivate
}}
'''

        # Windows activation
        scripts['activate.bat'] = f'''@echo off
REM DHT Normalized Activation Script

REM Save original environment
set "DHT_ORIGINAL_PATH=%PATH%"
set "DHT_ORIGINAL_PROMPT=%PROMPT%"

REM Activate venv
set "VIRTUAL_ENV={venv_path.resolve()}"
set "PATH={venv_path}\\Scripts;%PATH%"
set "PROMPT=(dht) %PROMPT%"

REM Set consistent environment
set PYTHONUNBUFFERED=1
set PYTHONDONTWRITEBYTECODE=1
set PYTHONHASHSEED=0

REM DHT-specific
set DHT_ACTIVE=1
set DHT_PROJECT_ROOT={venv_path.parent}
'''

        return scripts
```

**Rationale**:
- Consistent variable names across platforms
- Minimal PATH prevents conflicts
- Fixed terminal size for consistent output
- Platform-specific handling where necessary

### 5. Binary Tool Management

**Problems**:
- Different binary formats: ELF vs PE vs Mach-O
- Architecture differences: x86_64 vs ARM64
- Dynamic library loading: LD_LIBRARY_PATH vs PATH

**DHT Solution**:
```python
class BinaryToolManager:
    def install_binary_tool(self, tool_name: str, version: str) -> Path:
        """Install binary tool for current platform"""

        # Determine platform specifics
        platform_info = {
            'system': platform.system().lower(),
            'machine': platform.machine().lower(),
            'arch': 'x64' if '64' in platform.machine() else 'x86',
        }

        # Construct download URL
        tool_urls = {
            'node': {
                'base': 'https://nodejs.org/dist/v{version}/',
                'patterns': {
                    'windows-x64': 'node-v{version}-win-x64.zip',
                    'darwin-x64': 'node-v{version}-darwin-x64.tar.gz',
                    'darwin-arm64': 'node-v{version}-darwin-arm64.tar.gz',
                    'linux-x64': 'node-v{version}-linux-x64.tar.xz',
                    'linux-arm64': 'node-v{version}-linux-arm64.tar.xz',
                }
            },
            # More tools...
        }

        # Download and extract
        tool_dir = self.download_and_extract(tool_name, version, platform_info)

        # Create portable wrapper
        self.create_tool_wrapper(tool_name, tool_dir)

        return tool_dir

    def create_tool_wrapper(self, tool_name: str, tool_dir: Path):
        """Create wrapper script for consistent tool access"""

        wrapper_path = self.venv_bin / tool_name

        if platform.system() == 'Windows':
            # Batch wrapper
            wrapper_path = wrapper_path.with_suffix('.bat')
            content = f'''@echo off
"{tool_dir}\\{tool_name}.exe" %*
'''
        else:
            # Shell wrapper
            content = f'''#!/bin/bash
export LD_LIBRARY_PATH="{tool_dir}/lib:$LD_LIBRARY_PATH"
export DYLD_LIBRARY_PATH="{tool_dir}/lib:$DYLD_LIBRARY_PATH"
exec "{tool_dir}/bin/{tool_name}" "$@"
'''

        wrapper_path.write_text(content)
        wrapper_path.chmod(0o755)

    def verify_binary_compatibility(self, binary_path: Path) -> dict:
        """Check if binary is compatible with current platform"""

        checks = {
            'exists': binary_path.exists(),
            'executable': os.access(binary_path, os.X_OK),
            'architecture': None,
            'dependencies': [],
        }

        if not checks['exists']:
            return checks

        # Check architecture
        if platform.system() == 'Linux':
            result = subprocess.run(['file', str(binary_path)],
                                  capture_output=True, text=True)

            if 'ELF 64-bit' in result.stdout:
                checks['architecture'] = 'x64'
            elif 'ELF 32-bit' in result.stdout:
                checks['architecture'] = 'x86'

            # Check dependencies
            ldd_result = subprocess.run(['ldd', str(binary_path)],
                                      capture_output=True, text=True)

            for line in ldd_result.stdout.splitlines():
                if 'not found' in line:
                    lib = line.split('=>')[0].strip()
                    checks['dependencies'].append({'missing': lib})

        elif platform.system() == 'Darwin':
            result = subprocess.run(['file', str(binary_path)],
                                  capture_output=True, text=True)

            if 'x86_64' in result.stdout:
                checks['architecture'] = 'x64'
            elif 'arm64' in result.stdout:
                checks['architecture'] = 'arm64'

            # Check dependencies
            otool_result = subprocess.run(['otool', '-L', str(binary_path)],
                                        capture_output=True, text=True)

            for line in otool_result.stdout.splitlines():
                if '@rpath' in line:
                    lib = line.split()[0]
                    checks['dependencies'].append({'rpath': lib})

        elif platform.system() == 'Windows':
            # Use dumpbin or Dependencies.exe if available
            checks['architecture'] = 'x64' if 'x64' in str(binary_path) else 'x86'

        return checks
```

**Rationale**:
- Platform-specific binaries with common interface
- Wrapper scripts hide platform differences
- Library path management for dynamic loading
- Compatibility verification before use

### 6. Test Output Normalization

**Problems**:
- Different path representations in stack traces
- Platform-specific error messages
- Timing variations
- Memory addresses in output

**DHT Solution**:
```python
class TestOutputNormalizer:
    def __init__(self):
        self.normalizers = [
            self._normalize_paths,
            self._normalize_timestamps,
            self._normalize_memory,
            self._normalize_platform_errors,
            self._normalize_line_numbers,
        ]

    def normalize_output(self, output: str) -> str:
        """Normalize test output for comparison"""

        for normalizer in self.normalizers:
            output = normalizer(output)

        return output

    def _normalize_paths(self, text: str) -> str:
        """Normalize path representations"""

        # Windows paths to Unix
        text = re.sub(r'[A-Z]:\\\\', '/', text)
        text = re.sub(r'\\\\', '/', text)

        # Normalize home directory
        text = re.sub(r'/Users/\w+', '/home/user', text)
        text = re.sub(r'/home/\w+', '/home/user', text)
        text = re.sub(r'C:/Users/\w+', '/home/user', text)

        # Normalize temp paths
        text = re.sub(r'/tmp/[^/\s]+', '/tmp/TEMP', text)
        text = re.sub(r'/var/folders/[^/\s]+/[^/\s]+/[^/\s]+', '/tmp/TEMP', text)
        text = re.sub(r'%TEMP%\\[^\\s]+', '/tmp/TEMP', text)

        # Normalize venv paths
        text = re.sub(r'\.venv[/\\](?:lib[/\\]python\d+\.\d+[/\\])?site-packages',
                     '.venv/site-packages', text)

        return text

    def _normalize_timestamps(self, text: str) -> str:
        """Replace timestamps with placeholders"""

        # ISO format
        text = re.sub(r'\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?',
                     '<TIMESTAMP>', text)

        # Unix timestamps
        text = re.sub(r'\b1\d{9}\b', '<UNIX_TIME>', text)

        # Execution times
        text = re.sub(r'\d+\.\d+s', '<TIME>s', text)
        text = re.sub(r'\d+ms', '<TIME>ms', text)

        return text

    def _normalize_memory(self, text: str) -> str:
        """Normalize memory addresses and sizes"""

        # Memory addresses
        text = re.sub(r'0x[0-9a-fA-F]+', '<ADDR>', text)

        # Memory sizes (platform-specific)
        text = re.sub(r'\d+\s*[KMG]B', '<SIZE>', text)

        # Process IDs
        text = re.sub(r'pid[= ]\d+', 'pid=<PID>', text, flags=re.IGNORECASE)

        return text

    def _normalize_platform_errors(self, text: str) -> str:
        """Normalize platform-specific error messages"""

        error_mappings = {
            # Windows -> Unix errors
            'The system cannot find the file specified': 'No such file or directory',
            'Access is denied': 'Permission denied',
            'The process cannot access the file': 'Resource temporarily unavailable',

            # Normalize errno representations
            r'\\[Errno \d+\\]': '[Errno N]',
            r'error: \d+': 'error: N',
        }

        for pattern, replacement in error_mappings.items():
            text = re.sub(pattern, replacement, text)

        return text

    def _normalize_line_numbers(self, text: str) -> str:
        """Normalize line numbers in stack traces"""

        # Python traceback
        text = re.sub(r'File "([^"]+)", line \d+',
                     lambda m: f'File "{self._normalize_paths(m.group(1))}", line N',
                     text)

        # Other common formats
        text = re.sub(r':\d+:\d+', ':N:N', text)  # file.py:10:5
        text = re.sub(r'@\d+:\d+', '@N:N', text)  # JavaScript

        return text

# Usage in test comparison
def compare_test_outputs(output1: str, output2: str) -> bool:
    """Compare test outputs across platforms"""

    normalizer = TestOutputNormalizer()

    normalized1 = normalizer.normalize_output(output1)
    normalized2 = normalizer.normalize_output(output2)

    if normalized1 != normalized2:
        # Generate diff for debugging
        import difflib
        diff = difflib.unified_diff(
            normalized1.splitlines(keepends=True),
            normalized2.splitlines(keepends=True),
            fromfile='platform1',
            tofile='platform2'
        )

        print("Normalized outputs differ:")
        print(''.join(diff))

        return False

    return True
```

**Rationale**:
- Path normalization handles different separators
- Timestamp removal eliminates timing differences
- Memory address normalization removes non-deterministic values
- Error message mapping handles platform-specific messages
- Line number normalization handles code changes

## Integration Example: Complete Platform Test

```python
class PlatformCompatibilityTest:
    """Test that verifies code works identically on all platforms"""

    def test_cross_platform_build(self):
        """Build and verify on multiple platforms"""

        results = {}

        # Run on each platform (via CI or Docker)
        for platform_name in ['ubuntu', 'windows', 'macos']:
            with PlatformEnvironment(platform_name) as env:
                # Setup
                env.run('dhtl regenerate --strict')

                # Build
                build_result = env.run('dhtl build --reproducible')

                # Test
                test_result = env.run('dhtl test --deterministic')

                # Collect artifacts
                results[platform_name] = {
                    'build': env.collect_artifacts('dist/*'),
                    'test_output': test_result.stdout,
                    'checksums': env.calculate_checksums(),
                }

        # Verify all platforms produced identical results
        self.assert_builds_identical(results)
        self.assert_tests_identical(results)
        self.assert_checksums_match(results)
```

This comprehensive platform normalization ensures that DHT projects truly work identically everywhere, not just "mostly the same."
