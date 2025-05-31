# Copyright cocotb contributors
# Licensed under the Revised BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-3-Clause

"""Utility functions for copra."""

import re
from pathlib import Path
from typing import Any, List, Optional, Set, Type

# Print cocotb version for debugging
try:
    import cocotb  # type: ignore[import-untyped]
    
    COCOTB_AVAILABLE = True
    print(f"[copra.utils] Using cocotb version: {cocotb.__version__}")
except (ImportError, AttributeError):
    COCOTB_AVAILABLE = False
    print("[copra.utils] cocotb version information not available")


def get_python_type_for_handle(handle_type: Type[Any]) -> str:
    """Map a cocotb handle type to a Python type annotation.

    Args:
    ----
        handle_type: The cocotb handle type to map.

    Returns:
    -------
        A string representing the Python type annotation.

    """
    type_name = handle_type.__name__

    type_map = {
        "SimHandleBase": "SimHandleBase",
        "LogicArray": "LogicArray",
        "HierarchyObject": "HierarchyObject",
        "HierarchyArrayObject": "HierarchyArrayObject",
        "RealObject": "RealObject",
        "EnumObject": "EnumObject",
        "IntegerObject": "IntegerObject",
        "StringObject": "StringObject",
        "ArrayObject": "ArrayObject",
        # These types fall back to SimHandleBase
        "LogicObject": "SimHandleBase",
        "LogicArrayObject": "SimHandleBase",
        "ValueObjectBase": "SimHandleBase",
        "Logic": "SimHandleBase",
        "Range": "SimHandleBase",
    }

    return type_map.get(type_name, "SimHandleBase")


def get_imports_for_types(types: Set[Type[Any]]) -> List[str]:
    """Generate import statements for the given types.

    Args:
    ----
        types: Set of Python types to generate imports for.

    Returns:
    -------
        List of import statements.

    """
    imports = [
        "from typing import Any, Union",
        "from cocotb.handle import (",
        "    HierarchyObject,",
        "    HierarchyArrayObject,",
        "    SimHandleBase,",
        "    LogicArray,",
        "    RealObject,",
        "    EnumObject,",
        "    IntegerObject,",
        "    StringObject,",
        "    ArrayObject,",
        ")",
    ]

    return imports


def format_docstring(doc: Optional[str], indent: int = 4) -> str:
    """Format a docstring with proper indentation.

    Args:
    ----
        doc: The docstring to format.
        indent: Number of spaces to indent each line.

    Returns:
    -------
        Formatted docstring.

    """
    if not doc:
        return ""

    indent_str = " " * indent
    lines = doc.strip().split("\n")

    # Remove common indentation
    if len(lines) > 1:
        # Find minimum indentation (ignoring empty lines)
        min_indent: float = float("inf")
        for line in lines[1:]:
            stripped = line.lstrip()
            if stripped:  # Skip empty lines
                min_indent = min(min_indent, len(line) - len(stripped))

        # Remove common indentation
        if min_indent != float("inf"):
            min_indent_int = int(min_indent)
            lines = [lines[0]] + [line[min_indent_int:] for line in lines[1:]]

    # Apply new indentation
    return "\n".join(f"{indent_str}{line}" for line in lines)


def is_public_name(name: str) -> bool:
    """Check if a name should be considered public.

    Args:
    ----
        name: The name to check.

    Returns:
    -------
        True if the name is considered public, False otherwise.

    """
    return not name.startswith("_")


def to_capwords(name: str) -> str:
    """Convert a name to CapWords convention for class names.

    Args:
    ----
        name: The name to convert.

    Returns:
    -------
        The name converted to CapWords convention.

    """
    # Handle common separators and convert to CapWords
    # Split on underscores, hyphens, and preserve existing camelCase

    # Split on underscores and hyphens
    parts = re.split(r"[_-]", name)

    # Further split camelCase parts
    expanded_parts = []
    for part in parts:
        # Split camelCase: insert space before uppercase letters that follow lowercase
        camel_split = re.sub(r"([a-z])([A-Z])", r"\1 \2", part)
        expanded_parts.extend(camel_split.split())

    # Capitalize each part and join
    return "".join(part.capitalize() for part in expanded_parts if part)


def get_relative_import_path(from_path: Path, to_path: Path) -> str:
    """Get the relative import path from one path to another.

    Args:
    ----
        from_path: The source path.
        to_path: The destination path.

    Returns:
    -------
        The relative import path.

    """
    # Get the relative path between the two files
    rel_path = to_path.relative_to(from_path.parent)

    # Convert to import path
    parts = list(rel_path.parts)
    if parts[-1].endswith(".py"):
        parts[-1] = parts[-1][:-3]  # Remove .py

    # Handle __init__.py
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]

    return ".".join(parts)
