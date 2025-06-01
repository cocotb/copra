# Copyright cocotb contributors
# Licensed under the Revised BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-3-Clause

"""Tests for the simulation module."""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from copra.simulation import (
    DUTDiscoverySimulation,
    SimulationError,
    SimulatorDetector,
    run_discovery_simulation,
)


class TestSimulatorDetector(unittest.TestCase):
    """Test the SimulatorDetector class."""

    def setUp(self):
        """Set up test fixtures."""
        self.detector = SimulatorDetector()

    def test_supported_simulators_structure(self):
        """Test that supported simulators have correct structure."""
        for sim_name, sim_info in self.detector.SUPPORTED_SIMULATORS.items():
            self.assertIsInstance(sim_name, str)
            self.assertIn("executable", sim_info)
            self.assertIn("languages", sim_info)
            self.assertIn("interfaces", sim_info)
            self.assertIn("features", sim_info)
            self.assertIsInstance(sim_info["languages"], list)
            self.assertIsInstance(sim_info["interfaces"], list)
            self.assertIsInstance(sim_info["features"], list)

    @patch("subprocess.run")
    def test_check_simulator_available_success(self, mock_run):
        """Test successful simulator availability check."""
        mock_run.return_value.returncode = 0
        result = self.detector._check_simulator_available("iverilog")
        self.assertTrue(result)
        mock_run.assert_called_once()

    @patch("subprocess.run")
    def test_check_simulator_available_failure(self, mock_run):
        """Test failed simulator availability check."""
        mock_run.side_effect = FileNotFoundError()
        result = self.detector._check_simulator_available("nonexistent")
        self.assertFalse(result)

    @patch("subprocess.run")
    def test_check_simulator_available_timeout(self, mock_run):
        """Test simulator availability check with timeout."""
        from subprocess import TimeoutExpired

        mock_run.side_effect = TimeoutExpired("cmd", 5)
        result = self.detector._check_simulator_available("slow_sim")
        self.assertFalse(result)

    @patch.object(SimulatorDetector, "_check_simulator_available")
    def test_get_available_simulators(self, mock_check):
        """Test getting available simulators."""
        # Mock some simulators as available
        mock_check.side_effect = lambda exe: exe in ["iverilog", "verilator"]

        available = self.detector.get_available_simulators()

        # Should include icarus and verilator
        self.assertIn("icarus", available)
        self.assertIn("verilator", available)
        # Should not include others
        self.assertNotIn("questa", available)

    def test_get_simulator_info_valid(self):
        """Test getting info for valid simulator."""
        info = self.detector.get_simulator_info("icarus")
        self.assertEqual(info["executable"], "iverilog")
        self.assertIn("verilog", info["languages"])
        self.assertIn("available", info)

    def test_get_simulator_info_invalid(self):
        """Test getting info for invalid simulator."""
        with self.assertRaises(ValueError):
            self.detector.get_simulator_info("invalid_simulator")

    def test_get_best_simulator_verilog_only(self):
        """Test getting best simulator for Verilog sources."""
        with patch.object(self.detector, "get_available_simulators") as mock_available:
            mock_available.return_value = ["icarus", "verilator"]

            best = self.detector.get_best_simulator_for_sources(
                verilog_sources=["test.v"], vhdl_sources=[]
            )

            # Should prefer verilator over icarus for Verilog
            self.assertEqual(best, "verilator")

    def test_get_best_simulator_mixed_languages(self):
        """Test getting best simulator for mixed language sources."""
        with patch.object(self.detector, "get_available_simulators") as mock_available:
            mock_available.return_value = ["questa", "icarus"]

            best = self.detector.get_best_simulator_for_sources(
                verilog_sources=["test.v"], vhdl_sources=["test.vhd"]
            )

            # Should prefer questa for mixed languages
            self.assertEqual(best, "questa")

    def test_get_best_simulator_no_suitable(self):
        """Test getting best simulator when none are suitable."""
        with patch.object(self.detector, "get_available_simulators") as mock_available:
            mock_available.return_value = ["ghdl"]  # VHDL only

            with self.assertRaises(SimulationError):
                self.detector.get_best_simulator_for_sources(
                    verilog_sources=["test.v"], vhdl_sources=[]
                )

    def test_get_best_simulator_no_available(self):
        """Test getting best simulator when none are available."""
        with patch.object(self.detector, "get_available_simulators") as mock_available:
            mock_available.return_value = []

            with self.assertRaises(SimulationError):
                self.detector.get_best_simulator_for_sources(
                    verilog_sources=["test.v"], vhdl_sources=[]
                )

    def test_has_systemverilog_features_true(self):
        """Test SystemVerilog feature detection - positive case."""
        # Create a temporary file with SystemVerilog content
        with tempfile.NamedTemporaryFile(mode="w", suffix=".sv", delete=False) as f:
            f.write("interface my_interface; logic data; endinterface")
            temp_file = f.name

        try:
            result = self.detector._has_systemverilog_features(temp_file)
            self.assertTrue(result)
        finally:
            os.unlink(temp_file)

    def test_has_systemverilog_features_false(self):
        """Test SystemVerilog feature detection - negative case."""
        # Create a temporary file with plain Verilog content
        with tempfile.NamedTemporaryFile(mode="w", suffix=".v", delete=False) as f:
            f.write("module test; wire data; endmodule")
            temp_file = f.name

        try:
            result = self.detector._has_systemverilog_features(temp_file)
            self.assertFalse(result)
        finally:
            os.unlink(temp_file)

    def test_has_systemverilog_features_file_extension(self):
        """Test SystemVerilog feature detection by file extension."""
        # Test with .sv extension but no content check
        with patch("builtins.open", side_effect=OSError()):
            result = self.detector._has_systemverilog_features("test.sv")
            self.assertTrue(result)  # Should detect by extension


