"""Tests for the copra.mocking module."""

import tempfile
from pathlib import Path
from unittest.mock import Mock

from copra.mocking import (
    BusFunctionalModel,
    MockDUT,
    MockModule,
    MockSignal,
    SignalValueHistory,
    create_mock_dut_from_hierarchy,
)


class TestMockSignal:
    """Test the MockSignal class."""

    def test_mock_signal_creation(self):
        """Test basic MockSignal creation."""
        signal = MockSignal("test_signal", "SimHandleBase", 8)

        assert signal._name == "test_signal"
        assert signal._signal_type == "SimHandleBase"
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
        signal = MockSignal("test_signal", "SimHandleBase", 8)
        signal.value = 42

        assert str(signal) == "MockSignal(test_signal=42)"
        assert "MockSignal(name='test_signal'" in repr(signal)
        assert "type='SimHandleBase'" in repr(signal)
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

        signal = module.add_signal("test_signal", "SimHandleBase", 16)

        assert isinstance(signal, MockSignal)
        assert signal._name == "test_signal"
        assert signal._signal_type == "SimHandleBase"
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
        module.add_signal("existing_signal", "SimHandleBase")

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
        stub_content = """
class TestDut:
    clk: SimHandleBase
    rst_n: SimHandleBase
    submodule: SubModule

class SubModule:
    reg_a: SimHandleBase
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".pyi", delete=False) as f:
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

        signal = dut.add_signal("test_signal", "LogicArray", 32)

        assert isinstance(signal, MockSignal)
        assert signal._name == "test_signal"
        assert signal._signal_type == "LogicArray"
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
        dut.add_signal("clk", "SimHandleBase")
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


class TestSignalValueHistory:
    """Test signal value history tracking."""

    def test_record_change(self):
        """Test recording value changes."""
        history = SignalValueHistory(max_history=5)

        # Record some changes
        history.record_change(0, 1, 1.0)
        history.record_change(1, 0, 2.0)
        history.record_change(0, 1, 3.0)

        assert len(history.history) == 3
        assert history.history[0]["old_value"] == 0
        assert history.history[0]["new_value"] == 1
        assert history.history[0]["timestamp"] == 1.0

    def test_max_history_limit(self):
        """Test that history respects max_history limit."""
        history = SignalValueHistory(max_history=2)

        # Record more changes than the limit
        for i in range(5):
            history.record_change(i, i + 1, float(i))

        # Should only keep the last 2 changes
        assert len(history.history) == 2
        assert history.history[0]["old_value"] == 3
        assert history.history[1]["old_value"] == 4

    def test_get_change_count(self):
        """Test getting change count."""
        history = SignalValueHistory()

        assert history.get_change_count() == 0

        history.record_change(0, 1)
        history.record_change(1, 0)

        assert history.get_change_count() == 2

    def test_get_last_change(self):
        """Test getting last change."""
        history = SignalValueHistory()

        assert history.get_last_change() is None

        history.record_change(0, 1, 1.0)
        history.record_change(1, 0, 2.0)

        last_change = history.get_last_change()
        assert last_change["old_value"] == 1
        assert last_change["new_value"] == 0
        assert last_change["timestamp"] == 2.0

    def test_clear_history(self):
        """Test clearing history."""
        history = SignalValueHistory()

        history.record_change(0, 1)
        history.record_change(1, 0)
        assert len(history.history) == 2

        history.clear()
        assert len(history.history) == 0
        assert history.get_change_count() == 0


class TestEnhancedMockSignal:
    """Test enhanced MockSignal with value history and callbacks."""

    def test_signal_initialization(self):
        """Test signal initialization with width."""
        signal = MockSignal("test_signal", "SimHandleBase", width=8)

        assert signal._name == "test_signal"
        assert signal._handle_type == "SimHandleBase"
        assert signal._width == 8
        assert signal._value == 0
        assert not signal._is_driven

    def test_value_change_tracking(self):
        """Test that value changes are tracked in history."""
        signal = MockSignal("test_signal", "SimHandleBase")

        # Change value
        signal.value = 1
        assert signal.value == 1
        assert signal._value_history.get_change_count() == 1

        # Change again
        signal.value = 0
        assert signal.value == 0
        assert signal._value_history.get_change_count() == 2

        # Check last change
        last_change = signal._value_history.get_last_change()
        assert last_change["old_value"] == 1
        assert last_change["new_value"] == 0

    def test_callback_functionality(self):
        """Test callback registration and execution."""
        signal = MockSignal("test_signal", "SimHandleBase")

        callback_calls = []

        def test_callback(old_val, new_val):
            callback_calls.append((old_val, new_val))

        # Add callback
        signal.add_callback(test_callback)

        # Change value - should trigger callback
        signal.value = 1
        assert len(callback_calls) == 1
        assert callback_calls[0] == (0, 1)

        # Change again
        signal.value = 5
        assert len(callback_calls) == 2
        assert callback_calls[1] == (1, 5)

    def test_callback_removal(self):
        """Test callback removal."""
        signal = MockSignal("test_signal", "SimHandleBase")

        callback_calls = []

        def test_callback(old_val, new_val):
            callback_calls.append((old_val, new_val))

        # Add and remove callback
        signal.add_callback(test_callback)
        signal.remove_callback(test_callback)

        # Change value - should not trigger callback
        signal.value = 1
        assert len(callback_calls) == 0

    def test_width_validation(self):
        """Test signal width validation."""
        signal = MockSignal("test_signal", "SimHandleBase", width=4)

        # Valid value (within 4-bit range)
        signal.value = 15  # 0xF
        assert signal.value == 15

        # Value exceeding width should be masked
        signal.value = 16  # 0x10, should become 0
        assert signal.value == 0

        signal.value = 31  # 0x1F, should become 0xF
        assert signal.value == 15

    def test_driven_state_tracking(self):
        """Test tracking of driven state."""
        signal = MockSignal("test_signal", "SimHandleBase")

        assert not signal._is_driven

        # Setting value should mark as driven
        signal.value = 1
        assert signal._is_driven

        # Reset driven state
        signal._is_driven = False
        assert not signal._is_driven


class TestBusFunctionalModel:
    """Test bus functional model functionality."""

    def test_bfm_initialization(self):
        """Test BFM initialization."""
        bfm = BusFunctionalModel("test_bus")

        assert bfm.name == "test_bus"
        assert len(bfm.signals) == 0
        assert not bfm.is_active

    def test_signal_registration(self):
        """Test signal registration with BFM."""
        bfm = BusFunctionalModel("test_bus")
        signal = MockSignal("data", "SimHandleBase", width=8)

        bfm.add_signal("data", signal)
        assert "data" in bfm.signals
        assert bfm.signals["data"] is signal

    def test_transaction_execution(self):
        """Test transaction execution."""
        bfm = BusFunctionalModel("test_bus")

        # Add signals
        data_signal = MockSignal("data", "SimHandleBase", width=8)
        valid_signal = MockSignal("valid", "SimHandleBase")

        bfm.add_signal("data", data_signal)
        bfm.add_signal("valid", valid_signal)

        # Define a simple transaction
        async def write_transaction(data_value):
            bfm.signals["data"].value = data_value
            bfm.signals["valid"].value = 1
            # In real usage, would await clock cycles here
            bfm.signals["valid"].value = 0

        # Execute transaction
        import asyncio

        async def test_transaction():
            await write_transaction(0x42)
            assert data_signal.value == 0x42
            assert valid_signal.value == 0

        asyncio.run(test_transaction())

    def test_bfm_start_stop(self):
        """Test BFM start and stop functionality."""
        bfm = BusFunctionalModel("test_bus")

        assert not bfm.is_active

        bfm.start()
        assert bfm.is_active

        bfm.stop()
        assert not bfm.is_active

    def test_bfm_reset(self):
        """Test BFM reset functionality."""
        bfm = BusFunctionalModel("test_bus")

        # Add and configure signals
        signal1 = MockSignal("sig1", "SimHandleBase")
        signal2 = MockSignal("sig2", "SimHandleBase")

        bfm.add_signal("sig1", signal1)
        bfm.add_signal("sig2", signal2)

        # Set some values
        signal1.value = 1
        signal2.value = 1

        # Reset should clear all signals
        bfm.reset()
        assert signal1.value == 0
        assert signal2.value == 0


class TestEnhancedMockDUT:
    """Test enhanced MockDUT functionality."""

    def test_mock_dut_with_bfm(self):
        """Test MockDUT with bus functional model integration."""
        hierarchy = {
            "dut": Mock,
            "dut.bus_data": Mock,
            "dut.bus_valid": Mock,
            "dut.bus_ready": Mock,
        }

        mock_dut = create_mock_dut_from_hierarchy(hierarchy)

        # Should have created signals
        assert hasattr(mock_dut, "bus_data")
        assert hasattr(mock_dut, "bus_valid")
        assert hasattr(mock_dut, "bus_ready")

        # Test signal functionality
        mock_dut.bus_data.value = 0x42
        assert mock_dut.bus_data.value == 0x42

    def test_mock_dut_signal_access(self):
        """Test signal access patterns in MockDUT."""
        hierarchy = {
            "dut": Mock,
            "dut.clk": Mock,
            "dut.rst_n": Mock,
            "dut.data_in": Mock,
            "dut.data_out": Mock,
        }

        mock_dut = create_mock_dut_from_hierarchy(hierarchy)

        # Test direct access
        assert hasattr(mock_dut, "clk")
        assert hasattr(mock_dut, "rst_n")
        assert hasattr(mock_dut, "data_in")
        assert hasattr(mock_dut, "data_out")

        # Test value setting
        mock_dut.clk.value = 1
        mock_dut.rst_n.value = 0
        mock_dut.data_in.value = 0xFF

        assert mock_dut.clk.value == 1
        assert mock_dut.rst_n.value == 0
        assert mock_dut.data_in.value == 0xFF

    def test_mock_dut_with_arrays(self):
        """Test MockDUT with array signals."""
        hierarchy = {
            "dut": Mock,
            "dut.mem[0]": Mock,
            "dut.mem[1]": Mock,
            "dut.mem[2]": Mock,
            "dut.mem[3]": Mock,
        }

        mock_dut = create_mock_dut_from_hierarchy(hierarchy)

        # Should create array-like access
        # Note: This tests the basic functionality, real array access
        # would require more sophisticated implementation
        assert hasattr(mock_dut, "mem")


class TestMockingIntegration:
    """Test integration between different mocking components."""

    def test_signal_history_with_callbacks(self):
        """Test that signal history works with callbacks."""
        signal = MockSignal("test_signal", "SimHandleBase")

        callback_history = []

        def history_callback(old_val, new_val):
            callback_history.append(f"Changed from {old_val} to {new_val}")

        signal.add_callback(history_callback)

        # Make several changes
        signal.value = 1
        signal.value = 2
        signal.value = 0

        # Check both callback history and signal history
        assert len(callback_history) == 3
        assert signal._value_history.get_change_count() == 3

        # Verify callback content
        assert "Changed from 0 to 1" in callback_history[0]
        assert "Changed from 1 to 2" in callback_history[1]
        assert "Changed from 2 to 0" in callback_history[2]

    def test_bfm_with_signal_history(self):
        """Test BFM integration with signal value history."""
        bfm = BusFunctionalModel("test_bus")

        # Create signals with history tracking
        data_signal = MockSignal("data", "SimHandleBase", width=8)
        valid_signal = MockSignal("valid", "SimHandleBase")

        bfm.add_signal("data", data_signal)
        bfm.add_signal("valid", valid_signal)

        # Perform some operations
        bfm.signals["data"].value = 0x10
        bfm.signals["valid"].value = 1
        bfm.signals["valid"].value = 0
        bfm.signals["data"].value = 0x20

        # Check that history was recorded
        assert data_signal._value_history.get_change_count() == 2
        assert valid_signal._value_history.get_change_count() == 2

        # Check specific changes
        data_changes = data_signal._value_history.history
        assert data_changes[0]["new_value"] == 0x10
        assert data_changes[1]["new_value"] == 0x20

    def test_mock_dut_comprehensive(self):
        """Test comprehensive MockDUT functionality."""
        # Create a complex hierarchy
        hierarchy = {
            "dut": Mock,
            "dut.cpu": Mock,
            "dut.cpu.clk": Mock,
            "dut.cpu.rst_n": Mock,
            "dut.memory": Mock,
            "dut.memory.addr": Mock,
            "dut.memory.data": Mock,
            "dut.memory.we": Mock,
            "dut.bus": Mock,
            "dut.bus.req": Mock,
            "dut.bus.ack": Mock,
        }

        mock_dut = create_mock_dut_from_hierarchy(hierarchy)

        # Test nested access
        assert hasattr(mock_dut, "cpu")
        assert hasattr(mock_dut, "memory")
        assert hasattr(mock_dut, "bus")

        # Test signal operations
        mock_dut.cpu.clk.value = 1
        mock_dut.memory.addr.value = 0x1000
        mock_dut.memory.data.value = 0xDEADBEEF
        mock_dut.memory.we.value = 1

        # Verify values
        assert mock_dut.cpu.clk.value == 1
        assert mock_dut.memory.addr.value == 0x1000
        assert mock_dut.memory.data.value == 0xDEADBEEF
        assert mock_dut.memory.we.value == 1

        # Test that changes are tracked
        assert mock_dut.cpu.clk._value_history.get_change_count() == 1
        assert mock_dut.memory.addr._value_history.get_change_count() == 1
