# Copyright cocotb contributors
# Licensed under the Revised BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-3-Clause

"""Analysis and validation tools for copra stub generation.

This module provides tools for analyzing stub coverage, validating DUT interfaces,
and performing quality checks on generated stubs.
"""

import ast
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Union, Optional, Set

from cocotb.handle import HierarchyObject  # type: ignore[import-untyped]

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
    dut_name = getattr(dut, "_name", "dut")

    for path in actual_hierarchy.keys():
        # Remove the DUT name prefix and get individual signal names
        if path.startswith(f"{dut_name}."):
            signal_path = path[len(f"{dut_name}.") :]
            # Add both the full path and just the signal name
            actual_signals.add(signal_path)
            # Also add just the immediate signal name (last part)
            if "." in signal_path:
                actual_signals.add(signal_path.split(".")[-1])
            else:
                actual_signals.add(signal_path)
        else:
            # For paths that don't start with DUT name, add as-is
            actual_signals.add(path)
            if "." in path:
                actual_signals.add(path.split(".")[-1])

    # Parse stub file to get covered hierarchy
    covered_hierarchy = set()

    stub_path = Path(stub_file)
    if stub_path.exists():
        try:
            with open(stub_path, encoding="utf-8") as f:
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
        "coverage_ratio": coverage_ratio,
        "total_signals": len(actual_signals),
        "covered_signals": len(covered_signals),
        "missing_signals": sorted(list(missing_signals)),
        "extra_signals": sorted(list(extra_signals)),
        "stub_file": str(stub_path),
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
    dut_name = getattr(dut, "_name", "dut")

    for path in hierarchy.keys():
        # Remove the DUT name prefix and get individual signal names
        if path.startswith(f"{dut_name}."):
            signal_path = path[len(f"{dut_name}.") :]
            # Add both the full path and just the signal name
            actual_signals.add(signal_path)
            # Also add just the immediate signal name (last part)
            if "." in signal_path:
                actual_signals.add(signal_path.split(".")[-1])
            else:
                actual_signals.add(signal_path)
        else:
            # For paths that don't start with DUT name, add as-is
            actual_signals.add(path)
            if "." in path:
                actual_signals.add(path.split(".")[-1])

    expected_set = set(expected_signals)

    missing = expected_set - actual_signals
    extra = actual_signals - expected_set

    validation_result = {
        "valid": len(missing) == 0,
        "missing_signals": sorted(list(missing)),
        "extra_signals": sorted(list(extra)),
        "total_expected": len(expected_signals),
        "total_actual": len(actual_signals),
    }

    if validation_result["valid"]:
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


