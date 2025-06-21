# DHT Prefect Migration and Information Extraction Plan

## Current State Analysis

### Existing Components
1. **diagnostic_reporter.py**: Working prototype that extracts system information to JSON
2. **setup_tree_sitter.py**: Script to setup tree-sitter with Bash grammar
3. **Guardian (Shell-based)**: Current process management in `dhtl_guardian_*.sh`
4. **Tree-sitter dependencies**: Already in pyproject.toml with language packs

### Missing Components
1. **Prefect**: Not in dependencies yet
2. **YAML conversion**: diagnostic_reporter outputs JSON, need YAML
3. **File parsers**: No implementation for parsing various file types
4. **Tree-sitter parsers**: Only Bash setup exists, no actual parser implementation

## Implementation Plan

### Phase 1: Prefect Integration (Priority 1)

#### Step 1.1: Add Prefect to Dependencies
```toml
# Add to pyproject.toml
"prefect>=2.14.0",
"prefect-shell>=0.2.0",  # For shell command integration
```

#### Step 1.2: Create Prefect-based Guardian
```python
# DHT/modules/guardian_prefect.py
from prefect import flow, task
from prefect.task_runners import SequentialTaskRunner
import psutil
import os
from pathlib import Path

@task(retries=3, retry_delay_seconds=5)
def run_command_with_limits(cmd: list, memory_mb: int = 2048, timeout: int = 900):
    """Run command with memory and timeout limits"""
    # Implementation here
    pass

@flow(task_runner=SequentialTaskRunner())
def guardian_flow(commands: list):
    """Process commands sequentially with resource management"""
    for cmd in commands:
        run_command_with_limits(cmd)
```

#### Step 1.3: Create Guardian CLI Interface
```python
# DHT/modules/dhtl_guardian_prefect.py
import click
from prefect import serve
from guardian_prefect import guardian_flow

@click.command()
@click.argument('action', type=click.Choice(['start', 'stop', 'status', 'run']))
def guardian_cli(action):
    """Prefect-based guardian command interface"""
    if action == 'start':
        # Start Prefect server/worker
        serve(guardian_flow.to_deployment(name="dht-guardian"))
    elif action == 'run':
        # Submit job to Prefect
        guardian_flow.submit(commands)
```

### Phase 2: Information Extraction System (Priority 2)

#### Step 2.1: Convert diagnostic_reporter to YAML
```python
# Update diagnostic_reporter.py
import yaml

def save_report(self, data: dict, output_path: Path):
    """Save report in YAML format"""
    # Convert datetime objects to strings
    cleaned_data = self._clean_for_yaml(data)

    with open(output_path, 'w') as f:
        yaml.dump(cleaned_data, f,
                  default_flow_style=False,
                  sort_keys=False,
                  allow_unicode=True)
```

#### Step 2.2: Create Base Parser Framework
```python
# DHT/modules/parsers/base_parser.py
from abc import ABC, abstractmethod
from pathlib import Path
import tree_sitter
from prefect import task

class BaseParser(ABC):
    """Base class for all file parsers"""

    def __init__(self, language: str = None):
        if language:
            self.parser = tree_sitter.Parser()
            self.parser.set_language(self.get_language(language))

    @abstractmethod
    def parse_file(self, file_path: Path) -> dict:
        """Parse file and return structured data"""
        pass

    @abstractmethod
    def extract_dependencies(self, file_path: Path) -> list:
        """Extract dependencies from file"""
        pass

    @task
    def parse_with_prefect(self, file_path: Path) -> dict:
        """Prefect task wrapper for parsing"""
        return self.parse_file(file_path)
```

#### Step 2.3: Implement Language-Specific Parsers

**Python Parser**:
```python
# DHT/modules/parsers/python_parser.py
import ast
from pathlib import Path
from .base_parser import BaseParser

class PythonParser(BaseParser):
    def parse_file(self, file_path: Path) -> dict:
        """Parse Python file using AST"""
        with open(file_path, 'r') as f:
            tree = ast.parse(f.read())

        return {
            'imports': self._extract_imports(tree),
            'functions': self._extract_functions(tree),
            'classes': self._extract_classes(tree),
            'dependencies': self._infer_dependencies(tree)
        }

    def _extract_imports(self, tree):
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                for alias in node.names:
                    imports.append(f"{module}.{alias.name}")
        return imports
```

