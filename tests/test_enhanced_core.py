# Copyright cocotb contributors
# Licensed under the Revised BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-3-Clause

"""Tests for enhanced core functionality."""

import unittest
from unittest.mock import Mock, patch

from copra.core import (
    ArrayInfo,
    ModuleInfo,
    SignalMetadata,
    _detect_bus_protocol,
    _detect_signal_direction,
    _discover_hierarchy_iterative,
    _extract_signal_metadata,
    _flatten_multidimensional_index,
    _generate_signal_description,
    _is_clock_signal,
    _is_constant_signal,
    _is_reset_signal,
    _parse_multidimensional_array,
    discover_hierarchy,
)


class TestSignalMetadata(unittest.TestCase):
    """Test the SignalMetadata class."""

    def test_init_minimal(self):
        """Test initialization with minimal parameters."""
        metadata = SignalMetadata(name="test_signal", signal_type=Mock)

        self.assertEqual(metadata.name, "test_signal")
        self.assertEqual(metadata.signal_type, Mock)
        self.assertIsNone(metadata.width)
        self.assertIsNone(metadata.direction)
        self.assertFalse(metadata.is_clock)
        self.assertFalse(metadata.is_reset)
        self.assertFalse(metadata.is_constant)
        self.assertIsNone(metadata.bus_protocol)
        self.assertIsNone(metadata.description)

    def test_init_full(self):
        """Test initialization with all parameters."""
        metadata = SignalMetadata(
            name="clk_signal",
            signal_type=Mock,
            width=1,
            direction="input",
            is_clock=True,
            is_reset=False,
            is_constant=False,
            bus_protocol="AXI",
            description="Clock signal",
        )

        self.assertEqual(metadata.name, "clk_signal")
        self.assertEqual(metadata.width, 1)
        self.assertEqual(metadata.direction, "input")
        self.assertTrue(metadata.is_clock)
        self.assertFalse(metadata.is_reset)
        self.assertEqual(metadata.bus_protocol, "AXI")
        self.assertEqual(metadata.description, "Clock signal")

    def test_repr(self):
        """Test string representation."""
        metadata = SignalMetadata(name="test_signal", signal_type=Mock, width=8)

        repr_str = repr(metadata)
        self.assertIn("test_signal", repr_str)
        self.assertIn("width=8", repr_str)
        if "Mock" in Mock.__name__:
            self.assertIn("Mock", repr_str)


class TestArrayInfo(unittest.TestCase):
    """Test the ArrayInfo class."""

    def test_init_simple_array(self):
        """Test initialization of simple array."""
        array_info = ArrayInfo(base_name="mem", element_type=Mock, indices=[0, 1, 2, 3])

        self.assertEqual(array_info.base_name, "mem")
        self.assertEqual(array_info.element_type, Mock)
        self.assertEqual(array_info.indices, [0, 1, 2, 3])
        self.assertEqual(array_info.min_index, 0)
        self.assertEqual(array_info.max_index, 3)
        self.assertEqual(array_info.size, 4)
        self.assertTrue(array_info.is_contiguous)
        self.assertFalse(array_info.is_multidimensional)

    def test_init_multidimensional_array(self):
        """Test initialization of multidimensional array."""
        array_info = ArrayInfo(
            base_name="matrix",
            element_type=Mock,
            indices=[0, 1, 2],
            dimensions=[(0, 1), (0, 2)],
            is_multidimensional=True,
        )

        self.assertEqual(array_info.base_name, "matrix")
        self.assertTrue(array_info.is_multidimensional)
        self.assertEqual(len(array_info.dimensions), 2)

    def test_init_empty_array(self):
        """Test initialization with empty indices."""
        array_info = ArrayInfo(base_name="empty", element_type=Mock, indices=[])

        self.assertEqual(array_info.size, 0)
        self.assertEqual(array_info.min_index, 0)
        self.assertEqual(array_info.max_index, 0)

    def test_repr(self):
        """Test string representation."""
        array_info = ArrayInfo(base_name="test_array", element_type=Mock, indices=[0, 1, 2])

        repr_str = repr(array_info)
        self.assertIn("test_array", repr_str)
        self.assertIn("size=3", repr_str)
        # Mock.__name__ may vary between platforms, so be flexible
        if "Mock" in Mock.__name__:
            self.assertIn("Mock", repr_str)


