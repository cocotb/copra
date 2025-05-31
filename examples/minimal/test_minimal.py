"""Test for the minimal example module with type stub integration."""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge

# Import the generated stubs for type checking
# This enables IDE autocompletion and static type checking
try:
    from .dut import DutType
    # Type annotation for the DUT parameter
    # This tells the IDE and type checkers what attributes are available
    DUT_TYPE_AVAILABLE = True
except ImportError:
    # Fallback if stubs haven't been generated yet
    DUT_TYPE_AVAILABLE = False
    DutType = None


@cocotb.test()
async def test_minimal_functionality(dut):
    """Test the minimal example module functionality.

    Args:
    ----
        dut: The DUT (Design Under Test) handle.
             With generated stubs, this should provide autocompletion
             for dut.clk, dut.rst_n, dut.data_in, dut.data_out

    """
    # Type annotation for better IDE support (when stubs are available)
    if DUT_TYPE_AVAILABLE:
        dut: DutType  # This enables autocompletion and type checking
    
    print(f"[test] Starting test for DUT: {dut._name}")
    print(f"[test] Type stubs available: {DUT_TYPE_AVAILABLE}")

    # Create a 10ns period clock on the clk signal
    # With stubs, IDE should autocomplete dut.clk
    clock = Clock(dut.clk, 10, units="ns")

    # Start the clock
    cocotb.start_soon(clock.start())

    # Reset sequence
    print("[test] Applying reset...")
    dut.rst_n.value = 0  # Assert reset (active low)
    dut.data_in.value = 0  # Initialize input

    # Wait for two clock cycles during reset
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)

    # Release reset
    print("[test] Releasing reset...")
    dut.rst_n.value = 1

    # Wait for reset to take effect
    await RisingEdge(dut.clk)

    # Test data sequence
    test_values = [0x00, 0x55, 0xAA, 0xFF, 0x12, 0x34, 0x56, 0x78]
    
    print(f"[test] Testing {len(test_values)} data values...")

    # Apply test values and check outputs
    for i, val in enumerate(test_values):
        print(f"[test] Test {i+1}/{len(test_values)}: input = 0x{val:02X}")
        
        # Set input value
        # With stubs, IDE should autocomplete dut.data_in
        dut.data_in.value = val

        # Wait for the next clock edge (for the input to be captured)
        await RisingEdge(dut.clk)
        
        # Wait for another clock edge (for the output to be updated)
        await RisingEdge(dut.clk)

        # Check output value
        # With stubs, IDE should autocomplete dut.data_out
        output_val = int(dut.data_out.value)
        
        print(f"[test]   Expected: 0x{val:02X}, Got: 0x{output_val:02X}")
        
        # Verify the output matches the input (this is a simple passthrough)
        assert output_val == val, f"Mismatch! Expected 0x{val:02X}, got 0x{output_val:02X}"
        
        print(f"[test]   ✓ PASS")

    print("[test] All test values passed!")


@cocotb.test()
async def test_stub_generation_integration(dut):
    """Test that demonstrates stub generation from within a test.
    
    This test shows how to generate stubs during test execution,
    which is useful for updating stubs when the DUT changes.
    """
    print("[test] Demonstrating in-test stub generation...")
    
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

    # Continue with a simple test to ensure DUT still works
    dut.rst_n.value = 0
    dut.data_in.value = 0x42
    
    # Wait a bit
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    
    output_val = int(dut.data_out.value)
    print(f"[test] Quick test: input=0x42, output=0x{output_val:02X}")


# Additional test to demonstrate type checking benefits
@cocotb.test()
async def test_type_checking_demo(dut):
    """Demonstrate the benefits of type checking with generated stubs.
    
    This test shows how type stubs help catch common errors.
    """
    print("[test] Demonstrating type checking benefits...")
    
    # With proper stubs, these should all autocomplete in your IDE:
    # - dut.clk
    # - dut.rst_n  
    # - dut.data_in
    # - dut.data_out
    
    # And these would be caught by static type checkers if they don't exist:
    # - dut.nonexistent_signal  # Would show error in IDE
    # - dut.typo_signal         # Would show error in IDE
    
    # Create clock
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    
    # Test sequence
    dut.rst_n.value = 0
    await RisingEdge(dut.clk)
    
    dut.rst_n.value = 1
    dut.data_in.value = 0xAB
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    
    result = int(dut.data_out.value)
    print(f"[test] Type checking demo result: 0x{result:02X}")
    
    assert result == 0xAB, f"Expected 0xAB, got 0x{result:02X}"
    print("[test] ✓ Type checking demo passed!")
