#!/usr/bin/env python3

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Refactored to reduce file size from 25KB to under 10KB
# - Extracted PRACTICAL_TAXONOMY to system_taxonomy_data.py and system_taxonomy_data2.py
# - Extracted constants to system_taxonomy_constants.py
# - Retained core functionality with delegation to helper modules
#

"""
System taxonomy module for DHT.

This module provides a comprehensive categorization of development tools
organized by use-case. It handles platform-specific availability checking
and filtering to ensure only relevant tools are presented for each platform.

The taxonomy is designed to be:
- Use-case driven (organized by what developers need tools for)
- Platform-aware (knows which tools exist on which platforms)
- Atomic (every piece of information has a clear path)
- Extensible (easy to add new tools and categories)
"""

import copy
import platform
from typing import Any

from DHT.modules.system_taxonomy_constants import CROSS_PLATFORM_TOOLS, PLATFORM_EXCLUSIONS, PLATFORM_TOOLS

# Import taxonomy data and constants from helper modules
from DHT.modules.system_taxonomy_data import PRACTICAL_TAXONOMY as PRACTICAL_TAXONOMY_PART1
from DHT.modules.system_taxonomy_data2 import PRACTICAL_TAXONOMY_PART2


def get_current_platform() -> str:
    """
    Get the current platform name, normalized to lowercase.

    Returns:
        str: Normalized platform name ('macos', 'linux', 'windows', etc.)
    """
    system = platform.system()

    # Normalize platform names
    if system == 'Darwin':
        return 'macos'
    elif system == 'Linux':
        return 'linux'
    elif system == 'Windows':
        return 'windows'
    else:
        # Return as-is but lowercase for unknown platforms
        return system.lower()


def merge_taxonomies() -> dict[str, Any]:
    """
    Merge the taxonomy parts into a single dictionary.

    Returns:
        Dict containing the complete practical taxonomy
    """
    # Merge the two taxonomy parts
    complete_taxonomy = {}
    complete_taxonomy.update(PRACTICAL_TAXONOMY_PART1)
    complete_taxonomy.update(PRACTICAL_TAXONOMY_PART2)
    return complete_taxonomy


# Create the complete PRACTICAL_TAXONOMY by merging parts
PRACTICAL_TAXONOMY = merge_taxonomies()


def is_tool_available_on_platform(tool_name: str, platform_name: str = None) -> bool:
    """
    Check if a tool is available on the given platform.

    Args:
        tool_name: Name of the tool to check
        platform_name: Platform to check for (defaults to current platform)

    Returns:
        bool: True if tool is available on platform, False otherwise
    """
    if platform_name is None:
        platform_name = get_current_platform()

    # Check if tool is explicitly excluded on this platform
    if platform_name in PLATFORM_EXCLUSIONS:
        if tool_name in PLATFORM_EXCLUSIONS[platform_name]:
            return False

    # Check if it's a cross-platform tool (available everywhere)
    if tool_name in CROSS_PLATFORM_TOOLS:
        return True

    # Check if it's a platform-specific tool
    if platform_name in PLATFORM_TOOLS:
        for _category, tools in PLATFORM_TOOLS[platform_name].items():
            if tool_name in tools:
                return True

    # If not explicitly excluded and not in platform-specific lists,
    # we assume it might be available (user may have installed it)
    return True


def filter_tools_for_platform(tools: dict[str, Any], platform_name: str = None) -> dict[str, Any]:
    """
    Filter a tools dictionary to only include tools available on the platform.

    Args:
        tools: Dictionary of tools to filter
        platform_name: Platform to filter for (defaults to current platform)

    Returns:
        Dict: Filtered tools dictionary
    """
    if platform_name is None:
        platform_name = get_current_platform()

    filtered = {}
    for tool_name, tool_info in tools.items():
        if is_tool_available_on_platform(tool_name, platform_name):
            filtered[tool_name] = tool_info

    return filtered


def get_category_for_platform(category_name: str, platform_name: str = None) -> dict[str, Any]:
    """
    Get a category filtered for the given platform.

    Args:
        category_name: Name of the category to retrieve
        platform_name: Platform to filter for (defaults to current platform)

    Returns:
        Dict: Category information filtered for platform
    """
    if platform_name is None:
        platform_name = get_current_platform()

    if category_name not in PRACTICAL_TAXONOMY:
        return {}

    category = copy.deepcopy(PRACTICAL_TAXONOMY[category_name])

    # Handle nested categories (like package_managers)
    if 'categories' in category:
        for subcat_name, subcat_data in category['categories'].items():
            if 'tools' in subcat_data:
                subcat_data['tools'] = filter_tools_for_platform(
                    subcat_data['tools'], platform_name
                )
            # Handle language-specific package managers (different structure)
            elif subcat_name == 'language' and isinstance(subcat_data, dict):
                # The language subcategory has a different structure:
                # It has language names as keys instead of 'tools'
                for lang_name, lang_tools in subcat_data.items():
                    if lang_name != 'description' and isinstance(lang_tools, list):
                        # Filter list of tools
                        filtered_tools = [
                            tool for tool in lang_tools
                            if is_tool_available_on_platform(tool, platform_name)
                        ]
                        subcat_data[lang_name] = filtered_tools
    elif 'tools' in category:
        category['tools'] = filter_tools_for_platform(
            category['tools'], platform_name
        )

    return category


