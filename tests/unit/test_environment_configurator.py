#!/usr/bin/env python3
"""Tests for the environment configurator module."""

import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, mock_open
from dataclasses import asdict

from DHT.modules.environment_configurator import (
    EnvironmentConfigurator,
    EnvironmentConfig,
    ConfigurationResult
)


@pytest.fixture
def configurator():
    """Create an EnvironmentConfigurator instance."""
    return EnvironmentConfigurator()


@pytest.fixture
def sample_project_path(tmp_path):
    """Create a sample project directory."""
    project_path = tmp_path / "sample_project"
    project_path.mkdir()
    
    # Create some sample files
    (project_path / "pyproject.toml").write_text("""
[project]
name = "sample-project"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = ["requests", "click"]

[project.optional-dependencies]
dev = ["pytest", "black", "ruff"]

[tool.black]
line-length = 88

[tool.ruff]
select = ["E", "F"]
""")
    
    (project_path / "requirements.txt").write_text("requests>=2.28.0\nclick>=8.0.0")
    (project_path / ".python-version").write_text("3.11.5")
    
    return project_path


@pytest.fixture
def sample_analysis():
    """Sample analysis result."""
    return {
        "project_info": {
            "name": "sample-project",
            "project_type": "python",
            "configurations": {
                "has_pyproject": True,
                "has_git": True,
                "has_requirements": True
            },
            "dependencies": {
                "python": {
                    "runtime": ["requests", "click"],
                    "development": ["pytest", "black", "ruff"],
                    "all": ["requests", "click", "pytest", "black", "ruff"]
                }
            }
        },
        "detected_tools": ["black", "ruff", "pytest"],
        "recommended_tools": ["black", "ruff", "mypy", "pytest", "pre-commit"],
        "system_requirements": ["python-dev", "build-essential", "git", "curl"],
        "python_requirements": {
            "version": "3.11.5",
            "runtime_packages": ["pip", "setuptools", "wheel"],
            "dev_packages": ["pip", "setuptools", "wheel", "build"],
            "build_packages": ["Cython", "pybind11"]
        },
        "quality_setup": {
            "linting": ["ruff"],
            "formatting": ["black"],
            "testing": ["pytest"],
            "type_checking": ["mypy"],
            "pre_commit": True
        },
        "ci_setup": {
            "recommended": True,
            "platforms": ["github-actions"],
            "workflows": ["test", "lint", "build"],
            "matrix_testing": True
        },
        "info_tree": {"system": {"platform": "darwin"}}
    }