def analyze_hierarchy_complexity(dut: Any) -> Dict[str, Any]:
    """Analyze the complexity and structure of a DUT hierarchy.

    This function provides comprehensive analysis of the DUT structure including
    signal counts, depth analysis, and complexity metrics as specified in the design.

    Args:
    ----
        dut: The DUT object to analyze.

    Returns:
    -------
        Dictionary containing detailed analysis results.

    """
    from .core import HierarchyDict
    
    hierarchy: HierarchyDict = discover_hierarchy(dut, max_depth=100, include_constants=True)

    analysis: Dict[str, Any] = {
        "total_signals": 0,
        "total_modules": 0,
        "max_depth": 0,
        "module_count": 0,
        "array_count": 0,
        "signal_types": {},
        "depth_distribution": {},
        "naming_patterns": {},
        "complexity_score": 0.0,
        "hierarchy_paths": [],
        "module_types": set(),
        "signal_width_distribution": {},
        "array_size_distribution": {},
        "array_signals": {},  # Map array names to their elements
    }

    # First pass: identify which paths are modules (have children)
    module_paths: Set[str] = set()
    module_paths.add("dut")  # Root is always a module

    for path in hierarchy.keys():
        parts = path.split(".")
        # Add all parent paths as modules
        for i in range(1, len(parts)):
            parent_path = ".".join(parts[:i])
            module_paths.add(parent_path)

    # Analyze each path in the hierarchy
    for path, obj_type in hierarchy.items():
        analysis["hierarchy_paths"].append(path)

        # Calculate depth
        depth = path.count(".")
        analysis["max_depth"] = max(analysis["max_depth"], depth)

        # Update depth distribution
        analysis["depth_distribution"][depth] = analysis["depth_distribution"].get(depth, 0) + 1

        # Classify object type
        type_name = obj_type.__name__
        analysis["signal_types"][type_name] = analysis["signal_types"].get(type_name, 0) + 1

        # Count all objects as signals for total count (exclude root "dut" entry)
        if path != "dut":
            analysis["total_signals"] += 1

        # Count modules separately
        if path in module_paths:
            analysis["total_modules"] += 1
            analysis["module_types"].add(type_name)

        # Check for arrays
        if "[" in path and "]" in path:
            # Extract array size information
            array_match = re.search(r"\[(\d+)\]", path)
            if array_match:
                array_index = int(array_match.group(1))
                base_path = path[: path.rfind("[")]
                # Get just the array name (e.g., "mem" from "dut.mem")
                base_name = base_path.split(".")[-1]

                if base_path not in analysis["array_size_distribution"]:
                    analysis["array_size_distribution"][base_path] = {
                        "max_index": 0,
                        "indices": set(),
                    }
                    array_signals = analysis["array_signals"]
                    if isinstance(array_signals, dict):
                        array_signals[base_name] = []

                array_dist = analysis["array_size_distribution"]
                if isinstance(array_dist, dict) and base_path in array_dist:
                    current_max = array_dist[base_path]["max_index"]
                    if isinstance(current_max, int):
                        array_dist[base_path]["max_index"] = max(current_max, array_index)
                    
                    indices_set = array_dist[base_path]["indices"]
                    if isinstance(indices_set, set):
                        indices_set.add(array_index)
                
                array_signals = analysis["array_signals"]
                if isinstance(array_signals, dict) and base_name in array_signals:
                    signal_list = array_signals[base_name]
                    if isinstance(signal_list, list):
                        signal_list.append(path)

        # Analyze naming patterns
        path_parts = path.split(".")
        for part in path_parts:
            # Remove array indices for pattern analysis
            clean_part = re.sub(r"\[\d+\]", "", part)
            if clean_part:
                # Analyze naming conventions
                if "_" in clean_part:
                    pattern = "snake_case"
                elif clean_part[0].isupper():
                    pattern = "PascalCase"
                elif clean_part[0].islower() and any(c.isupper() for c in clean_part):
                    pattern = "camelCase"
                else:
                    pattern = "lowercase"

                current_count = analysis["naming_patterns"].get(pattern, 0)
                analysis["naming_patterns"][pattern] = current_count + 1

    # Calculate complexity score
    # Base score from number of objects
    complexity = len(hierarchy)

    # Add complexity for depth
    complexity += analysis["max_depth"] * 10

    # Add complexity for arrays
    complexity += analysis["array_count"] * 5

    # Add complexity for diverse signal types
    complexity += len(analysis["signal_types"]) * 2

    analysis["complexity_score"] = complexity
    analysis["module_count"] = analysis["total_modules"]

    # Calculate array size statistics
    array_size_dist = analysis["array_size_distribution"]
    if isinstance(array_size_dist, dict):
        for base_path, array_info in array_size_dist.items():
            if isinstance(array_info, dict):
                indices = array_info["indices"]
                if isinstance(indices, set):
                    array_info["size"] = len(indices)
                    max_index = array_info["max_index"]
                    if isinstance(max_index, int):
                        array_info["is_contiguous"] = (
                            array_info["size"] == max_index + 1 and min(indices) == 0
                        )

    # Count unique arrays (not individual elements)
    analysis["array_count"] = len(analysis["array_size_distribution"])

    # Detect functional naming patterns
    functional_patterns: Dict[str, List[str]] = {
        "clock_signals": [],
        "reset_signals": [],
        "input_signals": [],
        "output_signals": [],
        "bus_signals": [],
    }

    for path in hierarchy.keys():
        if path == "dut":
            continue
        path_lower = path.lower()

        # Detect clock signals
        clk_patterns = ["clk", "clock"]
        if any(clk_pattern in path_lower for clk_pattern in clk_patterns):
            signal_type = "clk" if "clk" in path_lower else "clock"
            functional_patterns["clock_signals"].append(signal_type)

        # Detect reset signals
        rst_patterns = ["rst", "reset"]
        if any(rst_pattern in path_lower for rst_pattern in rst_patterns):
            signal_type = "rst" if "rst" in path_lower else "reset"
            functional_patterns["reset_signals"].append(signal_type)

        # Detect input/output signals
        if "in" in path_lower or "input" in path_lower:
            signal_type = "in" if "in" in path_lower else "input"
            functional_patterns["input_signals"].append(signal_type)
        if "out" in path_lower or "output" in path_lower:
            signal_type = "out" if "out" in path_lower else "output"
            functional_patterns["output_signals"].append(signal_type)

        # Detect bus interfaces
        bus_patterns = ["axi", "ahb", "apb", "wishbone", "avalon"]
        if any(bus_pattern in path_lower for bus_pattern in bus_patterns):
            functional_patterns["bus_signals"].append(path)

    # Remove duplicates and add to analysis
    for pattern_type, patterns in functional_patterns.items():
        analysis["naming_patterns"][pattern_type] = list(set(patterns))

    return analysis


