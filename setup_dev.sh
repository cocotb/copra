#!/bin/bash

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Setup development environment for copra
echo "Installing dependencies..."
pip install -e .

# Install pre-commit hooks
echo "Installing pre-commit hooks..."
pre-commit install

# Create necessary directories
mkdir -p examples/minimal/sim_build

# Run tests
echo "Running tests..."
nox -s test

# Generate documentation
echo "Building documentation..."
nox -s docs

# Run the example
echo "Running example..."
nox -s examples

# Show generated stubs
if [ -f "examples/minimal/dut.pyi" ]; then
    echo -e "\nGenerated stub file contents:\n"
    cat examples/minimal/dut.pyi
else
    echo -e "\nGenerated stub file not found. Example may have failed to run."
fi

echo -e "\nDevelopment environment setup complete!"
