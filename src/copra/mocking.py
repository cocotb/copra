# Copyright cocotb contributors
# Licensed under the Revised BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-3-Clause

"""Mock objects for testing cocotb testbenches without a simulator."""

import ast
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Union


class MockSignal:
    """Mock implementation of a cocotb signal handle for testing purposes.

    This class provides enhanced signal behavior including value history tracking,
    change callbacks, and signal width validation as specified in the design document.
    """

    def __init__(self, name: str, handle_type: str = "LogicObject", width: int = 32):
        """Initialize a mock signal.

        Args:
        ----
            name: Signal name.
            handle_type: Type of handle this signal represents.
            width: Signal width in bits.

        """
        self._name = name
        self._handle_type = handle_type
        self._signal_type = handle_type  # Alias for compatibility with tests
        self._width = width
        self._value = 0
        self._callbacks: List[Callable[[int, int], None]] = []
        self._value_history = SignalValueHistory()
        self._is_driven = False
        self._drive_strength = 1.0
        self._last_change_time = time.time()

    @property
    def value(self) -> int:
        """Get the current signal value."""
        return self._value

    @value.setter
    def value(self, new_value: int) -> None:
        """Set the signal value with validation and history tracking.

        Args:
        ----
            new_value: New value to set.

        """
        # Mask value to signal width instead of raising error
        max_value = (1 << self._width) - 1
        if new_value < 0:
            new_value = 0
        elif new_value > max_value:
            new_value = new_value & max_value  # Mask to width

        old_value = self._value
        if old_value != new_value:
            self._value = new_value
            current_time = time.time()

            # Record value change in history
            self._value_history.record_change(old_value, new_value, current_time)
            self._last_change_time = current_time
            self._is_driven = True  # Mark as driven when value is set

            # Notify callbacks
            for callback in self._callbacks:
                try:
                    callback(old_value, new_value)
                except Exception as e:
                    print(f"Warning: Callback error for signal {self._name}: {e}")

    @property
    def width(self) -> int:
        """Get signal width in bits."""
        return self._width

    @property
    def is_driven(self) -> bool:
        """Check if signal is currently being driven."""
        return self._is_driven

    @is_driven.setter
    def is_driven(self, driven: bool) -> None:
        """Set signal drive state."""
        self._is_driven = driven

    @property
    def drive_strength(self) -> float:
        """Get signal drive strength (0.0 to 1.0)."""
        return self._drive_strength

    @drive_strength.setter
    def drive_strength(self, strength: float) -> None:
        """Set signal drive strength.

        Args:
        ----
            strength: Drive strength from 0.0 (weak) to 1.0 (strong).

        Raises:
        ------
            ValueError: If strength is not in valid range.

        """
        if not 0.0 <= strength <= 1.0:
            raise ValueError("Drive strength must be between 0.0 and 1.0")
        self._drive_strength = strength

    def add_callback(self, callback: Callable[[int, int], None]) -> None:
        """Add a callback function for value changes.

        Args:
        ----
            callback: Function to call when value changes.
                     Takes (old_value, new_value) as parameters.

        """
        if callback not in self._callbacks:
            self._callbacks.append(callback)

    def remove_callback(self, callback: Callable[[int, int], None]) -> None:
        """Remove a callback function.

        Args:
        ----
            callback: Callback function to remove.

        """
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    def clear_callbacks(self) -> None:
        """Remove all callback functions."""
        self._callbacks.clear()

    def get_value_history(self) -> List[Dict[str, Any]]:
        """Get signal value change history.

        Returns
        -------
            List of value change records.

        """
        return self._value_history.get_history()

    def get_recent_changes(self, count: int = 10) -> List[Dict[str, Any]]:
        """Get recent value changes.

        Args:
        ----
            count: Number of recent changes to return.

        Returns:
        -------
            List of recent change records.

        """
        return self._value_history.get_recent_changes(count)

    def clear_history(self) -> None:
        """Clear value change history."""
        self._value_history.clear_history()

    def get_change_count(self) -> int:
        """Get total number of value changes."""
        return len(self._value_history.history)

    def get_last_change_time(self) -> float:
        """Get timestamp of last value change."""
        return self._last_change_time

    def toggle(self) -> None:
        """Toggle signal value (useful for clock signals)."""
        if self._width == 1:
            self.value = 1 - self.value
        else:
            # For multi-bit signals, toggle all bits
            max_value = (1 << self._width) - 1
            self.value = max_value - self.value

    def pulse(self, duration: float = 0.001) -> None:
        """Generate a pulse on the signal.

        Args:
        ----
            duration: Pulse duration in seconds (for timing reference).

        """
        original_value = self.value
        self.toggle()
        # Note: In real implementation, this would use cocotb timing
        # Here we just record the pulse in history
        self._value_history.record_change(
            self.value, original_value,
            time.time() + duration
        )
        self.value = original_value

    def __str__(self) -> str:
        """Return string representation of the signal."""
        return f"MockSignal({self._name}={self._value})"

    def __repr__(self) -> str:
        """Detailed string representation."""
        return (f"MockSignal(name='{self._name}', handle_type='{self._handle_type}', "
                f"value={self._value}, width={self._width}, changes={self.get_change_count()})")


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

    def add_signal(self, name: str, signal_type: str = "LogicObject",
                   width: int = 32) -> MockSignal:
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
        """Return string representation of the module."""
        return f"MockModule({self._name})"

    def __repr__(self) -> str:
        """Detailed string representation."""
        return (
            f"MockModule(name='{self._name}', type='{self._module_type}', "
            f"children={len(self._children)})"
        )


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
        if self.stub_file is None:
            return

        try:
            with open(self.stub_file, encoding='utf-8') as f:
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

    def add_signal(self, name: str, signal_type: str = "LogicObject",
                   width: int = 32) -> MockSignal:
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
        """Return string representation of the mock DUT."""
        return f"MockDUT({self._name})"

    def __repr__(self) -> str:
        """Detailed string representation."""
        return (
            f"MockDUT(name='{self._name}', signals={len(self._signals)}, "
            f"submodules={len(self._sub_modules)})"
        )


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

    # First, identify all module paths (paths that have children)
    module_paths = set()
    for path in hierarchy.keys():
        parts = path.split('.')
        # Add all parent paths as modules (except the root 'dut')
        for i in range(1, len(parts)):
            parent_path = '.'.join(parts[:i])
            module_paths.add(parent_path)

    # Also check if any path is a prefix of another (indicating it's a module)
    all_paths = list(hierarchy.keys())
    for path in all_paths:
        for other_path in all_paths:
            if other_path != path and other_path.startswith(path + '.'):
                module_paths.add(path)

    # Process hierarchy to create mock structure
    for path, obj_type in hierarchy.items():
        parts = path.split('.')

        if len(parts) == 1:
            # Top-level item (skip 'dut' itself as it's the mock_dut)
            if path == name or path == 'dut':
                continue
            elif path in module_paths:
                # This is a module
                mock_dut.add_submodule(path, obj_type.__name__)
            else:
                # This is a signal
                mock_dut.add_signal(path, obj_type.__name__)
        else:
            # Nested item - create sub-modules as needed
            current: Union[MockDUT, MockModule] = mock_dut

            # Skip the first part if it's 'dut' (the root)
            path_parts = parts[1:] if parts[0] == 'dut' else parts

            for i, part in enumerate(path_parts[:-1]):
                # Handle both MockDUT and MockModule objects
                if isinstance(current, MockDUT):
                    if part not in current._sub_modules:
                        current.add_submodule(part)
                    current = current._sub_modules[part]
                elif isinstance(current, MockModule):
                    if part not in current._children:
                        current.add_submodule(part)
                    current = current._children[part]

            # Add the final item
            final_name = path_parts[-1]
            if path in module_paths:
                # This is a module
                if isinstance(current, MockDUT):
                    current.add_submodule(final_name, obj_type.__name__)
                elif isinstance(current, MockModule):
                    current.add_submodule(final_name, obj_type.__name__)
            else:
                # This is a signal
                if isinstance(current, MockDUT):
                    current.add_signal(final_name, obj_type.__name__)
                elif isinstance(current, MockModule):
                    current.add_signal(final_name, obj_type.__name__)

    return mock_dut