def generate_hierarchy_report(dut: Any, output_file: Optional[str] = None) -> str:
    """Generate a comprehensive hierarchy analysis report.

    Args:
    ----
        dut: The DUT object to analyze.
        output_file: Optional output file path.

    Returns:
    -------
        Generated report content.

    """
    analysis = analyze_hierarchy_complexity(dut)

    report_lines = [
        "# Hierarchy Analysis Report",
        f"Generated at: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        f"DUT: {dut._name}",
        "",
        "## Summary",
        f"- Total Signals: {analysis['total_signals']}",
        f"- Total Modules: {analysis['total_modules']}",
        f"- Maximum Depth: {analysis['max_depth']}",
        f"- Module Count: {analysis['module_count']}",
        f"- Array Count: {analysis['array_count']}",
        f"- Complexity Score: {analysis['complexity_score']}",
        "",
        "## Signal Types",
    ]

    for signal_type, count in analysis["signal_types"].items():
        report_lines.append(f"- {signal_type}: {count}")

    report_lines.extend(
        [
            "",
            "## Depth Distribution",
        ]
    )

    for depth, count in sorted(analysis["depth_distribution"].items()):
        report_lines.append(f"- Depth {depth}: {count} objects")

    if analysis.get("array_size_distribution"):
        report_lines.extend(
            [
                "",
                "## Array Analysis",
            ]
        )

        for base_path, array_info in sorted(analysis["array_size_distribution"].items()):
            contiguous = "contiguous" if array_info["is_contiguous"] else "sparse"
            report_lines.append(
                f"- {base_path}: {array_info['size']} elements "
                f"(max index: {array_info['max_index']}, {contiguous})"
            )

    report_content = "\n".join(report_lines)

    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(report_content)

    return report_content


def detect_design_patterns(dut: Any) -> Dict[str, List[str]]:
    """Detect common design patterns in the DUT hierarchy.

    Args:
    ----
        dut: The DUT object to analyze.

    Returns:
    -------
        Dictionary mapping pattern names to lists of detected instances.

    """
    import re

    from .core import discover_hierarchy

    hierarchy = discover_hierarchy(dut)
    patterns: Dict[str, List[str]] = {
        "clock_domains": [],
        "reset_signals": [],
        "bus_interfaces": [],
        "memory_interfaces": [],
        "state_machines": [],
        "counters": [],
        "fifos": [],
        "pipeline_stages": [],
    }

    for path in hierarchy.keys():
        path_lower = path.lower()

        # Detect clock signals
        if any(clk_pattern in path_lower for clk_pattern in ["clk", "clock", "ck"]):
            patterns["clock_domains"].append(path)

        # Detect reset signals
        if any(rst_pattern in path_lower for rst_pattern in ["rst", "reset", "res"]):
            patterns["reset_signals"].append(path)

        # Detect bus interfaces
        bus_patterns = ["axi", "ahb", "apb", "wishbone", "avalon"]
        if any(bus_pattern in path_lower for bus_pattern in bus_patterns):
            patterns["bus_interfaces"].append(path)

        # Detect memory interfaces
        mem_patterns = ["mem", "ram", "rom", "cache"]
        if any(mem_pattern in path_lower for mem_pattern in mem_patterns):
            patterns["memory_interfaces"].append(path)

        # Detect state machines
        if any(sm_pattern in path_lower for sm_pattern in ["state", "fsm", "sm"]):
            patterns["state_machines"].append(path)

        # Detect counters
        if any(cnt_pattern in path_lower for cnt_pattern in ["count", "cnt", "counter"]):
            patterns["counters"].append(path)

        # Detect FIFOs
        if any(fifo_pattern in path_lower for fifo_pattern in ["fifo", "queue", "buffer"]):
            patterns["fifos"].append(path)

        # Detect pipeline stages
        if re.search(r"stage\d+|pipe\d+|p\d+_", path_lower):
            patterns["pipeline_stages"].append(path)

    return patterns


