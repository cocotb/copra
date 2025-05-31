"""Tests for the copra.integration module."""

import os
from unittest.mock import Mock, patch

from copra.integration import (
    CocotbIntegration,
    RunnerIntegration,
    cocotb_test_wrapper,
    create_copra_config,
    integrate_with_makefile,
    load_copra_config,
    setup_automatic_stub_generation,
)


class TestCocotbIntegration:
    """Test the CocotbIntegration class."""

    def test_integration_initialization(self, tmp_path):
        """Test CocotbIntegration initialization."""
        output_dir = tmp_path / "test_stubs"
        integration = CocotbIntegration(auto_generate=True, output_dir=str(output_dir))

        assert integration.auto_generate is True
        assert integration.output_dir == output_dir
        assert output_dir.exists()

    def test_setup_test_hooks(self):
        """Test setting up test hooks."""
        integration = CocotbIntegration()
        # Should not raise an exception
        integration.setup_test_hooks()

    def test_generate_stubs_for_test_disabled(self, tmp_path):
        """Test stub generation when disabled."""
        integration = CocotbIntegration(auto_generate=False, output_dir=str(tmp_path))
        mock_dut = Mock()
        mock_dut._name = "test_dut"

        result = integration.generate_stubs_for_test(mock_dut, "test_name")
        assert result is None

    def test_generate_stubs_for_test_enabled(self, tmp_path):
        """Test stub generation when enabled."""
        integration = CocotbIntegration(auto_generate=True, output_dir=str(tmp_path))
        mock_dut = Mock()
        mock_dut._name = "test_dut"

        with patch("copra.core.create_stub_from_dut") as mock_create:
            result = integration.generate_stubs_for_test(mock_dut, "test_name")

            expected_file = tmp_path / "test_name_dut.pyi"
            mock_create.assert_called_once_with(mock_dut, str(expected_file))
            assert result == str(expected_file)

    def test_generate_stubs_for_test_error_handling(self, tmp_path):
        """Test error handling in stub generation."""
        integration = CocotbIntegration(auto_generate=True, output_dir=str(tmp_path))
        mock_dut = Mock()

        with patch("copra.core.create_stub_from_dut", side_effect=Exception("Test error")):
            result = integration.generate_stubs_for_test(mock_dut, "test_name")
            assert result is None


class TestAutomaticStubGeneration:
    """Test automatic stub generation setup."""

    def test_setup_automatic_stub_generation(self):
        """Test setting up automatic stub generation."""
        with patch.dict(os.environ, {}, clear=True):
            setup_automatic_stub_generation(
                output_dir="test_stubs",
                enable_for_all_tests=True,
                stub_naming_pattern="{test_name}_custom.pyi",
            )

            assert os.environ["COPRA_AUTO_GENERATE"] == "True"
            assert os.environ["COPRA_OUTPUT_DIR"] == "test_stubs"
            assert os.environ["COPRA_NAMING_PATTERN"] == "{test_name}_custom.pyi"

    def test_setup_automatic_stub_generation_disabled(self):
        """Test setting up automatic stub generation when disabled."""
        with patch.dict(os.environ, {}, clear=True):
            setup_automatic_stub_generation(enable_for_all_tests=False)

            assert os.environ["COPRA_AUTO_GENERATE"] == "False"


class TestCocotbTestWrapper:
    """Test the cocotb test wrapper decorator."""

    def test_wrapper_with_auto_generate_enabled(self, tmp_path):
        """Test wrapper when auto-generation is enabled."""

        @cocotb_test_wrapper
        async def test_function(dut):
            return "test_result"

        mock_dut = Mock()
        mock_dut._name = "test_dut"

        with patch.dict(
            os.environ, {"COPRA_AUTO_GENERATE": "True", "COPRA_OUTPUT_DIR": str(tmp_path)}
        ):
            with patch("copra.integration.CocotbIntegration") as mock_integration_class:
                mock_integration = Mock()
                mock_integration.generate_stubs_for_test.return_value = "stub_file.pyi"
                mock_integration_class.return_value = mock_integration

                import asyncio

                result = asyncio.run(test_function(mock_dut))

                assert result == "test_result"
                mock_integration.generate_stubs_for_test.assert_called_once_with(
                    mock_dut, "test_function"
                )

    def test_wrapper_with_auto_generate_disabled(self):
        """Test wrapper when auto-generation is disabled."""

        @cocotb_test_wrapper
        async def test_function(dut):
            return "test_result"

        mock_dut = Mock()

        with patch.dict(os.environ, {"COPRA_AUTO_GENERATE": "False"}):
            with patch("copra.integration.CocotbIntegration") as mock_integration_class:
                import asyncio

                result = asyncio.run(test_function(mock_dut))

                assert result == "test_result"
                mock_integration_class.assert_not_called()

    def test_wrapper_error_handling(self):
        """Test wrapper error handling."""

        @cocotb_test_wrapper
        async def test_function(dut):
            return "test_result"

        mock_dut = Mock()

        with patch.dict(os.environ, {"COPRA_AUTO_GENERATE": "True"}):
            with patch("copra.integration.CocotbIntegration", side_effect=Exception("Test error")):
                import asyncio

                result = asyncio.run(test_function(mock_dut))

                # Should still return the test result despite the error
                assert result == "test_result"


