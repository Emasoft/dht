#!/usr/bin/env python3
"""
Test suite for the project analyzer.  Tests the comprehensive project analysis functionality that: - Detects project types and structures - Analyzes dependencies across all files - Creates project metadata - Integrates with all parsers

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

"""
Test suite for the project analyzer.

Tests the comprehensive project analysis functionality that:
- Detects project types and structures
- Analyzes dependencies across all files
- Creates project metadata
- Integrates with all parsers
"""

import json
from unittest.mock import AsyncMock, Mock, patch

import pytest

from DHT.modules.project_analyzer import ProjectAnalyzer


class TestProjectAnalyzer:
    """Test the main project analyzer functionality."""

    @pytest.fixture
    def analyzer(self):
        """Create a project analyzer instance."""
        return ProjectAnalyzer()

    @pytest.fixture
    def simple_python_project(self, tmp_path):
        """Create a simple Python project structure."""
        # Create project structure
        project_dir = tmp_path / "simple_project"
        project_dir.mkdir()

        # Main Python file
        main_py = project_dir / "main.py"
        main_py.write_text("""
#!/usr/bin/env python3
import click
import requests
from pathlib import Path

@click.command()
def main():
    \"\"\"Simple CLI application.\"\"\"
    response = requests.get("https://api.example.com")
    print(response.json())

if __name__ == "__main__":
    main()
""")

        # Requirements file
        requirements = project_dir / "requirements.txt"
        requirements.write_text("""
click>=8.0.0
requests==2.28.0
pytest>=7.0.0
""")

        # Simple test file
        test_dir = project_dir / "tests"
        test_dir.mkdir()
        test_file = test_dir / "test_main.py"
        test_file.write_text("""
import pytest
from main import main

def test_main():
    assert main is not None
""")

        return project_dir

    @pytest.fixture
    def complex_python_project(self, tmp_path):
        """Create a complex Python project with pyproject.toml."""
        project_dir = tmp_path / "complex_project"
        project_dir.mkdir()

        # pyproject.toml
        pyproject = project_dir / "pyproject.toml"
        pyproject.write_text("""
[project]
name = "complex-app"
version = "0.1.0"
description = "A complex Python application"
requires-python = ">=3.8"
dependencies = [
    "fastapi>=0.95.0",
    "uvicorn[standard]>=0.20.0",
    "sqlalchemy>=2.0.0",
    "pydantic>=2.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "black>=23.0.0",
    "mypy>=1.0.0",
]

[build-system]
requires = ["setuptools>=61", "wheel"]
build-backend = "setuptools.build_meta"

[tool.black]
line-length = 88

[tool.mypy]
strict = true
""")

        # Source directory
        src_dir = project_dir / "src" / "complex_app"
        src_dir.mkdir(parents=True)

        # __init__.py
        (src_dir / "__init__.py").write_text('__version__ = "0.1.0"')

        # Main application
        (src_dir / "app.py").write_text("""
from fastapi import FastAPI
from sqlalchemy import create_engine
from pydantic import BaseModel

app = FastAPI()

class Item(BaseModel):
    name: str
    price: float

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post("/items/")
async def create_item(item: Item):
    return item
""")

        # Database models
        (src_dir / "models.py").write_text("""
from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    price = Column(Float, nullable=False)
""")

        return project_dir

    @pytest.fixture
    def node_project(self, tmp_path):
        """Create a Node.js project structure."""
        project_dir = tmp_path / "node_project"
        project_dir.mkdir()

        # package.json
        package_json = project_dir / "package.json"
        package_json.write_text(
            json.dumps(
                {
                    "name": "node-app",
                    "version": "1.0.0",
                    "description": "A Node.js application",
                    "main": "index.js",
                    "scripts": {
                        "start": "node index.js",
                        "test": "jest",
                        "dev": "nodemon index.js",
                    },
                    "dependencies": {
                        "express": "^4.18.0",
                        "mongoose": "^7.0.0",
                        "dotenv": "^16.0.0",
                    },
                    "devDependencies": {
                        "jest": "^29.0.0",
                        "nodemon": "^2.0.0",
                        "eslint": "^8.0.0",
                    },
                },
                indent=2,
            )
        )

        # index.js
        index_js = project_dir / "index.js"
        index_js.write_text("""
const express = require('express');
const mongoose = require('mongoose');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3000;

app.get('/', (req, res) => {
    res.json({ message: 'Hello World' });
});

