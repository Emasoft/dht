#!/usr/bin/env python3
"""
project_heuristics_patterns.py - Framework detection patterns and mappings.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Extracted from project_heuristics.py to reduce file size
# - Contains framework patterns, import mappings, and config templates
# - Follows CLAUDE.md modularity guidelines
#

from typing import Any

# Framework detection patterns
FRAMEWORK_PATTERNS: dict[str, dict[str, Any]] = {
    "django": {
        "files": ["manage.py", "wsgi.py", "asgi.py", "settings.py", "urls.py", "models.py"],
        "imports": ["django", "django.conf", "django.urls", "django.db"],
        "structure_hints": ["apps/", "templates/", "static/", "media/"],
        "config_files": ["django.ini", ".django"],
    },
    "flask": {
        "files": ["app.py", "application.py", "wsgi.py"],
        "imports": ["flask", "flask.Flask", "flask_sqlalchemy", "flask_migrate"],
        "structure_hints": ["templates/", "static/"],
        "config_files": [".flaskenv"],
    },
    "fastapi": {
        "files": ["main.py", "app.py"],
        "imports": ["fastapi", "fastapi.FastAPI", "uvicorn", "pydantic"],
        "structure_hints": ["routers/", "models/", "schemas/"],
        "config_files": [],
    },
    "streamlit": {
        "files": ["app.py", "streamlit_app.py"],
        "imports": ["streamlit", "st."],
        "structure_hints": ["pages/", ".streamlit/"],
        "config_files": [".streamlit/config.toml"],
    },
    "pytest": {
        "files": ["conftest.py", "pytest.ini", "tox.ini"],
        "imports": ["pytest", "unittest", "nose"],
        "structure_hints": ["tests/", "test_*.py", "*_test.py"],
        "config_files": ["pytest.ini", ".pytest.ini", "pyproject.toml"],
    },
    "library": {
        "files": ["setup.py", "setup.cfg", "pyproject.toml"],
        "imports": ["setuptools", "distutils", "flit", "poetry", "hatchling"],
        "structure_hints": ["src/", "dist/", "build/"],
        "config_files": ["setup.cfg", "pyproject.toml", "MANIFEST.in"],
    },
    "data_science": {
        "files": ["train.py", "model.py", "analysis.ipynb"],
        "imports": ["pandas", "numpy", "sklearn", "tensorflow", "torch", "keras", "matplotlib"],
        "structure_hints": ["notebooks/", "data/", "models/", "experiments/"],
        "config_files": ["environment.yml", "conda.yml"],
    },
}

# Import to system dependency mapping
IMPORT_TO_SYSTEM_DEPS: dict[str, list[str]] = {
    # Database drivers
    "psycopg2": ["postgresql-client", "libpq-dev"],
    "psycopg": ["postgresql-client", "libpq-dev"],
    "mysqlclient": ["mysql-client", "libmysqlclient-dev"],
    "pymongo": ["mongodb-clients", "mongodb-tools"],
    "redis": ["redis-tools"],
    # Scientific computing
    "numpy": ["libopenblas-dev", "gfortran"],
    "scipy": ["liblapack-dev", "libblas-dev", "gfortran"],
    "pandas": ["libhdf5-dev"],
    "matplotlib": ["libfreetype6-dev", "libpng-dev"],
    "opencv": ["libopencv-dev", "python3-opencv"],
    "cv2": ["libopencv-dev", "python3-opencv"],
    # Machine learning
    "tensorflow": ["cuda-toolkit", "cudnn"],
    "torch": ["cuda-toolkit", "cudnn"],
    "jax": ["cuda-toolkit", "cudnn"],
    # Image processing
    "PIL": ["libjpeg-dev", "zlib1g-dev", "libtiff-dev"],
    "Pillow": ["libjpeg-dev", "zlib1g-dev", "libtiff-dev"],
    "wand": ["imagemagick", "libmagickwand-dev"],
    # Audio/Video
    "pyaudio": ["portaudio19-dev"],
    "pydub": ["ffmpeg"],
    "moviepy": ["ffmpeg", "imagemagick"],
    # Cryptography
    "cryptography": ["libssl-dev", "libffi-dev"],
    "pycrypto": ["libssl-dev"],
    # Web scraping
    "lxml": ["libxml2-dev", "libxslt-dev"],
    "beautifulsoup4": ["libxml2-dev", "libxslt-dev"],
    # Geographic
    "geopandas": ["libgdal-dev", "gdal-bin"],
    "shapely": ["libgeos-dev"],
    "fiona": ["libgdal-dev"],
    # Other
    "uwsgi": ["build-essential", "python3-dev"],
    "gunicorn": ["build-essential"],
    "ldap": ["libldap2-dev", "libsasl2-dev"],
    "python-ldap": ["libldap2-dev", "libsasl2-dev"],
}

# Configuration templates for different project types
CONFIG_TEMPLATES: dict[str, dict[str, Any]] = {
    "django": {
        "pyproject.toml": {
            "tool.django": {
                "settings_module": "project.settings",
            },
            "tool.coverage.run": {
                "source": ["."],
                "omit": ["*/migrations/*", "*/tests/*", "*/venv/*"],
            },
        },
        "setup.cfg": {
            "flake8": {
                "exclude": "migrations,__pycache__,venv",
                "max-line-length": "88",
            }
        },
        ".pre-commit-config.yaml": {
            "repos": [
                {"repo": "https://github.com/psf/black", "hooks": [{"id": "black"}]},
                {"repo": "https://github.com/pycqa/isort", "hooks": [{"id": "isort"}]},
            ]
        },
    },
    "fastapi": {
        "pyproject.toml": {
            "tool.pytest.ini_options": {
                "testpaths": ["tests"],
                "python_files": "test_*.py",
            },
            "tool.mypy": {
                "plugins": ["pydantic.mypy"],
            },
        },
        ".env.example": "DATABASE_URL=postgresql://user:pass@localhost/dbname\nSECRET_KEY=your-secret-key\n",
    },
    "data_science": {
        "pyproject.toml": {
            "tool.jupyter": {
                "kernel": "python3",
            },
            "tool.black": {
                "include": '"\\.ipynb$"',
            },
        },
        ".gitignore": "*.csv\n*.h5\n*.pkl\n*.model\ndata/\nmodels/\n",
    },
}
