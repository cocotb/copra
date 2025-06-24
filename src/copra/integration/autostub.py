import os
from pathlib import Path
from cocotb.handle import HierarchyObject
import cocotb
from copra.discovery import discover
from copra.generation import generate_stub

@cocotb.test()
async def copra_autostub(dut: HierarchyObject) -> None:
    """Auto-generate stubs for the DUT hierarchy."""
    print("[copra] Discovering HDL hierarchy…")
    h = await discover(dut)
    out_dir = Path(os.getenv("COPRA_STUB_DIR", Path.cwd() / "copra_stubs"))
    out_dir.mkdir(parents=True, exist_ok=True)
    stub = generate_stub(h, out_dir)
    print(f"[copra] Stub written → {stub}")
