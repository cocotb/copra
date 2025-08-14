# Copra Examples

Examples demonstrating type stub generation for HDL designs.

## Running Examples

```bash
SIM=verilator uv run make

cd simple_dff && make # for a usual flow
# or
cd simple_dff && make gen_stubs # for a standalone flow (only stubs)
```

## Examples

- **simple_dff**: D flip-flop with logic signals
- **adder**: Parameterized adder with generate blocks  
- **multi_dim_array**: Multi-dimensional arrays
- **matrix_multiplier**: Matrix multiplier with parameters

## Usage

1. Add `copra.integration.autostub` to `COCOTB_TEST_MODULES` in your Makefile:
   ```makefile
   COCOTB_TEST_MODULES = copra.integration.autostub,your_test_module
   ```
2. Run cocotb tests - stubs generated automatically
3. Configure IDE to use generated stubs

Check generated `dut.pyi` files to see signal mappings.

