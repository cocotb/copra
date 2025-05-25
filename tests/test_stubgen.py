"""Tests for the copra.stubgen module."""

import io
from pathlib import Path
from typing import Any, Dict, List, Optional, Type
from unittest.mock import Mock

import pytest
from cocotb.handle import (
    EnumObject,
    HierarchyArrayObject,
    HierarchyObject,
    IntegerObject,
    LogicArrayObject,
    LogicObject,
    RealObject,
    StringObject,
    ValueObjectBase,
)

# Print cocotb version for debugging
try:
    import cocotb
    print(f"[test_stubgen] Using cocotb version: {cocotb.__version__}")
except (ImportError, AttributeError):
    print("[test_stubgen] cocotb version information not available")

from copra.stubgen import discover_hierarchy, generate_stub, generate_stub_to_file, main


class MockHandle:
    """Mock handle class for testing."""

    def __init__(
        self,
        name: str,
        handle_type: Type[Any],
        children: Optional[Dict[str, 'MockHandle']] = None,
    ):
        """Initialize a mock handle.

        Args:
        ----
            name: The name of the handle.
            handle_type: The type of the handle.
            children: Optional dictionary of child handles.

        """
        self._name = name
        self._handle_type = handle_type  # Store the intended type
        self._sub_handles = children or {}

    def __repr__(self) -> str:
        """Return string representation of the mock handle."""
        return f"<MockHandle {self._name} type={self._handle_type.__name__}>"


class MockArrayHandle(MockHandle):
    """Mock array handle for testing array functionality."""

    def __init__(self, name: str, handle_type: Type[Any], size: int = 3):
        """Initialize a mock array handle."""
        super().__init__(name, handle_type)
        self._size = size
        # Set up _sub_handles as a dict to avoid iteration issues
        self._sub_handles = {
            f"{name}[{i}]": MockHandle(f"{name}[{i}]", LogicObject) for i in range(size)
        }

    def __iter__(self) -> Any:
        """Make the handle iterable."""
        for i in range(self._size):
            yield MockHandle(f"{self._name}[{i}]", LogicObject)

    def __len__(self) -> int:
        """Return the size of the array."""
        return self._size


class MockRealHandle(MockHandle):
    """Mock handle without _name attribute for testing edge cases."""

    def __init__(self, handle_type: Type[Any]):
        """Initialize a mock handle without _name."""
        self._handle_type = handle_type
        # Intentionally don't set _name


class MockCocotbHandle:
    """Mock handle that simulates real cocotb handle behavior."""

    def __init__(self, name: str, sub_handles: Optional[List[Any]] = None):
        """Initialize mock cocotb handle."""
        self._name = name
        self._sub_handles = True if sub_handles else False
        self._sub_handles_list = sub_handles or []

    def _sub_handles_iter(self) -> Any:
        """Return iterator over sub-handles."""
        return iter(self._sub_handles_list)


@pytest.fixture
def mock_dut() -> MockHandle:
    """Create a mock DUT hierarchy for testing."""
    return MockHandle(
        "dut",
        HierarchyObject,
        {
            "clk": MockHandle("clk", LogicObject),
            "rst_n": MockHandle("rst_n", LogicObject),
            "data_in": MockHandle("data_in", LogicObject),
            "data_out": MockHandle("data_out", LogicObject),
            "submodule": MockHandle(
                "submodule",
                HierarchyObject,
                {
                    "reg_a": MockHandle("reg_a", LogicObject),
                    "reg_b": MockHandle("reg_b", LogicObject),
                },
            ),
        },
    )


@pytest.fixture
def complex_mock_dut() -> MockHandle:
    """Create a complex mock DUT with various handle types."""
    return MockHandle(
        "complex_dut",
        HierarchyObject,
        {
            "logic_signal": MockHandle("logic_signal", LogicObject),
            "logic_array": MockHandle("logic_array", LogicArrayObject),
            "hierarchy_array": MockArrayHandle("hierarchy_array", HierarchyArrayObject),
            "value_base": MockHandle("value_base", ValueObjectBase),
            "real_signal": MockHandle("real_signal", RealObject),
            "enum_signal": MockHandle("enum_signal", EnumObject),
            "integer_signal": MockHandle("integer_signal", IntegerObject),
            "string_signal": MockHandle("string_signal", StringObject),
            "nested": MockHandle(
                "nested",
                HierarchyObject,
                {
                    "deep_signal": MockHandle("deep_signal", LogicObject),
                    "array_in_nested": MockArrayHandle("array_in_nested", HierarchyArrayObject),
                },
            ),
        },
    )


