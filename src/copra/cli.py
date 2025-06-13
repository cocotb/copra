from __future__ import annotations

import argparse
import tempfile
from pathlib import Path

from .discovery import discover
from .generation import generate_stub


def _add_common_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("example", help="path to a cocotb example directory")
    p.add_argument(
        "--top",
        default="dut",
        help="toplevel HDL file (default: %(default)s.[sv|v])",
    )


def cmd_generate(args: argparse.Namespace) -> None:
    """Generate stubs using iterative hierarchy building approach."""
    ex = Path(args.example).resolve()
    rtl_dir = ex / "rtl"
    top_hdl = next(rtl_dir.glob(f"{args.top}.*"))
    
    print(f"[copra] Generating stubs for {top_hdl.name} using iterative hierarchy building…")
    
    scratch = Path(tempfile.mkdtemp(prefix="copra_"))
    
    tb_content = f'''
import cocotb
from pathlib import Path
from copra.discovery import discover
from copra.generation import generate_stub

@cocotb.test()
async def _copra_hierarchy_test(dut):
    # Use iterative hierarchy building approach
    hierarchy = await discover(dut)
    
    # Generate stub directly from hierarchy
    out_dir = Path(r"{ex / 'copra_stubs'}")
    stub_path = generate_stub(hierarchy, out_dir)
    
    print(f"[copra] Generated stub: {{stub_path}}")
    print(f"[copra] Discovered {{len(hierarchy.get_nodes())}} nodes in hierarchy")
'''

    tb_path = scratch / "copra_tb.py"
    tb_path.parent.mkdir(parents=True, exist_ok=True)
    tb_path.write_text(tb_content)

    from cocotb_tools.runner import get_runner
    
    all_sources = list(rtl_dir.glob("*.sv")) + list(rtl_dir.glob("*.v"))
    runner = get_runner("icarus")
    
    runner.build(
        verilog_sources=all_sources,
        hdl_toplevel=top_hdl.stem,
        build_dir=scratch,
        verbose=True,
    )
    
    runner.test(
        test_module="copra_tb",
        hdl_toplevel=top_hdl.stem,
        build_dir=scratch,
        test_dir=scratch,
        verbose=True,
    )
    
    print(f"[copra] Stub generation completed successfully!")


def main() -> None:
    ap = argparse.ArgumentParser(
        prog="copra",
        description="generate Python type stubs for cocotb using iterative hierarchy building"
    )
    sp = ap.add_subparsers(dest="cmd", required=True)

    p_gen = sp.add_parser("generate", help="generate .pyi stubs using iterative hierarchy building")
    _add_common_args(p_gen)
    p_gen.set_defaults(func=cmd_generate)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
