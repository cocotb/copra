# Copyright cocotb contributors
# Licensed under the Revised BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-3-Clause

"""Enhanced code generation utilities for copra.

This module provides template-based generation capabilities and enhanced
documentation generation as specified in the design document.
"""

import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

try:
    from cocotb.handle import HierarchyObject

    COCOTB_AVAILABLE = True
except ImportError:
    COCOTB_AVAILABLE = False

    class HierarchyObject:  # type: ignore[no-redef]
        """Mock HierarchyObject when cocotb is not available."""

        pass

from ._version import __version__
from .core import discover_hierarchy
from .utils import to_capwords


@dataclass
class StubGenerationOptions:
    """Configuration options for stub generation.

    Args:
    ----
        flat_hierarchy: Whether to generate a flat hierarchy or nested classes.
        include_metadata: Whether to include signal metadata in docstrings.
        include_arrays: Whether to generate array support classes.
        include_docstrings: Whether to generate docstrings.
        typing_style: Style of type hints ("modern" or "legacy").
        class_prefix: Prefix to add to generated class names.
        class_suffix: Suffix to add to generated class names.
        output_format: Output format ("pyi" or "py").

    """

    flat_hierarchy: bool = False
    include_metadata: bool = True
    include_arrays: bool = True
    include_docstrings: bool = True
    typing_style: str = "modern"
    class_prefix: str = ""
    class_suffix: str = ""
    output_format: str = "pyi"


