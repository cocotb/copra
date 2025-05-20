"""Tests for the copra.stubgen module."""

from pathlib import Path
from typing import Dict, Type

import pytest
from cocotb.handle import HierarchyObject, ModifiableObject, NonHierarchyObject

from copra.stubgen import discover_hierarchy, generate_stub


class MockHandle:
    """Mock handle class for testing."""
    
    def __init__(self, name: str, handle_type: Type, children: Dict[str, 'MockHandle'] = None):
        self._name = name
        self._type = handle_type
        self._sub_handles = children or {}
    
    def __repr__(self) -> str:
        return f"<MockHandle {self._name} type={self._type.__name__}>"


@pytest.fixture
def mock_dut() -> MockHandle:
    """Create a mock DUT hierarchy for testing."""
    return MockHandle(
        "dut",
        HierarchyObject,
        {
            "clk": MockHandle("clk", ModifiableObject),
            "rst_n": MockHandle("rst_n", ModifiableObject),
            "data_in": MockHandle("data_in", ModifiableObject),
            "data_out": MockHandle("data_out", ModifiableObject),
            "submodule": MockHandle(
                "submodule",
                HierarchyObject,
                {
                    "reg_a": MockHandle("reg_a", ModifiableObject),
                    "reg_b": MockHandle("reg_b", ModifiableObject),
                },
            ),
        },
    )


def test_discover_hierarchy(mock_dut: MockHandle) -> None:
    """Test discovery of hierarchy from a DUT."""
    hierarchy = discover_hierarchy(mock_dut)
    
    # Check that all expected paths are present
    expected_paths = {
        "dut",
        "dut.clk",
        "dut.rst_n",
        "dut.data_in",
        "dut.data_out",
        "dut.submodule",
        "dut.submodule.reg_a",
        "dut.submodule.reg_b",
    }
    
    assert set(hierarchy.keys()) == expected_paths
    
    # Check some type mappings
    assert hierarchy["dut"] is HierarchyObject
    assert hierarchy["dut.clk"] is ModifiableObject
    assert hierarchy["dut.submodule"] is HierarchyObject
    assert hierarchy["dut.submodule.reg_a"] is ModifiableObject


def test_generate_stub(mock_dut: MockHandle, tmp_path: Path) -> None:
    """Test generation of stub file content."""
    hierarchy = discover_hierarchy(mock_dut)
    stub_content = generate_stub(hierarchy)
    
    # Basic checks on the generated content
    assert "class dut(HierarchyObject):" in stub_content
    assert "class clk(dut):" in stub_content
    assert "class submodule(dut):" in stub_content
    assert "class reg_a(submodule):" in stub_content
    
    # Check for imports
    assert "from cocotb.handle import" in stub_content
    assert "HierarchyObject" in stub_content
    assert "ModifiableObject" in stub_content
    
    # Check that the content is valid Python syntax
    compile(stub_content, "<string>", "exec")