class TestRunnerIntegration:
    """Test the RunnerIntegration class."""

    def test_initialization(self):
        """Test RunnerIntegration initialization."""
        integration = RunnerIntegration("custom_runner")

        assert integration.runner_type == "custom_runner"
        assert integration.generated_stubs == []

    def test_pre_test_hook(self):
        """Test pre-test hook functionality."""
        integration = RunnerIntegration()
        mock_dut = Mock()
        mock_dut._name = "test_dut"

        with patch("copra.core.create_stub_from_dut") as mock_create:
            integration.pre_test_hook("test_name", mock_dut)

            mock_create.assert_called_once_with(mock_dut, "stubs/test_name_dut.pyi")
            assert "stubs/test_name_dut.pyi" in integration.generated_stubs

    def test_pre_test_hook_error_handling(self):
        """Test pre-test hook error handling."""
        integration = RunnerIntegration()
        mock_dut = Mock()

        with patch("copra.core.create_stub_from_dut", side_effect=Exception("Test error")):
            # Should not raise an exception
            integration.pre_test_hook("test_name", mock_dut)
            assert len(integration.generated_stubs) == 0

    def test_post_test_hook(self):
        """Test post-test hook functionality."""
        integration = RunnerIntegration()

        # Should not raise an exception
        integration.post_test_hook("test_name", "test_result")

    def test_generate_test_summary(self):
        """Test test summary generation."""
        integration = RunnerIntegration("test_runner")
        integration.generated_stubs = ["file1.pyi", "file2.pyi"]

        summary = integration.generate_test_summary()

        assert summary["total_stubs_generated"] == 2
        assert summary["generated_files"] == ["file1.pyi", "file2.pyi"]
        assert summary["runner_type"] == "test_runner"


class TestMakefileIntegration:
    """Test Makefile integration functionality."""

    def test_integrate_with_nonexistent_makefile(self, tmp_path):
        """Test integration with non-existent Makefile."""
        makefile_path = tmp_path / "Makefile"

        integrate_with_makefile(str(makefile_path))
        # Should handle gracefully without creating the file

    def test_integrate_with_existing_makefile(self, tmp_path):
        """Test integration with existing Makefile."""
        makefile_path = tmp_path / "Makefile"

        # Create a basic Makefile
        with open(makefile_path, "w") as f:
            f.write("# Basic Makefile\nTOPLEVEL = test\nMODULE = test_module\n")

        integrate_with_makefile(str(makefile_path))

        # Check that copra targets were added
        with open(makefile_path) as f:
            content = f.read()

        assert "generate-stubs:" in content
        assert "copra $(MODULE)" in content
        assert ".PHONY: generate-stubs" in content

    def test_integrate_with_existing_copra_makefile(self, tmp_path):
        """Test integration with Makefile that already has copra."""
        makefile_path = tmp_path / "Makefile"

        # Create a Makefile with existing copra integration
        with open(makefile_path, "w") as f:
            f.write("# Makefile with copra\ncopra test\n")

        integrate_with_makefile(str(makefile_path))

        # Should not modify the file
        with open(makefile_path) as f:
            content = f.read()

        # Should only contain the original content (case-insensitive check was used)
        # The function checks for 'copra' in content.lower(), so it finds it and doesn't add more
        lines = content.strip().split("\n")
        assert len(lines) == 2  # Should still have only the original 2 lines
        assert "# Makefile with copra" in content
        assert "copra test" in content