class StubGenerator:
    """Generate type stubs for DUT hierarchies with customizable options."""

    def __init__(self, options: Optional[StubGenerationOptions] = None):
        """Initialize stub generator with options.

        Args:
        ----
            options: Configuration options for stub generation.

        """
        self.options = options or StubGenerationOptions()
        self.template = StubTemplate()

    def generate_stub(self, hierarchy: Dict[str, type], module_name: str) -> str:
        """Generate a type stub from a hierarchy dictionary.

        Args:
        ----
            hierarchy: DUT hierarchy dictionary.
            module_name: Name of the top-level module.

        Returns:
        -------
            Generated stub file content.

        """
        content = []

        # Determine which imports are actually needed
        needed_imports = self._analyze_needed_imports(hierarchy)

        # Add header based on output format
        if self.options.output_format == "py":
            imports = []
            # Combine typing imports with TYPE_CHECKING first
            typing_imports = ["TYPE_CHECKING"]
            if needed_imports["typing"]:
                typing_imports.extend(sorted(needed_imports['typing']))
            imports.append(f"from typing import {', '.join(typing_imports)}")

            if needed_imports["cocotb"]:
                imports.append("")  # Blank line between import modules
                cocotb_imports = sorted(needed_imports['cocotb'])
                if len(cocotb_imports) == 1:
                    imports.append(f"from cocotb.handle import {cocotb_imports[0]}")
                else:
                    # Format long import lists properly
                    imports.append("from cocotb.handle import (")
                    for i, imp in enumerate(cocotb_imports):
                        if i == len(cocotb_imports) - 1:
                            imports.append(f"    {imp},")
                        else:
                            imports.append(f"    {imp},")
                    imports.append(")")
            imports.extend([
                "",
                "if TYPE_CHECKING:",
                "    # Runtime implementation would be here",
                "    pass",
            ])
        else:  # pyi format
            imports = []
            # Sort imports alphabetically
            if needed_imports["cocotb"]:
                cocotb_imports = sorted(needed_imports['cocotb'])
                if len(cocotb_imports) == 1:
                    imports.append(f"from cocotb.handle import {cocotb_imports[0]}")
                else:
                    # Format long import lists properly with proper line breaks
                    imports.append("from cocotb.handle import (")
                    for imp in cocotb_imports:
                        imports.append(f"    {imp},")
                    imports.append(")")

            if needed_imports["typing"]:
                if needed_imports["cocotb"]:
                    imports.append("")  # Blank line between import modules
                typing_imports = sorted(needed_imports['typing'])
                if len(typing_imports) == 1:
                    imports.append(f"from typing import {typing_imports[0]}")
                else:
                    # Format long import lists properly with proper line breaks
                    imports.append("from typing import (")
                    for imp in typing_imports:
                        imports.append(f"    {imp},")
                    imports.append(")")

        content.append(
            self.template.render_header(
                module_name=module_name,
                imports="\n".join(imports),
                output_format=self.options.output_format,
            )
        )

        # Generate array classes if needed
        if self.options.include_arrays:
            array_classes = self._generate_array_classes(hierarchy)
            if array_classes:
                content.extend(array_classes)
                content.append("")

        # Generate main DUT class
        if self.options.flat_hierarchy:
            content.extend(self._generate_flat_hierarchy(hierarchy, module_name))
        else:
            content.extend(self._generate_nested_hierarchy(hierarchy, module_name))

        # Add type alias for the main DUT
        main_class_name = (
            f"{self.options.class_prefix}{to_capwords(module_name)}{self.options.class_suffix}"
        )
        content.append("")
        content.append("# Type alias for the main DUT")
        content.append(f"DutType = {main_class_name}")

        # Add format-specific footer
        if self.options.output_format == "py":
            content.extend([
                "",
                "# Runtime implementation would include actual signal handling",
                "# This is a stub file for type checking purposes",
            ])

        return "\n".join(content) + "\n"

    def _analyze_needed_imports(self, hierarchy: Dict[str, type]) -> Dict[str, Set[str]]:
        """Analyze which imports are actually needed based on the hierarchy.

        Args:
        ----
            hierarchy: DUT hierarchy dictionary.

        Returns:
        -------
            Dictionary with sets of needed imports by module.

        """
        needed: Dict[str, Set[str]] = {
            "typing": set(),
            "cocotb": set(),
        }

        # Always need HierarchyObject for the main class
        needed["cocotb"].add("HierarchyObject")

        # Check if we need array-related imports
        has_arrays = any(re.match(r"^.+\[\d+\]$", path) for path in hierarchy.keys())
        if has_arrays and self.options.include_arrays:
            needed["typing"].update(["Sequence", "Iterator"])

        # Check what types are actually used
        used_types = set()
        for type_ in hierarchy.values():
            if hasattr(type_, "__name__"):
                used_types.add(type_.__name__)

        # Add SimHandleBase only if it's actually used
        if "SimHandleBase" in used_types:
            needed["cocotb"].add("SimHandleBase")

        # Add other cocotb types if used
        cocotb_types = ["ModifiableObject", "LogicObject", "LogicArrayObject", "IntegerObject"]
        for cocotb_type in cocotb_types:
            if cocotb_type in used_types:
                needed["cocotb"].add(cocotb_type)

        return needed

    def _generate_array_classes(self, hierarchy: Dict[str, type]) -> List[str]:
        """Generate array support classes."""
        array_classes = []
        arrays = {}

        # Find array patterns in hierarchy
        for path, type_ in hierarchy.items():
            array_match = re.match(r"^(.+)\[(\d+)\]$", path)
            if array_match:
                base_path = array_match.group(1)
                index = int(array_match.group(2))
                if base_path not in arrays:
                    arrays[base_path] = {
                        "indices": set(),
                        "element_type": type_,
                        "min_index": index,
                        "max_index": index,
                    }
                indices_set = arrays[base_path]["indices"]
                if isinstance(indices_set, set):
                    indices_set.add(index)
                min_index = arrays[base_path]["min_index"]
                if isinstance(min_index, int):
                    arrays[base_path]["min_index"] = min(min_index, index)
                max_index = arrays[base_path]["max_index"]
                if isinstance(max_index, int):
                    arrays[base_path]["max_index"] = max(max_index, index)

        # Generate array classes
        for base_path, info in arrays.items():
            class_name = f"{to_capwords(base_path.split('.')[-1])}Array"
            element_type = info["element_type"]
            indices = info["indices"]
            min_index = info["min_index"]
            max_index = info["max_index"]

            if (
                hasattr(element_type, "__name__")
                and isinstance(indices, set)
                and isinstance(min_index, int)
                and isinstance(max_index, int)
            ):
                array_classes.append(
                    self.template.render_array(
                        class_name=class_name,
                        base_name=base_path,
                        element_type=element_type.__name__,
                        size=len(indices),
                        min_index=min_index,
                        max_index=max_index,
                    )
                )

        return array_classes

    def _generate_flat_hierarchy(self, hierarchy: Dict[str, type], module_name: str) -> List[str]:
        """Generate a flat hierarchy with all signals in one class."""
        class_name = (
            f"{self.options.class_prefix}{to_capwords(module_name)}{self.options.class_suffix}"
        )
        attributes = []

        for path, type_ in sorted(hierarchy.items()):
            # Safe way to get type name, handling Mock objects
            if hasattr(type_, '__name__'):
                type_annotation = type_.__name__
            elif hasattr(type_, '__class__'):
                type_annotation = type_.__class__.__name__
            else:
                type_annotation = str(type(type_).__name__)

            # Use HierarchyObject for Mock objects to avoid import issues
            if type_annotation == "Mock":
                type_annotation = "HierarchyObject"

            if self.options.typing_style == "legacy":
                type_annotation = f"'{type_annotation}'"

            comment = ""
            if self.options.include_metadata:
                # Keep comments short to avoid line length issues
                if len(path) > 60:
                    comment = "Signal"
                else:
                    comment = f"Signal at path: {path}"

            # Create a Python-compliant variable name by replacing dots with underscores
            # and converting to lowercase to avoid mixed case linting errors
            variable_name = path.replace(".", "_").lower()

            # Create the signal line and check length
            signal_line = self.template.render_signal(
                name=variable_name, type_annotation=type_annotation, comment=comment
            )

            # If the line is too long, use a shorter comment
            if len(signal_line) > 88:  # Standard line length limit
                comment = "Signal" if self.options.include_metadata else ""
                signal_line = self.template.render_signal(
                    name=variable_name, type_annotation=type_annotation, comment=comment
                )

            attributes.append(signal_line)

        docstring = ""
        if self.options.include_docstrings:
            docstring = f'''    """Type stub for {module_name} DUT.

    This class provides type hints for all signals in the DUT hierarchy.
    Total signals: {len(hierarchy)}
    """
'''

        # Ensure proper formatting of attributes
        attributes_content = "\n".join(attributes) + "\n" if attributes else "    pass\n"

        return [
            self.template.render_class(
                class_name=class_name, docstring=docstring, attributes=attributes_content
            )
        ]

    def _generate_nested_hierarchy(self, hierarchy: Dict[str, type], module_name: str) -> List[str]:
        """Generate a nested hierarchy with classes for each module level."""
        classes: List[str] = []

        # Analyze the hierarchy to understand the structure
        modules = self._analyze_hierarchy_structure(hierarchy, module_name)

        # Generate classes for each module in the proper order
        for module_path, module_info in sorted(modules.items()):
            class_name = self._get_class_name_for_module(module_info["name"])

            # Generate the module class
            self._generate_module_class_new(
                class_name=class_name,
                module_name=module_info["name"],
                module_path=module_path,
                signals=module_info["signals"],
                submodules=module_info["submodules"],
                classes=classes,
                is_top_level=(module_path == module_name)
            )

        return classes

    def _analyze_hierarchy_structure(
        self, hierarchy: Dict[str, type], module_name: str
    ) -> Dict[str, Dict[str, Any]]:
        """Analyze hierarchy structure and group signals by module."""
        modules: Dict[str, Dict[str, Any]] = {}

        # Based on the simulation output, we know these are the hierarchical modules:
        # - cpu_top (HierarchyObject)
        # - cpu_top.u_clock_gen (HierarchyObject)
        # - cpu_top.u_cpu_complex (HierarchyObject)
        # - cpu_top.u_cpu_complex.u_dm_arbiter (HierarchyObject)
        # - cpu_top.u_cpu_complex.u_if_arbiter (HierarchyObject)
        # - cpu_top.u_csr_block (HierarchyObject)

        # Since type information is lost during pickle serialization, we need to
        # identify hierarchical modules by analyzing the path structure
        known_hierarchical_paths: Set[str] = set()

        # Find paths that have child paths (indicating they are modules)
        all_paths = set(hierarchy.keys())
        for path in all_paths:
            # Check if any other path starts with this path + "."
            for other_path in all_paths:
                if other_path.startswith(path + ".") and other_path != path:
                    known_hierarchical_paths.add(path)
                    break

        # For each identified module path, create a module entry
        for module_path in sorted(known_hierarchical_paths):
            module_name_only = module_path.split(".")[-1]

            modules[module_path] = {
                "name": module_name_only,
                "signals": {},
                "submodules": {}
            }

            # Find signals and submodules that belong directly to this module
            for path, obj_type in hierarchy.items():
                # Check if this signal belongs directly to the current module
                if (path.startswith(module_path + ".") and
                    path.count(".") == module_path.count(".") + 1):
                    signal_name = path.split(".")[-1]
                    # Check if this is a submodule (has children)
                    if path in known_hierarchical_paths:
                        modules[module_path]["submodules"][signal_name] = obj_type
                    else:
                        modules[module_path]["signals"][signal_name] = obj_type

        # Handle the top-level module specially
        if module_name not in modules:
            modules[module_name] = {
                "name": module_name,
                "signals": {},
                "submodules": {}
            }

        # Find top-level signals and immediate submodules
        for path, obj_type in hierarchy.items():
            parts = path.split(".")
            if len(parts) == 1:
                # This is the top-level module itself
                continue
            elif len(parts) == 2 and parts[0] == module_name:
                # This is a direct child of the top module
                signal_name = parts[1]
                if path in known_hierarchical_paths:
                    modules[module_name]["submodules"][signal_name] = obj_type
                else:
                    modules[module_name]["signals"][signal_name] = obj_type

        return modules

    def _generate_module_class_new(self, class_name: str, module_name: str, module_path: str,
                                  signals: Dict[str, type], submodules: Dict[str, type],
                                  classes: List[str], is_top_level: bool = False) -> None:
        """Generate a class for a specific module with proper structure."""
        attributes = []

        # Add signals
        if signals:
            if not is_top_level:
                attributes.append("    # Module signals")
            for signal_name, obj_type in sorted(signals.items()):
                type_annotation = self._get_safe_type_annotation(obj_type)

                if self.options.typing_style == "legacy":
                    type_annotation = f"'{type_annotation}'"

                comment = ""
                if self.options.include_metadata:
                    # Keep comments short to avoid line length issues
                    if len(module_name) > 20:
                        comment = f"Signal: {signal_name}"
                    else:
                        comment = f"Signal in {module_name}: {signal_name}"

                # Ensure the line isn't too long
                signal_line = self.template.render_signal(
                    name=signal_name, type_annotation=type_annotation, comment=comment
                )

                # If the line is too long, use a shorter comment
                if len(signal_line) > 88:  # Standard line length limit
                    comment = signal_name if self.options.include_metadata else ""
                    signal_line = self.template.render_signal(
                        name=signal_name, type_annotation=type_annotation, comment=comment
                    )

                attributes.append(signal_line)

            if signals:
                attributes.append("")

        # Add sub-modules
        if submodules:
            attributes.append("    # Sub-modules")
            for sub_name, obj_type in sorted(submodules.items()):
                sub_class_name = self._get_class_name_for_module(sub_name)

                comment = ""
                if self.options.include_metadata:
                    comment = f"Sub-module: {sub_name}"

                # Ensure the line isn't too long
                submodule_line = self.template.render_signal(
                    name=sub_name, type_annotation=sub_class_name, comment=comment
                )

                # If the line is too long, use a shorter comment
                if len(submodule_line) > 88:  # Standard line length limit
                    comment = sub_name if self.options.include_metadata else ""
                    submodule_line = self.template.render_signal(
                        name=sub_name, type_annotation=sub_class_name, comment=comment
                    )

                attributes.append(submodule_line)

            if submodules:
                attributes.append("")

        # Generate docstring
        docstring = ""
        if self.options.include_docstrings:
            if is_top_level:
                description = (
                    f"Type stub for {module_name} module.\n\n"
                    "    This class provides type hints for the top-level DUT."
                )
            else:
                description = (
                    f"Type stub for {module_name} sub-module.\n\n"
                    f"    This class provides type hints for signals in the "
                    f"{module_name} sub-module."
                )

            docstring = f'''    """{description}

    Top-level signals: {len(signals)}
    Sub-modules: {len(submodules)}
    """
'''

        # Generate the class
        if attributes or is_top_level:
            # Clean up attributes to ensure proper formatting
            if attributes:
                attributes_content = "\n".join(attributes)
                # Remove any trailing empty lines
                attributes_content = attributes_content.rstrip() + "\n"
            else:
                attributes_content = "    pass\n"

            classes.append(
                self.template.render_class(
                    class_name=class_name,
                    docstring=docstring,
                    attributes=attributes_content
                )
            )

    def _get_class_name_for_module(self, module_name: str) -> str:
        """Generate an appropriate class name for a module."""
        # Remove common prefixes and convert to CamelCase
        clean_name = module_name
        if clean_name.startswith("u_"):
            clean_name = clean_name[2:]  # Remove "u_" prefix
        return to_capwords(clean_name)

    def _is_hierarchical_type(self, obj_type: type) -> bool:
        """Determine if a type represents a hierarchical module."""
        # First check if it's actually a HierarchyObject class/type
        try:
            from cocotb.handle import HierarchyObject as CocotbHierarchyObject
            if (obj_type == CocotbHierarchyObject or
                (hasattr(obj_type, '__bases__') and
                 CocotbHierarchyObject in obj_type.__bases__)):
                return True
        except ImportError:
            pass

        # Fallback to string-based checking
        if hasattr(obj_type, '__name__'):
            type_name = obj_type.__name__
            return type_name in ["HierarchyObject", "ModifiableObject"] or "Hierarchy" in type_name

        return False

    def _get_safe_type_annotation(self, obj_type: type) -> str:
        """Get a safe type annotation string, handling Mock objects and unknown types."""
        if hasattr(obj_type, '__name__'):
            type_annotation = obj_type.__name__
        elif hasattr(obj_type, '__class__'):
            type_annotation = obj_type.__class__.__name__
        else:
            type_annotation = str(type(obj_type).__name__)

        # Map known cocotb types
        known_types = {
            "HierarchyObject": "HierarchyObject",
            "SimHandleBase": "SimHandleBase",
            "LogicObject": "SimHandleBase",
            "LogicArrayObject": "SimHandleBase",
            "IntegerObject": "SimHandleBase",
            "RealObject": "SimHandleBase",
            "StringObject": "SimHandleBase",
            "ModifiableObject": "SimHandleBase"
        }

        # Use SimHandleBase for Mock objects and unknown types, but preserve HierarchyObject
        if type_annotation == "Mock":
            return "SimHandleBase"
        elif type_annotation == "HierarchyObject":
            return "HierarchyObject"
        elif type_annotation not in known_types:
            return "SimHandleBase"

        return known_types.get(type_annotation, "SimHandleBase")