def validate_naming_conventions(
    dut: Any, conventions: Optional[Dict[str, str]] = None
) -> Dict[str, List[str]]:
    """Validate naming conventions in the DUT hierarchy.

    Args:
    ----
        dut: The DUT object to analyze.
        conventions: Dictionary of naming convention rules.

    Returns:
    -------
        Dictionary of validation results with violations.

    """
    if conventions is None:
        conventions = {
            "signals": "snake_case",
            "modules": "snake_case",
            "constants": "UPPER_CASE",
            "clocks": "clk_*",
            "resets": "rst_*",
        }

    import re

    from .core import discover_hierarchy

    hierarchy = discover_hierarchy(dut)
    violations: Dict[str, List[str]] = {
        "naming_violations": [],
        "reserved_word_usage": [],
        "length_violations": [],
        "character_violations": [],
    }

    # Python reserved words to check against
    reserved_words = {
        "and",
        "as",
        "assert",
        "break",
        "class",
        "continue",
        "def",
        "del",
        "elif",
        "else",
        "except",
        "exec",
        "finally",
        "for",
        "from",
        "global",
        "if",
        "import",
        "in",
        "is",
        "lambda",
        "not",
        "or",
        "pass",
        "print",
        "raise",
        "return",
        "try",
        "while",
        "with",
        "yield",
        "True",
        "False",
        "None",
    }

    for path in hierarchy.keys():
        path_parts = path.split(".")

        for part in path_parts:
            # Remove array indices for validation
            clean_part = re.sub(r"\[\d+\]", "", part)

            if not clean_part:
                continue

            # Check for reserved words
            if clean_part in reserved_words:
                msg = f"{path}: '{clean_part}' is a Python reserved word"
                violations["reserved_word_usage"].append(msg)

            # Check name length (reasonable limits)
            if len(clean_part) > 50:
                msg = f"{path}: '{clean_part}' is too long ({len(clean_part)} chars)"
                violations["length_violations"].append(msg)
            elif len(clean_part) < 2:
                msg = f"{path}: '{clean_part}' is too short"
                violations["length_violations"].append(msg)

            # Check for invalid characters
            if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", clean_part):
                msg = f"{path}: '{clean_part}' contains invalid characters"
                violations["character_violations"].append(msg)

            # Check naming conventions
            if "clk" in clean_part.lower() or "clock" in clean_part.lower():
                if not clean_part.lower().startswith("clk"):
                    msg = f"{path}: Clock signal '{clean_part}' should start with 'clk'"
                    violations["naming_violations"].append(msg)

            if "rst" in clean_part.lower() or "reset" in clean_part.lower():
                if not clean_part.lower().startswith("rst"):
                    msg = f"{path}: Reset signal '{clean_part}' should start with 'rst'"
                    violations["naming_violations"].append(msg)

    return violations


def find_unused_signals(
    hierarchy: Dict[str, type], exclude_patterns: Optional[List[str]] = None
) -> List[str]:
    """Find signals that appear to be unused based on naming patterns.

    Args:
    ----
        hierarchy: DUT hierarchy dictionary.
        exclude_patterns: List of glob patterns to exclude from unused detection.

    Returns:
    -------
        List of signal paths that appear unused.

    """
    import fnmatch

    if exclude_patterns is None:
        exclude_patterns = []

    # Mock usage analysis - in real implementation this would analyze actual usage
    usage_patterns = _analyze_signal_usage(hierarchy)

    unused_signals = []
    for path, obj_type in hierarchy.items():
        # Skip the root DUT
        if "." not in path:
            continue

        # Check if signal is in usage patterns
        if path not in usage_patterns:
            # Check if it matches any exclude pattern
            excluded = False
            signal_name = path.split(".")[-1]  # Get just the signal name
            for pattern in exclude_patterns:
                # Check both full path and signal name
                path_match = fnmatch.fnmatch(path, pattern)
                name_match = fnmatch.fnmatch(signal_name, pattern)
                if path_match or name_match:
                    excluded = True
                    break

            if not excluded:
                unused_signals.append(path)

    return unused_signals


