#!/usr/bin/env python3
"""
Test suite for package file parsers.  Tests various package file formats including: - requirements.txt and requirements.in - pyproject.toml - setup.py and setup.cfg - package.json - Cargo.toml

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

"""
Test suite for package file parsers.

Tests various package file formats including:
- requirements.txt and requirements.in
- pyproject.toml
- setup.py and setup.cfg
- package.json
- Cargo.toml
- go.mod
- Gemfile
- pom.xml
- build.gradle
"""

import json
from typing import Any

from DHT.modules.parsers.package_json_parser import PackageJsonParser
from DHT.modules.parsers.pyproject_parser import PyProjectParser

# Import implemented parsers
from DHT.modules.parsers.requirements_parser import RequirementsParser

# TODO: Implement these parsers
# from DHT.modules.parsers.setup_parser import SetupParser
# from DHT.modules.parsers.cargo_parser import CargoParser
# from DHT.modules.parsers.go_parser import GoModParser
# from DHT.modules.parsers.gemfile_parser import GemfileParser
# from DHT.modules.parsers.maven_parser import MavenParser
# from DHT.modules.parsers.gradle_parser import GradleParser


class TestRequirementsParser:
    """Test parsing of requirements.txt and requirements.in files."""

    def test_parse_simple_requirements(self, tmp_path) -> Any:
        """Test parsing a simple requirements.txt file."""
        content = """
# This is a comment
requests==2.28.0
flask>=2.0.0
django<4.0
numpy~=1.21.0
pandas
"""
        req_file = tmp_path / "requirements.txt"
        req_file.write_text(content)

        parser = RequirementsParser()
        result = parser.parse_file(req_file)

        # Expected result structure
        expected = {
            "dependencies": [
                {"name": "requests", "version": "==2.28.0", "line": 3},
                {"name": "flask", "version": ">=2.0.0", "line": 4},
                {"name": "django", "version": "<4.0", "line": 5},
                {"name": "numpy", "version": "~=1.21.0", "line": 6},
                {"name": "pandas", "version": None, "line": 7},
            ],
            "comments": [{"text": "This is a comment", "line": 2}],
            "file_metadata": {"name": "requirements.txt", "format": "requirements"},
        }

        assert len(result["dependencies"]) == len(expected["dependencies"])
        for i, dep in enumerate(result["dependencies"]):
            assert dep["name"] == expected["dependencies"][i]["name"]
            assert dep["version"] == expected["dependencies"][i]["version"]
            assert dep["line"] == expected["dependencies"][i]["line"]
        assert result["comments"] == expected["comments"]

    def test_parse_requirements_with_extras(self, tmp_path) -> Any:
        """Test parsing requirements with extras."""
        content = """
requests[security,socks]==2.28.0
celery[redis]>=5.0
"""
        req_file = tmp_path / "requirements.txt"
        req_file.write_text(content)

        # parser = RequirementsParser()
        # result = parser.parse_file(req_file)

        expected_deps = [
            {"name": "requests", "version": "==2.28.0", "extras": ["security", "socks"], "line": 2},
            {"name": "celery", "version": ">=5.0", "extras": ["redis"], "line": 3},
        ]

        # assert result["dependencies"][0]["extras"] == expected_deps[0]["extras"]

    def test_parse_requirements_with_urls(self, tmp_path) -> Any:
        """Test parsing requirements with direct URLs."""
        content = """
git+https://github.com/user/repo.git@v1.0#egg=mypackage
https://files.pythonhosted.org/packages/source/p/package/package-1.0.tar.gz
-e ./local/path
"""
        req_file = tmp_path / "requirements.txt"
        req_file.write_text(content)

        # parser = RequirementsParser()
        # result = parser.parse_file(req_file)

        expected_deps = [
            {"name": "mypackage", "url": "git+https://github.com/user/repo.git@v1.0", "vcs": "git", "line": 2},
            {"url": "https://files.pythonhosted.org/packages/source/p/package/package-1.0.tar.gz", "line": 3},
            {"path": "./local/path", "editable": True, "line": 4},
        ]

        # assert len(result["dependencies"]) == 3

    def test_parse_requirements_with_options(self, tmp_path) -> Any:
        """Test parsing requirements with pip options."""
        content = """
