"""Tests for the analysis module."""

import tempfile
from pathlib import Path
from typing import Any, Dict
from unittest.mock import Mock, patch

import pytest
from cocotb.handle import HierarchyObject, SimHandleBase

from copra.analysis import (
    analyze_hierarchy_complexity,
    analyze_stub_coverage,
    detect_naming_patterns,
    find_unused_signals,
    generate_hierarchy_report,
    suggest_signal_groupings,
    validate_dut_interface,
    validate_hierarchy_structure,
    validate_stub_syntax,
)


class MockHandle:
    """Mock handle class for testing."""

    def __init__(self, name: str, handle_type: type, children: Dict[str, Any] = None):
        """Initialize a mock handle."""
        self._name = name
        self._handle_type = handle_type
        self._sub_handles = children or {}


@pytest.fixture
def mock_dut():
    """Create a mock DUT for testing."""
    return MockHandle(
        "test_dut",
        HierarchyObject,
        {
            "clk": MockHandle("clk", SimHandleBase),
            "rst_n": MockHandle("rst_n", SimHandleBase),
            "data_in": MockHandle("data_in", SimHandleBase),
            "data_out": MockHandle("data_out", SimHandleBase),
            "submodule": MockHandle(
                "submodule",
                HierarchyObject,
                {
                    "reg_a": MockHandle("reg_a", SimHandleBase),
                    "reg_b": MockHandle("reg_b", SimHandleBase),
                },
            ),
        },
    )


@pytest.fixture
def sample_stub_content():
    """Sample stub content for testing."""
    return '''"""Auto-generated type stubs for cocotb DUT."""

from typing import Iterator, Union
from cocotb.handle import (
    HierarchyObject,
    SimHandleBase,
)

class TestDut(HierarchyObject):
    """Auto-generated class for TestDut."""

    # Signal attributes
    clk: SimHandleBase
    rst_n: SimHandleBase
    data_in: SimHandleBase
    data_out: SimHandleBase

    # Sub-module attributes
    submodule: Submodule

class Submodule(HierarchyObject):
    """Auto-generated class for Submodule."""

    # Signal attributes
    reg_a: SimHandleBase
    reg_b: SimHandleBase

# Type alias for the main DUT
DutType = TestDut
'''