class StubTemplate:
    """Template system for generating customizable stub files."""

    def __init__(self, template_name: str = "default"):
        """Initialize stub template.

        Args:
        ----
            template_name: Name of the template to use.

        """
        self.template_name = template_name
        self.header_template = self._get_header_template()
        self.class_template = self._get_class_template()
        self.signal_template = self._get_signal_template()
        self.array_template = self._get_array_template()

    def _get_header_template(self) -> str:
        """Get the header template for stub files."""
        return '''# This is an auto-generated stub file for cocotb testbench
# Generated by copra v{version} at {timestamp}
# Template: {template_name}
"""Auto-generated type stubs for cocotb DUT.

This file provides type hints for IDE autocompletion and static type checking.
Generated from DUT hierarchy analysis using copra.

Usage:
    from typing import cast
    from {module_name} import DutType

    @cocotb.test()
    async def test_example(dut):
        typed_dut = cast(DutType, dut)
        # Now you have full IDE support for dut.signal_name
"""

{imports}
'''

    def _get_class_template(self) -> str:
        """Get the class template for module definitions."""
        return """class {class_name}(HierarchyObject):
{docstring}
{attributes}
"""

    def _get_signal_template(self) -> str:
        """Get the template for signal attributes."""
        return "    {name}: {type_annotation}  # {comment}"

    def _get_array_template(self) -> str:
        """Get the template for array class definitions."""
        return '''class {class_name}(Sequence[{element_type}]):
    """Array access for {base_name} with {size} elements.

    This class provides sequence-like access to array elements in the DUT.
    Index range: [{min_index}:{max_index}]
    """

    def __getitem__(self, index: int) -> {element_type}:
        """Get array element by index."""
        if not ({min_index} <= index <= {max_index}):
            raise IndexError(
                f"Array index {{index}} out of bounds [{min_index}:{max_index}]"
            )
        raise NotImplementedError("This is a type stub - use the actual DUT object")

    def __len__(self) -> int:
        """Get array length."""
        return {size}

    def __iter__(self) -> Iterator[{element_type}]:
        """Iterate over array elements."""
        for i in range({min_index}, {max_index} + 1):
            yield self[i]

    def __contains__(self, item: object) -> bool:
        """Check if item is in the array."""
        try:
            for element in self:
                if element == item:
                    return True
            return False
        except NotImplementedError:
            return False

    @property
    def min_index(self) -> int:
        """Get minimum valid index."""
        return {min_index}

    @property
    def max_index(self) -> int:
        """Get maximum valid index."""
        return {max_index}
'''

    def render_header(self, **kwargs: Any) -> str:
        """Render the header template with provided variables."""
        defaults = {
            "version": __version__,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "template_name": self.template_name,
            "module_name": "dut",
            "imports": "from cocotb.handle import HierarchyObject",
            "output_format": "pyi",
        }
        defaults.update(kwargs)

        # Modify header based on output format
        if defaults.get("output_format") == "py":
            header_comment = "# This is an auto-generated Python module for cocotb testbench"
        else:
            header_comment = "# This is an auto-generated stub file for cocotb testbench"

        # Replace the first line in the template
        header_content = self.header_template.format(**defaults)
        lines = header_content.split("\n")
        if lines:
            lines[0] = header_comment

        # Clean up lines to ensure no trailing whitespace
        cleaned_lines = [line.rstrip() for line in lines]

        return "\n".join(cleaned_lines)

    def render_class(self, **kwargs: Any) -> str:
        """Render a class template with provided variables."""
        result = self.class_template.format(**kwargs)
        # Clean up any extra blank lines and ensure proper formatting
        lines = result.split('\n')
        cleaned_lines = []
        for line in lines:
            cleaned_lines.append(line.rstrip())

        # Ensure the class ends with exactly one blank line
        while cleaned_lines and not cleaned_lines[-1]:
            cleaned_lines.pop()
        cleaned_lines.append("")

        return "\n".join(cleaned_lines)

    def render_signal(self, **kwargs: Any) -> str:
        """Render a signal template with provided variables."""
        # Handle empty comments gracefully
        comment = kwargs.get('comment', '')
        if comment:
            return f"    {kwargs['name']}: {kwargs['type_annotation']}  # {comment}"
        else:
            return f"    {kwargs['name']}: {kwargs['type_annotation']}"

    def render_array(self, **kwargs: Any) -> str:
        """Render an array template with provided variables."""
        result = self.array_template.format(**kwargs)
        # Clean up any trailing whitespace and ensure proper formatting
        lines = result.split('\n')
        cleaned_lines = [line.rstrip() for line in lines]

        # Ensure the class ends with exactly one blank line
        while cleaned_lines and not cleaned_lines[-1]:
            cleaned_lines.pop()
        cleaned_lines.append("")

        return "\n".join(cleaned_lines)