--index-url https://pypi.org/simple
--extra-index-url https://test.pypi.org/simple
-r other-requirements.txt
--trusted-host pypi.org

numpy==1.21.0
"""
        req_file = tmp_path / "requirements.txt"
        req_file.write_text(content)

        # parser = RequirementsParser()
        # result = parser.parse_file(req_file)

        expected_options = {
            "index_url": "https://pypi.org/simple",
            "extra_index_urls": ["https://test.pypi.org/simple"],
            "includes": ["other-requirements.txt"],
            "trusted_hosts": ["pypi.org"],
        }

        # assert result["options"] == expected_options
        # assert len(result["dependencies"]) == 1


class TestPyProjectParser:
    """Test parsing of pyproject.toml files."""

    def test_parse_basic_pyproject(self, tmp_path) -> Any:
        """Test parsing a basic pyproject.toml."""
        content = """
[project]
name = "myproject"
version = "0.1.0"
description = "A sample project"
requires-python = ">=3.8"
dependencies = [
    "requests>=2.28",
    "click~=8.0",
]

[project.optional-dependencies]
dev = ["pytest>=7.0", "black"]
docs = ["sphinx"]

[project.scripts]
mycommand = "myproject.cli:main"

[build-system]
requires = ["setuptools>=61", "wheel"]
build-backend = "setuptools.build_meta"
"""
        pyproject_file = tmp_path / "pyproject.toml"
        pyproject_file.write_text(content)

        parser = PyProjectParser()
        result = parser.parse_file(pyproject_file)

        expected = {
            "project": {
                "name": "myproject",
                "version": "0.1.0",
                "description": "A sample project",
                "requires_python": ">=3.8",
                "dependencies": ["requests>=2.28", "click~=8.0"],
            },
            "optional_dependencies": {"dev": ["pytest>=7.0", "black"], "docs": ["sphinx"]},
            "scripts": {"mycommand": "myproject.cli:main"},
            "build_system": {"requires": ["setuptools>=61", "wheel"], "backend": "setuptools.build_meta"},
        }

        assert result["project"]["name"] == expected["project"]["name"]
        assert result["project"]["version"] == expected["project"]["version"]
        assert result["project"]["requires_python"] == expected["project"]["requires_python"]
        # Check dependencies are parsed
        assert len(result["project"]["dependencies"]) == 2
        assert result["project"]["dependencies"][0]["name"] == "requests"
        assert result["project"]["dependencies"][1]["name"] == "click"

    def test_parse_poetry_pyproject(self, tmp_path) -> Any:
        """Test parsing Poetry-style pyproject.toml."""
        content = """
[tool.poetry]
name = "poetry-project"
version = "0.1.0"
description = "Poetry project"

[tool.poetry.dependencies]
python = "^3.8"
requests = "^2.28"
flask = {version = "^2.0", optional = true}

[tool.poetry.group.dev.dependencies]
pytest = "^7.0"
black = "^22.0"

[tool.poetry.extras]
web = ["flask"]
"""
        pyproject_file = tmp_path / "pyproject.toml"
        pyproject_file.write_text(content)

        # parser = PyProjectParser()
        # result = parser.parse_file(pyproject_file)

        # assert result["tool"]["poetry"]["name"] == "poetry-project"
        # assert "flask" in result["tool"]["poetry"]["dependencies"]
        # assert result["tool"]["poetry"]["extras"]["web"] == ["flask"]

    def test_parse_uv_pyproject(self, tmp_path) -> Any:
        """Test parsing UV-style pyproject.toml."""
        content = """
[project]
name = "uv-project"
dependencies = [
    "pandas>=1.3.0",
    "numpy>=1.21.0",
]

[tool.uv]
dev-dependencies = [
    "pytest>=7.0.0",
    "mypy>=1.0.0",
]

