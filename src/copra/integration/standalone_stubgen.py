#!/usr/bin/env python3

import os
import sys
import tempfile
from pathlib import Path

copra_src = Path(__file__).parent.parent.parent
sys.path.insert(0, str(copra_src))

from cocotb_tools.runner import get_runner
from copra.config import get_config

def main():
    config = get_config()
    
    if len(sys.argv) > 1:
        output_dir = Path(sys.argv[1])
    else:
        out_dir_path = os.getenv(config.output.env_var_stub_dir, config.output.default_stub_dir)
        output_dir = Path(out_dir_path)
    
    if not output_dir.is_absolute():
        output_dir = Path.cwd() / output_dir
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    sim = os.getenv("SIM", "icarus")
    hdl_toplevel = os.getenv("COCOTB_TOPLEVEL")
    hdl_toplevel_lang = os.getenv("TOPLEVEL_LANG", "verilog")
    
    if not hdl_toplevel:
        sys.exit(1)
    
    verilog_sources, vhdl_sources = os.getenv("VERILOG_SOURCES", ""), os.getenv("VHDL_SOURCES", "")
    
    if hdl_toplevel_lang == "verilog" and verilog_sources:
        sources = [Path(s.strip()) for s in verilog_sources.split() if s.strip()]
    elif hdl_toplevel_lang == "vhdl" and vhdl_sources:
        sources = [Path(s.strip()) for s in vhdl_sources.split() if s.strip()]
    else:
        sys.exit(1)
    
    build_args: list[str] = []
    if build_args_str := os.getenv("COMPILE_ARGS"):
        args = build_args_str.split()
        i = 0
        while i < len(args):
            if args[i] == '-f' and i + 1 < len(args) and 'sim_build/cmds.f' in args[i + 1]:
                i += 2
            else:
                build_args.append(args[i])
                i += 1
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        env = os.environ.copy()
        env["COPRA_STUB_DIR"] = str(output_dir)
        runner = get_runner(sim)
        
        runner.build(
            sources=sources,
            hdl_toplevel=hdl_toplevel,
            build_args=build_args,
            build_dir=temp_path / "build",
            always=True,
        )
        
        runner.test(
            hdl_toplevel=hdl_toplevel,
            hdl_toplevel_lang=hdl_toplevel_lang,
            test_module="copra.integration.autostub",
            test_dir=temp_path,
            build_dir=temp_path / "build",
            extra_env=env,
        )
        
        stub_path = output_dir / config.output.stub_filename
        print(f"[copra] Stub written → {stub_path}")

if __name__ == "__main__":
    main() 