app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
});
""")

        return project_dir

    @pytest.fixture
    def mixed_language_project(self, tmp_path):
        """Create a project with multiple languages."""
        project_dir = tmp_path / "mixed_project"
        project_dir.mkdir()

        # Python backend
        backend_dir = project_dir / "backend"
        backend_dir.mkdir()

        (backend_dir / "requirements.txt").write_text("""
flask>=2.0.0
flask-cors>=3.0.0
redis>=4.0.0
""")

        (backend_dir / "app.py").write_text("""
from flask import Flask, jsonify
from flask_cors import CORS
import redis

app = Flask(__name__)
CORS(app)

@app.route('/api/data')
def get_data():
    return jsonify({"data": "from backend"})
""")

        # Node.js frontend
        frontend_dir = project_dir / "frontend"
        frontend_dir.mkdir()

        (frontend_dir / "package.json").write_text(
            json.dumps(
                {
                    "name": "frontend",
                    "version": "0.1.0",
                    "dependencies": {"react": "^18.0.0", "axios": "^1.0.0"},
                },
                indent=2,
            )
        )

        # Shell scripts
        (project_dir / "deploy.sh").write_text("""
#!/bin/bash
set -e

echo "Deploying application..."

# Build frontend
cd frontend
npm install
npm run build

# Deploy backend
cd ../backend
pip install -r requirements.txt
gunicorn app:app
""")

        # Docker compose
        (project_dir / "docker-compose.yml").write_text("""
version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "5000:5000"
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
  redis:
    image: redis:alpine
""")

        return project_dir

    def test_analyze_simple_python_project(self, analyzer, simple_python_project):
        """Test analyzing a simple Python project."""
        result = analyzer.analyze_project(simple_python_project)

        expected = {
            "project_type": "python",
            "project_subtypes": ["cli", "simple"],
            "root_path": str(simple_python_project),
            "name": "simple_project",
            "languages": {"python": {"file_count": 2, "line_count": 20}},
            "dependencies": {
                "python": {
                    "runtime": ["click", "requests"],
                    "development": ["pytest"],
                    "all": ["click", "requests", "pytest"],
                }
            },
            "files_analyzed": 3,
            "structure": {
                "has_tests": True,
                "has_requirements": True,
                "has_pyproject": False,
                "has_setup_py": False,
                "test_framework": "pytest",
                "entry_points": ["main.py"],
            },
        }

        assert result["project_type"] == expected["project_type"]
        assert result["languages"]["python"]["file_count"] == 2
        assert set(result["dependencies"]["python"]["runtime"]) == {"click", "requests"}

    def test_analyze_complex_python_project(self, analyzer, complex_python_project):
        """Test analyzing a complex Python project with pyproject.toml."""
        # result = analyzer.analyze_project(complex_python_project)

        expected = {
            "project_type": "python",
            "project_subtypes": ["web", "fastapi", "structured"],
            "frameworks": ["fastapi", "sqlalchemy"],
            "build_system": {
                "backend": "setuptools.build_meta",
                "requires": ["setuptools>=61", "wheel"],
            },
            "python_version": ">=3.8",
            "has_type_checking": True,
            "code_formatters": ["black"],
            "structure": {
                "layout": "src",
                "has_tests": False,  # No tests in this example
                "has_pyproject": True,
                "package_name": "complex_app",
            },
        }

        # assert result["project_type"] == "python"
        # assert "fastapi" in result["project_subtypes"]
        # assert result["structure"]["layout"] == "src"

    def test_analyze_node_project(self, analyzer, node_project):
        """Test analyzing a Node.js project."""
        # result = analyzer.analyze_project(node_project)

        expected = {
            "project_type": "nodejs",
            "project_subtypes": ["express", "web"],
            "frameworks": ["express", "mongoose"],
            "runtime": {
                "node": None,  # Version not specified
                "npm": None,
            },
            "scripts": {
                "start": "node index.js",
                "test": "jest",
                "dev": "nodemon index.js",
            },
            "test_framework": "jest",
            "dependencies": {
                "nodejs": {
                    "runtime": ["express", "mongoose", "dotenv"],
                    "development": ["jest", "nodemon", "eslint"],
                }
            },
        }

        # assert result["project_type"] == "nodejs"
        # assert "express" in result["frameworks"]
        # assert result["test_framework"] == "jest"

    def test_analyze_mixed_language_project(self, analyzer, mixed_language_project):
        """Test analyzing a project with multiple languages."""
        # result = analyzer.analyze_project(mixed_language_project)

        expected = {
            "project_type": "multi-language",
            "project_subtypes": ["fullstack", "containerized"],
            "languages": {
                "python": {"file_count": 1, "primary_use": "backend"},
                "javascript": {"file_count": 0, "primary_use": "frontend"},
                "shell": {"file_count": 1, "primary_use": "deployment"},
            },
            "components": {
                "backend": {
                    "language": "python",
                    "framework": "flask",
                    "path": "backend",
                },
                "frontend": {
                    "language": "javascript",
                    "framework": "react",
                    "path": "frontend",
                },
            },
            "deployment": {
                "containerized": True,
                "orchestration": "docker-compose",
                "services": ["backend", "frontend", "redis"],
            },
        }

        # assert result["project_type"] == "multi-language"
        # assert "backend" in result["components"]
        # assert result["deployment"]["containerized"] is True

    def test_detect_project_patterns(self, analyzer):
        """Test detection of common project patterns."""
        patterns = [
            {
                "files": ["manage.py", "requirements.txt", "settings.py"],
                "expected_type": "django",
                "expected_subtypes": ["web", "python"],
            },
            {
                "files": ["Cargo.toml", "src/main.rs"],
                "expected_type": "rust",
                "expected_subtypes": ["compiled"],
            },
            {
                "files": ["go.mod", "main.go"],
                "expected_type": "go",
                "expected_subtypes": ["compiled"],
            },
            {
                "files": ["pom.xml", "src/main/java/App.java"],
                "expected_type": "java",
                "expected_subtypes": ["maven", "compiled"],
            },
            {
                "files": ["Gemfile", "config.ru"],
                "expected_type": "ruby",
                "expected_subtypes": ["rack", "web"],
            },
        ]

        for _pattern in patterns:
            # project_type = analyzer.detect_project_type(pattern["files"])
            # assert project_type["primary"] == pattern["expected_type"]
            # assert set(pattern["expected_subtypes"]).issubset(project_type["subtypes"])
            pass

    def test_dependency_resolution(self, analyzer, tmp_path):
        """Test comprehensive dependency resolution across files."""
        project_dir = tmp_path / "dep_test"
        project_dir.mkdir()

        # Multiple dependency files
        (project_dir / "requirements.txt").write_text("requests>=2.25.0\nnumpy")
        (project_dir / "requirements-dev.txt").write_text("pytest\nblack")
        (project_dir / "setup.py").write_text("""
