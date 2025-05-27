# Copyright cocotb contributors
# Licensed under the Revised BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-3-Clause

"""Comprehensive integration tests for copra.

This module tests the complete integration of all copra functionality,
ensuring all design requirements are met exhaustively.
"""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest

from copra import (
    discover_hierarchy,
    generate_stub,
    analyze_hierarchy,
    DUTDiscoverySimulation,
    SimulatorDetector,
    run_discovery_simulation,
    SignalMetadataExtractor,
    extract_comprehensive_metadata,
    extract_enhanced_array_metadata,
    StubGenerator,
    StubGenerationOptions,
    MockDUT,
    MockSignal,
    create_mock_dut,
    CocotbIntegration,
    cli_main,
)


class TestComprehensiveIntegration(unittest.TestCase):
    """Test comprehensive integration of all copra functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.addCleanup(self._cleanup_temp_dir)

    def _cleanup_temp_dir(self):
        """Clean up temporary directory."""
        import shutil
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    @patch('copra.simulation.COCOTB_AVAILABLE', True)
    @patch('copra.simulation.get_runner')
    def test_end_to_end_simulation_to_stub_generation(self, mock_get_runner):
        """Test complete end-to-end workflow from simulation to stub generation."""
        # Setup mock runner
        mock_runner = Mock()
        mock_get_runner.return_value = mock_runner
        
        # Create mock DUT with complex hierarchy
        mock_dut = self._create_complex_mock_dut()
        
        # Test simulation discovery
        sim = DUTDiscoverySimulation(simulator="icarus", cleanup=False)
        
        with patch.object(sim, '_load_discovered_dut', return_value=mock_dut):
            with patch.object(sim, '_create_discovery_test'):
                discovered_dut = sim.discover_dut_from_sources(
                    verilog_sources=["test.v"],
                    top_module="test_cpu"
                )
        
        # Test hierarchy discovery
        hierarchy = discover_hierarchy(discovered_dut)
        self.assertIsInstance(hierarchy, dict)
        self.assertGreater(len(hierarchy), 0)
        
        # Test metadata extraction
        metadata = extract_comprehensive_metadata(hierarchy)
        self.assertIsInstance(metadata, dict)
        
        # Test array metadata extraction
        array_metadata = extract_enhanced_array_metadata(hierarchy)
        self.assertIsInstance(array_metadata, dict)
        
        # Test analysis
        analysis = analyze_hierarchy(hierarchy)
        self.assertIsNotNone(analysis)
        
        # Test stub generation with all options
        options = StubGenerationOptions(
            flat_hierarchy=False,
            include_metadata=True,
            include_arrays=True,
            include_docstrings=True,
            typing_style="modern",
            class_prefix="",
            class_suffix="",
            output_format="pyi",
        )
        
        generator = StubGenerator(options)
        stub_content = generator.generate_stub(hierarchy, "test_cpu")
        
        self.assertIsInstance(stub_content, str)
        self.assertIn("class", stub_content)
        self.assertIn("import", stub_content)

    def test_simulator_detection_and_selection(self):
        """Test comprehensive simulator detection and selection."""
        detector = SimulatorDetector()
        
        # Test getting all supported simulators
        supported = detector.SUPPORTED_SIMULATORS
        self.assertIsInstance(supported, dict)
        self.assertGreater(len(supported), 0)
        
        # Test simulator info retrieval
        for sim_name in supported.keys():
            info = detector.get_simulator_info(sim_name)
            self.assertIn("executable", info)
            self.assertIn("languages", info)
            self.assertIn("interfaces", info)
            self.assertIn("features", info)
            self.assertIn("available", info)
        
        # Test best simulator selection
        with patch.object(detector, 'get_available_simulators') as mock_available:
            mock_available.return_value = ["icarus", "verilator", "questa"]
            
            # Test Verilog-only selection
            best = detector.get_best_simulator_for_sources(
                verilog_sources=["test.v"]
            )
            self.assertIn(best, ["icarus", "verilator", "questa"])
            
            # Test mixed-language selection
            best = detector.get_best_simulator_for_sources(
                verilog_sources=["test.v"],
                vhdl_sources=["test.vhd"]
            )
            self.assertEqual(best, "questa")  # Should prefer mixed-language simulator

    def test_comprehensive_metadata_extraction(self):
        """Test comprehensive metadata extraction for all signal types."""
        extractor = SignalMetadataExtractor()
        
        # Test all signal type classifications
        test_signals = [
            ("clk", "clock"),
            ("rst_n", "reset"),
            ("enable", "enable"),
            ("valid", "valid"),
            ("ready", "ready"),
            ("addr", "address"),
            ("status", "status"),
            ("ctrl", "control"),
            ("data", "data"),
        ]
        
        for signal_name, expected_type in test_signals:
            signal_type = extractor._classify_signal_type(signal_name, f"test.{signal_name}")
            self.assertEqual(signal_type.value, expected_type)
        
        # Test bus protocol detection
        bus_signals = [
            ("awvalid", "axi4"),
            ("haddr", "ahb"),
            ("psel", "apb"),
            ("cyc", "wishbone"),
            ("avalon_read", "avalon"),
        ]
        
        for signal_name, expected_protocol in bus_signals:
            protocol = extractor._detect_bus_protocol(signal_name, f"test.{signal_name}")
            self.assertEqual(protocol.value, expected_protocol)
        
        # Test array detection
        array_signals = [
            ("data[0]", True, [0]),
            ("memory[1][2]", True, [1, 2]),
            ("signal(3)", True, [3]),
            ("normal_signal", False, None),
        ]
        
        for signal_name, is_array, dimensions in array_signals:
            detected_array, detected_dims = extractor._detect_array_signal(Mock(), signal_name)
            self.assertEqual(detected_array, is_array)
            if is_array:
                self.assertEqual(detected_dims, dimensions)

    def test_enhanced_array_support(self):
        """Test enhanced array support functionality."""
        # Create hierarchy with various array patterns
        hierarchy = {
            # Simple 1D array
            "data[0]": Mock,
            "data[1]": Mock,
            "data[2]": Mock,
            "data[3]": Mock,
            
            # 2D array
            "memory[0][0]": Mock,
            "memory[0][1]": Mock,
            "memory[1][0]": Mock,
            "memory[1][1]": Mock,
            
            # VHDL-style array
            "vhdl_array(0)": Mock,
            "vhdl_array(1)": Mock,
            "vhdl_array(2)": Mock,
            
            # Non-contiguous array
            "sparse[0]": Mock,
            "sparse[2]": Mock,
            "sparse[5]": Mock,
            
            # Regular signals
            "clk": Mock,
            "rst": Mock,
        }
        
        array_metadata = extract_enhanced_array_metadata(hierarchy)
        
        # Verify simple array
        self.assertIn("data", array_metadata)
        data_meta = array_metadata["data"]
        self.assertEqual(data_meta.dimensions, [4])
        self.assertFalse(data_meta.is_multidimensional)
        self.assertTrue(data_meta.is_contiguous)
        
        # Verify 2D array
        self.assertIn("memory", array_metadata)
        memory_meta = array_metadata["memory"]
        self.assertEqual(memory_meta.dimensions, [2, 2])
        self.assertTrue(memory_meta.is_multidimensional)
        self.assertTrue(memory_meta.is_contiguous)
        
        # Verify VHDL array
        self.assertIn("vhdl_array", array_metadata)
        vhdl_meta = array_metadata["vhdl_array"]
        self.assertEqual(vhdl_meta.dimensions, [3])
        
        # Verify sparse array
        self.assertIn("sparse", array_metadata)
        sparse_meta = array_metadata["sparse"]
        self.assertFalse(sparse_meta.is_contiguous)

    def test_mock_dut_functionality(self):
        """Test comprehensive mock DUT functionality."""
        # Test creating mock DUT from hierarchy
        hierarchy = {
            "clk": Mock,
            "rst": Mock,
            "data_in": Mock,
            "data_out": Mock,
            "cpu.reg_file.registers[0]": Mock,
            "cpu.reg_file.registers[1]": Mock,
            "cpu.alu.result": Mock,
        }
        
        mock_dut = create_mock_dut(hierarchy, "test_cpu")
        
        # Test basic signal access
        self.assertTrue(hasattr(mock_dut, 'clk'))
        self.assertTrue(hasattr(mock_dut, 'rst'))
        self.assertTrue(hasattr(mock_dut, 'data_in'))
        self.assertTrue(hasattr(mock_dut, 'data_out'))
        
        # Test hierarchical access
        self.assertTrue(hasattr(mock_dut, 'cpu'))
        self.assertTrue(hasattr(mock_dut.cpu, 'reg_file'))
        self.assertTrue(hasattr(mock_dut.cpu, 'alu'))
        
        # Test signal behavior
        mock_signal = mock_dut.clk
        self.assertIsInstance(mock_signal, MockSignal)  # MockSignal is the correct type
        
        # Test value setting and getting
        mock_signal.value = 1
        self.assertEqual(mock_signal.value, 1)

    @patch('copra.cli.run_discovery_simulation')
    @patch('copra.cli.discover_hierarchy')
    @patch('copra.cli.StubGenerator')
    def test_cli_integration_comprehensive(self, mock_generator_class, mock_discover, mock_run_sim):
        """Test comprehensive CLI integration."""
        # Setup mocks
        mock_dut = self._create_complex_mock_dut()
        mock_hierarchy = self._create_complex_hierarchy()
        
        mock_run_sim.return_value = mock_dut
        mock_discover.return_value = mock_hierarchy
        
        mock_generator = Mock()
        mock_generator.generate_stub.return_value = "comprehensive stub content"
        mock_generator_class.return_value = mock_generator
        
        # Test generate command with all options
        with patch('sys.argv', [
            'copra',
            '--sources', 'cpu.sv', 'alu.sv',
            '--top', 'test_cpu',
            '--simulator', 'icarus',
            '--outfile', str(self.temp_dir / 'cpu.pyi'),
            '--include-metadata',
            '--array-detection',
            '--include-constants',
            '--verbose'
        ]):
            with patch('builtins.open', create=True) as mock_open:
                result = cli_main()
        
        self.assertEqual(result, 0)
        mock_run_sim.assert_called_once()
        mock_discover.assert_called_once()
        mock_generator.generate_stub.assert_called_once()

    def test_cocotb_integration_workflow(self):
        """Test cocotb integration workflow."""
        integration = CocotbIntegration()
        
        # Test makefile integration
        makefile_content = integration.generate_makefile_integration(
            top_module="test_cpu",
            sources=["cpu.sv", "alu.sv"],
            simulator="icarus"
        )
        
        self.assertIsInstance(makefile_content, str)
        self.assertIn("test_cpu", makefile_content)
        self.assertIn("icarus", makefile_content)
        
        # Test test file integration
        test_content = integration.generate_test_integration(
            top_module="test_cpu",
            stub_file="cpu.pyi"
        )
        
        self.assertIsInstance(test_content, str)
        self.assertIn("@cocotb.test()", test_content)
        self.assertIn("test_cpu", test_content)

    def test_error_handling_comprehensive(self):
        """Test comprehensive error handling across all modules."""
        # Test simulation errors
        sim = DUTDiscoverySimulation()
        
        with self.assertRaises(Exception):  # SimulationError or similar
            sim.discover_dut_from_sources(top_module="nonexistent")
        
        # Test detector errors
        detector = SimulatorDetector()
        
        with self.assertRaises(ValueError):
            detector.get_simulator_info("nonexistent_simulator")
        
        # Test metadata extractor with invalid inputs
        extractor = SignalMetadataExtractor()
        
        # Should handle gracefully
        metadata = extractor.extract_signal_metadata(Mock(), "")
        self.assertIsNotNone(metadata)

    def test_performance_with_large_hierarchy(self):
        """Test performance with large hierarchies."""
        # Create large hierarchy (1000+ signals)
        large_hierarchy = {}
        
        # Add regular signals
        for i in range(500):
            large_hierarchy[f"signal_{i}"] = Mock
        
        # Add arrays
        for i in range(10):
            for j in range(50):
                large_hierarchy[f"array_{i}[{j}]"] = Mock
        
        # Test hierarchy analysis performance
        import time
        start_time = time.time()
        
        analysis = analyze_hierarchy(large_hierarchy)
        metadata = extract_comprehensive_metadata(large_hierarchy)
        array_metadata = extract_enhanced_array_metadata(large_hierarchy)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Should complete within reasonable time (adjust threshold as needed)
        self.assertLess(processing_time, 10.0)  # 10 seconds max
        
        # Verify results
        self.assertIsNotNone(analysis)
        self.assertGreater(len(metadata), 0)
        self.assertGreater(len(array_metadata), 0)

    def test_stub_generation_all_formats(self):
        """Test stub generation in all supported formats."""
        hierarchy = self._create_complex_hierarchy()
        
        # Test .pyi format
        options_pyi = StubGenerationOptions(output_format="pyi")
        generator_pyi = StubGenerator(options_pyi)
        stub_pyi = generator_pyi.generate_stub(hierarchy, "test_cpu")
        
        self.assertIsInstance(stub_pyi, str)
        self.assertIn("import", stub_pyi)
        self.assertIn("class", stub_pyi)
        
        # Test .py format
        options_py = StubGenerationOptions(output_format="py")
        generator_py = StubGenerator(options_py)
        stub_py = generator_py.generate_stub(hierarchy, "test_cpu")
        
        self.assertIsInstance(stub_py, str)
        self.assertIn("import", stub_py)
        self.assertIn("class", stub_py)
        
        # Verify differences between formats
        self.assertNotEqual(stub_pyi, stub_py)

    def test_typing_styles_compatibility(self):
        """Test all typing styles for compatibility."""
        hierarchy = self._create_complex_hierarchy()
        
        typing_styles = ["modern", "legacy", "compatible"]
        
        for style in typing_styles:
            options = StubGenerationOptions(typing_style=style)
            generator = StubGenerator(options)
            stub_content = generator.generate_stub(hierarchy, "test_cpu")
            
            self.assertIsInstance(stub_content, str)
            self.assertIn("import", stub_content)
            
            # Verify style-specific content
            if style == "modern":
                # Modern style should use newer typing features
                pass  # Add specific checks when implemented
            elif style == "legacy":
                # Legacy style should use older typing
                pass  # Add specific checks when implemented

    def _create_complex_mock_dut(self):
        """Create a complex mock DUT for testing."""
        mock_dut = Mock()
        mock_dut._name = "test_cpu"
        mock_dut._handle_type = Mock()
        mock_dut._handle_type.__name__ = "HierarchyObject"
        
        # Add signals with proper mock setup
        mock_dut.clk = Mock()
        mock_dut.clk._name = "clk"
        mock_dut.clk._handle_type = Mock()
        mock_dut.clk._handle_type.__name__ = "SimHandleBase"
        
        mock_dut.rst = Mock()
        mock_dut.rst._name = "rst"
        mock_dut.rst._handle_type = Mock()
        mock_dut.rst._handle_type.__name__ = "SimHandleBase"
        
        return mock_dut

    def _create_complex_hierarchy(self):
        """Create a complex hierarchy for testing."""
        # Create a mock class that has __name__ attribute
        class MockType:
            def __init__(self, name):
                self.__name__ = name
        
        return {
            "clk": MockType("SimHandleBase"),
            "rst": MockType("SimHandleBase"),
            "data_in": MockType("SimHandleBase"),
            "data_out": MockType("SimHandleBase"),
            "cpu.alu.result": MockType("SimHandleBase"),
            "cpu.reg_file.registers[0]": MockType("SimHandleBase"),
            "cpu.reg_file.registers[1]": MockType("SimHandleBase"),
            "cpu.reg_file.registers[2]": MockType("SimHandleBase"),
            "cpu.reg_file.registers[3]": MockType("SimHandleBase"),
            "memory[0]": MockType("SimHandleBase"),
            "memory[1]": MockType("SimHandleBase"),
            "memory[2]": MockType("SimHandleBase"),
            "memory[3]": MockType("SimHandleBase"),
            "bus.awvalid": MockType("SimHandleBase"),
            "bus.awready": MockType("SimHandleBase"),
            "bus.awaddr": MockType("SimHandleBase"),
            "bus.wdata": MockType("SimHandleBase"),
            "status.error_flag": MockType("SimHandleBase"),
            "control.enable": MockType("SimHandleBase"),
        }


class TestDesignRequirementsCompliance(unittest.TestCase):
    """Test compliance with all design requirements from design.md."""

    def test_accurate_dut_representation(self):
        """Test that DUT representation is accurate and faithful."""
        # This tests Design Goal 1: Accurate DUT Repr
        mock_dut = Mock()
        mock_dut._name = "test_dut"
        mock_dut._handle_type = Mock()
        mock_dut._handle_type.__name__ = "HierarchyObject"
        
        # Add various signal types with proper mock setup
        mock_dut.clk = Mock()
        mock_dut.clk._name = "clk"
        mock_dut.clk._handle_type = Mock()
        mock_dut.clk._handle_type.__name__ = "SimHandleBase"
        
        mock_dut.rst = Mock()
        mock_dut.rst._name = "rst"
        mock_dut.rst._handle_type = Mock()
        mock_dut.rst._handle_type.__name__ = "SimHandleBase"
        
        mock_dut.data = Mock()
        mock_dut.data._name = "data"
        mock_dut.data._handle_type = Mock()
        mock_dut.data._handle_type.__name__ = "SimHandleBase"
        
        mock_dut.sub_module = Mock()
        mock_dut.sub_module._name = "sub_module"
        mock_dut.sub_module._handle_type = Mock()
        mock_dut.sub_module._handle_type.__name__ = "HierarchyObject"
        mock_dut.sub_module.signal = Mock()
        mock_dut.sub_module.signal._name = "signal"
        mock_dut.sub_module.signal._handle_type = Mock()
        mock_dut.sub_module.signal._handle_type.__name__ = "SimHandleBase"
        
        # Mock the _sub_handles attribute for proper hierarchy discovery
        mock_dut._sub_handles = {
            "clk": mock_dut.clk,
            "rst": mock_dut.rst,
            "data": mock_dut.data,
            "sub_module": mock_dut.sub_module,
        }
        
        mock_dut.sub_module._sub_handles = {
            "signal": mock_dut.sub_module.signal,
        }
        
        hierarchy = discover_hierarchy(mock_dut)
        
        # Verify all signals are captured
        self.assertIn("test_dut.clk", hierarchy)
        self.assertIn("test_dut.rst", hierarchy)
        self.assertIn("test_dut.data", hierarchy)
        self.assertIn("test_dut.sub_module.signal", hierarchy)

    def test_ease_of_use_one_step_generation(self):
        """Test that stub generation is a one-step process."""
        # This tests Design Goal 2: Ease of Use via a One-Step Generation
        with patch('copra.simulation.run_discovery_simulation') as mock_sim:
            with patch('copra.core.discover_hierarchy') as mock_discover:
                with patch('copra.generation.StubGenerator') as mock_generator_class:
                    
                    mock_dut = Mock()
                    mock_hierarchy = {"signal": Mock}
                    mock_generator = Mock()
                    mock_generator.generate_stub.return_value = "stub content"
                    
                    mock_sim.return_value = mock_dut
                    mock_discover.return_value = mock_hierarchy
                    mock_generator_class.return_value = mock_generator
                    
                    # Single command should work
                    from copra.cli import handle_generate_command
                    from argparse import Namespace
                    
                    args = Namespace(
                        top_module="test",
                        verilog=["test.v"],
                        vhdl=None,
                        simulator="icarus",
                        parameters=None,
                        build_dir=None,
                        no_cleanup=False,
                        output=None,
                        output_dir=None,
                        format="pyi",
                        flat_hierarchy=False,
                        include_metadata=False,
                        include_arrays=False,
                        include_docstrings=False,
                        typing_style="modern",
                        class_prefix="",
                        class_suffix="",
                        verbose=0,
                    )
                    
                    with patch('builtins.open', create=True):
                        result = handle_generate_command(args)
                    
                    self.assertEqual(result, 0)

    def test_non_intrusive_integration(self):
        """Test that integration is non-intrusive."""
        # This tests Design Goal 3: Non-Intrusive Integration
        
        # Should work with cocotb-only functionality
        integration = CocotbIntegration()
        
        # Should not require modifications to DUT RTL
        makefile_content = integration.generate_makefile_integration(
            top_module="test_dut",
            sources=["test.v"],
            simulator="icarus"
        )
        
        # Should be add-on only
        self.assertIsInstance(makefile_content, str)
        self.assertIn("copra", makefile_content.lower())

    def test_intuitive_usage_consistent_with_stub_toolings(self):
        """Test that usage is intuitive and consistent."""
        # This tests Design Goal 4: Intuitive Usage
        
        # .pyi files should be generated in standard location
        options = StubGenerationOptions(output_format="pyi")
        generator = StubGenerator(options)
        
        hierarchy = {"signal": Mock}
        stub_content = generator.generate_stub(hierarchy, "test_dut")
        
        # Should generate valid Python stub syntax
        self.assertIsInstance(stub_content, str)
        self.assertIn("import", stub_content)

    def test_hierarchical_vs_flat_type_definitions(self):
        """Test hierarchical vs flat type definitions."""
        # This tests Design Goal 5: Hierarchical vs. Flat Type Definitions
        
        hierarchy = {
            "top.sub1.signal1": Mock,
            "top.sub1.signal2": Mock,
            "top.sub2.signal3": Mock,
        }
        
        # Test hierarchical generation
        options_hierarchical = StubGenerationOptions(flat_hierarchy=False)
        generator_hierarchical = StubGenerator(options_hierarchical)
        stub_hierarchical = generator_hierarchical.generate_stub(hierarchy, "top")
        
        # Test flat generation
        options_flat = StubGenerationOptions(flat_hierarchy=True)
        generator_flat = StubGenerator(options_flat)
        stub_flat = generator_flat.generate_stub(hierarchy, "top")
        
        # Should produce different outputs
        self.assertNotEqual(stub_hierarchical, stub_flat)

    def test_arrays_and_generators_support(self):
        """Test support for arrays and generators."""
        # This tests Design Goal 6: Arrays and Generators
        
        hierarchy = {
            "registers[0]": Mock,
            "registers[1]": Mock,
            "registers[2]": Mock,
            "registers[3]": Mock,
        }
        
        array_metadata = extract_enhanced_array_metadata(hierarchy)
        
        self.assertIn("registers", array_metadata)
        array_meta = array_metadata["registers"]
        self.assertEqual(array_meta.dimensions, [4])
        self.assertTrue(array_meta.is_contiguous)

    def test_typing_information_and_python_versions(self):
        """Test typing information and Python version compatibility."""
        # This tests Design Goal 7: Typing Information and Python Versions
        
        for typing_style in ["modern", "legacy", "compatible"]:
            options = StubGenerationOptions(typing_style=typing_style)
            generator = StubGenerator(options)
            
            hierarchy = {"signal": Mock}
            stub_content = generator.generate_stub(hierarchy, "test")
            
            # Should generate valid typing syntax
            self.assertIsInstance(stub_content, str)
            self.assertIn("import", stub_content)

    def test_pyi_vs_py_solution(self):
        """Test .pyi vs .py solution."""
        # This tests Design Goal 8: Solution for .pyi vs .py dilemma
        
        hierarchy = {"signal": Mock}
        
        # Test .pyi generation
        options_pyi = StubGenerationOptions(output_format="pyi")
        generator_pyi = StubGenerator(options_pyi)
        stub_pyi = generator_pyi.generate_stub(hierarchy, "test")
        
        # Test .py generation
        options_py = StubGenerationOptions(output_format="py")
        generator_py = StubGenerator(options_py)
        stub_py = generator_py.generate_stub(hierarchy, "test")
        
        # Both should work
        self.assertIsInstance(stub_pyi, str)
        self.assertIsInstance(stub_py, str)


if __name__ == "__main__":
    unittest.main() 