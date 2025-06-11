from __future__ import annotations

import argparse
import shutil
import tempfile
from pathlib import Path

from .discovery import run_and_pickle
from .generation import generate_stub


def _add_common_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("example", help="path to a cocotb example directory")
    p.add_argument(
        "--top",
        default="dut",
        help="toplevel HDL file (default: %(default)s.[sv|v])",
    )


def cmd_discover(args: argparse.Namespace) -> None:
    ex = Path(args.example).resolve()
    rtl_dir = ex / "rtl" # using rtl for now, TODO: make it configurable
    top_hdl = next(rtl_dir.glob(f"{args.top}.*"))
    scratch = Path(tempfile.mkdtemp(prefix="copra_build_"))
    out_pickle = ex / ".copra" / "hierarchy.pkl"

    print(f"[copra] simulating {top_hdl.name} …")
    run_and_pickle(
        test_module="N/A",
        toplevel=top_hdl,
        build_dir=scratch,
        out_pickle=out_pickle,
    )
    print(f"[copra] hierarchy → {out_pickle}")


def cmd_stubgen(args: argparse.Namespace) -> None:
    ex = Path(args.example).resolve()
    pickle_file = ex / ".copra" / "hierarchy.pkl"
    if not pickle_file.exists():
        print(f"[copra] Hierarchy pickle not found – running `copra discover` first: {pickle_file}")
        cmd_discover(args)
        # raise SystemExit(
        #     "Hierarchy pickle not found – run `copra discover` first."
        # )
    out_dir = ex / "copra_stubs"
    stub = generate_stub(pickle_file, out_dir)
    print(f"[copra] stubs written to {stub}")


def main() -> None:
    ap = argparse.ArgumentParser(prog="copra")
    sp = ap.add_subparsers(dest="cmd", required=True)

    p_disc = sp.add_parser("discover", help="run cocotb and pickle hierarchy")
    _add_common_args(p_disc)
    p_disc.set_defaults(func=cmd_discover)

    p_stub = sp.add_parser("stubgen", help="turn pickle into .pyi stubs")
    _add_common_args(p_stub)
    p_stub.set_defaults(func=cmd_stubgen)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
