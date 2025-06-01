#!/usr/bin/env python3
"""Generate type stubs for the minimal example DUT.

This script demonstrates how to use copra to generate type stubs
for a simple DUT by running an actual cocotb simulation and showcasing
the complete feature set of copra even for minimal designs.
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


def generate_minimal_stubs():
    """Generate type stubs for the minimal example DUT using comprehensive copra features."""
    print("=" * 60)
    print("Minimal Example: Comprehensive Stub Generation")
    print("=" * 60)

    # Define source files
    base_dir = Path(__file__).parent
    verilog_sources = [str(base_dir / "minimal.sv")]

    print("Source files:")
    for src in verilog_sources:
        print(f"  - {src}")

    print("\nTop module: minimal")
    print("Target simulator: icarus")

    try:
        print("\n" + "=" * 40)
        print("Step 1: Running DUT Discovery Simulation")
        print("=" * 40)

        # Run discovery simulation to get the real DUT
        dut = run_discovery_simulation(
            top_module="minimal",
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

        # Generate hierarchical stubs (even for minimal designs)
        print("Generating hierarchical stubs...")
        hierarchical_options = StubGenerationOptions(
            flat_hierarchy=False,  # Use hierarchical even for minimal designs
            include_metadata=True,
            include_arrays=True,
            include_docstrings=True,
            typing_style="modern",
            class_prefix="",
            class_suffix="",
            output_format="pyi",
        )

        hierarchical_generator = StubGenerator(hierarchical_options)
        hierarchical_stub_content = hierarchical_generator.generate_stub(hierarchy, "minimal")

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
        runtime_content = runtime_generator.generate_stub(hierarchy, "minimal")

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
            hierarchy, str(base_dir / "minimal_interface.md")
        )
        print("✓ Generated Markdown documentation: minimal_interface.md")

        print("Generating HTML documentation...")
        html_generator = DocumentationGenerator("html")
        html_generator.generate_interface_documentation(
            hierarchy, str(base_dir / "minimal_interface.html")
        )
        print("✓ Generated HTML documentation: minimal_interface.html")

        print("Generating RST documentation...")
        rst_generator = DocumentationGenerator("rst")
        rst_generator.generate_interface_documentation(
            hierarchy, str(base_dir / "minimal_interface.rst")
        )
        print("✓ Generated RST documentation: minimal_interface.rst")

        print("\n" + "=" * 40)
        print("Step 5: Testbench Template Generation")
        print("=" * 40)

        # Generate comprehensive testbench template
        print("Generating testbench template...")
        testbench_content = generate_testbench_template(
            hierarchy, str(base_dir / "test_minimal_generated.py")
        )

        print("✓ Generated testbench template: test_minimal_generated.py")
        print(f"  Template size: {len(testbench_content)} characters")

        print("\n" + "=" * 40)
        print("Step 6: Minimal Design Analysis")
        print("=" * 40)

        # Analyze the minimal design signals
        expected_signals = ['clk', 'rst_n', 'data_in', 'data_out']
        found_signals = []

        for path in hierarchy.keys():
            signal_name = path.split('.')[-1]  # Get the last part of the path
            if signal_name in expected_signals:
                found_signals.append(signal_name)

        print("Minimal Design Signal Analysis:")
        for signal in expected_signals:
            status = "✓ Found" if signal in found_signals else "✗ Missing"
            print(f"  {signal}: {status}")

        if len(found_signals) == len(expected_signals):
            print("✓ All expected minimal design signals discovered!")
        else:
            print(f"⚠ Found {len(found_signals)}/{len(expected_signals)} expected signals")

        # Enhanced design analysis
        print("\nDesign Functionality Analysis:")

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
        data_signals = [s for s in hierarchy.keys() if 'data' in s.lower()]
        print(f"  Data path signals: {len(data_signals)}")
        for data in data_signals:
            print(f"    - {data}")

        # Interface completeness analysis
        print("\nInterface Analysis:")
        all_signals = list(hierarchy.keys())
        input_signals = [s for s in all_signals if any(inp in s.lower()
                                                       for inp in ['in', 'input', 'clk', 'rst'])]
        output_signals = [s for s in all_signals if any(out in s.lower()
                                                        for out in ['out', 'output'])]

        print(f"  Potential input signals: {len(input_signals)}")
        for inp in input_signals:
            print(f"    - {inp}")

        print(f"  Potential output signals: {len(output_signals)}")
        for out in output_signals:
            print(f"    - {out}")

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
            ("minimal_interface.md", "Markdown documentation"),
            ("minimal_interface.html", "HTML documentation"),
            ("minimal_interface.rst", "RST documentation"),
            ("test_minimal_generated.py", "Testbench template"),
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
        print("✓ Comprehensive minimal stub generation completed!")
        print("=" * 40)

        print("\nComprehensive features demonstrated:")
        print("1. ✓ Hierarchical stub generation (even for minimal designs)")
        print("2. ✓ Multiple output formats (pyi, py)")
        print("3. ✓ Multiple documentation formats (md, html, rst)")
        print("4. ✓ Testbench template generation")
        print("5. ✓ Enhanced hierarchy analysis and metadata extraction")
        print("6. ✓ Design-specific signal analysis and validation")
        print("7. ✓ Interface completeness analysis")
        print("8. ✓ Configurable stub generation options")

        print("\nNext steps:")
        print("1. Run 'make test' to execute the testbench with type checking")
        print("2. Open dut.pyi in your IDE to see hierarchical autocompletion")
        print("3. View minimal_interface.html in a browser for rich documentation")
        print("4. Use test_minimal_generated.py as a starting point for comprehensive tests")
        print("5. Compare hierarchical vs runtime stub approaches")
        print("6. Explore different documentation formats for your needs")

        return hierarchical_stub_content

    except Exception as e:
        print(f"✗ Error during stub generation: {e}")
        print("\nFallback: Generating basic stubs without simulation")

        # Fallback to basic stub generation
        basic_stub = """# Basic type stub for minimal example
# Generated by copra (fallback mode)

from cocotb.handle import HierarchyObject, SimHandleBase

class Minimal(HierarchyObject):
    \"\"\"Minimal example DUT.

    A simple design demonstrating basic copra capabilities.

    Signals:
        clk: Clock input
        rst_n: Active-low reset
        data_in: 8-bit data input
        data_out: 8-bit data output
    \"\"\"

    clk: SimHandleBase
    rst_n: SimHandleBase
    data_in: SimHandleBase
    data_out: SimHandleBase

# Type alias for the main DUT
DutType = Minimal
"""

        stub_file = base_dir / "dut.pyi"
        with open(stub_file, "w") as f:
            f.write(basic_stub)

        print(f"✓ Generated basic stub file: {stub_file}")
        return basic_stub


if __name__ == "__main__":
    generate_minimal_stubs()