def _analyze_signal_usage(hierarchy: Dict[str, type]) -> Dict[str, List[str]]:
    """Analyze signal usage patterns in the hierarchy.

    This function performs a comprehensive analysis of how signals are used
    throughout the design hierarchy to identify potential unused signals.

    Args:
    ----
        hierarchy: Dictionary mapping signal paths to their types.

    Returns:
    -------
        Dictionary mapping signal paths to lists of usage patterns.
        Usage patterns include: 'read', 'write', 'clock', 'reset', 'constant'

    """
    usage_patterns = {}

    # Analyze each signal in the hierarchy
    for signal_path, signal_type in hierarchy.items():
        patterns = []

        # Skip the root DUT object
        if "." not in signal_path:
            continue

        signal_name = signal_path.split(".")[-1].lower()

        # Detect clock signals
        if any(clk_pattern in signal_name for clk_pattern in ["clk", "clock", "ck"]):
            patterns.append("clock")
            patterns.append("read")  # Clock signals are typically read

        # Detect reset signals
        elif any(rst_pattern in signal_name for rst_pattern in ["rst", "reset", "res"]):
            patterns.append("reset")
            patterns.append("read")  # Reset signals are typically read

        # Detect input signals (typically read)
        elif any(in_pattern in signal_name for in_pattern in ["_in", "input", "req", "valid"]):
            patterns.append("read")

        # Detect output signals (typically written)
        elif any(out_pattern in signal_name for out_pattern in ["_out", "output", "ack", "ready"]):
            patterns.append("write")

        # Detect data signals (both read and write)
        elif any(data_pattern in signal_name for data_pattern in ["data", "addr", "address"]):
            patterns.append("read")
            patterns.append("write")

        # Detect enable/control signals
        elif any(
            ctrl_pattern in signal_name for ctrl_pattern in ["enable", "en", "ctrl", "control"]
        ):
            patterns.append("read")

        # Detect constant-like signals
        elif signal_name.isupper() or "const" in signal_name:
            patterns.append("constant")
            patterns.append("read")

        # Default pattern for unrecognized signals
        else:
            # Assume basic read/write capability for most signals
            patterns.append("read")

        # Store the patterns for this signal
        if patterns:
            usage_patterns[signal_path] = patterns

    return usage_patterns


def detect_naming_patterns(signal_names: List[str]) -> Dict[str, List[str]]:
    """Detect common naming patterns in signal names.

    Args:
    ----
        signal_names: List of signal names to analyze.

    Returns:
    -------
        Dictionary mapping pattern types to detected patterns.

    """
    patterns: Dict[str, List[str]] = {
        "clock_signals": [],
        "reset_signals": [],
        "input_signals": [],
        "output_signals": [],
        "bus_signals": [],
    }

    # Detect clock patterns
    clock_patterns = set()
    for name in signal_names:
        name_lower = name.lower()
        if "clk" in name_lower or "clock" in name_lower:
            # Extract the pattern
            if "clk" in name_lower:
                clock_patterns.add("clk")
            if "clock" in name_lower:
                clock_patterns.add("clock")
    patterns["clock_signals"] = list(clock_patterns)

    # Detect reset patterns
    reset_patterns = set()
    for name in signal_names:
        name_lower = name.lower()
        if "rst" in name_lower or "reset" in name_lower:
            if "rst" in name_lower:
                reset_patterns.add("rst")
            if "reset" in name_lower:
                reset_patterns.add("reset")
    patterns["reset_signals"] = list(reset_patterns)

    # Detect input/output patterns
    input_patterns = set()
    output_patterns = set()
    for name in signal_names:
        name_lower = name.lower()
        if "in" in name_lower or "input" in name_lower:
            if "_in" in name_lower or "in_" in name_lower:
                input_patterns.add("in")
            if "input" in name_lower:
                input_patterns.add("input")
        if "out" in name_lower or "output" in name_lower:
            if "_out" in name_lower or "out_" in name_lower:
                output_patterns.add("out")
            if "output" in name_lower:
                output_patterns.add("output")
    patterns["input_signals"] = list(input_patterns)
    patterns["output_signals"] = list(output_patterns)

    # Detect bus patterns
    bus_patterns = set()
    for name in signal_names:
        name_lower = name.lower()
        # Look for common bus prefixes
        for bus_type in ["axi", "ahb", "apb", "pci", "usb", "spi", "i2c"]:
            if bus_type in name_lower:
                bus_patterns.add(bus_type)
    patterns["bus_signals"] = list(bus_patterns)

    return patterns