class TestModuleInfo(unittest.TestCase):
    """Test the ModuleInfo class."""

    def test_init_minimal(self):
        """Test initialization with minimal parameters."""
        module_info = ModuleInfo(name="test_module", module_type="TestModule")

        self.assertEqual(module_info.name, "test_module")
        self.assertEqual(module_info.module_type, "TestModule")
        self.assertEqual(len(module_info.signals), 0)
        self.assertEqual(len(module_info.submodules), 0)
        self.assertEqual(len(module_info.arrays), 0)
        self.assertEqual(len(module_info.parameters), 0)

    def test_init_full(self):
        """Test initialization with all parameters."""
        signals = {"clk": Mock()}
        submodules = {"cpu": Mock()}
        arrays = {"mem": Mock()}
        parameters = {"WIDTH": 32}

        module_info = ModuleInfo(
            name="complex_module",
            module_type="ComplexModule",
            signals=signals,
            submodules=submodules,
            arrays=arrays,
            parameters=parameters,
        )

        self.assertEqual(module_info.signals, signals)
        self.assertEqual(module_info.submodules, submodules)
        self.assertEqual(module_info.arrays, arrays)
        self.assertEqual(module_info.parameters, parameters)

    def test_repr(self):
        """Test string representation."""
        module_info = ModuleInfo(
            name="test_module", module_type="TestModule", signals={"clk": Mock(), "rst": Mock()}
        )

        repr_str = repr(module_info)
        self.assertIn("test_module", repr_str)
        self.assertIn("TestModule", repr_str)
        self.assertIn("signals=2", repr_str)


