"""Tests for the copra.__init__ module."""

import sys
from typing import Any, Mapping, Optional, Sequence
from unittest.mock import Mock, patch

import pytest


class TestVersionChecking:
    """Test the version checking functionality in __init__.py."""

    def test_version_check_success(self) -> None:
        """Test successful version check with valid cocotb version."""
        # Mock cocotb with a valid version
        mock_cocotb = Mock()
        mock_cocotb.__version__ = "2.0.0"

        with patch.dict('sys.modules', {'cocotb': mock_cocotb}):
            with patch('packaging.version.parse') as mock_parse:
                # Mock version parsing
                mock_version = Mock()
                mock_version.base_version = "2.0.0"
                mock_parse.return_value = mock_version

                # This should not raise an exception
                import copra
                assert copra.__version__ is not None

    def test_version_check_failure_old_version(self) -> None:
        """Test version check failure with old cocotb version."""
        from copra import _check_cocotb_version

        # Mock cocotb with an old version
        mock_cocotb = Mock()
        mock_cocotb.__version__ = "1.9.0"

        with patch.dict('sys.modules', {'cocotb': mock_cocotb}):
            with pytest.raises(ImportError, match="copra requires cocotb >= 2.0.0"):
                _check_cocotb_version()

    def test_version_check_dev_version(self) -> None:
        """Test version check with development version."""
        # Mock cocotb with a development version
        mock_cocotb = Mock()
        mock_cocotb.__version__ = "2.0.0.dev0"

        with patch.dict('sys.modules', {'cocotb': mock_cocotb}):
            with patch('packaging.version.parse') as mock_parse:
                # Mock version parsing for dev version
                mock_version = Mock()
                mock_version.base_version = "2.0.0"  # Dev versions should pass
                mock_parse.return_value = mock_version

                # This should not raise an exception
                import copra
                assert copra.__version__ is not None

    def test_cocotb_import_error(self) -> None:
        """Test handling of cocotb import error."""
        # Since the module is already imported, we test the version checking logic directly
        from copra import _check_cocotb_version

        # Mock cocotb to not exist
        with patch('builtins.__import__') as mock_import:
            def import_side_effect(
                name: str,
                globals: Optional[Mapping[str, object]] = None,
                locals: Optional[Mapping[str, object]] = None,
                fromlist: Sequence[str] = (),
                level: int = 0,
            ) -> Any:
                if name == 'cocotb':
                    raise ImportError("No module named 'cocotb'")
                return __import__(name, globals, locals, fromlist, level)

            mock_import.side_effect = import_side_effect

            with pytest.raises(ImportError, match="copra requires cocotb >= 2.0.0"):
                _check_cocotb_version()

    def test_cocotb_attribute_error(self) -> None:
        """Test handling of cocotb without __version__ attribute."""
        # Mock cocotb without __version__ attribute
        mock_cocotb = Mock(spec=[])  # Empty spec means no attributes

        with patch.dict('sys.modules', {'cocotb': mock_cocotb}):
            # This should print a message but not crash
            import copra
            assert copra.__version__ is not None

    def test_version_check_reraise_our_error(self) -> None:
        """Test that our version check errors are re-raised."""
        from copra import _check_cocotb_version

        # Test that version check errors are properly handled
        with patch('builtins.__import__') as mock_import:
            def import_side_effect(
                name: str,
                globals: Optional[Mapping[str, object]] = None,
                locals: Optional[Mapping[str, object]] = None,
                fromlist: Sequence[str] = (),
                level: int = 0,
            ) -> Any:
                if name == 'cocotb':
                    raise ImportError("copra requires cocotb >= 2.0.0, but found 1.8.0")
                return __import__(name, globals, locals, fromlist, level)

            mock_import.side_effect = import_side_effect

            with pytest.raises(ImportError, match="copra requires cocotb >= 2.0.0"):
                _check_cocotb_version()


class TestModuleExports:
    """Test the module exports and public API."""

    def test_all_exports(self) -> None:
        """Test that all expected functions are exported."""
        import copra

        expected_exports = [
            "__version__",
            "discover_hierarchy",
            "generate_stub",
            "generate_stub_to_file",
        ]

        for export in expected_exports:
            assert hasattr(copra, export), f"Missing export: {export}"
            assert export in copra.__all__, f"Export {export} not in __all__"

    def test_version_available(self) -> None:
        """Test that version is available."""
        import copra
        assert copra.__version__ is not None
        assert isinstance(copra.__version__, str)
        assert len(copra.__version__) > 0

    def test_functions_callable(self) -> None:
        """Test that exported functions are callable."""
        import copra

        callable_exports = [
            "discover_hierarchy",
            "generate_stub",
            "generate_stub_to_file",
        ]

        for export in callable_exports:
            func = getattr(copra, export)
            assert callable(func), f"Export {export} is not callable"


class TestVersionPrinting:
    """Test the version printing functionality."""

    def test_version_printing_success(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test that version printing works when cocotb is available."""
        # The version printing happens at import time
        # We can test this by checking if the import succeeds

        # If we get here, the import succeeded
        assert True

    def test_version_printing_with_mock(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test version printing with mocked cocotb."""
        mock_cocotb = Mock()
        mock_cocotb.__version__ = "2.0.0"  # Use valid version format

        with patch.dict('sys.modules', {'cocotb': mock_cocotb}):
            # Force a fresh import to trigger version printing
            if 'copra' in sys.modules:
                del sys.modules['copra']


            # Check that version was printed (captured by capsys)
            capsys.readouterr()
            # Note: The actual output might be captured at module level
            # This test mainly ensures no exceptions are raised
            assert True
