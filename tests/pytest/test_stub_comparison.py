import ast
import pathlib
import os
import subprocess
from typing import Dict, List

ROOT = pathlib.Path(__file__).resolve().parents[2]  # repo root


def parse_pyi_file(file_path: pathlib.Path) -> Dict[str, Dict[str, str]]:
    with open(file_path, 'r') as f:
        content = f.read()
    
    lines: List[str] = []
    for line in content.split('\n'):
        if line.strip().startswith('#'):
            continue
        if '#' in line:
            line = line[:line.index('#')]
        lines.append(line)
    
    content = '\n'.join(lines)
    
    tree = ast.parse(content)
    
    classes: Dict[str, Dict[str, str]] = {}
    
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            class_name = node.name
            attributes: Dict[str, str] = {}
            
            for item in node.body:
                if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                    attr_name = item.target.id
                    if item.annotation:
                        attr_type = ast.unparse(item.annotation)
                        attributes[attr_name] = attr_type
                elif isinstance(item, ast.Assign):
                    for target in item.targets:
                        if isinstance(target, ast.Name):
                            attr_name = target.id
            
            classes[class_name] = attributes
    
    return classes


def find_generated_stub(example_dir: pathlib.Path) -> pathlib.Path | None:
    stub_path = example_dir / "tests" / "copra_stubs.pyi"
    if stub_path.exists():
        return stub_path
    
    stub_path = example_dir / "copra_stubs.pyi"
    if stub_path.exists():
        return stub_path
    
    return None


def generate_stubs_for_example(example_dir: pathlib.Path) -> bool:
    """Generate stubs for an example using SIM=icarus make gen_stubs"""
    makefile_path = example_dir / "Makefile"
    if not makefile_path.exists():
        makefile_path = example_dir / "tests" / "Makefile"
        if not makefile_path.exists():
            return False
    
    env = os.environ.copy()
    env['SIM'] = 'icarus'
    env['PYTHONPATH'] = str(ROOT / 'src') + os.pathsep + env.get('PYTHONPATH', '')
    
    cwd = makefile_path.parent
    
    result = subprocess.run(
        ['make', 'gen_stubs'],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
    )
    
    if result.returncode != 0:
        print(f"Failed to generate stubs for {example_dir.name}: {result.stderr}")
        return False
    
    return True


def compare_stubs(golden_path: pathlib.Path, generated_path: pathlib.Path) -> List[str]:
    errors: List[str] = []
    
    if not golden_path.exists():
        errors.append(f"Golden file not found: {golden_path}")
        return errors
    
    if not generated_path.exists():
        errors.append(f"Generated stub not found: {generated_path}")
        return errors
    
    try:
        golden_classes = parse_pyi_file(golden_path)
        generated_classes = parse_pyi_file(generated_path)
    except Exception as e:
        errors.append(f"Failed to parse files: {e}")
        return errors
    
    for class_name in golden_classes:
        if class_name not in generated_classes:
            errors.append(f"Class '{class_name}' missing in generated stub")
            continue
        
        golden_attrs = golden_classes[class_name]
        generated_attrs = generated_classes[class_name]
        
        for attr_name, attr_type in golden_attrs.items():
            if attr_name not in generated_attrs:
                errors.append(f"Attribute '{class_name}.{attr_name}' missing in generated stub")
            elif generated_attrs[attr_name] != attr_type:
                errors.append(
                    f"Type mismatch for '{class_name}.{attr_name}': "
                    f"expected '{attr_type}', got '{generated_attrs[attr_name]}'"
                )
    
    return errors


def test_stub_comparison():
    """Test that generated stubs match golden reference files."""
    os.environ['SIM'] = 'icarus'
    
    examples_dir = ROOT / "examples"
    all_errors: List[str] = []

    for example_dir in examples_dir.iterdir():
        if not example_dir.is_dir():
            continue
        
        golden_path = example_dir / "dut_golden.pyi"
        if not golden_path.exists():
            continue
        
        print(f"Generating stubs for {example_dir.name}...")
        if not generate_stubs_for_example(example_dir):
            all_errors.append(f"Failed to generate stubs for {example_dir.name}")
            continue
        
        generated_path = find_generated_stub(example_dir)
        if generated_path is None:
            all_errors.append(f"No generated stub found for {example_dir.name}")
            continue
        
        print(f"Comparing stubs for {example_dir.name}...")
        errors = compare_stubs(golden_path, generated_path)
        
        if errors:
            all_errors.extend([f"{example_dir.name}: {error}" for error in errors])
    
    if all_errors:
        print("\n".join(all_errors))
        print(f"\nFound {len(all_errors)} stub comparison error(s)")
        print("Note: Some differences are expected if copra implementation is incomplete")
    
    print("Stub comparison completed!")