class TestDUTDiscoverySimulation(unittest.TestCase):
    """Test the DUTDiscoverySimulation class."""

    def setUp(self):
        """Set up test fixtures."""
        self.sim = DUTDiscoverySimulation(
            simulator="icarus",
            cleanup=False,  # Don't cleanup for testing
            timeout=5.0,
        )

    def test_init_default_values(self):
        """Test initialization with default values."""
        sim = DUTDiscoverySimulation()
        self.assertEqual(sim.simulator, "icarus")
        self.assertIsNone(sim.build_dir)
        self.assertTrue(sim.cleanup)
        self.assertEqual(sim.timeout, 30.0)

    def test_init_custom_values(self):
        """Test initialization with custom values."""
        build_dir = Path("/tmp/test_build")
        sim = DUTDiscoverySimulation(
            simulator="verilator", build_dir=str(build_dir), cleanup=False, timeout=60.0
        )
        self.assertEqual(sim.simulator, "verilator")
        self.assertEqual(sim.build_dir, build_dir)
        self.assertFalse(sim.cleanup)
        self.assertEqual(sim.timeout, 60.0)

    def test_detect_simulator(self):
        """Test simulator detection."""
        with patch.object(self.sim, "_check_executable") as mock_check:
            mock_check.side_effect = lambda exe: exe == "iverilog"

            detected = self.sim.detect_simulator()
            self.assertEqual(detected, "icarus")

    def test_detect_simulator_none_available(self):
        """Test simulator detection when none are available."""
        with patch.object(self.sim, "_check_executable", return_value=False):
            with self.assertRaises(SimulationError):
                self.sim.detect_simulator()

    @patch("copra.simulation.get_runner")
    def test_discover_dut_from_sources_no_sources(self, mock_get_runner):
        """Test discovery with no sources provided."""
        with self.assertRaises(SimulationError):
            self.sim.discover_dut_from_sources(
                verilog_sources=[], vhdl_sources=[], top_module="test"
            )

    @patch("copra.simulation.get_runner")
    @patch("tempfile.mkdtemp")
    def test_discover_dut_from_sources_success(self, mock_mkdtemp, mock_get_runner):
        """Test successful DUT discovery from sources."""
        # Mock temporary directory
        temp_dir = "/tmp/copra_test"
        mock_mkdtemp.return_value = temp_dir

        # Mock runner
        mock_runner = Mock()
        mock_get_runner.return_value = mock_runner

        # Mock DUT discovery
        mock_dut = Mock()
        mock_dut._name = "test_dut"

        with patch.object(self.sim, "_create_discovery_test") as mock_create_test, patch.object(
            self.sim, "_load_discovered_dut", return_value=mock_dut
        ):
            mock_create_test.return_value = Path(temp_dir) / "test.py"

            result = self.sim.discover_dut_from_sources(
                verilog_sources=["test.v"], top_module="test"
            )

            self.assertEqual(result, mock_dut)
            mock_runner.build.assert_called_once()
            mock_runner.test.assert_called_once()

    def test_discover_dut_from_module_success(self):
        """Test successful DUT discovery from module."""
        mock_dut = Mock()
        mock_dut._name = "test_dut"
        # Ensure the mock has the proper class name for detection
        mock_dut.__class__.__name__ = "MockDUT"

        mock_module = Mock()
        mock_module.dut = mock_dut

        with patch("importlib.import_module", return_value=mock_module):
            result = self.sim.discover_dut_from_module("test_module")
            self.assertEqual(result, mock_dut)

    def test_discover_dut_from_module_no_dut(self):
        """Test DUT discovery from module with no DUT attribute."""
        mock_module = Mock()
        # Explicitly remove all DUT-related attributes
        for attr in ["dut", "top", "toplevel", "design"]:
            if hasattr(mock_module, attr):
                delattr(mock_module, attr)

        with patch("importlib.import_module", return_value=mock_module):
            with self.assertRaises(SimulationError):
                self.sim.discover_dut_from_module("test_module")

    def test_discover_dut_from_module_import_error(self):
        """Test DUT discovery from module with import error."""
        with patch("importlib.import_module", side_effect=ImportError("Module not found")):
            with self.assertRaises(SimulationError):
                self.sim.discover_dut_from_module("nonexistent_module")

    @patch("copra.simulation.cocotb")
    def test_discover_dut_from_running_simulation_success(self, mock_cocotb):
        """Test successful DUT discovery from running simulation."""
        mock_dut = Mock()
        mock_cocotb.top = mock_dut

        result = self.sim.discover_dut_from_running_simulation()
        self.assertEqual(result, mock_dut)

    @patch("copra.simulation.cocotb")
    def test_discover_dut_from_running_simulation_no_top(self, mock_cocotb):
        """Test DUT discovery from running simulation with no top."""
        mock_cocotb.top = None

        with self.assertRaises(SimulationError):
            self.sim.discover_dut_from_running_simulation()

    def test_create_discovery_test(self):
        """Test creation of discovery test file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            self.sim._temp_dir = Path(temp_dir)

            test_file = self.sim._create_discovery_test("test_module")

            self.assertTrue(test_file.exists())
            self.assertEqual(test_file.name, "copra_discovery_test.py")

            # Check content
            content = test_file.read_text()
            self.assertIn("discover_dut_hierarchy", content)
            self.assertIn("test_module", content)

    def test_cleanup_temp_files(self):
        """Test cleanup of temporary files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            self.sim._temp_dir = Path(temp_dir)

            # Create a test file
            test_file = self.sim._temp_dir / "test.txt"
            test_file.write_text("test")
            self.assertTrue(test_file.exists())

            # Cleanup should remove the directory
            with patch("shutil.rmtree") as mock_rmtree:
                self.sim._cleanup_temp_files()
                mock_rmtree.assert_called_once_with(self.sim._temp_dir)


