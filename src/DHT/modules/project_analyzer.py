#!/usr/bin/env python3

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Initial implementation of project analyzer module
# - Provides basic project structure analysis
# - Integrates with parsers for dependency detection
# - Detects project type and configuration files
# 

"""
Project Analyzer Module.

This module analyzes project structures to detect type, dependencies,
and configuration requirements.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Set
import logging

from DHT.modules.parsers.python_parser import PythonParser


class ProjectAnalyzer:
    """Basic project analyzer for DHT configuration generation."""
    
    def __init__(self):
        """Initialize project analyzer."""
        self.logger = logging.getLogger(__name__)
        self.python_parser = PythonParser()
        
        # Common project file patterns
        self.project_files = {
            "python": {
                "pyproject.toml",
                "setup.py",
                "setup.cfg",
                "requirements.txt",
                "requirements.in",
                "Pipfile",
                "poetry.lock",
                "uv.lock",
            },
            "nodejs": {
                "package.json",
                "package-lock.json",
                "yarn.lock",
                "pnpm-lock.yaml",
            },
            "build": {
                "Makefile",
                "CMakeLists.txt",
                "meson.build",
            },
            "ci": {
                ".github/workflows",
                ".gitlab-ci.yml",
                ".travis.yml",
                "azure-pipelines.yml",
                ".circleci/config.yml",
            },
            "container": {
                "Dockerfile",
                "docker-compose.yml",
                "docker-compose.yaml",
                ".dockerignore",
            },
            "version_control": {
                ".git",
                ".gitignore",
                ".gitattributes",
            },
            "quality": {
                ".pre-commit-config.yaml",
                ".flake8",
                ".pylintrc",
                "tox.ini",
                ".editorconfig",
            },
        }
    
    def analyze_project(self, project_path: Path) -> dict[str, Any]:
        """
        Analyze a project directory and return structured information.
        
        Args:
            project_path: Path to the project root directory
            
        Returns:
            Dictionary containing project analysis results
        """
        project_path = Path(project_path).resolve()
        
        if not project_path.exists():
            return {"error": f"Project path does not exist: {project_path}"}
        
        # Collect basic project information
        project_info = {
            "name": project_path.name,
            "root_path": str(project_path),
            "project_type": "unknown",
            "project_subtypes": [],
            "configurations": {},
            "dependencies": {},
            "file_analysis": {},
            "structure": {
                "entry_points": [],
                "has_tests": False,
            },
        }
        
        # Scan for project files
        found_files = self._scan_project_files(project_path)
        
        # Determine project type
        project_type = self._determine_project_type(found_files)
        project_info["project_type"] = project_type
        
        # Detect configurations
        configs = self._detect_configurations(found_files)
        project_info["configurations"] = configs
        
        # Analyze dependencies (simplified)
        if project_type == "python":
            project_info["dependencies"] = self._analyze_python_dependencies(
                project_path, found_files
            )
        
        # Add subtypes based on findings
        if "docker" in configs:
            project_info["project_subtypes"].append("containerized")
        
        if any(ci in found_files for ci in self.project_files["ci"]):
            project_info["project_subtypes"].append("ci-enabled")
        
        # Analyze Python files
        self._analyze_python_files(project_path, project_info)
        
        return project_info
    
    def _scan_project_files(self, project_path: Path) -> set[str]:
        """Scan project for known configuration files."""
        found_files = set()
        
        # Check root directory
        for item in project_path.iterdir():
            if item.is_file():
                found_files.add(item.name)
            elif item.is_dir():
                found_files.add(item.name)
                # Check one level deep for CI configs
                if item.name == ".github":
                    workflows = item / "workflows"
                    if workflows.exists():
                        found_files.add(".github/workflows")
        
        return found_files
    
    def _determine_project_type(self, found_files: set[str]) -> str:
        """Determine the primary project type."""
        # Count indicators for each type
        type_scores = {}
        
        for project_type, indicators in self.project_files.items():
            if project_type in ["build", "ci", "container", "version_control", "quality"]:
                continue  # Skip non-primary types
            
            score = len(found_files & indicators)
            if score > 0:
                type_scores[project_type] = score
        
        if not type_scores:
            return "unknown"
        
        # Return type with highest score
        return max(type_scores, key=type_scores.get)
    
    def _detect_configurations(self, found_files: set[str]) -> dict[str, bool]:
        """Detect various configuration aspects."""
        configs = {}
        
        # Version control
        configs["has_git"] = ".git" in found_files
        configs["has_gitignore"] = ".gitignore" in found_files
        
        # Python specific
        configs["has_pyproject"] = "pyproject.toml" in found_files
        configs["has_setup_py"] = "setup.py" in found_files
        configs["has_requirements"] = "requirements.txt" in found_files
        configs["has_uv_lock"] = "uv.lock" in found_files
        
        # Build tools
        configs["has_makefile"] = "Makefile" in found_files
        configs["has_cmake"] = "CMakeLists.txt" in found_files
        
        # Container
        configs["has_dockerfile"] = "Dockerfile" in found_files
        configs["has_docker_compose"] = any(
            f in found_files for f in ["docker-compose.yml", "docker-compose.yaml"]
        )
        
        # Testing
        configs["has_pytest"] = any(
            "pytest" in str(f) or "test" in str(f) for f in found_files
        )
        configs["has_unittest"] = False  # Would need to check file contents
        
        # CI/CD
        configs["has_ci"] = any(
            indicator in found_files for indicator in self.project_files["ci"]
        )
        
        # Quality tools
        configs["has_pre_commit"] = ".pre-commit-config.yaml" in found_files
        configs["has_linting"] = any(
            f in found_files for f in [".flake8", ".pylintrc", "tox.ini"]
        )
        
        return configs
    
    def _analyze_python_dependencies(
        self, project_path: Path, found_files: set[str]
    ) -> dict[str, Any]:
        """Analyze Python dependencies from various sources."""
        dependencies = {
            "python": {
                "runtime": [],
                "development": [],
                "all": [],
            }
        }
        
        # Check requirements.txt
        if "requirements.txt" in found_files:
            req_path = project_path / "requirements.txt"
            if req_path.exists():
                try:
                    with open(req_path, "r") as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith("#"):
                                # Simple parsing - just get package name
                                pkg_name = line.split("==")[0].split(">=")[0].split("<")[0].strip()
                                if pkg_name:
                                    dependencies["python"]["runtime"].append(pkg_name)
                except Exception as e:
                    self.logger.warning(f"Failed to parse requirements.txt: {e}")
        
        # Set all dependencies
        all_deps = set(dependencies["python"]["runtime"] + dependencies["python"]["development"])
        dependencies["python"]["all"] = sorted(list(all_deps))
        
        return dependencies
    
    def _analyze_python_files(self, project_path: Path, project_info: dict[str, Any]) -> None:
        """Analyze Python files in the project."""
        # Common Python file patterns to analyze
        python_patterns = ["*.py"]
        entry_point_names = {"manage.py", "app.py", "main.py", "application.py", "wsgi.py", "asgi.py", "cli.py", "__main__.py"}
        
        # Limit the depth of search to avoid very deep recursion
        max_depth = 5
        analyzed_count = 0
        max_files = 100  # Limit to prevent excessive analysis
        
        def relative_path(file_path: Path) -> str:
            """Get relative path from project root."""
            try:
                return str(file_path.relative_to(project_path))
            except ValueError:
                return str(file_path)
        
        # Search for Python files
        for pattern in python_patterns:
            for depth in range(max_depth):
                search_pattern = "/".join(["*"] * depth + [pattern])
                for py_file in project_path.glob(search_pattern):
                    if analyzed_count >= max_files:
                        break
                    
                    if py_file.is_file() and not any(part.startswith('.') for part in py_file.parts):
                        # Skip hidden directories and common virtual env names
                        skip_dirs = {'venv', 'env', '.venv', '.env', '__pycache__', 'node_modules', '.git'}
                        if any(skip_dir in py_file.parts for skip_dir in skip_dirs):
                            continue
                        
                        # Parse the Python file
                        rel_path = relative_path(py_file)
                        parse_result = self.python_parser.parse_file(py_file)
                        
                        if "error" not in parse_result:
                            # Add to file analysis
                            project_info["file_analysis"][rel_path] = parse_result
                            analyzed_count += 1
                            
                            # Check if it's an entry point
                            if py_file.name in entry_point_names:
                                project_info["structure"]["entry_points"].append(rel_path)
                            
                            # Check if it's a test file
                            if "test" in py_file.name.lower() or "test" in str(py_file.parent).lower():
                                project_info["structure"]["has_tests"] = True
        
        # Add framework detection based on imports
        frameworks = set()
        for file_data in project_info["file_analysis"].values():
            if "imports" in file_data:
                for imp in file_data["imports"]:
                    module = imp.get("module", "")
                    if module.startswith("django"):
                        frameworks.add("django")
                    elif module.startswith("flask"):
                        frameworks.add("flask")
                    elif module.startswith("fastapi"):
                        frameworks.add("fastapi")
                    elif module.startswith("streamlit"):
                        frameworks.add("streamlit")
        
        project_info["frameworks"] = list(frameworks)
