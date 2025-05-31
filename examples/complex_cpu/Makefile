# Makefile for Complex CPU Example
# Demonstrates copra's capabilities with a large, complex design

# Project configuration
TOPLEVEL_LANG ?= verilog
TOPLEVEL = cpu_top
MODULE = test_cpu

# Source files
VERILOG_SOURCES = $(shell pwd)/cpu_top.sv \
                  $(shell pwd)/clock_gen.sv \
                  $(shell pwd)/cpu_complex.sv \
                  $(shell pwd)/cpu_core.sv \
                  $(shell pwd)/pipeline_stages.sv \
                  $(shell pwd)/support_modules.sv

# Simulation configuration
SIM ?= icarus
WAVES ?= 1
GUI ?= 0

# Test configuration
COCOTB_LOG_LEVEL ?= INFO
RANDOM_SEED ?= 12345

# Help target (must come before cocotb include)
.PHONY: help
help:
	@echo "Complex CPU Example Makefile"
	@echo "============================"
	@echo ""
	@echo "Main targets:"
	@echo "  generate-stubs    Generate type stubs with copra"
	@echo "  test             Run basic tests"
	@echo "  test-all         Run all tests"
	@echo "  test-stress      Run stress tests only"
	@echo "  typecheck        Run mypy type checking"
	@echo "  lint             Run code linting"
	@echo "  docs             Generate documentation"
	@echo "  view-docs        Open documentation in browser"
	@echo "  analyze          Analyze design metrics"
	@echo "  benchmark        Benchmark stub generation"
	@echo "  ci               Run all CI checks"
	@echo "  setup            Check development environment"
	@echo "  clean            Clean simulation files"
	@echo "  clean-stubs      Clean generated stubs"
	@echo ""
	@echo "Simulator targets:"
	@echo "  test-icarus      Run tests with Icarus Verilog"
	@echo "  test-verilator   Run tests with Verilator"
	@echo ""
	@echo "Configuration:"
	@echo "  SIM=<simulator>           Simulator to use (icarus, verilator)"
	@echo "  WAVES=1                   Enable waveform generation"
	@echo "  GUI=1                     Enable GUI mode"
	@echo "  COCOTB_LOG_LEVEL=<level>  Set log level (DEBUG, INFO, WARNING, ERROR)"
	@echo "  RANDOM_SEED=<seed>        Set random seed for reproducible tests"
	@echo ""
	@echo "Examples:"
	@echo "  make test SIM=verilator WAVES=1"
	@echo "  make test-stress COCOTB_LOG_LEVEL=DEBUG"
	@echo "  make benchmark"

# Include cocotb makefiles
include $(shell cocotb-config --makefiles)/Makefile.sim

# Copra stub generation
.PHONY: generate-stubs
generate-stubs:
	@echo "Generating type stubs with copra..."
	python3 generate_stubs.py

# Clean generated stubs
.PHONY: clean-stubs
clean-stubs:
	@echo "Cleaning generated stubs..."
	rm -f cpu_top.pyi
	rm -f cpu_top_types.py
	rm -f cpu_top_interface.md
	rm -f cpu_top_interface.html
	rm -f cpu_top_interface.rst
	rm -f test_cpu_generated.py

# Type checking with mypy
.PHONY: typecheck
typecheck: generate-stubs
	@echo "Running type checking with mypy..."
	mypy test_cpu.py --ignore-missing-imports --show-error-codes

# Lint the test files
.PHONY: lint
lint:
	@echo "Linting Python test files..."
	flake8 test_cpu.py generate_stubs.py --max-line-length=100 --ignore=E501,W503

# Run basic tests
.PHONY: test
test: generate-stubs
	@echo "Running basic CPU tests..."
	$(MAKE) SIM=$(SIM) TOPLEVEL_LANG=$(TOPLEVEL_LANG) TOPLEVEL=$(TOPLEVEL) MODULE=$(MODULE) \
		TESTCASE=test_cpu_reset_and_initialization,test_csr_access

# Run all tests
.PHONY: test-all
test-all: generate-stubs
	@echo "Running all CPU tests..."
	$(MAKE) SIM=$(SIM) TOPLEVEL_LANG=$(TOPLEVEL_LANG) TOPLEVEL=$(TOPLEVEL) MODULE=$(MODULE)

