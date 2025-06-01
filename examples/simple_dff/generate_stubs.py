#!/usr/bin/env python3
"""Generate type stubs for the simple DFF example DUT.

This script demonstrates how to use copra to generate type stubs
for a D flip-flop by running an actual cocotb simulation and showcasing
copra's comprehensive features even for simple designs.
"""

import sys
from pathlib import Path

# Add copra to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from copra import (
    DocumentationGenerator,
    StubGenerationOptions,
    StubGenerator,
    discover_hierarchy,
    generate_testbench_template,
    run_discovery_simulation,
)


def generate_dff_stubs():
    """Generate type stubs for the DFF example DUT using comprehensive copra features."""
    print("=" * 60)
    print("Simple DFF Example: Comprehensive Stub Generation")
    print("=" * 60)

    # Define source files
    base_dir = Path(__file__).parent
    verilog_sources = [str(base_dir / "dff.sv")]

    print("Source files:")
    for src in verilog_sources:
        print(f"  - {src}")

    print("\nTop module: dff")
    print("Target simulator: icarus")

    try:
        print("\n" + "=" * 40)
        print("Step 1: Running DUT Discovery Simulation")
        print("=" * 40)

        # Run discovery simulation to get the real DUT
        dut = run_discovery_simulation(
            top_module="dff",
            verilog_sources=verilog_sources,
            simulator="icarus",
            cleanup=True
        )

        print(f"✓ Successfully discovered DUT: {dut._name}")

        print("\n" + "=" * 40)
        print("Step 2: Enhanced Hierarchy Discovery")
        print("=" * 40)

        # Discover the hierarchy with enhanced options
        hierarchy = discover_hierarchy(
            dut,
            max_depth=5,
            include_constants=True,
            performance_mode=False,
            array_detection=True,
            extract_metadata=True
        )

        print(f"✓ Discovered {len(hierarchy)} signals/modules in hierarchy")

        # Print detailed hierarchy information
        print("\nHierarchy overview:")
        for path, obj_type in sorted(hierarchy.items()):
            # Safe way to get type name
            if hasattr(obj_type, '__name__'):
                type_name = obj_type.__name__
            elif hasattr(obj_type, '__class__'):
                type_name = obj_type.__class__.__name__
            else:
                type_name = str(type(obj_type).__name__)
            print(f"  {path}: {type_name}")

        print("\n" + "=" * 40)
        print("Step 3: Advanced Stub Generation")
        print("=" * 40)

        # Generate hierarchical stubs (even for simple designs)
        print("Generating hierarchical stubs...")
        hierarchical_options = StubGenerationOptions(
            flat_hierarchy=False,  # Use hierarchical even for simple designs
            include_metadata=True,
            include_arrays=True,
            include_docstrings=True,
            typing_style="modern",
            class_prefix="",
            class_suffix="",
            output_format="pyi",
        )

        hierarchical_generator = StubGenerator(hierarchical_options)
        hierarchical_stub_content = hierarchical_generator.generate_stub(hierarchy, "dff")

        # Write hierarchical stub
        hierarchical_stub_file = base_dir / "dut.pyi"
        with open(hierarchical_stub_file, "w") as f:
            f.write(hierarchical_stub_content)

        print(f"✓ Generated hierarchical stub file: {hierarchical_stub_file}")
        print(f"  Stub size: {len(hierarchical_stub_content)} characters")
        print(f"  Lines: {len(hierarchical_stub_content.splitlines())}")

        # Generate Python runtime module for comparison
        print("\nGenerating Python runtime module...")
        runtime_options = StubGenerationOptions(
            flat_hierarchy=True,
            include_metadata=True,
            include_arrays=True,
            include_docstrings=True,
            typing_style="modern",
            class_prefix="",
            class_suffix="",
            output_format="py",
        )

        runtime_generator = StubGenerator(runtime_options)
        runtime_content = runtime_generator.generate_stub(hierarchy, "dff")

        runtime_file = base_dir / "dut_runtime.pyi"
        with open(runtime_file, "w") as f:
            f.write(runtime_content)

        print(f"✓ Generated runtime module: {runtime_file}")

        print("\n" + "=" * 40)
        print("Step 4: Documentation Generation")
        print("=" * 40)

        # Generate documentation in multiple formats
        print("Generating Markdown documentation...")
        md_generator = DocumentationGenerator("markdown")
        md_generator.generate_interface_documentation(
            hierarchy, str(base_dir / "dff_interface.md")
        )
        print("✓ Generated Markdown documentation: dff_interface.md")

        print("Generating HTML documentation...")
        html_generator = DocumentationGenerator("html")
        html_generator.generate_interface_documentation(
            hierarchy, str(base_dir / "dff_interface.html")
        )
        print("✓ Generated HTML documentation: dff_interface.html")

        print("\n" + "=" * 40)
        print("Step 5: Testbench Template Generation")
        print("=" * 40)

        # Generate comprehensive testbench template
        print("Generating testbench template...")
        testbench_content = generate_testbench_template(
            hierarchy, str(base_dir / "test_dff_generated.py")
        )

        print("✓ Generated testbench template: test_dff_generated.py")
        print(f"  Template size: {len(testbench_content)} characters")

        print("\n" + "=" * 40)
        print("Step 6: DFF-Specific Analysis")
        print("=" * 40)

        # Analyze the DFF-specific signals
        expected_signals = ['clk', 'rst_n', 'd', 'q']
        found_signals = []

        for path in hierarchy.keys():
            signal_name = path.split('.')[-1]  # Get the last part of the path
            if signal_name in expected_signals:
                found_signals.append(signal_name)

        print("DFF Signal Analysis:")
        for signal in expected_signals:
            status = "✓ Found" if signal in found_signals else "✗ Missing"
            print(f"  {signal}: {status}")

        if len(found_signals) == len(expected_signals):
            print("✓ All expected DFF signals discovered!")
        else:
            print(f"⚠ Found {len(found_signals)}/{len(expected_signals)} expected signals")

        # Enhanced DFF functionality analysis
        print("\nDFF Functionality Analysis:")

        # Clock analysis
        clock_signals = [s for s in hierarchy.keys() if 'clk' in s.lower()]
        print(f"  Clock signals: {len(clock_signals)}")
        for clk in clock_signals:
            print(f"    - {clk}")

        # Reset analysis
        reset_signals = [s for s in hierarchy.keys() if 'rst' in s.lower() or 'reset' in s.lower()]
        print(f"  Reset signals: {len(reset_signals)}")
        for rst in reset_signals:
            print(f"    - {rst}")

        # Data path analysis
        data_signals = [s for s in hierarchy.keys() if s.split('.')[-1] in ['d', 'q']]
        print(f"  Data path signals: {len(data_signals)}")
        for data in data_signals:
            print(f"    - {data}")

        print("\n" + "=" * 40)
        print("Step 7: Validation and Preview")
        print("=" * 40)

        # Show preview of the generated content
        lines = hierarchical_stub_content.splitlines()
        print("Generated stub preview (first 20 lines):")
        print("-" * 50)
        for i, line in enumerate(lines[:20], 1):
            print(f"{i:2d}: {line}")
        if len(lines) > 20:
            print(f"... and {len(lines) - 20} more lines")
        print("-" * 50)

        print("\n" + "=" * 40)
        print("Generation Summary")
        print("=" * 40)

        print("Generated files:")
        generated_files = [
            ("dut.pyi", "Hierarchical type stubs"),
            ("dut_runtime.pyi", "Runtime type stubs"),
            ("dff_interface.md", "Markdown documentation"),
            ("dff_interface.html", "HTML documentation"),
            ("test_dff_generated.py", "Testbench template"),
        ]

        total_size = 0
        for filename, description in generated_files:
            filepath = base_dir / filename
            if filepath.exists():
                size = filepath.stat().st_size
                total_size += size
                print(f"  ✓ {filename} ({size:,} bytes) - {description}")
            else:
                print(f"  ✗ {filename} (not found) - {description}")

        print(f"\nTotal generated content: {total_size:,} bytes")

        print("\n" + "=" * 40)
        print("✓ Comprehensive DFF stub generation completed!")
        print("=" * 40)

        print("\nComprehensive features demonstrated:")
        print("1. ✓ Hierarchical stub generation (even for simple designs)")
        print("2. ✓ Multiple output formats (pyi, py)")
        print("3. ✓ Multiple documentation formats (md, html)")
        print("4. ✓ Testbench template generation")
        print("5. ✓ Enhanced hierarchy analysis and metadata extraction")
        print("6. ✓ DFF-specific signal analysis and validation")
        print("7. ✓ Configurable stub generation options")

        print("\nNext steps:")
        print("1. Run 'make test' to execute the testbench with type checking")
        print("2. Open dut.pyi in your IDE to see hierarchical autocompletion")
        print("3. View dff_interface.html in a browser for rich documentation")
        print("4. Use test_dff_generated.py as a starting point for comprehensive tests")
        print("5. Compare hierarchical vs runtime stub approaches")

        return hierarchical_stub_content

    except Exception as e:
        print(f"✗ Error during stub generation: {e}")
        print("\nFallback: Generating basic DFF stubs without simulation")

        # Fallback to basic stub generation for DFF
        basic_stub = """# Basic type stub for DFF example
# Generated by copra (fallback mode)

from cocotb.handle import HierarchyObject, SimHandleBase

class Dff(HierarchyObject):
    \"\"\"Simple D Flip-Flop DUT.

    A basic D flip-flop with clock and active-low reset.

    Signals:
        clk: Clock input
        rst_n: Active-low reset
        d: Data input
        q: Data output (registered)
    \"\"\"

    clk: SimHandleBase
    rst_n: SimHandleBase
    d: SimHandleBase
    q: SimHandleBase

# Type alias for the main DUT
DutType = Dff
"""

        stub_file = base_dir / "dut.pyi"
        with open(stub_file, "w") as f:
            f.write(basic_stub)

        print(f"✓ Generated basic DFF stub file: {stub_file}")
        return basic_stub


if __name__ == "__main__":
    generate_dff_stubs()
