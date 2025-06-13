from __future__ import annotations

from pathlib import Path
from textwrap import indent
from typing import Dict, List

from .discovery import HierarchyDict

def _generate_class(name: str, tree_node: Dict, depth: int = 0) -> List[str]:
    lines = []
    node = tree_node.get("_node")
    children = tree_node.get("_children", {})
    
    if node and node.is_scope and children:
        class_name = f"{name.title().replace('_', '')}"
        lines.append(f"class {class_name}(_hdl.HierarchyObject):")
        
        for child_name, child_tree in children.items():
            child_node = child_tree.get("_node")
            if child_node:
                if child_node.is_scope and child_tree.get("_children"):
                    child_class_name = f"{child_name.title().replace('_', '')}"
                    lines.append(indent(f"{child_name}: {child_class_name}", "    "))
                else:
                    target = f"_hdl.{child_node.py_type}"
                    lines.append(indent(f"{child_name}: {target}", "    "))
        
        lines.append("")
        
        for child_name, child_tree in children.items():
            child_node = child_tree.get("_node")
            if child_node and child_node.is_scope and child_tree.get("_children"):
                lines.extend(_generate_class(child_name, child_tree, depth + 1))
    
    return lines


def generate_stub(hierarchy: HierarchyDict, out_dir: Path) -> Path:
    """Generate stub file from HierarchyDict."""
    lines: list[str] = [
        "from __future__ import annotations",
        "import cocotb.handle as _hdl",
        "",
        "",
    ]
    
    tree = hierarchy.get_tree()
    
    if not tree:
        lines.extend([
            "class DUT(_hdl.HierarchyObject):",
            "    pass",
            "",
        ])
    else:
        top_level_name = list(tree.keys())[0] if tree else "dut"
        top_tree = tree[top_level_name]
        
        lines.append("class DUT(_hdl.HierarchyObject):")
        
        children = top_tree.get("_children", {})
        for child_name, child_tree in children.items():
            child_node = child_tree.get("_node")
            if child_node:
                if child_node.is_scope and child_tree.get("_children"):
                    child_class_name = f"{child_name.title().replace('_', '')}"
                    lines.append(indent(f"{child_name}: {child_class_name}", "    "))
                else:
                    target = f"_hdl.{child_node.py_type}"
                    lines.append(indent(f"{child_name}: {target}", "    "))
        
        lines.append("")
        
        for child_name, child_tree in children.items():
            child_node = child_tree.get("_node")
            if child_node and child_node.is_scope and child_tree.get("_children"):
                lines.extend(_generate_class(child_name, child_tree))
        
        lines.append("")
    
    out_dir.mkdir(parents=True, exist_ok=True)
    text = "\n".join(lines)
    stub_path = out_dir / "dut.pyi"
    stub_path.write_text(text)
    return stub_path
