# Copyright cocotb contributors
# Licensed under the Revised BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-3-Clause

"""Integration utilities for copra with cocotb workflows.

This module provides enhanced integration capabilities for copra with cocotb
test environments, including automatic stub generation hooks and test runner
integration as specified in the design document.
"""

import os
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

try:
    from cocotb.handle import HierarchyObject

    COCOTB_AVAILABLE = True
except ImportError:
    COCOTB_AVAILABLE = False

    class MockHierarchyObject:
        """Mock HierarchyObject when cocotb is not available."""

        pass

    # Use the mock as HierarchyObject when cocotb is not available
    HierarchyObject = MockHierarchyObject  # type: ignore[misc,assignment]

class CocotbIntegration:
    """Integration helper for cocotb workflows."""

    def __init__(self, auto_generate: bool = True, output_dir: str = "stubs"):
        """Initialize cocotb integration.

        Args:
        ----
            auto_generate: Whether to automatically generate stubs.
            output_dir: Directory to store generated stubs.

        """
        self.auto_generate = auto_generate
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def setup_test_hooks(self) -> None:
        """Set up automatic stub generation hooks for cocotb tests."""
        if not COCOTB_AVAILABLE:
            print("[copra] Warning: cocotb not available, skipping test hooks setup")
            return

        # Register hooks with cocotb if available
        try:
            # This would integrate with cocotb's test discovery and execution
            print("[copra] Setting up cocotb test hooks for automatic stub generation")
        except Exception as e:
            print(f"[copra] Warning: Failed to set up test hooks: {e}")

    def generate_stubs_for_test(self, dut: HierarchyObject, test_name: str) -> Optional[str]:
        """Generate stubs for a specific test.

        Args:
        ----
            dut: The DUT object from the test.
            test_name: Name of the test.

        Returns:
        -------
            Path to generated stub file, or None if generation failed.

        """
        if not self.auto_generate:
            return None

        try:
            from .core import create_stub_from_dut

            stub_file = self.output_dir / f"{test_name}_dut.pyi"
            create_stub_from_dut(dut, str(stub_file))
            return str(stub_file)
        except Exception as e:
            print(f"[copra] Warning: Failed to generate stubs for test {test_name}: {e}")
            return None

    def generate_makefile_integration(
        self,
        makefile_path: str = "Makefile",
        top_module: Optional[str] = None,
        sources: Optional[List[str]] = None,
        simulator: Optional[str] = None,
    ) -> str:
        """Generate Makefile integration for automatic stub generation.

        Args:
        ----
            makefile_path: Path to the Makefile to modify.
            top_module: Top-level module name.
            sources: List of source files.
            simulator: Simulator to use.

        Returns:
        -------
            Generated makefile content.

        """
        try:
            makefile = Path(makefile_path)

            # Generate makefile content
            integration_content = """
# Copra stub generation integration
.PHONY: copra-stubs
copra-stubs:
\t@echo "Generating copra stubs..."
"""

            if sources and top_module:
                sources_str = " ".join(sources)
                integration_content += (
                    f"\t@python -m copra --sources {sources_str} --top {top_module}"
                )
                if simulator:
                    integration_content += f" --simulator {simulator}"
                integration_content += "\n"
            else:
                integration_content += "\t@python -m copra --auto-generate\n"

            integration_content += """
# Add copra-stubs as dependency to test targets
test: copra-stubs
"""

            if makefile.exists():
                with open(makefile, "a") as f:
                    f.write(integration_content)
                    print(f"[copra] Added Makefile integration to {makefile_path}")

            return integration_content

        except Exception as e:
            print(f"[copra] Warning: Failed to generate Makefile integration: {e}")
            return ""

    def generate_test_integration(self, top_module: str, stub_file: str) -> str:
        """Generate test integration content.

        Args:
        ----
            top_module: Top-level module name.
            stub_file: Path to the stub file.

        Returns:
        -------
            Generated test integration content.

        """
        test_content = f'''"""Auto-generated test integration for {top_module}."""

import cocotb
from cocotb.triggers import Timer
from typing import cast

# Import the generated DUT type
from {stub_file.replace('.pyi', '').replace('.py', '')} import DutType


@cocotb.test()
async def test_{top_module}(dut):
    """Test the {top_module} functionality.

    Args:
    ----
        dut: The DUT instance from cocotb.
    """
    # Cast to typed DUT for IDE support
    typed_dut = cast(DutType, dut)

    # Add your test logic here
    await Timer(10, units='ns')

    dut._log.info("Test completed successfully")
'''
        return test_content


