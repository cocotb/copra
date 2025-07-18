from __future__ import annotations

import argparse
import tempfile
from pathlib import Path
from typing import Optional, List, Any

from .config import get_config

class HDLFileDiscoverer:
    """Configurable HDL file discovery."""
    
    def __init__(self):
        self.config = get_config()
    
    def find_rtl_directory(self, base_path: Path) -> Path:
        """Find the RTL directory based on configuration."""
        for dirname in self.config.hdl.rtl_directory_names:
            candidate = base_path / dirname
            if candidate.exists() and candidate.is_dir():
                return candidate
        return base_path
    
    def find_top_hdl_file(self, rtl_dir: Path, top_name: str) -> Optional[Path]:
        """Find the top HDL file based on configuration."""
        for ext in self.config.hdl.all_extensions:
            candidate = rtl_dir / f"{top_name}{ext}"
            if candidate.exists():
                return candidate
        return None
    
    def get_all_hdl_files(self, rtl_dir: Path) -> List[Path]:
        """Get all HDL files in the directory."""
        files: List[Path] = []
        for ext in self.config.hdl.all_extensions:
            files.extend(rtl_dir.glob(f"*{ext}"))
        return files
    
    def extract_module_name(self, hdl_file: Path) -> str:
        """Extract the module name from an HDL file."""
        content = hdl_file.read_text()
        patterns = self.config.hdl.get_module_patterns()
        
        if self.config.hdl.is_verilog(hdl_file):
            match = patterns['verilog'].search(content)
            if match:
                return match.group(1)
        elif self.config.hdl.is_vhdl(hdl_file):
            match = patterns['vhdl'].search(content)
            if match:
                return match.group(1)
        
        return hdl_file.stem

class SimulatorRunner:
    """Configurable simulator integration."""
    
    def __init__(self):
        self.config = get_config()
    
    def run_simulation(
        self, 
        hdl_files: List[Path], 
        top_module: str, 
        project_dir: Path,
        top_hdl_file: Path,
        simulator: Optional[str] = None
    ) -> None:
        """Run simulation with the specified or auto-detected simulator."""
        import os
        
        scratch = Path(tempfile.mkdtemp(prefix=self.config.output.temp_prefix))
        
        stub_dir = project_dir / self.config.output.default_stub_dir
        os.environ[self.config.output.env_var_stub_dir] = str(stub_dir)
        
        runner = self.config.get_simulator_runner(simulator)
        simulator_name = self._detect_simulator_name(runner)
        
        if simulator:
            print(f"[copra] Using {simulator_name} simulator (explicitly specified)")
        elif os.getenv('SIM'):
            print(f"[copra] Using {simulator_name} simulator (from SIM environment variable)")
        else:
            print(f"[copra] Using {simulator_name} simulator (auto-detected)")
        
        self._setup_simulator_environment(simulator_name)
        
        verilog_files = [f for f in hdl_files if self.config.hdl.is_verilog(f)]
        vhdl_files = [f for f in hdl_files if self.config.hdl.is_vhdl(f)]
        
        if vhdl_files and not verilog_files:
            raise ValueError(f"VHDL files found but current simulator configuration may not support VHDL")
        
        build_args = self.config.simulator.build_args.get(simulator_name, [])
        
        print(f"[copra] Found {len(hdl_files)} HDL files")

        if self.config.simulator.supports_language(simulator_name, 'verilog') and verilog_files:
            sources_to_use = [str(f) for f in verilog_files]
            print(f"[copra] Using {len(sources_to_use)} Verilog files (simulator supports Verilog)")
            runner.build(
                verilog_sources=sources_to_use,
                hdl_toplevel=top_module,
                build_dir=scratch,
                build_args=build_args,
                verbose=True,
            )
        elif self.config.simulator.supports_language(simulator_name, 'vhdl') and vhdl_files:
            sources_to_use = [str(f) for f in vhdl_files]
            print(f"[copra] Using {len(sources_to_use)} VHDL files (simulator supports VHDL)")
            runner.build(
                vhdl_sources=sources_to_use,
                hdl_toplevel=top_module,
                build_dir=scratch,
                build_args=build_args,
                verbose=True,
            )
        else:
            raise ValueError(
                f"Simulator '{simulator_name}' does not support any available HDL languages. "
                f"Available files: {len(verilog_files)} Verilog, {len(vhdl_files)} VHDL. "
                f"Simulator supports: {self.config.simulator.language_support.get(simulator_name, [])}"
            )
        
        runner.test(
            test_module="copra.integration.autostub",
            hdl_toplevel=top_module,
            build_dir=scratch,
            verbose=True,
        )
    
    def _detect_simulator_name(self, runner: Any) -> str:
        """Detect the simulator name from the runner."""
        runner_class_name = type(runner).__name__.lower()
        for sim_name in self.config.simulator.preferred_simulators:
            if sim_name in runner_class_name:
                return sim_name
        return 'unknown'
    
    def _setup_simulator_environment(self, simulator_name: str) -> None:
        """Setup environment variables for the simulator."""
        import os
        env_vars = self.config.simulator.env_vars.get(simulator_name, {})
        for key, value in env_vars.items():
            os.environ[key] = value

