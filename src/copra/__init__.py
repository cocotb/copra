# Copyright cocotb contributors
# Licensed under the Revised BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-3-Clause

"""Copra - Python type stubs generator for cocotb testbenches."""

from ._version import __version__
from .stubgen import (
    create_stub_from_dut,
    discover_hierarchy,
    generate_stub,
    generate_stub_to_file,
    generate_stub_with_validation,
    validate_stub_syntax,
)


def _check_cocotb_version() -> None:
    """Check that cocotb version meets minimum requirements."""
    try:
        import cocotb
        print(f"[copra] Using cocotb version: {cocotb.__version__}")

        # Check minimum version requirement
        from packaging import version
        cocotb_version = version.parse(cocotb.__version__)

        # Handle development versions - 2.0.0.dev0 should be considered >= 2.0.0
        if cocotb_version.base_version < "2.0.0":
            raise ImportError(
                f"copra requires cocotb >= 2.0.0, but found {cocotb.__version__}. "
                "Please install cocotb 2.0.0+ from source: "
                "pip install git+https://github.com/cocotb/cocotb.git"
            )
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
    "create_stub_from_dut",
    "discover_hierarchy",
    "generate_stub",
    "generate_stub_to_file",
    "generate_stub_with_validation",
    "validate_stub_syntax",
]
