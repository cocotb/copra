import subprocess, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]  # repo root

def test_stubs_typecheck() -> None:
    """Fail if mypy finds *any* typing errors anywhere under examples/."""
    examples_dir = ROOT / "examples"
    
    errors = [
        f"Errors in {d.name}:\n{subprocess.run([
            sys.executable, '-m', 'mypy',
            '--config-file', str(ROOT / 'pyproject.toml'),
            str(d / 'copra_stubs')
        ], capture_output=True, text=True).stdout}"
        for d in examples_dir.iterdir()
        if d.is_dir() and (d / "copra_stubs").exists() 
        and subprocess.run([
            sys.executable, '-m', 'mypy',
            '--config-file', str(ROOT / 'pyproject.toml'), 
            str(d / 'copra_stubs')
        ], capture_output=True, text=True).returncode
    ]

    if errors:
        print("\n".join(errors))
    assert not errors, f"MyPy found {len(errors)} example(s) with type errors"
