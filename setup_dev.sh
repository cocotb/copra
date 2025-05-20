#!/bin/bash

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Setup development environment for copra
echo "Installing dependencies..."
pip install -e .
pip install -r requirements.txt

# Install pre-commit hooks
echo "Installing pre-commit hooks..."
pre-commit install

# Create necessary directories
mkdir -p examples/minimal/sim_build

# Run tests
echo "Running tests..."
python -m pytest tests/

# Generate documentation
echo "Building documentation..."
if [ -d "docs" ]; then
    cd docs
    if [ ! -f "source/conf.py" ]; then
        echo "Documentation not set up. Skipping..."
    else
        make html
    fi
    cd ..
else
    echo "Docs directory not found. Skipping..."
fi

# Run the example
echo "Running example..."
python examples/run_example.py

# Show generated stubs
if [ -f "examples/minimal/dut.pyi" ]; then
    echo -e "\nGenerated stub file contents:\n"
    cat examples/minimal/dut.pyi
else
    echo -e "\nGenerated stub file not found. Example may have failed to run."
fi

echo -e "\nDevelopment environment setup complete!"