class DocumentationGenerator:
    """Generate comprehensive documentation for DUT hierarchies."""

    def __init__(self, format_type: str = "markdown"):
        """Initialize documentation generator.

        Args:
        ----
            format_type: Output format ('markdown', 'rst', 'html').

        """
        self.format_type = format_type

    def generate_interface_documentation(
        self, hierarchy: Dict[str, type], output_file: Optional[str] = None
    ) -> str:
        """Generate interface documentation from hierarchy.

        Args:
        ----
            hierarchy: DUT hierarchy dictionary.
            output_file: Optional output file path.

        Returns:
        -------
            Generated documentation content.

        """
        if self.format_type == "markdown":
            return self._generate_markdown_docs(hierarchy, output_file)
        elif self.format_type == "rst":
            return self._generate_rst_docs(hierarchy, output_file)
        elif self.format_type == "html":
            return self._generate_html_docs(hierarchy, output_file)
        else:
            raise ValueError(f"Unsupported format: {self.format_type}")

    def _generate_markdown_docs(
        self,
        hierarchy: Dict[str, type],
        output_file: Optional[str] = None,
    ) -> str:
        """Generate Markdown documentation."""
        lines = [
            "# DUT Interface Documentation",
            "",
            f"Generated at: {time.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Overview",
            "",
            f"This document describes the interface of the Device Under Test (DUT) "
            f"with {len(hierarchy)} total objects in the hierarchy.",
            "",
            "## Hierarchy Structure",
            "",
        ]

        # Group by modules
        modules: Dict[str, List[Tuple[str, type]]] = {}
        signals: Dict[str, type] = {}

        for path, obj_type in hierarchy.items():
            if "." in path:
                module_path = ".".join(path.split(".")[:-1])
                signal_name = path.split(".")[-1]
                if module_path not in modules:
                    modules[module_path] = []
                modules[module_path].append((signal_name, obj_type))
            else:
                signals[path] = obj_type

        # Document top-level signals
        if signals:
            lines.extend(
                [
                    "### Top-Level Signals",
                    "",
                    "| Signal Name | Type | Description |",
                    "|-------------|------|-------------|",
                ]
            )

            for signal_name, obj_type in sorted(signals.items()):
                # Safe way to get type name, handling Mock objects
                if hasattr(obj_type, '__name__'):
                    type_name = obj_type.__name__
                elif hasattr(obj_type, '__class__'):
                    type_name = obj_type.__class__.__name__
                else:
                    type_name = str(type(obj_type).__name__)
                description = f"{type_name} signal"
                lines.append(f"| `{signal_name}` | {type_name} | {description} |")

            lines.append("")

        # Document modules
        for module_path, module_signals in sorted(modules.items()):
            lines.extend(
                [
                    f"### Module: `{module_path}`",
                    "",
                    "| Signal Name | Type | Description |",
                    "|-------------|------|-------------|",
                ]
            )

            for signal_name, obj_type in sorted(module_signals):
                # Safe way to get type name, handling Mock objects
                if hasattr(obj_type, '__name__'):
                    type_name = obj_type.__name__
                elif hasattr(obj_type, '__class__'):
                    type_name = obj_type.__class__.__name__
                else:
                    type_name = str(type(obj_type).__name__)
                description = f"{type_name} signal"
                lines.append(f"| `{signal_name}` | {type_name} | {description} |")

            lines.append("")

        content = "\n".join(lines)

        if output_file:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(content)

        return content

    def _generate_rst_docs(
        self,
        hierarchy: Dict[str, type],
        output_file: Optional[str] = None,
    ) -> str:
        """Generate reStructuredText documentation."""
        lines = [
            "DUT Interface Documentation",
            "===========================",
            "",
            f"Generated at: {time.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "Overview",
            "--------",
            "",
            f"This document describes the interface of the Device Under Test (DUT) "
            f"with {len(hierarchy)} total objects in the hierarchy.",
            "",
        ]

        # Add hierarchy information in RST format
        for path, obj_type in sorted(hierarchy.items()):
            # Safe way to get type name, handling Mock objects
            if hasattr(obj_type, '__name__'):
                type_name = obj_type.__name__
            elif hasattr(obj_type, '__class__'):
                type_name = obj_type.__class__.__name__
            else:
                type_name = str(type(obj_type).__name__)
            lines.extend(
                [f"``{path}``", "^" * (len(path) + 4), "", f"Type: {type_name}", ""]
            )

        content = "\n".join(lines)

        if output_file:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(content)

        return content

    def _generate_html_docs(
        self,
        hierarchy: Dict[str, type],
        output_file: Optional[str] = None,
    ) -> str:
        """Generate HTML documentation."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        hierarchy_count = len(hierarchy)

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DUT Interface Documentation</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        .hierarchy {{ margin-left: 20px; }}
        .signal {{ color: #0066cc; }}
        .module {{ color: #cc6600; font-weight: bold; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
    <h1>DUT Interface Documentation</h1>
    <p>Generated at: {timestamp}</p>

    <h2>Overview</h2>
    <p>This document describes the interface of the Device Under Test (DUT)
       with {hierarchy_count} total objects in the hierarchy.</p>

    <h2>Hierarchy</h2>
    <table>
        <tr>
            <th>Path</th>
            <th>Type</th>
            <th>Category</th>
        </tr>
"""

        for path, obj_type in sorted(hierarchy.items()):
            # Safe way to get type name, handling Mock objects
            if hasattr(obj_type, '__name__'):
                type_name = obj_type.__name__
            elif hasattr(obj_type, '__class__'):
                type_name = obj_type.__class__.__name__
            else:
                type_name = str(type(obj_type).__name__)
            category = "Module" if "Hierarchy" in type_name else "Signal"
            html_content += f"""        <tr>
            <td><code>{path}</code></td>
            <td>{type_name}</td>
            <td>{category}</td>
        </tr>
"""

        html_content += """    </table>
</body>
</html>"""

        if output_file:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(html_content)

        return html_content


