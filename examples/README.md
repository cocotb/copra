# copra Examples

This directory contains examples demonstrating how to use copra to generate Python type stubs for cocotb testbenches.

## Simple DFF Example

```python
# examples/simple_dff/test_dff.py
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge

@cocotb.test()
async def test_dff(dut):
    """Test a simple D flip-flop."""
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    
    # Reset
    dut.rst_n.value = 0
    dut.d.value = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    
    # Test data
    test_values = [0, 1, 0, 1, 1, 0]
    
    for i, val in enumerate(test_values, 1):
        dut.d.value = val
        await RisingEdge(dut.clk)
        assert dut.q.value == (test_values[i-2] if i > 1 else 0), \
            f"Expected {test_values[i-2]}, got {dut.q.value}"
```

To generate stubs for this example:

```bash
# From the repository root
copra examples/simple_dff/dff -o examples/simple_dff/dut.pyi
```

The generated `dut.pyi` will contain type information for the DUT hierarchy, enabling better IDE support and type checking.
