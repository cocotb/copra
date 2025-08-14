# This file is public domain, it can be freely copied without restrictions.
# SPDX-License-Identifier: CC0-1.0

TOPLEVEL_LANG ?= verilog

ifeq ($(TOPLEVEL_LANG),verilog)
  VERILOG_SOURCES = $(shell pwd)/dff.sv
else ifeq ($(TOPLEVEL_LANG),vhdl)
  VHDL_SOURCES = $(shell pwd)/dff.vhdl
endif

COCOTB_TEST_MODULES = copra.integration.autostub,test_dff
COCOTB_TOPLEVEL = dff

include $(shell cocotb-config --makefiles)/Makefile.sim

gen_stubs:
	COCOTB_TOPLEVEL=$(COCOTB_TOPLEVEL) \
	TOPLEVEL_LANG=$(TOPLEVEL_LANG) \
	VERILOG_SOURCES="$(VERILOG_SOURCES)" \
	VHDL_SOURCES="$(VHDL_SOURCES)" \
	$(shell cocotb-config --python-bin) $(shell pwd)/../../src/copra/integration/standalone_stubgen.py
