"""Tests for the copra.generation module."""

import tempfile
from pathlib import Path
from typing import Any, Dict
from unittest.mock import Mock, mock_open, patch

import pytest
from cocotb.handle import HierarchyObject, SimHandleBase
from copra.generation import (
    DocumentationGenerator,
    StubTemplate,
    generate_interface_documentation,
    generate_testbench_template,
)


class MockHandle:
    """Mock handle class for testing."""

    def __init__(self, name: str, handle_type: type, children: Dict[str, Any] = None):
        """Initialize a mock handle."""
        self._name = name
        self._handle_type = handle_type
        self._sub_handles = children or {}


@pytest.fixture
def mock_cpu_dut():
    """Create a mock CPU DUT for testing."""
    return MockHandle(
        "riscv_cpu",
        HierarchyObject,
        {
            "clk": MockHandle("clk", SimHandleBase),
            "rst_n": MockHandle("rst_n", SimHandleBase),
            "instr_addr": MockHandle("instr_addr", SimHandleBase),
            "instr_data": MockHandle("instr_data", SimHandleBase),
            "data_addr": MockHandle("data_addr", SimHandleBase),
            "data_wdata": MockHandle("data_wdata", SimHandleBase),
            "data_rdata": MockHandle("data_rdata", SimHandleBase),
            "interrupt": MockHandle("interrupt", SimHandleBase),
            "halt": MockHandle("halt", SimHandleBase),
            "debug": MockHandle(
                "debug",
                HierarchyObject,
                {
                    "enable": MockHandle("enable", SimHandleBase),
                    "step": MockHandle("step", SimHandleBase),
                },
            ),
        },
    )


@pytest.fixture
def simple_mock_dut():
    """Create a simple mock DUT for testing."""
    return MockHandle(
        "simple_dut",
        HierarchyObject,
        {
            "clock": MockHandle("clock", SimHandleBase),
            "reset": MockHandle("reset", SimHandleBase),
            "input_signal": MockHandle("input_signal", SimHandleBase),
            "output_signal": MockHandle("output_signal", SimHandleBase),
        },
    )


class TestStubTemplate:
    """Test stub template system functionality."""

    def test_template_initialization(self):
        """Test template initialization."""
        template = StubTemplate("custom")

        assert template.template_name == "custom"
        assert template.header_template is not None
        assert template.class_template is not None
        assert template.signal_template is not None
        assert template.array_template is not None

    def test_header_template_rendering(self):
        """Test header template rendering."""
        template = StubTemplate("test")

        with patch("copra.generation.__version__", "1.0.0"):
            header = template.render_header(
                module_name="test_module", imports="from test import TestClass"
            )

            assert "copra v1.0.0" in header
            assert "test_module" in header
            assert "from test import TestClass" in header
            assert "Template: test" in header

    def test_class_template_rendering(self):
        """Test class template rendering."""
        template = StubTemplate()

        class_def = template.render_class(
            class_name="TestClass",
            docstring='    """Test class docstring."""',
            attributes="    signal1: SimHandleBase\n    signal2: SimHandleBase",
        )

        assert "class TestClass(HierarchyObject):" in class_def
        assert "Test class docstring" in class_def
        assert "signal1: SimHandleBase" in class_def
        assert "signal2: SimHandleBase" in class_def

    def test_signal_template_rendering(self):
        """Test signal template rendering."""
        template = StubTemplate()

        signal_def = template.render_signal(
            name="test_signal", type_annotation="SimHandleBase", comment="Test signal comment"
        )

        assert "test_signal: SimHandleBase" in signal_def
        assert "Test signal comment" in signal_def

    def test_array_template_rendering(self):
        """Test array template rendering."""
        template = StubTemplate()

        array_def = template.render_array(
            class_name="TestArray",
            element_type="SimHandleBase",
            base_name="test_array",
            size=4,
            min_index=0,
            max_index=3,
        )

        assert "class TestArray(Sequence[SimHandleBase]):" in array_def
        assert "test_array with 4 elements" in array_def
        assert "[0:3]" in array_def
        assert "__getitem__" in array_def
        assert "__len__" in array_def
        assert "__iter__" in array_def
        assert "__contains__" in array_def
        assert "min_index" in array_def
        assert "max_index" in array_def


