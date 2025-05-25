# Minimal Example

Demonstrates basic copra type stub generation for a simple module.

## Usage

Generate type stubs:
```bash
python generate_stubs.py
```

Run the test:
```bash
make
```

## Files

- `minimal.sv` - Simple module (clk, rst_n, data_in, data_out)
- `test_minimal.py` - Cocotb testbench
- `generate_stubs.py` - Stub generator
- `dut.pyi` - Generated type stubs

## Requirements

- copra: `pip install copra`
- cocotb 2.0+
- Icarus Verilog

