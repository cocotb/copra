"""Test for the simple DFF module with type stub integration."""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

# Import the generated stubs for type checking
# This enables IDE autocompletion and static type checking
try:
    from .dut import DutType
    # Type annotation for the DUT parameter
    DUT_TYPE_AVAILABLE = True
except ImportError:
    # Fallback if stubs haven't been generated yet
    DUT_TYPE_AVAILABLE = False
    DutType = None


@cocotb.test()
async def test_dff_basic_functionality(dut):
    """Test the basic D flip-flop functionality.

    Args:
    ----
        dut: The DUT (Design Under Test) handle.
             With generated stubs, this should provide autocompletion
             for dut.clk, dut.rst_n, dut.d, dut.q

    """
    # Type annotation for better IDE support (when stubs are available)
    if DUT_TYPE_AVAILABLE:
        dut: DutType  # This enables autocompletion and type checking
    
    print(f"[test] Starting DFF test for DUT: {dut._name}")
    print(f"[test] Type stubs available: {DUT_TYPE_AVAILABLE}")

    # Create a 10ns period clock on the clk signal
    # With stubs, IDE should autocomplete dut.clk
    clock = Clock(dut.clk, 10, units="ns")

    # Start the clock
    cocotb.start_soon(clock.start())

    # Reset sequence
    print("[test] Applying reset...")
    dut.rst_n.value = 0  # Assert reset (active low)
    dut.d.value = 0      # Initialize D input

    # Wait for two clock cycles during reset
    await RisingEdge(dut.clk)
    await Timer(1, units="ns")  # Small delay for signal propagation
    await RisingEdge(dut.clk)
    await Timer(1, units="ns")  # Small delay for signal propagation

    # Check that output is 0 during reset
    q_val = int(dut.q.value)
    print(f"[test] Output during reset: {q_val}")
    assert q_val == 0, f"Expected Q=0 during reset, got Q={q_val}"

    # Release reset
    print("[test] Releasing reset...")
    dut.rst_n.value = 1

    # Wait for reset to take effect
    await RisingEdge(dut.clk)
    await Timer(1, units="ns")  # Small delay for signal propagation

    # Test D flip-flop behavior
    test_values = [0, 1, 0, 1, 1, 0, 0, 1]
    
    print(f"[test] Testing {len(test_values)} D input values...")

    for i, d_val in enumerate(test_values):
        print(f"[test] Test {i+1}/{len(test_values)}: D = {d_val}")
        
        # Set D input
        # With stubs, IDE should autocomplete dut.d
        dut.d.value = d_val

        # Wait for the clock edge (D should be captured)
        await RisingEdge(dut.clk)
        await Timer(1, units="ns")  # Small delay for signal propagation
        
        # Check Q output after the clock edge
        # With stubs, IDE should autocomplete dut.q
        q_val = int(dut.q.value)
        
        print(f"[test]   D = {d_val}, Q = {q_val}")
        
        # Verify that Q follows D after clock edge
        assert q_val == d_val, f"DFF failed! Expected Q={d_val}, got Q={q_val}"
        
        print(f"[test]   ✓ PASS")

    print("[test] All DFF functionality tests passed!")


@cocotb.test()
async def test_dff_reset_behavior(dut):
    """Test the reset behavior of the D flip-flop."""
    print("[test] Testing DFF reset behavior...")
    
    # Type annotation
    if DUT_TYPE_AVAILABLE:
        dut: DutType
    
    # Create clock
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    
    # Initialize properly
    dut.rst_n.value = 0
    dut.d.value = 0
    await RisingEdge(dut.clk)
    await Timer(1, units="ns")
    
    # Set D to 1 and release reset to get Q = 1
    dut.d.value = 1
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)
    await Timer(1, units="ns")  # Small delay for signal propagation
    
    q_val = int(dut.q.value)
    print(f"[test] Q after setting D=1: {q_val}")
    assert q_val == 1, f"Expected Q=1, got Q={q_val}"
    
    # Now test reset while Q is 1
    print("[test] Testing reset while Q=1...")
    dut.rst_n.value = 0  # Assert reset
    
    # Reset should be asynchronous, so Q should go to 0 immediately
    # Wait a small amount for the reset to propagate
    await Timer(1, units="ns")  # Small delay for reset propagation
    
    q_val = int(dut.q.value)
    print(f"[test] Q after reset assertion: {q_val}")
    assert q_val == 0, f"Reset failed! Expected Q=0, got Q={q_val}"
    
    # Keep reset asserted for multiple cycles
    for i in range(3):
        await RisingEdge(dut.clk)
        await Timer(1, units="ns")
        q_val = int(dut.q.value)
        print(f"[test] Q during reset cycle {i+1}: {q_val}")
        assert q_val == 0, f"Q should remain 0 during reset, got Q={q_val}"
    
    print("[test] ✓ Reset behavior test passed!")