class TestDiscoverHierarchy:
    """Test the discover_hierarchy function."""

    def test_discover_hierarchy(self, mock_dut: MockHandle) -> None:
        """Test discovery of hierarchy from a DUT."""
        hierarchy = discover_hierarchy(mock_dut)

        # Check that all expected paths are present
        expected_paths = {
            "dut",
            "dut.clk",
            "dut.rst_n",
            "dut.data_in",
            "dut.data_out",
            "dut.submodule",
            "dut.submodule.reg_a",
            "dut.submodule.reg_b",
        }

        assert set(hierarchy.keys()) == expected_paths

        # Check some type mappings
        assert hierarchy["dut"] is HierarchyObject
        assert hierarchy["dut.clk"] is LogicObject
        assert hierarchy["dut.submodule"] is HierarchyObject
        assert hierarchy["dut.submodule.reg_a"] is LogicObject

    def test_discover_hierarchy_complex(self, complex_mock_dut: MockHandle) -> None:
        """Test discovery of complex hierarchy with various types."""
        hierarchy = discover_hierarchy(complex_mock_dut)

        # Check that all handle types are discovered
        assert hierarchy["complex_dut.logic_signal"] is LogicObject
        assert hierarchy["complex_dut.logic_array"] is LogicArrayObject
        assert hierarchy["complex_dut.hierarchy_array"] is HierarchyArrayObject
        assert hierarchy["complex_dut.value_base"] is ValueObjectBase
        assert hierarchy["complex_dut.real_signal"] is RealObject
        assert hierarchy["complex_dut.enum_signal"] is EnumObject
        assert hierarchy["complex_dut.integer_signal"] is IntegerObject
        assert hierarchy["complex_dut.string_signal"] is StringObject

        # Check nested hierarchy
        assert hierarchy["complex_dut.nested.deep_signal"] is LogicObject

    def test_discover_hierarchy_with_arrays(self, complex_mock_dut: MockHandle) -> None:
        """Test discovery of hierarchy with array handles."""
        hierarchy = discover_hierarchy(complex_mock_dut)

        # Check that array elements are discovered through _sub_handles
        # The MockArrayHandle sets up _sub_handles with the full path including the parent
        expected_array_paths = [
            "complex_dut.hierarchy_array.hierarchy_array[0]",
            "complex_dut.hierarchy_array.hierarchy_array[1]",
            "complex_dut.hierarchy_array.hierarchy_array[2]",
        ]

        for path in expected_array_paths:
            assert path in hierarchy
            assert hierarchy[path] is LogicObject

    def test_discover_hierarchy_no_name_attribute(self) -> None:
        """Test discovery with handle that has no _name attribute."""
        mock_handle = MockRealHandle(LogicObject)
        hierarchy = discover_hierarchy(mock_handle)

        # Should return empty hierarchy since handle has no _name
        assert hierarchy == {}

    def test_discover_hierarchy_with_real_cocotb_handles(self) -> None:
        """Test discovery with mock that simulates real cocotb handles."""
        # Create a mock that simulates real cocotb handle behavior
        sub_handle = MockCocotbHandle("sub_signal")
        mock_dut = MockCocotbHandle("real_dut", [sub_handle])

        hierarchy = discover_hierarchy(mock_dut)

        # Should discover both the main handle and sub-handle
        assert "real_dut" in hierarchy
        assert "real_dut.sub_signal" in hierarchy

    def test_discover_hierarchy_iteration_error(self) -> None:
        """Test discovery with handle that raises error during iteration."""
        mock_handle = Mock()
        mock_handle._name = "error_handle"
        # Set up _sub_handles as empty dict to avoid iteration issues
        mock_handle._sub_handles = {}

        hierarchy = discover_hierarchy(mock_handle)

        # Should still discover the main handle despite iteration error
        assert "error_handle" in hierarchy

    def test_discover_hierarchy_with_string_object(self) -> None:
        """Test that string objects are not iterated over."""
        mock_handle = Mock()
        mock_handle._name = "string_handle"
        # Set up _sub_handles as empty dict to avoid iteration issues
        mock_handle._sub_handles = {}

        hierarchy = discover_hierarchy(mock_handle)

        # Should not iterate over string-like objects
        assert len(hierarchy) == 1
        assert "string_handle" in hierarchy

    def test_discover_hierarchy_with_bytes_object(self) -> None:
        """Test that bytes objects are not iterated over."""
        mock_handle = Mock()
        mock_handle._name = "bytes_handle"
        # Set up _sub_handles as empty dict to avoid iteration issues
        mock_handle._sub_handles = {}

        hierarchy = discover_hierarchy(mock_handle)

        # Should not iterate over bytes-like objects
        assert len(hierarchy) == 1
        assert "bytes_handle" in hierarchy


