#!/usr/bin/env python3
"""
project_heuristics_deps.py - System dependency inference from Python imports.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Extracted from project_heuristics.py to reduce file size
# - Contains system dependency inference logic
# - Follows CLAUDE.md modularity guidelines
#

import logging
from typing import Any

from prefect import task

from .project_heuristics_patterns import IMPORT_TO_SYSTEM_DEPS


class DependencyInferrer:
    """Handles system dependency inference from Python imports."""

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

    @task
    def infer_system_dependencies(self, analysis_result: dict[str, Any]) -> dict[str, Any]:
        """
        Infer system dependencies based on Python imports.

        Args:
            analysis_result: Output from ProjectAnalyzer

        Returns:
            Dictionary mapping dependency names to system packages
        """
        imports = self._extract_all_imports(analysis_result)
        system_deps: dict[str, list[str]] = {}

        for import_name in imports:
            # Check direct mapping
            if import_name in IMPORT_TO_SYSTEM_DEPS:
                deps = IMPORT_TO_SYSTEM_DEPS[import_name]
                system_deps[import_name] = deps
            else:
                # Check if it's a submodule of a known package
                base_module = import_name.split(".")[0]
                if base_module in IMPORT_TO_SYSTEM_DEPS:
                    deps = IMPORT_TO_SYSTEM_DEPS[base_module]
                    system_deps[base_module] = deps

        # Deduplicate system packages
        all_packages: set[str] = set()
        for deps in system_deps.values():
            all_packages.update(deps)

        return {
            "inferred_packages": sorted(all_packages),
            "import_mapping": system_deps,
            "confidence": "high" if system_deps else "low",
        }

    def _extract_all_imports(self, analysis_result: dict[str, Any]) -> set[str]:
        """Extract all unique imports from the analysis."""
        imports: set[str] = set()

        # From file analysis
        for file_data in analysis_result.get("file_analysis", {}).values():
            if "imports" in file_data:
                for imp in file_data["imports"]:
                    if isinstance(imp, dict):
                        module = imp.get("module", "")
                        if module:
                            imports.add(module)
                            # Also add parent modules for submodule matching
                            parts = module.split(".")
                            for i in range(1, len(parts)):
                                imports.add(".".join(parts[:i]))
                    else:
                        imports.add(str(imp))

        # From dependencies
        deps = analysis_result.get("dependencies", {})
        for lang_deps in deps.values():
            if isinstance(lang_deps, dict) and "all" in lang_deps:
                imports.update(lang_deps["all"])

        return imports
