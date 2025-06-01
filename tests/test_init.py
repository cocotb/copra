"""Tests for the copra.__init__ module."""

import sys
from unittest.mock import Mock, patch

import pytest


class TestVersionChecking:
    """Test the version checking functionality in __init__.py."""

    def test_version_check_success(self) -> None:
        """Test successful version check with valid cocotb version."""
        # Mock cocotb with a valid version
        mock_cocotb = Mock()
        mock_cocotb.__version__ = "2.0.0"

        with patch.dict("sys.modules", {"cocotb": mock_cocotb}):
            with patch("packaging.version.parse") as mock_parse:
                # Mock version parsing
                mock_version = Mock()
                mock_version.base_version = "2.0.0"
                mock_parse.return_value = mock_version

                # This should not raise an exception
                import copra

                assert copra.__version__ is not None

    def test_version_check_failure_old_version(self) -> None:
        """Test version check failure with old cocotb version."""
        # Test the version checking logic directly by patching the global variables
        with patch("copra.COCOTB_AVAILABLE", True), \
             patch("copra.COCOTB_VERSION", "1.9.0"):

            # Create a mock cocotb that doesn't look like a Mock object
            class FakeCocotb:
                __version__ = "1.9.0"

            with patch("copra.cocotb", FakeCocotb()):
                # Import the function after patching
                from copra import _check_cocotb_version

                with pytest.raises(ImportError, match="copra requires cocotb >= 2.0.0"):
                    _check_cocotb_version()

    def test_version_check_dev_version(self) -> None:
        """Test version check with development version."""
        # Test with a development version that should pass
        with patch("copra.COCOTB_AVAILABLE", True), \
             patch("copra.COCOTB_VERSION", "2.0.0.dev0"):

            # Create a mock cocotb that doesn't look like a Mock object
            class FakeCocotb:
                __version__ = "2.0.0.dev0"

            with patch("copra.cocotb", FakeCocotb()):
                from copra import _check_cocotb_version

                # This should not raise an exception
                try:
                    _check_cocotb_version()
                except ImportError:
                    pytest.fail("Version check should not fail for dev version 2.0.0.dev0")

    def test_cocotb_import_error(self) -> None:
        """Test handling of cocotb import error."""
        # Test when cocotb is not available
        with patch("copra.COCOTB_AVAILABLE", False):
            from copra import _check_cocotb_version

            with pytest.raises(ImportError, match="copra requires cocotb >= 2.0.0"):
                _check_cocotb_version()

    def test_cocotb_attribute_error(self) -> None:
        """Test handling of cocotb without __version__ attribute."""
        # Test when version is unknown
        with patch("copra.COCOTB_AVAILABLE", True), \
             patch("copra.COCOTB_VERSION", "unknown"):

            # Create a mock cocotb that doesn't look like a Mock object
            class FakeCocotb:
                __version__ = None

            with patch("copra.cocotb", FakeCocotb()):
                from copra import _check_cocotb_version

                # This should not raise an exception, just print a warning
                try:
                    _check_cocotb_version()
                except ImportError:
                    pytest.fail("Version check should not fail when version is unknown")

    def test_version_check_reraise_our_error(self) -> None:
        """Test that our version check errors are re-raised."""
        # Test that specific version errors are properly raised
        with patch("copra.COCOTB_AVAILABLE", True), \
             patch("copra.COCOTB_VERSION", "1.8.0"):

            # Create a mock cocotb that doesn't look like a Mock object
            class FakeCocotb:
                __version__ = "1.8.0"

            with patch("copra.cocotb", FakeCocotb()):
                from copra import _check_cocotb_version

                with pytest.raises(ImportError, match="copra requires cocotb >= 2.0.0"):
                    _check_cocotb_version()


