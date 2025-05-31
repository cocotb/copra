# Copyright cocotb contributors
# Licensed under the Revised BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-3-Clause

"""Tests for the metadata module."""

import unittest
from unittest.mock import Mock, patch

from copra.metadata import (
    ArrayMetadata,
    BusProtocol,
    SignalDirection,
    SignalMetadata,
    SignalMetadataExtractor,
    SignalType,
    extract_comprehensive_metadata,
    extract_enhanced_array_metadata,
)


class TestEnums(unittest.TestCase):
    """Test the enumeration classes."""

    def test_signal_direction_values(self):
        """Test SignalDirection enum values."""
        self.assertEqual(SignalDirection.INPUT.value, "input")
        self.assertEqual(SignalDirection.OUTPUT.value, "output")
        self.assertEqual(SignalDirection.INOUT.value, "inout")
        self.assertEqual(SignalDirection.INTERNAL.value, "internal")
        self.assertEqual(SignalDirection.UNKNOWN.value, "unknown")

    def test_signal_type_values(self):
        """Test SignalType enum values."""
        self.assertEqual(SignalType.CLOCK.value, "clock")
        self.assertEqual(SignalType.RESET.value, "reset")
        self.assertEqual(SignalType.DATA.value, "data")
        self.assertEqual(SignalType.CONTROL.value, "control")
        self.assertEqual(SignalType.STATUS.value, "status")
        self.assertEqual(SignalType.ADDRESS.value, "address")
        self.assertEqual(SignalType.ENABLE.value, "enable")
        self.assertEqual(SignalType.VALID.value, "valid")
        self.assertEqual(SignalType.READY.value, "ready")
        self.assertEqual(SignalType.UNKNOWN.value, "unknown")

    def test_bus_protocol_values(self):
        """Test BusProtocol enum values."""
        self.assertEqual(BusProtocol.AXI4.value, "axi4")
        self.assertEqual(BusProtocol.AXI4_LITE.value, "axi4_lite")
        self.assertEqual(BusProtocol.AXI4_STREAM.value, "axi4_stream")
        self.assertEqual(BusProtocol.AHB.value, "ahb")
        self.assertEqual(BusProtocol.APB.value, "apb")
        self.assertEqual(BusProtocol.AVALON.value, "avalon")
        self.assertEqual(BusProtocol.WISHBONE.value, "wishbone")
        self.assertEqual(BusProtocol.CUSTOM.value, "custom")
        self.assertEqual(BusProtocol.NONE.value, "none")


class TestSignalMetadata(unittest.TestCase):
    """Test the SignalMetadata dataclass."""

    def test_signal_metadata_creation(self):
        """Test creating SignalMetadata instance."""
        metadata = SignalMetadata(
            name="test_signal",
            width=8,
            direction=SignalDirection.INPUT,
            signal_type=SignalType.DATA,
            bus_protocol=BusProtocol.NONE,
        )

        self.assertEqual(metadata.name, "test_signal")
        self.assertEqual(metadata.width, 8)
        self.assertEqual(metadata.direction, SignalDirection.INPUT)
        self.assertEqual(metadata.signal_type, SignalType.DATA)
        self.assertEqual(metadata.bus_protocol, BusProtocol.NONE)
        self.assertIsNone(metadata.clock_domain)
        self.assertIsNone(metadata.reset_signal)
        self.assertFalse(metadata.is_array)

    def test_signal_metadata_with_optional_fields(self):
        """Test SignalMetadata with optional fields."""
        metadata = SignalMetadata(
            name="clk_signal",
            width=1,
            direction=SignalDirection.INPUT,
            signal_type=SignalType.CLOCK,
            bus_protocol=BusProtocol.NONE,
            clock_domain="main_clk",
            is_array=True,
            array_dimensions=[4],
            is_signed=True,
        )

        self.assertEqual(metadata.clock_domain, "main_clk")
        self.assertTrue(metadata.is_array)
        self.assertEqual(metadata.array_dimensions, [4])
        self.assertTrue(metadata.is_signed)


