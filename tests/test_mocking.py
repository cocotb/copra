"""Tests for the copra.mocking module."""

import tempfile
from pathlib import Path
from typing import Any, Dict

import pytest

from copra.mocking import (
    MockDUT,
    MockModule,
    MockSignal,
    create_mock_dut_from_hierarchy,
)


class TestMockSignal:
    """Test the MockSignal class."""

    def test_mock_signal_creation(self):
        """Test basic MockSignal creation."""
        signal = MockSignal("test_signal", "LogicObject", 8)
        
        assert signal._name == "test_signal"
        assert signal._signal_type == "LogicObject"
        assert signal._width == 8
        assert signal.value == 0

    def test_mock_signal_value_property(self):
        """Test MockSignal value property."""
        signal = MockSignal("test_signal")
        
        # Test initial value
        assert signal.value == 0
        
        # Test setting value
        signal.value = 42
        assert signal.value == 42

    def test_mock_signal_width_property(self):
        """Test MockSignal width property."""
        signal = MockSignal("test_signal", width=16)
        assert signal.width == 16

    def test_mock_signal_callbacks(self):
        """Test MockSignal callback functionality."""
        signal = MockSignal("test_signal")
        callback_calls = []
        
        def test_callback(old_val, new_val):
            callback_calls.append((old_val, new_val))
        
        signal.add_callback(test_callback)
        
        # Change value and check callback was called
        signal.value = 5
        assert len(callback_calls) == 1
        assert callback_calls[0] == (0, 5)
        
        # Change value again
        signal.value = 10
        assert len(callback_calls) == 2
        assert callback_calls[1] == (5, 10)

    def test_mock_signal_remove_callback(self):
        """Test removing callbacks from MockSignal."""
        signal = MockSignal("test_signal")
        callback_calls = []
        
        def test_callback(old_val, new_val):
            callback_calls.append((old_val, new_val))
        
        signal.add_callback(test_callback)
        signal.value = 5
        assert len(callback_calls) == 1
        
        # Remove callback
        signal.remove_callback(test_callback)
        signal.value = 10
        assert len(callback_calls) == 1  # No new calls

    def test_mock_signal_string_representation(self):
        """Test MockSignal string representations."""
        signal = MockSignal("test_signal", "LogicObject", 8)
        signal.value = 42
        
        assert str(signal) == "MockSignal(test_signal=42)"
        assert "MockSignal(name='test_signal'" in repr(signal)
        assert "type='LogicObject'" in repr(signal)
        assert "width=8" in repr(signal)
        assert "value=42" in repr(signal)


class TestMockModule:
    """Test the MockModule class."""

    def test_mock_module_creation(self):
        """Test basic MockModule creation."""
        module = MockModule("test_module", "HierarchyObject")
        
        assert module._name == "test_module"
        assert module._module_type == "HierarchyObject"
        assert len(module._children) == 0

    def test_mock_module_add_signal(self):
        """Test adding signals to MockModule."""
        module = MockModule("test_module")
        
        signal = module.add_signal("test_signal", "LogicObject", 16)
        
        assert isinstance(signal, MockSignal)
        assert signal._name == "test_signal"
        assert signal._signal_type == "LogicObject"
        assert signal._width == 16
        assert "test_signal" in module._children

    def test_mock_module_add_submodule(self):
        """Test adding sub-modules to MockModule."""
        module = MockModule("test_module")
        
        submodule = module.add_submodule("sub", "SubModuleType")
        
        assert isinstance(submodule, MockModule)
        assert submodule._name == "sub"
        assert submodule._module_type == "SubModuleType"
        assert "sub" in module._children

    def test_mock_module_getattr(self):
        """Test MockModule attribute access."""
        module = MockModule("test_module")
        
        # Add a signal
        module.add_signal("existing_signal", "LogicObject")
        
        # Access existing signal
        signal = module.existing_signal
        assert isinstance(signal, MockSignal)
        assert signal._name == "existing_signal"
        
        # Access non-existing signal (should create one)
        new_signal = module.new_signal
        assert isinstance(new_signal, MockSignal)
        assert new_signal._name == "new_signal"
        assert "new_signal" in module._children

    def test_mock_module_setattr(self):
        """Test MockModule attribute setting."""
        module = MockModule("test_module")
        
        # Set a signal directly
        signal = MockSignal("direct_signal")
        module.direct_signal = signal
        
        assert module.direct_signal is signal
        assert "direct_signal" in module._children

    def test_mock_module_get_children(self):
        """Test MockModule get_children method."""
        module = MockModule("test_module")
        
        module.add_signal("signal1")
        module.add_signal("signal2")
        module.add_submodule("sub1")
        
        children = module.get_children()
        assert len(children) == 3
        assert "signal1" in children
        assert "signal2" in children
        assert "sub1" in children

    def test_mock_module_string_representation(self):
        """Test MockModule string representations."""
        module = MockModule("test_module", "CustomType")
        module.add_signal("signal1")
        module.add_submodule("sub1")
        
        assert str(module) == "MockModule(test_module)"
        assert "MockModule(name='test_module'" in repr(module)
        assert "type='CustomType'" in repr(module)
        assert "children=2" in repr(module)


