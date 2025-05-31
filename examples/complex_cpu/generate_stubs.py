#!/usr/bin/env python3
"""Generate type stubs for the complex CPU design using copra.

This script demonstrates copra's advanced capabilities with a large, complex design
using real simulation-based hierarchy discovery and advanced generation features.
"""

import sys
from pathlib import Path

# Add copra to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from copra import (
    DocumentationGenerator,
    StubGenerationOptions,
    StubGenerator,
    create_stub_from_dut,
    discover_hierarchy,
    generate_stub,
    generate_testbench_template,
    run_discovery_simulation,
)


def generate_cpu_stubs():
    """Generate type stubs for the complex CPU design using advanced copra features."""
    print("=" * 60)
    print("Complex CPU Example: Advanced Stub Generation")
    print("=" * 60)

    # Define source files
    base_dir = Path(__file__).parent
    verilog_sources = [
        str(base_dir / "cpu_top.sv"),
        str(base_dir / "clock_gen.sv"),
        str(base_dir / "cpu_complex.sv"),
        str(base_dir / "cpu_core.sv"),
        str(base_dir / "pipeline_stages.sv"),
        str(base_dir / "support_modules.sv"),
    ]
    
    print("Source files:")
    for src in verilog_sources:
        print(f"  - {src}")
    
    print("\nTop module: cpu_top")
    print("Target simulator: icarus")

    try:
        print("\n" + "=" * 40)
        print("Step 1: Running DUT Discovery Simulation")
        print("=" * 40)

        # Run discovery simulation to get the real DUT
        dut = run_discovery_simulation(
            top_module="cpu_top",
            verilog_sources=verilog_sources,
            simulator="icarus",
            cleanup=True
        )

        print(f"✓ Successfully discovered DUT: {dut._name}")

        print("\n" + "=" * 40)
        print("Step 2: Advanced Hierarchy Discovery")
        print("=" * 40)

        # Discover the hierarchy with enhanced options
        hierarchy = discover_hierarchy(
            dut,
            max_depth=10,  # Allow deeper hierarchy discovery
            include_constants=True,
            performance_mode=False,  # Use full discovery for complex designs
            array_detection=True,
            extract_metadata=True
        )
        
        print(f"✓ Discovered {len(hierarchy)} signals/modules in hierarchy")
        
        # Enhanced hierarchy analysis
        print("\nDetailed hierarchy analysis:")
        _analyze_hierarchy_structure(hierarchy)

        print("\n" + "=" * 40)
        print("Step 3: Advanced Stub Generation")
        print("=" * 40)

        # Generate stubs with advanced options
        print("Generating nested hierarchy stubs...")
        nested_options = StubGenerationOptions(
            flat_hierarchy=False,  # Use nested hierarchy for better organization
            include_metadata=True,
            include_arrays=True,
            include_docstrings=True,
            typing_style="modern",
            class_prefix="",
            class_suffix="",
            output_format="pyi",
        )

        nested_generator = StubGenerator(nested_options)
        nested_stub_content = nested_generator.generate_stub(hierarchy, "cpu_top")

        # Write nested hierarchy stub
        nested_stub_file = base_dir / "cpu_top.pyi"
        with open(nested_stub_file, "w") as f:
            f.write(nested_stub_content)

        print(f"✓ Generated nested stub file: {nested_stub_file}")
        print(f"  Stub size: {len(nested_stub_content)} characters")
        print(f"  Lines: {len(nested_stub_content.splitlines())}")

        # Generate flat hierarchy version for comparison
        print("\nGenerating flat hierarchy stubs...")
        flat_options = StubGenerationOptions(
            flat_hierarchy=True,  # Flat for comparison
            include_metadata=True,
            include_arrays=True,
            include_docstrings=True,
            typing_style="modern",
            class_prefix="",
            class_suffix="",
            output_format="pyi",
        )

        flat_generator = StubGenerator(flat_options)
        flat_stub_content = flat_generator.generate_stub(hierarchy, "cpu_top")

        flat_stub_file = base_dir / "cpu_top_flat.pyi"
        with open(flat_stub_file, "w") as f:
            f.write(flat_stub_content)

        print(f"✓ Generated flat stub file: {flat_stub_file}")

        # Generate Python module format
        print("\nGenerating Python types module...")
        py_options = StubGenerationOptions(
            flat_hierarchy=True,
            include_metadata=True,
            include_arrays=True,
            include_docstrings=True,
            typing_style="modern",
            class_prefix="",
            class_suffix="",
            output_format="py",
        )

        py_generator = StubGenerator(py_options)
        py_content = py_generator.generate_stub(hierarchy, "cpu_top")

        py_file = base_dir / "cpu_top_types.py"
        with open(py_file, "w") as f:
            f.write(py_content)

        print(f"✓ Generated Python types module: {py_file}")

        print("\n" + "=" * 40)
        print("Step 4: Advanced Documentation Generation")
        print("=" * 40)

        # Generate multiple documentation formats
        print("Generating Markdown documentation...")
        md_generator = DocumentationGenerator("markdown")
        md_content = md_generator.generate_interface_documentation(
            hierarchy, str(base_dir / "cpu_top_interface.md")
        )
        print(f"✓ Generated Markdown documentation: cpu_top_interface.md")

        print("Generating HTML documentation...")
        html_generator = DocumentationGenerator("html")
        html_content = html_generator.generate_interface_documentation(
            hierarchy, str(base_dir / "cpu_top_interface.html")
        )
        print(f"✓ Generated HTML documentation: cpu_top_interface.html")

        print("Generating RST documentation...")
        rst_generator = DocumentationGenerator("rst")
        rst_content = rst_generator.generate_interface_documentation(
            hierarchy, str(base_dir / "cpu_top_interface.rst")
        )
        print(f"✓ Generated RST documentation: cpu_top_interface.rst")

        print("\n" + "=" * 40)
        print("Step 5: Testbench Template Generation")
        print("=" * 40)

        # Generate comprehensive testbench template
        print("Generating comprehensive testbench template...")
        testbench_content = generate_testbench_template(
            hierarchy, str(base_dir / "test_cpu_generated.py")
        )

        print(f"✓ Generated testbench template: test_cpu_generated.py")
        print(f"  Template size: {len(testbench_content)} characters")

        print("\n" + "=" * 40)
        print("Step 6: CPU-Specific Analysis")
        print("=" * 40)

        # Enhanced CPU-specific analysis
        _perform_cpu_analysis(hierarchy)

        print("\n" + "=" * 40)
        print("Step 7: Validation and Preview")
        print("=" * 40)

        # Show preview of the advanced generated content
        lines = nested_stub_content.splitlines()
        print("Advanced stub preview (first 25 lines):")
        print("-" * 50)
        for i, line in enumerate(lines[:25], 1):
            print(f"{i:2d}: {line}")
        if len(lines) > 25:
            print(f"... and {len(lines) - 25} more lines")
        print("-" * 50)

        print("\n" + "=" * 40)
        print("Generation Summary")
        print("=" * 40)

        print("Generated files:")
        generated_files = [
            ("cpu_top.pyi", "Nested hierarchy type stubs"),
            ("cpu_top_flat.pyi", "Flat hierarchy type stubs"),
            ("cpu_top_types.py", "Python types module"),
            ("cpu_top_interface.md", "Markdown documentation"),
            ("cpu_top_interface.html", "HTML documentation"),
            ("cpu_top_interface.rst", "RST documentation"),
            ("test_cpu_generated.py", "Comprehensive testbench template"),
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
        print("✓ Advanced CPU stub generation completed successfully!")
        print("=" * 40)

        print("\nAdvanced features demonstrated:")
        print("1. ✓ Nested vs flat hierarchy generation")
        print("2. ✓ Multiple output formats (pyi, py)")
        print("3. ✓ Multiple documentation formats (md, html, rst)")
        print("4. ✓ Comprehensive testbench template generation")
        print("5. ✓ Enhanced hierarchy analysis and metadata extraction")
        print("6. ✓ Configurable stub generation options")

        print("\nNext steps:")
        print("1. Run 'make test' to execute the testbench with type checking")
        print("2. Open cpu_top.pyi in your IDE to see advanced autocompletion")
        print("3. View cpu_top_interface.html in a browser for rich documentation")
        print("4. Use test_cpu_generated.py as a starting point for comprehensive tests")
        print("5. Compare nested vs flat stub approaches for your use case")

        return nested_stub_content

    except Exception as e:
        print(f"✗ Error during advanced stub generation: {e}")
        print("\nFallback: Generating basic CPU stubs without advanced features")
        
        # Fallback to basic stub generation
        basic_stub = """# Basic type stub for complex CPU example
# Generated by copra (fallback mode)

from cocotb.handle import HierarchyObject, SimHandleBase

class CpuTopType(HierarchyObject):
    \"\"\"Complex CPU Top-Level Module.
    
    A sophisticated CPU design with multiple pipeline stages,
    memory interfaces, and control logic.
    
    Signals:
        clk: System clock
        rst_n: Active-low reset
        
    Sub-modules:
        u_cpu_complex: Main CPU complex
        u_clock_gen: Clock generation unit
        u_csr_block: Control and status registers
    \"\"\"
    
    # Clock and reset
    clk: SimHandleBase
    rst_n: SimHandleBase
    
    # Sub-modules (would be discovered from real simulation)
    u_cpu_complex: HierarchyObject
    u_clock_gen: HierarchyObject
    u_csr_block: HierarchyObject

# Type alias for the main DUT
DutType = CpuTopType
"""
        
        stub_file = base_dir / "cpu_top.pyi"
        with open(stub_file, "w") as f:
            f.write(basic_stub)
        
        print(f"✓ Generated basic CPU stub file: {stub_file}")
        return basic_stub


def _analyze_hierarchy_structure(hierarchy):
    """Perform detailed analysis of the hierarchy structure."""
    # Analyze hierarchy depth and structure
    depth_counts = {}
    max_depth = 0
    module_structure = {}
    
    for path in hierarchy.keys():
        depth = path.count(".")
        depth_counts[depth] = depth_counts.get(depth, 0) + 1
        max_depth = max(max_depth, depth)
        
        # Analyze module structure
        if depth == 0:
            module_structure["top_level"] = module_structure.get("top_level", 0) + 1
        elif depth == 1:
            module_name = path.split('.')[0]
            module_structure[module_name] = module_structure.get(module_name, 0) + 1
    
    print(f"  Maximum hierarchy depth: {max_depth}")
    print("  Depth distribution:")
    for depth in sorted(depth_counts.keys()):
        print(f"    Level {depth}: {depth_counts[depth]} signals/modules")
    
    print("  Module structure:")
    for module, count in sorted(module_structure.items()):
        if module != "top_level":
            print(f"    {module}: {count} signals")
    
    # Find array-like structures
    array_patterns = [path for path in hierarchy.keys() if "[" in path and "]" in path]
    print(f"  Array-like structures: {len(array_patterns)}")
    
    if array_patterns:
        print("  Sample arrays:")
        for array_path in sorted(array_patterns)[:5]:
            print(f"    {array_path}")


def _perform_cpu_analysis(hierarchy):
    """Perform CPU-specific analysis of the hierarchy."""
    # Categorize signals by function
    categories = {
        "clock_reset": [],
        "axi_interface": [],
        "apb_interface": [],
        "debug_interface": [],
        "performance_counters": [],
        "control_status": [],
        "interrupts": [],
        "other": []
    }
    
    for path in hierarchy.keys():
        path_lower = path.lower()
        signal_name = path.split('.')[-1].lower()
        
        # Categorize signals
        if any(term in signal_name for term in ['clk', 'rst', 'reset']):
            categories["clock_reset"].append(path)
        elif 'axi' in signal_name:
            categories["axi_interface"].append(path)
        elif 'apb' in signal_name:
            categories["apb_interface"].append(path)
        elif 'debug' in signal_name:
            categories["debug_interface"].append(path)
        elif 'perf' in signal_name or 'count' in signal_name:
            categories["performance_counters"].append(path)
        elif any(term in signal_name for term in ['enable', 'active', 'ready', 'error']):
            categories["control_status"].append(path)
        elif 'interrupt' in signal_name:
            categories["interrupts"].append(path)
        else:
            categories["other"].append(path)
    
    print("CPU Design Analysis by Function:")
    for category, signals in categories.items():
        if signals:
            print(f"  {category.replace('_', ' ').title()}: {len(signals)} signals")
            # Show a few examples
            for signal in sorted(signals)[:3]:
                print(f"    - {signal}")
            if len(signals) > 3:
                print(f"    ... and {len(signals) - 3} more")
    
    # Analyze interface completeness
    print("\nInterface Completeness Analysis:")
    
    # AXI interface analysis
    axi_dm_signals = [s for s in categories["axi_interface"] if "dm" in s]
    axi_if_signals = [s for s in categories["axi_interface"] if "if" in s]
    print(f"  AXI Data Memory Interface: {len(axi_dm_signals)} signals")
    print(f"  AXI Instruction Fetch Interface: {len(axi_if_signals)} signals")
    
    # APB interface analysis
    apb_signals = categories["apb_interface"]
    print(f"  APB Configuration Interface: {len(apb_signals)} signals")
    
    # Performance monitoring
    perf_signals = categories["performance_counters"]
    print(f"  Performance Monitoring: {len(perf_signals)} counters")


if __name__ == "__main__":
    generate_cpu_stubs()