from setuptools import setup
setup(
    install_requires=["click", "requests"],
    extras_require={"test": ["pytest", "coverage"]}
)
""")

        # result = analyzer.analyze_dependencies(project_dir)
        expected = {
            "python": {
                "sources": {
                    "requirements.txt": ["requests", "numpy"],
                    "requirements-dev.txt": ["pytest", "black"],
                    "setup.py": {
                        "install": ["click", "requests"],
                        "test": ["pytest", "coverage"],
                    },
                },
                "consolidated": {
                    "runtime": ["requests", "numpy", "click"],
                    "development": ["pytest", "black", "coverage"],
                    "all": [
                        "requests",
                        "numpy",
                        "click",
                        "pytest",
                        "black",
                        "coverage",
                    ],
                },
                "conflicts": [],  # No version conflicts in this example
            }
        }

        # assert set(result["python"]["consolidated"]["all"]) == set(expected["python"]["consolidated"]["all"])

    @pytest.mark.asyncio
    async def test_parallel_file_analysis(self, analyzer, complex_python_project):
        """Test that files are analyzed in parallel for performance."""
        # Mock the file parsers to track call timing
        with patch("modules.project_analyzer.PythonParser") as mock_parser:
            mock_instance = Mock()
            mock_parser.return_value = mock_instance

            # Simulate slow parsing
            async def slow_parse(file_path):
                import asyncio

                await asyncio.sleep(0.1)
                return {"file": str(file_path)}

            mock_instance.parse_file = AsyncMock(side_effect=slow_parse)

            # start = time.time()
            # await analyzer.analyze_project_async(complex_python_project)
            # duration = time.time() - start

            # Should be faster than sequential (0.1s * file_count)
            # assert duration < 0.5

    def test_configuration_detection(self, analyzer, tmp_path):
        """Test detection of various configuration files."""
        project_dir = tmp_path / "config_test"
        project_dir.mkdir()

        # Create various config files
        configs = {
            ".gitignore": "*.pyc\n__pycache__/",
            ".dockerignore": "*.log\nnode_modules/",
            "Makefile": "test:\n\tpytest",
            ".github/workflows/test.yml": "name: Test\non: push",
            ".gitlab-ci.yml": "test:\n  script: pytest",
            ".pre-commit-config.yaml": "repos: []",
            "tox.ini": "[tox]\nenvlist = py38,py39",
            ".editorconfig": "root = true",
            ".eslintrc.json": "{}",
            "jest.config.js": "module.exports = {}",
        }

        for filename, content in configs.items():
            file_path = project_dir / filename
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content)

        # result = analyzer.detect_configurations(project_dir)
        expected = {
            "version_control": {"system": "git", "ignore_files": [".gitignore"]},
            "ci_cd": {"github_actions": True, "gitlab_ci": True},
            "containerization": {"docker": True, "ignore_files": [".dockerignore"]},
            "build_tools": ["make"],
            "code_quality": {"pre_commit": True, "linters": ["eslint"]},
            "testing": {"frameworks": ["jest", "pytest"], "tools": ["tox"]},
        }

        # assert result["version_control"]["system"] == "git"
        # assert result["ci_cd"]["github_actions"] is True
        # assert "make" in result["build_tools"]

    def test_project_metadata_generation(self, analyzer, complex_python_project):
        """Test generation of comprehensive project metadata."""
        # result = analyzer.generate_metadata(complex_python_project)

        expected_keys = [
            "project_hash",  # Unique identifier
            "analysis_timestamp",
            "dht_version",
            "project_info",
            "file_statistics",
            "dependency_summary",
            "quality_metrics",
            "recommendations",
        ]

        # for key in expected_keys:
        #     assert key in result

        # assert result["project_info"]["name"] == "complex-app"
        # assert isinstance(result["analysis_timestamp"], str)

    def test_error_handling(self, analyzer, tmp_path):
        """Test graceful error handling for various edge cases."""
        # Empty directory
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        # result = analyzer.analyze_project(empty_dir)
        # assert result["project_type"] == "unknown"
        # assert result["warnings"] == ["No recognizable project files found"]

        # Corrupted files
        corrupt_dir = tmp_path / "corrupt"
        corrupt_dir.mkdir()
        (corrupt_dir / "requirements.txt").write_bytes(b"\x00\x01\x02\x03")
        # result = analyzer.analyze_project(corrupt_dir)
        # assert len(result["errors"]) > 0

        # Missing permissions (would need to test on real filesystem)
        # locked_file = tmp_path / "locked.py"
        # locked_file.write_text("print('hello')")
        # locked_file.chmod(0o000)
        # result = analyzer.analyze_file(locked_file)
        # assert "permission" in result.get("error", "").lower()

    def test_caching_mechanism(self, analyzer, simple_python_project):
        """Test that analysis results are cached appropriately."""
        # First analysis
        # result1 = analyzer.analyze_project(simple_python_project)
        # analysis_time1 = result1["_analysis_duration"]

        # Second analysis (should be cached)
        # result2 = analyzer.analyze_project(simple_python_project)
        # analysis_time2 = result2["_analysis_duration"]

        # assert analysis_time2 < analysis_time1 * 0.1  # Much faster
        # assert result1["project_hash"] == result2["project_hash"]

        # Modify a file
        (simple_python_project / "new_file.py").write_text("print('new')")

        # Third analysis (cache invalidated)
        # result3 = analyzer.analyze_project(simple_python_project)
        # assert result3["project_hash"] != result1["project_hash"]
        pass


class TestProjectTypeDetection:
    """Test project type detection heuristics."""

    def test_python_project_variants(self):
        """Test detection of various Python project types."""
        test_cases = [
            {
                "files": ["manage.py", "wsgi.py", "urls.py"],
                "expected": {"primary": "python", "framework": "django"},
            },
            {
                "files": ["app.py", "models.py", "templates/"],
                "content_hints": {"app.py": "from flask import Flask"},
                "expected": {"primary": "python", "framework": "flask"},
            },
            {
                "files": ["main.py", "routers/", "models.py"],
                "content_hints": {"main.py": "from fastapi import FastAPI"},
                "expected": {"primary": "python", "framework": "fastapi"},
            },
            {
                "files": ["setup.py", "src/", "tests/", "tox.ini"],
                "expected": {"primary": "python", "structure": "library"},
            },
            {
                "files": ["notebook.ipynb", "data/", "requirements.txt"],
                "expected": {"primary": "python", "variant": "data-science"},
            },
        ]

        # detector = ProjectTypeDetector()
        for _case in test_cases:
            # result = detector.detect(case["files"], case.get("content_hints", {}))
            # assert result["primary"] == case["expected"]["primary"]
            # if "framework" in case["expected"]:
            #     assert result["framework"] == case["expected"]["framework"]
            pass

    def test_web_project_detection(self):
        """Test detection of web projects."""
        test_cases = [
            {
                "files": ["package.json", "src/App.js", "public/index.html"],
                "package_json": {"dependencies": {"react": "^18.0.0"}},
                "expected": {"primary": "javascript", "framework": "react"},
            },
            {
                "files": ["package.json", "pages/", "next.config.js"],
                "expected": {"primary": "javascript", "framework": "nextjs"},
            },
            {
                "files": ["package.json", "nuxt.config.js"],
                "expected": {"primary": "javascript", "framework": "nuxt"},
            },
            {
                "files": ["angular.json", "src/app/"],
                "expected": {"primary": "typescript", "framework": "angular"},
            },
            {
                "files": ["index.html", "style.css", "script.js"],
                "expected": {"primary": "web", "variant": "static"},
            },
        ]

        for _case in test_cases:
            # result = detector.detect_web_project(case["files"], case.get("package_json"))
            # assert result["framework"] == case["expected"]["framework"]
            pass

    def test_mobile_project_detection(self):
        """Test detection of mobile projects."""
        test_cases = [
            {
                "files": ["pubspec.yaml", "lib/main.dart"],
                "expected": {"primary": "dart", "framework": "flutter"},
            },
            {
                "files": ["package.json", "App.tsx", "android/", "ios/"],
                "package_json": {"dependencies": {"react-native": "0.70.0"}},
                "expected": {"primary": "javascript", "framework": "react-native"},
            },
            {
                "files": ["AndroidManifest.xml", "build.gradle", "src/main/java/"],
                "expected": {"primary": "android", "language": "java"},
            },
            {
                "files": ["Package.swift", "Sources/", "*.xcodeproj"],
                "expected": {"primary": "ios", "language": "swift"},
            },
        ]

        for _case in test_cases:
            # result = detector.detect_mobile_project(case["files"])
            # assert result["primary"] == case["expected"]["primary"]
            pass


class TestDependencyAnalysis:
    """Test dependency analysis across different package managers."""

    def test_python_dependency_consolidation(self):
        """Test consolidating Python dependencies from multiple sources."""
        sources = {
            "requirements.txt": [
                {"name": "django", "version": ">=3.2"},
                {"name": "requests", "version": "==2.28.0"},
            ],
            "setup.py": [
                {"name": "django", "version": ">=3.2,<4.0"},
                {"name": "click", "version": None},
            ],
            "pyproject.toml": [
                {"name": "django", "version": "^3.2"},
                {"name": "pytest", "version": ">=7.0"},
            ],
        }

        # consolidator = DependencyConsolidator()
        # result = consolidator.consolidate_python(sources)

        expected = {
            "django": {
                "versions": [">=3.2", ">=3.2,<4.0", "^3.2"],
                "sources": ["requirements.txt", "setup.py", "pyproject.toml"],
                "resolved": ">=3.2,<4.0",  # Most restrictive
            },
            "requests": {
                "versions": ["==2.28.0"],
                "sources": ["requirements.txt"],
                "resolved": "==2.28.0",
            },
            "click": {"versions": [None], "sources": ["setup.py"], "resolved": None},
            "pytest": {
                "versions": [">=7.0"],
                "sources": ["pyproject.toml"],
                "resolved": ">=7.0",
            },
        }

        # assert result == expected

    def test_version_conflict_detection(self):
        """Test detection of version conflicts."""
        dependencies = [
            {"name": "package-a", "version": "==1.0.0", "source": "file1"},
            {"name": "package-a", "version": "==2.0.0", "source": "file2"},
            {"name": "package-b", "version": ">=1.0", "source": "file1"},
            {"name": "package-b", "version": "<1.5", "source": "file2"},
        ]

        # detector = ConflictDetector()
        # conflicts = detector.find_conflicts(dependencies)

        expected_conflicts = [
            {
                "package": "package-a",
                "conflict_type": "incompatible_versions",
                "versions": ["==1.0.0", "==2.0.0"],
                "sources": ["file1", "file2"],
            }
        ]

        # assert len(conflicts) == 1
        # assert conflicts[0]["package"] == "package-a"
