# Copyright cocotb contributors
# Licensed under the Revised BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-3-Clause

"""Enhanced code generation utilities for copra.

This module provides template-based generation capabilities and enhanced
documentation generation as specified in the design document.
"""

import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Sequence, Iterator
from dataclasses import dataclass
import re

from cocotb.handle import HierarchyObject

from .core import discover_hierarchy
from .utils import to_capwords
from ._version import __version__


@dataclass
class StubGenerationOptions:
    """Configuration options for stub generation.

    Args:
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
            options: Configuration options for stub generation.
        """
        self.options = options or StubGenerationOptions()
        self.template = StubTemplate()

    def generate_stub(self, hierarchy: Dict[str, type], module_name: str) -> str:
        """Generate a type stub from a hierarchy dictionary.

        Args:
            hierarchy: DUT hierarchy dictionary.
            module_name: Name of the top-level module.

        Returns:
            Generated stub file content.
        """
        content = []

        # Add header based on output format
        if self.options.output_format == "py":
            imports = [
                "from typing import Sequence, Iterator, cast, TYPE_CHECKING",
                "from cocotb.handle import HierarchyObject",
                "",
                "if TYPE_CHECKING:",
                "    # Runtime implementation would be here",
                "    pass",
            ]
        else:  # pyi format
            imports = [
                "from typing import Sequence, Iterator, cast",
                "from cocotb.handle import HierarchyObject",
            ]
        
        content.append(self.template.render_header(
            module_name=module_name,
            imports="\n".join(imports),
            output_format=self.options.output_format
        ))

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

        # Add format-specific footer
        if self.options.output_format == "py":
            content.append("")
            content.append("# Runtime implementation would include actual signal handling")
            content.append("# This is a stub file for type checking purposes")

        return "\n".join(content)

    def _generate_array_classes(self, hierarchy: Dict[str, type]) -> List[str]:
        """Generate array support classes."""
        array_classes = []
        arrays = {}

        # Find array patterns in hierarchy
        for path, type_ in hierarchy.items():
            array_match = re.match(r'^(.+)\[(\d+)\]$', path)
            if array_match:
                base_path = array_match.group(1)
                index = int(array_match.group(2))
                if base_path not in arrays:
                    arrays[base_path] = {
                        'indices': set(),
                        'element_type': type_,
                        'min_index': index,
                        'max_index': index
                    }
                arrays[base_path]['indices'].add(index)
                arrays[base_path]['min_index'] = min(arrays[base_path]['min_index'], index)
                arrays[base_path]['max_index'] = max(arrays[base_path]['max_index'], index)

        # Generate array classes
        for base_path, info in arrays.items():
            class_name = f"{to_capwords(base_path.split('.')[-1])}Array"
            array_classes.append(self.template.render_array(
                class_name=class_name,
                base_name=base_path,
                element_type=info['element_type'].__name__,
                size=len(info['indices']),
                min_index=info['min_index'],
                max_index=info['max_index']
            ))

        return array_classes

    def _generate_flat_hierarchy(self, hierarchy: Dict[str, type], module_name: str) -> List[str]:
        """Generate a flat hierarchy with all signals in one class."""
        class_name = f"{self.options.class_prefix}{to_capwords(module_name)}{self.options.class_suffix}"
        attributes = []

        for path, type_ in sorted(hierarchy.items()):
            type_annotation = type_.__name__
            if self.options.typing_style == "legacy":
                type_annotation = f"'{type_annotation}'"

            comment = ""
            if self.options.include_metadata:
                comment = f"Signal at path: {path}"

            attributes.append(self.template.render_signal(
                name=path.replace(".", "_"),
                type_annotation=type_annotation,
                comment=comment
            ))

        docstring = ""
        if self.options.include_docstrings:
            docstring = f'''    """Type stub for {module_name} DUT.

    This class provides type hints for all signals in the DUT hierarchy.
    Total signals: {len(hierarchy)}
    """
'''

        return [self.template.render_class(
            class_name=class_name,
            docstring=docstring,
            attributes="\n".join(attributes)
        )]

    def _generate_nested_hierarchy(self, hierarchy: Dict[str, type], module_name: str) -> List[str]:
        """Generate a nested hierarchy with classes for each module."""
        # Group signals by module
        modules = {}
        for path, type_ in hierarchy.items():
            parts = path.split(".")
            if len(parts) == 1:
                if "" not in modules:
                    modules[""] = {}
                modules[""][parts[0]] = type_
            else:
                module = ".".join(parts[:-1])
                if module not in modules:
                    modules[module] = {}
                modules[module][parts[-1]] = type_

        # Generate classes for each module
        classes = []
        for module_path, signals in sorted(modules.items()):
            if module_path == "":
                class_name = f"{self.options.class_prefix}{to_capwords(module_name)}{self.options.class_suffix}"
            else:
                class_name = f"{self.options.class_prefix}{to_capwords(module_path.split('.')[-1])}{self.options.class_suffix}"

            attributes = []
            for name, type_ in sorted(signals.items()):
                type_annotation = type_.__name__
                if self.options.typing_style == "legacy":
                    type_annotation = f"'{type_annotation}'"

                comment = ""
                if self.options.include_metadata:
                    full_path = f"{module_path}.{name}" if module_path else name
                    comment = f"Signal at path: {full_path}"

                attributes.append(self.template.render_signal(
                    name=name,
                    type_annotation=type_annotation,
                    comment=comment
                ))

            docstring = ""
            if self.options.include_docstrings:
                docstring = f'''    """Type stub for {module_path if module_path else module_name} module.

    This class provides type hints for signals in this module.
    Total signals: {len(signals)}
    """
'''

            classes.append(self.template.render_class(
                class_name=class_name,
                docstring=docstring,
                attributes="\n".join(attributes)
            ))

        return classes


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
        return '''class {class_name}(HierarchyObject):
{docstring}
{attributes}
'''

    def _get_signal_template(self) -> str:
        """Get the template for signal attributes."""
        return '    {name}: {type_annotation}  # {comment}'

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
            raise IndexError(f"Array index {{index}} out of bounds [{min_index}:{max_index}]")
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

    def render_header(self, **kwargs) -> str:
        """Render the header template with provided variables."""
        from ._version import __version__

        defaults = {
            'version': __version__,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'template_name': self.template_name,
            'module_name': 'dut',
            'imports': 'from cocotb.handle import HierarchyObject',
            'output_format': 'pyi'
        }
        defaults.update(kwargs)

        # Modify header based on output format
        if defaults.get('output_format') == 'py':
            header_comment = "# This is an auto-generated Python module for cocotb testbench"
        else:
            header_comment = "# This is an auto-generated stub file for cocotb testbench"

        # Replace the first line in the template
        header_content = self.header_template.format(**defaults)
        lines = header_content.split('\n')
        if lines:
            lines[0] = header_comment
        
        return '\n'.join(lines)

    def render_class(self, **kwargs) -> str:
        """Render a class template with provided variables."""
        return self.class_template.format(**kwargs)

    def render_signal(self, **kwargs) -> str:
        """Render a signal template with provided variables."""
        return self.signal_template.format(**kwargs)

    def render_array(self, **kwargs) -> str:
        """Render an array template with provided variables."""
        return self.array_template.format(**kwargs)