def generate_testbench_template(
    hierarchy_or_dut: Union[Dict[str, type], Any], output_file: Optional[str] = None
) -> str:
    """Generate a testbench template with proper typing.

    Args:
    ----
        hierarchy_or_dut: Either a DUT hierarchy dictionary or a DUT object.
        output_file: Optional output file path. If provided, generates comprehensive template.

    Returns:
    -------
        Generated testbench template code.

    """
    # Handle both dictionary and DUT object inputs
    if isinstance(hierarchy_or_dut, dict):
        hierarchy = hierarchy_or_dut
        dut_name = "dut"
    else:
        # Assume it's a DUT object, discover its hierarchy
        from .core import discover_hierarchy

        hierarchy = discover_hierarchy(hierarchy_or_dut)
        dut_name = getattr(hierarchy_or_dut, "_name", "dut")

    # Determine test name from output file or use default
    if output_file:
        test_name = Path(output_file).stem if output_file != "test.py" else dut_name
        # Generate comprehensive template
        template = _generate_comprehensive_template(hierarchy, dut_name, test_name)

        # Write to file if output_file is provided
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(template)
    else:
        # Generate simple template (backward compatibility)
        test_name = "test_dut"
        template = _generate_simple_template(hierarchy, test_name)

    return template


def _generate_simple_template(hierarchy: Dict[str, type], test_name: str) -> str:
    """Generate a simple testbench template."""
    # Find DUT signals (signals that are direct children of the DUT)
    dut_signals = []
    for path in hierarchy.keys():
        # Look for signals that are direct children of 'dut' (e.g., 'dut.clk', 'dut.rst_n')
        if path.startswith("dut.") and path.count(".") == 1:
            signal_name = path.split(".")[1]  # Extract signal name after 'dut.'
            dut_signals.append(signal_name)

    # If no DUT signals found, look for any top-level signals
    if not dut_signals:
        dut_signals = [path for path in hierarchy.keys() if "." not in path and path != "dut"]

    # Sort imports and only include what's needed
    template = f'''"""Auto-generated testbench template.

This template provides a starting point for writing cocotb tests with
proper type hints and IDE support.
"""

from typing import cast

import cocotb
from cocotb.triggers import Timer

# Import the generated DUT type
from dut import DutType


@cocotb.test()
async def {test_name}(dut):
    """Test the DUT functionality.

    Args:
    ----
        dut: The DUT instance from cocotb.

    """
    # Cast to typed DUT for IDE support
    typed_dut = cast(DutType, dut)

    # Initialize signals
'''

    # Add initialization for common signals
    for signal in dut_signals[:5]:  # Limit to first 5 signals
        if "clk" in signal.lower() or "clock" in signal.lower():
            template += f"    typed_dut.{signal}.value = 0\n"
        elif "rst" in signal.lower() or "reset" in signal.lower():
            template += f"    typed_dut.{signal}.value = 1  # Assert reset\n"
        else:
            template += f"    typed_dut.{signal}.value = 0\n"

    # If no signals found, add a default initialization
    if not dut_signals:
        template += "    typed_dut.dut.value = 0\n"

    template += """
    # Wait for a few clock cycles
    for _ in range(10):
        await Timer(10, units='ns')

    # Add your test logic here
    # Example: Check signal values, drive inputs, verify outputs

    # Log test completion
    dut._log.info("Test completed successfully")
"""

    return template