def suggest_signal_groupings(
    signal_names: List[str], group_by: str = "prefix", min_group_size: int = 2
) -> Dict[str, List[str]]:
    """Suggest logical groupings for signals based on naming patterns.

    Args:
    ----
        signal_names: List of signal names to group.
        group_by: Grouping strategy ('prefix', 'suffix', 'function').
        min_group_size: Minimum number of signals required for a group.

    Returns:
    -------
        Dictionary mapping group names to lists of signal names.

    """
    groupings: Dict[str, List[str]] = {}

    if group_by == "prefix":
        # Group by common prefixes
        prefix_groups: Dict[str, List[str]] = {}
        for name in signal_names:
            # Extract prefix (everything before first underscore)
            if "_" in name:
                prefix = name.split("_")[0]
                if prefix not in prefix_groups:
                    prefix_groups[prefix] = []
                prefix_groups[prefix].append(name)

        # Filter by minimum group size
        for prefix, signals in prefix_groups.items():
            if len(signals) >= min_group_size:
                groupings[prefix] = signals

    elif group_by == "function":
        # Group by functional similarity
        functional_groups: Dict[str, List[str]] = {
            "clock_signals": [],
            "reset_signals": [],
            "data_signals": [],
            "control_signals": [],
            "interrupt_signals": [],
        }

        for name in signal_names:
            name_lower = name.lower()
            if "clk" in name_lower or "clock" in name_lower:
                functional_groups["clock_signals"].append(name)
            elif "rst" in name_lower or "reset" in name_lower:
                functional_groups["reset_signals"].append(name)
            elif "data" in name_lower or "addr" in name_lower:
                functional_groups["data_signals"].append(name)
            elif "irq" in name_lower or "int" in name_lower:
                functional_groups["interrupt_signals"].append(name)
            else:
                functional_groups["control_signals"].append(name)

        # Filter by minimum group size
        for group_name, signals in functional_groups.items():
            if len(signals) >= min_group_size:
                groupings[group_name] = signals

    return groupings


def validate_hierarchy_structure(hierarchy: Dict[str, type], max_depth: int = 20) -> Dict[str, Any]:
    """Validate the structure of a DUT hierarchy.

    Args:
    ----
        hierarchy: DUT hierarchy dictionary.
        max_depth: Maximum allowed hierarchy depth.

    Returns:
    -------
        Dictionary containing validation results.

    """
    validation: Dict[str, Any] = {
        "is_valid": True,
        "has_root": False,
        "max_depth": 0,
        "orphaned_signals": [],
        "issues": [],
    }

    # Check for root element
    root_candidates = [path for path in hierarchy.keys() if "." not in path]
    if len(root_candidates) == 1:
        validation["has_root"] = True
        root_name = root_candidates[0]
    elif len(root_candidates) > 1:
        # Multiple roots - this is invalid
        validation["is_valid"] = False
        validation["has_root"] = False
        issues_list = validation["issues"]
        if isinstance(issues_list, list):
            issues_list.append(f"Multiple root elements found: {root_candidates}")
        return validation
    else:
        validation["is_valid"] = False
        validation["has_root"] = False
        issues_list = validation["issues"]
        if isinstance(issues_list, list):
            issues_list.append("No root element found in hierarchy")
        return validation

    # Calculate maximum depth and find orphaned signals
    for path in hierarchy.keys():
        depth = path.count(".")
        current_max = validation["max_depth"]
        if isinstance(current_max, int):
            validation["max_depth"] = max(current_max, depth)

        # Check if signal is properly connected to root
        if "." in path and not path.startswith(root_name + "."):
            orphaned_list = validation["orphaned_signals"]
            if isinstance(orphaned_list, list):
                orphaned_list.append(path)

    # Check depth limit
    max_depth_val = validation["max_depth"]
    if isinstance(max_depth_val, int) and max_depth_val > max_depth:
        validation["is_valid"] = False
        issues_list = validation["issues"]
        if isinstance(issues_list, list):
            msg = f"Hierarchy depth {max_depth_val} exceeds limit {max_depth}"
            issues_list.append(msg)

    # Check for orphaned signals
    orphaned_list = validation["orphaned_signals"]
    if isinstance(orphaned_list, list) and orphaned_list:
        validation["is_valid"] = False
        issues_list = validation["issues"]
        if isinstance(issues_list, list):
            issues_list.append(f"Found {len(orphaned_list)} orphaned signals")

    return validation


