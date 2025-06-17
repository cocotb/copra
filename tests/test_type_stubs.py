import subprocess, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]  # repo root

def test_stubs_typecheck() -> None:
    """Fail if mypy finds *any* typing errors anywhere under examples/."""
    cmd = [
        sys.executable, "-m", "mypy",
        "--config-file", str(ROOT / "pyproject.toml"),
        str(ROOT / "examples"),
    ]
    completed = subprocess.run(
        cmd, capture_output=True, text=True
    )
    if completed.returncode:            # mypy raised complaints
        print(completed.stdout)          # forward full report to pytest
    assert completed.returncode == 0
