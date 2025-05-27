# Copyright cocotb contributors
# Licensed under the Revised BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-3-Clause

"""Mock objects for copra testing and development.

This module provides mock implementations of cocotb handles that can be used
for unit testing testbench components without requiring a full simulation environment.
"""

import ast
from pathlib import Path
from typing import Any, Dict, Union


class MockSignal:
    """Mock signal that behaves like a cocotb signal handle.
    
    This class provides a lightweight mock implementation of cocotb signal handles
    that can be used for testing and development without requiring a simulator.
    """
    
    def __init__(self, name: str, signal_type: str = "LogicObject", width: int = 1):
        """Initialize mock signal.
        
        Args:
        ----
            name: Name of the signal.
            signal_type: Type of the signal (LogicObject, LogicArrayObject, etc.).
            width: Bit width of the signal (for array signals).
        """
        self._name = name
        self._signal_type = signal_type
        self._width = width
        self._value = 0
        self._callbacks = []
        
    @property
    def value(self) -> int:
        """Get signal value."""
        return self._value
    
    @value.setter
    def value(self, val: int) -> None:
        """Set signal value and trigger callbacks."""
        old_value = self._value
        self._value = val
        
        # Trigger value change callbacks
        for callback in self._callbacks:
            callback(old_value, val)
    
    def add_callback(self, callback) -> None:
        """Add a value change callback."""
        self._callbacks.append(callback)
        
    def remove_callback(self, callback) -> None:
        """Remove a value change callback."""
        if callback in self._callbacks:
            self._callbacks.remove(callback)
    
    @property
    def width(self) -> int:
        """Get signal width in bits."""
        return self._width
    
    def __str__(self) -> str:
        """String representation of the signal."""
        return f"MockSignal({self._name}={self._value})"
    
    def __repr__(self) -> str:
        """Detailed string representation."""
        return f"MockSignal(name='{self._name}', type='{self._signal_type}', width={self._width}, value={self._value})"


class MockModule:
    """Mock module that behaves like a hierarchical cocotb handle.
    
    This class provides a mock implementation of hierarchical cocotb handles
    for testing purposes.
    """
    
    def __init__(self, name: str, module_type: str = "HierarchyObject"):
        """Initialize mock module.
        
        Args:
        ----
            name: Name of the module.
            module_type: Type of the module.
        """
        self._name = name
        self._module_type = module_type
        self._children: Dict[str, Any] = {}
        
    def add_signal(self, name: str, signal_type: str = "LogicObject", width: int = 1) -> MockSignal:
        """Add a signal to this module.
        
        Args:
        ----
            name: Signal name.
            signal_type: Signal type.
            width: Signal width.
            
        Returns:
        -------
            The created mock signal.
        """
        signal = MockSignal(name, signal_type, width)
        self._children[name] = signal
        return signal
        
    def add_submodule(self, name: str, module_type: str = "HierarchyObject") -> "MockModule":
        """Add a sub-module to this module.
        
        Args:
        ----
            name: Sub-module name.
            module_type: Sub-module type.
            
        Returns:
        -------
            The created mock sub-module.
        """
        submodule = MockModule(name, module_type)
        self._children[name] = submodule
        return submodule
    
    def __getattr__(self, name: str) -> Any:
        """Get child attribute."""
        if name.startswith('_'):
            # Avoid infinite recursion for private attributes
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")
            
        if name not in self._children:
            # Create a mock signal for unknown children
            self._children[name] = MockSignal(name, 'LogicObject')
        return self._children[name]
    
    def __setattr__(self, name: str, value: Any) -> None:
        """Set attribute value."""
        if name.startswith('_'):
            super().__setattr__(name, value)
        else:
            self._children[name] = value
    
    def get_children(self) -> Dict[str, Any]:
        """Get all child objects."""
        return self._children.copy()
    
    def __str__(self) -> str:
        """String representation of the module."""
        return f"MockModule({self._name})"
    
    def __repr__(self) -> str:
        """Detailed string representation."""
        return f"MockModule(name='{self._name}', type='{self._module_type}', children={len(self._children)})"


