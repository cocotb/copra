# copra

> [Copra](https://www.britannica.com/topic/copra) is the kernel, edible of the fruit of the coconut palm. 

As copra is the essential core of a coconut, this tool extracts the crucial typing information from your cocotb testbenches, enhancing their functionality and reliability.

## ⚠️ Work in Progress ⚠️

**This project is currently in early development and is not yet functional.** The current implementation is a proof-of-concept and is not ready for production use. The API and functionality are subject to significant changes.

## Copra

<!-- [![PyPI](https://img.shields.io/pypi/v/cocotb-copra)](https://pypi.org/project/cocotb-copra/)
[![License](https://img.shields.io/pypi/l/cocotb-copra)](LICENSE)
[![Python](https://img.shields.io/pypi/pyversions/cocotb-copra)](pyproject.toml)
[![Status: WIP](https://img.shields.io/badge/status-WIP-yellow)](https://github.com/cocotb/copra) -->

Copra is an experimental Python package that aims to generate type stubs for [cocotb](https://github.com/cocotb/cocotb) testbenches. Once complete, it will provide better IDE support and type checking for your verification code.

## Features

- 🚀 Generate Python type stubs from Verilog/SystemVerilog DUTs
- 🧩 Supports both scalar and array ports
- 🎯 Improves IDE autocompletion and type checking
- ⚡ Works with any cocotb-compatible simulator
- 🔍 Discovers DUT hierarchy automatically
- Integrates with mypy and other type checkers

## Installation

```bash
pip install copra
```

For development:

```bash
git clone https://github.com/yourusername/copra.git
cd copra
pip install -e .[dev]
```

## Quick Start (Planned Functionality)

> ⚠️ **Note**: The functionality described below is planned but not yet implemented.

1: Install cocotb:

```bash
pip install cocotb
```

Install copra (from source):

```bash
git clone https://github.com/cocotb/copra.git
cd copra
python -m venv .env && source .env/bin/activate
pip install -r requirements.txt
pip install -e .[dev]
```

> 1x: Install copra and cocotb (when in pypi):
> ```bash
> pip install copra cocotb
>  ```

2. Generate stubs for your DUT:

```bash
copra your_top_module --outfile dut.pyi
```

3. Use the generated stubs in your testbench:

```python
from dut import *  # Import the generated stubs
import cocotb
from cocotb.clock import Clock

@cocotb.test()
async def test_my_design(dut: dut):  # Type hints will work!
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    
    dut.rst_n.value = 0
    await cocotb.triggers.Timer(100, units="ns")
    dut.rst_n.value = 1
    
    # Your test code here
```

## Current Status

### What works:
- Basic DUT hierarchy discovery (in tests)
- Simple stub generation for mock DUTs
- Basic command-line interface (non-functional for real DUTs)

### What's coming:
- Integration with cocotb simulation
- Support for real DUT introspection
- Complete type stub generation
- Array and complex type support
- Documentation and examples

## Development

### Running Tests

```bash
pytest tests/
```

### Building Documentation

```bash
cd docs
make html
```

## License

BSD-3-Clause (same as cocotb)