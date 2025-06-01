# Minimal Example

Simple 8-bit passthrough module demonstrating copra's complete feature set.

## Files

- `minimal.sv` - Simple 8-bit passthrough module with reset
- `generate_stubs.py` - Comprehensive stub generation script
- `test_minimal.py` - Test suite with type integration
- `Makefile` - Build and test configuration

## Features Demonstrated

- **Hierarchical Stub Generation** - Proper module structure for simple designs
- **Multiple Output Formats** - `.pyi` stubs and `.py` runtime modules
- **Documentation Generation** - Markdown, HTML, and RST formats
- **Testbench Templates** - Auto-generated test scaffolding
- **Enhanced Analysis** - Signal categorization and interface validation
- **Real Simulation Integration** - Uses actual cocotb simulation for discovery

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
- `minimal_interface.{md,html,rst}` - Documentation
- `test_minimal_generated.py` - Testbench template

## Generated Type Stubs

```python
class Minimal(HierarchyObject):
    """Type stub for minimal module."""
    
    clk: SimHandleBase      # Clock input
    rst_n: SimHandleBase    # Active-low reset
    data_in: SimHandleBase  # 8-bit data input
    data_out: SimHandleBase # 8-bit data output

DutType = Minimal
```

## Signal Analysis

The generator automatically categorizes signals:
- **Clock signals**: `clk`
- **Reset signals**: `rst_n` 
- **Data signals**: `data_in`, `data_out`
- **Interface analysis**: Input vs output identification

## Requirements

- Python 3.8+
- cocotb 2.0+
- icarus verilog
- copra