**Bash Parser (using tree-sitter)**:
```python
# DHT/modules/parsers/bash_parser.py
import tree_sitter
from pathlib import Path
from .base_parser import BaseParser

class BashParser(BaseParser):
    def __init__(self):
        super().__init__('bash')
        self.language = tree_sitter.Language('build/languages.so', 'bash')

    def parse_file(self, file_path: Path) -> dict:
        """Parse Bash file using tree-sitter"""
        with open(file_path, 'rb') as f:
            content = f.read()

        tree = self.parser.parse(content)

        return {
            'functions': self._extract_functions(tree),
            'variables': self._extract_variables(tree),
            'commands': self._extract_commands(tree),
            'sourced_files': self._extract_sources(tree)
        }

    def _extract_functions(self, tree):
        """Extract function definitions from bash AST"""
        functions = []

        # Query for function definitions
        query = self.language.query("""
            (function_definition
                name: (word) @name
                body: (compound_statement) @body)
        """)

        captures = query.captures(tree.root_node)
        for node, name in captures:
            if name == 'name':
                functions.append({
                    'name': node.text.decode('utf-8'),
                    'start_line': node.start_point[0],
                    'end_line': node.end_point[0]
                })

        return functions
```

**Package File Parsers**:
```python
# DHT/modules/parsers/package_parsers.py
import toml
import json
import yaml
from pathlib import Path

class PyProjectParser(BaseParser):
    def parse_file(self, file_path: Path) -> dict:
        """Parse pyproject.toml"""
        with open(file_path, 'r') as f:
            data = toml.load(f)

        return {
            'project_name': data.get('project', {}).get('name'),
            'version': data.get('project', {}).get('version'),
            'python_requires': data.get('project', {}).get('requires-python'),
            'dependencies': data.get('project', {}).get('dependencies', []),
            'dev_dependencies': data.get('project', {}).get('optional-dependencies', {}).get('dev', []),
            'build_system': data.get('build-system', {})
        }

class PackageJsonParser(BaseParser):
    def parse_file(self, file_path: Path) -> dict:
        """Parse package.json"""
        with open(file_path, 'r') as f:
            data = json.load(f)

        return {
            'name': data.get('name'),
            'version': data.get('version'),
            'dependencies': data.get('dependencies', {}),
            'devDependencies': data.get('devDependencies', {}),
            'scripts': data.get('scripts', {}),
            'engines': data.get('engines', {})
        }

class CargoTomlParser(BaseParser):
    def parse_file(self, file_path: Path) -> dict:
        """Parse Cargo.toml"""
        with open(file_path, 'r') as f:
            data = toml.load(f)

        return {
            'package': data.get('package', {}),
            'dependencies': data.get('dependencies', {}),
            'dev-dependencies': data.get('dev-dependencies', {}),
            'build-dependencies': data.get('build-dependencies', {})
        }
```

