import os
from pathlib import Path
from cocotb.handle import HierarchyObject
import cocotb
from copra.discovery import discover
from copra.generation import generate_stub
from copra.config import get_config

@cocotb.test()
async def copra_autostub(dut: HierarchyObject) -> None:
    """Auto-generate stubs for the DUT hierarchy."""
    config = get_config()
    
    print("[copra] Discovering HDL hierarchy…")
    h = await discover(dut)
    
    out_dir_path = os.getenv(config.output.env_var_stub_dir, config.output.default_stub_dir)
    out_dir = Path(out_dir_path)
    
    if not out_dir.is_absolute():
        out_dir = Path.cwd() / out_dir
    
    out_dir.mkdir(parents=True, exist_ok=True)
    stub = generate_stub(h, out_dir)
    print(f"[copra] Stub written → {stub}")
