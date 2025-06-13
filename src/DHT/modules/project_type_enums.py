#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
project_type_enums.py - Project type and category enumerations

This module contains the enumerations for project types and categories
used throughout the DHT project type detection system.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Extracted from project_type_detector.py to reduce file size
# - Contains ProjectType and ProjectCategory enums
# - Added helper methods for category classification
#

from enum import Enum, auto


class ProjectType(Enum):
    """Enumeration of supported project types."""
    GENERIC = "generic"
    DJANGO = "django"
    DJANGO_REST = "django_rest_framework"
    FLASK = "flask"
    FASTAPI = "fastapi"
    STREAMLIT = "streamlit"
    GRADIO = "gradio"
    DATA_SCIENCE = "data_science"
    MACHINE_LEARNING = "machine_learning"
    LIBRARY = "library"
    CLI = "cli"
    REACT = "react"
    VUE = "vue"
    HYBRID = "hybrid"


class ProjectCategory(Enum):
    """High-level project categories."""
    UNKNOWN = "unknown"
    WEB_FRAMEWORK = "web_framework"
    WEB_API = "web_api"
    MACHINE_LEARNING = "machine_learning"
    DATA_ANALYSIS = "data_analysis"
    COMMAND_LINE = "command_line"
    PACKAGE = "package"
    FULL_STACK = "full_stack"
    
    def is_web_related(self) -> bool:
        """Check if category is web-related."""
        return self in {
            self.WEB_FRAMEWORK, 
            self.WEB_API, 
            self.FULL_STACK
        }
    
    def is_data_related(self) -> bool:
        """Check if category is data-related."""
        return self in {
            self.MACHINE_LEARNING,
            self.DATA_ANALYSIS
        }
    
    def requires_database(self) -> bool:
        """Check if category typically requires a database."""
        return self in {
            self.WEB_FRAMEWORK,
            self.WEB_API,
            self.FULL_STACK
        }
    
    def requires_gpu_support(self) -> bool:
        """Check if category might need GPU support."""
        return self == self.MACHINE_LEARNING