def _generate_comprehensive_template(
    hierarchy: Dict[str, type], dut_name: str, test_name: str
) -> str:
    """Generate a comprehensive testbench template with class structure."""
    # Find all signals
    signals = []
    clock_signals = []
    reset_signals = []

    for path in hierarchy.keys():
        if "." in path:
            parts = path.split(".")
            if len(parts) == 2 and parts[0] == dut_name:
                signal_name = parts[1]
                signals.append(signal_name)

                # Detect clock and reset signals
                if "clk" in signal_name.lower() or "clock" in signal_name.lower():
                    clock_signals.append(signal_name)
                elif "rst" in signal_name.lower() or "reset" in signal_name.lower():
                    reset_signals.append(signal_name)

    # Use defaults if no clock/reset detected
    if not clock_signals:
        clock_signals = ["clk"]
    if not reset_signals:
        reset_signals = ["rst_n"]

    # Generate class name
    class_name = to_capwords(dut_name) + "TestBench"
    # ruff: noqa
    template = f'''"""Auto-generated testbench for {dut_name}.

This testbench provides comprehensive test coverage with proper
clock and reset handling, multiple test scenarios, and TestFactory integration.
"""

from typing import Any, cast

import cocotb
from cocotb.clock import Clock
from cocotb.regression import TestFactory
from cocotb.triggers import ClockCycles

# Import the generated DUT type
from dut import DutType


class {class_name}:
    """Testbench class for {dut_name}."""

    def __init__(self, dut: Any):
        """Initialize testbench.

        Args:
        ----
            dut: The DUT instance from cocotb.

        """
        self.dut = cast(DutType, dut)
        self.clock_period = 10  # ns

    async def setup_clock(self):
        """Set up clock generation."""
        clock = Clock(self.dut.{clock_signals[0]}, self.clock_period, units="ns")
        cocotb.start_soon(clock.start())

    async def reset_dut(self):
        """Reset the DUT."""
        # Assert reset
        self.dut.{reset_signals[0]}.value = 0
        await ClockCycles(self.dut.{clock_signals[0]}, 5)

        # Deassert reset
        self.dut.{reset_signals[0]}.value = 1
        await ClockCycles(self.dut.{clock_signals[0]}, 5)


# Signal list for reference:
'''

    # Add signal documentation
    for signal in signals:
        template += f"# - dut.{signal}\n"

    template += f'''

@cocotb.test()
async def test_{dut_name}_reset(dut):
    """Test reset functionality."""
    tb = {class_name}(dut)
    await tb.setup_clock()
    await tb.reset_dut()

    # Verify reset state
    # Add your reset verification logic here

    dut._log.info("Reset test completed")


@cocotb.test()
async def test_{dut_name}_basic_operation(dut):
    """Test basic operation."""
    tb = {class_name}(dut)
    await tb.setup_clock()
    await tb.reset_dut()

    # Add your basic operation test logic here
    await ClockCycles(dut.{clock_signals[0]}, 10)

    dut._log.info("Basic operation test completed")


@cocotb.test()
async def test_{dut_name}_edge_cases(dut):
    """Test edge cases."""
    tb = {class_name}(dut)
    await tb.setup_clock()
    await tb.reset_dut()

    # Add your edge case test logic here
    await ClockCycles(dut.{clock_signals[0]}, 20)

    dut._log.info("Edge cases test completed")


async def run_random_test(dut, iterations: int = 100):
    """Run randomized test."""
    tb = {class_name}(dut)
    await tb.setup_clock()
    await tb.reset_dut()

    for i in range(iterations):
        # Add your randomized test logic here
        await ClockCycles(dut.{clock_signals[0]}, 1)

        if i % 10 == 0:
            dut._log.info(f"Random test iteration {{i}}/{{iterations}}")

    dut._log.info(f"Random test completed ({{iterations}} iterations)")


# TestFactory for parameterized tests
factory = TestFactory(run_random_test)
factory.add_option("iterations", [10, 50, 100])
factory.generate_tests()
'''

    return template