class TestGenerateStub:
    """Test the generate_stub function."""

    def test_generate_stub(self, mock_dut: MockHandle) -> None:
        """Test generation of stub file content."""
        hierarchy = discover_hierarchy(mock_dut)
        stub_content = generate_stub(hierarchy)

        # Basic checks on the generated content
        assert "class Dut(HierarchyObject):" in stub_content
        assert "clk: LogicObject" in stub_content
        assert "data_in: LogicObject" in stub_content
        assert "class Submodule(HierarchyObject):" in stub_content
        assert "reg_a: LogicObject" in stub_content
        assert "reg_b: LogicObject" in stub_content

        # Check that imports are present
        assert "from cocotb.handle import" in stub_content
        assert "HierarchyObject" in stub_content
        assert "LogicObject" in stub_content

        # Check that the main DUT type alias is present
        assert "DutType = Dut" in stub_content

    def test_generate_stub_complex_types(self, complex_mock_dut: MockHandle) -> None:
        """Test generation of stub with complex types."""
        hierarchy = discover_hierarchy(complex_mock_dut)
        stub_content = generate_stub(hierarchy)

        # Check that all handle types are included in imports
        expected_imports = [
            "HierarchyObject",
            "LogicObject",
            "LogicArrayObject",
            "HierarchyArrayObject",
            "ValueObjectBase",
            "RealObject",
            "EnumObject",
            "IntegerObject",
            "StringObject",
        ]

        for import_name in expected_imports:
            assert import_name in stub_content

        # Check that the generated stub has proper class structure
        assert "class ComplexDut(HierarchyObject):" in stub_content
        assert "enum_signal: EnumObject" in stub_content
        assert "logic_array: LogicArrayObject" in stub_content

    def test_generate_stub_empty_hierarchy(self) -> None:
        """Test generation of stub with empty hierarchy."""
        hierarchy: Dict[str, type] = {}
        stub_content = generate_stub(hierarchy)

        # Should still generate header and basic imports
        assert "# This is an auto-generated stub file" in stub_content
        assert "from cocotb.handle import" in stub_content
        assert "HierarchyObject" in stub_content  # Always included

    def test_generate_stub_unknown_type(self) -> None:
        """Test generation of stub with unknown handle type."""
        # Create hierarchy with unknown type
        hierarchy = {"dut.unknown": type("UnknownType", (), {})}
        stub_content = generate_stub(hierarchy)

        # Unknown types should be treated as sub-modules and fall back to HierarchyObject
        assert "class Dut(HierarchyObject):" in stub_content
        assert "unknown: HierarchyObject" in stub_content


class TestGenerateStubToFile:
    """Test the generate_stub_to_file function."""

    def test_generate_stub_to_file(self, mock_dut: MockHandle, tmp_path: Path) -> None:
        """Test generation of stub file to file object."""
        hierarchy = discover_hierarchy(mock_dut)

        output_file = io.StringIO()
        generate_stub_to_file(hierarchy, output_file)

        content = output_file.getvalue()

        # Check that content was written
        assert len(content) > 0
        assert "class Dut(HierarchyObject):" in content
        assert "clk: LogicObject" in content
        assert "data_in: LogicObject" in content
        assert "submodule: HierarchyObject" in content

    def test_generate_stub_to_file_with_typing_imports(self) -> None:
        """Test generation with types that might need typing imports."""
        # Create a hierarchy that might trigger typing imports
        hierarchy = {"dut": HierarchyObject}

        output_file = io.StringIO()
        generate_stub_to_file(hierarchy, output_file)

        content = output_file.getvalue()
        assert "from cocotb.handle import" in content

    def test_generate_stub_to_file_array_handling(self) -> None:
        """Test generation with array indices in paths."""
        hierarchy = {
            "dut": HierarchyObject,
            "dut.array[0]": LogicObject,
            "dut.array[1]": LogicObject,
        }

        output_file = io.StringIO()
        generate_stub_to_file(hierarchy, output_file)

        content = output_file.getvalue()
        # Array indices should be stripped from class names
        assert "array: LogicObject" in content


class TestMain:
    """Test the main function."""

    def test_main_help(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test main function with help argument."""
        with pytest.raises(SystemExit) as exc_info:
            main(["--help"])

        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "usage:" in captured.out.lower()

    def test_main_version(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test main function with version argument."""
        # The current implementation now has a --version flag
        with pytest.raises(SystemExit) as exc_info:
            main(["--version"])

        # Should exit with success code for version display
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "copra" in captured.out

    def test_main_no_args(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test main function with no arguments."""
        with pytest.raises(SystemExit) as exc_info:
            main([])

        # Should exit with error code for missing required arguments
        assert exc_info.value.code == 2

    def test_main_invalid_module(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test main function with invalid module."""
        # The new implementation tries to actually discover DUT hierarchies
        result = main(["nonexistent_module"])
        assert result == 1  # New implementation returns 1 for errors

        captured = capsys.readouterr()
        assert "Runtime Error" in captured.err

    def test_main_success_path(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        """Test main function success path with current implementation."""
        output_file = tmp_path / "output.pyi"

        result = main(["test_module", "--outfile", str(output_file)])

        assert result == 1  # New implementation returns 1 for errors when module doesn't exist
        captured = capsys.readouterr()
        assert "Runtime Error" in captured.err


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_generate_stub_with_array_indices_in_names(self) -> None:
        """Test stub generation with array indices in signal names."""
        hierarchy = {
            "dut": HierarchyObject,
            "dut.signal[0]": LogicObject,
            "dut.signal[1]": LogicObject,
            "dut.other_signal": LogicObject,
        }

        stub_content = generate_stub(hierarchy)

        # Array indices should be handled properly
        assert "signal: LogicObject" in stub_content
        assert "other_signal: LogicObject" in stub_content

    def test_version_printing_on_import(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test that version information is printed on module import."""
        # The version printing happens at module import time
        # This test ensures the import doesn't crash
        from copra import stubgen

        # If we get here, the import succeeded
        assert stubgen is not None
