from __future__ import annotations

from pathlib import Path
from textwrap import indent
from typing import Dict, List, Set, Any

from .discovery import HierarchyDict
from .config import get_config
from .introspection import sanitize_name

class StubGenerator:
    """Configurable stub file generator."""
    
    def __init__(self):
        self.config = get_config()
    
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
            top_key = list(tree.keys())[0]
            top_tree = tree[top_key]
            top_node = top_tree.get("_node")
            
            top_class_name = sanitize_name(top_key)
            
            base_class_key = 'hierarchy'
            if top_node and self.config.types.base_classes['hierarchy_array'].split('.')[-1] in top_node.py_type:
                base_class_key = 'hierarchy_array'
            
            base_class = self.config.types.base_classes[base_class_key]
            lines.append(f"class {top_class_name}({base_class}):")
            
            children = top_tree.get("_children", {})
            if not children:
                lines.append("    pass")
            else:
                self._generate_class_attributes(lines, children, "    ", filter_deep_signals=True)
            lines.append("")
            
            generated_classes: Set[str] = set()
            self._generate_meaningful_classes(tree, lines, generated_classes, top_class_name)
        
        out_dir.mkdir(parents=True, exist_ok=True)
        text = "\n".join(lines)
        stub_path = out_dir / self.config.output.stub_filename
        stub_path.write_text(text)
        return stub_path

    def _generate_class_attributes(self, lines: List[str], children: Dict[str, Any], indent_str: str, filter_deep_signals: bool = False) -> None:
        """Generate class attributes with proper type annotations."""
        for child_name, child_tree in sorted(children.items()):
            if '[' in child_name and child_name.endswith(']'):
                continue
                
            child_node = child_tree.get("_node")
            if child_node:
                if filter_deep_signals:
                    if not child_node.is_scope and '.' in child_node.path and child_node.path.count('.') > 1:
                        continue
                
                if child_node.is_scope:
                    class_name = sanitize_name(child_name)
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
                
    def _should_add_value_property(self, py_type: str) -> bool:
        """Check if we should add a value type annotation for this handle type."""
        return any(handle_type in py_type for handle_type in self.config.types.patterns.value_object_patterns)

    def _get_value_type_annotation(self, py_type: str) -> str:
        """Get the value type annotation for a handle type."""
        if 'ArrayObject[' in py_type:
            start = py_type.find('[') + 1
            depth = 1
            end = start
            while end < len(py_type) and depth > 0:
                if py_type[end] == '[':
                    depth += 1
                elif py_type[end] == ']':
                    depth -= 1
                elif py_type[end] == ',' and depth == 1:
                    break
                end += 1
            
            if end < len(py_type):
                element_type = py_type[start:end].strip()
                return f"cocotb.types.Array[{element_type}]"
        
        for handle_type, value_type in self.config.types.value_annotations.items():
            if handle_type in py_type:
                return value_type
        
        return "Any"

    def _generate_meaningful_classes(self, tree: Dict[str, Any], lines: List[str], generated_classes: Set[str], top_class_name: str) -> None:
        """Generate class definitions only for nodes that represent meaningful nested modules."""
        for name, subtree in sorted(tree.items()):
            node = subtree.get("_node")
            children = subtree.get("_children", {})
            
            if node and node.is_scope and children and name != list(tree.keys())[0]:
                class_name = sanitize_name(name)
                if class_name not in generated_classes and class_name != top_class_name:
                    generated_classes.add(class_name)
                    
                    base_class_key = 'hierarchy'
                    hierarchy_array_class = self.config.types.base_classes['hierarchy_array'].split('.')[-1]
                    if hierarchy_array_class in node.py_type:
                        base_class_key = 'hierarchy_array'
                    
                    base_class = self.config.types.base_classes[base_class_key]
                    lines.append(f"class {class_name}({base_class}):")
                    
                    is_array_object = hierarchy_array_class in node.py_type
                    has_non_index_children = False
                    
                    for child_name, child_tree in sorted(children.items()):
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
                                child_class_name = sanitize_name(child_name)
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
            
            self._generate_meaningful_classes(children, lines, generated_classes, top_class_name)

def generate_stub(hierarchy: HierarchyDict, out_dir: Path) -> Path:
    """Generate comprehensive stub file from HierarchyDict with proper cocotb types."""
    generator = StubGenerator()
    return generator.generate_stub(hierarchy, out_dir)