# Legacy function for backward compatibility
def generate_interface_documentation(
    dut: HierarchyObject, output_file: Optional[str] = "interface.dutdoc.md"
) -> str:
    """Generate markdown documentation for the DUT interface.

    Args:
    ----
        dut: The DUT object to document.
        output_file: Path to write the documentation to.

    Returns:
    -------
        Generated documentation content as a string.

    """
    hierarchy = discover_hierarchy(dut)

    # Organize signals by type and hierarchy
    signals_by_type: Dict[str, List[str]] = {}
    for path, obj_type in hierarchy.items():
        type_name = obj_type.__name__
        if type_name not in signals_by_type:
            signals_by_type[type_name] = []
        signals_by_type[type_name].append(path)

    doc_content = f"""# {dut._name} Interface Documentation

Auto-generated interface documentation for the {dut._name} module.

## Overview

This document describes the complete interface of the {dut._name} module,
including all signals, their types, and hierarchical organization.

## Signal Summary

| Signal Type | Count |
|-------------|-------|
"""

    for signal_type, signals in signals_by_type.items():
        doc_content += f"| {signal_type} | {len(signals)} |\n"

    doc_content += f"\n**Total Signals:** {len(hierarchy)}\n\n"

    # Document each signal type
    for signal_type, signals in sorted(signals_by_type.items()):
        doc_content += f"## {signal_type} Signals\n\n"

        for signal in sorted(signals):
            # Determine signal direction and purpose based on naming conventions
            direction = "Unknown"
            if any(pattern in signal.lower() for pattern in ["in", "input"]):
                direction = "Input"
            elif any(pattern in signal.lower() for pattern in ["out", "output"]):
                direction = "Output"
            elif any(pattern in signal.lower() for pattern in ["clk", "clock"]):
                direction = "Clock"
            elif any(pattern in signal.lower() for pattern in ["rst", "reset"]):
                direction = "Reset"

            doc_content += f"### `{signal}`\n\n"
            doc_content += f"- **Type:** {signal_type}\n"
            doc_content += f"- **Direction:** {direction}\n"
            doc_content += f"- **Hierarchy Level:** {signal.count('.') + 1}\n\n"

    # Write documentation to file
    if output_file is not None:
        doc_path = Path(output_file)
        doc_path.parent.mkdir(parents=True, exist_ok=True)

        with open(doc_path, "w", encoding="utf-8") as f:
            f.write(doc_content)

        print(f"[copra] Generated interface documentation: {doc_path}")
    else:
        print("[copra] Generated interface documentation (no file output)")

    return doc_content
