"""Utility functions for copra."""

import inspect
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Type, Union


def get_python_type_for_handle(handle_type: Type[Any]) -> str:
    """Map a cocotb handle type to a Python type annotation.
    
    Args:
        handle_type: The cocotb handle type to map.
        
    Returns:
        A string representing the Python type annotation.
    """
    type_name = handle_type.__name__
    
    type_map = {
        "ModifiableObject": "ModifiableObject[Any]",
        "NonHierarchyObject": "NonHierarchyObject[Any]",
        "RealObject": "RealObject",
        "EnumObject": "EnumObject",
        "IntegerObject": "IntegerObject",
        "StringObject": "StringObject",
        "RealObject": "RealObject",
        "LogicObject": "LogicObject",
        "LogicArray": "LogicArray",
        "Logic": "Logic",
        "Range": "Range",
    }
    
    return type_map.get(type_name, "Any")


def get_imports_for_types(types: Set[Type[Any]]) -> List[str]:
    """Generate import statements for the given types.
    
    Args:
        types: Set of Python types to generate imports for.
        
    Returns:
        List of import statements.
    """
    imports = [
        "from typing import Any, List, Optional, Union, Dict, Tuple, Set, Callable, Type, TypeVar",
        "import cocotb.handle",
        "from cocotb.handle import (",
        "    HierarchyObject,",
        "    ModifiableObject,",
        "    NonHierarchyObject,",
        "    HierarchyArrayObject,",
        "    HierarchyObjectIterator,",
        "    RealObject,",
        "    EnumObject,",
        "    IntegerObject,",
        "    StringObject,",
        "    LogicObject,",
        "    Range,",
        "    SimHandleBase,",
        ")",
        "from cocotb.types import Logic, LogicArray, BitArray, BinaryValue",
    ]
    
    return imports


def format_docstring(doc: Optional[str], indent: int = 4) -> str:
    """Format a docstring with proper indentation.
    
    Args:
        doc: The docstring to format.
        indent: Number of spaces to indent each line.
        
    Returns:
        Formatted docstring.
    """
    if not doc:
        return ''
    
    indent_str = ' ' * indent
    lines = doc.strip().split('\n')
    
    # Remove common indentation
    if len(lines) > 1:
        # Find minimum indentation (ignoring empty lines)
        min_indent = float('inf')
        for line in lines[1:]:
            stripped = line.lstrip()
            if stripped:  # Skip empty lines
                min_indent = min(min_indent, len(line) - len(stripped))
        
        # Remove common indentation
        if min_indent != float('inf'):
            lines = [lines[0]] + [line[min_indent:] for line in lines[1:]]
    
    # Apply new indentation
    return '\n'.join(f'{indent_str}{line}' for line in lines)


def is_public_name(name: str) -> bool:
    """Check if a name should be considered public.
    
    Args:
        name: The name to check.
        
    Returns:
        True if the name is considered public, False otherwise.
    """
    return not (name.startswith('_') or name.endswith('_'))


def get_relative_import_path(from_path: Path, to_path: Path) -> str:
    """Get the relative import path from one path to another.
    
    Args:
        from_path: The source path.
        to_path: The destination path.
        
    Returns:
        The relative import path.
    """
    # Get the relative path between the two files
    rel_path = to_path.relative_to(from_path.parent)
    
    # Convert to import path
    parts = list(rel_path.parts)
    if parts[-1].endswith('.py'):
        parts[-1] = parts[-1][:-3]  # Remove .py
    
    # Handle __init__.py
    if parts and parts[-1] == '__init__':
        parts = parts[:-1]
    
    return '.'.join(parts)
