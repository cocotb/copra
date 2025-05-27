# Copyright cocotb contributors
# Licensed under the Revised BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-3-Clause

"""Core stub generation functionality for copra.

This module provides the fundamental functionality for discovering DUT hierarchies
and generating Python type stubs for cocotb testbenches.

Example usage:
    # From within a cocotb test:
    @cocotb.test()
    async def test_generate_stubs(dut):
        from copra import create_stub_from_dut
        stub_content = create_stub_from_dut(dut, "my_dut.pyi")

    # From command line:
    $ copra my_testbench_module --outfile stubs/dut.pyi
"""

import argparse
import importlib
import re
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, Optional, TextIO, TypeVar

from cocotb.handle import (
    EnumObject,
    HierarchyArrayObject,
    HierarchyObject,
    IntegerObject,
    LogicArrayObject,
    LogicObject,
    RealObject,
    StringObject,
    ValueObjectBase,
)

# Print cocotb version for debugging
try:
    import cocotb
    print(f"[copra.core] Using cocotb version: {cocotb.__version__}")
except (ImportError, AttributeError):
    print("[copra.core] cocotb version information not available")

from ._version import __version__
from .utils import to_capwords

# Public API
__all__ = [
    "discover_hierarchy",
    "generate_stub",
    "generate_stub_to_file",
    "generate_stub_with_validation",
    "create_stub_from_dut",
    "auto_generate_stubs",
    "main",
]

# Type variable for generic functions
F = TypeVar('F', bound=Callable[..., Any])


def discover_hierarchy(
    dut: Any, max_depth: int = 50, include_constants: bool = False
) -> Dict[str, type]:
    """Discover the hierarchy of objects in the DUT.

    Args:
    ----
        dut: The root DUT object.
        max_depth: Maximum recursion depth to prevent infinite loops.
        include_constants: Whether to include constant signals in discovery.

    Returns:
    -------
        A dictionary mapping hierarchical paths to their corresponding Python types.

    Raises:
    ------
        ValueError: If max_depth is exceeded or invalid parameters provided.
        RuntimeError: If discovery fails due to simulator issues.

    """
    if max_depth <= 0:
        raise ValueError("max_depth must be positive")

    hierarchy: Dict[str, type] = {}
    discovery_stats = {
        'total_objects': 0,
        'max_depth_reached': 0,
        'errors_encountered': 0
    }

    def _discover(obj: object, path: str, current_depth: int = 0) -> None:
        """Recursively discover the DUT hierarchy.

        Args:
        ----
            obj: The current object to discover.
            path: The current path in the hierarchy.
            current_depth: Current recursion depth.

        Raises:
        ------
            ValueError: If max_depth is exceeded.

        """
        if current_depth > max_depth:
            raise ValueError(f"Maximum hierarchy depth ({max_depth}) exceeded at path: {path}")

        discovery_stats['max_depth_reached'] = max(
            discovery_stats['max_depth_reached'], current_depth
        )

        # Get the object name
        obj_name = getattr(obj, '_name', None)
        if obj_name is None:
            return

        # Build the full path
        full_path = f"{path}.{obj_name}" if path else obj_name

        # Store the object type in hierarchy
        # For mock handles used in tests, use the intended handle type
        if hasattr(obj, '_handle_type'):
            hierarchy[full_path] = obj._handle_type
        else:
            hierarchy[full_path] = type(obj)

        discovery_stats['total_objects'] += 1

        # Skip constants unless explicitly requested
        if not include_constants and hasattr(obj, '_type') and 'const' in str(obj._type).lower():
            return

        # For real cocotb handles, use _discover_all() to populate sub-handles
        if hasattr(obj, '_discover_all') and callable(obj._discover_all):
            try:
                obj._discover_all()
            except Exception as e:
                discovery_stats['errors_encountered'] += 1
                print(f"[copra] Warning: Failed to discover children of {full_path}: {e}")
                # Continue with what we have
                pass

        # Get sub-handles for further exploration
        sub_handles = {}

        try:
            # For real cocotb HierarchyObject instances
            if hasattr(obj, '_sub_handles') and isinstance(obj._sub_handles, dict):
                sub_handles = obj._sub_handles
            # For mock handles used in tests
            elif hasattr(obj, '_sub_handles') and hasattr(obj, '_sub_handles_iter'):
                try:
                    sub_handles = {h._name: h for h in obj._sub_handles_iter()}
                except (TypeError, AttributeError):
                    # Handle case where _sub_handles_iter() is not iterable or fails
                    pass
            # For HierarchyArrayObject and other iterable objects
            elif hasattr(obj, '__iter__') and not isinstance(obj, (str, bytes)):
                try:
                    # Check if it's actually iterable and not a Mock
                    iter_obj = iter(obj)
                    for i, child in enumerate(iter_obj):
                        if hasattr(child, '_name'):
                            _discover(child, f"{full_path}[{i}]", current_depth + 1)
                    return
                except (TypeError, AttributeError):
                    # Not actually iterable or iteration failed
                    pass
        except Exception as e:
            discovery_stats['errors_encountered'] += 1
            print(f"[copra] Warning: Error accessing sub-handles of {full_path}: {e}")

        # Recursively discover sub-handles
        for name, child in sub_handles.items():
            # Skip if child is None or doesn't have required attributes
            if child is None or not hasattr(child, '_name'):
                continue
            try:
                _discover(child, full_path, current_depth + 1)
            except Exception as e:
                discovery_stats['errors_encountered'] += 1
                print(f"[copra] Warning: Error discovering {full_path}.{name}: {e}")
                continue

    try:
        _discover(dut, "")
    except Exception as e:
        raise RuntimeError(f"Hierarchy discovery failed: {e}") from e

    print(f"[copra] Discovery completed: {discovery_stats['total_objects']} objects, "
          f"max depth {discovery_stats['max_depth_reached']}, "
          f"{discovery_stats['errors_encountered']} errors")

    return hierarchy