class MockDUT:
    """Mock DUT class that implements the same interface as the generated stub.
    
    This class can be used for unit testing testbench components without
    requiring a full simulation environment. It can be initialized from
    a stub file or created programmatically.
    """
    
    def __init__(self, stub_file: Union[str, Path, None] = None, name: str = "mock_dut"):
        """Initialize mock DUT from a stub file or create empty.
        
        Args:
        ----
            stub_file: Path to the generated stub file (optional).
            name: Name of the DUT.
        """
        self._name = name
        self.stub_file = Path(stub_file) if stub_file else None
        self._signals: Dict[str, MockSignal] = {}
        self._sub_modules: Dict[str, MockModule] = {}
        
        if self.stub_file and self.stub_file.exists():
            self._parse_stub_file()
    
    def _parse_stub_file(self) -> None:
        """Parse the stub file to extract interface information."""
        try:
            with open(self.stub_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse the AST to extract class definitions
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    self._parse_class_definition(node)
                    
        except Exception as e:
            print(f"[copra] Warning: Failed to parse stub file {self.stub_file}: {e}")
    
    def _parse_class_definition(self, class_node: ast.ClassDef) -> None:
        """Parse a class definition to extract signals and sub-modules."""
        for node in class_node.body:
            if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                attr_name = node.target.id
                if isinstance(node.annotation, ast.Name):
                    type_name = node.annotation.id
                    if type_name in ('LogicObject', 'LogicArrayObject', 'ValueObjectBase'):
                        self._signals[attr_name] = MockSignal(attr_name, type_name)
                    else:
                        self._sub_modules[attr_name] = MockModule(attr_name, type_name)
    
    def add_signal(self, name: str, signal_type: str = "LogicObject", width: int = 1) -> MockSignal:
        """Add a signal to the mock DUT.
        
        Args:
        ----
            name: Signal name.
            signal_type: Signal type.
            width: Signal width.
            
        Returns:
        -------
            The created mock signal.
        """
        signal = MockSignal(name, signal_type, width)
        self._signals[name] = signal
        return signal
        
    def add_submodule(self, name: str, module_type: str = "HierarchyObject") -> MockModule:
        """Add a sub-module to the mock DUT.
        
        Args:
        ----
            name: Sub-module name.
            module_type: Sub-module type.
            
        Returns:
        -------
            The created mock sub-module.
        """
        submodule = MockModule(name, module_type)
        self._sub_modules[name] = submodule
        return submodule
    
    def __getattr__(self, name: str) -> Any:
        """Get attribute by name, returning mock objects."""
        if name.startswith('_'):
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")
            
        if name in self._signals:
            return self._signals[name]
        elif name in self._sub_modules:
            return self._sub_modules[name]
        else:
            # Return a generic mock signal for unknown attributes
            signal = MockSignal(name, 'LogicObject')
            self._signals[name] = signal
            return signal
    
    def get_signals(self) -> Dict[str, MockSignal]:
        """Get all signals in the mock DUT."""
        return self._signals.copy()
    
    def get_submodules(self) -> Dict[str, MockModule]:
        """Get all sub-modules in the mock DUT."""
        return self._sub_modules.copy()
    
    def reset_all_signals(self, value: int = 0) -> None:
        """Reset all signals to a specified value."""
        for signal in self._signals.values():
            signal.value = value
            
        # Recursively reset sub-module signals
        for submodule in self._sub_modules.values():
            for child_signal in submodule.get_children().values():
                if isinstance(child_signal, MockSignal):
                    child_signal.value = value
    
    def __str__(self) -> str:
        """String representation of the mock DUT."""
        return f"MockDUT({self._name})"
    
    def __repr__(self) -> str:
        """Detailed string representation."""
        return f"MockDUT(name='{self._name}', signals={len(self._signals)}, submodules={len(self._sub_modules)})"


def create_mock_dut_from_hierarchy(hierarchy: Dict[str, type], name: str = "mock_dut") -> MockDUT:
    """Create a mock DUT from a hierarchy dictionary.
    
    Args:
    ----
        hierarchy: Hierarchy dictionary from discover_hierarchy().
        name: Name for the mock DUT.
        
    Returns:
    -------
        Configured mock DUT with the specified hierarchy.
    """
    mock_dut = MockDUT(name=name)
    
    # Process hierarchy to create mock structure
    for path, obj_type in hierarchy.items():
        parts = path.split('.')
        
        if len(parts) == 1:
            # Top-level signal
            signal_name = parts[0]
            mock_dut.add_signal(signal_name, obj_type.__name__)
        else:
            # Nested signal - create sub-modules as needed
            current = mock_dut
            for i, part in enumerate(parts[:-1]):
                # Handle both MockDUT and MockModule objects
                if isinstance(current, MockDUT):
                    if part not in current._sub_modules:
                        current.add_submodule(part)
                    current = current._sub_modules[part]
                elif isinstance(current, MockModule):
                    if part not in current._children:
                        current.add_submodule(part)
                    current = current._children[part]
            
            # Add the final signal
            signal_name = parts[-1]
            if isinstance(current, MockDUT):
                current.add_signal(signal_name, obj_type.__name__)
            elif isinstance(current, MockModule):
                current.add_signal(signal_name, obj_type.__name__)
    
    return mock_dut 