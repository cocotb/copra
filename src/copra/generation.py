from __future__ import annotations

from pathlib import Path
from textwrap import indent
from typing import Dict, List, Set, Any

from .discovery import HierarchyDict
from .config import get_config

class StubGenerator:
    """Configurable stub file generator."""
    
    def __init__(self):
        self.config = get_config()
    
    def _sanitize_name(self, name: str) -> str:
        """Convert HDL name to Python class name."""
        return ''.join(word.capitalize() for word in name.split('[')[0].split('_'))
    
    def generate_stub(self, hierarchy: HierarchyDict, out_dir: Path) -> Path:
        """Generate comprehensive stub file from HierarchyDict with proper cocotb types."""
        lines: list[str] = []
        
        lines.extend(self.config.types.import_statements)
        lines.append("")
        
        for header_line in self.config.output.header_lines:
            lines.append(f"# {header_line}")
        lines.append("")
        
        tree = hierarchy.get_tree()
        
        if not tree:
            lines.extend([
                f"class {self.config.output.root_class_name}({self.config.types.base_classes['hierarchy']}):",
                "    pass",
                "",
            ])
        else:
            top_tree = tree[list(tree.keys())[0]]
            top_node = top_tree.get("_node")
            
            base_class_key = 'hierarchy'
            if top_node and self.config.types.base_classes['hierarchy_array'].split('.')[-1] in top_node.py_type:
                base_class_key = 'hierarchy_array'
            
            base_class = self.config.types.base_classes[base_class_key]
            lines.append(f"class {self.config.output.root_class_name}({base_class}):")
            
            children = top_tree.get("_children", {})
            if not children:
                lines.append("    pass")
            else:
                self._generate_class_attributes(lines, children, "    ")
            lines.append("")
            
            generated_classes: Set[str] = set()
            self._generate_all_classes(tree, lines, generated_classes)
        
        out_dir.mkdir(parents=True, exist_ok=True)
        text = "\n".join(lines)
        stub_path = out_dir / self.config.output.stub_filename
        stub_path.write_text(text)
        return stub_path

    def _generate_class_attributes(self, lines: List[str], children: Dict[str, Any], indent_str: str) -> None:
        """Generate class attributes with proper type annotations."""
        for child_name, child_tree in children.items():
            if '[' in child_name and child_name.endswith(']'):
                continue
                
            child_node = child_tree.get("_node")
            if child_node:
                if child_node.is_scope:
                    class_name = self._sanitize_name(child_name)
                    hierarchy_array_class = self.config.types.base_classes['hierarchy_array'].split('.')[-1]
                    
                    if hierarchy_array_class in child_node.py_type:
                        if "[" in child_node.py_type and "]" in child_node.py_type:
                            type_annotation = child_node.py_type
                        else:
                            type_annotation = f"{self.config.types.base_classes['hierarchy_array']}[{class_name}]"
                    else:
                        type_annotation = class_name
                else:
                    type_annotation = child_node.py_type
                
                lines.append(f"{indent_str}{child_name}: {type_annotation}")

    def _generate_all_classes(self, tree: Dict[str, Any], lines: List[str], generated_classes: Set[str]) -> None:
        """Generate all class definitions by walking the tree."""
        for name, subtree in tree.items():
            node = subtree.get("_node")
            children = subtree.get("_children", {})
            
            if node and node.is_scope and children:
                class_name = self._sanitize_name(name)
                if class_name not in generated_classes:
                    generated_classes.add(class_name)
                    
                    base_class_key = 'hierarchy'
                    hierarchy_array_class = self.config.types.base_classes['hierarchy_array'].split('.')[-1]
                    if hierarchy_array_class in node.py_type:
                        base_class_key = 'hierarchy_array'
                    
                    base_class = self.config.types.base_classes[base_class_key]
                    lines.append(f"class {class_name}({base_class}):")
                    
                    is_array_object = hierarchy_array_class in node.py_type
                    has_non_index_children = False
                    
                    for child_name, child_tree in children.items():
                        child_node = child_tree.get("_node")
                        if child_node:
                            if is_array_object:
                                try:
                                    int(child_name)
                                    continue
                                except ValueError:
                                    pass
                            
                            if '[' in child_name and child_name.endswith(']'):
                                continue
                            
                            has_non_index_children = True
                            
                            if child_node.is_scope:
                                child_class_name = self._sanitize_name(child_name)
                                if hierarchy_array_class in child_node.py_type:
                                    if "[" in child_node.py_type and "]" in child_node.py_type:
                                        type_annotation = child_node.py_type
                                    else:
                                        type_annotation = f"{self.config.types.base_classes['hierarchy_array']}[{child_class_name}]"
                                    lines.append(indent(f"{child_name}: {type_annotation}", "    "))
                                else:
                                    lines.append(indent(f"{child_name}: {child_class_name}", "    "))
                            else:
                                lines.append(indent(f"{child_name}: {child_node.py_type}", "    "))
                    
                    if not has_non_index_children:
                        lines.append("    pass")
                        
                    lines.append("")
            
            self._generate_all_classes(children, lines, generated_classes)

_generator = StubGenerator()

def generate_stub(hierarchy: HierarchyDict, out_dir: Path) -> Path:
    """Generate comprehensive stub file from HierarchyDict with proper cocotb types."""
    return _generator.generate_stub(hierarchy, out_dir)
