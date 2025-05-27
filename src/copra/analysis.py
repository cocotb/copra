# Copyright cocotb contributors
# Licensed under the Revised BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-3-Clause

"""Analysis and validation tools for copra stub generation.

This module provides tools for analyzing stub coverage, validating DUT interfaces,
and performing quality checks on generated stubs.
"""

import ast
from pathlib import Path
from typing import Any, Dict, List, Union

from cocotb.handle import HierarchyObject

from .core import discover_hierarchy


def analyze_stub_coverage(dut: HierarchyObject, stub_file: Union[str, Path]) -> Dict[str, Any]:
    """Analyze how well a stub file covers the actual DUT hierarchy.
    
    This function compares the actual DUT hierarchy with the generated stub file
    to determine coverage completeness and identify any discrepancies.
    
    Args:
    ----
        dut: The actual DUT object to analyze.
        stub_file: Path to the generated stub file.
        
    Returns:
    -------
        Dictionary containing comprehensive coverage analysis results including:
        - coverage_ratio: Percentage of signals covered (0.0 to 1.0)
        - total_signals: Total number of signals in the DUT
        - covered_signals: Number of signals covered by the stub
        - missing_signals: List of signals present in DUT but not in stub
        - extra_signals: List of signals in stub but not in DUT
        - stub_file: Path to the analyzed stub file
        
    Example:
    -------
        coverage = analyze_stub_coverage(dut, "my_dut.pyi")
        print(f"Coverage: {coverage['coverage_ratio']:.1%}")
        if coverage['missing_signals']:
            print(f"Missing: {coverage['missing_signals']}")
    """
    # Discover actual hierarchy
    actual_hierarchy = discover_hierarchy(dut)
    
    # Extract signal names from hierarchy (remove the DUT prefix)
    actual_signals = set()
    dut_name = getattr(dut, '_name', 'dut')
    
    for path in actual_hierarchy.keys():
        # Remove the DUT name prefix and get individual signal names
        if path.startswith(f"{dut_name}."):
            signal_path = path[len(f"{dut_name}."):]
            # Add both the full path and just the signal name
            actual_signals.add(signal_path)
            # Also add just the immediate signal name (last part)
            if '.' in signal_path:
                actual_signals.add(signal_path.split('.')[-1])
            else:
                actual_signals.add(signal_path)
        else:
            # For paths that don't start with DUT name, add as-is
            actual_signals.add(path)
            if '.' in path:
                actual_signals.add(path.split('.')[-1])
    
    # Parse stub file to get covered hierarchy
    covered_hierarchy = set()
    
    stub_path = Path(stub_file)
    if stub_path.exists():
        try:
            with open(stub_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    for child in node.body:
                        if isinstance(child, ast.AnnAssign) and isinstance(child.target, ast.Name):
                            covered_hierarchy.add(child.target.id)
        except Exception as e:
            print(f"[copra] Warning: Failed to analyze stub file: {e}")
    
    # Calculate coverage metrics
    covered_signals = covered_hierarchy & actual_signals
    coverage_ratio = len(covered_signals) / len(actual_signals) if actual_signals else 0
    
    missing_signals = actual_signals - covered_hierarchy
    extra_signals = covered_hierarchy - actual_signals
    
    return {
        'coverage_ratio': coverage_ratio,
        'total_signals': len(actual_signals),
        'covered_signals': len(covered_signals),
        'missing_signals': sorted(list(missing_signals)),
        'extra_signals': sorted(list(extra_signals)),
        'stub_file': str(stub_path),
    }


def validate_dut_interface(dut: HierarchyObject, expected_signals: List[str]) -> Dict[str, Any]:
    """Validate that a DUT has the expected interface.
    
    This function checks whether a DUT contains all expected signals and identifies
    any missing or extra signals compared to the expected interface specification.
    
    Args:
    ----
        dut: The DUT object to validate.
        expected_signals: List of expected signal names that should be present.
        
    Returns:
    -------
        Dictionary containing validation results including:
        - valid: Boolean indicating if validation passed
        - missing_signals: List of expected signals not found in DUT
        - extra_signals: List of DUT signals not in expected list
        - total_expected: Number of expected signals
        - total_actual: Number of actual signals in DUT
        
    Example:
    -------
        expected = ["clk", "rst_n", "data_in", "data_out", "valid"]
        result = validate_dut_interface(dut, expected)
        if result['valid']:
            print("Interface validation passed!")
        else:
            print(f"Missing signals: {result['missing_signals']}")
    """
    hierarchy = discover_hierarchy(dut)
    
    # Extract signal names from hierarchy (remove the DUT prefix)
    actual_signals = set()
    dut_name = getattr(dut, '_name', 'dut')
    
    for path in hierarchy.keys():
        # Remove the DUT name prefix and get individual signal names
        if path.startswith(f"{dut_name}."):
            signal_path = path[len(f"{dut_name}."):]
            # Add both the full path and just the signal name
            actual_signals.add(signal_path)
            # Also add just the immediate signal name (last part)
            if '.' in signal_path:
                actual_signals.add(signal_path.split('.')[-1])
            else:
                actual_signals.add(signal_path)
        else:
            # For paths that don't start with DUT name, add as-is
            actual_signals.add(path)
            if '.' in path:
                actual_signals.add(path.split('.')[-1])
    
    expected_set = set(expected_signals)
    
    missing = expected_set - actual_signals
    extra = actual_signals - expected_set
    
    validation_result = {
        'valid': len(missing) == 0,
        'missing_signals': sorted(list(missing)),
        'extra_signals': sorted(list(extra)),
        'total_expected': len(expected_signals),
        'total_actual': len(actual_signals),
    }
    
    if validation_result['valid']:
        print(f"[copra] DUT interface validation passed: {len(expected_signals)} signals found")
    else:
        print(f"[copra] DUT interface validation failed: {len(missing)} missing signals")
        for signal in missing:
            print(f"[copra]   Missing: {signal}")
    
    return validation_result


def validate_stub_syntax(stub_content: str) -> bool:
    """Validate that the generated stub content is syntactically correct Python.

    Args:
    ----
        stub_content: The generated stub file content as a string.

    Returns:
    -------
        True if the stub content is valid Python syntax, False otherwise.

    """
    try:
        import ast
        ast.parse(stub_content)
        return True
    except SyntaxError as e:
        print(f"[copra] Warning: Generated stub has syntax error: {e}")
        return False
    except Exception as e:
        print(f"[copra] Warning: Could not validate stub syntax: {e}")
        return False


def analyze_hierarchy_complexity(dut: HierarchyObject) -> Dict[str, Any]:
    """Analyze the complexity metrics of a DUT hierarchy.
    
    Args:
    ----
        dut: The DUT object to analyze.
        
    Returns:
    -------
        Dictionary containing complexity metrics including:
        - total_signals: Total number of signals
        - max_depth: Maximum hierarchy depth
        - module_count: Number of hierarchical modules
        - array_count: Number of array structures detected
        - signal_types: Distribution of signal types
    """
    hierarchy = discover_hierarchy(dut)
    
    # Calculate depth metrics
    max_depth = 0
    module_count = 0
    array_count = 0
    signal_types = {}
    
    for path, obj_type in hierarchy.items():
        # Calculate depth
        depth = path.count('.')
        max_depth = max(max_depth, depth)
        
        # Count modules (paths with sub-elements)
        if any(other_path.startswith(path + '.') for other_path in hierarchy.keys()):
            module_count += 1
            
        # Count arrays (paths with brackets)
        if '[' in path and ']' in path:
            array_count += 1
            
        # Count signal types
        type_name = obj_type.__name__
        signal_types[type_name] = signal_types.get(type_name, 0) + 1
    
    return {
        'total_signals': len(hierarchy),
        'max_depth': max_depth,
        'module_count': module_count,
        'array_count': array_count,
        'signal_types': signal_types,
    } 