class TestSignalDetection(unittest.TestCase):
    """Test signal detection functions."""

    def test_detect_signal_direction_input(self):
        """Test input signal direction detection."""
        obj = Mock()

        # Test various input patterns
        self.assertEqual(_detect_signal_direction("data_in", obj), "input")
        self.assertEqual(_detect_signal_direction("input_signal", obj), "input")
        self.assertEqual(_detect_signal_direction("addr_i", obj), "input")

    def test_detect_signal_direction_output(self):
        """Test output signal direction detection."""
        obj = Mock()

        # Test various output patterns
        self.assertEqual(_detect_signal_direction("data_out", obj), "output")
        self.assertEqual(_detect_signal_direction("output_signal", obj), "output")
        self.assertEqual(_detect_signal_direction("result_o", obj), "output")

    def test_detect_signal_direction_inout(self):
        """Test bidirectional signal direction detection."""
        obj = Mock()

        # Test various bidirectional patterns
        self.assertEqual(_detect_signal_direction("data_io", obj), "inout")
        self.assertEqual(_detect_signal_direction("inout_signal", obj), "inout")
        self.assertEqual(_detect_signal_direction("bidir_bus", obj), "inout")

    def test_detect_signal_direction_from_object(self):
        """Test signal direction detection from object properties."""
        obj = Mock()
        obj._direction = "input"

        result = _detect_signal_direction("unknown_signal", obj)
        self.assertEqual(result, "input")

    def test_detect_signal_direction_none(self):
        """Test signal direction detection when no pattern matches."""
        obj = Mock()

        result = _detect_signal_direction("unknown_signal", obj)
        self.assertIsNone(result)

    def test_is_clock_signal_true(self):
        """Test clock signal detection - positive cases."""
        self.assertTrue(_is_clock_signal("clk"))
        self.assertTrue(_is_clock_signal("clock"))
        self.assertTrue(_is_clock_signal("sys_clk"))
        self.assertTrue(_is_clock_signal("clkin"))
        self.assertTrue(_is_clock_signal("clkout"))
        self.assertTrue(_is_clock_signal("ck"))

    def test_is_clock_signal_false(self):
        """Test clock signal detection - negative cases."""
        self.assertFalse(_is_clock_signal("data"))
        self.assertFalse(_is_clock_signal("reset"))
        self.assertFalse(_is_clock_signal("enable"))

    def test_is_reset_signal_true(self):
        """Test reset signal detection - positive cases."""
        self.assertTrue(_is_reset_signal("rst"))
        self.assertTrue(_is_reset_signal("reset"))
        self.assertTrue(_is_reset_signal("sys_rst"))
        self.assertTrue(_is_reset_signal("rst_n"))
        self.assertTrue(_is_reset_signal("resetn"))
        self.assertTrue(_is_reset_signal("nrst"))

    def test_is_reset_signal_false(self):
        """Test reset signal detection - negative cases."""
        self.assertFalse(_is_reset_signal("clk"))
        self.assertFalse(_is_reset_signal("data"))
        self.assertFalse(_is_reset_signal("enable"))

    def test_is_constant_signal_by_type(self):
        """Test constant signal detection by object type."""
        obj = Mock()
        obj._type = "const_signal"

        result = _is_constant_signal(obj, "test_signal")
        self.assertTrue(result)

    def test_is_constant_signal_by_name(self):
        """Test constant signal detection by naming pattern."""
        obj = Mock()

        # Test ALL_CAPS_WITH_UNDERSCORES pattern
        result = _is_constant_signal(obj, "MAX_VALUE")
        self.assertTrue(result)

        result = _is_constant_signal(obj, "CONSTANT_DATA")
        self.assertTrue(result)

    def test_is_constant_signal_false(self):
        """Test constant signal detection - negative cases."""
        obj = Mock()

        result = _is_constant_signal(obj, "normal_signal")
        self.assertFalse(result)

        result = _is_constant_signal(obj, "CamelCase")
        self.assertFalse(result)

    def test_detect_bus_protocol_axi(self):
        """Test AXI bus protocol detection."""
        # Test signal name patterns
        self.assertEqual(_detect_bus_protocol("awvalid", "module.awvalid"), "AXI")
        self.assertEqual(_detect_bus_protocol("awready", "module.awready"), "AXI")
        self.assertEqual(_detect_bus_protocol("wvalid", "module.wvalid"), "AXI")
        self.assertEqual(_detect_bus_protocol("rready", "module.rready"), "AXI")

        # Test path patterns
        self.assertEqual(_detect_bus_protocol("valid", "axi_master.valid"), "AXI")

    def test_detect_bus_protocol_ahb(self):
        """Test AHB bus protocol detection."""
        self.assertEqual(_detect_bus_protocol("haddr", "module.haddr"), "AHB")
        self.assertEqual(_detect_bus_protocol("hwrite", "module.hwrite"), "AHB")
        self.assertEqual(_detect_bus_protocol("hrdata", "module.hrdata"), "AHB")

    def test_detect_bus_protocol_apb(self):
        """Test APB bus protocol detection."""
        self.assertEqual(_detect_bus_protocol("paddr", "module.paddr"), "APB")
        self.assertEqual(_detect_bus_protocol("pwrite", "module.pwrite"), "APB")
        self.assertEqual(_detect_bus_protocol("prdata", "module.prdata"), "APB")

    def test_detect_bus_protocol_none(self):
        """Test bus protocol detection when no protocol matches."""
        result = _detect_bus_protocol("data", "module.data")
        self.assertIsNone(result)

    def test_generate_signal_description(self):
        """Test signal description generation."""
        # Test with all parameters
        desc = _generate_signal_description("clk", Mock, 1, "input")
        # On different platforms, Mock.__name__ may vary, so be flexible
        self.assertIn("Input signal (1 bit)", desc)
        if "Mock" in Mock.__name__:
            self.assertIn("Mock", desc)

        # Test with width > 1
        desc = _generate_signal_description("data", Mock, 32, "output")
        self.assertIn("Output signal (32 bits)", desc)
        if "Mock" in Mock.__name__:
            self.assertIn("Mock", desc)

        # Test without direction
        desc = _generate_signal_description("signal", Mock, 8, None)
        self.assertIn("Signal (8 bits)", desc)
        if "Mock" in Mock.__name__:
            self.assertIn("Mock", desc)

        # Test without width
        desc = _generate_signal_description("signal", Mock, None, "input")
        self.assertIn("Input signal", desc)
        if "Mock" in Mock.__name__:
            self.assertIn("Mock", desc)

        # Test with SimHandleBase - should not include type info
        from unittest.mock import MagicMock
        # Create a mock that looks like SimHandleBase
        mock_shb = MagicMock()
        mock_shb.__name__ = "SimHandleBase"
        desc = _generate_signal_description("clk", mock_shb, 1, "input")
        self.assertEqual(desc, "Input signal (1 bit)")


