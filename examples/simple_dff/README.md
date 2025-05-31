# Simple DFF Example: Comprehensive Type Stub Generation

This example demonstrates copra's capabilities with a D flip-flop, showing comprehensive testing and advanced stub generation features.

## Overview

The simple DFF example includes:
- **`dff.sv`**: A D flip-flop with clock and active-low reset
- **`generate_stubs.py`**: Advanced stub generation with DFF-specific analysis
- **`test_dff.py`**: Comprehensive test suite with multiple test scenarios
- **`dut.pyi`**: Generated type stubs with detailed signal information

## Key Features Demonstrated

1. **Real Simulation Integration**: Uses actual cocotb simulation for DUT discovery
2. **Signal-Specific Analysis**: Validates expected DFF signals (clk, rst_n, d, q)
3. **Comprehensive Testing**: Multiple test scenarios covering all DFF behaviors
4. **Advanced Type Annotations**: Shows proper type usage in complex test scenarios
5. **Edge Case Testing**: Demonstrates timing and reset behavior validation

## Quick Start

### 1. Generate Type Stubs

```bash
# Run the advanced stub generator
python generate_stubs.py
```

This will:
- Compile the DFF module using icarus verilog
- Run discovery simulation to introspect the DUT
- Analyze DFF-specific signals and validate completeness
- Generate comprehensive `dut.pyi` with proper annotations

### 2. Run Comprehensive Tests

```bash
# Run the full test suite
make
```

The test suite includes:
- **Basic functionality**: D input to Q output behavior
- **Reset behavior**: Asynchronous reset testing
- **Edge cases**: Timing and rapid input changes
- **Runtime generation**: In-test stub generation
- **Comprehensive sequences**: Complex test patterns

## Generated Stub Structure

The generated `dut.pyi` provides:

```python
from cocotb.handle import HierarchyObject, SimHandleBase

class Dff(HierarchyObject):
    """Simple D Flip-Flop DUT.
    
    A basic D flip-flop with clock and active-low reset.
    
    Signals:
        clk: Clock input
        rst_n: Active-low reset
        d: Data input
        q: Data output (registered)
    """
    
    clk: SimHandleBase
    rst_n: SimHandleBase
    d: SimHandleBase
    q: SimHandleBase

DutType = Dff  # Type alias for convenience
```

## Test Scenarios

### 1. Basic Functionality Test
- Verifies D-to-Q transfer on clock edges
- Tests multiple input patterns
- Validates proper clocking behavior

### 2. Reset Behavior Test
- Tests asynchronous reset assertion
- Verifies reset holds Q at 0
- Tests reset release behavior

### 3. Edge Case Test
- Rapid D input changes between clock edges
- Validates only final D value matters at clock edge
- Tests setup/hold time behavior

### 4. Comprehensive Sequence Test
- Complex binary patterns
- State transitions
- Extended test sequences

## Advanced Features

### DFF-Specific Analysis
The generator performs DFF-specific validation:
- Checks for expected signals (clk, rst_n, d, q)
- Validates signal discovery completeness
- Provides detailed analysis report

### Type Safety Benefits
With generated stubs:
- IDE autocompletion for all DFF signals
- Static type checking catches signal name typos
- Better code documentation and navigation
- Improved development experience

## Requirements

- Python 3.8+
- cocotb 2.0+
- icarus verilog (or another supported simulator)
- copra (this project)

## Files

- `dff.sv` - D flip-flop with clock and reset
- `generate_stubs.py` - Advanced stub generation with DFF analysis
- `test_dff.py` - Comprehensive test suite with multiple scenarios
- `Makefile` - cocotb test configuration
- `dut.pyi` - Generated type stubs (created by generator) 