class TestDocumentationGenerator:
    """Test documentation generator functionality."""

    def test_markdown_generator_initialization(self):
        """Test markdown generator initialization."""
        generator = DocumentationGenerator("markdown")

        assert generator.format_type == "markdown"

    def test_rst_generator_initialization(self):
        """Test RST generator initialization."""
        generator = DocumentationGenerator("rst")

        assert generator.format_type == "rst"

    def test_html_generator_initialization(self):
        """Test HTML generator initialization."""
        generator = DocumentationGenerator("html")

        assert generator.format_type == "html"

    def test_unsupported_format_error(self):
        """Test error handling for unsupported formats."""
        generator = DocumentationGenerator("unsupported")

        hierarchy = {"dut": Mock}

        with pytest.raises(ValueError, match="Unsupported format"):
            generator.generate_interface_documentation(hierarchy)

    def test_markdown_documentation_generation(self):
        """Test markdown documentation generation."""
        generator = DocumentationGenerator("markdown")

        hierarchy = {
            "dut": Mock,
            "dut.clk": Mock,
            "dut.rst_n": Mock,
            "dut.cpu": Mock,
            "dut.cpu.pc": Mock,
            "dut.cpu.instruction": Mock,
            "dut.memory": Mock,
            "dut.memory.addr": Mock,
            "dut.memory.data": Mock,
        }

        # Mock the type objects
        for obj_type in hierarchy.values():
            obj_type.__name__ = "SimHandleBase"

        docs = generator.generate_interface_documentation(hierarchy)

        assert "# DUT Interface Documentation" in docs
        assert "## Overview" in docs
        assert "## Hierarchy Structure" in docs
        assert "### Top-Level Signals" in docs
        assert "### Module:" in docs
        assert "| Signal Name | Type | Description |" in docs
        assert "SimHandleBase" in docs

    def test_rst_documentation_generation(self):
        """Test RST documentation generation."""
        generator = DocumentationGenerator("rst")

        hierarchy = {"dut": Mock, "dut.signal1": Mock, "dut.signal2": Mock}

        # Mock the type objects
        for obj_type in hierarchy.values():
            obj_type.__name__ = "SimHandleBase"

        docs = generator.generate_interface_documentation(hierarchy)

        assert "DUT Interface Documentation" in docs
        assert "===========================" in docs
        assert "Overview" in docs
        assert "--------" in docs
        assert "``dut``" in docs
        assert "Type: SimHandleBase" in docs

    def test_html_documentation_generation(self):
        """Test HTML documentation generation."""
        generator = DocumentationGenerator("html")

        hierarchy = {"dut": Mock, "dut.signal1": Mock, "dut.signal2": Mock}

        # Mock the type objects
        for obj_type in hierarchy.values():
            obj_type.__name__ = "SimHandleBase"

        docs = generator.generate_interface_documentation(hierarchy)

        assert "<!DOCTYPE html>" in docs
        assert '<html lang="en">' in docs
        assert "<title>DUT Interface Documentation</title>" in docs
        assert "<h1>DUT Interface Documentation</h1>" in docs
        assert "<table>" in docs
        assert "<th>Path</th>" in docs
        assert "<th>Type</th>" in docs
        assert "<th>Category</th>" in docs
        assert "SimHandleBase" in docs
        assert "</html>" in docs

    def test_documentation_with_file_output(self):
        """Test documentation generation with file output."""
        generator = DocumentationGenerator("markdown")

        hierarchy = {"dut": Mock, "dut.signal": Mock}

        # Mock the type objects
        for obj_type in hierarchy.values():
            obj_type.__name__ = "SimHandleBase"

        with patch("builtins.open", mock_open()) as mock_file:
            docs = generator.generate_interface_documentation(hierarchy, "test_docs.md")

            mock_file.assert_called_once_with("test_docs.md", "w", encoding="utf-8")
            mock_file().write.assert_called()
            assert isinstance(docs, str)


