from pathlib import Path
from copra.discovery import HierarchyDict, HDLNode
from copra.generation import generate_stub


def test_stub_uses_actual_module_name(tmp_path: Path):
    """Test that generated stubs use actual HDL module names instead of hardcoded 'DUT'."""
    hierarchy = HierarchyDict()
    
    test_module_node = HDLNode(
        path="test_module",
        py_type="cocotb.handle.HierarchyObject",
        width=None,
        is_scope=True
    )
    
    test_signal_node = HDLNode(
        path="test_module.clk",
        py_type="cocotb.handle.LogicObject",
        width=None,
        is_scope=False
    )
    
    hierarchy._nodes["test_module"] = test_module_node # type: ignore
    hierarchy._build_tree_node(test_module_node) # type: ignore
    hierarchy._nodes["test_module.clk"] = test_signal_node # type: ignore
    hierarchy._build_tree_node(test_signal_node) # type: ignore
    
    stub_path = generate_stub(hierarchy, tmp_path)
    content = stub_path.read_text()
    
    assert "class TestModule(" in content, f"Expected 'class TestModule(' but got:\n{content}"
    assert "class DUT(" not in content, f"Found unexpected 'class DUT(' in:\n{content}"
    assert "clk: cocotb.handle.LogicObject" in content, "Expected signal definition missing"


def test_stub_handles_underscore_module_names(tmp_path: Path):
    """Test that module names with underscores are properly sanitized."""
    hierarchy = HierarchyDict()
    
    complex_module_node = HDLNode(
        path="my_complex_module",
        py_type="cocotb.handle.HierarchyObject",
        width=None,
        is_scope=True
    )
    
    hierarchy._nodes["my_complex_module"] = complex_module_node # type: ignore
    hierarchy._build_tree_node(complex_module_node) # type: ignore
    
    stub_path = generate_stub(hierarchy, tmp_path)
    content = stub_path.read_text()
    assert "class MyComplexModule(" in content, f"Expected 'class MyComplexModule(' but got:\n{content}"