class TestConfigurationManagement:
    """Test configuration file management."""

    def test_create_copra_config(self, tmp_path):
        """Test creating a copra configuration file."""
        config_path = tmp_path / ".copra.toml"

        create_copra_config(
            config_path=str(config_path),
            auto_generate=True,
            output_dir="custom_stubs",
            max_depth=100,
            include_constants=True,
            performance_mode=True,
        )

        assert config_path.exists()

        with open(config_path) as f:
            content = f.read()

        assert "auto_generate = true" in content
        assert 'output_dir = "custom_stubs"' in content
        assert "max_depth = 100" in content
        assert "include_constants = true" in content
        assert "performance_mode = true" in content

    def test_load_copra_config_nonexistent(self, tmp_path):
        """Test loading non-existent configuration file."""
        config_path = tmp_path / ".copra.toml"

        config = load_copra_config(str(config_path))
        assert config == {}

    def test_load_copra_config_invalid(self, tmp_path):
        """Test loading invalid configuration file."""
        config_path = tmp_path / ".copra.toml"

        # Create invalid TOML file
        with open(config_path, "w") as f:
            f.write("invalid toml content [[[")

        config = load_copra_config(str(config_path))
        assert config == {}

    def test_load_copra_config_no_toml_library(self, tmp_path):
        """Test loading config when TOML library is not available."""
        config_path = tmp_path / ".copra.toml"

        # Create valid TOML file
        with open(config_path, "w") as f:
            f.write("[copra]\nauto_generate = true\n")

        # Mock missing TOML libraries
        with patch.dict("sys.modules", {"tomllib": None, "tomli": None}):
            config = load_copra_config(str(config_path))
            assert config == {}


class TestIntegrationWorkflow:
    """Test complete integration workflows."""

    def test_complete_workflow(self, tmp_path):
        """Test a complete integration workflow."""
        # Set up environment
        output_dir = tmp_path / "stubs"

        # Create configuration
        config_path = tmp_path / ".copra.toml"
        create_copra_config(config_path=str(config_path), output_dir=str(output_dir))

        # Set up automatic generation
        setup_automatic_stub_generation(output_dir=str(output_dir))

        # Create test runner integration
        runner = RunnerIntegration()

        # Simulate test execution
        mock_dut = Mock()
        mock_dut._name = "workflow_dut"

        with patch("copra.core.create_stub_from_dut"):
            runner.pre_test_hook("workflow_test", mock_dut)
            runner.post_test_hook("workflow_test", "success")

            summary = runner.generate_test_summary()

            assert summary["total_stubs_generated"] == 1
            assert "stubs/workflow_test_dut.pyi" in summary["generated_files"]

    def test_makefile_and_config_integration(self, tmp_path):
        """Test integration of Makefile and configuration."""
        # Create Makefile
        makefile_path = tmp_path / "Makefile"
        with open(makefile_path, "w") as f:
            f.write("TOPLEVEL = test_module\nMODULE = test\n")

        # Create configuration
        config_path = tmp_path / ".copra.toml"
        create_copra_config(config_path=str(config_path))

        # Integrate with Makefile
        integrate_with_makefile(str(makefile_path))

        # Verify both files exist and have expected content
        assert makefile_path.exists()
        assert config_path.exists()

        with open(makefile_path) as f:
            makefile_content = f.read()

        assert "generate-stubs:" in makefile_content
        assert "copra $(MODULE)" in makefile_content


class TestErrorHandling:
    """Test error handling in integration functionality."""

    def test_integration_with_missing_cocotb(self):
        """Test integration when cocotb is not available."""
        with patch("copra.integration.COCOTB_AVAILABLE", False):
            # Should handle gracefully
            setup_automatic_stub_generation()

            integration = CocotbIntegration()
            integration.setup_test_hooks()

    def test_wrapper_with_missing_environment_variables(self):
        """Test wrapper with missing environment variables."""

        @cocotb_test_wrapper
        async def test_function(dut):
            return "test_result"

        mock_dut = Mock()

        # Clear environment variables
        with patch.dict(os.environ, {}, clear=True):
            import asyncio

            result = asyncio.run(test_function(mock_dut))

            # Should still work with defaults
            assert result == "test_result"

    def test_runner_integration_with_invalid_paths(self):
        """Test runner integration with invalid paths."""
        runner = RunnerIntegration()
        mock_dut = Mock()

        # Test with invalid stub file path
        with patch("copra.core.create_stub_from_dut", side_effect=OSError("Permission denied")):
            runner.pre_test_hook("test_name", mock_dut)

            # Should handle error gracefully
            assert len(runner.generated_stubs) == 0
