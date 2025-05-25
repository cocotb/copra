# Copyright cocotb contributors
# Licensed under the Revised BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-3-Clause

"""Generate Python type stubs for cocotb testbenches.

This module provides functionality to automatically generate Python type stubs (.pyi files)
for cocotb Device Under Test (DUT) objects. The generated stubs enable IDE autocompletion
and static type checking for cocotb testbenches.

Example usage:
    # From within a cocotb test:
    @cocotb.test()
    async def test_generate_stubs(dut):
        from copra.stubgen import create_stub_from_dut
        stub_content = create_stub_from_dut(dut, "my_dut.pyi")

    # From command line:
    $ copra my_testbench_module --outfile stubs/dut.pyi
"""

import argparse
import importlib
import sys
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, TextIO

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
    print(f"[copra.stubgen] Using cocotb version: {cocotb.__version__}")
except (ImportError, AttributeError):
    print("[copra.stubgen] cocotb version information not available")

from ._version import __version__
from .utils import to_capwords

# Public API
__all__ = [
    "discover_hierarchy",
    "generate_stub",
    "generate_stub_to_file",
    "generate_stub_with_validation",
    "validate_stub_syntax",
    "create_stub_from_dut",
    "main",
]


def discover_hierarchy(dut: Any) -> Dict[str, type]:
    """Discover the hierarchy of objects in the DUT.

    Args:
    ----
        dut: The root DUT object.

    Returns:
    -------
        A dictionary mapping hierarchical paths to their corresponding Python types.

    """
    hierarchy: Dict[str, type] = {}

    def _discover(obj: object, path: str) -> None:
        """Recursively discover the DUT hierarchy.

        Args:
        ----
            obj: The current object to discover.
            path: The current path in the hierarchy.

        """
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

        # For real cocotb handles, use _discover_all() to populate sub-handles
        if hasattr(obj, '_discover_all') and callable(obj._discover_all):
            try:
                obj._discover_all()
            except Exception:
                # If discovery fails, continue with what we have
                pass

        # Get sub-handles for further exploration
        sub_handles = {}

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
                        _discover(child, f"{full_path}[{i}]")
                return
            except (TypeError, AttributeError):
                # Not actually iterable or iteration failed
                pass

        # Recursively discover sub-handles
        for name, child in sub_handles.items():
            # Skip if child is None or doesn't have required attributes
            if child is None or not hasattr(child, '_name'):
                continue
            _discover(child, full_path)

    _discover(dut, "")
    return hierarchy


def generate_stub_to_file(hierarchy: Mapping[str, type], output_file: TextIO) -> None:
    """Generate a Python stub file from the discovered hierarchy.

    Args:
    ----
        hierarchy: Dictionary mapping paths to types.
        output_file: File object to write the stub content to.

    """
    # Determine which types are actually used
    used_types = set(hierarchy.values())

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

    # Organize hierarchy into module types and their members
    module_types: Dict[str, Dict[str, type]] = {}

    for path, obj_type in hierarchy.items():
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
        arrays = {}

        for member_name, obj_type in sorted(members.items()):
            if obj_type in (LogicObject, LogicArrayObject, ValueObjectBase,
                          RealObject, EnumObject, IntegerObject, StringObject):
                signals[member_name] = obj_type
            elif obj_type == HierarchyArrayObject:
                arrays[member_name] = obj_type
            else:
                sub_modules[member_name] = obj_type

        # Generate the class docstring with proper formatting
        output_file.write(f'    """Auto-generated class for {class_name}."""\n')
        output_file.write("\n")

        # Generate signal attributes
        if signals:
            for name, obj_type in sorted(signals.items()):
                type_name = _get_type_annotation(obj_type)
                output_file.write(f"    {name}: {type_name}\n")

        # Generate sub-module attributes
        if sub_modules:
            for name, obj_type in sorted(sub_modules.items()):
                type_name = "HierarchyObject"
                output_file.write(f"    {name}: {type_name}\n")

        # Generate array attributes with indexing support
        if arrays:
            for name, obj_type in sorted(arrays.items()):
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
    else:
        return "ValueObjectBase"