class TestAnalyzeStubCoverage:
    """Test the analyze_stub_coverage function."""

    def test_analyze_stub_coverage_complete(self, mock_dut, sample_stub_content):
        """Test coverage analysis with complete coverage."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".pyi", delete=False) as f:
            f.write(sample_stub_content)
            stub_file = f.name

        try:
            coverage = analyze_stub_coverage(mock_dut, stub_file)

            # Should have good coverage since the stub matches the DUT
            assert coverage["total_signals"] > 0
            assert coverage["covered_signals"] > 0
            assert coverage["coverage_ratio"] > 0.0
            assert isinstance(coverage["missing_signals"], list)
            assert isinstance(coverage["extra_signals"], list)
            assert coverage["stub_file"] == stub_file
        finally:
            Path(stub_file).unlink()

    def test_analyze_stub_coverage_missing_file(self, mock_dut):
        """Test coverage analysis with missing stub file."""
        coverage = analyze_stub_coverage(mock_dut, "nonexistent.pyi")

        assert coverage["coverage_ratio"] == 0.0
        assert coverage["covered_signals"] == 0
        assert len(coverage["missing_signals"]) == coverage["total_signals"]

    def test_analyze_stub_coverage_invalid_syntax(self, mock_dut):
        """Test coverage analysis with invalid stub syntax."""
        invalid_stub = "this is not valid python syntax {"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".pyi", delete=False) as f:
            f.write(invalid_stub)
            stub_file = f.name

        try:
            coverage = analyze_stub_coverage(mock_dut, stub_file)

            # Should handle invalid syntax gracefully
            assert coverage["coverage_ratio"] == 0.0
            assert coverage["covered_signals"] == 0
        finally:
            Path(stub_file).unlink()


class TestValidateDutInterface:
    """Test the validate_dut_interface function."""

    def test_validate_dut_interface_complete(self, mock_dut):
        """Test interface validation with complete expected signals."""
        expected_signals = ["clk", "rst_n", "data_in", "data_out", "submodule"]

        result = validate_dut_interface(mock_dut, expected_signals)

        assert result["valid"] is True
        assert len(result["missing_signals"]) == 0
        assert result["total_expected"] == len(expected_signals)
        assert result["total_actual"] > 0

    def test_validate_dut_interface_missing_signals(self, mock_dut):
        """Test interface validation with missing signals."""
        expected_signals = ["clk", "rst_n", "missing_signal", "another_missing"]

        result = validate_dut_interface(mock_dut, expected_signals)

        assert result["valid"] is False
        assert "missing_signal" in result["missing_signals"]
        assert "another_missing" in result["missing_signals"]
        assert result["total_expected"] == len(expected_signals)

    def test_validate_dut_interface_extra_signals(self, mock_dut):
        """Test interface validation with extra signals in DUT."""
        expected_signals = ["clk", "rst_n"]  # Only subset of actual signals

        result = validate_dut_interface(mock_dut, expected_signals)

        assert result["valid"] is True  # Valid because all expected are present
        assert len(result["extra_signals"]) > 0  # But there are extra signals
        assert "data_in" in result["extra_signals"]

    def test_validate_dut_interface_empty_expected(self, mock_dut):
        """Test interface validation with empty expected signals."""
        result = validate_dut_interface(mock_dut, [])

        assert result["valid"] is True
        assert result["total_expected"] == 0
        assert len(result["extra_signals"]) > 0


class TestValidateStubSyntax:
    """Test the validate_stub_syntax function."""

    def test_validate_stub_syntax_valid(self, sample_stub_content):
        """Test syntax validation with valid Python code."""
        assert validate_stub_syntax(sample_stub_content) is True

    def test_validate_stub_syntax_invalid(self):
        """Test syntax validation with invalid Python code."""
        invalid_code = "def invalid_function(\n    missing_closing_paren"
        assert validate_stub_syntax(invalid_code) is False

    def test_validate_stub_syntax_empty(self):
        """Test syntax validation with empty content."""
        assert validate_stub_syntax("") is True

    def test_validate_stub_syntax_comments_only(self):
        """Test syntax validation with comments only."""
        comments_only = "# This is a comment\n# Another comment"
        assert validate_stub_syntax(comments_only) is True


class TestAnalyzeHierarchyComplexity:
    """Test the analyze_hierarchy_complexity function."""

    def test_analyze_hierarchy_complexity_basic(self, mock_dut):
        """Test complexity analysis with basic hierarchy."""
        complexity = analyze_hierarchy_complexity(mock_dut)

        assert complexity["total_signals"] > 0
        assert complexity["max_depth"] >= 0
        assert complexity["module_count"] >= 0
        assert complexity["array_count"] >= 0
        assert isinstance(complexity["signal_types"], dict)

    def test_analyze_hierarchy_complexity_with_arrays(self) -> None:
        """Test hierarchy complexity analysis with arrays."""
        hierarchy = {
            "dut": HierarchyObject,
            "dut.array[0]": SimHandleBase,
            "dut.array[1]": SimHandleBase,
            "dut.array[2]": SimHandleBase,
            "dut.signal": SimHandleBase,
            "dut.array": SimHandleBase,  # Array base entry added by enhanced array detection
        }

        # The analyze_hierarchy_complexity function expects a DUT object, not a hierarchy dict
        # Let's create a mock DUT that would produce this hierarchy
        mock_dut = Mock()
        mock_dut._name = "dut"

        with patch("copra.analysis.discover_hierarchy") as mock_discover:
            mock_discover.return_value = hierarchy

            complexity = analyze_hierarchy_complexity(mock_dut)

            assert (
                complexity["total_signals"] == 5
            )  # 4 signals + 1 DUT (array base not counted separately)
            assert complexity["total_modules"] == 1
            assert complexity["max_depth"] == 1
            assert (
                complexity["array_count"] == 1
            )  # Only one array detected by the actual implementation

    def test_analyze_hierarchy_complexity_deep_hierarchy(self):
        """Test complexity analysis with deep hierarchy."""
        # Create a deeply nested hierarchy
        deep_dut = MockHandle(
            "deep_dut",
            HierarchyObject,
            {
                "level1": MockHandle(
                    "level1",
                    HierarchyObject,
                    {
                        "level2": MockHandle(
                            "level2",
                            HierarchyObject,
                            {
                                "level3": MockHandle(
                                    "level3",
                                    HierarchyObject,
                                    {
                                        "deep_signal": MockHandle("deep_signal", SimHandleBase),
                                    },
                                ),
                            },
                        ),
                    },
                ),
            },
        )

        complexity = analyze_hierarchy_complexity(deep_dut)

        assert complexity["max_depth"] >= 3  # At least 3 levels deep
        assert complexity["module_count"] >= 3  # Multiple modules

    def test_analyze_hierarchy_complexity_empty(self):
        """Test complexity analysis with empty hierarchy."""
        empty_dut = MockHandle("empty_dut", HierarchyObject, {})

        complexity = analyze_hierarchy_complexity(empty_dut)

        assert complexity["total_signals"] == 1  # Just the DUT itself
        assert complexity["max_depth"] == 0
        assert complexity["module_count"] == 0
        assert complexity["array_count"] == 0


class TestHierarchyComplexityAnalysis:
    """Test hierarchy complexity analysis functionality."""

    def test_analyze_simple_hierarchy(self):
        """Test analysis of a simple hierarchy."""
        mock_dut = Mock()
        mock_dut._name = "simple_dut"
        mock_dut._sub_handles = {
            "clk": Mock(),
            "rst_n": Mock(),
            "data_in": Mock(),
            "data_out": Mock(),
        }

        # Mock the discover_hierarchy function
        with patch("copra.analysis.discover_hierarchy") as mock_discover:
            mock_discover.return_value = {
                "dut": Mock,
                "dut.clk": Mock,
                "dut.rst_n": Mock,
                "dut.data_in": Mock,
                "dut.data_out": Mock,
            }

            analysis = analyze_hierarchy_complexity(mock_dut)

            assert analysis["total_signals"] == 4  # Excluding DUT itself
            assert analysis["total_modules"] == 1
            assert analysis["max_depth"] == 1
            assert analysis["module_count"] == 1
            assert analysis["array_count"] == 0

    def test_analyze_complex_hierarchy(self):
        """Test analysis of a complex hierarchy with nested modules."""
        mock_dut = Mock()
        mock_dut._name = "complex_dut"

        with patch("copra.analysis.discover_hierarchy") as mock_discover:
            # Create a complex hierarchy
            hierarchy = {
                "dut": Mock,
                "dut.cpu": Mock,
                "dut.cpu.clk": Mock,
                "dut.cpu.rst_n": Mock,
                "dut.cpu.alu": Mock,
                "dut.cpu.alu.a": Mock,
                "dut.cpu.alu.b": Mock,
                "dut.cpu.alu.result": Mock,
                "dut.memory": Mock,
                "dut.memory.addr": Mock,
                "dut.memory.data": Mock,
                "dut.memory.we": Mock,
                "dut.bus": Mock,
                "dut.bus.req": Mock,
                "dut.bus.ack": Mock,
                "dut.array[0]": Mock,
                "dut.array[1]": Mock,
                "dut.array[2]": Mock,
                "dut.array[3]": Mock,
            }

            mock_discover.return_value = hierarchy

            analysis = analyze_hierarchy_complexity(mock_dut)

            assert analysis["total_signals"] > 10
            assert analysis["max_depth"] == 3  # dut.cpu.alu.a
            assert analysis["module_count"] >= 3  # cpu, memory, bus
            assert analysis["array_count"] >= 1  # array signals

            # Check depth distribution
            assert 1 in analysis["depth_distribution"]
            assert 2 in analysis["depth_distribution"]
            assert 3 in analysis["depth_distribution"]

    def test_analyze_hierarchy_with_arrays(self):
        """Test analysis specifically focusing on array detection."""
        mock_dut = Mock()
        mock_dut._name = "array_dut"

        with patch("copra.analysis.discover_hierarchy") as mock_discover:
            hierarchy = {
                "dut": Mock,
                "dut.mem[0]": Mock,
                "dut.mem[1]": Mock,
                "dut.mem[2]": Mock,
                "dut.mem[3]": Mock,
                "dut.reg_file[0]": Mock,
                "dut.reg_file[1]": Mock,
                "dut.single_signal": Mock,
            }

            mock_discover.return_value = hierarchy

            analysis = analyze_hierarchy_complexity(mock_dut)

            assert analysis["array_count"] == 2  # mem and reg_file arrays
            assert "mem" in analysis["array_signals"]
            assert "reg_file" in analysis["array_signals"]
            assert len(analysis["array_signals"]["mem"]) == 4
            assert len(analysis["array_signals"]["reg_file"]) == 2

    def test_analyze_naming_patterns(self):
        """Test naming pattern detection."""
        mock_dut = Mock()
        mock_dut._name = "pattern_dut"

        with patch("copra.analysis.discover_hierarchy") as mock_discover:
            hierarchy = {
                "dut": Mock,
                "dut.clk": Mock,
                "dut.clk_div": Mock,
                "dut.rst_n": Mock,
                "dut.reset_sync": Mock,
                "dut.data_in": Mock,
                "dut.data_out": Mock,
                "dut.valid_in": Mock,
                "dut.valid_out": Mock,
                "dut.ready": Mock,
            }

            mock_discover.return_value = hierarchy

            analysis = analyze_hierarchy_complexity(mock_dut)

            # Check naming patterns
            patterns = analysis["naming_patterns"]
            assert "clk" in patterns["clock_signals"]
            assert "rst" in patterns["reset_signals"] or "reset" in patterns["reset_signals"]
            assert "in" in patterns["input_signals"]
            assert "out" in patterns["output_signals"]


class TestHierarchyReportGeneration:
    """Test hierarchy report generation."""

    def test_generate_basic_report(self):
        """Test basic report generation."""
        mock_dut = Mock()
        mock_dut._name = "test_dut"

        with patch("copra.analysis.analyze_hierarchy_complexity") as mock_analyze:
            mock_analyze.return_value = {
                "total_signals": 10,
                "total_modules": 3,
                "max_depth": 2,
                "module_count": 3,
                "array_count": 1,
                "signal_types": {"SimHandleBase": 8, "LogicArray": 2},
                "depth_distribution": {1: 5, 2: 5},
                "naming_patterns": {
                    "clock_signals": ["clk"],
                    "reset_signals": ["rst_n"],
                    "input_signals": ["in"],
                    "output_signals": ["out"],
                },
                "array_signals": {"mem": ["mem[0]", "mem[1]"]},
                "complexity_score": 15.5,
            }

            report = generate_hierarchy_report(mock_dut)

            assert "Hierarchy Analysis Report" in report
            assert "test_dut" in report
            assert "Total Signals: 10" in report
            assert "Maximum Depth: 2" in report
            assert "Array Count: 1" in report
            assert "Complexity Score: 15.5" in report

    def test_generate_report_with_output_file(self):
        """Test report generation with file output."""
        mock_dut = Mock()
        mock_dut._name = "test_dut"

        with patch("copra.analysis.analyze_hierarchy_complexity") as mock_analyze:
            mock_analyze.return_value = {
                "total_signals": 5,
                "total_modules": 1,
                "max_depth": 1,
                "module_count": 1,
                "array_count": 0,
                "signal_types": {"SimHandleBase": 5},
                "depth_distribution": {1: 5},
                "naming_patterns": {
                    "clock_signals": [],
                    "reset_signals": [],
                    "input_signals": [],
                    "output_signals": [],
                },
                "array_signals": {},
                "complexity_score": 5.0,
            }

            with patch("builtins.open", create=True) as mock_open:
                report = generate_hierarchy_report(mock_dut, "test_report.txt")

                mock_open.assert_called_once_with("test_report.txt", "w", encoding="utf-8")
                assert isinstance(report, str)


class TestUnusedSignalDetection:
    """Test unused signal detection functionality."""

    def test_find_unused_signals_basic(self):
        """Test basic unused signal detection."""
        hierarchy = {
            "dut": Mock,
            "dut.used_signal": Mock,
            "dut.unused_signal": Mock,
            "dut.another_used": Mock,
        }

        # Mock usage patterns - simulate some signals being used
        usage_patterns = {
            "dut.used_signal": ["read", "write"],
            "dut.another_used": ["read"],
            # dut.unused_signal is not in usage_patterns
        }

        with patch("copra.analysis._analyze_signal_usage", return_value=usage_patterns):
            unused = find_unused_signals(hierarchy)

            assert "dut.unused_signal" in unused
            assert "dut.used_signal" not in unused
            assert "dut.another_used" not in unused

    def test_find_unused_signals_with_exclusions(self):
        """Test unused signal detection with exclusion patterns."""
        hierarchy = {
            "dut": Mock,
            "dut.debug_signal": Mock,
            "dut.test_signal": Mock,
            "dut.normal_signal": Mock,
        }

        usage_patterns = {
            "dut.normal_signal": ["read"]
            # debug_signal and test_signal are unused
        }

        exclude_patterns = ["debug_*", "test_*"]

        with patch("copra.analysis._analyze_signal_usage", return_value=usage_patterns):
            unused = find_unused_signals(hierarchy, exclude_patterns)

            # debug_signal and test_signal should be excluded from unused list
            assert "dut.debug_signal" not in unused
            assert "dut.test_signal" not in unused
            assert "dut.normal_signal" not in unused  # This one is used


class TestNamingPatternDetection:
    """Test naming pattern detection functionality."""

    def test_detect_clock_patterns(self):
        """Test detection of clock signal patterns."""
        signal_names = ["clk", "clock", "clk_div", "sys_clk", "pci_clk", "data", "reset", "enable"]

        patterns = detect_naming_patterns(signal_names)

        clock_patterns = patterns["clock_signals"]
        assert "clk" in clock_patterns
        assert "clock" in clock_patterns

        # Should not include non-clock signals
        assert "data" not in clock_patterns
        assert "reset" not in clock_patterns

    def test_detect_reset_patterns(self):
        """Test detection of reset signal patterns."""
        signal_names = ["rst", "reset", "rst_n", "reset_sync", "sys_reset", "clk", "data", "enable"]

        patterns = detect_naming_patterns(signal_names)

        reset_patterns = patterns["reset_signals"]
        assert "rst" in reset_patterns
        assert "reset" in reset_patterns

        # Should not include non-reset signals
        assert "clk" not in reset_patterns
        assert "data" not in reset_patterns

    def test_detect_direction_patterns(self):
        """Test detection of input/output signal patterns."""
        signal_names = [
            "data_in",
            "data_out",
            "valid_in",
            "valid_out",
            "input_ready",
            "output_valid",
            "clk",
            "reset",
        ]

        patterns = detect_naming_patterns(signal_names)

        input_patterns = patterns["input_signals"]
        output_patterns = patterns["output_signals"]

        assert "in" in input_patterns
        assert "input" in input_patterns
        assert "out" in output_patterns
        assert "output" in output_patterns

    def test_detect_bus_patterns(self):
        """Test detection of bus signal patterns."""
        signal_names = [
            "axi_awaddr",
            "axi_awvalid",
            "axi_awready",
            "ahb_haddr",
            "ahb_hwrite",
            "ahb_hrdata",
            "pci_req",
            "pci_gnt",
            "single_signal",
        ]

        patterns = detect_naming_patterns(signal_names)

        bus_patterns = patterns["bus_signals"]
        assert "axi" in bus_patterns
        assert "ahb" in bus_patterns
        assert "pci" in bus_patterns


class TestSignalGroupingSuggestions:
    """Test signal grouping suggestion functionality."""

    def test_suggest_groupings_by_prefix(self):
        """Test grouping suggestions based on signal prefixes."""
        signal_names = [
            "cpu_clk",
            "cpu_rst",
            "cpu_enable",
            "mem_addr",
            "mem_data",
            "mem_we",
            "bus_req",
            "bus_ack",
            "bus_data",
            "single_signal",
        ]

        groupings = suggest_signal_groupings(signal_names)

        assert "cpu" in groupings
        assert "mem" in groupings
        assert "bus" in groupings

        assert len(groupings["cpu"]) == 3
        assert len(groupings["mem"]) == 3
        assert len(groupings["bus"]) == 3

        # Single signal should not be grouped
        assert "single" not in groupings or len(groupings.get("single", [])) < 2

    def test_suggest_groupings_by_function(self):
        """Test grouping suggestions based on signal function."""
        signal_names = [
            "clk1",
            "clk2",
            "sys_clk",
            "rst_n",
            "reset_sync",
            "por_reset",
            "data_in",
            "data_out",
            "addr_in",
            "irq0",
            "irq1",
            "irq2",
        ]

        groupings = suggest_signal_groupings(signal_names, group_by="function")

        # Should group by functional similarity
        assert any("clock" in group_name.lower() for group_name in groupings.keys())
        assert any("reset" in group_name.lower() for group_name in groupings.keys())

    def test_suggest_groupings_minimum_size(self):
        """Test grouping with minimum group size."""
        signal_names = ["group1_a", "group1_b", "group1_c", "group2_a", "group2_b", "single_signal"]

        groupings = suggest_signal_groupings(signal_names, min_group_size=3)

        # Only group1 should be included (has 3 signals)
        assert "group1" in groupings
        assert "group2" not in groupings  # Only has 2 signals
        assert len(groupings["group1"]) == 3


class TestHierarchyValidation:
    """Test hierarchy structure validation."""

    def test_validate_basic_hierarchy(self):
        """Test validation of a basic hierarchy structure."""
        hierarchy = {"dut": Mock, "dut.clk": Mock, "dut.rst_n": Mock, "dut.data": Mock}

        validation = validate_hierarchy_structure(hierarchy)

        assert validation["is_valid"] is True
        assert validation["has_root"] is True
        assert len(validation["issues"]) == 0

    def test_validate_hierarchy_without_root(self):
        """Test validation of hierarchy without proper root."""
        hierarchy = {"signal1": Mock, "signal2": Mock, "module.signal": Mock}

        validation = validate_hierarchy_structure(hierarchy)

        assert validation["is_valid"] is False
        assert validation["has_root"] is False
        assert len(validation["issues"]) > 0
        assert any("root" in issue.lower() for issue in validation["issues"])

    def test_validate_hierarchy_with_orphaned_signals(self):
        """Test validation detecting orphaned signals."""
        hierarchy = {
            "dut": Mock,
            "dut.cpu": Mock,
            "dut.cpu.clk": Mock,
            "orphaned.signal": Mock,  # This doesn't connect to dut
            "another.orphan": Mock,
        }

        validation = validate_hierarchy_structure(hierarchy)

        assert validation["is_valid"] is False
        assert len(validation["orphaned_signals"]) == 2
        assert "orphaned.signal" in validation["orphaned_signals"]
        assert "another.orphan" in validation["orphaned_signals"]

    def test_validate_hierarchy_depth_issues(self):
        """Test validation detecting depth issues."""
        # Create a very deep path
        deep_key1 = "dut.level1.level2.level3.level4.level5"
        deep_key2 = "level6.level7.level8.level9.level10.level11"
        deep_path = f"{deep_key1}.{deep_key2}"
        hierarchy = {
            "dut": Mock,
            "dut.level1": Mock,
            "dut.level1.level2": Mock,
            "dut.level1.level2.level3": Mock,
            "dut.level1.level2.level3.level4": Mock,
            "dut.level1.level2.level3.level4.level5": Mock,
            "dut.level1.level2.level3.level4.level5.level6": Mock,
            "dut.level1.level2.level3.level4.level5.level6.level7": Mock,
            "dut.level1.level2.level3.level4.level5.level6.level7.level8": Mock,
            "dut.level1.level2.level3.level4.level5.level6.level7.level8.level9": Mock,
            "dut.level1.level2.level3.level4.level5.level6.level7.level8.level9.level10": Mock,
            deep_path: Mock,
        }

        validation = validate_hierarchy_structure(hierarchy, max_depth=10)

        assert validation["is_valid"] is False
        assert validation["max_depth"] > 10
        assert len(validation["issues"]) > 0
        assert any("depth" in issue.lower() for issue in validation["issues"])


class TestAnalysisIntegration:
    """Test integration between different analysis components."""

    def test_comprehensive_analysis_workflow(self):
        """Test a comprehensive analysis workflow."""
        mock_dut = Mock()
        mock_dut._name = "comprehensive_dut"

        # Mock a realistic hierarchy
        hierarchy = {
            "dut": Mock,
            "dut.cpu": Mock,
            "dut.cpu.clk": Mock,
            "dut.cpu.rst_n": Mock,
            "dut.cpu.pc": Mock,
            "dut.cpu.instruction": Mock,
            "dut.memory": Mock,
            "dut.memory.addr": Mock,
            "dut.memory.data_in": Mock,
            "dut.memory.data_out": Mock,
            "dut.memory.we": Mock,
            "dut.cache[0]": Mock,
            "dut.cache[1]": Mock,
            "dut.cache[2]": Mock,
            "dut.cache[3]": Mock,
            "dut.debug_port": Mock,
            "dut.test_mode": Mock,
        }

        with patch("copra.analysis.discover_hierarchy", return_value=hierarchy):
            # Run comprehensive analysis
            complexity = analyze_hierarchy_complexity(mock_dut)
            report = generate_hierarchy_report(mock_dut)
            unused = find_unused_signals(hierarchy, exclude_patterns=["debug_*", "test_*"])

            signal_names = [path.split(".")[-1] for path in hierarchy.keys() if "." in path]
            patterns = detect_naming_patterns(signal_names)
            groupings = suggest_signal_groupings(signal_names)
            validation = validate_hierarchy_structure(hierarchy)

            # Verify all analyses completed successfully
            assert isinstance(complexity, dict)
            assert isinstance(report, str)
            assert isinstance(unused, list)
            assert isinstance(patterns, dict)
            assert isinstance(groupings, dict)
            assert isinstance(validation, dict)

            # Check that analyses are consistent
            assert complexity["total_signals"] > 0
            assert "comprehensive_dut" in report
            assert validation["is_valid"] in [True, False]  # Should be a boolean

    def test_analysis_with_empty_hierarchy(self):
        """Test analysis behavior with empty hierarchy."""
        mock_dut = Mock()
        mock_dut._name = "empty_dut"

        with patch("copra.analysis.discover_hierarchy", return_value={"dut": Mock}):
            complexity = analyze_hierarchy_complexity(mock_dut)

            assert complexity["total_signals"] == 0
            assert complexity["total_modules"] == 1
            assert complexity["max_depth"] == 0
            assert complexity["array_count"] == 0

    def test_analysis_error_handling(self):
        """Test analysis error handling."""
        mock_dut = Mock()
        mock_dut._name = "error_dut"

        # Test with discovery failure
        with patch("copra.analysis.discover_hierarchy", side_effect=Exception("Discovery failed")):
            with pytest.raises(Exception):
                analyze_hierarchy_complexity(mock_dut)
