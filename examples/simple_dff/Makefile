# Makefile for simple DFF example

TOPLEVEL_LANG ?= verilog
VERILOG_SOURCES = $(shell pwd)/dff.sv
TOPLEVEL = dff
MODULE = test_dff

include $(shell cocotb-config --makefiles)/Makefile.sim

# Generate stubs with copra
generate-stubs:
	copra $(TOPLEVEL) -o dut.pyi

.PHONY: generate-stubs