class CopraCommandProcessor:
    """Main command processor for copra."""
    
    def __init__(self):
        self.config = get_config()
        self.file_discoverer = HDLFileDiscoverer()
        self.simulator_runner = SimulatorRunner()
    
    def generate_stubs(self, project_path: str, top_name: str, simulator: Optional[str] = None) -> None:
        """Generate stubs for the given project."""
        project_dir = Path(project_path).resolve()
        
        if not project_dir.exists():
            raise FileNotFoundError(f"Project directory not found: {project_dir}")
        
        rtl_dir = self.file_discoverer.find_rtl_directory(project_dir)
        top_hdl = self.file_discoverer.find_top_hdl_file(rtl_dir, top_name)
        
        if not top_hdl:
            available_files = self.file_discoverer.get_all_hdl_files(rtl_dir)
            if available_files:
                print(f"[copra] Error: Could not find HDL file matching '{top_name}.*' in {rtl_dir}")
                print(f"[copra] Available HDL files:")
                for f in available_files:
                    print(f"  - {f.name}")
            else:
                print(f"[copra] Error: No HDL files found in {rtl_dir}")
            return
        
        module_name = self.file_discoverer.extract_module_name(top_hdl)
        all_hdl_files = self.file_discoverer.get_all_hdl_files(rtl_dir)
        
        if not all_hdl_files:
            print(f"[copra] Error: No HDL source files found in {rtl_dir}")
            return
        
        print(f"[copra] Generating stubs for {top_hdl.name} (module: {module_name})")
        print(f"[copra] Found {len(all_hdl_files)} HDL files in {rtl_dir}")
        
        try:
            self.simulator_runner.run_simulation(
                all_hdl_files, 
                module_name, 
                project_dir,
                top_hdl,
                simulator
            )
            print(f"[copra] Stub generation completed successfully!")
        except Exception as e:
            print(f"[copra] Error during simulation: {e}")

def create_argument_parser() -> argparse.ArgumentParser:
    """Create the argument parser for copra."""
    config = get_config()
    
    parser = argparse.ArgumentParser(
        prog="copra",
        description="Generate Python type stubs for cocotb HDL designs"
    )
    
    subparsers = parser.add_subparsers(dest="cmd", required=True)
    
    gen_parser = subparsers.add_parser(
        "generate", 
        help="Generate .pyi stubs for HDL design"
    )
    
    gen_parser.add_argument(
        "project", 
        help="Path to HDL project directory"
    )
    
    gen_parser.add_argument(
        "--top",
        default="dut",
        help=f"Top-level HDL module name (default: %(default)s)"
    )
    
    gen_parser.add_argument(
        "--simulator",
        choices=config.simulator.preferred_simulators,
        help="Simulator to use (auto-detected if not specified)"
    )
    
    return parser

def main() -> None:
    """Main entry point for copra CLI."""
    parser = create_argument_parser()
    args = parser.parse_args()
    
    processor = CopraCommandProcessor()
    
    if args.cmd == "generate":
        processor.generate_stubs(
            args.project, 
            args.top, 
            getattr(args, 'simulator', None)
        )

if __name__ == "__main__":
    main()