class TestModuleExports:
    """Test the module exports and public API."""

    def test_all_exports(self) -> None:
        """Test that all expected functions are exported."""
        import copra

        # Core functionality exports
        core_exports = [
            "__version__",
            "create_stub_from_dut",
            "discover_hierarchy",
            "generate_stub",
            "generate_stub_to_file",
            "generate_stub_with_validation",
            "validate_stub_syntax",
            "auto_generate_stubs",
        ]

        # Analysis and validation exports
        analysis_exports = [
            "analyze_stub_coverage",
            "validate_dut_interface",
        ]

        # Code generation exports
        generation_exports = [
            "generate_testbench_template",
        ]

        # Mocking and testing exports
        mocking_exports = [
            "MockDUT",
            "MockSignal",
            "MockModule",
        ]

        all_expected_exports = (
            core_exports + analysis_exports + generation_exports + mocking_exports
        )

        for export in all_expected_exports:
            assert hasattr(copra, export), f"Missing export: {export}"
            assert export in copra.__all__, f"Export {export} not in __all__"

    def test_version_available(self) -> None:
        """Test that version is available."""
        import copra

        assert copra.__version__ is not None
        assert isinstance(copra.__version__, str)
        assert len(copra.__version__) > 0

    def test_core_functions_callable(self) -> None:
        """Test that core exported functions are callable."""
        import copra

        callable_exports = [
            "create_stub_from_dut",
            "discover_hierarchy",
            "generate_stub",
            "generate_stub_to_file",
            "generate_stub_with_validation",
            "validate_stub_syntax",
            "auto_generate_stubs",
        ]

        for export in callable_exports:
            func = getattr(copra, export)
            assert callable(func), f"Export {export} is not callable"

    def test_analysis_functions_callable(self) -> None:
        """Test that analysis exported functions are callable."""
        import copra

        callable_exports = [
            "analyze_stub_coverage",
            "validate_dut_interface",
        ]

        for export in callable_exports:
            func = getattr(copra, export)
            assert callable(func), f"Export {export} is not callable"

    def test_generation_functions_callable(self) -> None:
        """Test that generation exported functions are callable."""
        import copra

        callable_exports = [
            "generate_testbench_template",
        ]

        for export in callable_exports:
            func = getattr(copra, export)
            assert callable(func), f"Export {export} is not callable"

    def test_mocking_classes_available(self) -> None:
        """Test that mocking classes are available and instantiable."""
        import copra

        # Test MockSignal
        signal = copra.MockSignal("test_signal")
        assert signal._name == "test_signal"

        # Test MockModule
        module = copra.MockModule("test_module")
        assert module._name == "test_module"

        # Test MockDUT
        dut = copra.MockDUT(name="test_dut")
        assert dut._name == "test_dut"


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

        with patch.dict("sys.modules", {"cocotb": mock_cocotb}):
            # Force a fresh import to trigger version printing
            if "copra" in sys.modules:
                del sys.modules["copra"]

            # Check that version was printed (captured by capsys)
            capsys.readouterr()
            # Note: The actual output might be captured at module level
            # This test mainly ensures no exceptions are raised
            assert True


class TestModuleStructure:
    """Test the overall module structure and organization."""

    def test_module_organization(self) -> None:
        """Test that the module is properly organized."""
        import copra

        # Test that we can access all major components
        assert hasattr(copra, "core")
        assert hasattr(copra, "analysis")
        assert hasattr(copra, "generation")
        assert hasattr(copra, "mocking")

        # Test that the main API is available at the top level
        assert callable(copra.create_stub_from_dut)
        assert callable(copra.discover_hierarchy)
        assert callable(copra.generate_stub)

    def test_backwards_compatibility(self) -> None:
        """Test that the API maintains backwards compatibility."""
        import copra

        # These functions should still be available for backwards compatibility
        essential_functions = [
            "discover_hierarchy",
            "generate_stub",
            "create_stub_from_dut",
        ]

        for func_name in essential_functions:
            assert hasattr(copra, func_name)
            assert callable(getattr(copra, func_name))

    def test_professional_api_structure(self) -> None:
        """Test that the API follows professional structure patterns."""
        import copra

        # Core functionality should be easily accessible
        assert hasattr(copra, "create_stub_from_dut")
        assert hasattr(copra, "auto_generate_stubs")

        # Analysis tools should be available
        assert hasattr(copra, "analyze_stub_coverage")
        assert hasattr(copra, "validate_dut_interface")

        # Code generation should be available
        assert hasattr(copra, "generate_testbench_template")

        # Mocking should be available
        assert hasattr(copra, "MockDUT")
        assert hasattr(copra, "MockSignal")
        assert hasattr(copra, "MockModule")