class TestArrayParsing(unittest.TestCase):
    """Test array parsing functions."""

    def test_parse_multidimensional_array_simple(self):
        """Test parsing simple array names."""
        result = _parse_multidimensional_array("mem[0]")
        self.assertIsNotNone(result)
        base_name, dimensions = result
        self.assertEqual(base_name, "mem")
        self.assertEqual(dimensions, [0])

    def test_parse_multidimensional_array_2d(self):
        """Test parsing 2D array names."""
        result = _parse_multidimensional_array("matrix[1][2]")
        self.assertIsNotNone(result)
        base_name, dimensions = result
        self.assertEqual(base_name, "matrix")
        self.assertEqual(dimensions, [1, 2])

    def test_parse_multidimensional_array_3d(self):
        """Test parsing 3D array names."""
        result = _parse_multidimensional_array("cube[0][1][2]")
        self.assertIsNotNone(result)
        base_name, dimensions = result
        self.assertEqual(base_name, "cube")
        self.assertEqual(dimensions, [0, 1, 2])

    def test_parse_multidimensional_array_non_numeric(self):
        """Test parsing array with non-numeric indices."""
        result = _parse_multidimensional_array("mem[x]")
        self.assertIsNone(result)

    def test_parse_multidimensional_array_not_array(self):
        """Test parsing non-array names."""
        result = _parse_multidimensional_array("simple_signal")
        self.assertIsNone(result)

    def test_flatten_multidimensional_index(self):
        """Test flattening multidimensional indices."""
        # Simple test - just sum the indices
        result = _flatten_multidimensional_index([1, 2, 3])
        self.assertEqual(result, 6)

        result = _flatten_multidimensional_index([0])
        self.assertEqual(result, 0)


class TestExtractSignalMetadata(unittest.TestCase):
    """Test signal metadata extraction."""

    def test_extract_signal_metadata_hierarchy_object(self):
        """Test that hierarchy objects don't generate metadata."""
        from cocotb.handle import HierarchyObject

        obj = Mock(spec=HierarchyObject)
        result = _extract_signal_metadata(obj, "module.submodule")
        self.assertIsNone(result)

    def test_extract_signal_metadata_signal(self):
        """Test metadata extraction for signals."""
        obj = Mock()
        obj._range = Mock()
        obj._range.__len__ = Mock(return_value=8)

        result = _extract_signal_metadata(obj, "module.data_signal")

        self.assertIsNotNone(result)
        self.assertEqual(result.name, "data_signal")
        self.assertEqual(result.width, 8)
        self.assertFalse(result.is_clock)
        self.assertFalse(result.is_reset)

    def test_extract_signal_metadata_clock(self):
        """Test metadata extraction for clock signals."""
        obj = Mock()

        result = _extract_signal_metadata(obj, "module.clk")

        self.assertIsNotNone(result)
        self.assertTrue(result.is_clock)
        self.assertFalse(result.is_reset)

    def test_extract_signal_metadata_reset(self):
        """Test metadata extraction for reset signals."""
        obj = Mock()

        result = _extract_signal_metadata(obj, "module.rst_n")

        self.assertIsNotNone(result)
        self.assertFalse(result.is_clock)
        self.assertTrue(result.is_reset)

    def test_extract_signal_metadata_with_value_length(self):
        """Test width extraction from value length."""
        obj = Mock()
        obj.value = Mock()
        obj.value.__len__ = Mock(return_value=16)

        result = _extract_signal_metadata(obj, "module.wide_signal")

        self.assertIsNotNone(result)
        self.assertEqual(result.width, 16)


