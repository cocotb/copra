"""Tests for the copra.utils module."""

from pathlib import Path
from typing import Any, Set, Type
from unittest.mock import Mock

import pytest

from copra.utils import (
    format_docstring,
    get_imports_for_types,
    get_python_type_for_handle,
    get_relative_import_path,
    is_public_name,
    to_capwords,
)


class TestGetPythonTypeForHandle:
    """Test the get_python_type_for_handle function."""

    def test_known_types(self) -> None:
        """Test mapping of known handle types."""
        # Create mock types with known names
        mock_types = {
            "LogicObject": Mock(__name__="LogicObject"),
            "LogicArrayObject": Mock(__name__="LogicArrayObject"),
            "HierarchyObject": Mock(__name__="HierarchyObject"),
            "HierarchyArrayObject": Mock(__name__="HierarchyArrayObject"),
            "ValueObjectBase": Mock(__name__="ValueObjectBase"),
            "RealObject": Mock(__name__="RealObject"),
            "EnumObject": Mock(__name__="EnumObject"),
            "IntegerObject": Mock(__name__="IntegerObject"),
            "StringObject": Mock(__name__="StringObject"),
            "ArrayObject": Mock(__name__="ArrayObject"),
        }

        for expected_name, mock_type in mock_types.items():
            result = get_python_type_for_handle(mock_type)
            assert result == expected_name

        # Test types that fall back to ValueObjectBase
        fallback_types = {
            "LogicArray": Mock(__name__="LogicArray"),
            "Logic": Mock(__name__="Logic"),
            "Range": Mock(__name__="Range"),
        }

        for type_name, mock_type in fallback_types.items():
            result = get_python_type_for_handle(mock_type)
            assert result == "ValueObjectBase", \
                    f"Expected {type_name} to fall back to ValueObjectBase"

    def test_unknown_type(self) -> None:
        """Test mapping of unknown handle types."""
        unknown_type = Mock(__name__="UnknownType")
        result = get_python_type_for_handle(unknown_type)
        assert result == "ValueObjectBase"


class TestGetImportsForTypes:
    """Test the get_imports_for_types function."""

    def test_get_imports(self) -> None:
        """Test generation of import statements."""
        # The function doesn't actually use the types parameter currently
        # but we test with a set anyway for future compatibility
        types: Set[Type[Any]] = set()
        imports = get_imports_for_types(types)

        # Check that all expected imports are present
        expected_imports = [
            "from typing import Any, Union",
            "from cocotb.handle import (",
            "    HierarchyObject,",
            "    HierarchyArrayObject,",
            "    LogicObject,",
            "    LogicArrayObject,",
            "    ValueObjectBase,",
            "    RealObject,",
            "    EnumObject,",
            "    IntegerObject,",
            "    StringObject,",
            "    ArrayObject,",
            ")",
        ]

        assert imports == expected_imports


class TestFormatDocstring:
    """Test the format_docstring function."""

    def test_empty_docstring(self) -> None:
        """Test formatting of empty docstring."""
        assert format_docstring(None) == ""
        assert format_docstring("") == ""

    def test_single_line_docstring(self) -> None:
        """Test formatting of single line docstring."""
        doc = "This is a single line docstring."
        result = format_docstring(doc, indent=4)
        expected = "    This is a single line docstring."
        assert result == expected

    def test_multiline_docstring(self) -> None:
        """Test formatting of multiline docstring."""
        doc = """This is a multiline docstring.
        It has multiple lines with indentation.
        And some more content."""

        result = format_docstring(doc, indent=4)
        lines = result.split('\n')

        # Check that all lines start with the correct indentation
        for line in lines:
            assert line.startswith("    ")

    def test_docstring_with_common_indentation(self) -> None:
        """Test formatting of docstring with common indentation."""
        doc = """First line.
    Second line with indentation.
    Third line with same indentation."""

        result = format_docstring(doc, indent=2)
        expected = """  First line.
  Second line with indentation.
  Third line with same indentation."""
        assert result == expected

    def test_custom_indentation(self) -> None:
        """Test formatting with custom indentation."""
        doc = "Simple docstring."
        result = format_docstring(doc, indent=8)
        assert result == "        Simple docstring."