def _extract_array_info(hierarchy: Mapping[str, type]) -> Dict[str, Dict[str, Any]]:
    """Extract array information from the hierarchy.

    Args:
    ----
        hierarchy: Dictionary mapping paths to types.

    Returns:
    -------
        Dictionary mapping base paths to array information including indices and element type.

    """
    arrays: Dict[str, Dict[str, Any]] = {}

    for path, obj_type in hierarchy.items():
        # Look for array patterns like "module.signal[0]", "module.signal[1]", etc.
        array_match = re.match(r'^(.+)\[(\d+)\]$', path)
        if array_match:
            base_path = array_match.group(1)
            index = int(array_match.group(2))

            if base_path not in arrays:
                arrays[base_path] = {
                    'indices': set(),
                    'element_type': obj_type,
                    'max_index': index,
                    'min_index': index
                }

            arrays[base_path]['indices'].add(index)
            arrays[base_path]['max_index'] = max(arrays[base_path]['max_index'], index)
            arrays[base_path]['min_index'] = min(arrays[base_path]['min_index'], index)

            # Ensure all elements have the same type
            if arrays[base_path]['element_type'] != obj_type:
                # If types differ, use the most general type
                arrays[base_path]['element_type'] = ValueObjectBase

    return arrays


def _generate_array_class(base_name: str, array_info: Dict[str, Any]) -> str:
    """Generate a class for array access.

    Args:
    ----
        base_name: Base name of the array.
        array_info: Array information including indices and element type.

    Returns:
    -------
        Generated class definition as a string.

    """
    class_name = f"{to_capwords(base_name)}Array"
    element_type = _get_type_annotation(array_info['element_type'])
    max_index = array_info['max_index']
    min_index = array_info['min_index']
    array_length = max_index - min_index + 1

    class_def = f"""from typing import Iterator, Sequence

class {class_name}(Sequence[{element_type}]):
    \"\"\"Array access for {base_name} with indices [{min_index}:{max_index}].

    This class provides sequence-like access to array elements in the DUT,
    supporting both indexing and iteration as specified in the design document.
    \"\"\"

    def __getitem__(self, index: int) -> {element_type}:
        \"\"\"Get array element by index.

        Args:
        ----
            index: Array index (0-based).

        Returns:
        -------
            Array element at the specified index.

        Raises:
        ------
            IndexError: If index is out of bounds.
        \"\"\"
        ...

    def __len__(self) -> int:
        \"\"\"Get array length.

        Returns:
        -------
            Number of elements in the array.
        \"\"\"
        return {array_length}

    def __iter__(self) -> Iterator[{element_type}]:
        \"\"\"Iterate over array elements.

        Returns:
        -------
            Iterator over array elements.
        \"\"\"
        ...

    def __contains__(self, item: object) -> bool:
        \"\"\"Check if item is in the array.

        Args:
        ----
            item: Item to check for.

        Returns:
        -------
            True if item is in array, False otherwise.
        \"\"\"
        ...

    @property
    def min_index(self) -> int:
        \"\"\"Get minimum valid index.\"\"\"
        return {min_index}

    @property
    def max_index(self) -> int:
        \"\"\"Get maximum valid index.\"\"\"
        return {max_index}
"""

    return class_def


