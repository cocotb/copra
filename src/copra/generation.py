from __future__ import annotations

from pathlib import Path
from textwrap import indent
from typing import Dict, List, Set

from .discovery import HDLNode
from .utils import load_pickle


_CLASS_MAP: dict[str, str] = {
    "LogicObject": "cocotb.handle.LogicObject",
    "LogicArrayObject": "cocotb.handle.LogicArrayObject",
    "HierarchyObject": "cocotb.handle.HierarchyObject",
    "HierarchyArrayObject": "cocotb.handle.HierarchyArrayObject",
    "IntegerObject": "cocotb.handle.IntegerObject",
    "RealObject": "cocotb.handle.RealObject",
    "StringObject": "cocotb.handle.StringObject",
} # TODO: no need now because we can just use the keys, did this when I didn't know there's was 1:1 mapping?


def _build_hierarchy_tree(nodes: List[HDLNode]) -> Dict:
    tree = {}
    for node in nodes:
        path_parts = node.path.split(".")
        current = tree
        
        for i, part in enumerate(path_parts):
            if part not in current:
                current[part] = {"_node": None, "_children": {}}
            
            if i == len(path_parts) - 1:
                current[part]["_node"] = node
            
            current = current[part]["_children"]
    
    return tree


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
                    target = _CLASS_MAP.get(child_node.py_type, f"cocotb.handle.{child_node.py_type}")
                    lines.append(indent(f"{child_name}: {target}", "    "))
        
        lines.append("")
        
        for child_name, child_tree in children.items():
            child_node = child_tree.get("_node")
            if child_node and child_node.is_scope and child_tree.get("_children"):
                lines.extend(_generate_class(child_name, child_tree, depth + 1))
    
    return lines


def _render(nodes: List[HDLNode]) -> str:
    lines: list[str] = [
        "from __future__ import annotations",
        "import cocotb.handle as _hdl",
        "",
        "",
    ]
    
    tree = _build_hierarchy_tree(nodes)
    
    if not tree:
        lines.extend([
            "class DUT(_hdl.HierarchyObject):",
            "    pass",
            "",
        ])
        return "\n".join(lines)
    
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
                target = _CLASS_MAP.get(child_node.py_type, f"cocotb.handle.{child_node.py_type}")
                lines.append(indent(f"{child_name}: {target}", "    "))
    
    lines.append("")
    
    for child_name, child_tree in children.items():
        child_node = child_tree.get("_node")
        if child_node and child_node.is_scope and child_tree.get("_children"):
            lines.extend(_generate_class(child_name, child_tree))
    
    lines.append("")
    return "\n".join(lines)


def generate_stub(pickle_file: Path, out_dir: Path) -> Path:
    nodes: List[HDLNode] = load_pickle(pickle_file)
    out_dir.mkdir(parents=True, exist_ok=True)
    text = _render(nodes)
    stub_path = out_dir / "dut.pyi"
    stub_path.write_text(text)
    return stub_path
