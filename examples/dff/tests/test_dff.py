#!/usr/bin/env python3
"""
Cocotb 2.0 tests for DFF example
"""
from typing import TYPE_CHECKING
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer, ClockCycles


if TYPE_CHECKING:
    from examples.dff.copra_stubs.dut import DUT
    dut: DUT


@cocotb.test()
async def test_dff_reset(dut: DUT):
    """Test that the DFF correctly resets when rst_n is low."""
    # Create clock
    clock = Clock(dut.clk, 10, "ns")
    clock.start()
    
    # Assert reset
    dut.rst_n.value = 0
    dut.d.value = 1
    
    await ClockCycles(dut.clk, 2)
    
    # Check that output is 0 during reset regardless of input
    assert dut.q.value == 0, f"Expected q=0 during reset, got {dut.q.value}"
    
    clock.stop()


@cocotb.test()
async def test_dff_basic_functionality(dut: DUT):
    """Test basic D flip-flop functionality."""
    # Create clock
    clock = Clock(dut.clk, 10, "ns")
    clock.start()
    
    # Release reset
    dut.rst_n.value = 1
    dut.d.value = 0
    
    await ClockCycles(dut.clk, 1)
    
    # Test setting input to 1
    dut.d.value = 1
    await RisingEdge(dut.clk)
    await Timer(1, "ns")  # Small delay to allow output to settle
    assert dut.q.value == 1, f"Expected q=1 after positive edge with d=1, got {dut.q.value}"
    
    # Test setting input to 0
    dut.d.value = 0
    await RisingEdge(dut.clk)
    await Timer(1, "ns")
    assert dut.q.value == 0, f"Expected q=0 after positive edge with d=0, got {dut.q.value}"
    
    clock.stop()


@cocotb.test()
async def test_dff_data_sequence(dut: DUT):
    """Test DFF with a sequence of data patterns."""
    # Create clock
    clock = Clock(dut.clk, 10, "ns")
    clock.start()
    
    # Release reset
    dut.rst_n.value = 1
    dut.d.value = 0  # Start with known value
    await ClockCycles(dut.clk, 1)
    
    # Test sequence: 1, 0, 1, 1, 0
    test_sequence = [1, 0, 1, 1, 0]
    
    for i, data in enumerate(test_sequence):
        dut.d.value = data
        await RisingEdge(dut.clk)
        await Timer(1, "ns")
        
        # Output should now match the input we set before this clock edge
        assert dut.q.value == data, \
            f"Step {i}: Expected q={data}, got {dut.q.value}"
    
    clock.stop()


@cocotb.test()
async def test_dff_reset_during_operation(dut: DUT):
    """Test that reset works correctly during normal operation."""
    # Create clock
    clock = Clock(dut.clk, 10, "ns")
    clock.start()
    
    # Normal operation
    dut.rst_n.value = 1
    dut.d.value = 1
    await ClockCycles(dut.clk, 2)
    
    # Verify q is 1
    assert dut.q.value == 1, f"Expected q=1 after normal operation, got {dut.q.value}"
    
    # Assert reset in middle of operation
    dut.rst_n.value = 0
    await Timer(1, "ns")  # Reset is asynchronous
    assert dut.q.value == 0, "Reset should immediately clear output"
    
    # Continue with reset asserted
    await ClockCycles(dut.clk, 2)
    assert dut.q.value == 0, "Output should remain 0 while reset is asserted"
    
    # Release reset and set up for next clock edge
    dut.rst_n.value = 1
    dut.d.value = 1
    await RisingEdge(dut.clk)  # Wait for rising edge
    await Timer(1, "ns")  # Allow output to settle
    assert dut.q.value == 1, "Normal operation should resume after reset release"
    
    clock.stop()


@cocotb.test()
async def test_dff_setup_hold_timing(dut: DUT):
    """Test setup and hold time requirements (basic test)."""
    # Create clock
    clock = Clock(dut.clk, 10, "ns")
    clock.start()
    
    # Release reset
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 1)
    
    # Change data just before clock edge to test setup time
    dut.d.value = 0
    await Timer(8, "ns")  # Wait most of the clock period
    dut.d.value = 1
    await Timer(2, "ns")  # Clock edge should occur here
    await Timer(1, "ns")  # Allow output to settle
    
    # The exact behavior depends on the simulator's timing model
    # This is more of a demonstration of how to test timing
    cocotb.log.info(f"Output after timing test: {dut.q.value}")
    
    clock.stop()


# Note: This file should be run using the Makefile with a simulator like:
# make SIM=icarus
# or simply: make