class TestEnvironmentConfigurator:
    """Tests for EnvironmentConfigurator class."""
    
    def test_init(self, configurator):
        """Test configurator initialization."""
        assert configurator.analyzer is not None
        assert configurator.system_package_mappings is not None
        assert configurator.tool_configs is not None
        assert "pytest" in configurator.tool_configs
        assert "black" in configurator.tool_configs
    
    @patch('DHT.modules.environment_configurator.build_system_report')
    def test_analyze_environment_requirements(
        self, 
        mock_build_system_report, 
        configurator, 
        sample_project_path
    ):
        """Test environment requirements analysis."""
        # Mock the info tree
        mock_info_tree = {"system": {"platform": "darwin"}}
        mock_build_system_report.return_value = mock_info_tree
        
        # Mock project analyzer
        with patch.object(configurator.analyzer, 'analyze_project') as mock_analyze:
            mock_analyze.return_value = {
                "name": "test-project",
                "project_type": "python",
                "configurations": {"has_pyproject": True}
            }
            
            result = configurator.analyze_environment_requirements(
                project_path=sample_project_path,
                include_system_info=True
            )
            
            assert "project_info" in result
            assert "detected_tools" in result
            assert "recommended_tools" in result
            assert "system_requirements" in result
            assert "python_requirements" in result
            assert "quality_setup" in result
            assert "ci_setup" in result
            assert result["info_tree"] == mock_info_tree
            
            mock_build_system_report.assert_called_once()
    
    def test_detect_tools_from_project(self, configurator, sample_project_path):
        """Test tool detection from project files."""
        project_info = {
            "project_type": "python",
            "configurations": {"has_pyproject": True}
        }
        
        detected = configurator._detect_tools_from_project(
            sample_project_path, 
            project_info
        )
        
        # Should detect tools from pyproject.toml
        assert "black" in detected
        assert "ruff" in detected
    
    def test_recommend_tools_python(self, configurator):
        """Test tool recommendations for Python projects."""
        project_info = {
            "project_type": "python",
            "configurations": {"has_pyproject": True}
        }
        
        recommended = configurator._recommend_tools(project_info)
        
        assert "black" in recommended
        assert "ruff" in recommended
        assert "mypy" in recommended
        assert "pytest" in recommended
        assert "pre-commit" in recommended
    
    def test_recommend_tools_nodejs(self, configurator):
        """Test tool recommendations for Node.js projects."""
        project_info = {
            "project_type": "nodejs",
            "configurations": {}
        }
        
        recommended = configurator._recommend_tools(project_info)
        
        assert "eslint" in recommended
        assert "prettier" in recommended
        assert "jest" in recommended
    
    def test_determine_system_requirements(self, configurator):
        """Test system requirements determination."""
        project_info = {
            "project_type": "python",
            "configurations": {
                "has_git": True,
                "has_dockerfile": True
            }
        }
        
        requirements = configurator._determine_system_requirements(project_info)
        
        assert "python-dev" in requirements
        assert "build-essential" in requirements
        assert "git" in requirements
        assert "docker" in requirements
        assert "curl" in requirements
        assert "openssl" in requirements
    
    def test_determine_python_requirements(self, configurator, sample_project_path):
        """Test Python requirements determination."""
        project_info = {"project_type": "python"}
        
        requirements = configurator._determine_python_requirements(
            sample_project_path,
            project_info
        )
        
        assert requirements["version"] == "3.11.5"  # From .python-version
        assert "pip" in requirements["dev_packages"]
        assert "setuptools" in requirements["dev_packages"]
        assert "wheel" in requirements["dev_packages"]
        assert "build" in requirements["dev_packages"]
    
    def test_recommend_quality_tools_python(self, configurator):
        """Test quality tools recommendation for Python."""
        project_info = {"project_type": "python"}
        
        quality = configurator._recommend_quality_tools(project_info)
        
        assert "ruff" in quality["linting"]
        assert "black" in quality["formatting"]
        assert "pytest" in quality["testing"]
        assert "mypy" in quality["type_checking"]
        assert quality["pre_commit"] is True
    
    def test_recommend_ci_setup(self, configurator):
        """Test CI setup recommendations."""
        project_info = {
            "project_type": "python",  # Add project type
            "configurations": {"has_git": True},
            "dependencies": {
                "python": {
                    "all": ["package1", "package2", "package3", "package4"]
                }
            }
        }
        
        ci_config = configurator._recommend_ci_setup(project_info)
        
        assert ci_config["recommended"] is True
        assert "github-actions" in ci_config["platforms"]
        assert "test" in ci_config["workflows"]
    
    def test_generate_environment_config(self, configurator, sample_project_path, sample_analysis):
        """Test environment configuration generation."""
        config = configurator.generate_environment_config(
            project_path=sample_project_path,
            analysis=sample_analysis
        )
        
        assert isinstance(config, EnvironmentConfig)
        assert config.project_path == sample_project_path
        assert config.project_type == "python"
        assert config.python_version == "3.11.5"
        assert len(config.system_packages) > 0
        assert len(config.quality_tools) > 0
        assert "PYTHONDONTWRITEBYTECODE" in config.environment_variables
    
    def test_resolve_system_packages_darwin(self, configurator):
        """Test system package resolution for macOS."""
        requirements = ["python-dev", "build-essential", "git"]
        
        with patch('platform.system', return_value='Darwin'):
            resolved = configurator._resolve_system_packages(requirements)
            
            # On macOS, python-dev and build-essential map to empty lists
            assert "git" in resolved
            # Should not contain python-dev or build-essential packages
            assert not any("python3-dev" in pkg for pkg in resolved)
    
    def test_resolve_system_packages_linux(self, configurator):
        """Test system package resolution for Linux."""
        requirements = ["python-dev", "build-essential", "git"]
        
        with patch('platform.system', return_value='Linux'):
            resolved = configurator._resolve_system_packages(requirements)
            
            assert "python3-dev" in resolved
            assert "build-essential" in resolved
            assert "git" in resolved
    
    def test_generate_container_config(self, configurator):
        """Test container configuration generation."""
        config = EnvironmentConfig(
            project_path=Path("/test"),
            project_type="python",
            python_version="3.11",
            system_packages=["git", "curl"],
            environment_variables={"ENV_VAR": "value"}
        )
        
        container_config = configurator._generate_container_config(config)
        
        assert container_config["base_image"] == "python:3.11-slim"
        assert container_config["python_version"] == "3.11"
        assert container_config["working_dir"] == "/app"
        assert 8000 in container_config["exposed_ports"]
        assert container_config["environment"]["ENV_VAR"] == "value"
    
    def test_generate_ci_config(self, configurator):
        """Test CI configuration generation."""
        config = EnvironmentConfig(
            project_path=Path("/test"),
            project_type="python",
            python_version="3.11"
        )
        
        ci_setup = {
            "platforms": ["github-actions"],
            "workflows": ["test", "lint", "build"],
            "matrix_testing": True
        }
        
        ci_config = configurator._generate_ci_config(config, ci_setup)
        
        assert "github-actions" in ci_config["platforms"]
        assert "test" in ci_config["workflows"]
        assert ci_config["matrix_testing"] is True
        assert "3.11" in ci_config["python_versions"]
        assert "checkout" in ci_config["steps"]
        assert "run-tests" in ci_config["steps"]
    
    def test_apply_custom_requirements(self, configurator):
        """Test applying custom requirements."""
        config = EnvironmentConfig(
            project_path=Path("/test"),
            project_type="python",
            python_version="3.10",
            python_packages=["requests"],
            environment_variables={"VAR1": "value1"}
        )
        
        custom = {
            "python_version": "3.12",
            "python_packages": ["flask"],
            "dev_packages": ["pytest"],
            "environment_variables": {"VAR2": "value2"}
        }
        
        updated_config = configurator._apply_custom_requirements(config, custom)
        
        assert updated_config.python_version == "3.12"
        assert "flask" in updated_config.python_packages
        assert "pytest" in updated_config.dev_packages
        assert updated_config.environment_variables["VAR1"] == "value1"
        assert updated_config.environment_variables["VAR2"] == "value2"
    
    @patch('DHT.modules.environment_configurator.check_uv_available')
    @patch('DHT.modules.environment_configurator.ensure_python_version')
    @patch('DHT.modules.environment_configurator.create_virtual_environment')
    @patch('DHT.modules.environment_configurator.install_dependencies')
    def test_install_python_environment_success(
        self,
        mock_install_deps,
        mock_create_venv,
        mock_ensure_python,
        mock_check_uv,
        configurator
    ):
        """Test successful Python environment installation."""
        # Setup mocks
        mock_check_uv.return_value = {"available": True}
        mock_ensure_python.return_value = Path("/usr/bin/python3.11")
        mock_create_venv.return_value = Path("/project/.venv")
        mock_install_deps.return_value = {"success": True, "message": "Success"}
        
        config = EnvironmentConfig(
            project_path=Path("/project"),
            project_type="python",
            python_version="3.11",
            dev_packages=["pytest", "black"]
        )
        
        result = ConfigurationResult(
            success=False,
            config=config
        )
        
        success = configurator._install_python_environment(config, result)
        
        assert success is True
        mock_check_uv.assert_called_once()
        mock_ensure_python.assert_called_once_with("3.11")
        mock_create_venv.assert_called_once()
        mock_install_deps.assert_called_once()
    
    @patch('DHT.modules.environment_configurator.check_uv_available')
    def test_install_python_environment_no_uv(self, mock_check_uv, configurator):
        """Test Python environment installation when UV is not available."""
        mock_check_uv.return_value = {"available": False}
        
        config = EnvironmentConfig(
            project_path=Path("/project"),
            project_type="python"
        )
        
        result = ConfigurationResult(success=False, config=config)
        
        with patch.object(configurator, '_install_with_pip', return_value=True) as mock_pip:
            success = configurator._install_python_environment(config, result)
            
            assert success is True
            mock_pip.assert_called_once_with(config, result)
            assert "UV not available, using system pip" in result.warnings
    
    @patch('subprocess.run')
    @patch('sys.executable', '/usr/bin/python3')
    def test_install_with_pip(self, mock_subprocess, configurator):
        """Test fallback pip installation."""
        mock_subprocess.return_value = None  # Successful execution
        
        config = EnvironmentConfig(
            project_path=Path("/tmp/project"),
            project_type="python",
            python_packages=["requests"],
            dev_packages=["pytest"]
        )
        
        result = ConfigurationResult(success=False, config=config)
        
        success = configurator._install_with_pip(config, result)
        
        assert success is True
        # Should call venv creation and pip install
        assert mock_subprocess.call_count >= 2
    
    def test_generate_ruff_config(self, configurator, tmp_path):
        """Test ruff configuration generation."""
        configurator._generate_ruff_config(tmp_path)
        
        ruff_config = tmp_path / "ruff.toml"
        assert ruff_config.exists()
        
        content = ruff_config.read_text()
        assert "target-version" in content
        assert "line-length = 88" in content
        assert '"E"' in content  # pycodestyle errors
    
    def test_generate_black_config(self, configurator, tmp_path):
        """Test black configuration generation."""
        configurator._generate_black_config(tmp_path)
        
        pyproject = tmp_path / "pyproject.toml"
        assert pyproject.exists()
        
        # Should be able to parse the generated TOML
        try:
            import tomllib
        except ImportError:
            import tomli as tomllib
        
        with open(pyproject, "rb") as f:
            data = tomllib.load(f)
        
        assert "tool" in data
        assert "black" in data["tool"]
        assert data["tool"]["black"]["line-length"] == 88
    
    def test_generate_mypy_config(self, configurator, tmp_path):
        """Test mypy configuration generation."""
        configurator._generate_mypy_config(tmp_path)
        
        mypy_config = tmp_path / "mypy.ini"
        assert mypy_config.exists()
        
        content = mypy_config.read_text()
        assert "[mypy]" in content
        assert "python_version = 3.11" in content
        assert "disallow_untyped_defs = True" in content
    
    def test_generate_pytest_config(self, configurator, tmp_path):
        """Test pytest configuration generation."""
        configurator._generate_pytest_config(tmp_path)
        
        pytest_config = tmp_path / "pytest.ini"
        assert pytest_config.exists()
        
        content = pytest_config.read_text()
        assert "[tool:pytest]" in content
        assert "testpaths = tests" in content
        assert "python_files = test_*.py" in content
    
    def test_generate_precommit_config(self, configurator, tmp_path):
        """Test pre-commit configuration generation."""
        quality_tools = ["black", "ruff", "mypy"]
        
        configurator._generate_precommit_config(tmp_path, quality_tools)
        
        precommit_config = tmp_path / ".pre-commit-config.yaml"
        assert precommit_config.exists()
        
        import yaml
        with open(precommit_config) as f:
            data = yaml.safe_load(f)
        
        assert "repos" in data
        repo_names = [repo["repo"] for repo in data["repos"]]
        assert any("black" in repo for repo in repo_names)
        assert any("ruff" in repo for repo in repo_names)
        assert any("mypy" in repo for repo in repo_names)
    
    def test_generate_gitignore(self, configurator, tmp_path):
        """Test .gitignore generation."""
        configurator._generate_gitignore(tmp_path, "python")
        
        gitignore = tmp_path / ".gitignore"
        assert gitignore.exists()
        
        content = gitignore.read_text()
        assert "__pycache__/" in content
        assert "*.pyc" in content
        assert ".venv" in content
        assert ".pytest_cache/" in content
    
    def test_generate_dockerfile(self, configurator, tmp_path):
        """Test Dockerfile generation."""
        config = EnvironmentConfig(
            project_path=tmp_path,
            project_type="python",
            container_config={
                "base_image": "python:3.11-slim",
                "system_packages": ["git", "curl"],
                "working_dir": "/app",
                "exposed_ports": [8000, 5000],
                "environment": {"DEBUG": "1"}
            }
        )
        
        configurator._generate_dockerfile(config)
        
        dockerfile = tmp_path / "Dockerfile"
        assert dockerfile.exists()
        
        content = dockerfile.read_text()
        assert "FROM python:3.11-slim" in content
        assert "WORKDIR /app" in content
        assert "EXPOSE 8000" in content
        assert "EXPOSE 5000" in content
        assert "git curl" in content
    
    def test_generate_github_workflow(self, configurator, tmp_path):
        """Test GitHub Actions workflow generation."""
        config = EnvironmentConfig(
            project_path=tmp_path,
            project_type="python",
            ci_config={
                "os_matrix": ["ubuntu-latest", "macos-latest"],
                "python_versions": ["3.10", "3.11"],
                "workflows": ["test", "lint"]
            }
        )
        
        configurator._generate_github_workflow(config)
        
        workflow_file = tmp_path / ".github" / "workflows" / "ci.yml"
        assert workflow_file.exists()
        
        import yaml
        with open(workflow_file) as f:
            data = yaml.safe_load(f)
        
        assert data["name"] == "CI"
        assert "test" in data["jobs"]
        assert data["jobs"]["test"]["strategy"]["matrix"]["os"] == ["ubuntu-latest", "macos-latest"]
        assert data["jobs"]["test"]["strategy"]["matrix"]["python-version"] == ["3.10", "3.11"]
        
        # Check for test and lint steps
        step_names = [step.get("name", "") for step in data["jobs"]["test"]["steps"]]
        assert any("test" in name.lower() for name in step_names)
        assert any("lint" in name.lower() for name in step_names)
    
    def test_generate_env_file(self, configurator, tmp_path):
        """Test .env.example file generation."""
        config = EnvironmentConfig(
            project_path=tmp_path,
            project_type="python",
            environment_variables={
                "DEBUG": "1",
                "DATABASE_URL": "sqlite:///db.sqlite3"
            }
        )
        
        configurator._generate_env_file(config)
        
        env_file = tmp_path / ".env.example"
        assert env_file.exists()
        
        content = env_file.read_text()
        assert "DEBUG=1" in content
        assert "DATABASE_URL=sqlite:///db.sqlite3" in content
        assert "# Environment Variables" in content