@cocotb.test()
async def test_dff_edge_cases(dut):
    """Test edge cases and timing for the D flip-flop."""
    print("[test] Testing DFF edge cases...")
    
    # Type annotation
    if DUT_TYPE_AVAILABLE:
        dut: DutType
    
    # Create clock
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    
    # Initialize properly
    dut.rst_n.value = 0
    dut.d.value = 0
    await RisingEdge(dut.clk)
    await Timer(1, units="ns")
    
    # Release reset
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)
    await Timer(1, units="ns")
    
    # Test rapid D changes (only the value at clock edge should matter)
    print("[test] Testing rapid D input changes...")
    
    # Set D = 1 just before clock edge
    dut.d.value = 1
    await RisingEdge(dut.clk)
    await Timer(1, units="ns")  # Small delay for signal propagation
    
    # Q should be 1 now
    q_val = int(dut.q.value)
    assert q_val == 1, f"Expected Q=1 after D=1 at clock edge, got Q={q_val}"
    
    # Change D multiple times between clock edges
    dut.d.value = 0
    dut.d.value = 1
    dut.d.value = 0  # Final value before next clock edge
    
    await RisingEdge(dut.clk)
    await Timer(1, units="ns")  # Small delay for signal propagation
    
    # Q should reflect the final D value (0)
    q_val = int(dut.q.value)
    assert q_val == 0, f"Expected Q=0 (final D value), got Q={q_val}"
    
    print("[test] ✓ Edge case tests passed!")


@cocotb.test()
async def test_stub_generation_integration(dut):
    """Test that demonstrates stub generation from within a DFF test."""
    print("[test] Demonstrating in-test stub generation for DFF...")
    
    try:
        # Import copra for stub generation
        from copra import create_stub_from_dut
        
        # Generate stubs from the current DUT
        stub_content = create_stub_from_dut(dut, "dut_runtime.pyi")
        
        print(f"[test] ✓ Generated runtime stubs: {len(stub_content)} characters")
        print(f"[test] ✓ Stub file: dut_runtime.pyi")
        
        # Show a preview of the generated stubs
        lines = stub_content.splitlines()
        print("[test] Generated stub preview:")
        for i, line in enumerate(lines[:10], 1):
            print(f"[test]   {i:2d}: {line}")
        if len(lines) > 10:
            print(f"[test]   ... and {len(lines) - 10} more lines")
            
    except ImportError:
        print("[test] ⚠ copra not available for runtime stub generation")
    except Exception as e:
        print(f"[test] ⚠ Error during runtime stub generation: {e}")

    # Continue with a simple DFF test to ensure DUT still works
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    
    # Initialize properly
    dut.rst_n.value = 0
    dut.d.value = 0
    await RisingEdge(dut.clk)
    await Timer(1, units="ns")
    
    # Set D=1 and release reset
    dut.d.value = 1
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)
    await Timer(1, units="ns")  # Small delay for signal propagation
    
    q_val = int(dut.q.value)
    print(f"[test] Quick DFF test: D=1, Q={q_val}")
    assert q_val == 1, f"Expected Q=1, got Q={q_val}"


@cocotb.test()
async def test_dff_comprehensive_sequence(dut):
    """Comprehensive test sequence for the D flip-flop."""
    print("[test] Running comprehensive DFF test sequence...")
    
    # Type annotation
    if DUT_TYPE_AVAILABLE:
        dut: DutType
    
    # Create clock
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    
    # Test sequence: binary counting pattern
    test_sequence = [
        (0, 0),  # (D, expected_Q_after_clock)
        (1, 1),
        (0, 0),
        (1, 1),
        (1, 1),  # D stays same
        (0, 0),
        (0, 0),  # D stays same
        (1, 1),
    ]
    
    # Initialize properly
    dut.rst_n.value = 0
    dut.d.value = 0
    await RisingEdge(dut.clk)
    await Timer(1, units="ns")
    
    # Release reset
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)
    await Timer(1, units="ns")
    
    print("[test] Running test sequence:")
    for i, (d_val, expected_q) in enumerate(test_sequence):
        print(f"[test] Step {i+1}: D={d_val}")
        
        # Set D input
        dut.d.value = d_val
        
        # Clock edge
        await RisingEdge(dut.clk)
        await Timer(1, units="ns")  # Small delay for signal propagation
        
        # Check Q
        q_val = int(dut.q.value)
        print(f"[test]   Result: Q={q_val} (expected {expected_q})")
        
        assert q_val == expected_q, f"Step {i+1} failed: expected Q={expected_q}, got Q={q_val}"
        print(f"[test]   ✓ PASS")
    
    print("[test] ✓ Comprehensive sequence test passed!")


# This would be the command to generate stubs for this example:
# $ copra examples/simple_dff/dff -o examples/simple_dff/dut.pyi