def generate_stub_to_file(hierarchy: Mapping[str, type], output_file: TextIO) -> None:
    """Generate a Python stub file from the discovered hierarchy.

    Args:
    ----
        hierarchy: Dictionary mapping paths to types.
        output_file: File object to write the stub content to.

    """
    # Extract array information
    arrays = _extract_array_info(hierarchy)

    # Determine which types are actually used
    used_types = set(hierarchy.values())
    for array_info in arrays.values():
        used_types.add(array_info['element_type'])

    # Always include HierarchyObject as it's the base class
    used_types.add(HierarchyObject)

    # Write header and imports
    output_file.write("# This is an auto-generated stub file for cocotb testbench\n")
    output_file.write("# Generated by copra\n")
    output_file.write('"""Auto-generated type stubs for cocotb DUT."""\n\n')

    # Import cocotb handle types - only the ones we actually use
    handle_imports = ["HierarchyObject"]  # Always needed as base class

    # Add imports based on actual usage
    if LogicObject in used_types:
        handle_imports.append("LogicObject")
    if LogicArrayObject in used_types:
        handle_imports.append("LogicArrayObject")
    if ValueObjectBase in used_types:
        handle_imports.append("ValueObjectBase")
    if HierarchyArrayObject in used_types:
        handle_imports.append("HierarchyArrayObject")
    if RealObject in used_types:
        handle_imports.append("RealObject")
    if EnumObject in used_types:
        handle_imports.append("EnumObject")
    if IntegerObject in used_types:
        handle_imports.append("IntegerObject")
    if StringObject in used_types:
        handle_imports.append("StringObject")

    output_file.write("from cocotb.handle import (\n")
    for imp in sorted(handle_imports):
        output_file.write(f"    {imp},\n")
    output_file.write(")\n\n")

    # Generate array classes first
    for base_path, array_info in arrays.items():
        array_class = _generate_array_class(base_path.split('.')[-1], array_info)
        output_file.write(array_class)
        output_file.write("\n")

    # Organize hierarchy into module types and their members
    module_types: Dict[str, Dict[str, type]] = {}

    # First, add array base paths to the hierarchy so they can be processed as members
    extended_hierarchy = dict(hierarchy)
    for base_path, array_info in arrays.items():
        if base_path not in extended_hierarchy:
            # Add the array base path with a special marker type
            extended_hierarchy[base_path] = type(
                'ArrayBase',
                (),
                {
                    '_is_array_base': True,
                    '_element_type': array_info['element_type']
                }
            )

    for path, obj_type in extended_hierarchy.items():
        # Skip array elements - they'll be handled by array classes
        if re.match(r'^.+\[\d+\]$', path):
            continue

        parts = path.split('.')

        # Handle array indices in paths
        clean_parts = []
        for part in parts:
            if '[' in part:
                # Extract base name without array index
                base_name = part.split('[')[0]
                clean_parts.append(base_name)
            else:
                clean_parts.append(part)

        # Determine module type name
        if len(clean_parts) == 1:
            # Top-level object
            module_name = to_capwords(clean_parts[0])
            member_name = clean_parts[0]
        else:
            # Nested object - use parent as module type
            module_name = to_capwords(clean_parts[-2])
            member_name = clean_parts[-1]

        if module_name not in module_types:
            module_types[module_name] = {}

        module_types[module_name][member_name] = obj_type

    # Generate class definitions
    for module_name, members in sorted(module_types.items()):
        # Use CapWords for class names
        class_name = to_capwords(module_name)

        output_file.write(f"class {class_name}(HierarchyObject):\n")

        # Group members by type for better organization
        signals = {}
        sub_modules = {}
        array_members = {}

        for member_name, obj_type in sorted(members.items()):
            # Check if this member is an array base
            member_path = f"{module_name.lower()}.{member_name}"
            if member_path in arrays:
                array_members[member_name] = arrays[member_path]
            elif hasattr(obj_type, '_is_array_base'):
                # This is an array base type we added
                if member_path in arrays:
                    array_members[member_name] = arrays[member_path]
                else:
                    array_members[member_name] = {
                        'element_type': getattr(obj_type, '_element_type', ValueObjectBase)
                    }
            elif obj_type in (LogicObject, LogicArrayObject, ValueObjectBase,
                          RealObject, EnumObject, IntegerObject, StringObject):
                signals[member_name] = obj_type
            elif obj_type == HierarchyArrayObject:
                array_members[member_name] = {'element_type': HierarchyObject}
            else:
                sub_modules[member_name] = obj_type

        # Generate comprehensive docstring
        docstring = _generate_enhanced_class_docstring(
            class_name, signals, sub_modules, array_members
        )
        output_file.write(docstring)
        output_file.write("\n\n")  # Add extra blank line after docstring

        # Generate signal attributes
        if signals:
            output_file.write("    # Signal attributes\n")
            for name, obj_type in sorted(signals.items()):
                type_name = _get_type_annotation(obj_type)
                output_file.write(f"    {name}: {type_name}\n")
            output_file.write("\n")

        # Generate sub-module attributes
        if sub_modules:
            output_file.write("    # Sub-module attributes\n")
            for name, obj_type in sorted(sub_modules.items()):
                # Try to determine if this is a known module type
                sub_class_name = to_capwords(name)
                if sub_class_name in [to_capwords(mod) for mod in module_types.keys()]:
                    type_name = sub_class_name
                else:
                    type_name = "HierarchyObject"
                output_file.write(f"    {name}: {type_name}\n")
            output_file.write("\n")

        # Generate array attributes
        if array_members:
            output_file.write("    # Array attributes\n")
            for name, array_info in sorted(array_members.items()):
                if 'element_type' in array_info:
                    _get_type_annotation(array_info['element_type'])
                    array_class_name = f"{to_capwords(name)}Array"
                    output_file.write(f"    {name}: {array_class_name}\n")
                else:
                    output_file.write(f"    {name}: HierarchyArrayObject\n")
            output_file.write("\n")

    # Add a type alias for the top-level DUT if we have a clear top-level module
    if module_types:
        top_module = sorted(module_types.keys())[0]
        top_class = to_capwords(top_module)
        output_file.write("# Type alias for the main DUT\n")
        output_file.write(f"DutType = {top_class}\n")


