# Simple DFF Example

D flip-flop example demonstrating comprehensive type stub generation with signal analysis.

## Files

- `dff.sv` - D flip-flop with clock and active-low reset
- `generate_stubs.py` - Comprehensive stub generator with DFF analysis
- `test_dff.py` - Test suite with multiple scenarios
- `Makefile` - Build and test configuration

## Features Demonstrated

- **Real Simulation Integration** - Uses actual cocotb simulation for DUT discovery
- **Signal-Specific Analysis** - Validates expected DFF signals (clk, rst_n, d, q)
- **Comprehensive Testing** - Multiple test scenarios and edge cases
- **Enhanced Type Annotations** - Full IDE support with autocompletion
- **Multi-Format Output** - Type stubs, documentation, and testbench templates

## Quick Start

```bash
# Generate all outputs
python generate_stubs.py

# Run tests
make
```

**Generated files:**
- `dut.pyi` - Hierarchical type stubs
- `dut_runtime.pyi` - Runtime type module
- `dff_interface.{md,html}` - Documentation
- `test_dff_generated.py` - Testbench template

## Generated Type Stubs

```python
class Dff(HierarchyObject):
    """Simple D Flip-Flop DUT."""
    
    clk: SimHandleBase    # Clock input
    rst_n: SimHandleBase  # Active-low reset
    d: SimHandleBase      # Data input
    q: SimHandleBase      # Data output (registered)

DutType = Dff
```

## Requirements

- Python 3.8+
- cocotb 2.0+
- icarus verilog
- copra 