class TestRunDiscoverySimulation(unittest.TestCase):
    """Test the run_discovery_simulation function."""

    @patch("copra.simulation.SimulatorDetector")
    @patch("copra.simulation.DUTDiscoverySimulation")
    def test_run_discovery_simulation_auto_detect(self, mock_sim_class, mock_detector_class):
        """Test run_discovery_simulation with auto-detected simulator."""
        # Mock detector
        mock_detector = Mock()
        mock_detector.get_best_simulator_for_sources.return_value = "verilator"
        mock_detector_class.return_value = mock_detector

        # Mock simulation
        mock_sim = Mock()
        mock_dut = Mock()
        mock_sim.discover_dut_from_sources.return_value = mock_dut
        mock_sim_class.return_value = mock_sim

        result = run_discovery_simulation(top_module="test", verilog_sources=["test.v"])

        self.assertEqual(result, mock_dut)
        mock_detector.get_best_simulator_for_sources.assert_called_once()
        mock_sim.discover_dut_from_sources.assert_called_once()

    @patch("copra.simulation.DUTDiscoverySimulation")
    def test_run_discovery_simulation_specified_simulator(self, mock_sim_class):
        """Test run_discovery_simulation with specified simulator."""
        # Mock simulation
        mock_sim = Mock()
        mock_dut = Mock()
        mock_sim.discover_dut_from_sources.return_value = mock_dut
        mock_sim_class.return_value = mock_sim

        result = run_discovery_simulation(
            top_module="test", verilog_sources=["test.v"], simulator="icarus"
        )

        self.assertEqual(result, mock_dut)
        mock_sim_class.assert_called_once_with(simulator="icarus", build_dir=None, cleanup=True)

    @patch("copra.simulation.DUTDiscoverySimulation")
    def test_run_discovery_simulation_with_parameters(self, mock_sim_class):
        """Test run_discovery_simulation with parameters."""
        # Mock simulation
        mock_sim = Mock()
        mock_dut = Mock()
        mock_sim.discover_dut_from_sources.return_value = mock_dut
        mock_sim_class.return_value = mock_sim

        parameters = {"WIDTH": 32, "DEPTH": 16}

        result = run_discovery_simulation(
            top_module="test",
            verilog_sources=["test.v"],
            simulator="icarus",
            parameters=parameters,
            build_dir="/tmp/build",
            cleanup=False,
        )

        self.assertEqual(result, mock_dut)
        mock_sim.discover_dut_from_sources.assert_called_once_with(
            verilog_sources=["test.v"], vhdl_sources=None, top_module="test", parameters=parameters
        )


