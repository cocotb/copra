# Copra - Type Stubs for Cocotb

Generates type stubs for HDL designs to enable IDE autocomplete in cocotb testbenches.

## Quick Start

1. Add copra to your test dependencies
2. Add copra to your Makefile:
   ```makefile
   COCOTB_TEST_MODULES = copra.integration.autostub,your_test_module
   ```
3. Run your cocotb tests - stubs generated in `copra_stubs.pyi`

## Configuration

You can configure how copra works by setting environment variables:

| Variable name          | Description                                                         | Default           |
|------------------------|---------------------------------------------------------------------|-------------------|
| `COPRA_STUB_DIRECTORY` | Directory to save stub file to                                      | `.`               |
| `COPRA_STUB_FILENAME`  | Filename of file to store stubs in. Stub files should end in `.pyi` | `copra_stubs.pyi` |
| `COPRA_MAX_DEPTH`      | Maximum recursion depth of type discovery.                          | `100`             |


## How it Works

Copra introspects the live cocotb hierarchy and maps HDL signals to cocotb handle types:

- Single logic → `LogicObject`
- Logic arrays → `LogicArrayObject`  
- Unpacked arrays → `ArrayObject[...]`
- Generate blocks → `HierarchyArrayObject[...]`
- Modules → `HierarchyObject`
- Parameters → `IntegerObject`

See examples directory.
