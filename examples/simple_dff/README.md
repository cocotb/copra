# Simple D Flip-Flop Example

Demonstrates copra type stub generation for a D flip-flop module.

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

- `dff.sv` - D flip-flop module (clk, rst_n, d, q)
- `test_dff.py` - Cocotb testbench
- `generate_stubs.py` - Stub generator
- `dut.pyi` - Generated type stubs

## Requirements

- copra: `pip install copra`
- cocotb 2.0+
- Icarus Verilog 