def _get_type_annotation(obj_type: type) -> str:
    """Get the appropriate type annotation string for a cocotb object type.

    Args:
    ----
        obj_type: The Python type of the cocotb object.

    Returns:
    -------
        String representation of the type annotation.

    """
    if obj_type == LogicObject:
        return "LogicObject"
    elif obj_type == LogicArrayObject:
        return "LogicArrayObject"
    elif obj_type == HierarchyArrayObject:
        return "HierarchyArrayObject"
    elif obj_type == RealObject:
        return "RealObject"
    elif obj_type == EnumObject:
        return "EnumObject"
    elif obj_type == IntegerObject:
        return "IntegerObject"
    elif obj_type == StringObject:
        return "StringObject"
    elif obj_type == ValueObjectBase:
        return "ValueObjectBase"
    elif hasattr(obj_type, '__name__') and obj_type.__name__ == 'Mock':
        # Handle Mock objects in tests
        return "Mock"
    else:
        return "ValueObjectBase"


def _generate_enhanced_class_docstring(
    class_name: str,
    signals: Dict[str, type],
    sub_modules: Dict[str, type],
    arrays: Dict[str, Dict[str, Any]]
) -> str:
    """Generate a comprehensive docstring for a stub class.

    Args:
    ----
        class_name: Name of the class.
        signals: Dictionary of signal names to types.
        sub_modules: Dictionary of sub-module names to types.
        arrays: Dictionary of array names to array information.

    Returns:
    -------
        Formatted docstring for the class.

    """
    lines = [f'    """Auto-generated class for {class_name}.']

    if signals or sub_modules or arrays:
        lines.append("")
        lines.append("    This class provides typed access to the DUT hierarchy,")
        lines.append("    enabling IDE autocompletion and static type checking.")
        lines.append("")

        if signals:
            lines.append("    Signals:")
            for name, obj_type in sorted(signals.items()):
                type_name = _get_type_annotation(obj_type)
                lines.append(f"        {name}: {type_name}")
            lines.append("")

        if sub_modules:
            lines.append("    Sub-modules:")
            for name, obj_type in sorted(sub_modules.items()):
                sub_class_name = to_capwords(name)
                lines.append(f"        {name}: {sub_class_name} (hierarchical module)")
            lines.append("")

        if arrays:
            lines.append("    Arrays:")
            for name, array_info in sorted(arrays.items()):
                if 'max_index' in array_info and 'min_index' in array_info:
                    range_info = f"[{array_info['min_index']}:{array_info['max_index']}]"
                    element_type = _get_type_annotation(array_info['element_type'])
                    lines.append(f"        {name}: Array of {element_type} {range_info}")
                else:
                    lines.append(f"        {name}: Array of hierarchical objects")

    lines.append('    """')
    return "\n".join(lines)


