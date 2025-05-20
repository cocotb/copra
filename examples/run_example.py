"""Example usage of the copra stub generator."""

import os
import sys
from pathlib import Path

# Add the parent directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from cocotb.runner import get_runner
from copra.stubgen import discover_hierarchy, generate_stub


def main():
    """Run the example."""
    # Get the runner for the simulator (using iverilog)
    runner = get_runner("icarus")
    
    # Path to the minimal example
    minimal_dir = Path(__file__).parent / "minimal"
    
    # For this example, we'll skip the actual build since we're using a mock DUT
    print("Skipping actual simulation build for this example...")
    
    # In a real implementation, you would run the simulation like this:
    # runner.build(
    #     verilog_sources=[str(minimal_dir / "minimal.sv")],
    #     hdl_toplevel="minimal",
    #     build_dir=str(minimal_dir / "sim_build"),
    #     always=True,
    # )
    
    # For demonstration, we'll use a mock DUT since we don't have a real simulation
    print("Using mock DUT for demonstration (would use real simulation in production)")
    
    # Create a mock DUT with the expected structure
    class MockDUT:
        def __init__(self):
            self._name = "minimal"
            self.clk = MockHandle("clk", ModifiableObject)
            self.rst_n = MockHandle("rst_n", ModifiableObject)
            self.data_in = MockHandle("data_in", ModifiableObject)
            self.data_out = MockHandle("data_out", ModifiableObject)
            self._sub_handles = {
                "clk": self.clk,
                "rst_n": self.rst_n,
                "data_in": self.data_in,
                "data_out": self.data_out,
            }
    
    class MockHandle:
        def __init__(self, name, handle_type):
            self._name = name
            self._type = handle_type
    
    # Import the handle types after the mock is defined
    from cocotb.handle import HierarchyObject, ModifiableObject
    
    # Generate the stub
    mock_dut = MockDUT()
    mock_dut._type = HierarchyObject  # Set the type for the root DUT
    hierarchy = discover_hierarchy(mock_dut)
    stub_content = generate_stub(hierarchy)
    
    # Write the stub to a file
    output_file = minimal_dir / "dut.pyi"
    output_file.write_text(stub_content)
    print(f"Generated stub file: {output_file}")
    print("\nGenerated stub content:")
    print("-" * 80)
    print(stub_content)
    print("-" * 80)
    print("\nTo use these stubs in your testbench, add the following import:")
    print(f"from {minimal_dir.name}.dut import *")


if __name__ == "__main__":
    main()