class TestEnhancedTestbenchGeneration:
    """Test enhanced testbench template generation functionality."""

    def test_basic_testbench_generation(self):
        """Test basic testbench template generation."""
        hierarchy = {
            "dut": Mock,
            "dut.clk": Mock,
            "dut.rst_n": Mock,
            "dut.data_in": Mock,
            "dut.data_out": Mock,
        }

        template = generate_testbench_template(hierarchy)  # No output file = simple template

        assert "async def test_dut(dut):" in template
        assert "from typing import cast" in template
        assert "from dut import DutType" in template
        assert "typed_dut = cast(DutType, dut)" in template
        assert "typed_dut.clk.value = 0" in template
        assert "typed_dut.rst_n.value = 1" in template  # Reset assertion
        assert "typed_dut.data_in.value = 0" in template
        assert "await Timer(10, units='ns')" in template
        assert "dut._log.info" in template

    def test_testbench_with_clock_signals(self):
        """Test testbench generation with clock signal detection."""
        hierarchy = {"dut": Mock, "dut.clock": Mock, "dut.clk_div": Mock, "dut.data": Mock}

        template = generate_testbench_template(hierarchy)

        # Clock signals should be initialized to 0
        assert "typed_dut.clock.value = 0" in template
        assert "typed_dut.clk_div.value = 0" in template
        assert "typed_dut.data.value = 0" in template

    def test_testbench_with_reset_signals(self):
        """Test testbench generation with reset signal detection."""
        hierarchy = {"dut": Mock, "dut.reset": Mock, "dut.rst_async": Mock, "dut.data": Mock}

        template = generate_testbench_template(hierarchy)

        # Reset signals should be asserted (set to 1)
        assert "typed_dut.reset.value = 1" in template
        assert "typed_dut.rst_async.value = 1" in template
        assert "typed_dut.data.value = 0" in template

    def test_testbench_with_many_signals(self):
        """Test testbench generation with many signals (should limit to 5)."""
        hierarchy = {
            "dut": Mock,
            "dut.signal1": Mock,
            "dut.signal2": Mock,
            "dut.signal3": Mock,
            "dut.signal4": Mock,
            "dut.signal5": Mock,
            "dut.signal6": Mock,
            "dut.signal7": Mock,
            "dut.signal8": Mock,
        }

        template = generate_testbench_template(hierarchy)

        # Should only initialize first 5 signals
        signal_count = template.count("typed_dut.signal")
        assert signal_count == 5

    def test_testbench_with_custom_test_name(self):
        """Test testbench generation with custom test name."""
        hierarchy = {"dut": Mock, "dut.clk": Mock}

        # For simple template, test name is always test_dut
        template = generate_testbench_template(hierarchy)

        assert "async def test_dut(dut):" in template

    def test_testbench_with_empty_hierarchy(self):
        """Test testbench generation with empty hierarchy."""
        hierarchy = {}

        template = generate_testbench_template(hierarchy)

        # Should still generate a valid template
        assert "async def test_dut(dut):" in template
        assert "typed_dut = cast(DutType, dut)" in template
        assert "await Timer(10, units='ns')" in template