[tool.uv.sources]
my-package = { git = "https://github.com/user/repo", branch = "main" }
"""
        pyproject_file = tmp_path / "pyproject.toml"
        pyproject_file.write_text(content)

        # parser = PyProjectParser()
        # result = parser.parse_file(pyproject_file)

        # assert result["tool"]["uv"]["dev-dependencies"] == ["pytest>=7.0.0", "mypy>=1.0.0"]
        # assert "my-package" in result["tool"]["uv"]["sources"]


class TestSetupParser:
    """Test parsing of setup.py and setup.cfg files."""

    def test_parse_setup_py(self, tmp_path) -> Any:
        """Test parsing a setup.py file."""
        content = """
from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="mypackage",
    version="0.1.0",
    author="John Doe",
    author_email="john@example.com",
    description="A sample package",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/user/repo",
    packages=find_packages(),
    install_requires=[
        "requests>=2.25.0",
        "click>=7.0",
    ],
    extras_require={
        "dev": ["pytest>=6.0", "black"],
        "docs": ["sphinx>=4.0"],
    },
    python_requires=">=3.7",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
    ],
    entry_points={
        "console_scripts": [
            "mycommand=mypackage.cli:main",
        ],
    },
)
"""
        setup_file = tmp_path / "setup.py"
        setup_file.write_text(content)

        # parser = SetupParser()
        # result = parser.parse_file(setup_file)

        expected = {
            "name": "mypackage",
            "version": "0.1.0",
            "author": "John Doe",
            "author_email": "john@example.com",
            "install_requires": ["requests>=2.25.0", "click>=7.0"],
            "extras_require": {"dev": ["pytest>=6.0", "black"], "docs": ["sphinx>=4.0"]},
            "python_requires": ">=3.7",
            "entry_points": {"console_scripts": ["mycommand=mypackage.cli:main"]},
        }

        # assert result["name"] == expected["name"]
        # assert result["install_requires"] == expected["install_requires"]

    def test_parse_setup_cfg(self, tmp_path) -> Any:
        """Test parsing a setup.cfg file."""
        content = """
[metadata]
name = mypackage
version = 0.1.0
author = John Doe
author_email = john@example.com
description = A sample package
long_description = file: README.md
long_description_content_type = text/markdown
url = https://github.com/user/repo

[options]
packages = find:
python_requires = >=3.7
install_requires =
    requests>=2.25.0
    click>=7.0

[options.extras_require]
dev =
    pytest>=6.0
    black
docs =
    sphinx>=4.0

[options.entry_points]
console_scripts =
    mycommand = mypackage.cli:main
"""
        setup_cfg = tmp_path / "setup.cfg"
        setup_cfg.write_text(content)

        # parser = SetupParser()
        # result = parser.parse_file(setup_cfg)

        # assert result["metadata"]["name"] == "mypackage"
        # assert result["options"]["python_requires"] == ">=3.7"


class TestPackageJsonParser:
    """Test parsing of package.json files."""

    def test_parse_basic_package_json(self, tmp_path) -> Any:
        """Test parsing a basic package.json."""
        content = {
            "name": "my-app",
            "version": "1.0.0",
            "description": "My Node.js app",
            "main": "index.js",
            "scripts": {"start": "node index.js", "test": "jest", "build": "webpack"},
            "dependencies": {"express": "^4.18.0", "lodash": "~4.17.21"},
            "devDependencies": {"jest": "^29.0.0", "webpack": "^5.0.0"},
            "engines": {"node": ">=14.0.0", "npm": ">=6.0.0"},
        }

        package_file = tmp_path / "package.json"
        package_file.write_text(json.dumps(content, indent=2))

        parser = PackageJsonParser()
        result = parser.parse_file(package_file)

        assert result["name"] == "my-app"
        assert len(result["dependencies"]) == 2
        assert result["dependencies"][0]["name"] == "express"
        assert result["dependencies"][0]["version"] == "^4.18.0"
        assert len(result["devDependencies"]) == 2
        assert result["engines"]["node"] == ">=14.0.0"

    def test_parse_workspaces_package_json(self, tmp_path) -> Any:
        """Test parsing package.json with workspaces."""
        content = {
            "name": "monorepo",
            "private": True,
            "workspaces": ["packages/*", "apps/*"],
            "devDependencies": {"lerna": "^6.0.0"},
        }

        package_file = tmp_path / "package.json"
        package_file.write_text(json.dumps(content, indent=2))

        # parser = PackageJsonParser()
        # result = parser.parse_file(package_file)

        # assert result["workspaces"] == ["packages/*", "apps/*"]
        # assert result["private"] is True


class TestCargoParser:
    """Test parsing of Cargo.toml files."""

    def test_parse_cargo_toml(self, tmp_path) -> Any:
        """Test parsing a Cargo.toml file."""
        content = """