class DocumentationGenerator:
    """Generate comprehensive documentation for DUT hierarchies."""

    def __init__(self, format_type: str = "markdown"):
        """Initialize documentation generator.

        Args:
        ----
            format_type: Output format ('markdown', 'rst', 'html').

        """
        self.format_type = format_type

    def generate_interface_documentation(self, hierarchy: Dict[str, type],
                                       output_file: str = None) -> str:
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

    def _generate_markdown_docs(self, hierarchy: Dict[str, type],
                               output_file: str = None) -> str:
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
            ""
        ]

        # Group by modules
        modules = {}
        signals = {}

        for path, obj_type in hierarchy.items():
            if '.' in path:
                module_path = '.'.join(path.split('.')[:-1])
                signal_name = path.split('.')[-1]
                if module_path not in modules:
                    modules[module_path] = []
                modules[module_path].append((signal_name, obj_type))
            else:
                signals[path] = obj_type

        # Document top-level signals
        if signals:
            lines.extend([
                "### Top-Level Signals",
                "",
                "| Signal Name | Type | Description |",
                "|-------------|------|-------------|"
            ])

            for signal_name, obj_type in sorted(signals.items()):
                type_name = obj_type.__name__
                description = f"{type_name} signal"
                lines.append(f"| `{signal_name}` | {type_name} | {description} |")

            lines.append("")

        # Document modules
        for module_path, module_signals in sorted(modules.items()):
            lines.extend([
                f"### Module: `{module_path}`",
                "",
                "| Signal Name | Type | Description |",
                "|-------------|------|-------------|"
            ])

            for signal_name, obj_type in sorted(module_signals):
                type_name = obj_type.__name__
                description = f"{type_name} signal"
                lines.append(f"| `{signal_name}` | {type_name} | {description} |")

            lines.append("")

        content = "\n".join(lines)

        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(content)

        return content

    def _generate_rst_docs(self, hierarchy: Dict[str, type],
                          output_file: str = None) -> str:
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
            ""
        ]

        # Add hierarchy information in RST format
        for path, obj_type in sorted(hierarchy.items()):
            lines.extend([
                f"``{path}``",
                "^" * (len(path) + 4),
                "",
                f"Type: {obj_type.__name__}",
                ""
            ])

        content = "\n".join(lines)

        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(content)

        return content

    def _generate_html_docs(self, hierarchy: Dict[str, type],
                           output_file: str = None) -> str:
        """Generate HTML documentation."""
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
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
            category = "Module" if "Hierarchy" in obj_type.__name__ else "Signal"
            html_content += f"""        <tr>
            <td><code>{path}</code></td>
            <td>{obj_type.__name__}</td>
            <td>{category}</td>
        </tr>
"""

        html_content += """    </table>
</body>
</html>"""

        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html_content)

        return html_content


