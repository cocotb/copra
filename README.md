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

First, clone the repository and set up a virtual environment:

```bash
# Clone the repository
git clone https://github.com/cocotb/copra.git
cd copra

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install the package in development mode
pip install -e .
```

### Dependencies

The project requires:
- Python 3.8+
- cocotb 1.8.0 or later
- Icarus Verilog (or another cocotb-compatible simulator)
- pytest for running tests
- Sphinx for building documentation (optional)

Install development dependencies:

```bash
pip install -e .[dev,test,docs]
```

## Quick Start

### Running the Example

The `examples/minimal` directory contains a working example. To run it:

```bash
# Navigate to the example
cd examples/minimal

# Clean any previous builds
make clean

# Run the example
make
```

This will:
1. Compile the Verilog DUT
2. Run the cocotb testbench
3. Show the test results

### Expected Output

```
** TEST                          STATUS  SIM TIME (ns)  REAL TIME (s)  RATIO (ns/s) **
** test_minimal.test_minimal      PASS          90.00           0.00      63959.94  **
** TESTS=1 PASS=1 FAIL=0 SKIP=0                 90.00           0.41        219.23  **
```

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
- Example testbench with a simple DUT
- Test suite with pytest
- End-to-end example in `examples/minimal`
- Basic documentation structure

### What's coming:
- Integration with cocotb simulation
- Support for real DUT introspection
- Complete type stub generation
- Array and complex type support
- Documentation and examples

## Development

### Running Tests

To run the test suite:

```bash
# Install test dependencies if not already installed
pip install -e .[test]

# Run all tests
pytest tests/ -v

# Run a specific test file
pytest tests/test_stubgen.py -v

# Run with coverage report
pytest --cov=copra tests/
```

### Testing with Different Simulators

By default, the tests use Icarus Verilog. To use a different simulator, set the `SIM` environment variable:

```bash
# For VCS
SIM=vcs pytest tests/ -v

# For Verilator
SIM=verilator pytest tests/ -v
```

### Examples

The `examples/` directory contains working examples. Here's how to run them:

```bash
# Navigate to the minimal example
cd examples/minimal

# Clean any previous builds
make clean

# Run the example test
make

# To see the generated VCD waveform (if enabled in the Makefile)
gtkwave dump.vcd
```

### Building Documentation

To build the documentation locally:

```bash
# Install documentation dependencies
pip install -e .[docs]

# Build the documentation
cd docs
make html

# Open the documentation in your default browser
open _build/html/index.html


## License

BSD-3-Clause (same as cocotb)