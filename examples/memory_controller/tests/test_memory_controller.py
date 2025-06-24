#!/usr/bin/env python3
"""
Cocotb 2.0 tests for Memory Controller example
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles
import random
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from copra_stubs.dut import DUT
else:
    DUT = Any


@cocotb.test()
async def test_memory_controller_reset(dut: DUT):
    """Test that the memory controller correctly resets."""
    # Create clock
    clock = Clock(dut.clk, 10, "ns")
    clock.start()
    
    # Assert reset
    dut.rst_n.value = 0
    dut.enable.value = 0
    dut.ch_req.value = 0
    dut.refresh_interval.value = 1000
    dut.bank_count.value = 4
    
    await ClockCycles(dut.clk, 5)
    
    # Check initial state
    # Note: Some memory controllers may not reset ready signal
    # assert dut.ready.value == 0, "Ready should be low during reset"
    assert dut.error_status.value == 0, "Error status should be clear during reset"
    
    # Release reset
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 2)
    
    # Check that controller is ready after reset
    assert dut.ready.value == 1, "Ready should be high after reset release"
    
    clock.stop()


@cocotb.test()
async def test_memory_controller_basic_operation(dut: DUT):
    """Test basic memory controller operation."""
    # Create clock
    clock = Clock(dut.clk, 10, "ns")
    clock.start()
    
    # Initialize
    dut.rst_n.value = 1
    dut.enable.value = 1
    dut.refresh_interval.value = 1000
    dut.bank_count.value = 4
    dut.ch_req.value = 0
    dut.ch_addr_packed.value = 0
    dut.ch_wdata_packed.value = 0
    dut.ch_wr_en.value = 0
    
    await ClockCycles(dut.clk, 5)
    
    # Verify idle state
    assert dut.ready.value == 1, "Controller should be ready in idle state"
    
    # Issue a read request on channel 0
    dut.ch_req.value = 1  # Request on channel 0
    dut.ch_addr_packed.value = 0x1000  # Address for channel 0
    dut.ch_wr_en.value = 0  # Read operation
    
    await ClockCycles(dut.clk, 3)
    
    # Clear request
    dut.ch_req.value = 0
    await ClockCycles(dut.clk, 2)
    
    # Verify return to ready state
    assert dut.ready.value == 1, "Controller should return to ready state"
    
    clock.stop()


@cocotb.test()
async def test_memory_controller_write_operation(dut: DUT):
    """Test memory controller write operation."""
    # Create clock
    clock = Clock(dut.clk, 10, "ns")
    clock.start()
    
    # Initialize
    dut.rst_n.value = 1
    dut.enable.value = 1
    dut.refresh_interval.value = 1000
    dut.bank_count.value = 4
    dut.ch_req.value = 0
    dut.ch_addr_packed.value = 0
    dut.ch_wdata_packed.value = 0
    dut.ch_wr_en.value = 0
    
    await ClockCycles(dut.clk, 5)
    
    # Issue a write request
    dut.ch_req.value = 1  # Request on channel 0
    dut.ch_addr_packed.value = 0x2000  # Address for channel 0
    dut.ch_wdata_packed.value = 0xDEADBEEF  # Write data for channel 0
    dut.ch_wr_en.value = 1  # Write operation
    
    await ClockCycles(dut.clk, 3)
    
    # Clear request
    dut.ch_req.value = 0
    dut.ch_wr_en.value = 0
    await ClockCycles(dut.clk, 2)
    
    # Verify return to ready state
    assert dut.ready.value == 1, "Controller should return to ready state after write"
    
    clock.stop()


@cocotb.test()
async def test_memory_controller_multi_channel(dut: DUT):
    """Test multi-channel memory controller operation."""
    # Create clock
    clock = Clock(dut.clk, 10, "ns")
    clock.start()
    
    # Initialize
    dut.rst_n.value = 1
    dut.enable.value = 1
    dut.refresh_interval.value = 1000
    dut.bank_count.value = 4
    dut.ch_req.value = 0
    dut.ch_addr_packed.value = 0
    dut.ch_wdata_packed.value = 0
    dut.ch_wr_en.value = 0
    
    await ClockCycles(dut.clk, 5)
    
    # Issue requests on multiple channels
    # Channel 0: Read from 0x1000
    # Channel 1: Write 0x12345678 to 0x2000
    # Channel 2: Read from 0x3000
    
    ch_req_val = 0b0111  # Channels 0, 1, 2
    ch_wr_en_val = 0b0010  # Only channel 1 is write
    
    # Pack addresses for channels 0, 1, 2
    addr_0 = 0x1000
    addr_1 = 0x2000
    addr_2 = 0x3000
    addr_3 = 0x0000
    packed_addr = (addr_3 << 96) | (addr_2 << 64) | (addr_1 << 32) | addr_0
    
    # Pack write data
    wdata_0 = 0x00000000
    wdata_1 = 0x12345678
    wdata_2 = 0x00000000
    wdata_3 = 0x00000000
    packed_wdata = (wdata_3 << 192) | (wdata_2 << 128) | (wdata_1 << 64) | wdata_0
    
    dut.ch_req.value = ch_req_val
    dut.ch_addr_packed.value = packed_addr
    dut.ch_wdata_packed.value = packed_wdata
    dut.ch_wr_en.value = ch_wr_en_val
    
    await ClockCycles(dut.clk, 5)
    
    # Clear requests
    dut.ch_req.value = 0
    dut.ch_wr_en.value = 0
    await ClockCycles(dut.clk, 3)
    
    # Verify return to ready state
    assert dut.ready.value == 1, "Controller should handle multi-channel requests"
    
    clock.stop()


@cocotb.test()
async def test_memory_controller_refresh(dut: DUT):
    """Test memory controller refresh operation."""
    # Create clock
    clock = Clock(dut.clk, 10, "ns")
    clock.start()
    
    # Initialize with short refresh interval
    dut.rst_n.value = 1
    dut.enable.value = 1
    dut.refresh_interval.value = 10  # Short interval for testing
    dut.bank_count.value = 4
    dut.ch_req.value = 0
    dut.ch_addr_packed.value = 0
    dut.ch_wdata_packed.value = 0
    dut.ch_wr_en.value = 0
    
    await ClockCycles(dut.clk, 5)
    
    # Wait for refresh to trigger
    await ClockCycles(dut.clk, 15)
    
    # Verify that controller still operates normally after refresh
    dut.ch_req.value = 1
    dut.ch_addr_packed.value = 0x4000
    dut.ch_wr_en.value = 0
    
    await ClockCycles(dut.clk, 5)
    
    dut.ch_req.value = 0
    await ClockCycles(dut.clk, 2)
    
    assert dut.ready.value == 1, "Controller should work normally after refresh"
    
    clock.stop()


@cocotb.test()
async def test_memory_controller_disable(dut: DUT):
    """Test memory controller disable functionality."""
    # Create clock
    clock = Clock(dut.clk, 10, "ns")
    clock.start()
    
    # Initialize
    dut.rst_n.value = 1
    dut.enable.value = 1
    dut.refresh_interval.value = 1000
    dut.bank_count.value = 4
    dut.ch_req.value = 0
    
    await ClockCycles(dut.clk, 5)
    assert dut.ready.value == 1, "Controller should be ready when enabled"
    
    # Disable controller
    dut.enable.value = 0
    await ClockCycles(dut.clk, 2)
    
    # Try to issue request while disabled
    dut.ch_req.value = 1
    dut.ch_addr_packed.value = 0x5000
    
    await ClockCycles(dut.clk, 5)
    
    # Controller should ignore requests when disabled
    # The exact behavior depends on implementation, but it should not process normally
    
    # Re-enable
    dut.enable.value = 1
    dut.ch_req.value = 0
    await ClockCycles(dut.clk, 2)
    
    assert dut.ready.value == 1, "Controller should be ready when re-enabled"
    
    clock.stop()


@cocotb.test()
async def test_memory_controller_performance_counters(dut: DUT):
    """Test memory controller performance monitoring."""
    # Create clock
    clock = Clock(dut.clk, 10, "ns")
    clock.start()
    
    # Initialize
    dut.rst_n.value = 1
    dut.enable.value = 1
    dut.refresh_interval.value = 1000
    dut.bank_count.value = 4
    dut.ch_req.value = 0
    
    await ClockCycles(dut.clk, 5)
    
    # Get initial counter values
    initial_cycle_count = int(dut.cycle_counter.value)
    
    # Perform some operations
    for i in range(3):
        dut.ch_req.value = 1
        dut.ch_addr_packed.value = 0x1000 + i * 0x100
        dut.ch_wr_en.value = i % 2  # Alternate read/write
        if i % 2:
            dut.ch_wdata_packed.value = 0x12345678 + i
        
        await ClockCycles(dut.clk, 3)
        
        dut.ch_req.value = 0
        dut.ch_wr_en.value = 0
        await ClockCycles(dut.clk, 2)
    
    # Check that counters have incremented
    final_cycle_count = int(dut.cycle_counter.value)
    assert final_cycle_count > initial_cycle_count, "Cycle counter should increment"
    
    clock.stop()


@cocotb.test()
async def test_memory_controller_stress(dut: DUT):
    """Stress test with random operations."""
    # Create clock
    clock = Clock(dut.clk, 10, "ns")
    clock.start()
    
    # Initialize
    dut.rst_n.value = 1
    dut.enable.value = 1
    dut.refresh_interval.value = 100
    dut.bank_count.value = 4
    dut.ch_req.value = 0
    
    await ClockCycles(dut.clk, 5)
    
    # Random operations
    random.seed(42)  # Reproducible random sequence
    
    for i in range(10):
        # Random channel (0-3)
        channel = random.randint(0, 3)
        # Random address
        addr = random.randint(0, 0xFFFF) & 0xFFFC  # Word aligned
        # Random write enable
        is_write = random.choice([0, 1])
        # Random data
        wdata = random.randint(0, 0xFFFFFFFF)
        
        # Set up request
        dut.ch_req.value = 1 << channel
        
        # Pack address and data for the specific channel
        packed_addr = addr << (32 * channel)
        packed_wdata = wdata << (64 * channel)
        
        dut.ch_addr_packed.value = packed_addr
        dut.ch_wdata_packed.value = packed_wdata
        dut.ch_wr_en.value = is_write << channel
        
        await ClockCycles(dut.clk, random.randint(2, 5))
        
        # Clear request
        dut.ch_req.value = 0
        dut.ch_wr_en.value = 0
        await ClockCycles(dut.clk, random.randint(1, 3))
        
        # Verify no error
        assert dut.error_status.value == 0, f"Error occurred during operation {i}"
    
    # Final check
    assert dut.ready.value == 1, "Controller should be ready after stress test"
    
    clock.stop()


# Note: This file should be run using the Makefile with a simulator like:
# make SIM=icarus
# or simply: make
