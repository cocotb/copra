# Complex CPU Example

Multi-core CPU design demonstrating advanced hierarchical stub generation with deep module structures.

## Files

- `cpu_top.sv` - Top-level CPU module
- `cpu_complex.sv` - CPU complex with arbiters  
- `cpu_core.sv` - Individual CPU core
- `clock_gen.sv` - Clock generation module
- `*.sv` - Supporting modules
- `generate_stubs.py` - Advanced stub generator with CPU analysis
- `test_cpu.py` - Comprehensive test suite
- `Makefile` - Build and test configuration

## Design Overview

- **Multi-core CPU** with individual clock gating
- **AXI4 interfaces** for instruction fetch and data memory
- **APB interface** for control/status registers
- **Debug interface** for development support
- **Performance counters** for monitoring
- **Deep hierarchy** with multiple sub-modules

## Features Demonstrated

- **Advanced Hierarchical Stubs** - Complex nested module structures
- **Multiple Output Formats** - Type stubs, runtime modules, documentation
- **CPU-Specific Analysis** - Interface categorization (AXI, APB, debug)
- **Enhanced Documentation** - Markdown, HTML, and RST formats
- **Testbench Templates** - Comprehensive test scaffolding
- **Signal Classification** - Clock, reset, data, control, and interrupt signals

## Quick Start

```bash
# Generate all outputs (requires more time due to complexity)
python generate_stubs.py

# Run tests
make
```

**Generated files:**
- `cpu_top.pyi` - Hierarchical type stubs (nested modules)
- `cpu_top_flat.pyi` - Flat hierarchy version for comparison
- `cpu_top_types.py` - Runtime type module
- `cpu_top_interface.{md,html,rst}` - Documentation
- `test_cpu_generated.py` - Testbench template

## Generated Hierarchy Example

```python
class CpuTop(HierarchyObject):
    """Type stub for cpu_top module."""
    
    # Top-level signals
    clk: SimHandleBase
    rst_n: SimHandleBase
    
    # Sub-modules with proper hierarchy
    u_cpu_complex: CpuComplex
    u_clock_gen: ClockGen
    u_csr_block: CsrBlock

class CpuComplex(HierarchyObject):
    """Type stub for cpu_complex sub-module."""
    
    # Module signals
    enable: SimHandleBase
    ready: SimHandleBase
    
    # Nested sub-modules
    u_dm_arbiter: DmArbiter
    u_if_arbiter: IfArbiter
```

## Signal Analysis

The generator categorizes signals by function:
- **Clock/Reset**: System timing and control
- **AXI Interface**: Memory and instruction fetch
- **APB Interface**: Configuration registers
- **Debug Interface**: Development and debugging
- **Performance Counters**: Monitoring and profiling
- **Interrupts**: System event handling

## Requirements

- Python 3.8+
- cocotb 2.0+
- icarus verilog
- copra

**Note**: This example requires more simulation time due to design complexity.