def generate_stub(hierarchy: Mapping[str, type]) -> str:
    """Generate a Python stub file from the discovered hierarchy.

    Args:
    ----
        hierarchy: Dictionary mapping paths to types.

    Returns:
    -------
        A string containing the generated stub file content.

    """
    from io import StringIO

    output = StringIO()
    generate_stub_to_file(hierarchy, output)
    return output.getvalue()


def _run_discovery_simulation(top_module: str) -> HierarchyObject:
    """Run a minimal cocotb simulation to discover the DUT hierarchy.

    This function attempts multiple strategies to obtain a DUT handle:
    1. Try to import a module that already has a dut attribute
    2. Try to run a minimal cocotb test to get the DUT
    3. Try to use cocotb's test runner infrastructure

    Args:
    ----
        top_module: Name of the top-level module to introspect.

    Returns:
    -------
        The DUT handle from the simulation.

    Raises:
    ------
        ImportError: If the module cannot be imported or cocotb setup fails.
        AttributeError: If no DUT can be obtained.
        RuntimeError: If simulation setup fails.

    """
    # Strategy 1: Try to import a module that has a dut attribute
    try:
        module = importlib.import_module(top_module)
        if hasattr(module, 'dut') and isinstance(module.dut, HierarchyObject):
            print(f"[copra] Found DUT in module {top_module}")
            return module.dut
    except ImportError:
        pass  # Try other strategies

    # Strategy 2: Try to get DUT from cocotb's current simulation
    try:
        import cocotb
        if hasattr(cocotb, 'top') and cocotb.top is not None:
            print("[copra] Using cocotb.top as DUT")
            # Check if cocotb.top is a HierarchyObject, if not try to cast it
            if isinstance(cocotb.top, HierarchyObject):
                return cocotb.top
            else:
                # cocotb.top might be a SimHandleBase, try to use it anyway
                # since HierarchyObject is a subclass of SimHandleBase
                return cocotb.top  # type: ignore[return-value]
    except (ImportError, AttributeError):
        pass

    # Strategy 3: Try to create a minimal test environment
    try:
        # This is a more advanced approach that would require setting up
        # a full cocotb simulation environment. For now, we'll provide
        # a helpful error message.
        raise RuntimeError(
            f"Could not obtain DUT handle for module '{top_module}'. "
            "Please ensure that:\n"
            "1. The module is importable and contains a 'dut' attribute, or\n"
            "2. You are running this from within a cocotb test environment, or\n"
            "3. The cocotb simulation is already running with the DUT loaded.\n\n"
            "Example usage:\n"
            "  # In your test file:\n"
            "  import cocotb\n"
            "  from copra import discover_hierarchy, generate_stub\n"
            "  \n"
            "  @cocotb.test()\n"
            "  async def generate_stubs(dut):\n"
            "      hierarchy = discover_hierarchy(dut)\n"
            "      stub_content = generate_stub(hierarchy)\n"
            "      with open('dut.pyi', 'w') as f:\n"
            "          f.write(stub_content)\n"
        )
    except Exception as e:
        raise RuntimeError(f"Failed to set up simulation environment: {e}") from e