class TestDiscoverHierarchyEnhanced(unittest.TestCase):
    """Test enhanced hierarchy discovery functionality."""

    def test_discover_hierarchy_with_metadata(self):
        """Test hierarchy discovery with metadata extraction."""
        # Create mock DUT
        mock_dut = Mock()
        mock_dut._name = "top"
        mock_dut._discover_all = Mock()
        mock_dut._sub_handles = {}

        # Create mock signal
        mock_signal = Mock()
        mock_signal._name = "clk"
        mock_dut._sub_handles["clk"] = mock_signal

        hierarchy = discover_hierarchy(mock_dut, extract_metadata=True, max_depth=10)

        self.assertIn("top", hierarchy)
        self.assertIn("top.clk", hierarchy)

        # Check that metadata was extracted
        self.assertTrue(hasattr(hierarchy, "_signal_metadata"))

    def test_discover_hierarchy_with_arrays(self):
        """Test hierarchy discovery with array detection."""
        # Create mock DUT
        mock_dut = Mock()
        mock_dut._name = "top"
        mock_dut._discover_all = Mock()
        mock_dut._sub_handles = {}

        # Create mock array elements
        mock_mem0 = Mock()
        mock_mem0._name = "mem[0]"
        mock_mem1 = Mock()
        mock_mem1._name = "mem[1]"

        mock_dut._sub_handles["mem[0]"] = mock_mem0
        mock_dut._sub_handles["mem[1]"] = mock_mem1

        hierarchy = discover_hierarchy(mock_dut, array_detection=True, max_depth=10)

        self.assertIn("top", hierarchy)
        # Should detect array base
        self.assertIn("top.mem", hierarchy)

        # Check that array info was extracted
        self.assertTrue(hasattr(hierarchy, "_array_info"))

    def test_discover_hierarchy_performance_mode(self):
        """Test hierarchy discovery in performance mode."""
        mock_dut = Mock()
        mock_dut._name = "top"
        mock_dut._discover_all = Mock()
        mock_dut._sub_handles = {}

        with patch("copra.core._discover_hierarchy_iterative") as mock_iterative:
            mock_iterative.return_value = {"top": Mock}

            discover_hierarchy(mock_dut, performance_mode=True, max_depth=10)

            mock_iterative.assert_called_once()

    def test_discover_hierarchy_iterative(self):
        """Test iterative hierarchy discovery."""
        # Create mock DUT with nested structure
        mock_dut = Mock()
        mock_dut._name = "top"
        mock_dut._discover_all = Mock()

        # Create nested structure
        mock_sub = Mock()
        mock_sub._name = "sub"
        mock_sub._discover_all = Mock()
        mock_sub._sub_handles = {}

        mock_dut._sub_handles = {"sub": mock_sub}

        hierarchy = _discover_hierarchy_iterative(
            mock_dut,
            max_depth=10,
            include_constants=False,
            array_detection=True,
            discovery_stats={},
        )

        self.assertIn("top", hierarchy)
        self.assertIn("top.sub", hierarchy)

    def test_discover_hierarchy_max_depth_exceeded(self):
        """Test hierarchy discovery with max depth exceeded."""
        mock_dut = Mock()
        mock_dut._name = "top"
        mock_dut._discover_all = Mock()
        mock_dut._sub_handles = {}

        # Test with very low max depth
        with self.assertRaises(ValueError):
            discover_hierarchy(mock_dut, max_depth=0)

    def test_discover_hierarchy_with_errors(self):
        """Test hierarchy discovery with errors in sub-handles."""
        mock_dut = Mock()
        mock_dut._name = "top"
        mock_dut._discover_all = Mock(side_effect=Exception("Discovery error"))
        mock_dut._sub_handles = {}

        # Should not raise exception, but handle gracefully
        hierarchy = discover_hierarchy(mock_dut, max_depth=10)

        self.assertIn("top", hierarchy)
        # Check that error was recorded in stats
        self.assertTrue(hasattr(hierarchy, "_discovery_stats"))
        self.assertGreater(hierarchy._discovery_stats["errors_encountered"], 0)

    def test_discover_hierarchy_include_constants(self):
        """Test hierarchy discovery including constants."""
        mock_dut = Mock()
        mock_dut._name = "top"
        mock_dut._discover_all = Mock()

        # Create mock constant signal
        mock_const = Mock()
        mock_const._name = "CONSTANT_VALUE"
        mock_const._type = "const_signal"

        mock_dut._sub_handles = {"CONSTANT_VALUE": mock_const}

        # Test without including constants
        hierarchy = discover_hierarchy(mock_dut, include_constants=False, max_depth=10)

        # Should not include constant
        self.assertNotIn("top.CONSTANT_VALUE", hierarchy)

        # Test with including constants
        hierarchy = discover_hierarchy(mock_dut, include_constants=True, max_depth=10)

        # Should include constant
        self.assertIn("top.CONSTANT_VALUE", hierarchy)


if __name__ == "__main__":
    unittest.main()
