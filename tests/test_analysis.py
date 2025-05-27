"""Tests for the copra.analysis module."""

import tempfile
from pathlib import Path
from typing import Any, Dict
from unittest.mock import Mock

import pytest
from cocotb.handle import HierarchyObject, LogicObject

from copra.analysis import (
    analyze_hierarchy_complexity,
    analyze_stub_coverage,
    validate_dut_interface,
    validate_stub_syntax,
)
from copra.core import discover_hierarchy


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
            "clk": MockHandle("clk", LogicObject),
            "rst_n": MockHandle("rst_n", LogicObject),
            "data_in": MockHandle("data_in", LogicObject),
            "data_out": MockHandle("data_out", LogicObject),
            "submodule": MockHandle(
                "submodule",
                HierarchyObject,
                {
                    "reg_a": MockHandle("reg_a", LogicObject),
                    "reg_b": MockHandle("reg_b", LogicObject),
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
    LogicObject,
)

class TestDut(HierarchyObject):
    """Auto-generated class for TestDut."""
    
    # Signal attributes
    clk: LogicObject
    rst_n: LogicObject
    data_in: LogicObject
    data_out: LogicObject
    
    # Sub-module attributes
    submodule: Submodule

class Submodule(HierarchyObject):
    """Auto-generated class for Submodule."""
    
    # Signal attributes
    reg_a: LogicObject
    reg_b: LogicObject

# Type alias for the main DUT
DutType = TestDut
'''


class TestAnalyzeStubCoverage:
    """Test the analyze_stub_coverage function."""

    def test_analyze_stub_coverage_complete(self, mock_dut, sample_stub_content):
        """Test coverage analysis with complete coverage."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.pyi', delete=False) as f:
            f.write(sample_stub_content)
            stub_file = f.name

        try:
            coverage = analyze_stub_coverage(mock_dut, stub_file)
            
            # Should have good coverage since the stub matches the DUT
            assert coverage['total_signals'] > 0
            assert coverage['covered_signals'] > 0
            assert coverage['coverage_ratio'] > 0.0
            assert isinstance(coverage['missing_signals'], list)
            assert isinstance(coverage['extra_signals'], list)
            assert coverage['stub_file'] == stub_file
        finally:
            Path(stub_file).unlink()

    def test_analyze_stub_coverage_missing_file(self, mock_dut):
        """Test coverage analysis with missing stub file."""
        coverage = analyze_stub_coverage(mock_dut, "nonexistent.pyi")
        
        assert coverage['coverage_ratio'] == 0.0
        assert coverage['covered_signals'] == 0
        assert len(coverage['missing_signals']) == coverage['total_signals']

    def test_analyze_stub_coverage_invalid_syntax(self, mock_dut):
        """Test coverage analysis with invalid stub syntax."""
        invalid_stub = "this is not valid python syntax {"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.pyi', delete=False) as f:
            f.write(invalid_stub)
            stub_file = f.name

        try:
            coverage = analyze_stub_coverage(mock_dut, stub_file)
            
            # Should handle invalid syntax gracefully
            assert coverage['coverage_ratio'] == 0.0
            assert coverage['covered_signals'] == 0
        finally:
            Path(stub_file).unlink()


class TestValidateDutInterface:
    """Test the validate_dut_interface function."""

    def test_validate_dut_interface_complete(self, mock_dut):
        """Test interface validation with complete expected signals."""
        expected_signals = ["clk", "rst_n", "data_in", "data_out", "submodule"]
        
        result = validate_dut_interface(mock_dut, expected_signals)
        
        assert result['valid'] is True
        assert len(result['missing_signals']) == 0
        assert result['total_expected'] == len(expected_signals)
        assert result['total_actual'] > 0

    def test_validate_dut_interface_missing_signals(self, mock_dut):
        """Test interface validation with missing signals."""
        expected_signals = ["clk", "rst_n", "missing_signal", "another_missing"]
        
        result = validate_dut_interface(mock_dut, expected_signals)
        
        assert result['valid'] is False
        assert "missing_signal" in result['missing_signals']
        assert "another_missing" in result['missing_signals']
        assert result['total_expected'] == len(expected_signals)

    def test_validate_dut_interface_extra_signals(self, mock_dut):
        """Test interface validation with extra signals in DUT."""
        expected_signals = ["clk", "rst_n"]  # Only subset of actual signals
        
        result = validate_dut_interface(mock_dut, expected_signals)
        
        assert result['valid'] is True  # Valid because all expected are present
        assert len(result['extra_signals']) > 0  # But there are extra signals
        assert "data_in" in result['extra_signals']

    def test_validate_dut_interface_empty_expected(self, mock_dut):
        """Test interface validation with empty expected signals."""
        result = validate_dut_interface(mock_dut, [])
        
        assert result['valid'] is True
        assert result['total_expected'] == 0
        assert len(result['extra_signals']) > 0


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
        
        assert complexity['total_signals'] > 0
        assert complexity['max_depth'] >= 0
        assert complexity['module_count'] >= 0
        assert complexity['array_count'] >= 0
        assert isinstance(complexity['signal_types'], dict)

    def test_analyze_hierarchy_complexity_with_arrays(self):
        """Test complexity analysis with array structures."""
        # Create a DUT with array-like signals
        array_dut = MockHandle(
            "array_dut",
            HierarchyObject,
            {
                "signal[0]": MockHandle("signal[0]", LogicObject),
                "signal[1]": MockHandle("signal[1]", LogicObject),
                "signal[2]": MockHandle("signal[2]", LogicObject),
                "normal_signal": MockHandle("normal_signal", LogicObject),
            },
        )
        
        complexity = analyze_hierarchy_complexity(array_dut)
        
        assert complexity['array_count'] == 3  # Three array elements
        assert complexity['total_signals'] == 5  # 4 signals + 1 DUT
        assert 'LogicObject' in complexity['signal_types']

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
                                        "deep_signal": MockHandle("deep_signal", LogicObject),
                                    },
                                ),
                            },
                        ),
                    },
                ),
            },
        )
        
        complexity = analyze_hierarchy_complexity(deep_dut)
        
        assert complexity['max_depth'] >= 3  # At least 3 levels deep
        assert complexity['module_count'] >= 3  # Multiple modules

    def test_analyze_hierarchy_complexity_empty(self):
        """Test complexity analysis with empty hierarchy."""
        empty_dut = MockHandle("empty_dut", HierarchyObject, {})
        
        complexity = analyze_hierarchy_complexity(empty_dut)
        
        assert complexity['total_signals'] == 1  # Just the DUT itself
        assert complexity['max_depth'] == 0
        assert complexity['module_count'] == 0
        assert complexity['array_count'] == 0 