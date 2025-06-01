# Makefile for minimal example

TOPLEVEL_LANG ?= verilog
VERILOG_SOURCES = $(shell pwd)/minimal.sv
TOPLEVEL = minimal
MODULE = test_minimal

include $(shell cocotb-config --makefiles)/Makefile.sim

# Generate stubs with copra
generate-stubs:
	python generate_stubs.py

.PHONY: generate-stubs

# Run tests
test: generate-stubs
	make SIM=icarus TOPLEVEL_LANG=$(TOPLEVEL_LANG) TOPLEVEL=$(TOPLEVEL) MODULE=$(MODULE)

.PHONY: test
