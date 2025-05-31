# Minimal Example: End-to-End Type Stub Generation

This example demonstrates copra's core functionality with a simple SystemVerilog module. It shows the complete workflow from HDL source to generated type stubs.

## Overview

The minimal example includes:
- **`minimal.sv`**: A simple SystemVerilog module (8-bit passthrough with reset)
- **`generate_stubs.py`**: Script that runs real simulation to discover DUT hierarchy
- **`test_minimal.py`**: Comprehensive test suite demonstrating stub usage
- **`dut.pyi`**: Generated type stubs (created by running the generator)

## Key Features Demonstrated

1. **Real Simulation Integration**: Uses actual cocotb simulation to discover DUT
2. **Hierarchy Discovery**: Automatically finds all signals and their types
3. **Type Stub Generation**: Creates `.pyi` files for IDE autocompletion
4. **IDE Integration**: Shows how stubs enable autocompletion and type checking
5. **Runtime Generation**: Demonstrates generating stubs from within tests

## Quick Start

### 1. Generate Type Stubs

```bash
# Run the stub generator (requires icarus verilog)
python generate_stubs.py
```

This will:
- Compile the SystemVerilog module using icarus
- Run a discovery simulation to introspect the DUT
- Generate `dut.pyi` with proper type annotations

### 2. Run Tests with Type Support

```bash
# Run the test suite
make
```

The tests demonstrate:
- Basic functionality testing
- Runtime stub generation
- Type checking benefits

## Generated Stub Structure

The generated `dut.pyi` provides:

```python
from cocotb.handle import HierarchyObject, SimHandleBase

class Minimal(HierarchyObject):
    """Minimal example DUT with proper type annotations."""
    
    clk: SimHandleBase      # Clock input
    rst_n: SimHandleBase    # Active-low reset  
    data_in: SimHandleBase  # 8-bit data input
    data_out: SimHandleBase # 8-bit data output

DutType = Minimal  # Type alias for convenience
```

## IDE Benefits

With the generated stubs, your IDE will provide:

- **Autocompletion**: Type `dut.` and see all available signals
- **Type Checking**: Catch typos like `dut.clokc` before runtime
- **Documentation**: Hover over signals to see descriptions
- **Navigation**: Jump to signal definitions

## Requirements

- Python 3.8+
- cocotb 2.0+
- icarus verilog (or another supported simulator)
- copra (this project)

## Files

- `minimal.sv` - Simple 8-bit passthrough module with reset
- `generate_stubs.py` - End-to-end stub generation script  
- `test_minimal.py` - Test suite with type stub integration
- `Makefile` - cocotb test configuration
- `dut.pyi` - Generated type stubs (created by generator)

