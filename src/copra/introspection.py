from typing import Any, Type, get_origin, get_args
from cocotb.handle import SimHandleBase

def extract_full_type_info(obj: SimHandleBase) -> str:
    """Extract full typing information from an object using introspection."""
    obj_type: Type[Any] = type(obj)
    type_name = obj_type.__name__
    module = getattr(obj_type, '__module__', '')

    def find_generic_base_info(cls: Type[Any]) -> str | None:
        """Find the most specific generic base class and extract its type parameters."""
        orig_bases = getattr(cls, '__orig_bases__', ())
        for base in orig_bases:
            origin = get_origin(base)
            args = get_args(base)
            if origin is not None and args:
                origin_name = getattr(origin, '__name__', str(origin))
                args_str = ', '.join(_format_type_arg(arg) for arg in args)
                return f"{origin_name}[{args_str}]" if 'cocotb' in module else f"cocotb.handle.{origin_name}[{args_str}]"
        
        for mro_class in cls.__mro__[1:]:
            mro_orig_bases = getattr(mro_class, '__orig_bases__', ())
            for base in mro_orig_bases:
                origin = get_origin(base)
                args = get_args(base)
                if origin is not None and args:
                    origin_name = getattr(origin, '__name__', str(origin))
                    args_str = ', '.join(_format_type_arg(arg) for arg in args)
                    if 'cocotb' in module:
                        return f"cocotb.handle.{origin_name}[{args_str}]"
                    else:
                        return f"{origin_name}[{args_str}]"
        return None
    
    def introspect_actual_types(obj: SimHandleBase) -> str | None:
        """Introspect the actual object using capabilities rather than isinstance checks."""
        full_class_name = f"{obj_type.__module__}.{obj_type.__name__}" if obj_type.__module__ else obj_type.__name__
        
        has_range = False
        try:
            if hasattr(obj, 'range'):
                _ = obj.range   # type: ignore
                has_range = True
        except (RuntimeError, AttributeError):
            has_range = False
        
        has_get = hasattr(obj, 'get') and callable(getattr(obj, 'get', None))
        has_getitem = hasattr(obj, '__getitem__')
        has_len = hasattr(obj, '__len__')
        mro_names = [cls.__name__ for cls in obj_type.__mro__]
        if has_range and has_getitem:
            try:
                if has_len and len(obj) > 0:  # type: ignore
                    first_idx = next(iter(obj.range))  # type: ignore
                    child = obj[first_idx]  # type: ignore
                    child_type_info = _extract_full_type_info(child)  # type: ignore
                    elem_value_type = "Any"
                    if hasattr(child, 'get') and callable(getattr(child, 'get', None)):  # type: ignore
                        try:
                            value = getattr(child, 'get')()  # type: ignore
                            if value is not None and hasattr(value, '__class__'):
                                cls = value.__class__
                                cls_name = getattr(cls, '__name__', 'Any')
                                cls_module = getattr(cls, '__module__', '')
                                elem_value_type = f"{cls_module}.{cls_name}" if cls_module else cls_name
                        except Exception:
                            elem_value_type = "Any"
                    
                    return f"{full_class_name}[{elem_value_type}, {child_type_info}]"
                else:
                    return f"{full_class_name}[Any, Any]"
            except Exception:
                pass
        
        elif has_range and 'HierarchyArrayObject' in mro_names:
            return full_class_name
        
        elif has_get:
            try:
                value_get_type = "Any"
                value_set_type = "Any"
                
                try:
                    value = getattr(obj, 'get')()  # type: ignore
                    if value is not None and hasattr(value, '__class__'):
                        cls = value.__class__
                        cls_name = getattr(cls, '__name__', 'Any')
                        cls_module = getattr(cls, '__module__', '')
                        value_get_type = f"{cls_module}.{cls_name}" if cls_module else cls_name
                        value_set_type = value_get_type
                except Exception:
                    pass
                
                if 'ValueObjectBase' in mro_names and obj_type.__name__ == 'ValueObjectBase':
                    return f"{full_class_name}[{value_get_type}, {value_set_type}]"
                else:
                    return full_class_name
            except Exception:
                pass
        
        return full_class_name
    
    introspected = introspect_actual_types(obj)
    if introspected:
        return introspected
    
    generic_info = find_generic_base_info(obj_type)
    if generic_info:
        return generic_info
    
    if 'cocotb' in module:
        return f"cocotb.handle.{type_name}"
    
    return type_name

def _format_type_arg(arg: Any) -> str:
    """Format a type argument for string representation."""
    if hasattr(arg, '__name__'):
        name = getattr(arg, '__name__')
        module = getattr(arg, '__module__', '')
        if 'cocotb' in module and not name.startswith('cocotb.'):
            return f"cocotb.handle.{name}" if 'handle' in module else f"cocotb.{name}"
        return name
    elif hasattr(arg, '_name'):
        return getattr(arg, '_name')
    elif get_origin(arg) is not None:
        origin = get_origin(arg)
        args = get_args(arg)
        if args:
            origin_name = getattr(origin, '__name__', str(origin)) if origin else str(origin)
            origin_module = getattr(origin, '__module__', '') if origin else ''
            if 'cocotb' in origin_module and not origin_name.startswith('cocotb.'):
                origin_name = f"cocotb.handle.{origin_name}" if 'handle' in origin_module else f"cocotb.{origin_name}"
            args_str = ', '.join(_format_type_arg(a) for a in args)
            return f"{origin_name}[{args_str}]"
        else:
            origin_name = getattr(origin, '__name__', str(origin)) if origin else str(origin)
            origin_module = getattr(origin, '__module__', '') if origin else ''
            if 'cocotb' in origin_module and not origin_name.startswith('cocotb.'):
                origin_name = f"cocotb.handle.{origin_name}" if 'handle' in origin_module else f"cocotb.{origin_name}"
            return origin_name
    else:
        return str(arg)
