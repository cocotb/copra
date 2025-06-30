from cocotb.handle import SimHandleBase, _type2cls   # type: ignore
from cocotb import simulator

def extract_full_type_info(obj: SimHandleBase) -> str:
    """Extract type information directly from the simulator handle."""
    sim_type = obj._handle.get_type()  # type: ignore
    if sim_type == simulator.NETARRAY:
        try:
            left, _, _ = obj._handle.get_range()  # type: ignore
            first_idx = left
            child_handle = obj._handle.get_handle_by_index(first_idx)  # type: ignore
        except:
            child_handle = obj._handle.get_handle_by_index(0)  # type: ignore
            
        if child_handle:
            child_sim_type = child_handle.get_type()
            if child_sim_type in _type2cls:
                child_cls = _type2cls[child_sim_type]
                child_cls_name = child_cls.__name__
                child_type_info = f"cocotb.handle.{child_cls_name}"
                if child_cls_name == "LogicArrayObject":
                    elem_value_type = "cocotb.types.LogicArray"
                elif child_cls_name == "LogicObject":
                    elem_value_type = "cocotb.types.Logic"
                else:
                    elem_value_type = "Any"
                
                return f"cocotb.handle.ArrayObject[{elem_value_type}, {child_type_info}]"
        return "cocotb.handle.ArrayObject[Any, Any]"
            
    if sim_type in _type2cls:
        cls = _type2cls[sim_type]
        module = getattr(cls, '__module__', '')
        class_name = cls.__name__
        
        if 'cocotb' in module:
            return f"cocotb.handle.{class_name}"
        return class_name
    else:
        type_string = obj._handle.get_type_string()  # type: ignore
        return f"cocotb.handle.SimHandleBase  # Unknown type: {type_string}({sim_type})"