# Run stress tests only
.PHONY: test-stress
test-stress: generate-stubs
	@echo "Running stress tests..."
	$(MAKE) SIM=$(SIM) TOPLEVEL_LANG=$(TOPLEVEL_LANG) TOPLEVEL=$(TOPLEVEL) MODULE=$(MODULE) \
		TESTCASE=run_stress_test

# Run with different simulators
.PHONY: test-icarus
test-icarus: generate-stubs
	@echo "Running tests with Icarus Verilog..."
	$(MAKE) test SIM=icarus

.PHONY: test-verilator
test-verilator: generate-stubs
	@echo "Running tests with Verilator..."
	$(MAKE) test SIM=verilator EXTRA_ARGS="--trace --trace-structs"

.PHONY: test-ghdl
test-ghdl:
	@echo "GHDL not supported for this Verilog design"

# Performance testing
.PHONY: test-performance
test-performance: generate-stubs
	@echo "Running performance tests..."
	time $(MAKE) test-all SIM=$(SIM)

# Generate documentation
.PHONY: docs
docs: generate-stubs
	@echo "Generated documentation files:"
	@ls -la *.md *.html *.rst 2>/dev/null || echo "No documentation files found"

# View documentation
.PHONY: view-docs
view-docs: docs
	@echo "Opening documentation in browser..."
	@if command -v xdg-open > /dev/null; then \
		xdg-open cpu_top_interface.html; \
	elif command -v open > /dev/null; then \
		open cpu_top_interface.html; \
	else \
		echo "Please open cpu_top_interface.html in your browser"; \
	fi

# Analyze the design
.PHONY: analyze
analyze: generate-stubs
	@echo "Design Analysis:"
	@echo "================"
	@echo "Source files:"
	@for file in $(VERILOG_SOURCES); do \
		if [ -f "$$file" ]; then \
			lines=$$(wc -l < "$$file"); \
			echo "  $$(basename $$file): $$lines lines"; \
		fi; \
	done
	@echo ""
	@echo "Generated files:"
	@for file in cpu_top.pyi cpu_top_types.py cpu_top_interface.md; do \
		if [ -f "$$file" ]; then \
			size=$$(wc -c < "$$file"); \
			lines=$$(wc -l < "$$file"); \
			echo "  $$file: $$lines lines, $$size bytes"; \
		fi; \
	done

# Benchmark stub generation
.PHONY: benchmark
benchmark:
	@echo "Benchmarking stub generation..."
	@echo "==============================="
	@for i in 1 2 3; do \
		echo "Run $$i:"; \
		time python3 generate_stubs.py > /dev/null 2>&1; \
		echo ""; \
	done

# Interactive debugging
.PHONY: debug
debug: generate-stubs
	@echo "Running in debug mode with GUI..."
	$(MAKE) test SIM=$(SIM) GUI=1 WAVES=1 COCOTB_LOG_LEVEL=DEBUG

# Continuous integration target
.PHONY: ci
ci: clean generate-stubs typecheck lint test-all
	@echo "All CI checks passed!"

# Development setup
.PHONY: setup
setup:
	@echo "Setting up development environment..."
	@echo "Checking dependencies..."
	@python3 -c "import cocotb; print(f'cocotb version: {cocotb.__version__}')" || \
		echo "❌ cocotb not found - please install cocotb"
	@python3 -c "import mypy; print('✓ mypy available')" || \
		echo "⚠️  mypy not found - type checking will be skipped"
	@python3 -c "import flake8; print('✓ flake8 available')" || \
		echo "⚠️  flake8 not found - linting will be skipped"
	@which iverilog > /dev/null && echo "✓ Icarus Verilog available" || \
		echo "⚠️  Icarus Verilog not found"
	@which verilator > /dev/null && echo "✓ Verilator available" || \
		echo "⚠️  Verilator not found"



# Clean everything
.PHONY: clean-all
clean-all: clean clean-stubs
	@echo "Cleaned all generated files"

# Default target
.DEFAULT_GOAL := help 