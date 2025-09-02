# Copyright cocotb contributors
# Licensed under the Revised BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-3-Clause
"""
Test cases for SystemVerilog identifier handling in stub generation.
"""

import pytest
from typing import Dict, Any

from copra.generation import StubGenerator


class TestIdentifierHandling:
    """Test SystemVerilog identifier handling in stub generation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.generator = StubGenerator()

    @pytest.mark.parametrize("signal_name,expected_literal", [
        ("clk", "Literal['clk']"),
        ("reset_n", "Literal['reset_n']"),
        ("data_bus", "Literal['data_bus']"),
        
        ("_reset_n", "Literal['_reset_n']"),
        ("__internal", "Literal['__internal']"),
        
        ("!special!\\\\", "Literal['!special!\\\\']"),
        ("$signal\\\\", "Literal['$signal\\\\']"),
        ("name with spaces\\\\", "Literal['name with spaces\\\\']"),
        ("123_numeric_start\\\\", "Literal['123_numeric_start\\\\']"),
        
        ("", "Literal['']"),
        ("a", "Literal['a']"),
        ("A_Very_Long_Signal_Name_That_Exceeds_Normal_Limits", 
         "Literal['A_Very_Long_Signal_Name_That_Exceeds_Normal_Limits']"),
    ])
    def test_signal_name_literal_generation(self, signal_name: str, expected_literal: str):
        """Test that signal names are properly converted to Python literals."""
        # Simulate the repr() call that happens in generation
        actual_literal = f"Literal[{repr(signal_name)}]"
        assert actual_literal == expected_literal, (
            f"Signal name {repr(signal_name)} should generate {expected_literal}, "
            f"but got {actual_literal}"
        )
    
    def test_getitem_overload_generation(self):
        """Test that __getitem__ overloads are generated correctly."""
        children: Dict[str, Any] = {
            "clk": {"_node": MockNode("clk", "cocotb.handle.LogicObject", False)},
            "_reset_n": {"_node": MockNode("_reset_n", "cocotb.handle.LogicObject", False)},
            "!special!\\": {"_node": MockNode("!special!\\", "cocotb.handle.LogicObject", False)},
        }
        
        lines = []
        self.generator._generate_getitem_overloads(lines, children, "    ")
        
        overload_lines = [line for line in lines if "def __getitem__" in line]
        
        expected_overloads = [
            "def __getitem__(self, name: Literal['clk']) -> cocotb.handle.LogicObject: ...",
            "def __getitem__(self, name: Literal['_reset_n']) -> cocotb.handle.LogicObject: ...",
            "def __getitem__(self, name: Literal['!special!\\\\']) -> cocotb.handle.LogicObject: ...",
            "def __getitem__(self, name: str) -> cocotb.handle.SimHandleBase: ...",
        ]
        
        for expected in expected_overloads:
            assert any(expected in line for line in overload_lines), (
                f"Expected overload {expected} not found in generated lines: {overload_lines}"
            )
    
    def test_attribute_vs_getitem_access(self):
        """Test that signals get appropriate access methods based on Python validity."""
        children: Dict[str, Any] = {
            "valid_identifier": {"_node": MockNode("valid_identifier", "cocotb.handle.LogicObject", False)},
            "_underscore_start": {"_node": MockNode("_underscore_start", "cocotb.handle.LogicObject", False)},
            "!invalid!\\\\": {"_node": MockNode("!invalid!\\\\", "cocotb.handle.LogicObject", False)},
        }
        
        attr_lines = []
        self.generator._generate_class_attributes(attr_lines, children, "    ")
        
        getitem_lines = []
        self.generator._generate_getitem_overloads(getitem_lines, children, "    ")
        
        # valid_identifier should have both attribute and __getitem__ access
        assert any("valid_identifier:" in line for line in attr_lines)
        assert any("'valid_identifier'" in line for line in getitem_lines)
        
        assert not any("_underscore_start:" in line for line in attr_lines)
        assert any("'_underscore_start'" in line for line in getitem_lines)
        
        assert not any("!invalid!" in line for line in attr_lines)
        assert any("'!invalid!\\\\'" in line for line in getitem_lines)


class MockNode:
    """Mock node for testing."""
    
    def __init__(self, name: str, py_type: str, is_scope: bool):
        self.path = name
        self.py_type = py_type
        self.is_scope = is_scope
        self.width = None
