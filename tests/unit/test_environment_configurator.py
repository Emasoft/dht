#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test suite for environment configurator.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Initial test suite for environment configurator
# - Tests for refactored modules
#

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from DHT.modules.environment_configurator import EnvironmentConfigurator
from DHT.modules.environment_config_models import EnvironmentConfig, ConfigurationResult
from DHT.modules.environment_analyzer import EnvironmentAnalyzer
from DHT.modules.environment_installer import EnvironmentInstaller


class TestEnvironmentConfigurator:
    """Test the environment configurator."""
    
    @pytest.fixture
    def configurator(self):
        """Create a configurator instance."""
        return EnvironmentConfigurator()
    
    @pytest.fixture
    def sample_project(self, tmp_path):
        """Create a sample Python project."""
        project_dir = tmp_path / "sample_project"
        project_dir.mkdir()
        
        # Create basic Python project structure
        (project_dir / "main.py").write_text("""
import click

@click.command()
def main():
    print("Hello World")

if __name__ == "__main__":
    main()
""")
        
        (project_dir / "requirements.txt").write_text("click>=8.0\n")
        
        (project_dir / "pyproject.toml").write_text("""
[project]
name = "sample-project"
version = "0.1.0"
dependencies = ["click>=8.0"]
requires-python = ">=3.11"

[tool.black]
line-length = 88
""")
        
        return project_dir
    
    def test_configurator_initialization(self, configurator):
        """Test configurator initializes with required components."""
        assert configurator.analyzer is not None
        assert configurator.env_analyzer is not None
        assert configurator.installer is not None
        assert isinstance(configurator.env_analyzer, EnvironmentAnalyzer)
        assert isinstance(configurator.installer, EnvironmentInstaller)
    
    @patch('DHT.modules.environment_analyzer.build_system_report')
    def test_analyze_environment_requirements(self, mock_system_report, configurator, sample_project):
        """Test environment requirements analysis."""
        mock_system_report.return_value = {
            "system": {"platform": "darwin"},
            "tools": {}
        }
        
        analysis = configurator.analyze_environment_requirements(sample_project)
        
        assert "project_info" in analysis
        assert "detected_tools" in analysis
        assert "recommended_tools" in analysis
        assert "python_requirements" in analysis
    
    def test_generate_environment_config(self, configurator, sample_project):
        """Test environment configuration generation."""
        # Create analysis result
        analysis = {
            "project_info": {"project_type": "python"},
            "existing_tools": ["black"],
            "recommended_tools": ["ruff", "mypy", "pytest"],
            "python_requirements": {
                "version": "3.11",
                "dev_packages": ["pip", "setuptools", "wheel"]
            },
            "quality_setup": {
                "linting": ["ruff"],
                "formatting": ["black"],
                "testing": ["pytest"],
                "type_checking": ["mypy"]
            }
        }
        
        # Custom requirements
        custom_reqs = {
            "quality_tools": ["black", "ruff", "mypy"]
        }
        
        config = configurator.generate_environment_config(
            sample_project,
            analysis,
            custom_reqs
        )
        
        assert isinstance(config, EnvironmentConfig)
        assert config.project_type == "python"
        assert config.python_version == "3.11"
        assert "black" in config.quality_tools
        assert "ruff" in config.quality_tools
    
    @patch('DHT.modules.environment_installer.check_uv_available')
    @patch('DHT.modules.environment_installer.create_virtual_environment')
    @patch('DHT.modules.environment_installer.install_dependencies')
    def test_configure_development_environment(
        self, 
        mock_install_deps,
        mock_create_venv,
        mock_check_uv,
        configurator,
        sample_project
    ):
        """Test full environment configuration flow."""
        # Mock UV availability
        mock_check_uv.return_value = {"available": True}
        mock_create_venv.return_value = sample_project / ".venv"
        mock_install_deps.return_value = {"success": True}
        
        # Mock analysis
        with patch.object(configurator, 'analyze_environment_requirements') as mock_analyze:
            mock_analyze.return_value = {
                "project_info": {"project_type": "python"},
                "existing_tools": [],
                "recommended_tools": ["black", "ruff"],
                "python_requirements": {"version": "3.11"}
            }
            
            result = configurator.configure_development_environment(sample_project)
            
            assert isinstance(result, ConfigurationResult)
            assert result.success
            assert "create_virtual_environment" in result.steps_completed
    
    def test_environment_analyzer_integration(self, configurator, sample_project):
        """Test that environment analyzer is properly integrated."""
        # The analyzer methods should be delegated to
        with patch.object(configurator.env_analyzer, '_detect_tools_from_project') as mock_detect:
            with patch.object(configurator.env_analyzer, '_recommend_tools') as mock_recommend:
                mock_detect.return_value = ["black", "pytest"]
                mock_recommend.return_value = ["ruff", "mypy"]
                
                with patch('DHT.modules.environment_configurator.build_system_report') as mock_report:
                    mock_report.return_value = {"system": {"platform": "darwin"}}
                    
                    result = configurator.analyze_environment_requirements(sample_project)
                    
                    # Check that analyzer methods were called
                    mock_detect.assert_called_once()
                    mock_recommend.assert_called_once()
                    
                    # Check result structure
                    assert "detected_tools" in result
                    assert result["detected_tools"] == ["black", "pytest"]
                    assert "recommended_tools" in result
                    assert result["recommended_tools"] == ["ruff", "mypy"]
    
    def test_config_file_generation(self, configurator, sample_project):
        """Test configuration file generation."""
        config = EnvironmentConfig(
            project_path=sample_project,
            project_type="python",
            quality_tools=["black", "ruff", "mypy"],
            test_frameworks=["pytest"],
            build_tools=["build", "wheel"],
            environment_variables={"TEST": "value"}
        )
        
        result = ConfigurationResult(
            success=True,
            config=config
        )
        
        # Test that config files would be generated
        with patch('DHT.modules.environment_configurator.generate_gitignore') as mock_gitignore:
            with patch('DHT.modules.environment_configurator.generate_env_file') as mock_env:
                with patch('DHT.modules.environment_configurator.generate_makefile') as mock_make:
                    success = configurator._generate_config_files(config, result)
                    
                    assert success
                    # Check that generator functions were called
                    mock_gitignore.assert_called_once_with(sample_project, "python")
                    mock_env.assert_called_once_with(config)
                    mock_make.assert_called_once_with(config)