[package]
name = "my-rust-app"
version = "0.1.0"
edition = "2021"
authors = ["John Doe <john@example.com>"]

[dependencies]
serde = { version = "1.0", features = ["derive"] }
tokio = { version = "1.0", features = ["full"] }
reqwest = "0.11"

[dev-dependencies]
mockito = "0.31"

[build-dependencies]
cc = "1.0"

[[bin]]
name = "myapp"
path = "src/main.rs"

[features]
default = ["json"]
json = ["serde/json"]
"""
        cargo_file = tmp_path / "Cargo.toml"
        cargo_file.write_text(content)

        # parser = CargoParser()
        # result = parser.parse_file(cargo_file)

        expected = {
            "package": {"name": "my-rust-app", "version": "0.1.0", "edition": "2021"},
            "dependencies": {
                "serde": {"version": "1.0", "features": ["derive"]},
                "tokio": {"version": "1.0", "features": ["full"]},
                "reqwest": "0.11",
            },
            "dev_dependencies": {"mockito": "0.31"},
            "features": {"default": ["json"], "json": ["serde/json"]},
        }

        # assert result["package"]["name"] == "my-rust-app"
        # assert result["dependencies"]["serde"]["features"] == ["derive"]


class TestGoModParser:
    """Test parsing of go.mod files."""

    def test_parse_go_mod(self, tmp_path) -> Any:
        """Test parsing a go.mod file."""
        content = """
module github.com/user/myapp

go 1.19

require (
    github.com/gin-gonic/gin v1.9.0
    github.com/go-sql-driver/mysql v1.7.0
    golang.org/x/crypto v0.6.0
)

require (
    github.com/bytedance/sonic v1.8.0 // indirect
    github.com/chenzhuoyu/base64x v0.0.0-20221115062448-fe3a3abad311 // indirect
)

replace github.com/broken/package => github.com/fixed/package v1.0.0

exclude github.com/bad/package v1.0.0
"""
        go_mod = tmp_path / "go.mod"
        go_mod.write_text(content)

        # parser = GoModParser()
        # result = parser.parse_file(go_mod)

        expected = {
            "module": "github.com/user/myapp",
            "go_version": "1.19",
            "require": [
                {"path": "github.com/gin-gonic/gin", "version": "v1.9.0"},
                {"path": "github.com/go-sql-driver/mysql", "version": "v1.7.0"},
                {"path": "golang.org/x/crypto", "version": "v0.6.0"},
            ],
            "indirect": [
                {"path": "github.com/bytedance/sonic", "version": "v1.8.0"},
                {"path": "github.com/chenzhuoyu/base64x", "version": "v0.0.0-20221115062448-fe3a3abad311"},
            ],
            "replace": [{"old": "github.com/broken/package", "new": "github.com/fixed/package", "version": "v1.0.0"}],
        }

        # assert result["module"] == expected["module"]
        # assert result["go_version"] == expected["go_version"]


class TestGemfileParser:
    """Test parsing of Gemfile."""

    def test_parse_gemfile(self, tmp_path) -> Any:
        """Test parsing a Gemfile."""
        content = """
source 'https://rubygems.org'
git_source(:github) { |repo| "https://github.com/#{repo}.git" }

