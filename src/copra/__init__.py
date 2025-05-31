# Copyright cocotb contributors
# Licensed under the Revised BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-3-Clause

"""Copra - Python type stubs generator for cocotb testbenches.

Copra automatically generates Python type stubs (.pyi files) for cocotb Device Under Test (DUT)
objects, enabling IDE autocompletion and static type checking for hardware verification testbenches.

Key Features:
- Automatic DUT hierarchy discovery and stub generation
- Support for arrays, sub-modules, and complex hierarchies
- IDE integration with autocompletion and type checking
- Mock DUT creation for unit testing
- Testbench template generation
- Interface validation and coverage analysis

Example Usage:
    # Generate stubs from within a cocotb test
    @cocotb.test()
    async def test_generate_stubs(dut):
        from copra import create_stub_from_dut
        create_stub_from_dut(dut, "my_dut.pyi")

    # Command line usage
    $ copra my_testbench_module --outfile stubs/dut.pyi

    # Automatic stub generation decorator
    @cocotb.test()
    @copra.auto_generate_stubs("dut.pyi")
    async def test_my_module(dut):
        # Test code with full type support
        pass
"""

from ._version import __version__
from .analysis import (
    analyze_hierarchy,
    analyze_stub_coverage,
    validate_dut_interface,
    validate_stub_syntax,
)
from .cli import main as cli_main
from .core import (
    auto_generate_stubs,
    create_stub_from_dut,
    discover_hierarchy,
    generate_stub,
    generate_stub_to_file,
    generate_stub_with_validation,
)
from .generation import (
    DocumentationGenerator,
    StubGenerationOptions,
    StubGenerator,
    generate_testbench_template,
)
from .integration import (
    CocotbIntegration,
    RunnerIntegration,
    cocotb_test_wrapper,
    create_copra_config,
    integrate_with_makefile,
    setup_automatic_stub_generation,
)
from .metadata import (
    ArrayMetadata,
    BusProtocol,
    SignalDirection,
    SignalMetadata,
    SignalMetadataExtractor,
    SignalType,
    extract_comprehensive_metadata,
    extract_enhanced_array_metadata,
)
from .mocking import (
    MockDUT,
    MockModule,
    MockSignal,
    create_mock_dut,
)
from .simulation import (
    DUTDiscoverySimulation,
    SimulationError,
    SimulatorDetector,
    run_discovery_simulation,
)

try:
    import cocotb  # type: ignore[import-untyped]
    
    COCOTB_AVAILABLE = True
    COCOTB_VERSION = getattr(cocotb, "__version__", "unknown")
except ImportError:
    COCOTB_AVAILABLE = False
    COCOTB_VERSION = "not available"


def _check_cocotb_version() -> None:
    """Check that cocotb version meets minimum requirements."""
    try:
        # Skip version check if we're in a test environment with mocked cocotb
        if not COCOTB_AVAILABLE:
            raise ImportError(
                "copra requires cocotb >= 2.0.0. "
                "Please install cocotb 2.0.0+ from source: "
                "pip install git+https://github.com/cocotb/cocotb.git"
            )
        
        print(f"[copra] Using cocotb version: {COCOTB_VERSION}")

        # Check minimum version requirement
        try:
            from packaging import version
        except ImportError:
            # If packaging is not available, skip version check
            print("[copra] packaging module not available, skipping version check")
            return

        # Handle cases where version is not available or is a mock
        if COCOTB_VERSION == "unknown" or COCOTB_VERSION == "not available":
            print("[copra] cocotb version information not available")
            return
        
        # Skip version check for mock objects (testing) - but only if it's actually a Mock class name
        if hasattr(cocotb, '__class__') and cocotb.__class__.__name__ == 'Mock':
            return

        try:
            cocotb_version = version.parse(COCOTB_VERSION)
            
            # Handle development versions - 2.0.0.dev0 should be considered >= 2.0.0
            if cocotb_version.base_version < "2.0.0":
                raise ImportError(
                    f"copra requires cocotb >= 2.0.0, but found {COCOTB_VERSION}. "
                    "Please install cocotb 2.0.0+ from source: "
                    "pip install git+https://github.com/cocotb/cocotb.git"
                )
        except ImportError:
            # Re-raise ImportError (our version check errors)
            raise
        except Exception as e:
            # If version parsing fails for other reasons, just warn and continue
            print(f"[copra] Warning: Could not parse cocotb version '{COCOTB_VERSION}': {e}")
            
    except ImportError as e:
        if "copra requires cocotb" in str(e):
            raise  # Re-raise our version check error
        print("[copra] cocotb version information not available")
        raise ImportError(
            "copra requires cocotb >= 2.0.0. "
            "Please install cocotb 2.0.0+ from source: "
            "pip install git+https://github.com/cocotb/cocotb.git"
        ) from e
    except AttributeError:
        print("[copra] cocotb version information not available")


# Perform version check on import
_check_cocotb_version()

__all__ = [
    "__version__",
    # Core stub generation
    "create_stub_from_dut",
    "discover_hierarchy",
    "generate_stub",
    "generate_stub_to_file",
    "generate_stub_with_validation",
    "auto_generate_stubs",
    # Analysis and validation
    "analyze_stub_coverage",
    "validate_dut_interface",
    "validate_stub_syntax",
    "analyze_hierarchy",
    # Code generation
    "generate_testbench_template",
    "StubGenerator",
    "StubGenerationOptions",
    "DocumentationGenerator",
    # Mocking and testing
    "MockDUT",
    "MockSignal",
    "MockModule",
    "create_mock_dut",
    # Integration
    "CocotbIntegration",
    "RunnerIntegration",
    "cocotb_test_wrapper",
    "setup_automatic_stub_generation",
    "integrate_with_makefile",
    "create_copra_config",
    # Simulation integration
    "DUTDiscoverySimulation",
    "SimulationError",
    "SimulatorDetector",
    "run_discovery_simulation",
    # Metadata extraction
    "SignalMetadata",
    "ArrayMetadata",
    "SignalDirection",
    "SignalType",
    "BusProtocol",
    "SignalMetadataExtractor",
    "extract_comprehensive_metadata",
    "extract_enhanced_array_metadata",
    # CLI
    "cli_main",
]