#### Step 2.4: Create Comprehensive Project Analyzer
```python
# DHT/modules/project_analyzer.py
from pathlib import Path
from prefect import flow, task
from typing import Dict, List
import concurrent.futures
from .parsers import *

class ProjectAnalyzer:
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.parsers = {
            '.py': PythonParser(),
            '.sh': BashParser(),
            '.bash': BashParser(),
            'pyproject.toml': PyProjectParser(),
            'package.json': PackageJsonParser(),
            'Cargo.toml': CargoTomlParser(),
            'go.mod': GoModParser(),
            'requirements.txt': RequirementsParser(),
            'Gemfile': GemfileParser(),
            'CMakeLists.txt': CMakeParser(),
        }

    @flow(name="analyze-project")
    def analyze(self) -> Dict:
        """Comprehensive project analysis"""
        # Step 1: Find all relevant files
        files = self.find_all_files()

        # Step 2: Parse files in parallel
        parsed_data = self.parse_files_parallel(files)

        # Step 3: Extract cross-file relationships
        relationships = self.analyze_relationships(parsed_data)

        # Step 4: Infer project structure
        structure = self.infer_project_structure(parsed_data)

        # Step 5: Generate comprehensive report
        return self.generate_report(parsed_data, relationships, structure)

    @task
    def find_all_files(self) -> Dict[str, List[Path]]:
        """Find all files grouped by type"""
        files = {}

        # Define patterns for each file type
        patterns = {
            'python': ['**/*.py'],
            'bash': ['**/*.sh', '**/*.bash'],
            'javascript': ['**/*.js', '**/*.jsx', '**/*.ts', '**/*.tsx'],
            'rust': ['**/*.rs'],
            'go': ['**/*.go'],
            'c_cpp': ['**/*.c', '**/*.cpp', '**/*.h', '**/*.hpp'],
            'config': ['**/pyproject.toml', '**/package.json', '**/Cargo.toml',
                      '**/go.mod', '**/requirements*.txt', '**/Gemfile',
                      '**/CMakeLists.txt', '**/.env*', '**/*.yaml', '**/*.yml']
        }

        for file_type, patterns_list in patterns.items():
            files[file_type] = []
            for pattern in patterns_list:
                files[file_type].extend(self.project_root.glob(pattern))

        return files

    @task
    def parse_files_parallel(self, files: Dict[str, List[Path]]) -> Dict:
        """Parse all files using appropriate parsers"""
        parsed_data = {}

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = {}

            for file_type, file_list in files.items():
                for file_path in file_list:
                    # Skip virtual environments and build directories
                    if any(part in str(file_path) for part in ['.venv', '__pycache__', 'node_modules', 'target', 'build']):
                        continue

                    # Get appropriate parser
                    parser = self.get_parser_for_file(file_path)
                    if parser:
                        future = executor.submit(parser.parse_file, file_path)
                        futures[future] = (file_path, file_type)

            # Collect results
            for future in concurrent.futures.as_completed(futures):
                file_path, file_type = futures[future]
                try:
                    result = future.result()
                    parsed_data[str(file_path)] = {
                        'type': file_type,
                        'data': result
                    }
                except Exception as e:
                    print(f"Error parsing {file_path}: {e}")

        return parsed_data
```

#### Step 2.5: Create Heuristic Analysis Functions
```python
# DHT/modules/heuristics.py
from typing import Dict, List
from pathlib import Path

class ProjectHeuristics:
    """Heuristic analysis for project type and structure inference"""

    @staticmethod
    def detect_project_type(parsed_data: Dict) -> str:
        """Detect the primary project type"""
        indicators = {
            'django': ['manage.py', 'settings.py', 'wsgi.py', 'django imports'],
            'flask': ['app.py', 'flask imports', 'application.py'],
            'fastapi': ['main.py', 'fastapi imports', 'uvicorn'],
            'react': ['package.json with react', 'App.js', 'index.js'],
            'vue': ['package.json with vue', 'App.vue'],
            'cli': ['click imports', 'argparse imports', '__main__.py'],
            'library': ['setup.py', '__init__.py in root', 'no main entry'],
            'data-science': ['jupyter files', 'pandas imports', 'numpy imports'],
            'microservice': ['Dockerfile', 'docker-compose.yml', 'multiple services']
        }

        scores = {}
        for project_type, markers in indicators.items():
            score = 0
            for marker in markers:
                if ProjectHeuristics._check_marker(parsed_data, marker):
                    score += 1
            scores[project_type] = score

        return max(scores, key=scores.get) if scores else 'generic'

    @staticmethod
    def infer_dependencies(parsed_data: Dict) -> Dict[str, List[str]]:
        """Infer system and package dependencies from imports"""
        dependencies = {
            'python': [],
            'system': [],
            'nodejs': [],
            'rust': [],
            'go': []
        }

        # Python dependencies from imports
        import_to_package = {
            'cv2': 'opencv-python',
            'sklearn': 'scikit-learn',
            'PIL': 'Pillow',
            'yaml': 'PyYAML',
            'psycopg2': {'package': 'psycopg2-binary', 'system': ['postgresql-client']},
            'mysqldb': {'package': 'mysqlclient', 'system': ['mysql-client']},
        }

        # Analyze all Python files
        for file_path, file_data in parsed_data.items():
            if file_data['type'] == 'python':
                imports = file_data['data'].get('imports', [])
                for imp in imports:
                    base_module = imp.split('.')[0]
                    if base_module in import_to_package:
                        mapping = import_to_package[base_module]
                        if isinstance(mapping, dict):
                            dependencies['python'].append(mapping['package'])
                            dependencies['system'].extend(mapping.get('system', []))
                        else:
                            dependencies['python'].append(mapping)

        # Remove duplicates
        for key in dependencies:
            dependencies[key] = list(set(dependencies[key]))

        return dependencies
```

