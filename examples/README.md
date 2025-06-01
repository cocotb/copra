# copra Examples

Examples demonstrating copra's comprehensive capabilities for generating Python type stubs for cocotb testbenches.

## Examples

- **[minimal/](minimal/)** - Simple 8-bit module showing core features
- **[simple_dff/](simple_dff/)** - D flip-flop with signal analysis
- **[complex_cpu/](complex_cpu/)** - Multi-core CPU with deep hierarchy

## Features Demonstrated

Each example shows the complete copra feature set:

1. **Hierarchical Stub Generation** - Proper module structure representation
2. **Multiple Output Formats** - `.pyi` stubs and `.py` runtime modules  
3. **Documentation Generation** - Markdown, HTML, and RST formats
4. **Testbench Templates** - Auto-generated test scaffolding
5. **Enhanced Analysis** - Signal categorization and validation
6. **Configurable Options** - Customizable generation parameters

## Quick Start

```bash
cd examples/simple_dff
python generate_stubs.py  # Generates all outputs
make                      # Run tests with type checking
```

**Generated files:**
- `dut.pyi` - Hierarchical type stubs
- `dut_runtime.pyi` - Runtime type module
- `*_interface.{md,html,rst}` - Documentation
- `test_*_generated.py` - Testbench template

## Usage Example

```python
import cocotb
from typing import cast
from dut import DutType  # Generated type stub

@cocotb.test()
async def test_with_types(dut):
    typed_dut = cast(DutType, dut)  # Full IDE support
    typed_dut.clk.value = 0        # Autocompletion
    # ... rest of test
```

See individual example directories for detailed information.