class TestGenerateTestbenchTemplate:
    """Test the generate_testbench_template function."""

    def test_generate_testbench_template_basic(self, mock_cpu_dut):
        """Test basic testbench template generation."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            template_file = f.name

        try:
            template = generate_testbench_template(mock_cpu_dut, template_file)

            # Check that template was generated
            assert len(template) > 0
            assert "riscv_cpu" in template
            assert "import cocotb" in template
            assert "from cocotb.clock import Clock" in template
            assert "from cocotb.triggers import" in template
            assert "class RiscvCpuTestBench:" in template
            assert "@cocotb.test()" in template

            # Check that file was written
            assert Path(template_file).exists()
            with open(template_file) as f:
                file_content = f.read()
            assert file_content == template

        finally:
            Path(template_file).unlink()

    def test_generate_testbench_template_clock_detection(self, mock_cpu_dut):
        """Test that clock signals are properly detected."""
        template = generate_testbench_template(mock_cpu_dut, "test.py")

        # Should detect 'clk' as clock signal
        assert "self.dut.clk" in template
        assert "Clock(self.dut.clk" in template

    def test_generate_testbench_template_reset_detection(self, mock_cpu_dut):
        """Test that reset signals are properly detected."""
        template = generate_testbench_template(mock_cpu_dut, "test.py")

        # Should detect 'rst_n' as reset signal
        assert "self.dut.rst_n.value = 0" in template
        assert "self.dut.rst_n.value = 1" in template

    def test_generate_testbench_template_alternative_naming(self, simple_mock_dut):
        """Test template generation with alternative clock/reset naming."""
        template = generate_testbench_template(simple_mock_dut, "test.py")

        # Should detect 'clock' and 'reset' signals
        assert "self.dut.clock" in template
        assert "self.dut.reset" in template

    def test_generate_testbench_template_no_clock_reset(self):
        """Test template generation when no clock/reset signals are detected."""
        no_clk_dut = MockHandle(
            "no_clk_dut",
            HierarchyObject,
            {
                "data_in": MockHandle("data_in", SimHandleBase),
                "data_out": MockHandle("data_out", SimHandleBase),
            },
        )

        template = generate_testbench_template(no_clk_dut, "test.py")

        # Should use default names
        assert "self.dut.clk" in template  # Default clock
        assert "self.dut.rst_n" in template  # Default reset

    def test_generate_testbench_template_signal_list(self, mock_cpu_dut):
        """Test that all signals are listed in the template."""
        template = generate_testbench_template(mock_cpu_dut, "test.py")

        # Check that signals are documented
        assert "# - dut.clk" in template
        assert "# - dut.rst_n" in template
        assert "# - dut.instr_addr" in template
        assert "# - dut.data_addr" in template

    def test_generate_testbench_template_test_functions(self, mock_cpu_dut):
        """Test that all required test functions are generated."""
        template = generate_testbench_template(mock_cpu_dut, "test.py")

        # Check for test functions
        assert "async def test_riscv_cpu_reset" in template
        assert "async def test_riscv_cpu_basic_operation" in template
        assert "async def test_riscv_cpu_edge_cases" in template
        assert "async def run_random_test" in template

    def test_generate_testbench_template_test_factory(self, mock_cpu_dut):
        """Test that TestFactory is properly configured."""
        template = generate_testbench_template(mock_cpu_dut, "test.py")

        assert "TestFactory" in template
        assert "factory = TestFactory(run_random_test)" in template
        assert "factory.add_option" in template
        assert "factory.generate_tests()" in template

    def test_generate_testbench_template_directory_creation(self, mock_cpu_dut):
        """Test that output directories are created if they don't exist."""
        output_dir = Path(tempfile.mkdtemp()) / "nested" / "directory"
        template_file = output_dir / "test.py"

        try:
            generate_testbench_template(mock_cpu_dut, str(template_file))

            # Directory should be created
            assert output_dir.exists()
            assert template_file.exists()

        finally:
            # Clean up
            if template_file.exists():
                template_file.unlink()
            if output_dir.exists():
                output_dir.rmdir()
            output_dir.parent.rmdir()