class TestArrayMetadata(unittest.TestCase):
    """Test the ArrayMetadata dataclass."""

    def test_array_metadata_creation(self):
        """Test creating ArrayMetadata instance."""
        metadata = ArrayMetadata(
            base_name="memory",
            dimensions=[4, 8],
            element_type=int,
            min_indices=[0, 0],
            max_indices=[3, 7],
            is_contiguous=True,
            total_elements=32,
            is_multidimensional=True,
            naming_pattern="memory[{}][{}]",
        )

        self.assertEqual(metadata.base_name, "memory")
        self.assertEqual(metadata.dimensions, [4, 8])
        self.assertEqual(metadata.element_type, int)
        self.assertEqual(metadata.min_indices, [0, 0])
        self.assertEqual(metadata.max_indices, [3, 7])
        self.assertTrue(metadata.is_contiguous)
        self.assertEqual(metadata.total_elements, 32)
        self.assertTrue(metadata.is_multidimensional)
        self.assertEqual(metadata.naming_pattern, "memory[{}][{}]")


class TestSignalMetadataExtractor(unittest.TestCase):
    """Test the SignalMetadataExtractor class."""

    def setUp(self):
        """Set up test fixtures."""
        self.extractor = SignalMetadataExtractor()

    def test_extract_signal_width_from_attribute(self):
        """Test extracting signal width from _width attribute."""
        mock_obj = Mock()
        mock_obj._width = 16

        width = self.extractor._extract_signal_width(mock_obj)
        self.assertEqual(width, 16)

    def test_extract_signal_width_from_range(self):
        """Test extracting signal width from range attribute."""
        mock_obj = Mock()
        del mock_obj._width  # Remove _width attribute
        mock_obj.range = [0, 1, 2, 3, 4, 5, 6, 7]  # 8-bit signal

        width = self.extractor._extract_signal_width(mock_obj)
        self.assertEqual(width, 8)

    def test_extract_signal_width_default(self):
        """Test extracting signal width with default fallback."""
        mock_obj = Mock()
        del mock_obj._width
        del mock_obj.range
        del mock_obj._handle

        width = self.extractor._extract_signal_width(mock_obj)
        self.assertEqual(width, 1)  # Default

    def test_detect_signal_direction_from_handle(self):
        """Test detecting signal direction from handle."""
        mock_obj = Mock()
        mock_obj._handle.get_direction.return_value = "input"

        direction = self.extractor._detect_signal_direction(mock_obj, "test", "test")
        self.assertEqual(direction, SignalDirection.INPUT)

    def test_detect_signal_direction_from_name_input(self):
        """Test detecting input signal direction from name."""
        mock_obj = Mock()
        del mock_obj._handle

        direction = self.extractor._detect_signal_direction(mock_obj, "data_in", "test.data_in")
        self.assertEqual(direction, SignalDirection.INPUT)

    def test_detect_signal_direction_from_name_output(self):
        """Test detecting output signal direction from name."""
        mock_obj = Mock()
        del mock_obj._handle

        direction = self.extractor._detect_signal_direction(
            mock_obj, "result_out", "test.result_out"
        )
        self.assertEqual(direction, SignalDirection.OUTPUT)

    def test_detect_signal_direction_from_name_inout(self):
        """Test detecting inout signal direction from name."""
        mock_obj = Mock()
        del mock_obj._handle

        direction = self.extractor._detect_signal_direction(mock_obj, "data_io", "test.data_io")
        self.assertEqual(direction, SignalDirection.INOUT)

    def test_detect_signal_direction_unknown(self):
        """Test detecting unknown signal direction."""
        mock_obj = Mock()
        del mock_obj._handle

        direction = self.extractor._detect_signal_direction(
            mock_obj, "unknown_signal", "test.unknown_signal"
        )
        self.assertEqual(direction, SignalDirection.UNKNOWN)

    def test_classify_signal_type_clock(self):
        """Test classifying clock signal type."""
        signal_type = self.extractor._classify_signal_type("clk", "test.clk")
        self.assertEqual(signal_type, SignalType.CLOCK)

        signal_type = self.extractor._classify_signal_type("clock", "test.clock")
        self.assertEqual(signal_type, SignalType.CLOCK)

        signal_type = self.extractor._classify_signal_type("main_clk", "test.main_clk")
        self.assertEqual(signal_type, SignalType.CLOCK)

    def test_classify_signal_type_reset(self):
        """Test classifying reset signal type."""
        signal_type = self.extractor._classify_signal_type("rst", "test.rst")
        self.assertEqual(signal_type, SignalType.RESET)

        signal_type = self.extractor._classify_signal_type("reset", "test.reset")
        self.assertEqual(signal_type, SignalType.RESET)

        signal_type = self.extractor._classify_signal_type("rst_n", "test.rst_n")
        self.assertEqual(signal_type, SignalType.RESET)

    def test_classify_signal_type_enable(self):
        """Test classifying enable signal type."""
        signal_type = self.extractor._classify_signal_type("en", "test.en")
        self.assertEqual(signal_type, SignalType.ENABLE)

        signal_type = self.extractor._classify_signal_type("enable", "test.enable")
        self.assertEqual(signal_type, SignalType.ENABLE)

    def test_classify_signal_type_valid(self):
        """Test classifying valid signal type."""
        signal_type = self.extractor._classify_signal_type("valid", "test.valid")
        self.assertEqual(signal_type, SignalType.VALID)

        signal_type = self.extractor._classify_signal_type("data_vld", "test.data_vld")
        self.assertEqual(signal_type, SignalType.VALID)

    def test_classify_signal_type_ready(self):
        """Test classifying ready signal type."""
        signal_type = self.extractor._classify_signal_type("ready", "test.ready")
        self.assertEqual(signal_type, SignalType.READY)

        signal_type = self.extractor._classify_signal_type("data_rdy", "test.data_rdy")
        self.assertEqual(signal_type, SignalType.READY)

    def test_classify_signal_type_address(self):
        """Test classifying address signal type."""
        signal_type = self.extractor._classify_signal_type("addr", "test.addr")
        self.assertEqual(signal_type, SignalType.ADDRESS)

        signal_type = self.extractor._classify_signal_type("address", "test.address")
        self.assertEqual(signal_type, SignalType.ADDRESS)

    def test_classify_signal_type_status(self):
        """Test classifying status signal type."""
        signal_type = self.extractor._classify_signal_type("status", "test.status")
        self.assertEqual(signal_type, SignalType.STATUS)

        signal_type = self.extractor._classify_signal_type("error_flag", "test.error_flag")
        self.assertEqual(signal_type, SignalType.STATUS)

    def test_classify_signal_type_control(self):
        """Test classifying control signal type."""
        signal_type = self.extractor._classify_signal_type("ctrl", "test.ctrl")
        self.assertEqual(signal_type, SignalType.CONTROL)

        signal_type = self.extractor._classify_signal_type("command", "test.command")
        self.assertEqual(signal_type, SignalType.CONTROL)

    def test_classify_signal_type_data_default(self):
        """Test classifying data signal type (default)."""
        signal_type = self.extractor._classify_signal_type("data", "test.data")
        self.assertEqual(signal_type, SignalType.DATA)

        signal_type = self.extractor._classify_signal_type("unknown_signal", "test.unknown_signal")
        self.assertEqual(signal_type, SignalType.DATA)

    def test_detect_bus_protocol_axi4(self):
        """Test detecting AXI4 bus protocol."""
        protocol = self.extractor._detect_bus_protocol("awvalid", "test.axi.awvalid")
        self.assertEqual(protocol, BusProtocol.AXI4)

        protocol = self.extractor._detect_bus_protocol("rdata", "test.axi.rdata")
        self.assertEqual(protocol, BusProtocol.AXI4)

    def test_detect_bus_protocol_axi4_lite(self):
        """Test detecting AXI4-Lite bus protocol."""
        protocol = self.extractor._detect_bus_protocol("awvalid", "test.axi_lite.awvalid")
        self.assertEqual(protocol, BusProtocol.AXI4_LITE)

    def test_detect_bus_protocol_axi4_stream(self):
        """Test detecting AXI4-Stream bus protocol."""
        protocol = self.extractor._detect_bus_protocol("tvalid", "test.axi_stream.tvalid")
        self.assertEqual(protocol, BusProtocol.AXI4_STREAM)

    def test_detect_bus_protocol_ahb(self):
        """Test detecting AHB bus protocol."""
        protocol = self.extractor._detect_bus_protocol("haddr", "test.ahb.haddr")
        self.assertEqual(protocol, BusProtocol.AHB)

        protocol = self.extractor._detect_bus_protocol("hready", "test.ahb.hready")
        self.assertEqual(protocol, BusProtocol.AHB)

    def test_detect_bus_protocol_apb(self):
        """Test detecting APB bus protocol."""
        protocol = self.extractor._detect_bus_protocol("paddr", "test.apb.paddr")
        self.assertEqual(protocol, BusProtocol.APB)

        protocol = self.extractor._detect_bus_protocol("psel", "test.apb.psel")
        self.assertEqual(protocol, BusProtocol.APB)

    def test_detect_bus_protocol_avalon(self):
        """Test detecting Avalon bus protocol."""
        protocol = self.extractor._detect_bus_protocol("avalon_read", "test.avalon_read")
        self.assertEqual(protocol, BusProtocol.AVALON)

    def test_detect_bus_protocol_wishbone(self):
        """Test detecting Wishbone bus protocol."""
        protocol = self.extractor._detect_bus_protocol("cyc", "test.wb.cyc")
        self.assertEqual(protocol, BusProtocol.WISHBONE)

        protocol = self.extractor._detect_bus_protocol("stb", "test.wb.stb")
        self.assertEqual(protocol, BusProtocol.WISHBONE)

    def test_detect_bus_protocol_none(self):
        """Test detecting no bus protocol."""
        protocol = self.extractor._detect_bus_protocol("data", "test.data")
        self.assertEqual(protocol, BusProtocol.NONE)

    def test_detect_signed_signal_from_handle(self):
        """Test detecting signed signal from handle."""
        mock_obj = Mock()
        mock_obj._handle.is_signed.return_value = True

        is_signed = self.extractor._detect_signed_signal(mock_obj)
        self.assertTrue(is_signed)

    def test_detect_signed_signal_from_type(self):
        """Test detecting signed signal from type."""
        mock_obj = Mock()
        del mock_obj._handle
        mock_obj._type = "signed_integer"

        is_signed = self.extractor._detect_signed_signal(mock_obj)
        self.assertTrue(is_signed)

    def test_detect_signed_signal_unsigned_type(self):
        """Test detecting unsigned signal from type."""
        mock_obj = Mock()
        del mock_obj._handle
        mock_obj._type = "unsigned_integer"

        is_signed = self.extractor._detect_signed_signal(mock_obj)
        self.assertFalse(is_signed)

    def test_detect_signed_signal_default(self):
        """Test detecting signed signal with default."""
        mock_obj = Mock()
        del mock_obj._handle
        del mock_obj._type

        is_signed = self.extractor._detect_signed_signal(mock_obj)
        self.assertFalse(is_signed)  # Default to unsigned

    def test_detect_array_signal_single_dimension(self):
        """Test detecting single-dimension array signal."""
        is_array, dimensions = self.extractor._detect_array_signal(Mock(), "data[5]")
        self.assertTrue(is_array)
        self.assertEqual(dimensions, [5])

    def test_detect_array_signal_multi_dimension(self):
        """Test detecting multi-dimension array signal."""
        is_array, dimensions = self.extractor._detect_array_signal(Mock(), "memory[4][8]")
        self.assertTrue(is_array)
        self.assertEqual(dimensions, [4, 8])

    def test_detect_array_signal_vhdl_style(self):
        """Test detecting VHDL-style array signal."""
        is_array, dimensions = self.extractor._detect_array_signal(Mock(), "data(5)")
        self.assertTrue(is_array)
        self.assertEqual(dimensions, [5])

    def test_detect_array_signal_not_array(self):
        """Test detecting non-array signal."""
        is_array, dimensions = self.extractor._detect_array_signal(Mock(), "data")
        self.assertFalse(is_array)
        self.assertIsNone(dimensions)

    def test_detect_clock_domain_from_path(self):
        """Test detecting clock domain from path."""
        clock_domain = self.extractor._detect_clock_domain(Mock(), "data", "cpu.clk_domain.data")
        self.assertEqual(clock_domain, "clk_domain")

    def test_detect_clock_domain_from_name(self):
        """Test detecting clock domain from signal name."""
        clock_domain = self.extractor._detect_clock_domain(Mock(), "main_clk", "cpu.main_clk")
        self.assertEqual(clock_domain, "main_clk")

    def test_detect_clock_domain_none(self):
        """Test detecting no clock domain."""
        clock_domain = self.extractor._detect_clock_domain(Mock(), "data", "cpu.data")
        self.assertIsNone(clock_domain)

    def test_detect_reset_signal(self):
        """Test detecting reset signal."""
        reset_signal = self.extractor._detect_reset_signal(Mock(), "data", "cpu.core.data")
        # Should return one of the common reset signal names
        self.assertIn(reset_signal, ["rst", "reset", "rst_n", "nrst", "arst", "srst", None])

    def test_extract_signal_metadata_complete(self):
        """Test extracting complete signal metadata."""
        mock_obj = Mock()
        mock_obj._name = "test_clk"
        mock_obj._width = 1

        metadata = self.extractor.extract_signal_metadata(mock_obj, "cpu.test_clk")

        self.assertEqual(metadata.name, "test_clk")
        self.assertEqual(metadata.width, 1)
        self.assertEqual(metadata.signal_type, SignalType.CLOCK)
        self.assertIsInstance(metadata.direction, SignalDirection)
        self.assertIsInstance(metadata.bus_protocol, BusProtocol)

    def test_extract_array_metadata_simple(self):
        """Test extracting array metadata for simple arrays."""
        hierarchy = {
            "data[0]": int,
            "data[1]": int,
            "data[2]": int,
            "data[3]": int,
        }

        arrays = self.extractor.extract_array_metadata(hierarchy)

        self.assertIn("data", arrays)
        array_meta = arrays["data"]
        self.assertEqual(array_meta.base_name, "data")
        self.assertEqual(array_meta.dimensions, [4])
        self.assertEqual(array_meta.total_elements, 4)
        self.assertFalse(array_meta.is_multidimensional)

    def test_extract_array_metadata_multidimensional(self):
        """Test extracting array metadata for multidimensional arrays."""
        hierarchy = {
            "memory[0][0]": int,
            "memory[0][1]": int,
            "memory[1][0]": int,
            "memory[1][1]": int,
        }

        arrays = self.extractor.extract_array_metadata(hierarchy)

        self.assertIn("memory", arrays)
        array_meta = arrays["memory"]
        self.assertEqual(array_meta.base_name, "memory")
        self.assertEqual(array_meta.dimensions, [2, 2])
        self.assertEqual(array_meta.total_elements, 4)
        self.assertTrue(array_meta.is_multidimensional)

    def test_extract_array_metadata_vhdl_style(self):
        """Test extracting array metadata for VHDL-style arrays."""
        hierarchy = {
            "data(0)": int,
            "data(1)": int,
            "data(2)": int,
        }

        arrays = self.extractor.extract_array_metadata(hierarchy)

        self.assertIn("data", arrays)
        array_meta = arrays["data"]
        self.assertEqual(array_meta.base_name, "data")
        self.assertEqual(array_meta.dimensions, [3])

    def test_extract_array_metadata_non_contiguous(self):
        """Test extracting array metadata for non-contiguous arrays."""
        hierarchy = {
            "data[0]": int,
            "data[2]": int,  # Missing data[1]
            "data[4]": int,
        }

        arrays = self.extractor.extract_array_metadata(hierarchy)

        self.assertIn("data", arrays)
        array_meta = arrays["data"]
        self.assertFalse(array_meta.is_contiguous)

    def test_analyze_array_structure_unrecognized_pattern(self):
        """Test analyzing array structure with unrecognized pattern."""
        hierarchy = {
            "data_weird_0": int,
            "data_weird_1": int,
        }

        # This should not be recognized as an array due to naming pattern
        arrays = self.extractor.extract_array_metadata(hierarchy)
        self.assertEqual(len(arrays), 0)


