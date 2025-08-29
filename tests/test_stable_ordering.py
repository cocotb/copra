"""Test stable ordering in generated stubs."""

import tempfile
from pathlib import Path
from typing import List

def test_stub_ordering_is_deterministic():
    """Test that generated stubs have deterministic ordering of class attributes and overloads."""
    
    from copra.discovery import HierarchyDict, HDLNode
    from copra.generation import generate_stub
    
    hierarchy = HierarchyDict()
    
    test_signals = [
        ("z_signal", "cocotb.handle.LogicObject", False),
        ("a_signal", "cocotb.handle.LogicArrayObject", False), 
        ("m_signal", "cocotb.handle.LogicObject", False),
        ("b_bus", "cocotb.handle.HierarchyObject", True),
    ]
    
    for signal_name, py_type, is_scope in test_signals:
        node = HDLNode(
            path=f"dut.{signal_name}",
            py_type=py_type,
            width=8 if "Array" in py_type else 1,
            is_scope=is_scope
        )
        hierarchy._nodes[f"dut.{signal_name}"] = node  # type: ignore[reportPrivateUsage]
        hierarchy._build_tree_node(node)  # type: ignore[reportPrivateUsage]
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        stub_path1 = generate_stub(hierarchy, temp_path / "run1")
        content1 = stub_path1.read_text()
        
        stub_path2 = generate_stub(hierarchy, temp_path / "run2")
        content2 = stub_path2.read_text()
        
        assert content1 == content2, "Generated stubs should be deterministic"
        
        lines = content1.split('\n')
        
        in_class = False
        class_attr_lines: List[str] = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('class '):
                in_class = True
                continue
            elif stripped and in_class and not stripped.startswith('#') and not stripped.startswith('@') and not stripped.startswith('def '):
                if ':' in stripped and not stripped.startswith('class '):
                    attr_name = stripped.split(':')[0].strip()
                    class_attr_lines.append(attr_name)
                elif stripped and not stripped.startswith(' ') and not stripped.startswith('\t'):
                    # We've exited the class
                    in_class = False
        
        if len(class_attr_lines) > 1:
            # alphabetical ordering
            sorted_names = sorted(class_attr_lines)
            assert class_attr_lines == sorted_names, f"Class attributes should be in alphabetical order. Got: {class_attr_lines}, Expected: {sorted_names}"


def test_overload_ordering_is_deterministic():
    """Test that overload methods are generated in deterministic order."""
    
    from copra.discovery import HierarchyDict, HDLNode
    from copra.generation import generate_stub
    
    hierarchy = HierarchyDict()
    
    signals = ["zebra", "alpha", "beta", "gamma"] 
    for signal in signals:
        node = HDLNode(
            path=f"dut.{signal}",
            py_type="cocotb.handle.LogicObject", 
            width=1,
            is_scope=False
        )
        hierarchy._nodes[f"dut.{signal}"] = node  # type: ignore[reportPrivateUsage]
        hierarchy._build_tree_node(node)  # type: ignore[reportPrivateUsage]
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        stub_path = generate_stub(hierarchy, temp_path)
        content = stub_path.read_text()
        
        lines = content.split('\n')
        overload_lines: List[str] = []
        in_overloads = False
        
        for line in lines:
            if '@overload' in line:
                in_overloads = True
            elif in_overloads and 'def __getitem__' in line and 'Literal[' in line:
                start = line.find('Literal["') + 9
                end = line.find('"]', start)
                if start > 8 and end > start:
                    literal_value = line[start:end]
                    overload_lines.append(literal_value)
            elif in_overloads and line.strip() and not line.startswith('    ') and not line.startswith('@'):
                break
        
        if len(overload_lines) > 1:
            # alphabetical ordering
            sorted_overloads = sorted(overload_lines)
            assert overload_lines == sorted_overloads, f"Overloads should be in alphabetical order. Got: {overload_lines}, Expected: {sorted_overloads}"


if __name__ == "__main__":
    test_stub_ordering_is_deterministic()
    test_overload_ordering_is_deterministic()
    print("All ordering tests passed!")
