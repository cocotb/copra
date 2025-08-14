# Copyright copra contributors
# Licensed under the Revised BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-3-Clause

TOPLEVEL_LANG ?= verilog

PWD=$(shell pwd)

ifeq ($(TOPLEVEL_LANG),verilog)
    VERILOG_SOURCES = $(PWD)/../rtl/multi_dim_array_pkg.sv $(PWD)/../rtl/multi_dim_array.sv
else
    $(error multi_dim_array example only supports verilog (TOPLEVEL_LANG=$(TOPLEVEL_LANG)))
endif

SIM ?= icarus

COCOTB_TOPLEVEL := multi_dim_array
COCOTB_TEST_MODULES := copra.integration.autostub,test_multi_dim_array

include $(shell cocotb-config --makefiles)/Makefile.sim 

gen_stubs:
	COCOTB_TOPLEVEL=$(COCOTB_TOPLEVEL) \
	TOPLEVEL_LANG=$(TOPLEVEL_LANG) \
	VERILOG_SOURCES="$(VERILOG_SOURCES)" \
	VHDL_SOURCES="$(VHDL_SOURCES)" \
	$(shell cocotb-config --python-bin) $(shell pwd)/../../../src/copra/integration/standalone_stubgen.py 