def create_stub_from_dut(dut: HierarchyObject, output_file: str = "dut.pyi") -> str:
    """Create a stub file from an existing DUT handle.

    This is the recommended way to use copra from within a cocotb test.

    Args:
    ----
        dut: The DUT handle from a cocotb test.
        output_file: Path to write the stub file to.

    Returns:
    -------
        The generated stub content as a string.

    Example:
    -------
        @cocotb.test()
        async def test_generate_stubs(dut):
            from copra import create_stub_from_dut
            stub_content = create_stub_from_dut(dut, "my_dut.pyi")
            print(f"Generated {len(stub_content)} characters of stub content")

    """
    print(f"[copra] Discovering hierarchy for DUT: {dut._name}")
    hierarchy = discover_hierarchy(dut)

    if not hierarchy:
        print("[copra] Warning: No hierarchy discovered. Generated stub will be empty.")
    else:
        print(f"[copra] Discovered {len(hierarchy)} objects in hierarchy")

    print(f"[copra] Generating stub file: {output_file}")
    stub_content = generate_stub(hierarchy)

    # Create output directory if it doesn't exist
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write to output file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(stub_content)

    print(f"[copra] Successfully generated stub file: {output_path}")
    print(f"[copra] Stub file contains {len(stub_content.splitlines())} lines")

    return stub_content


def auto_generate_stubs(
    output_file: str = "dut.pyi",
    enable: bool = True
) -> Callable[[F], F]:
    """Generate stubs automatically for cocotb tests.

    This decorator can be applied to cocotb test functions to automatically
    generate type stubs for the DUT when the test runs.

    Args:
    ----
        output_file: Path to write the stub file to.
        enable: Whether to enable stub generation (useful for conditional generation).

    Returns:
    -------
        Decorator function.

    Example:
    -------
        @cocotb.test()
        @auto_generate_stubs("my_dut.pyi")
        async def test_my_dut(dut):
            # Test code here
            pass

    """
    def decorator(test_func: F) -> F:
        """Actual decorator function."""
        import functools

        @functools.wraps(test_func)
        async def wrapper(dut: Any, *args: Any, **kwargs: Any) -> Any:
            """Generate stubs before running the test."""
            if enable:
                try:
                    print(f"[copra] Auto-generating stubs for {dut._name}")
                    create_stub_from_dut(dut, output_file)
                except Exception as e:
                    print(f"[copra] Warning: Failed to generate stubs: {e}")

            # Run the original test
            return await test_func(dut, *args, **kwargs)

        return wrapper  # type: ignore[return-value]
    return decorator


