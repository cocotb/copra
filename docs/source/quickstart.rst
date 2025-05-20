.. _quickstart:

Quickstart
==========

This guide will help you get started with copra, the Python type stub generator for cocotb testbenches.

Installation
------------

copra can be installed using pip:

.. code-block:: bash

    pip install copra

If you want to install from source:

.. code-block:: bash

    git clone https://github.com/cocotb/copra.git
    cd copra
    pip install -e .

Basic Usage
-----------

To generate type stubs for your cocotb testbench, run:

.. code-block:: bash

    copra path/to/your/testbench

This will analyze your testbench and generate a `dut.pyi` file in the current directory.

Example
-------

Given a simple D flip-flop testbench:

.. code-block:: python
    :caption: test_dff.py

    import cocotb
    from cocotb.clock import Clock
    from cocotb.triggers import RisingEdge

    @cocotb.test()
    async def test_dff(dut):
        """Test a simple D flip-flop."""
        clock = Clock(dut.clk, 10, units="ns")
        cocotb.start_soon(clock.start())
        
        # Reset
        dut.rst_n.value = 0
        dut.d.value = 0
        await RisingEdge(dut.clk)
        await RisingEdge(dut.clk)
        dut.rst_n.value = 1
        
        # Test data
        test_values = [0, 1, 0, 1, 1, 0]
        
        for i, val in enumerate(test_values, 1):
            dut.d.value = val
            await RisingEdge(dut.clk)
            assert dut.q.value == (test_values[i-2] if i > 1 else 0), \
                f"Expected {test_values[i-2]}, got {dut.q.value}"

Run the stub generator:

.. code-block:: bash

    copra test_dff.py -o dut.pyi

This will generate a `dut.pyi` file with type information for your DUT.

Using the Generated Stubs
------------------------

To use the generated stubs in your IDE:

1. Place the `.pyi` file in your project directory
2. Configure your IDE to use the stubs (most IDEs do this automatically)

For example, in VS Code, add this to your `settings.json`:

.. code-block:: json

    {
        "python.analysis.typeCheckingMode": "basic",
        "python.analysis.diagnosticMode": "workspace",
        "python.analysis.stubPath": "."
    }

Development
-----------

To set up a development environment:

.. code-block:: bash

    git clone https://github.com/cocotb/copra.git
    cd copra
    pip install -e .[dev]
    pre-commit install

Run the tests:

.. code-block:: bash

    pytest

Build the documentation:

.. code-block:: bash

    cd docs
    make html

Contributing
------------

Contributions are welcome! Please see our `contributing guide <https://github.com/cocotb/copra/CONTRIBUTING.md>`_ for details.
