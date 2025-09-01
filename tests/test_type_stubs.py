import subprocess, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]  # repo root

def test_stubs_typecheck() -> None:
    """Fail if mypy finds *any* typing errors anywhere under examples/."""
    examples_dir = ROOT / "examples"
    
    errors: list[str] = []
    for d in examples_dir.iterdir():
        if d.is_dir() and (d / "copra_stubs").exists():
            result = subprocess.run([
                sys.executable, '-m', 'mypy',
                '--config-file', str(ROOT / 'pyproject.toml'), 
                str(d / 'copra_stubs')
            ], capture_output=True, text=True)
            if result.returncode:
                errors.append(f"Errors in {d.name}:\n{result.stdout}")

    if errors:
        print("\n".join(errors))
    assert not errors, f"MyPy found {len(errors)} example(s) with type errors"