class TestEnvironmentConfig:
    """Tests for EnvironmentConfig dataclass."""
    
    def test_environment_config_creation(self):
        """Test creating EnvironmentConfig."""
        config = EnvironmentConfig(
            project_path=Path("/test"),
            project_type="python",
            python_version="3.11"
        )
        
        assert config.project_path == Path("/test")
        assert config.project_type == "python"
        assert config.python_version == "3.11"
        assert config.system_packages == []  # Default empty list
        assert config.environment_variables == {}  # Default empty dict
    
    def test_environment_config_with_all_fields(self):
        """Test creating EnvironmentConfig with all fields."""
        config = EnvironmentConfig(
            project_path=Path("/test"),
            project_type="python",
            python_version="3.11",
            system_packages=["git", "curl"],
            python_packages=["requests"],
            dev_packages=["pytest"],
            environment_variables={"DEBUG": "1"},
            quality_tools=["black", "ruff"],
            test_frameworks=["pytest"],
            build_tools=["setuptools", "wheel"],
            container_config={"base_image": "python:3.11"},
            ci_config={"platforms": ["github-actions"]}
        )
        
        assert len(config.system_packages) == 2
        assert len(config.python_packages) == 1
        assert len(config.dev_packages) == 1
        assert config.environment_variables["DEBUG"] == "1"
        assert len(config.quality_tools) == 2
        assert config.container_config["base_image"] == "python:3.11"