class TestMockDUT:
    """Test the MockDUT class."""

    def test_mock_dut_creation_empty(self):
        """Test basic MockDUT creation without stub file."""
        dut = MockDUT(name="test_dut")
        
        assert dut._name == "test_dut"
        assert dut.stub_file is None
        assert len(dut._signals) == 0
        assert len(dut._sub_modules) == 0

    def test_mock_dut_creation_with_stub(self):
        """Test MockDUT creation with stub file."""
        stub_content = '''
class TestDut:
    clk: LogicObject
    rst_n: LogicObject
    submodule: SubModule

class SubModule:
    reg_a: LogicObject
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.pyi', delete=False) as f:
            f.write(stub_content)
            stub_file = f.name

        try:
            dut = MockDUT(stub_file=stub_file, name="test_dut")
            
            assert dut.stub_file == Path(stub_file)
            # Note: The parsing is basic and may not capture all signals
            # This test mainly ensures no errors occur during parsing
            
        finally:
            Path(stub_file).unlink()

    def test_mock_dut_add_signal(self):
        """Test adding signals to MockDUT."""
        dut = MockDUT(name="test_dut")
        
        signal = dut.add_signal("test_signal", "LogicArrayObject", 32)
        
        assert isinstance(signal, MockSignal)
        assert signal._name == "test_signal"
        assert signal._signal_type == "LogicArrayObject"
        assert signal._width == 32
        assert "test_signal" in dut._signals

    def test_mock_dut_add_submodule(self):
        """Test adding sub-modules to MockDUT."""
        dut = MockDUT(name="test_dut")
        
        submodule = dut.add_submodule("cpu_core", "CoreModule")
        
        assert isinstance(submodule, MockModule)
        assert submodule._name == "cpu_core"
        assert submodule._module_type == "CoreModule"
        assert "cpu_core" in dut._sub_modules

    def test_mock_dut_getattr(self):
        """Test MockDUT attribute access."""
        dut = MockDUT(name="test_dut")
        
        # Add existing signal and module
        dut.add_signal("clk", "LogicObject")
        dut.add_submodule("core", "CoreModule")
        
        # Access existing signal
        clk = dut.clk
        assert isinstance(clk, MockSignal)
        assert clk._name == "clk"
        
        # Access existing module
        core = dut.core
        assert isinstance(core, MockModule)
        assert core._name == "core"
        
        # Access non-existing attribute (should create signal)
        new_signal = dut.new_signal
        assert isinstance(new_signal, MockSignal)
        assert new_signal._name == "new_signal"

    def test_mock_dut_get_signals(self):
        """Test MockDUT get_signals method."""
        dut = MockDUT(name="test_dut")
        
        dut.add_signal("clk")
        dut.add_signal("rst_n")
        dut.add_submodule("core")  # Should not appear in signals
        
        signals = dut.get_signals()
        assert len(signals) == 2
        assert "clk" in signals
        assert "rst_n" in signals
        assert "core" not in signals

    def test_mock_dut_get_submodules(self):
        """Test MockDUT get_submodules method."""
        dut = MockDUT(name="test_dut")
        
        dut.add_signal("clk")  # Should not appear in submodules
        dut.add_submodule("core")
        dut.add_submodule("memory")
        
        submodules = dut.get_submodules()
        assert len(submodules) == 2
        assert "core" in submodules
        assert "memory" in submodules
        assert "clk" not in submodules

    def test_mock_dut_reset_all_signals(self):
        """Test MockDUT reset_all_signals method."""
        dut = MockDUT(name="test_dut")
        
        # Add signals and set values
        dut.add_signal("clk")
        dut.add_signal("data")
        dut.clk.value = 1
        dut.data.value = 42
        
        # Add submodule with signals
        core = dut.add_submodule("core")
        core.add_signal("reg")
        core.reg.value = 100
        
        # Reset all signals
        dut.reset_all_signals()
        
        assert dut.clk.value == 0
        assert dut.data.value == 0
        assert core.reg.value == 0

    def test_mock_dut_reset_all_signals_custom_value(self):
        """Test MockDUT reset_all_signals with custom value."""
        dut = MockDUT(name="test_dut")
        
        dut.add_signal("signal1")
        dut.add_signal("signal2")
        dut.signal1.value = 10
        dut.signal2.value = 20
        
        # Reset to custom value
        dut.reset_all_signals(value=5)
        
        assert dut.signal1.value == 5
        assert dut.signal2.value == 5

    def test_mock_dut_string_representation(self):
        """Test MockDUT string representations."""
        dut = MockDUT(name="test_dut")
        dut.add_signal("clk")
        dut.add_submodule("core")
        
        assert str(dut) == "MockDUT(test_dut)"
        assert "MockDUT(name='test_dut'" in repr(dut)
        assert "signals=1" in repr(dut)
        assert "submodules=1" in repr(dut)


class TestCreateMockDutFromHierarchy:
    """Test the create_mock_dut_from_hierarchy function."""

    def test_create_mock_dut_from_hierarchy_basic(self):
        """Test creating MockDUT from basic hierarchy."""
        hierarchy = {
            "dut": object,  # Top-level
            "clk": MockSignal,
            "rst_n": MockSignal,
            "data_in": MockSignal,
        }
        
        mock_dut = create_mock_dut_from_hierarchy(hierarchy, "test_dut")
        
        assert mock_dut._name == "test_dut"
        assert "clk" in mock_dut._signals
        assert "rst_n" in mock_dut._signals
        assert "data_in" in mock_dut._signals

    def test_create_mock_dut_from_hierarchy_nested(self):
        """Test creating MockDUT from nested hierarchy."""
        hierarchy = {
            "dut": object,
            "clk": MockSignal,
            "core.enable": MockSignal,
            "core.data": MockSignal,
            "memory.addr": MockSignal,
            "memory.data": MockSignal,
        }
        
        mock_dut = create_mock_dut_from_hierarchy(hierarchy, "nested_dut")
        
        assert mock_dut._name == "nested_dut"
        assert "clk" in mock_dut._signals
        assert "core" in mock_dut._sub_modules
        assert "memory" in mock_dut._sub_modules
        
        # Check nested signals
        core = mock_dut._sub_modules["core"]
        assert "enable" in core._children
        assert "data" in core._children
        
        memory = mock_dut._sub_modules["memory"]
        assert "addr" in memory._children
        assert "data" in memory._children

    def test_create_mock_dut_from_hierarchy_deep_nesting(self):
        """Test creating MockDUT from deeply nested hierarchy."""
        hierarchy = {
            "dut": object,
            "cpu.core.alu.result": MockSignal,
            "cpu.core.alu.flags": MockSignal,
            "cpu.cache.hit": MockSignal,
        }
        
        mock_dut = create_mock_dut_from_hierarchy(hierarchy, "deep_dut")
        
        assert "cpu" in mock_dut._sub_modules
        cpu = mock_dut._sub_modules["cpu"]
        
        assert "core" in cpu._children
        core = cpu._children["core"]
        
        assert "alu" in core._children
        alu = core._children["alu"]
        
        assert "result" in alu._children
        assert "flags" in alu._children
        
        assert "cache" in cpu._children
        cache = cpu._children["cache"]
        assert "hit" in cache._children

    def test_create_mock_dut_from_hierarchy_empty(self):
        """Test creating MockDUT from empty hierarchy."""
        hierarchy = {}
        
        mock_dut = create_mock_dut_from_hierarchy(hierarchy, "empty_dut")
        
        assert mock_dut._name == "empty_dut"
        assert len(mock_dut._signals) == 0
        assert len(mock_dut._sub_modules) == 0

    def test_create_mock_dut_from_hierarchy_mixed_types(self):
        """Test creating MockDUT from hierarchy with mixed signal types."""
        hierarchy = {
            "dut": object,
            "logic_signal": MockSignal,
            "array_signal": MockSignal,
            "module.sub_signal": MockSignal,
        }
        
        mock_dut = create_mock_dut_from_hierarchy(hierarchy, "mixed_dut")
        
        # Check that all signals are created with correct types
        assert "logic_signal" in mock_dut._signals
        assert "array_signal" in mock_dut._signals
        assert "module" in mock_dut._sub_modules
        
        module = mock_dut._sub_modules["module"]
        assert "sub_signal" in module._children 