def analyze_hierarchy(hierarchy: Dict[str, type]) -> Dict[str, Any]:
    """Analyze a hierarchy dictionary to extract useful information.

    This function analyzes a hierarchy dictionary (as returned by discover_hierarchy)
    to extract useful information about the design structure, signal types, arrays,
    and other patterns.

    Args:
    ----
        hierarchy: Dictionary mapping paths to types.

    Returns:
    -------
        Dictionary containing analysis results including:
        - total_objects: Total number of objects in hierarchy
        - max_depth: Maximum depth of hierarchy
        - signal_types: Dictionary mapping signal types to counts
        - arrays: Dictionary of array information
        - patterns: Dictionary of detected design patterns
        - naming_conventions: Dictionary of naming convention analysis
        - structure: Dictionary of hierarchy structure analysis
        - unused_signals: List of potentially unused signals

    """
    # Get basic statistics
    total_objects = len(hierarchy)
    max_depth = max(path.count(".") for path in hierarchy.keys()) if hierarchy else 0

    # Analyze signal types
    signal_types: Dict[str, int] = {}
    for path, obj_type in hierarchy.items():
        type_name = obj_type.__name__
        signal_types[type_name] = signal_types.get(type_name, 0) + 1

    # Find arrays and their patterns
    arrays: Dict[str, Dict[str, Any]] = {}
    for path, obj_type in hierarchy.items():
        array_match = re.match(r"^(.+)\[(\d+)\]$", path)
        if array_match:
            base_path = array_match.group(1)
            index = int(array_match.group(2))
            if base_path not in arrays:
                arrays[base_path] = {
                    "indices": set(),
                    "element_type": obj_type,
                    "max_index": index,
                    "min_index": index,
                }
            array_data = arrays[base_path]
            indices_set = array_data["indices"]
            if isinstance(indices_set, set):
                indices_set.add(index)
            max_index = array_data["max_index"]
            if isinstance(max_index, int):
                array_data["max_index"] = max(max_index, index)
            min_index = array_data["min_index"]
            if isinstance(min_index, int):
                array_data["min_index"] = min(min_index, index)

    # For design patterns and naming conventions, we need a mock DUT object
    # since these functions expect a DUT object, not a hierarchy dict
    from unittest.mock import Mock
    mock_dut = Mock()
    mock_dut._name = "dut"
    
    # Temporarily patch the discover_hierarchy function to return our hierarchy
    from . import core
    original_discover = core.discover_hierarchy
    
    def mock_discover_hierarchy(dut: Any, **kwargs: Any) -> Dict[str, type]:
        return hierarchy
    
    try:
        # Temporarily replace the function
        core.discover_hierarchy = mock_discover_hierarchy  # type: ignore[assignment]
        
        # Detect design patterns
        patterns = detect_design_patterns(mock_dut)

        # Analyze naming conventions  
        naming_conventions = validate_naming_conventions(mock_dut)
    finally:
        # Restore original function
        core.discover_hierarchy = original_discover

    # Analyze hierarchy structure
    structure = validate_hierarchy_structure(hierarchy)

    # Find potentially unused signals
    unused = find_unused_signals(hierarchy)

    return {
        "total_objects": total_objects,
        "max_depth": max_depth,
        "signal_types": signal_types,
        "arrays": arrays,
        "patterns": patterns,
        "naming_conventions": naming_conventions,
        "structure": structure,
        "unused_signals": unused,
    }