class TestConfigurationResult:
    """Tests for ConfigurationResult dataclass."""
    
    def test_configuration_result_creation(self):
        """Test creating ConfigurationResult."""
        config = EnvironmentConfig(
            project_path=Path("/test"),
            project_type="python"
        )
        
        result = ConfigurationResult(
            success=True,
            config=config
        )
        
        assert result.success is True
        assert result.config == config
        assert result.steps_completed == []  # Default empty list
        assert result.execution_time == 0.0  # Default value
    
    def test_configuration_result_with_details(self):
        """Test creating ConfigurationResult with all details."""
        config = EnvironmentConfig(
            project_path=Path("/test"),
            project_type="python"
        )
        
        result = ConfigurationResult(
            success=False,
            config=config,
            steps_completed=["analyze", "configure"],
            steps_failed=["install"],
            warnings=["UV not available"],
            execution_time=10.5
        )
        
        assert result.success is False
        assert len(result.steps_completed) == 2
        assert len(result.steps_failed) == 1
        assert len(result.warnings) == 1
        assert result.execution_time == 10.5


class TestIntegration:
    """Integration tests for environment configurator."""
    
    @patch('DHT.modules.environment_configurator.build_system_report')
    @patch('DHT.modules.environment_configurator.check_uv_available')
    @patch('DHT.modules.environment_configurator.create_markdown_artifact')
    def test_configure_development_environment_flow(
        self,
        mock_create_artifact,
        mock_check_uv,
        mock_build_system_report,
        sample_project_path
    ):
        """Test the complete environment configuration flow."""
        # Setup mocks
        mock_build_info_tree.return_value = {"system": {"platform": "darwin"}}
        mock_check_uv.return_value = {"available": False}  # Force pip fallback
        
        configurator = EnvironmentConfigurator()
        
        # Mock the install methods to avoid actual installation
        with patch.object(configurator, '_install_with_pip', return_value=True), \
             patch.object(configurator, '_configure_quality_tools', return_value=True), \
             patch.object(configurator, '_generate_config_files', return_value=True):
            
            result = configurator.configure_development_environment(
                project_path=sample_project_path,
                auto_install=True,
                include_system_info=True,
                create_artifacts=True
            )
            
            assert isinstance(result, ConfigurationResult)
            assert result.success is True
            assert len(result.steps_completed) > 0
            assert result.config.project_type == "python"
            assert result.config.python_version == "3.11.5"  # From .python-version
            
            # Verify artifacts were created
            mock_create_artifact.assert_called()
    
    def test_end_to_end_config_generation(self, sample_project_path):
        """Test end-to-end configuration generation without external dependencies."""
        configurator = EnvironmentConfigurator()
        
        # Mock external dependencies
        with patch('DHT.modules.environment_configurator.build_system_report') as mock_system_report:
            mock_system_report.return_value = {"system": {"platform": "darwin"}}
            
            # Analyze requirements
            analysis = configurator.analyze_environment_requirements(
                project_path=sample_project_path,
                include_system_info=False
            )
            
            # Generate configuration
            config = configurator.generate_environment_config(
                project_path=sample_project_path,
                analysis=analysis
            )
            
            # Verify configuration
            assert config.project_type == "python"
            assert config.python_version == "3.11.5"
            assert len(config.system_packages) > 0
            assert "PYTHONDONTWRITEBYTECODE" in config.environment_variables
            
            # Verify detected tools are included
            assert any(tool in ["black", "ruff"] for tool in config.quality_tools)