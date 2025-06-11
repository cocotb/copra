from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Generator, List

from cocotb.handle import (
    HierarchyArrayObject,
    HierarchyObject,
    SimHandleBase,
)

from .utils import dump_pickle


@dataclass(slots=True)
class HDLNode:
    path: str
    py_type: str
    width: int | None
    is_scope: bool


def _walk(obj: SimHandleBase) -> Generator[SimHandleBase, None, None]:
    yield obj
    if isinstance(obj, HierarchyArrayObject):
        try:
            for idx in obj.range:
                yield from _walk(obj[idx])
        except RuntimeError:
            pass
    elif isinstance(obj, HierarchyObject):
        for child in obj:
            yield from _walk(child)


async def discover(dut) -> List[HDLNode]:
    dut._discover_all()
    nodes: list[HDLNode] = []

    for h in _walk(dut):
        width = len(h) if hasattr(h, "__len__") else None
        nodes.append(
            HDLNode(
                path=h._path,
                py_type=type(h).__name__,
                width=width,
                is_scope=isinstance(h, (HierarchyObject, HierarchyArrayObject)),
            )
        )
    return nodes


def run_and_pickle(
    test_module: str,
    toplevel: Path,
    build_dir: Path,
    out_pickle: Path,
) -> None:
    from cocotb_tools.runner import get_runner
    
    tb_content = f'''
import cocotb
from pathlib import Path
from copra.discovery import discover
from copra.utils import dump_pickle

@cocotb.test()
async def _copra_hierarchy_test(dut):
    nodes = await discover(dut)
    dump_pickle(nodes, Path(r"{out_pickle}"))
'''

    tb_path = build_dir / "copra_tb.py"
    tb_path.parent.mkdir(parents=True, exist_ok=True)
    tb_path.write_text(tb_content)

    rtl_dir = toplevel.parent
    all_sources = list(rtl_dir.glob("*.sv")) + list(rtl_dir.glob("*.v"))

    runner = get_runner("icarus")
    
    runner.build(
        verilog_sources=all_sources,
        hdl_toplevel=toplevel.stem,
        build_dir=build_dir,
        verbose=True,
    )
    
    runner.test(
        test_module="copra_tb",
        hdl_toplevel=toplevel.stem,
        build_dir=build_dir,
        test_dir=build_dir,
        verbose=True,
    )
