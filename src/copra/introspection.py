from __future__ import annotations

from typing import Dict, Optional
from cocotb.handle import (
    SimHandleBase, ArrayObject, HierarchyArrayObject,
    LogicObject, LogicArrayObject, IntegerObject, RealObject, 
    EnumObject, StringObject, HierarchyObject
)
from cocotb import simulator
from .config import get_config

class TypeIntrospector:
    """Configurable type introspection for HDL objects."""
    
    def __init__(self):
        self.config = get_config()
        self._type_mappings = self._build_type_mappings()
        self._value_mappings = self._build_value_mappings()
    
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
    
    def get_nested_array_child_type(self, obj: SimHandleBase) -> Optional[str]:
        """Get the child type for nested array structures."""
        try:
            try:
                range_obj = obj.range  # type: ignore
                first_idx = range_obj.left  # type: ignore
            except (RuntimeError, AttributeError):
                return None
                
            if not hasattr(obj, "__getitem__"):
                return None
                
            child_obj = obj[first_idx]  # type: ignore
            child_handle = getattr(child_obj, "_handle", None)  # type: ignore
            if child_handle:
                child_sim_type = child_handle.get_type()
                
                if child_sim_type == simulator.NETARRAY:
                    return self.get_nested_array_child_type(child_obj)  # type: ignore
                elif child_sim_type == simulator.LOGIC_ARRAY:
                    return self.config.types.value_types['logic_array']
                elif child_sim_type == simulator.LOGIC:
                    return self.config.types.value_types['logic']
                elif child_sim_type == simulator.INTEGER:
                    return self.config.types.value_types['integer']
                elif child_sim_type == simulator.REAL:
                    return self.config.types.value_types['real']
                elif child_sim_type == simulator.STRING:
                    return self.config.types.value_types['string']
                elif child_sim_type == simulator.ENUM:
                    return self.config.types.value_types['enum']
                    
        except (IndexError, AttributeError, TypeError):
            pass
        return None
    
    def get_array_depth(self, obj: SimHandleBase) -> int:
        """Get the depth of nested arrays."""
        try:
            try:
                range_obj = obj.range  # type: ignore
                first_idx = range_obj.left  # type: ignore
            except (RuntimeError, AttributeError):
                return 0
                
            if not hasattr(obj, "__getitem__"):
                return 0
                
            child_obj = obj[first_idx]  # type: ignore
            child_handle = getattr(child_obj, "_handle", None)  # type: ignore
            if child_handle:
                child_sim_type = child_handle.get_type()
                
                if child_sim_type == simulator.NETARRAY:
                    return 1 + self.get_array_depth(child_obj)  # type: ignore
                else:
                    return 1
                    
        except (IndexError, AttributeError, TypeError):
            pass
        return 0
    
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
    
    def extract_full_type_info(self, obj: SimHandleBase) -> str:
        """Extract comprehensive type information with proper generic parameters."""
        handle = getattr(obj, "_handle", None)
        if not handle:
            return self.config.types.fallback_types['base']
            
        sim_type = handle.get_type()
        
        if sim_type not in self._type_mappings:
            return f"{self.config.types.fallback_types['base']}"
        
        base_class = self._type_mappings[sim_type]
        
        if sim_type == simulator.NETARRAY:
            elem_value_type = self.get_array_element_value_type(obj)
            child_object_type = self.get_array_element_handle_type(obj)
            
            if elem_value_type and child_object_type:
                return f"cocotb.handle.ArrayObject[{elem_value_type}, {child_object_type}]"
            elif elem_value_type:
                return f"cocotb.handle.ArrayObject[{elem_value_type}, {self.config.types.fallback_types['handle']}]"
            else:
                return f"cocotb.handle.ArrayObject[{self.config.types.fallback_types['value']}, {self.config.types.fallback_types['handle']}]"
        
        elif sim_type == simulator.GENARRAY:
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
                        base_name = parent_name[len(prefix):]
                        parts = base_name.split('_')
                        class_name = prefix.capitalize() + ''.join(part.capitalize() for part in parts)
                        return f"cocotb.handle.HierarchyArrayObject[{class_name}]"
                
                parent_path = getattr(obj, "_path", "")
                if parent_path:
                    path_parts = parent_path.split('.')
                    for part in reversed(path_parts):
                        for prefix in self.config.discovery.generate_prefixes:
                            if part.startswith(prefix):
                                base_name = part[len(prefix):]
                                parts = base_name.split('_')
                                class_name = prefix.capitalize() + ''.join(part.capitalize() for part in parts)
                                return f"cocotb.handle.HierarchyArrayObject[{class_name}]"
                
                if hasattr(child_obj, "_name"):  # type: ignore
                    child_name = getattr(child_obj, "_name")  # type: ignore
                    if child_name and not child_name.isdigit():
                        sanitized_name = ''.join(word.capitalize() for word in child_name.split('_'))
                        return f"cocotb.handle.HierarchyArrayObject[{sanitized_name}]"
                    
                child_class_name = type(child_obj).__name__  # type: ignore
                return f"cocotb.handle.HierarchyArrayObject[{child_class_name}]"
                
            except (IndexError, AttributeError, TypeError):
                pass
            return f"cocotb.handle.HierarchyArrayObject[{self.config.types.fallback_types['value']}]"
        
        return f"cocotb.handle.{base_class.__name__}"
    
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
                sanitized_name = ''.join(word.capitalize() for word in child_name.split('_'))
                return sanitized_name
        except (IndexError, AttributeError, TypeError):
            pass
        return None

_introspector = TypeIntrospector()

def extract_full_type_info(obj: SimHandleBase) -> str:
    """Extract comprehensive type information with proper generic parameters."""
    return _introspector.extract_full_type_info(obj)

def extract_hierarchy_element_type(obj: SimHandleBase) -> Optional[str]:
    """Extract the element type for HierarchyArrayObject generic parameter."""
    return _introspector.extract_hierarchy_element_type(obj)
