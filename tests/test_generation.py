"""Tests for the copra.generation module."""

import tempfile
from pathlib import Path
from typing import Any, Dict

import pytest
from cocotb.handle import HierarchyObject, LogicObject

from copra.generation import generate_interface_documentation, generate_testbench_template


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
            "clk": MockHandle("clk", LogicObject),
            "rst_n": MockHandle("rst_n", LogicObject),
            "instr_addr": MockHandle("instr_addr", LogicObject),
            "instr_data": MockHandle("instr_data", LogicObject),
            "data_addr": MockHandle("data_addr", LogicObject),
            "data_wdata": MockHandle("data_wdata", LogicObject),
            "data_rdata": MockHandle("data_rdata", LogicObject),
            "interrupt": MockHandle("interrupt", LogicObject),
            "halt": MockHandle("halt", LogicObject),
            "debug": MockHandle(
                "debug",
                HierarchyObject,
                {
                    "enable": MockHandle("enable", LogicObject),
                    "step": MockHandle("step", LogicObject),
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
            "clock": MockHandle("clock", LogicObject),
            "reset": MockHandle("reset", LogicObject),
            "input_signal": MockHandle("input_signal", LogicObject),
            "output_signal": MockHandle("output_signal", LogicObject),
        },
    )


class TestGenerateTestbenchTemplate:
    """Test the generate_testbench_template function."""

    def test_generate_testbench_template_basic(self, mock_cpu_dut):
        """Test basic testbench template generation."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
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
            with open(template_file, 'r') as f:
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
                "data_in": MockHandle("data_in", LogicObject),
                "data_out": MockHandle("data_out", LogicObject),
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
            template = generate_testbench_template(mock_cpu_dut, str(template_file))
            
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
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            doc_file = f.name

        try:
            documentation = generate_interface_documentation(mock_cpu_dut, doc_file)
            
            # Check that documentation was generated
            assert len(documentation) > 0
            assert "# riscv_cpu Interface Documentation" in documentation
            assert "## Overview" in documentation
            assert "## Signal Summary" in documentation
            assert "| Signal Type | Count |" in documentation
            assert "**Total Signals:**" in documentation
            
            # Check that file was written
            assert Path(doc_file).exists()
            with open(doc_file, 'r') as f:
                file_content = f.read()
            assert file_content == documentation
            
        finally:
            Path(doc_file).unlink()

    def test_generate_interface_documentation_signal_types(self, mock_cpu_dut):
        """Test that signal types are properly documented."""
        documentation = generate_interface_documentation(mock_cpu_dut, "cpu.dutdoc.md")
        
        # Should include LogicObject and HierarchyObject sections
        assert "## LogicObject Signals" in documentation
        assert "## HierarchyObject Signals" in documentation

    def test_generate_interface_documentation_signal_details(self, mock_cpu_dut):
        """Test that individual signals are properly documented."""
        documentation = generate_interface_documentation(mock_cpu_dut, "cpu.dutdoc.md")
        
        # Check for specific signal documentation (with full paths)
        assert "### `riscv_cpu.clk`" in documentation
        assert "### `riscv_cpu.rst_n`" in documentation
        assert "### `riscv_cpu.debug`" in documentation
        
        # Check for signal properties
        assert "- **Type:**" in documentation
        assert "- **Direction:**" in documentation
        assert "- **Hierarchy Level:**" in documentation

    def test_generate_interface_documentation_direction_detection(self, simple_mock_dut):
        """Test that signal directions are properly detected."""
        documentation = generate_interface_documentation(simple_mock_dut, "simple_dut.dutdoc.md")
        
        # Should detect signal directions based on naming
        assert "Clock" in documentation  # clock signal
        assert "Reset" in documentation  # reset signal
        assert "Input" in documentation  # input_signal
        assert "Output" in documentation  # output_signal

    def test_generate_interface_documentation_hierarchy_levels(self, mock_cpu_dut):
        """Test that hierarchy levels are properly calculated."""
        documentation = generate_interface_documentation(mock_cpu_dut, "cpu.dutdoc.md")
        
        # Top-level signals should be level 1, nested signals level 2+
        assert "- **Hierarchy Level:** 1" in documentation
        assert "- **Hierarchy Level:** 2" in documentation

    def test_generate_interface_documentation_empty_dut(self):
        """Test documentation generation with empty DUT."""
        empty_dut = MockHandle("empty_dut", HierarchyObject, {})
        
        documentation = generate_interface_documentation(empty_dut, "empty_dut.dutdoc.md")
        
        assert "# empty_dut Interface Documentation" in documentation
        assert "**Total Signals:** 1" in documentation  # Just the DUT itself

    def test_generate_interface_documentation_directory_creation(self, mock_cpu_dut):
        """Test that output directories are created if they don't exist."""
        output_dir = Path(tempfile.mkdtemp()) / "docs" / "interface"
        doc_file = output_dir / "interface.md"
        
        try:
            documentation = generate_interface_documentation(mock_cpu_dut, str(doc_file))
            
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