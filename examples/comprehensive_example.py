#!/usr/bin/env python3
"""Comprehensive example demonstrating copra's full capabilities.

This example showcases the complete feature set of copra for generating
Python type stubs for cocotb testbenches, including:

- Automatic DUT hierarchy discovery
- Type stub generation with enhanced array support
- Mock DUT creation for unit testing
- Coverage analysis and interface validation
- Testbench template generation
- Documentation generation

This serves as both a demonstration and a reference implementation
for integrating copra into hardware verification workflows.
"""

import asyncio
from pathlib import Path
from typing import Dict, Any

# Import copra's complete API
import copra
from copra import (
    # Core functionality
    create_stub_from_dut,
    discover_hierarchy,
    generate_stub,
    auto_generate_stubs,
    
    # Analysis and validation
    analyze_stub_coverage,
    validate_dut_interface,
    
    # Code generation
    generate_testbench_template,
    
    # Mocking and testing
    MockDUT,
    MockSignal,
    MockModule,
)
from copra.mocking import create_mock_dut_from_hierarchy


class ProcessorDUT:
    """Example processor DUT for demonstration.
    
    This class simulates a realistic processor DUT with typical
    interfaces found in CPU designs.
    """
    
    def __init__(self, name: str = "riscv_cpu"):
        """Initialize the processor DUT."""
        self._name = name
        self._sub_handles = {}
        
        # Create a realistic processor interface
        self._create_clock_and_reset()
        self._create_instruction_interface()
        self._create_data_interface()
        self._create_control_interface()
        self._create_debug_interface()
        self._create_cache_interfaces()
    
    def _create_clock_and_reset(self):
        """Create clock and reset signals."""
        self._sub_handles.update({
            "clk": MockSignal("clk", "LogicObject"),
            "rst_n": MockSignal("rst_n", "LogicObject"),
            "clk_en": MockSignal("clk_en", "LogicObject"),
        })
    
    def _create_instruction_interface(self):
        """Create instruction fetch interface."""
        self._sub_handles.update({
            "instr_addr": MockSignal("instr_addr", "LogicArrayObject", 32),
            "instr_data": MockSignal("instr_data", "LogicArrayObject", 32),
            "instr_valid": MockSignal("instr_valid", "LogicObject"),
            "instr_ready": MockSignal("instr_ready", "LogicObject"),
            "instr_error": MockSignal("instr_error", "LogicObject"),
        })
    
    def _create_data_interface(self):
        """Create data memory interface."""
        self._sub_handles.update({
            "data_addr": MockSignal("data_addr", "LogicArrayObject", 32),
            "data_wdata": MockSignal("data_wdata", "LogicArrayObject", 32),
            "data_rdata": MockSignal("data_rdata", "LogicArrayObject", 32),
            "data_we": MockSignal("data_we", "LogicObject"),
            "data_be": MockSignal("data_be", "LogicArrayObject", 4),
            "data_valid": MockSignal("data_valid", "LogicObject"),
            "data_ready": MockSignal("data_ready", "LogicObject"),
        })
    
    def _create_control_interface(self):
        """Create control and status interface."""
        self._sub_handles.update({
            "interrupt": MockSignal("interrupt", "LogicArrayObject", 8),
            "exception": MockSignal("exception", "LogicObject"),
            "halt": MockSignal("halt", "LogicObject"),
            "sleep": MockSignal("sleep", "LogicObject"),
            "pc": MockSignal("pc", "LogicArrayObject", 32),
            "status": MockSignal("status", "LogicArrayObject", 32),
        })
    
    def _create_debug_interface(self):
        """Create debug interface."""
        debug_module = MockModule("debug", "DebugInterface")
        debug_module.add_signal("enable", "LogicObject")
        debug_module.add_signal("step", "LogicObject")
        debug_module.add_signal("breakpoint", "LogicArrayObject", 32)
        debug_module.add_signal("watchpoint", "LogicArrayObject", 32)
        debug_module.add_signal("trace_data", "LogicArrayObject", 64)
        debug_module.add_signal("trace_valid", "LogicObject")
        
        self._sub_handles["debug"] = debug_module
    
    def _create_cache_interfaces(self):
        """Create cache interfaces."""
        # Instruction cache
        icache = MockModule("icache", "CacheInterface")
        icache.add_signal("hit", "LogicObject")
        icache.add_signal("miss", "LogicObject")
        icache.add_signal("flush", "LogicObject")
        icache.add_signal("invalidate", "LogicObject")
        
        # Data cache
        dcache = MockModule("dcache", "CacheInterface")
        dcache.add_signal("hit", "LogicObject")
        dcache.add_signal("miss", "LogicObject")
        dcache.add_signal("flush", "LogicObject")
        dcache.add_signal("writeback", "LogicObject")
        
        self._sub_handles.update({
            "icache": icache,
            "dcache": dcache,
        })
    
    def _discover_all(self):
        """Mock discover_all method."""
        pass