class TestSimulationIntegration(unittest.TestCase):
    """Integration tests for simulation functionality."""

    def test_simulation_error_inheritance(self):
        """Test that SimulationError is properly defined."""
        error = SimulationError("Test error")
        self.assertIsInstance(error, Exception)
        self.assertEqual(str(error), "Test error")

    def test_simulator_detector_singleton_behavior(self):
        """Test that SimulatorDetector behaves consistently."""
        detector1 = SimulatorDetector()
        detector2 = SimulatorDetector()

        # Should have same supported simulators
        self.assertEqual(
            detector1.SUPPORTED_SIMULATORS.keys(), detector2.SUPPORTED_SIMULATORS.keys()
        )

    @patch("copra.simulation.COCOTB_AVAILABLE", False)
    def test_cocotb_not_available(self):
        """Test behavior when cocotb is not available."""
        # When COCOTB_AVAILABLE is False, the classes should
        # still exist but may have limited functionality
        sim = DUTDiscoverySimulation()

        # The test should focus on the behavior when cocotb is not available
        # rather than trying to run a real simulation
        self.assertIsInstance(sim, DUTDiscoverySimulation)

        # Test that the simulator can be initialized even when cocotb is not available
        self.assertEqual(sim.simulator, "icarus")
        self.assertIsNone(sim._temp_dir)

        # The actual limitation would be in trying to import cocotb-specific functionality
        # But the basic class structure should still work

    def test_global_discovered_dut_variable(self):
        """Test the global _DISCOVERED_DUT variable."""
        from copra.simulation import _DISCOVERED_DUT

        # Should initially be None
        self.assertIsNone(_DISCOVERED_DUT)


if __name__ == "__main__":
    unittest.main()
