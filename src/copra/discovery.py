from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any

from cocotb.handle import (
    HierarchyArrayObject,
    HierarchyObject,
    SimHandleBase,
)
from cocotb import simulator
from .introspection import extract_full_type_info
from .config import get_config

@dataclass(slots=True)
class HDLNode:
    path: str
    py_type: str
    width: int | None
    is_scope: bool

class HierarchyDict(Dict[str, Any]):
    """A mutating dictionary that builds hierarchy iteratively during discovery."""
    
    def __init__(self) -> None:
        super().__init__()
        self._nodes: Dict[str, HDLNode] = {}
        self._tree: Dict[str, Any] = {}
        self.config = get_config()
    
    def add_node(self, obj: SimHandleBase, path: str) -> None:
        """Add a node to the hierarchy, building the tree structure as we go."""
        width: int | None = None
        try:
            if hasattr(obj, '__len__'):
                width = len(obj)  # type: ignore
        except (TypeError, AttributeError, RuntimeError, Exception):
            width = None
        
        is_scope = self._determine_scope(obj)
        
        node = HDLNode(
            path=path,
            py_type=extract_full_type_info(obj),
            width=width,
            is_scope=is_scope,
        )
        self._nodes[path] = node
        self._build_tree_node(node)
    
    def _determine_scope(self, obj: SimHandleBase) -> bool:
        """Determine if an object represents a scope based on configuration."""
        try:
            handle = getattr(obj, "_handle", None)
            if handle is None:
                return isinstance(obj, (HierarchyObject, HierarchyArrayObject))
                
            sim_type = handle.get_type()
            scope_type_constants = {
                getattr(simulator, scope_type) 
                for scope_type in self.config.discovery.scope_types
                if hasattr(simulator, scope_type)
            }
            return sim_type in scope_type_constants
        except (AttributeError, TypeError, RuntimeError):
            return isinstance(obj, (HierarchyObject, HierarchyArrayObject))
    
    def _build_tree_node(self, node: HDLNode) -> None:
        """Build tree structure for a single node as it's discovered."""
        path_parts = node.path.split(".")
        current = self._tree
        
        for i, part in enumerate(path_parts):
            if part not in current:
                current[part] = {"_node": None, "_children": {}}
            
            if i == len(path_parts) - 1:
                current[part]["_node"] = node
            
            current = current[part]["_children"]
    
    def get_nodes(self) -> list[HDLNode]:
        """Get all nodes as a list."""
        return list(self._nodes.values())
    
    def get_tree(self) -> Dict[str, Any]:
        """Get the built tree structure."""
        return self._tree

class HierarchyDiscoverer:
    """Configurable hierarchy discovery system."""
    
    def __init__(self):
        self.config = get_config()
    
    async def discover(self, dut: SimHandleBase) -> HierarchyDict:
        """Discover hierarchy iteratively while building, avoiding explore-then-rebuild pattern."""
        dut._discover_all()  # type: ignore
        hierarchy = HierarchyDict()
        await self._discover_recursive(dut, hierarchy, "")
        return hierarchy

    async def _discover_recursive(
        self, 
        obj: SimHandleBase, 
        hierarchy: HierarchyDict, 
        path_prefix: str,
        current_depth: int = 0
    ) -> None:
        """Recursively discover hierarchy."""
        if current_depth > self.config.discovery.max_depth:
            return
        
        obj_name = getattr(obj, "_name", None)
        if obj_name is None:
            return
        
        full_path = f"{path_prefix}.{obj_name}" if path_prefix else obj_name
        hierarchy.add_node(obj, full_path)
        
        if hasattr(obj, "_discover_all"):
            obj._discover_all()  # type: ignore
        
        sub_handles = getattr(obj, "_sub_handles", {})
        
        for key, child in sub_handles.items():
            if isinstance(obj, HierarchyArrayObject):
                child_path = f"{full_path}[{key}]"
            else:
                child_path = f"{full_path}.{key}"
            
            hierarchy.add_node(child, child_path)
            
            if self._should_recurse(child):
                await self._discover_recursive(
                    child, 
                    hierarchy, 
                    child_path.rsplit('.', 1)[0] if '.' in child_path else "",
                    current_depth + 1
                )
    
    def _should_recurse(self, child: SimHandleBase) -> bool:
        """Determine if we should recurse into a child object."""
        try:
            child_handle = getattr(child, "_handle", None)
            if not child_handle:
                return False
            
            child_sim_type = child_handle.get_type()
            scope_type_constants = {
                getattr(simulator, scope_type) 
                for scope_type in self.config.discovery.scope_types
                if hasattr(simulator, scope_type)
            }
            return child_sim_type in scope_type_constants
        except (AttributeError, TypeError, RuntimeError):
            return False

async def discover(dut: SimHandleBase) -> HierarchyDict:
    """Discover hierarchy iteratively while building, avoiding explore-then-rebuild pattern."""
    discoverer = HierarchyDiscoverer()
    return await discoverer.discover(dut)
