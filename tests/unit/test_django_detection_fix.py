#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test to verify Django project detection is working correctly after the fix.
"""

import pytest
from pathlib import Path
import tempfile

from DHT.modules.project_analyzer import ProjectAnalyzer
from DHT.modules.project_heuristics import ProjectHeuristics
from DHT.modules.project_type_detector import ProjectTypeDetector, ProjectType


class TestDjangoDetectionFix:
    """Test Django project detection after analyzer enhancement."""
    
    @pytest.fixture
    def django_project(self):
        """Create a minimal Django project structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            proj_dir = Path(tmpdir) / 'django_test'
            proj_dir.mkdir()
            
            # Create manage.py
            (proj_dir / 'manage.py').write_text('''#!/usr/bin/env python
import os
import sys
from django.core.management import execute_from_command_line

if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
    execute_from_command_line(sys.argv)
''')
            
            # Create project directory
            app_dir = proj_dir / 'myproject'
            app_dir.mkdir()
            (app_dir / '__init__.py').write_text('')
            
            # Create settings.py
            (app_dir / 'settings.py').write_text('''
from django.conf import settings
import os

DEBUG = True
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
]
''')
            
            # Create urls.py
            (app_dir / 'urls.py').write_text('''
from django.urls import path
from django.contrib import admin

urlpatterns = [
    path('admin/', admin.site.urls),
]
''')
            
            # Create wsgi.py
            (app_dir / 'wsgi.py').write_text('''
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
application = get_wsgi_application()
''')
            
            # Create an app
            app_subdir = proj_dir / 'myapp'
            app_subdir.mkdir()
            (app_subdir / '__init__.py').write_text('')
            
            # Create models.py
            (app_subdir / 'models.py').write_text('''
from django.db import models

class MyModel(models.Model):
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
''')
            
            # Create views.py
            (app_subdir / 'views.py').write_text('''
from django.shortcuts import render
from django.http import HttpResponse

def index(request):
    return HttpResponse("Hello, Django!")
''')
            
            # Create requirements.txt
            (proj_dir / 'requirements.txt').write_text('''Django==4.2.0
celery==5.3.0
redis==4.5.0
psycopg2-binary==2.9.6
''')
            
            yield proj_dir
    
    def test_project_analyzer_detects_django_files(self, django_project):
        """Test that ProjectAnalyzer properly analyzes Django files."""
        analyzer = ProjectAnalyzer()
        result = analyzer.analyze_project(django_project)
        
        # Check that Python files were analyzed
        assert 'file_analysis' in result
        assert len(result['file_analysis']) > 0
        
        # Check that manage.py was found and marked as entry point
        assert 'structure' in result
        assert 'entry_points' in result['structure']
        assert 'manage.py' in result['structure']['entry_points']
        
        # Check that Django was detected in frameworks
        assert 'frameworks' in result
        assert 'django' in result['frameworks']
        
        # Check that Django files were analyzed
        file_names = list(result['file_analysis'].keys())
        assert 'manage.py' in file_names
        assert any('settings.py' in f for f in file_names)
        assert any('models.py' in f for f in file_names)
        
        # Check that imports were extracted
        manage_py_analysis = result['file_analysis']['manage.py']
        assert 'imports' in manage_py_analysis
        imports = [imp['module'] for imp in manage_py_analysis['imports']]
        assert 'django.core.management' in imports
    
    def test_project_heuristics_detects_django(self, django_project):
        """Test that ProjectHeuristics correctly identifies Django project."""
        analyzer = ProjectAnalyzer()
        analysis_result = analyzer.analyze_project(django_project)
        
        heuristics = ProjectHeuristics()
        heuristic_result = heuristics.detect_project_type(analysis_result)
        
        # Check primary type
        assert heuristic_result['primary_type'] == 'django'
        
        # Check confidence is high
        assert heuristic_result['confidence'] >= 0.9
        
        # Check that Django framework was detected with good score
        assert 'frameworks' in heuristic_result
        assert 'django' in heuristic_result['frameworks']
        django_info = heuristic_result['frameworks']['django']
        assert django_info['score'] >= 20  # Should have high score
        assert django_info['confidence'] >= 0.9
        
        # Check matches include both files and imports
        matches = django_info['matches']
        file_matches = [m for m in matches if m.startswith('file:')]
        import_matches = [m for m in matches if m.startswith('import:')]
        
        assert len(file_matches) > 0  # Should find Django files
        assert len(import_matches) > 0  # Should find Django imports
        assert 'file:manage.py' in matches
        assert 'import:django' in matches
    
    def test_project_type_detector_full_flow(self, django_project):
        """Test the complete project type detection flow."""
        detector = ProjectTypeDetector()
        analysis = detector.analyze(django_project)
        
        # Check detected type
        assert analysis.type == ProjectType.DJANGO
        
        # Check confidence
        assert analysis.confidence >= 0.9
        
        # Check markers
        assert len(analysis.markers) > 0
        assert any('manage.py' in marker for marker in analysis.markers)
        
        # Check primary dependencies
        assert 'Django' in analysis.primary_dependencies
        
        # Verify it's not detected as GENERIC
        assert analysis.type != ProjectType.GENERIC
    
    def test_django_rest_framework_detection(self, django_project):
        """Test detection of Django REST Framework projects."""
        # Add DRF to requirements
        req_file = django_project / 'requirements.txt'
        content = req_file.read_text()
        req_file.write_text(content + '\ndjangorestframework==3.14.0\n')
        
        # Add a serializer file
        app_dir = django_project / 'myapp'
        (app_dir / 'serializers.py').write_text('''
from rest_framework import serializers
from .models import MyModel

class MyModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = MyModel
        fields = '__all__'
''')
        
        # Add API views
        (app_dir / 'api_views.py').write_text('''
from rest_framework import viewsets
from .models import MyModel
from .serializers import MyModelSerializer

class MyModelViewSet(viewsets.ModelViewSet):
    queryset = MyModel.objects.all()
    serializer_class = MyModelSerializer
''')
        
        detector = ProjectTypeDetector()
        analysis = detector.analyze(django_project)
        
        # Should detect as Django REST
        assert analysis.type == ProjectType.DJANGO_REST
        assert analysis.confidence >= 0.9
        assert 'djangorestframework' in analysis.primary_dependencies