def create_mock_dut(hierarchy: Dict[str, type], name: str = "mock_dut") -> MockDUT:
    """Create a mock DUT from a hierarchy dictionary.

    This is an alias for create_mock_dut_from_hierarchy for backward compatibility.

    Args:
        hierarchy: Dictionary mapping paths to types.
        name: Name for the mock DUT.

    Returns:
        Mock DUT instance.
    """
    return create_mock_dut_from_hierarchy(hierarchy, name)


class SignalValueHistory:
    """Track signal value changes over time for analysis and debugging."""

    def __init__(self, max_history: int = 1000):
        """Initialize value history tracker.

        Args:
        ----
            max_history: Maximum number of value changes to track.

        """
        self.max_history = max_history
        self.history: List[Dict[str, Any]] = []

    def record_change(self, old_value: int, new_value: int, timestamp: float = None) -> None:
        """Record a value change.

        Args:
        ----
            old_value: Previous signal value.
            new_value: New signal value.
            timestamp: Time of change (defaults to current time).

        """
        if timestamp is None:
            timestamp = time.time()

        change_record = {
            'timestamp': timestamp,
            'old_value': old_value,
            'new_value': new_value,
            'change_count': len(self.history) + 1
        }

        self.history.append(change_record)

        # Limit history size
        if len(self.history) > self.max_history:
            self.history.pop(0)

    def get_history(self) -> List[Dict[str, Any]]:
        """Get complete value change history."""
        return self.history.copy()

    def get_recent_changes(self, count: int = 10) -> List[Dict[str, Any]]:
        """Get most recent value changes.

        Args:
        ----
            count: Number of recent changes to return.

        Returns:
        -------
            List of recent change records.

        """
        return self.history[-count:] if self.history else []

    def get_change_count(self) -> int:
        """Get total number of value changes recorded."""
        return len(self.history)

    def get_last_change(self) -> Dict[str, Any]:
        """Get the most recent value change.

        Returns
        -------
            Most recent change record, or None if no changes recorded.

        """
        return self.history[-1] if self.history else None

    def clear(self) -> None:
        """Clear all recorded history."""
        self.history.clear()

    def clear_history(self) -> None:
        """Clear all recorded history (alias for clear)."""
        self.clear()


