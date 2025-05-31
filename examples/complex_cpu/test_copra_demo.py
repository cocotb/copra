#!/usr/bin/env python3
"""Demonstration of copra's capabilities with the complex CPU design.

This script shows what copra can do without requiring a full simulation run.
"""

import sys
from pathlib import Path

# Add copra to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


def demo_copra_capabilities():
    """Demonstrate copra's capabilities."""
    print("=" * 60)
    print("Complex CPU Design - copra Capabilities Demo")
    print("=" * 60)

    # Show the design files
    base_dir = Path(__file__).parent
    verilog_sources = [
        "cpu_top.sv",
        "clock_gen.sv",
        "cpu_complex.sv",
        "cpu_core.sv",
        "pipeline_stages.sv",
        "support_modules.sv",
    ]

    print("Design Overview:")
    print("================")

    total_lines = 0
    total_modules = 0

    for src in verilog_sources:
        filepath = base_dir / src
        if filepath.exists():
            with open(filepath) as f:
                content = f.read()
                lines = len(content.splitlines())
                modules = content.count("module ")
                total_lines += lines
                total_modules += modules
                print(f"  {src:20} - {lines:4} lines, {modules:2} modules")
        else:
            print(f"  {src:20} - NOT FOUND")

    print(f"\nTotal: {total_lines} lines of SystemVerilog, {total_modules} modules")

    print("\nDesign Features:")
    print("================")
    features = [
        "4-core CPU complex with individual clock gating",
        "Dual AXI4 master interfaces (instruction fetch and data memory)",
        "APB slave interface for control and status registers",
        "16 interrupt sources with handling logic",
        "Debug interface for register access",
        "Performance monitoring with comprehensive counters",
        "5-stage pipeline per core (IF, ID, EX, MEM, WB)",
        "Register files with debug access",
        "Round-robin arbiters for bus access",
        "Clock generation and power management",
    ]

    for i, feature in enumerate(features, 1):
        print(f"  {i:2}. {feature}")

    print("\nWhat copra would generate:")
    print("==========================")

    # Simulate what copra would discover and generate
    estimated_signals = [
        ("Top-level I/O signals", 50),
        ("Clock and reset signals", 20),
        ("AXI interface signals", 80),
        ("APB interface signals", 15),
        ("Internal core signals", 200),
        ("Performance counter signals", 30),
        ("Debug interface signals", 25),
        ("Array elements (registers, cores)", 150),
    ]

    total_estimated = sum(count for _, count in estimated_signals)

    print("Estimated signal discovery:")
    for category, count in estimated_signals:
        print(f"  {category:30} - ~{count:3} signals")
    print(f"  {'Total estimated signals':30} - ~{total_estimated:3} signals")

    print("\nGenerated files would include:")
    generated_files = [
        ("cpu_top.pyi", "Type stub for IDE autocompletion"),
        ("cpu_top_types.py", "Python module with type definitions"),
        ("cpu_top_interface.md", "Markdown documentation"),
        ("cpu_top_interface.html", "HTML documentation"),
        ("cpu_top_interface.rst", "reStructuredText documentation"),
        ("test_cpu_generated.py", "Auto-generated testbench template"),
    ]

    for filename, description in generated_files:
        print(f"  {filename:25} - {description}")

    print("\nHierarchy Analysis:")
    print("===================")

    # Analyze the hierarchy from the source files
    hierarchy_info = {
        "cpu_top": {
            "u_clock_gen": "clock_gen",
            "u_cpu_complex": {
                "gen_cpu_cores[0..3].u_cpu_core": {
                    "u_if_stage": "if_stage",
                    "u_id_stage": "id_stage",
                    "u_ex_stage": "ex_stage",
                    "u_mem_stage": "mem_stage",
                    "u_wb_stage": "wb_stage",
                    "u_register_file": "register_file",
                    "u_perf_counters": "performance_counters",
                },
                "u_if_arbiter": "if_arbiter_axi",
                "u_dm_arbiter": "dm_arbiter_axi",
            },
            "u_csr_block": "csr_block",
        }
    }

    def print_hierarchy(obj, indent=0):
        if isinstance(obj, dict):
            for key, value in obj.items():
                print("  " * indent + f"├── {key}")
                if isinstance(value, dict):
                    print_hierarchy(value, indent + 1)
                else:
                    print("  " * (indent + 1) + f"({value})")
        else:
            print("  " * indent + f"({obj})")

    print_hierarchy(hierarchy_info)

    print("\nType Safety Benefits:")
    print("=====================")
    benefits = [
        "IDE autocompletion for all signals and modules",
        "Static type checking with mypy",
        "Catch signal name typos at development time",
        "Understand signal types and bit widths",
        "Navigate complex hierarchies easily",
        "Generate documentation automatically",
        "Reduce debugging time with better tooling",
        "Improve code maintainability",
    ]

    for i, benefit in enumerate(benefits, 1):
        print(f"  {i}. {benefit}")

    print("\nExample Generated Type Stub Preview:")
    print("=====================================")

    # Show what a type stub might look like
    stub_preview = '''
class CpuTopType:
    """Type stub for cpu_top module."""

    # Clock and reset
    clk: SimHandleBase
    rst_n: SimHandleBase

    # Core control
    core_enable: SimHandleBase  # [3:0]
    core_active: SimHandleBase  # [3:0]
    core_halted: SimHandleBase  # [3:0]

    # AXI Instruction Fetch Interface
    m_axi_if_araddr: SimHandleBase  # [31:0]
    m_axi_if_arvalid: SimHandleBase
    m_axi_if_arready: SimHandleBase
    m_axi_if_rdata: SimHandleBase   # [31:0]
    m_axi_if_rvalid: SimHandleBase
    m_axi_if_rready: SimHandleBase

    # APB Control Interface
    s_apb_paddr: SimHandleBase   # [31:0]
    s_apb_psel: SimHandleBase
    s_apb_penable: SimHandleBase
    s_apb_pwrite: SimHandleBase
    s_apb_prdata: SimHandleBase  # [31:0]
    s_apb_pready: SimHandleBase

    # Hierarchical modules
    u_clock_gen: ClockGenType
    u_cpu_complex: CpuComplexType
    u_csr_block: CsrBlockType

class CpuComplexType:
    """Type stub for cpu_complex module."""

    # Core array
    gen_cpu_cores: List[CpuCoreType]  # [0:3]

    # Arbiters
    u_if_arbiter: IfArbiterAxiType
    u_dm_arbiter: DmArbiterAxiType

class CpuCoreType:
    """Type stub for cpu_core module."""

    # Pipeline stages
    u_if_stage: IfStageType
    u_id_stage: IdStageType
    u_ex_stage: ExStageType
    u_mem_stage: MemStageType
    u_wb_stage: WbStageType

    # Core components
    u_register_file: RegisterFileType
    u_perf_counters: PerformanceCountersType
'''

    print(stub_preview)

    print("\nUsage in Test Code:")
    print("===================")

    usage_example = '''
import cocotb
from cocotb.triggers import ClockCycles
from typing import cast
from cpu_top import CpuTopType

@cocotb.test()
async def test_cpu_functionality(dut):
    """Test with full type safety."""
    # Cast to typed interface
    cpu = cast(CpuTopType, dut)

    # IDE autocompletion works!
    cpu.rst_n.value = 0
    cpu.core_enable.value = 0xF

    await ClockCycles(cpu.clk, 10)

    # Access nested hierarchy with type safety
    core0 = cpu.u_cpu_complex.gen_cpu_cores[0]
    pc_value = core0.u_if_stage.pc.value

    # Read performance counters
    cycles = core0.u_perf_counters.cycle_count.value
    instrs = core0.u_perf_counters.instr_count.value

    # Access CSR registers
    status = await read_csr(cpu.u_csr_block, 0x0000)
'''

    print(usage_example)

    print("\n" + "=" * 60)
    print("Demo completed! This shows copra's potential with complex designs.")
    print("=" * 60)

    print("\nTo run the full example (requires cocotb 2.0+):")
    print("1. Install cocotb 2.0: pip install git+https://github.com/cocotb/cocotb.git")
    print("2. Run: make generate-stubs")
    print("3. Run: make test")
    print("4. View: make view-docs")


if __name__ == "__main__":
    demo_copra_capabilities()