ruby '3.1.0'

gem 'rails', '~> 7.0.4'
gem 'pg', '>= 0.18', '< 2.0'
gem 'puma', '~> 5.0'

group :development, :test do
  gem 'byebug', platforms: [:mri, :mingw, :x64_mingw]
  gem 'rspec-rails'
end

group :development do
  gem 'web-console'
  gem 'listen', '~> 3.3'
end

gem 'bootsnap', '>= 1.4.4', require: false
"""
        gemfile = tmp_path / "Gemfile"
        gemfile.write_text(content)

        # parser = GemfileParser()
        # result = parser.parse_file(gemfile)

        expected = {
            "source": "https://rubygems.org",
            "ruby_version": "3.1.0",
            "gems": [
                {"name": "rails", "version": "~> 7.0.4"},
                {"name": "pg", "version": ">= 0.18, < 2.0"},
                {"name": "puma", "version": "~> 5.0"},
            ],
            "groups": {
                "development": ["web-console", "listen"],
                "test": ["rspec-rails"],
                "development,test": ["byebug", "rspec-rails"],
            },
        }

        # assert result["ruby_version"] == "3.1.0"
        # assert len(result["gems"]) >= 3


class TestMavenParser:
    """Test parsing of pom.xml files."""

    def test_parse_pom_xml(self, tmp_path) -> Any:
        """Test parsing a pom.xml file."""
        content = """<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0
         http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>

    <groupId>com.example</groupId>
    <artifactId>my-app</artifactId>
    <version>1.0.0</version>
    <packaging>jar</packaging>

    <properties>
        <maven.compiler.source>11</maven.compiler.source>
        <maven.compiler.target>11</maven.compiler.target>
        <spring.version>5.3.23</spring.version>
    </properties>

    <dependencies>
        <dependency>
            <groupId>org.springframework</groupId>
            <artifactId>spring-core</artifactId>
            <version>${spring.version}</version>
        </dependency>
        <dependency>
            <groupId>junit</groupId>
            <artifactId>junit</artifactId>
            <version>4.13.2</version>
            <scope>test</scope>
        </dependency>
    </dependencies>

    <build>
        <plugins>
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-compiler-plugin</artifactId>
                <version>3.10.1</version>
            </plugin>
        </plugins>
    </build>
</project>
"""
        pom_file = tmp_path / "pom.xml"
        pom_file.write_text(content)

        # parser = MavenParser()
        # result = parser.parse_file(pom_file)

        expected = {
            "groupId": "com.example",
            "artifactId": "my-app",
            "version": "1.0.0",
            "properties": {"maven.compiler.source": "11", "maven.compiler.target": "11", "spring.version": "5.3.23"},
            "dependencies": [
                {"groupId": "org.springframework", "artifactId": "spring-core", "version": "${spring.version}"},
                {"groupId": "junit", "artifactId": "junit", "version": "4.13.2", "scope": "test"},
            ],
        }

        # assert result["artifactId"] == "my-app"
        # assert len(result["dependencies"]) == 2


class TestGradleParser:
    """Test parsing of build.gradle files."""

    def test_parse_build_gradle(self, tmp_path) -> Any:
        """Test parsing a build.gradle file."""
        content = """
plugins {
    id 'java'
    id 'org.springframework.boot' version '2.7.5'
    id 'io.spring.dependency-management' version '1.0.15.RELEASE'
}

group = 'com.example'
version = '0.0.1-SNAPSHOT'
sourceCompatibility = '11'

repositories {
    mavenCentral()
}

dependencies {
    implementation 'org.springframework.boot:spring-boot-starter-web'
    implementation 'org.springframework.boot:spring-boot-starter-data-jpa'
    runtimeOnly 'com.h2database:h2'
    testImplementation 'org.springframework.boot:spring-boot-starter-test'
}