class BusFunctionalModel:
    """Base class for creating bus functional models with mock signals."""

    def __init__(self, name: str, clock_signal: str = "clk"):
        """Initialize bus functional model.

        Args:
        ----
            name: Name of the bus functional model.
            clock_signal: Name of the clock signal to use for timing.

        """
        self.name = name
        self.clock_signal = clock_signal
        self.signals: Dict[str, MockSignal] = {}
        self.transactions: List[Dict[str, Any]] = []
        self.is_active = False

    def add_signal(self, name: str, signal_or_width: Union[MockSignal, int] = 32,
                   initial_value: int = 0) -> MockSignal:
        """Add a signal to the bus functional model.

        Args:
        ----
            name: Signal name.
            signal_or_width: Either a MockSignal object or signal width in bits.
            initial_value: Initial signal value (only used if signal_or_width is width).

        Returns:
        -------
            Created or registered mock signal.

        """
        if isinstance(signal_or_width, MockSignal):
            # Register existing signal
            signal = signal_or_width
            self.signals[name] = signal
        else:
            # Create new signal
            width = signal_or_width
            signal = MockSignal(name, "LogicArrayObject" if width > 1 else "LogicObject", width)
            signal.value = initial_value
            self.signals[name] = signal
        return signal

    def start_transaction(self, transaction_type: str, **kwargs) -> Dict[str, Any]:
        """Start a new bus transaction.

        Args:
        ----
            transaction_type: Type of transaction (e.g., 'read', 'write').
            **kwargs: Transaction-specific parameters.

        Returns:
        -------
            Transaction record.

        """
        transaction = {
            'id': len(self.transactions),
            'type': transaction_type,
            'start_time': time.time(),
            'status': 'active',
            'parameters': kwargs
        }
        self.transactions.append(transaction)
        return transaction

    def complete_transaction(self, transaction_id: int, result: Any = None) -> None:
        """Complete a bus transaction.

        Args:
        ----
            transaction_id: ID of transaction to complete.
            result: Transaction result data.

        """
        if transaction_id < len(self.transactions):
            transaction = self.transactions[transaction_id]
            transaction['status'] = 'completed'
            transaction['end_time'] = time.time()
            transaction['duration'] = transaction['end_time'] - transaction['start_time']
            transaction['result'] = result

    def get_transaction_history(self) -> List[Dict[str, Any]]:
        """Get all transaction history."""
        return self.transactions.copy()

    def reset(self) -> None:
        """Reset the bus functional model to initial state."""
        for signal in self.signals.values():
            signal.value = 0
        self.transactions.clear()
        self.is_active = False

    def start(self) -> None:
        """Start the bus functional model."""
        self.is_active = True

    def stop(self) -> None:
        """Stop the bus functional model."""
        self.is_active = False
