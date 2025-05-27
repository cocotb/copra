#!/usr/bin/env python3
"""Generate type stubs for the simple DFF example DUT.

This script demonstrates how to use copra to generate type stubs
for a D flip-flop module within a self-contained example.
"""

from pathlib import Path

# Import copra as an installed library
from copra import generate_stub


# Mock the cocotb classes for demonstration purposes
# In a real scenario, these would come from the actual cocotb simulation
class MockType:
    """Mock base type for demonstration purposes."""

    def __init__(self, name):
        """Initialize mock type with a name."""
        self.__name__ = name


# Create mock handle types that match cocotb 2.0+ API
class HierarchyObject(MockType):
    """Mock HierarchyObject for demonstration purposes."""

    def __init__(self):
        """Initialize mock HierarchyObject."""
        super().__init__("HierarchyObject")


class LogicObject(MockType):
    """Mock LogicObject for demonstration purposes."""

    def __init__(self):
        """Initialize mock LogicObject."""
        super().__init__("LogicObject")


def generate_dff_stubs():
    """Generate type stubs for the simple DFF example DUT."""
    print("Generating type stubs for simple DFF example DUT...")

    # Define the hierarchy for our DFF DUT
    # This matches the dff.sv module interface:
    # - clk: input wire
    # - rst_n: input wire
    # - d: input wire
    # - q: output reg
    hierarchy = {
        'dff': HierarchyObject,
        'dff.clk': LogicObject,
        'dff.rst_n': LogicObject,
        'dff.d': LogicObject,
        'dff.q': LogicObject,
    }

    # Generate stub content
    stub_content = generate_stub(hierarchy)

    # Write to the dut.pyi file in this directory
    stub_file = Path(__file__).parent / "dut.pyi"
    with open(stub_file, "w") as f:
        f.write(stub_content)

    print(f"Generated stub file: {stub_file}")
    print(f"Stub file contains {len(stub_content.splitlines())} lines")

    # Show the generated content
    print("\nGenerated stub content:")
    print("-" * 50)
    print(stub_content)
    print("-" * 50)

    return stub_content

if __name__ == "__main__":
    generate_dff_stubs()
