import tempfile
from pathlib import Path
from copra.discovery import HierarchyDict, HDLNode
from copra.generation import generate_stub


def test_stub_uses_actual_module_name():
    """Test that generated stubs use actual HDL module names instead of hardcoded 'DUT'."""
    hierarchy = HierarchyDict()
    
    module_node = HDLNode(
        path="test_module",
        py_type="cocotb.handle.HierarchyObject",
        width=None,
        is_scope=True
    )
    
    signal_node = HDLNode(
        path="test_module.clk",
        py_type="cocotb.handle.LogicObject",
        width=None,
        is_scope=False
    )
    
    hierarchy._nodes["test_module"] = module_node
    hierarchy._build_tree_node(module_node)
    hierarchy._nodes["test_module.clk"] = signal_node
    hierarchy._build_tree_node(signal_node)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        stub_path = generate_stub(hierarchy, Path(temp_dir))
        content = stub_path.read_text()
        
        assert "class TestModule(" in content, f"Expected 'class TestModule(' but got:\n{content}"
        assert "class DUT(" not in content, f"Found unexpected 'class DUT(' in:\n{content}"
        assert "clk: cocotb.handle.LogicObject" in content, "Expected signal definition missing"


def test_stub_handles_underscore_module_names():
    """Test that module names with underscores are properly sanitized."""
    hierarchy = HierarchyDict()
    
    module_node = HDLNode(
        path="my_complex_module",
        py_type="cocotb.handle.HierarchyObject",
        width=None,
        is_scope=True
    )
    
    hierarchy._nodes["my_complex_module"] = module_node
    hierarchy._build_tree_node(module_node)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        stub_path = generate_stub(hierarchy, Path(temp_dir))
        content = stub_path.read_text()
        assert "class MyComplexModule(" in content, f"Expected 'class MyComplexModule(' but got:\n{content}"