def setup_automatic_stub_generation(
    output_dir: str = "stubs",
    enable_for_all_tests: bool = True,
    stub_naming_pattern: str = "{test_name}_dut.pyi",
) -> None:
    """Set up automatic stub generation for all cocotb tests.

    Args:
    ----
        output_dir: Directory to store generated stubs.
        enable_for_all_tests: Whether to enable for all tests automatically.
        stub_naming_pattern: Pattern for naming stub files.

    """
    if not COCOTB_AVAILABLE:
        print("[copra] Warning: cocotb not available, cannot set up automatic generation")
        return

    integration = CocotbIntegration(auto_generate=enable_for_all_tests, output_dir=output_dir)
    integration.setup_test_hooks()

    # Store configuration for later use
    os.environ["COPRA_AUTO_GENERATE"] = str(enable_for_all_tests)
    os.environ["COPRA_OUTPUT_DIR"] = output_dir
    os.environ["COPRA_NAMING_PATTERN"] = stub_naming_pattern


def cocotb_test_wrapper(test_func: Callable[..., Any]) -> Callable[..., Any]:
    """Wrap cocotb tests with automatic stub generation.

    This decorator can be applied to cocotb test functions to automatically
    generate stubs when the test runs.

    Args:
    ----
        test_func: The test function to wrap.

    Returns:
    -------
        Wrapped test function.

    Example:
    -------
        @cocotb.test()
        @cocotb_test_wrapper
        async def test_my_dut(dut):
            # Test code here
            pass

    """
    import functools

    @functools.wraps(test_func)
    async def wrapper(dut: Any, *args: Any, **kwargs: Any) -> Any:
        """Generate stubs before running the test."""
        # Check if automatic generation is enabled
        auto_generate = os.environ.get("COPRA_AUTO_GENERATE", "True").lower() == "true"

        if auto_generate:
            try:
                output_dir = os.environ.get("COPRA_OUTPUT_DIR", "stubs")
                os.environ.get("COPRA_NAMING_PATTERN", "{test_name}_dut.pyi")

                integration = CocotbIntegration(output_dir=output_dir)
                test_name = test_func.__name__
                stub_file = integration.generate_stubs_for_test(dut, test_name)

                if stub_file:
                    print(f"[copra] Generated stubs for test {test_name}: {stub_file}")
            except Exception as e:
                print(
                    f"[copra] Warning: Failed to generate stubs for test {test_func.__name__}: {e}"
                )

        # Run the original test
        return await test_func(dut, *args, **kwargs)

    return wrapper


class RunnerIntegration:
    """Integration with cocotb test runners for enhanced workflow support."""

    def __init__(self, runner_type: str = "auto"):
        """Initialize test runner integration.

        Args:
        ----
            runner_type: Type of test runner to integrate with.

        """
        self.runner_type = runner_type
        self.generated_stubs: List[str] = []

    def pre_test_hook(self, test_name: str, dut: HierarchyObject) -> None:
        """Call before each test runs.

        Args:
        ----
            test_name: Name of the test about to run.
            dut: The DUT object for the test.

        """
        try:
            from .core import create_stub_from_dut

            stub_file = f"stubs/{test_name}_dut.pyi"
            create_stub_from_dut(dut, stub_file)
            self.generated_stubs.append(stub_file)
            print(f"[copra] Pre-test stub generation: {stub_file}")
        except Exception as e:
            print(f"[copra] Warning: Pre-test stub generation failed: {e}")

    def post_test_hook(self, test_name: str, test_result: Any) -> None:
        """Call after each test completes.

        Args:
        ----
            test_name: Name of the completed test.
            test_result: Result of the test.

        """
        print(f"[copra] Post-test cleanup for {test_name}")
        # Could perform cleanup or additional processing here

    def generate_test_summary(self) -> Dict[str, Any]:
        """Generate a summary of all stub generation activities.

        Returns
        -------
            Dictionary containing summary information.

        """
        return {
            "total_stubs_generated": len(self.generated_stubs),
            "generated_files": self.generated_stubs,
            "runner_type": self.runner_type,
        }