### Phase 3: Integration with DHT

#### Step 3.1: Update diagnostic_reporter.py
```python
# Add to diagnostic_reporter.py
from project_analyzer import ProjectAnalyzer
from prefect import flow

class DiagnosticReporter:
    # ... existing code ...

    @flow(name="comprehensive-diagnostic")
    def generate_comprehensive_report(self, include_project_analysis=True):
        """Generate complete environment and project report"""

        # Existing system diagnostics
        system_data = self.collect_system_info()

        # New project analysis
        if include_project_analysis:
            analyzer = ProjectAnalyzer(Path.cwd())
            project_data = analyzer.analyze()
        else:
            project_data = {}

        # Combine all data
        report = {
            'version': '2.0',
            'timestamp': datetime.utcnow().isoformat(),
            'system': system_data,
            'project': project_data,
            'validation': self.generate_checksums()
        }

        # Save as YAML
        output_path = Path('.dht') / 'environment_report.yaml'
        self.save_report(report, output_path)

        return report
```

#### Step 3.2: Create Background Analysis Service
```python
# DHT/modules/background_analyzer.py
from prefect import serve
from project_analyzer import ProjectAnalyzer
from diagnostic_reporter import DiagnosticReporter
import time

def start_background_analysis():
    """Start Prefect server with analysis flows"""

    # Create deployments
    analyzer_deployment = ProjectAnalyzer.analyze.to_deployment(
        name="project-analyzer",
        interval=300  # Run every 5 minutes
    )

    diagnostic_deployment = DiagnosticReporter.generate_comprehensive_report.to_deployment(
        name="diagnostic-reporter",
        interval=600  # Run every 10 minutes
    )

    # Serve both deployments
    serve(analyzer_deployment, diagnostic_deployment)
```

## Updated Task List for tasks_checklist.md

### Phase 0: Prefect Foundation (NEW - Highest Priority)

- **#32a - Install and Configure Prefect:** Add Prefect to dependencies and create base configuration
- **#32b - Create Prefect Guardian:** Replace shell-based guardian with Prefect flows
- **#32c - Implement Task Queue System:** Create queue for all DHT operations

### Phase 1: Information Extraction (Revised)

- **#33a - Convert to YAML Output:** Update diagnostic_reporter to use YAML
- **#33b - Create Parser Framework:** Base parser class with Prefect integration
- **#33c - Implement Python Parser:** AST-based Python file analysis
- **#33d - Implement Bash Parser:** Tree-sitter based Bash analysis
- **#33e - Implement Package Parsers:** Parse pyproject.toml, package.json, etc.
- **#33f - Create Project Analyzer:** Comprehensive parallel file analysis
- **#33g - Implement Heuristics:** Project type detection and dependency inference
- **#33h - Create Background Service:** Prefect-based continuous analysis

This approach ensures:
1. All operations run through Prefect for proper resource management
2. Comprehensive file parsing using appropriate tools
3. Parallel processing for performance
4. Extensible parser framework for adding new languages
5. YAML output for consistency with .dhtconfig