class CopraDemonstration:
    """Comprehensive demonstration of copra capabilities."""
    
    def __init__(self):
        """Initialize the demonstration."""
        self.dut = ProcessorDUT("riscv_cpu")
        self.output_dir = Path("copra_demo_output")
        self.output_dir.mkdir(exist_ok=True)
        
    def run_complete_demonstration(self):
        """Run the complete copra demonstration."""
        print("=" * 80)
        print("COPRA - Comprehensive Demonstration")
        print("Python Type Stubs Generator for cocotb Testbenches")
        print("=" * 80)
        
        try:
            self.demonstrate_hierarchy_discovery()
            self.demonstrate_stub_generation()
            self.demonstrate_enhanced_features()
            self.demonstrate_mock_testing()
            self.demonstrate_analysis_tools()
            self.demonstrate_code_generation()
            self.demonstrate_integration_workflow()
            
            self.print_summary()
            
        except Exception as e:
            print(f"Error during demonstration: {e}")
            import traceback
            traceback.print_exc()
    
    def demonstrate_hierarchy_discovery(self):
        """Demonstrate DUT hierarchy discovery."""
        print("\n1. DUT Hierarchy Discovery")
        print("-" * 40)
        
        hierarchy = discover_hierarchy(self.dut)
        
        print(f"Discovered {len(hierarchy)} signals and modules:")
        for path, obj_type in sorted(hierarchy.items()):
            print(f"  {path:<30} -> {obj_type.__name__}")
        
        # Analyze hierarchy complexity
        from copra.analysis import analyze_hierarchy_complexity
        complexity = analyze_hierarchy_complexity(self.dut)
        
        print(f"\nHierarchy Complexity Analysis:")
        print(f"  Total signals: {complexity['total_signals']}")
        print(f"  Maximum depth: {complexity['max_depth']}")
        print(f"  Module count: {complexity['module_count']}")
        print(f"  Array count: {complexity['array_count']}")
        print(f"  Signal types: {complexity['signal_types']}")
    
    def demonstrate_stub_generation(self):
        """Demonstrate stub generation with enhanced features."""
        print("\n2. Enhanced Stub Generation")
        print("-" * 40)
        
        stub_file = self.output_dir / "riscv_cpu.pyi"
        stub_content = create_stub_from_dut(self.dut, str(stub_file))
        
        print(f"Generated stub file: {stub_file}")
        print(f"Stub contains {len(stub_content.splitlines())} lines")
        
        # Show a preview of the generated stub
        lines = stub_content.splitlines()
        print("\nStub preview (first 20 lines):")
        for i, line in enumerate(lines[:20], 1):
            print(f"  {i:2d}: {line}")
        
        if len(lines) > 20:
            print(f"  ... ({len(lines) - 20} more lines)")
    
    def demonstrate_enhanced_features(self):
        """Demonstrate enhanced array and hierarchy support."""
        print("\n3. Enhanced Array and Hierarchy Support")
        print("-" * 40)
        
        # Create a DUT with arrays for demonstration
        array_dut = MockModule("array_example", "ArrayDUT")
        
        # Add array signals
        for i in range(4):
            array_dut.add_signal(f"reg_bank[{i}]", "LogicArrayObject", 32)
            array_dut.add_signal(f"status[{i}]", "LogicObject")
        
        # Add sub-module arrays
        for i in range(2):
            core = MockModule(f"core[{i}]", "CoreModule")
            core.add_signal("enable", "LogicObject")
            core.add_signal("data", "LogicArrayObject", 64)
            array_dut._children[f"core[{i}]"] = core
        
        # Generate stub with array support
        array_hierarchy = discover_hierarchy(array_dut)
        array_stub = generate_stub(array_hierarchy)
        
        array_stub_file = self.output_dir / "array_example.pyi"
        with open(array_stub_file, 'w') as f:
            f.write(array_stub)
        
        print(f"Generated array-enhanced stub: {array_stub_file}")
        print("Array structures are automatically detected and typed")
    
    def demonstrate_mock_testing(self):
        """Demonstrate mock DUT creation and testing."""
        print("\n4. Mock DUT Creation and Testing")
        print("-" * 40)
        
        # Create mock DUT from hierarchy
        hierarchy = discover_hierarchy(self.dut)
        mock_dut = create_mock_dut_from_hierarchy(hierarchy, "mock_riscv_cpu")
        
        print(f"Created mock DUT: {mock_dut}")
        print(f"Mock has {len(mock_dut.get_signals())} signals")
        print(f"Mock has {len(mock_dut.get_submodules())} sub-modules")
        
        # Demonstrate mock usage
        print("\nDemonstrating mock signal operations:")
        mock_dut.clk.value = 1
        mock_dut.rst_n.value = 0
        print(f"  Set clk = {mock_dut.clk.value}")
        print(f"  Set rst_n = {mock_dut.rst_n.value}")
        
        # Test signal callbacks
        def on_reset_change(old_val, new_val):
            print(f"  Reset changed: {old_val} -> {new_val}")
        
        mock_dut.rst_n.add_callback(on_reset_change)
        mock_dut.rst_n.value = 1  # This will trigger the callback
        
        # Reset all signals
        mock_dut.reset_all_signals()
        print("  All signals reset to 0")
    
    def demonstrate_analysis_tools(self):
        """Demonstrate analysis and validation tools."""
        print("\n5. Analysis and Validation Tools")
        print("-" * 40)
        
        stub_file = self.output_dir / "riscv_cpu.pyi"
        
        # Coverage analysis
        coverage = analyze_stub_coverage(self.dut, stub_file)
        print(f"Stub Coverage Analysis:")
        print(f"  Coverage ratio: {coverage['coverage_ratio']:.1%}")
        print(f"  Total signals: {coverage['total_signals']}")
        print(f"  Covered signals: {coverage['covered_signals']}")
        
        if coverage['missing_signals']:
            print(f"  Missing signals: {coverage['missing_signals'][:5]}...")
        
        # Interface validation
        expected_signals = [
            "clk", "rst_n", "instr_addr", "instr_data", "data_addr",
            "data_wdata", "data_rdata", "pc", "status"
        ]
        
        validation = validate_dut_interface(self.dut, expected_signals)
        print(f"\nInterface Validation:")
        print(f"  Validation passed: {validation['valid']}")
        print(f"  Expected signals: {validation['total_expected']}")
        print(f"  Actual signals: {validation['total_actual']}")
    
    def demonstrate_code_generation(self):
        """Demonstrate testbench and documentation generation."""
        print("\n6. Code and Documentation Generation")
        print("-" * 40)
        
        # Generate testbench template
        testbench_file = self.output_dir / "test_riscv_cpu.py"
        template = generate_testbench_template(self.dut, str(testbench_file))
        
        print(f"Generated testbench template: {testbench_file}")
        print(f"Template contains {len(template.splitlines())} lines")
        
        # Generate interface documentation
        from copra.generation import generate_interface_documentation
        doc_file = self.output_dir / "riscv_cpu_interface.md"
        documentation = generate_interface_documentation(self.dut, str(doc_file))
        
        print(f"Generated interface documentation: {doc_file}")
        print(f"Documentation contains {len(documentation.splitlines())} lines")
    
    def demonstrate_integration_workflow(self):
        """Demonstrate integration with cocotb workflow."""
        print("\n7. Integration with cocotb Workflow")
        print("-" * 40)
        
        # Demonstrate the auto-generation decorator
        print("Auto-generation decorator example:")
        
        @auto_generate_stubs(str(self.output_dir / "auto_generated.pyi"))
        async def example_test(dut):
            """Example test with automatic stub generation."""
            print(f"  Running test with DUT: {dut._name}")
            # Simulate test operations
            dut._sub_handles["clk"].value = 1
            await asyncio.sleep(0.001)
            dut._sub_handles["rst_n"].value = 0
            await asyncio.sleep(0.001)
            dut._sub_handles["rst_n"].value = 1
            print("  Test completed with automatic stub generation")
        
        # Run the example test
        asyncio.run(example_test(self.dut))
        
        print("\nIntegration benefits:")
        print("  - Seamless integration with existing cocotb tests")
        print("  - Automatic stub generation during test execution")
        print("  - No changes required to existing test infrastructure")
        print("  - Full IDE support with type checking and autocompletion")
    
    def print_summary(self):
        """Print demonstration summary."""
        print("\n" + "=" * 80)
        print("DEMONSTRATION SUMMARY")
        print("=" * 80)
        
        print("\nGenerated Files:")
        for file_path in self.output_dir.glob("*"):
            size = file_path.stat().st_size
            print(f"  {file_path.name:<30} ({size:,} bytes)")
        
        print(f"\nTotal output directory size: {sum(f.stat().st_size for f in self.output_dir.glob('*')):,} bytes")
        
        print("\nCopra Features Demonstrated:")
        features = [
            "✓ DUT hierarchy discovery and analysis",
            "✓ Enhanced stub generation with array support",
            "✓ Mock DUT creation for unit testing",
            "✓ Coverage analysis and interface validation", 
            "✓ Testbench template generation",
            "✓ Interface documentation generation",
            "✓ Seamless cocotb workflow integration",
            "✓ Professional-grade type safety and IDE support"
        ]
        
        for feature in features:
            print(f"  {feature}")
        
        print(f"\nFor more information, visit: https://github.com/cocotb/copra")
        print("Thank you for using copra!")


def main():
    """Run the comprehensive copra demonstration."""
    demo = CopraDemonstration()
    demo.run_complete_demonstration()


if __name__ == "__main__":
    main() 