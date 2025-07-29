from __future__ import annotations

from typing import Dict, Optional, Tuple, Any
from cocotb.handle import (
    SimHandleBase, ArrayObject, HierarchyArrayObject,
    LogicObject, LogicArrayObject, IntegerObject, RealObject, 
    EnumObject, StringObject, HierarchyObject
)
from cocotb import simulator
from .config import get_config

def sanitize_name(name: str) -> str:
    """Convert HDL name to Python class name - shared with generation module."""
    return ''.join(word.capitalize() for word in name.split('[')[0].split('_'))

class TypeIntrospector:
    """Clean type introspection using only cocotb's type hierarchy."""
    
    def __init__(self):
        self.config = get_config()
        self._type_mappings = self._build_type_mappings()
        self._value_mappings = self._build_value_mappings()
        self._simulator_type_handlers = self._build_simulator_type_handlers()
        self._base_class_mappings = self._build_base_class_mappings()
    
    def _build_type_mappings(self) -> Dict[int, type]:
        """Build simulator type to cocotb handle class mappings."""
        try:
            from cocotb.handle import _type2cls  # type: ignore
            return dict(_type2cls)
        except ImportError:
            return {
                simulator.MODULE: HierarchyObject,
                simulator.STRUCTURE: HierarchyObject,
                simulator.PACKED_STRUCTURE: LogicArrayObject,
                simulator.LOGIC: LogicObject,
                simulator.LOGIC_ARRAY: LogicArrayObject,
                simulator.NETARRAY: ArrayObject,
                simulator.REAL: RealObject,
                simulator.INTEGER: IntegerObject,
                simulator.ENUM: EnumObject,
                simulator.STRING: StringObject,
                simulator.GENARRAY: HierarchyArrayObject,
                simulator.PACKAGE: HierarchyObject,
            }
    
    def _build_value_mappings(self) -> Dict[str, str]:
        """Build value type to handle type mappings."""
        types = self.config.types
        return {
            types.value_types['logic']: types.base_classes['logic'],
            types.value_types['logic_array']: types.base_classes['logic_array'], 
            types.value_types['integer']: types.base_classes['integer'],
            types.value_types['real']: types.base_classes['real'],
            types.value_types['string']: types.base_classes['string'],
            types.value_types['enum']: types.base_classes['enum'],
        }
    
    def _build_simulator_type_handlers(self) -> Dict[int, str]:
        """Build mapping from simulator types to their handler methods."""
        handlers = {}
        type_mappings = [
            ('NETARRAY', 'NETARRAY'),
            ('LOGIC_ARRAY', 'LOGIC_ARRAY'), 
            ('LOGIC', 'LOGIC'),
            ('INTEGER', 'INTEGER'),
            ('REAL', 'REAL'),
            ('STRING', 'STRING'),
            ('ENUM', 'ENUM'),
            ('GENARRAY', 'GENARRAY'),
        ]
        
        for attr_name, handler_name in type_mappings:
            sim_type = getattr(simulator, attr_name, None)
            if sim_type is not None:
                handlers[sim_type] = handler_name
        
        return handlers
    
    def _build_base_class_mappings(self) -> Dict[type, str]:
        """Build mapping from base classes to their string representations."""
        return {
            HierarchyObject: "cocotb.handle.HierarchyObject",
            ArrayObject: f"cocotb.handle.ArrayObject[{self.config.types.fallback_types['value']}, {self.config.types.fallback_types['handle']}]",
            LogicArrayObject: "cocotb.handle.LogicArrayObject",
            LogicObject: "cocotb.handle.LogicObject",
            IntegerObject: "cocotb.handle.IntegerObject",
            RealObject: "cocotb.handle.RealObject",
            EnumObject: "cocotb.handle.EnumObject",
            StringObject: "cocotb.handle.StringObject",
            HierarchyArrayObject: f"cocotb.handle.HierarchyArrayObject[cocotb.handle.SimHandleBase]",
        }
    
    def _get_object_info(self, obj: SimHandleBase) -> Tuple[Optional[Any], int]:
        """Extract basic object information needed for type detection."""
        handle = getattr(obj, "_handle", None)
        if not handle:
            return None, -1
            
        sim_type = handle.get_type()
        return handle, sim_type
    
    def _get_array_child_info(self, obj: SimHandleBase) -> Tuple[Optional[Any], Optional[int]]:
        """Get information about array child elements."""
        try:
            try:
                range_obj = obj.range  # type: ignore
                first_idx = range_obj.left  # type: ignore
            except (RuntimeError, AttributeError):
                return None, None
                
            if not hasattr(obj, "__getitem__"):
                return None, None
                
            child_obj = obj[first_idx]  # type: ignore
            child_handle = getattr(child_obj, "_handle", None)  # type: ignore
            if child_handle:
                child_sim_type = child_handle.get_type()
                return child_obj, child_sim_type    # type: ignore
                
        except (IndexError, AttributeError, TypeError):
            pass
        return None, None
    
    def _get_child_type_by_simulator_type(self, child_sim_type: int) -> Optional[str]:
        """Get child type based on simulator type using intelligent lookup."""
        type_handler = self._simulator_type_handlers.get(child_sim_type)
        if type_handler == 'NETARRAY':
            return None  # Indicates recursive processing needed
        elif type_handler == 'LOGIC_ARRAY':
            return self.config.types.value_types['logic_array']
        elif type_handler == 'LOGIC':
            return self.config.types.value_types['logic']
        elif type_handler == 'INTEGER':
            return self.config.types.value_types['integer']
        elif type_handler == 'REAL':
            return self.config.types.value_types['real']
        elif type_handler == 'STRING':
            return self.config.types.value_types['string']
        elif type_handler == 'ENUM':
            return self.config.types.value_types['enum']
        return None
    
    def get_nested_array_child_type(self, obj: SimHandleBase) -> Optional[str]:
        """Get the child type for nested array structures."""
        child_obj, child_sim_type = self._get_array_child_info(obj)
        if child_obj is None or child_sim_type is None:
            return None
            
        child_type = self._get_child_type_by_simulator_type(child_sim_type)
        if child_type is None and self._simulator_type_handlers.get(child_sim_type) == 'NETARRAY':
            return self.get_nested_array_child_type(child_obj)  # type: ignore
        
        return child_type
    
    def get_array_depth(self, obj: SimHandleBase) -> int:
        """Get the depth of nested arrays."""
        child_obj, child_sim_type = self._get_array_child_info(obj)
        if child_obj is None or child_sim_type is None:
            return 0
            
        if self._simulator_type_handlers.get(child_sim_type) == 'NETARRAY':
            return 1 + self.get_array_depth(child_obj)  # type: ignore
        else:
            return 1
    
    def get_array_element_value_type(self, obj: SimHandleBase) -> str:
        """Get the value type for array elements (ElemValueT)."""
        base_type = self.get_nested_array_child_type(obj)
        array_depth = self.get_array_depth(obj)
        
        if base_type and array_depth > 1:
            result = base_type
            for _ in range(array_depth - 1):
                result = f"cocotb.types.Array[{result}]"
            return result
        elif base_type:
            return base_type
        return self.config.types.fallback_types['value']
    
    def get_array_element_handle_type(self, obj: SimHandleBase) -> str:
        """Get the handle type for array elements (ChildObjectT)."""
        base_type = self.get_nested_array_child_type(obj)
        array_depth = self.get_array_depth(obj)
        
        if base_type and array_depth > 1:
            handle_base_type = self._value_mappings.get(base_type, self.config.types.fallback_types['handle'])
            
            result = handle_base_type
            inner_value_type = base_type
            
            for _ in range(array_depth - 1):
                result = f"cocotb.handle.ArrayObject[{inner_value_type}, {result}]"
                inner_value_type = f"cocotb.types.Array[{inner_value_type}]"
            
            return result
        elif base_type:
            return self._value_mappings.get(base_type, self.config.types.fallback_types['handle'])
        return self.config.types.fallback_types['handle']
    
    def _process_netarray_type(self, obj: SimHandleBase) -> str:
        """Process NETARRAY type objects."""
        elem_value_type = self.get_array_element_value_type(obj)
        child_object_type = self.get_array_element_handle_type(obj)
        
        if elem_value_type and child_object_type:
            return f"cocotb.handle.ArrayObject[{elem_value_type}, {child_object_type}]"
        elif elem_value_type:
            return f"cocotb.handle.ArrayObject[{elem_value_type}, {self.config.types.fallback_types['handle']}]"
        else:
            return f"cocotb.handle.ArrayObject[{self.config.types.fallback_types['value']}, {self.config.types.fallback_types['handle']}]"
    
    def _process_logic_array_type(self, obj: SimHandleBase) -> str:
        """Process LOGIC_ARRAY type objects."""
        # LogicArrayObjects are LogicArrayObjects regardless of their length
        return "cocotb.handle.LogicArrayObject"
    
    def _process_genarray_type(self, obj: SimHandleBase) -> str:
        """Process GENARRAY type objects."""
        try:
            try:
                range_obj = obj.range  # type: ignore
                first_idx = range_obj.left  # type: ignore
            except (RuntimeError, AttributeError):
                first_idx = 0
                
            if not hasattr(obj, "__getitem__"):
                return f"cocotb.handle.HierarchyArrayObject[{self.config.types.fallback_types['value']}]"
                
            child_obj = obj[first_idx]  # type: ignore
            
            parent_name = getattr(obj, "_name", "")
            
            for prefix in self.config.discovery.generate_prefixes:
                if parent_name and parent_name.startswith(prefix):
                    class_name = sanitize_name(parent_name)
                    return f"cocotb.handle.HierarchyArrayObject[{class_name}]"
            
            parent_path = getattr(obj, "_path", "")
            if parent_path:
                path_parts = parent_path.split('.')
                for part in reversed(path_parts):
                    for prefix in self.config.discovery.generate_prefixes:
                        if part.startswith(prefix):
                            class_name = sanitize_name(part)
                            return f"cocotb.handle.HierarchyArrayObject[{class_name}]"
            
            return f"cocotb.handle.HierarchyArrayObject[cocotb.handle.SimHandleBase]"
            
        except (IndexError, AttributeError, TypeError):
            return f"cocotb.handle.HierarchyArrayObject[cocotb.handle.SimHandleBase]"
    
    def _map_base_class_to_string(self, base_class: type) -> str:
        """Map base class type to its string representation using intelligent lookup."""
        return self._base_class_mappings.get(base_class, self.config.types.fallback_types['base'])
    
    def _process_simulator_type(self, sim_type: int, obj: SimHandleBase) -> str:
        """Process different simulator types using intelligent dispatch."""
        type_handler = self._simulator_type_handlers.get(sim_type)
        
        if type_handler == 'NETARRAY':
            return self._process_netarray_type(obj)
        elif type_handler == 'LOGIC_ARRAY':
            return self._process_logic_array_type(obj)
        elif type_handler == 'LOGIC':
            return "cocotb.handle.LogicObject"
        elif type_handler == 'INTEGER':
            return "cocotb.handle.IntegerObject"
        elif type_handler == 'REAL':
            return "cocotb.handle.RealObject"
        elif type_handler == 'ENUM':
            return "cocotb.handle.EnumObject"
        elif type_handler == 'STRING':
            return "cocotb.handle.StringObject"
        elif type_handler == 'GENARRAY':
            return self._process_genarray_type(obj)
        
        base_class = self._type_mappings.get(sim_type)
        if base_class:
            return self._map_base_class_to_string(base_class)
        
        return self.config.types.fallback_types['base']
    
    def extract_full_type_info(self, obj: SimHandleBase) -> str:
        """Extract comprehensive type information with proper generic parameters."""
        handle, sim_type = self._get_object_info(obj)
        if handle is None:
            return self.config.types.fallback_types['base']
        
        if sim_type not in self._type_mappings:
            return f"{self.config.types.fallback_types['base']}"
        
        return self._process_simulator_type(sim_type, obj)
    
    def extract_hierarchy_element_type(self, obj: SimHandleBase) -> Optional[str]:
        """Extract the element type for HierarchyArrayObject generic parameter."""
        try:
            try:
                range_obj = obj.range  # type: ignore
                first_idx = range_obj.left  # type: ignore
            except (RuntimeError, AttributeError):
                return None
                
            if not hasattr(obj, "__getitem__"):
                return None
                
            child_obj = obj[first_idx]  # type: ignore
            if hasattr(child_obj, "_name"):  # type: ignore
                child_name = getattr(child_obj, "_name")  # type: ignore
                sanitized_name = sanitize_name(child_name)
                return sanitized_name
        except (IndexError, AttributeError, TypeError):
            pass
        return None

def extract_full_type_info(obj: SimHandleBase) -> str:
    """Extract comprehensive type information with proper generic parameters."""
    introspector = TypeIntrospector()
    return introspector.extract_full_type_info(obj)

def extract_hierarchy_element_type(obj: SimHandleBase) -> Optional[str]:
    """Extract the element type for HierarchyArrayObject generic parameter."""
    introspector = TypeIntrospector()
    return introspector.extract_hierarchy_element_type(obj)