class TestModuleFunctions(unittest.TestCase):
    """Test module-level functions."""

    @patch("copra.metadata.SignalMetadataExtractor")
    def test_extract_comprehensive_metadata(self, mock_extractor_class):
        """Test extract_comprehensive_metadata function."""
        # Setup mock
        mock_extractor = Mock()
        mock_metadata = Mock()
        mock_extractor.extract_signal_metadata.return_value = mock_metadata
        mock_extractor_class.return_value = mock_extractor

        hierarchy = {
            "signal1": Mock,
            "signal2": Mock,
        }

        result = extract_comprehensive_metadata(hierarchy)

        self.assertEqual(len(result), 2)
        self.assertIn("signal1", result)
        self.assertIn("signal2", result)
        self.assertEqual(mock_extractor.extract_signal_metadata.call_count, 2)

    @patch("copra.metadata.SignalMetadataExtractor")
    def test_extract_enhanced_array_metadata(self, mock_extractor_class):
        """Test extract_enhanced_array_metadata function."""
        # Setup mock
        mock_extractor = Mock()
        mock_arrays = {"array1": Mock()}
        mock_extractor.extract_array_metadata.return_value = mock_arrays
        mock_extractor_class.return_value = mock_extractor

        hierarchy = {"signal[0]": Mock, "signal[1]": Mock}

        result = extract_enhanced_array_metadata(hierarchy)

        self.assertEqual(result, mock_arrays)
        mock_extractor.extract_array_metadata.assert_called_once_with(hierarchy)


if __name__ == "__main__":
    unittest.main()