class TestEnvironmentAnalyzer:
    """Test the environment analyzer module."""
    
    @pytest.fixture
    def analyzer(self):
        """Create an analyzer instance."""
        return EnvironmentAnalyzer()
    
    def test_analyze_environment_requirements(self, analyzer, tmp_path):
        """Test basic environment analysis."""
        project_dir = tmp_path / "test_project"
        project_dir.mkdir()
        
        (project_dir / "requirements.txt").write_text("django>=4.0\n")
        
        with patch('DHT.modules.environment_analyzer.build_system_report') as mock_report:
            mock_report.return_value = {"system": {"platform": "linux"}}
            
            analysis = analyzer.analyze_environment_requirements(project_dir)
            
            assert "project_info" in analysis
            assert "system_requirements" in analysis
            assert "python_requirements" in analysis
    
    def test_detect_tools_from_project(self, analyzer, tmp_path):
        """Test tool detection from project files."""
        project_dir = tmp_path / "test_project"
        project_dir.mkdir()
        
        # Create pyproject.toml with tool configs
        (project_dir / "pyproject.toml").write_text("""
[tool.black]
line-length = 88

[tool.ruff]
target-version = "py311"

[project]
dependencies = ["pytest>=7.0"]
""")
        
        project_info = {}
        detected = analyzer._detect_tools_from_project(project_dir, project_info)
        
        assert "black" in detected
        assert "ruff" in detected
        assert "pytest" in detected


class TestEnvironmentInstaller:
    """Test the environment installer module."""
    
    @pytest.fixture
    def installer(self):
        """Create an installer instance."""
        return EnvironmentInstaller()
    
    @patch('DHT.modules.environment_installer.check_uv_available')
    @patch('DHT.modules.environment_installer.create_virtual_environment')
    def test_install_python_environment_with_uv(
        self,
        mock_create_venv,
        mock_check_uv,
        installer,
        tmp_path
    ):
        """Test Python environment installation with UV."""
        mock_check_uv.return_value = {"available": True}
        mock_create_venv.return_value = tmp_path / ".venv"
        
        config = EnvironmentConfig(
            project_path=tmp_path,
            project_type="python",
            python_version="3.11"
        )
        result = ConfigurationResult(success=True, config=config)
        
        with patch('DHT.modules.environment_installer.install_dependencies') as mock_install:
            mock_install.return_value = {"success": True}
            
            success = installer.install_python_environment(config, result)
            
            assert success
            assert "create_virtual_environment" in result.steps_completed
    
    def test_install_with_pip_fallback(self, installer, tmp_path):
        """Test fallback to pip when UV is not available."""
        config = EnvironmentConfig(
            project_path=tmp_path,
            project_type="python",
            python_packages=["click", "requests"]
        )
        result = ConfigurationResult(success=True, config=config)
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            
            success = installer._install_with_pip(config, result)
            
            assert success
            assert "create_virtual_environment_pip" in result.steps_completed