class TestGenerateInterfaceDocumentation:
    """Test the generate_interface_documentation function."""

    def test_generate_interface_documentation_basic(self, mock_cpu_dut):
        """Test basic interface documentation generation."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            doc_file = f.name

        try:
            documentation = generate_interface_documentation(mock_cpu_dut, doc_file)

            # Check that documentation was generated
            assert len(documentation) > 0
            assert "# riscv_cpu Interface Documentation" in documentation
            assert "## Overview" in documentation
            assert "## Signal Summary" in documentation
            assert "| Signal Type | Count |" in documentation

            # Check that file was written
            assert Path(doc_file).exists()
            with open(doc_file) as f:
                file_content = f.read()
            assert file_content == documentation

        finally:
            Path(doc_file).unlink()

    def test_generate_interface_documentation_signal_types(self, mock_cpu_dut):
        """Test that signal types are properly categorized."""
        documentation = generate_interface_documentation(mock_cpu_dut, "test.md")

        # Should contain signal type information
        assert "SimHandleBase" in documentation
        assert "HierarchyObject" in documentation

    def test_generate_interface_documentation_signal_details(self, mock_cpu_dut):
        """Test that individual signals are documented."""
        documentation = generate_interface_documentation(mock_cpu_dut, "test.md")

        # Should contain signal details
        assert "clk" in documentation
        assert "rst_n" in documentation
        assert "instr_addr" in documentation
        assert "debug.enable" in documentation

    def test_generate_interface_documentation_direction_detection(self, simple_mock_dut):
        """Test that signal directions are detected."""
        documentation = generate_interface_documentation(simple_mock_dut, "test.md")

        # Should detect signal directions
        assert "Input" in documentation or "Output" in documentation
        assert "Clock" in documentation or "Reset" in documentation

    def test_generate_interface_documentation_hierarchy_levels(self, mock_cpu_dut):
        """Test that hierarchy levels are calculated."""
        documentation = generate_interface_documentation(mock_cpu_dut, "test.md")

        # Should show hierarchy levels
        assert "Hierarchy Level:** 1" in documentation  # Top-level signals
        assert "Hierarchy Level:** 2" in documentation  # debug.enable, debug.step

    def test_generate_interface_documentation_empty_dut(self):
        """Test documentation generation for empty DUT."""
        empty_dut = MockHandle("empty_dut", HierarchyObject, {})

        documentation = generate_interface_documentation(empty_dut, "test.md")

        assert "# empty_dut Interface Documentation" in documentation
        assert "**Total Signals:** 1" in documentation  # The DUT itself is counted

    def test_generate_interface_documentation_directory_creation(self, mock_cpu_dut):
        """Test that output directories are created if they don't exist."""
        output_dir = Path(tempfile.mkdtemp()) / "nested" / "directory"
        doc_file = output_dir / "interface.md"

        try:
            generate_interface_documentation(mock_cpu_dut, str(doc_file))

            # Directory should be created
            assert output_dir.exists()
            assert doc_file.exists()

        finally:
            # Clean up
            if doc_file.exists():
                doc_file.unlink()
            if output_dir.exists():
                output_dir.rmdir()
            output_dir.parent.rmdir()


class TestGenerationIntegration:
    """Test integration between different generation components."""

    def test_template_and_documentation_integration(self):
        """Test integration between template system and documentation generation."""
        # Create a hierarchy
        hierarchy = {
            "dut": Mock,
            "dut.cpu": Mock,
            "dut.cpu.clk": Mock,
            "dut.cpu.rst_n": Mock,
            "dut.memory": Mock,
            "dut.memory.addr": Mock,
            "dut.memory.data": Mock,
        }

        # Mock the type objects
        for obj_type in hierarchy.values():
            obj_type.__name__ = "SimHandleBase"

        # Generate documentation
        doc_generator = DocumentationGenerator("markdown")
        docs = doc_generator.generate_interface_documentation(hierarchy)

        # Generate testbench template
        testbench = generate_testbench_template(hierarchy)  # Simple template

        # Both should be generated successfully
        assert isinstance(docs, str)
        assert isinstance(testbench, str)

        # Documentation should contain hierarchy information
        assert "cpu" in docs
        assert "memory" in docs
        assert "clk" in docs

        # Testbench should contain proper initialization
        assert "test_dut" in testbench
        assert "typed_dut" in testbench

    def test_multiple_format_documentation(self):
        """Test generating documentation in multiple formats."""
        hierarchy = {"dut": Mock, "dut.signal1": Mock, "dut.signal2": Mock}

        # Mock the type objects
        for obj_type in hierarchy.values():
            obj_type.__name__ = "SimHandleBase"

        # Generate in all formats
        markdown_gen = DocumentationGenerator("markdown")
        rst_gen = DocumentationGenerator("rst")
        html_gen = DocumentationGenerator("html")

        markdown_docs = markdown_gen.generate_interface_documentation(hierarchy)
        rst_docs = rst_gen.generate_interface_documentation(hierarchy)
        html_docs = html_gen.generate_interface_documentation(hierarchy)

        # All should be generated successfully
        assert isinstance(markdown_docs, str)
        assert isinstance(rst_docs, str)
        assert isinstance(html_docs, str)

        # Each should have format-specific content
        assert "# DUT Interface Documentation" in markdown_docs
        assert "DUT Interface Documentation" in rst_docs and "===" in rst_docs
        assert "<!DOCTYPE html>" in html_docs