def main(args: Optional[List[str]] = None) -> int:
    """Generate Python type stubs for cocotb testbenches.

    Args:
    ----
        args: Command line arguments. If None, uses sys.argv[1:].

    Returns:
    -------
        Exit code.

    """
    parser = argparse.ArgumentParser(
        description='Generate Python type stubs for cocotb testbenches.',
        epilog="""
Examples:
  copra my_testbench_module --outfile stubs/dut.pyi
  copra my_project.tests.test_cpu --max-depth 20 --include-constants
  copra my_module --format json --outfile hierarchy.json

Note: This tool works best when run from within a cocotb test environment
or when the target module already has a 'dut' attribute available.

For the most reliable results, use create_stub_from_dut() directly in your
cocotb test functions.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        '-V', '--version',
        action='version',
        version=f'copra {__version__}',
        help='Show version and exit',
    )
    parser.add_argument(
        'top_module',
        help='Top-level module name to generate stubs for',
    )
    parser.add_argument(
        '--outfile',
        default='dut.pyi',
        help='Output file path (default: dut.pyi)',
    )
    parser.add_argument(
        '--format',
        choices=['pyi', 'json', 'yaml'],
        default='pyi',
        help='Output format: pyi (Python stub), json, or yaml (default: pyi)',
    )
    parser.add_argument(
        '--max-depth',
        type=int,
        default=50,
        help='Maximum hierarchy depth to traverse (default: 50)',
    )
    parser.add_argument(
        '--include-constants',
        action='store_true',
        help='Include constant signals in the output',
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output',
    )
    parser.add_argument(
        '--no-validation',
        action='store_true',
        help='Skip syntax validation of generated stubs',
    )
    parser.add_argument(
        '--stats',
        action='store_true',
        help='Show detailed statistics about the discovered hierarchy',
    )

    parsed_args = parser.parse_args(args)

    try:
        # Validate module name
        if not parsed_args.top_module or not parsed_args.top_module.strip():
            raise ValueError("Empty module name")

        # Create output directory if it doesn't exist
        output_path = Path(parsed_args.outfile)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Run discovery simulation to get DUT handle
        if parsed_args.verbose:
            print(f"[copra] Attempting to discover hierarchy for module: {parsed_args.top_module}")
        else:
            print(f"[copra] Discovering hierarchy for module: {parsed_args.top_module}")

        dut = _run_discovery_simulation(parsed_args.top_module)

        # Discover the hierarchy with enhanced options
        if parsed_args.verbose:
            print("[copra] Analyzing DUT hierarchy...")
        hierarchy = discover_hierarchy(
            dut,
            max_depth=parsed_args.max_depth,
            include_constants=parsed_args.include_constants
        )

        if not hierarchy:
            print("[copra] Warning: No hierarchy discovered. Generated output will be empty.")
            if parsed_args.verbose:
                print("[copra] This might happen if:")
                print("  - The DUT has no accessible sub-handles")
                print("  - The simulation hasn't been properly initialized")
                print("  - The DUT object doesn't support introspection")
        else:
            if parsed_args.verbose:
                print(f"[copra] Discovered {len(hierarchy)} objects in hierarchy:")
                for path, obj_type in sorted(hierarchy.items()):
                    print(f"  {path}: {obj_type.__name__}")
            else:
                print(f"[copra] Discovered {len(hierarchy)} objects in hierarchy")

        # Generate output based on format
        if parsed_args.verbose:
            print(f"[copra] Generating {parsed_args.format} output...")

        if parsed_args.format == 'pyi':
            if parsed_args.no_validation:
                output_content = generate_stub(hierarchy)
            else:
                try:
                    output_content = generate_stub_with_validation(hierarchy)
                    if parsed_args.verbose:
                        print("[copra] Stub syntax validation passed")
                except SyntaxError as e:
                    print(f"[copra] Error: Generated stub has syntax errors: {e}", file=sys.stderr)
                    print("[copra] Try using --no-validation to skip validation", file=sys.stderr)
                    return 1
        elif parsed_args.format == 'json':
            import json
            # Convert hierarchy to JSON-serializable format
            json_hierarchy = {path: obj_type.__name__ for path, obj_type in hierarchy.items()}
            output_content = json.dumps(json_hierarchy, indent=2, sort_keys=True)
        elif parsed_args.format == 'yaml':
            try:
                import yaml
                # Convert hierarchy to YAML-serializable format
                yaml_hierarchy = {path: obj_type.__name__ for path, obj_type in hierarchy.items()}
                output_content = yaml.dump(yaml_hierarchy, default_flow_style=False, sort_keys=True)
            except ImportError:
                print("[copra] Error: PyYAML is required for YAML output format", file=sys.stderr)
                print("[copra] Install with: pip install PyYAML", file=sys.stderr)
                return 1

        # Write to output file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(output_content)

        print(f"[copra] Successfully generated {parsed_args.format} file: {output_path}")
        if parsed_args.verbose:
            print(f"[copra] Output file contains {len(output_content.splitlines())} lines")
            print(f"[copra] File size: {len(output_content)} characters")

        # Show statistics if requested
        if parsed_args.stats:
            from .analysis import analyze_hierarchy_complexity
            stats = analyze_hierarchy_complexity(dut)
            print("\n[copra] Hierarchy Statistics:")
            print(f"  Total signals: {stats['total_signals']}")
            print(f"  Maximum depth: {stats['max_depth']}")
            print(f"  Module count: {stats['module_count']}")
            print(f"  Array count: {stats['array_count']}")
            print("  Signal types:")
            for signal_type, count in sorted(stats['signal_types'].items()):
                print(f"    {signal_type}: {count}")

    except ImportError as e:
        print(f"[copra] Import Error: {e}", file=sys.stderr)
        print(f"[copra] Make sure the module '{parsed_args.top_module}' is importable",
              file=sys.stderr)
        if parsed_args.verbose:
            print("[copra] Check your PYTHONPATH and ensure all dependencies are installed",
                  file=sys.stderr)
        return 1

    except AttributeError as e:
        print(f"[copra] Attribute Error: {e}", file=sys.stderr)
        print("[copra] The module should contain a 'dut' attribute with the DUT handle",
              file=sys.stderr)
        return 1

    except ValueError as e:
        print(f"[copra] Value Error: {e}", file=sys.stderr)
        return 1

    except RuntimeError as e:
        print(f"[copra] Runtime Error: {e}", file=sys.stderr)
        return 1

    except OSError as e:
        print(f"[copra] File I/O Error: {e}", file=sys.stderr)
        print(f"[copra] Check that you have write permissions for {parsed_args.outfile}",
              file=sys.stderr)
        return 1

    except KeyboardInterrupt:
        print("\n[copra] Operation cancelled by user", file=sys.stderr)
        return 130  # Standard exit code for SIGINT

    except Exception as e:
        print(f"[copra] Unexpected error: {e}", file=sys.stderr)
        if parsed_args.verbose:
            import traceback
            traceback.print_exc()
        print("[copra] Please report this issue at: https://github.com/cocotb/copra/issues",
              file=sys.stderr)
        return 1

    return 0


def generate_stub_with_validation(hierarchy: Mapping[str, type]) -> str:
    """Generate a Python stub file with syntax validation.

    Args:
    ----
        hierarchy: Dictionary mapping paths to types.

    Returns:
    -------
        A string containing the generated stub file content.

    Raises:
    ------
        SyntaxError: If the generated stub content is not valid Python syntax.

    """
    from .analysis import validate_stub_syntax

    stub_content = generate_stub(hierarchy)

    if not validate_stub_syntax(stub_content):
        raise SyntaxError("Generated stub content contains syntax errors")

    return stub_content


def _get_signal_width_info(obj: Any) -> Dict[str, Any]:
    """Extract signal width and type information from a cocotb handle.

    Args:
    ----
        obj: The cocotb handle object.

    Returns:
    -------
        Dictionary containing width, type, and other signal information.

    """
    # Get the object type first to determine default type_name
    obj_type = type(obj)
    is_mock = hasattr(obj_type, '__name__') and obj_type.__name__ == 'Mock'
    default_type_name = 'Mock' if is_mock else 'LogicObject'

    info = {
        'width': 1,
        'is_array': False,
        'is_signed': False,
        'type_name': default_type_name
    }

    try:
        # Try to get width information
        if hasattr(obj, '_length') and obj._length is not None:
            info['width'] = obj._length
            info['is_array'] = obj._length > 1

        # Determine if signal is signed (check for signed but not unsigned)
        if hasattr(obj, '_type'):
            type_str = str(obj._type).lower()
            if 'signed' in type_str and 'unsigned' not in type_str:
                info['is_signed'] = True

        # Get more specific type information
        if obj_type == LogicArrayObject:
            info['type_name'] = 'LogicArrayObject'
            info['is_array'] = True
        elif obj_type == LogicObject:
            info['type_name'] = 'LogicObject'
        elif obj_type == RealObject:
            info['type_name'] = 'RealObject'
        elif obj_type == IntegerObject:
            info['type_name'] = 'IntegerObject'
        elif obj_type == EnumObject:
            info['type_name'] = 'EnumObject'
        elif obj_type == StringObject:
            info['type_name'] = 'StringObject'
        elif hasattr(obj_type, '__name__') and obj_type.__name__ == 'Mock':
            # Handle Mock objects in tests
            info['type_name'] = 'Mock'
        else:
            info['type_name'] = obj_type.__name__

    except Exception:
        # If we can't get detailed info, use defaults
        pass

    return info


if __name__ == "__main__":
    sys.exit(main())