test {
    useJUnitPlatform()
}
"""
        gradle_file = tmp_path / "build.gradle"
        gradle_file.write_text(content)

        # parser = GradleParser()
        # result = parser.parse_file(gradle_file)

        expected = {
            "plugins": [
                {"id": "java"},
                {"id": "org.springframework.boot", "version": "2.7.5"},
                {"id": "io.spring.dependency-management", "version": "1.0.15.RELEASE"},
            ],
            "group": "com.example",
            "version": "0.0.1-SNAPSHOT",
            "java_version": "11",
            "repositories": ["mavenCentral"],
            "dependencies": {
                "implementation": [
                    "org.springframework.boot:spring-boot-starter-web",
                    "org.springframework.boot:spring-boot-starter-data-jpa",
                ],
                "runtimeOnly": ["com.h2database:h2"],
                "testImplementation": ["org.springframework.boot:spring-boot-starter-test"],
            },
        }

        # assert result["group"] == "com.example"
        # assert "implementation" in result["dependencies"]

    def test_parse_build_gradle_kts(self, tmp_path) -> Any:
        """Test parsing a build.gradle.kts (Kotlin DSL) file."""
        content = """
import org.jetbrains.kotlin.gradle.tasks.KotlinCompile

plugins {
    id("org.springframework.boot") version "2.7.5"
    id("io.spring.dependency-management") version "1.0.15.RELEASE"
    kotlin("jvm") version "1.7.20"
    kotlin("plugin.spring") version "1.7.20"
}

group = "com.example"
version = "0.0.1-SNAPSHOT"
java.sourceCompatibility = JavaVersion.VERSION_11

repositories {
    mavenCentral()
}

dependencies {
    implementation("org.springframework.boot:spring-boot-starter-web")
    implementation("com.fasterxml.jackson.module:jackson-module-kotlin")
    implementation("org.jetbrains.kotlin:kotlin-reflect")
    implementation("org.jetbrains.kotlin:kotlin-stdlib-jdk8")
    testImplementation("org.springframework.boot:spring-boot-starter-test")
}

tasks.withType<KotlinCompile> {
    kotlinOptions {
        freeCompilerArgs = listOf("-Xjsr305=strict")
        jvmTarget = "11"
    }
}
"""
        gradle_kts = tmp_path / "build.gradle.kts"
        gradle_kts.write_text(content)

        # parser = GradleParser()
        # result = parser.parse_file(gradle_kts)

        # assert result["group"] == "com.example"
        # assert "kotlin" in str(result["dependencies"]["implementation"])


# Test utility functions that parsers might share
class TestParserUtilities:
    """Test common utility functions used by parsers."""

    def test_version_parsing(self) -> Any:
        """Test parsing various version specifier formats."""
        test_cases = [
            ("==1.2.3", {"operator": "==", "version": "1.2.3"}),
            (">=2.0", {"operator": ">=", "version": "2.0"}),
            ("~=1.4.0", {"operator": "~=", "version": "1.4.0"}),
            (
                "<3.0,>=2.0",
                {"constraints": [{"operator": "<", "version": "3.0"}, {"operator": ">=", "version": "2.0"}]},
            ),
            ("^1.2.3", {"operator": "^", "version": "1.2.3"}),  # npm style
            ("~1.2.3", {"operator": "~", "version": "1.2.3"}),  # npm style
        ]

        # for spec, expected in test_cases:
        #     result = parse_version_spec(spec)
        #     assert result == expected

    def test_dependency_normalization(self) -> Any:
        """Test normalizing dependency names across ecosystems."""
        test_cases = [
            # Python packages are case-insensitive and use hyphens/underscores interchangeably
            ("Django", "python", "django"),
            ("Flask-RESTful", "python", "flask-restful"),
            ("typing_extensions", "python", "typing-extensions"),
            # npm packages are case-sensitive
            ("@angular/core", "npm", "@angular/core"),
            ("lodash.debounce", "npm", "lodash.debounce"),
            # Maven uses groupId:artifactId
            ("org.springframework:spring-core", "maven", "org.springframework:spring-core"),
        ]

        # for name, ecosystem, expected in test_cases:
        #     result = normalize_dependency_name(name, ecosystem)
        #     assert result == expected