def generate_testbench_template(hierarchy_or_dut: Union[Dict[str, type], Any],
                               output_file: Optional[str] = None) -> str:
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
        dut_name = getattr(hierarchy_or_dut, '_name', 'dut')

    # Determine test name from output file or use default
    if output_file:
        test_name = Path(output_file).stem if output_file != "test.py" else dut_name
        # Generate comprehensive template
        template = _generate_comprehensive_template(hierarchy, dut_name, test_name)

        # Write to file if output_file is provided
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
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
        if path.startswith('dut.') and path.count('.') == 1:
            signal_name = path.split('.')[1]  # Extract signal name after 'dut.'
            dut_signals.append(signal_name)

    # If no DUT signals found, look for any top-level signals
    if not dut_signals:
        dut_signals = [
            path for path in hierarchy.keys()
            if '.' not in path and path != 'dut'
        ]

    template = f'''"""Auto-generated testbench template.

This template provides a starting point for writing cocotb tests with
proper type hints and IDE support.
"""

import cocotb
from cocotb.triggers import Timer, RisingEdge, FallingEdge
from typing import cast

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
        if 'clk' in signal.lower() or 'clock' in signal.lower():
            template += f"    typed_dut.{signal}.value = 0\n"
        elif 'rst' in signal.lower() or 'reset' in signal.lower():
            template += f"    typed_dut.{signal}.value = 1  # Assert reset\n"
        else:
            template += f"    typed_dut.{signal}.value = 0\n"

    # If no signals found, add a default initialization
    if not dut_signals:
        template += "    typed_dut.dut.value = 0\n"

    template += '''
    # Wait for a few clock cycles
    for _ in range(10):
        await Timer(10, units='ns')

    # Add your test logic here
    # Example: Check signal values, drive inputs, verify outputs

    # Log test completion
    dut._log.info("Test completed successfully")
'''

    return template


def _generate_comprehensive_template(hierarchy: Dict[str, type],
                                   dut_name: str, test_name: str) -> str:
    """Generate a comprehensive testbench template with class structure."""
    # Find all signals
    signals = []
    clock_signals = []
    reset_signals = []

    for path in hierarchy.keys():
        if '.' in path:
            parts = path.split('.')
            if len(parts) == 2 and parts[0] == dut_name:
                signal_name = parts[1]
                signals.append(signal_name)

                # Detect clock and reset signals
                if 'clk' in signal_name.lower() or 'clock' in signal_name.lower():
                    clock_signals.append(signal_name)
                elif 'rst' in signal_name.lower() or 'reset' in signal_name.lower():
                    reset_signals.append(signal_name)

    # Use defaults if no clock/reset detected
    if not clock_signals:
        clock_signals = ['clk']
    if not reset_signals:
        reset_signals = ['rst_n']

    # Generate class name
    class_name = to_capwords(dut_name) + "TestBench"

    template = f'''"""Auto-generated testbench for {dut_name}.

This testbench provides comprehensive test coverage with proper
clock and reset handling, multiple test scenarios, and TestFactory integration.
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import Timer, RisingEdge, FallingEdge, ClockCycles
from cocotb.regression import TestFactory
from typing import cast, Any

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
    dut: HierarchyObject,
    output_file: str = "interface.dutdoc.md"
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
            if any(pattern in signal.lower() for pattern in ['in', 'input']):
                direction = "Input"
            elif any(pattern in signal.lower() for pattern in ['out', 'output']):
                direction = "Output"
            elif any(pattern in signal.lower() for pattern in ['clk', 'clock']):
                direction = "Clock"
            elif any(pattern in signal.lower() for pattern in ['rst', 'reset']):
                direction = "Reset"

            doc_content += f"### `{signal}`\n\n"
            doc_content += f"- **Type:** {signal_type}\n"
            doc_content += f"- **Direction:** {direction}\n"
            doc_content += f"- **Hierarchy Level:** {signal.count('.') + 1}\n\n"

    # Write documentation to file
    doc_path = Path(output_file)
    doc_path.parent.mkdir(parents=True, exist_ok=True)

    with open(doc_path, 'w', encoding='utf-8') as f:
        f.write(doc_content)

    print(f"[copra] Generated interface documentation: {doc_path}")
    return doc_content