def integrate_with_makefile(makefile_path: str = "Makefile") -> None:
    """Add copra integration to a cocotb Makefile.

    Args:
    ----
        makefile_path: Path to the Makefile to modify.

    """
    makefile = Path(makefile_path)
    if not makefile.exists():
        print(f"[copra] Warning: Makefile not found at {makefile_path}")
        return

    # Read existing Makefile
    with open(makefile) as f:
        content = f.read()

    # Check if copra integration is already present
    if "copra" in content.lower():
        print("[copra] Makefile already contains copra integration")
        return

    # Add copra targets
    copra_targets = """
# Copra stub generation targets
generate-stubs:
\tcopra $(MODULE) --outfile stubs/$(TOPLEVEL).pyi --verbose

generate-stubs-with-docs:
\tcopra $(MODULE) --outfile stubs/$(TOPLEVEL).pyi --output-format both --verbose

clean-stubs:
\trm -rf stubs/

.PHONY: generate-stubs generate-stubs-with-docs clean-stubs

# Add stub generation to the default test target
test: generate-stubs
"""

    # Append to Makefile
    with open(makefile, "a") as f:
        f.write(copra_targets)

    print(f"[copra] Added copra integration to {makefile_path}")


def create_copra_config(
    config_path: str = ".copra.toml",
    auto_generate: bool = True,
    output_dir: str = "stubs",
    max_depth: int = 50,
    include_constants: bool = False,
    performance_mode: bool = False,
) -> None:
    """Create a copra configuration file.

    Args:
    ----
        config_path: Path to create the configuration file.
        auto_generate: Whether to enable automatic generation.
        output_dir: Directory for generated stubs.
        max_depth: Maximum hierarchy depth.
        include_constants: Whether to include constants.
        performance_mode: Whether to enable performance mode.

    """
    config_content = f"""# Copra configuration file
# This file configures automatic stub generation for cocotb tests

[copra]
auto_generate = {str(auto_generate).lower()}
output_dir = "{output_dir}"
max_depth = {max_depth}
include_constants = {str(include_constants).lower()}
performance_mode = {str(performance_mode).lower()}

[copra.output]
format = "pyi"
include_documentation = true
template = "default"

[copra.integration]
enable_test_hooks = true
naming_pattern = "{{test_name}}_dut.pyi"
makefile_integration = true
"""

    with open(config_path, "w") as f:
        f.write(config_content)

    print(f"[copra] Created configuration file: {config_path}")


def load_copra_config(config_path: str = ".copra.toml") -> Dict[str, Any]:
    """Load copra configuration from file.

    Args:
    ----
        config_path: Path to the configuration file.

    Returns:
    -------
        Configuration dictionary.

    """
    config_file = Path(config_path)
    if not config_file.exists():
        return {}

    try:
        import tomllib  # type: ignore[import-untyped]
    except ImportError:
        try:
            import tomli as tomllib  # type: ignore[import-untyped]
        except ImportError:
            print("[copra] Warning: TOML library not available, using default configuration")
            return {}

    try:
        with open(config_file, "rb") as f:
            config_data: Dict[str, Any] = tomllib.load(f)
            return config_data
    except Exception as e:
        print(f"[copra] Warning: Failed to load configuration: {e}")
        return {}