def _generate_class_docstring(module_name: str, signals: Dict[str, type],
                             sub_modules: Dict[str, type], arrays: Dict[str, type]) -> str:
    """Generate a comprehensive docstring for a stub class.

    Args:
    ----
        module_name: Name of the module/class.
        signals: Dictionary of signal names to types.
        sub_modules: Dictionary of sub-module names to types.
        arrays: Dictionary of array names to types.

    Returns:
    -------
        Formatted docstring for the class.

    """
    lines = [f"Auto-generated class for {module_name}."]

    if signals or sub_modules or arrays:
        lines.append("")
        lines.append("Attributes:")

        # Document signals
        for name, obj_type in sorted(signals.items()):
            type_name = _get_type_annotation(obj_type)
            lines.append(f"    {name}: {type_name}")

        # Document sub-modules
        for name, obj_type in sorted(sub_modules.items()):
            if obj_type == HierarchyObject:
                type_name = "HierarchyObject"
            else:
                # For consistency with the main generation logic, use HierarchyObject
                # since we can't easily check module_types from here
                type_name = "HierarchyObject"
            lines.append(f"    {name}: {type_name}")

        # Document arrays
        for name, obj_type in sorted(arrays.items()):
            lines.append(f"    {name}: HierarchyArrayObject")

    # Format with proper indentation
    formatted_lines = []
    for i, line in enumerate(lines):
        if i == 0:
            formatted_lines.append(f'    """{line}')
        elif line == "":
            formatted_lines.append("    ")
        else:
            formatted_lines.append(f"    {line}")

    formatted_lines.append('    """')
    return "\n".join(formatted_lines)


def _should_generate_array_methods(module_name: str, hierarchy: Mapping[str, type],
                                  arrays: Dict[str, type]) -> bool:
    """Determine if array access methods should be generated for a class.

    Args:
    ----
        module_name: Name of the module/class.
        hierarchy: Full hierarchy dictionary.
        arrays: Dictionary of array names to types.

    Returns:
    -------
        True if array methods should be generated.

    """
    # Generate array methods if there are explicit arrays
    if arrays:
        return True

    # Or if there are indexed elements in the hierarchy for this module
    module_paths = [path for path in hierarchy.keys()
                   if path.lower().startswith(module_name.lower())]
    return any('[' in path for path in module_paths)


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
            "  from copra.stubgen import discover_hierarchy, generate_stub\n"
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
            from copra.stubgen import create_stub_from_dut
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
  copra my_project.tests.test_cpu

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
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output',
    )
    parser.add_argument(
        '--no-validation',
        action='store_true',
        help='Skip syntax validation of generated stubs',
    )

    parsed_args = parser.parse_args(args)

    try:
        # Create output directory if it doesn't exist
        output_path = Path(parsed_args.outfile)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Run discovery simulation to get DUT handle
        if parsed_args.verbose:
            print(f"[copra] Attempting to discover hierarchy for module: {parsed_args.top_module}")
        else:
            print(f"[copra] Discovering hierarchy for module: {parsed_args.top_module}")

        dut = _run_discovery_simulation(parsed_args.top_module)

        # Discover the hierarchy
        if parsed_args.verbose:
            print("[copra] Analyzing DUT hierarchy...")
        hierarchy = discover_hierarchy(dut)

        if not hierarchy:
            print("[copra] Warning: No hierarchy discovered. Generated stub will be empty.")
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

        # Generate stub content
        if parsed_args.verbose:
            print("[copra] Generating stub file...")

        if parsed_args.no_validation:
            stub_content = generate_stub(hierarchy)
        else:
            try:
                stub_content = generate_stub_with_validation(hierarchy)
                if parsed_args.verbose:
                    print("[copra] Stub syntax validation passed")
            except SyntaxError as e:
                print(f"[copra] Error: Generated stub has syntax errors: {e}", file=sys.stderr)
                print("[copra] Try using --no-validation to skip validation", file=sys.stderr)
                return 1

        # Write to output file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(stub_content)

        print(f"[copra] Successfully generated stub file: {output_path}")
        if parsed_args.verbose:
            print(f"[copra] Stub file contains {len(stub_content.splitlines())} lines")
            print(f"[copra] File size: {len(stub_content)} characters")

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


def validate_stub_syntax(stub_content: str) -> bool:
    """Validate that the generated stub content is syntactically correct Python.

    Args:
    ----
        stub_content: The generated stub file content as a string.

    Returns:
    -------
        True if the stub content is valid Python syntax, False otherwise.

    """
    try:
        import ast
        ast.parse(stub_content)
        return True
    except SyntaxError as e:
        print(f"[copra] Warning: Generated stub has syntax error: {e}")
        return False
    except Exception as e:
        print(f"[copra] Warning: Could not validate stub syntax: {e}")
        return False


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
    stub_content = generate_stub(hierarchy)

    if not validate_stub_syntax(stub_content):
        raise SyntaxError("Generated stub content contains syntax errors")

    return stub_content


if __name__ == "__main__":
    sys.exit(main())
