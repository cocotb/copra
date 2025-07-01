from cocotb.handle import (
    SimHandleBase, _type2cls,   # type: ignore
)
from cocotb import simulator

def _get_array_type_info(obj: SimHandleBase, default: str) -> str:
    """Get type info for array elements/objects."""
    first_idx = obj.range.left if hasattr(obj, "range") else 0  # type: ignore
    if (child_handle := getattr(obj, "_handle").get_handle_by_index(first_idx)):  # type: ignore
        if (child_sim_type := child_handle.get_type()) in _type2cls:
            return f"cocotb.handle.{_type2cls[child_sim_type].__name__}"
    return default

def extract_full_type_info(obj: SimHandleBase) -> str:
    """Extract type information."""
    handle = getattr(obj, "_handle")  # type: ignore
    sim_type = handle.get_type()
    if sim_type in _type2cls:
        if sim_type == simulator.NETARRAY:
            return f"cocotb.handle.ArrayObject[{_get_array_type_info(obj, 'Any')}, {_get_array_type_info(obj, 'cocotb.handle.ValueObjectBase[Any, Any]')}]"
        return f"cocotb.handle.{_type2cls[sim_type].__name__}"
    type_string = handle.get_type_string()
    return f"cocotb.handle.SimHandleBase  # Unknown type: {type_string}({sim_type})"