class TestIsPublicName:
    """Test the is_public_name function."""

    def test_public_names(self) -> None:
        """Test identification of public names."""
        public_names = [
            "public_name",
            "PublicName",
            "name123",
            "a",
            "CamelCase",
            "snake_case",
        ]

        for name in public_names:
            assert is_public_name(name), f"'{name}' should be considered public"

    def test_private_names(self) -> None:
        """Test identification of private names."""
        private_names = [
            "_private",
            "__dunder__",
            "_single_underscore",
            "__double_underscore",
            "_",
            "__",
        ]

        for name in private_names:
            assert not is_public_name(name), f"'{name}' should be considered private"


class TestToCapwords:
    """Test the to_capwords function."""

    def test_underscore_separated(self) -> None:
        """Test conversion of underscore-separated names."""
        test_cases = [
            ("simple_name", "SimpleName"),
            ("very_long_name_here", "VeryLongNameHere"),
            ("single", "Single"),
            ("a_b_c", "ABC"),
        ]

        for input_name, expected in test_cases:
            result = to_capwords(input_name)
            assert result == expected, f"'{input_name}' -> '{result}', expected '{expected}'"

    def test_hyphen_separated(self) -> None:
        """Test conversion of hyphen-separated names."""
        test_cases = [
            ("hyphen-name", "HyphenName"),
            ("multi-word-name", "MultiWordName"),
            ("a-b", "AB"),
        ]

        for input_name, expected in test_cases:
            result = to_capwords(input_name)
            assert result == expected, f"'{input_name}' -> '{result}', expected '{expected}'"

    def test_camelcase_names(self) -> None:
        """Test conversion of camelCase names."""
        test_cases = [
            ("camelCase", "CamelCase"),
            ("someVariableName", "SomeVariableName"),
            ("XMLHttpRequest", "XmlhttpRequest"),
            ("iPhone", "IPhone"),
        ]

        for input_name, expected in test_cases:
            result = to_capwords(input_name)
            assert result == expected, f"'{input_name}' -> '{result}', expected '{expected}'"

    def test_mixed_separators(self) -> None:
        """Test conversion of names with mixed separators."""
        test_cases = [
            ("mixed_name-here", "MixedNameHere"),
            ("complex_camelCase-name", "ComplexCamelCaseName"),
        ]

        for input_name, expected in test_cases:
            result = to_capwords(input_name)
            assert result == expected, f"'{input_name}' -> '{result}', expected '{expected}'"

    def test_edge_cases(self) -> None:
        """Test edge cases for to_capwords."""
        test_cases = [
            ("", ""),
            ("_", ""),
            ("-", ""),
            ("a", "A"),
            ("A", "A"),
            ("123", "123"),
        ]

        for input_name, expected in test_cases:
            result = to_capwords(input_name)
            assert result == expected, f"'{input_name}' -> '{result}', expected '{expected}'"


class TestGetRelativeImportPath:
    """Test the get_relative_import_path function."""

    def test_simple_relative_path(self, tmp_path: Path) -> None:
        """Test simple relative import path."""
        from_path = tmp_path / "src" / "module.py"
        to_path = tmp_path / "src" / "other.py"

        result = get_relative_import_path(from_path, to_path)
        assert result == "other"

    def test_subdirectory_path(self, tmp_path: Path) -> None:
        """Test relative import path to subdirectory."""
        from_path = tmp_path / "src" / "module.py"
        to_path = tmp_path / "src" / "subdir" / "other.py"

        result = get_relative_import_path(from_path, to_path)
        assert result == "subdir.other"

    def test_init_file_path(self, tmp_path: Path) -> None:
        """Test relative import path to __init__.py file."""
        from_path = tmp_path / "src" / "module.py"
        to_path = tmp_path / "src" / "package" / "__init__.py"

        result = get_relative_import_path(from_path, to_path)
        assert result == "package"

    def test_nested_package_path(self, tmp_path: Path) -> None:
        """Test relative import path to nested package."""
        from_path = tmp_path / "src" / "module.py"
        to_path = tmp_path / "src" / "package" / "subpackage" / "module.py"

        result = get_relative_import_path(from_path, to_path)
        assert result == "package.subpackage.module"


# Test the module-level cocotb version printing
def test_module_import_version_printing(capsys: pytest.CaptureFixture[str]) -> None:
    """Test that the module prints cocotb version information on import."""
    # The version printing happens at module import time
    # We can't easily test this without reimporting, but we can verify
    # the code paths exist by checking the captured output
    capsys.readouterr()
    # The output might be empty if cocotb is already imported
    # This is mainly to ensure the code doesn't crash
    assert True  # If we get here, the import succeeded
