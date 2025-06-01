"""Auto-generated testbench for dut.

This testbench provides comprehensive test coverage with proper
clock and reset handling, multiple test scenarios, and TestFactory integration.
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles
from cocotb.regression import TestFactory
from typing import cast, Any

# Import the generated DUT type
from dut import DutType


class DutTestBench:
    """Testbench class for dut."""

    def __init__(self, dut: Any):
        """Initialize testbench.

        Args:
        ----
            dut: The DUT instance from cocotb.
        """
        self.dut = cast(DutType, dut)
        self.clock_period = 10  # ns

    async def setup_clock(self):
        """Set up clock generation."""
        clock = Clock(self.dut.clk, self.clock_period, units="ns")
        cocotb.start_soon(clock.start())

    async def reset_dut(self):
        """Reset the DUT."""
        # Assert reset
        self.dut.rst_n.value = 0
        await ClockCycles(self.dut.clk, 5)

        # Deassert reset
        self.dut.rst_n.value = 1
        await ClockCycles(self.dut.clk, 5)


# Signal list for reference:


@cocotb.test()
async def test_dut_reset(dut):
    """Test reset functionality."""
    tb = DutTestBench(dut)
    await tb.setup_clock()
    await tb.reset_dut()

    # Verify reset state
    # Add your reset verification logic here

    dut._log.info("Reset test completed")


@cocotb.test()
async def test_dut_basic_operation(dut):
    """Test basic operation."""
    tb = DutTestBench(dut)
    await tb.setup_clock()
    await tb.reset_dut()

    # Add your basic operation test logic here
    await ClockCycles(dut.clk, 10)

    dut._log.info("Basic operation test completed")


@cocotb.test()
async def test_dut_edge_cases(dut):
    """Test edge cases."""
    tb = DutTestBench(dut)
    await tb.setup_clock()
    await tb.reset_dut()

    # Add your edge case test logic here
    await ClockCycles(dut.clk, 20)

    dut._log.info("Edge cases test completed")


async def run_random_test(dut, iterations: int = 100):
    """Run randomized test."""
    tb = DutTestBench(dut)
    await tb.setup_clock()
    await tb.reset_dut()

    for i in range(iterations):
        # Add your randomized test logic here
        await ClockCycles(dut.clk, 1)

        if i % 10 == 0:
            dut._log.info(f"Random test iteration {i}/{iterations}")

    dut._log.info(f"Random test completed ({iterations} iterations)")


# TestFactory for parameterized tests
factory = TestFactory(run_random_test)
factory.add_option("iterations", [10, 50, 100])
factory.generate_tests()
