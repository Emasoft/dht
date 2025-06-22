#!/usr/bin/env python3
"""
uv_manager_exceptions.py - Exception classes for UV Manager  This module contains all exception classes used by the UV Manager.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

"""
uv_manager_exceptions.py - Exception classes for UV Manager

This module contains all exception classes used by the UV Manager.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Extracted from uv_manager.py to reduce file size
# - Contains all UV-related exception classes
#


class UVError(Exception):
    """Base exception for UV-related errors."""

    pass


class UVNotFoundError(UVError):
    """UV executable not found."""

    pass


class PythonVersionError(UVError):
    """Python version-related error."""

    pass


class DependencyError(UVError):
    """Dependency resolution error."""

    pass