def get_tool_fields(category_name: str, tool_name: str) -> list[str]:
    """
    Get the list of fields available for a specific tool in a category.

    Args:
        category_name: Name of the category (can be nested like 'package_managers.language.python')
        tool_name: Name of the tool

    Returns:
        List[str]: List of field names available for the tool
    """
    # For single category names, search directly
    if '.' not in category_name:
        if category_name in PRACTICAL_TAXONOMY:
            category_data = PRACTICAL_TAXONOMY[category_name]

            # Check direct tools
            if 'tools' in category_data and tool_name in category_data['tools']:
                return category_data['tools'][tool_name]

            # Check nested categories
            if 'categories' in category_data:
                for subcat_name, subcat_data in category_data['categories'].items():
                    # Check standard subcategory with tools
                    if isinstance(subcat_data, dict) and 'tools' in subcat_data:
                        if tool_name in subcat_data['tools']:
                            return subcat_data['tools'][tool_name]
                    # Check language subcategory structure
                    elif subcat_name == 'language' and isinstance(subcat_data, dict):
                        for lang_name, lang_tools in subcat_data.items():
                            if lang_name != 'description' and isinstance(lang_tools, list):
                                if tool_name in lang_tools:
                                    # For tools in language lists, return standard version field
                                    return ['version']
    else:
        # Handle nested category paths
        category_parts = category_name.split('.')
        current_data = PRACTICAL_TAXONOMY

        # Navigate to the correct category
        for i, part in enumerate(category_parts):
            if part in current_data:
                current_data = current_data[part]
                if 'categories' in current_data and i < len(category_parts) - 1:
                    current_data = current_data['categories']
            else:
                return []

        # Look for the tool
        if 'tools' in current_data and tool_name in current_data['tools']:
            return current_data['tools'][tool_name]

        # Handle language-specific package managers
        if isinstance(current_data, dict):
            for lang_name, lang_data in current_data.items():
                if lang_name != 'description':
                    if isinstance(lang_data, dict) and 'tools' in lang_data and tool_name in lang_data['tools']:
                        return lang_data['tools'][tool_name]
                    elif isinstance(lang_data, list) and tool_name in lang_data:
                        # For simple lists, return standard fields
                        return ['version']

    return []


def get_all_tools_for_platform(platform_name: str = None) -> dict[str, list[str]]:
    """
    Get all tools available on the given platform, organized by category.

    Args:
        platform_name: Platform to get tools for (defaults to current platform)

    Returns:
        Dict: Tools organized by category
    """
    if platform_name is None:
        platform_name = get_current_platform()

    result = {}

    for category_name, _category_data in PRACTICAL_TAXONOMY.items():
        filtered_category = get_category_for_platform(category_name, platform_name)

        if 'tools' in filtered_category and filtered_category['tools']:
            result[category_name] = list(filtered_category['tools'].keys())

        # Handle nested categories
        if 'categories' in filtered_category:
            for subcat_name, subcat_data in filtered_category['categories'].items():
                if 'tools' in subcat_data and subcat_data['tools']:
                    result[f"{category_name}.{subcat_name}"] = list(subcat_data['tools'].keys())

                # Handle language-specific package managers
                elif isinstance(subcat_data, dict):
                    for lang_name, lang_tools in subcat_data.items():
                        if lang_name != 'description' and isinstance(lang_tools, list) and lang_tools:
                            result[f"{category_name}.{subcat_name}.{lang_name}"] = lang_tools

    return result


def find_tool_category(tool_name: str) -> str | None:
    """
    Find which category a tool belongs to.

    Args:
        tool_name: Name of the tool to find

    Returns:
        Optional[str]: Category path (e.g., "package_managers.language.python") or None
    """
    for category_name, category_data in PRACTICAL_TAXONOMY.items():
        if 'tools' in category_data and tool_name in category_data['tools']:
            return category_name

        # Handle nested categories
        if 'categories' in category_data:
            for subcat_name, subcat_data in category_data['categories'].items():
                if 'tools' in subcat_data and tool_name in subcat_data['tools']:
                    return f"{category_name}.{subcat_name}"

                # Handle language-specific package managers
                elif isinstance(subcat_data, dict):
                    for lang_name, lang_tools in subcat_data.items():
                        if lang_name != 'description' and isinstance(lang_tools, list):
                            if tool_name in lang_tools:
                                return f"{category_name}.{subcat_name}.{lang_name}"

    return None


def get_relevant_categories(platform_name: str = None) -> dict[str, Any]:
    """
    Get all categories relevant to the given platform, with tools filtered.

    Args:
        platform_name: Platform to get categories for (defaults to current platform)

    Returns:
        Dict: All categories with tools filtered for the platform
    """
    if platform_name is None:
        platform_name = get_current_platform()

    filtered_taxonomy = copy.deepcopy(PRACTICAL_TAXONOMY)

    # Filter each category for the platform
    for category_name in list(filtered_taxonomy.keys()):
        category_data = get_category_for_platform(category_name, platform_name)

        # Remove empty categories
        if 'tools' in category_data and not category_data['tools']:
            # Check if there are subcategories with tools
            has_tools = False
            if 'categories' in category_data:
                for subcat in category_data['categories'].values():
                    if 'tools' in subcat and subcat['tools']:
                        has_tools = True
                        break
                    # Check language-specific tools
                    elif isinstance(subcat, dict):
                        for lang_name, lang_tools in subcat.items():
                            if lang_name != 'description' and isinstance(lang_tools, list) and lang_tools:
                                has_tools = True
                                break

            if not has_tools:
                del filtered_taxonomy[category_name]
        else:
            filtered_taxonomy[category_name] = category_data

    return filtered_taxonomy


# Export public API
__all__ = [
    'PRACTICAL_TAXONOMY',
    'PLATFORM_TOOLS',
    'get_current_platform',
    'is_tool_available_on_platform',
    'filter_tools_for_platform',
    'get_category_for_platform',
    'get_tool_fields',
    'get_all_tools_for_platform',
    'find_tool_category',
    'get_relevant_categories',
]
