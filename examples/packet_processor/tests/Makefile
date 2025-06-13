# Copyright cocotb contributors
# Licensed under the Revised BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-3-Clause

TOPLEVEL_LANG ?= verilog

PWD=$(shell pwd)

ifeq ($(TOPLEVEL_LANG),verilog)
    VERILOG_SOURCES = $(PWD)/../rtl/packet_processor.sv
    VERILOG_SOURCES += $(PWD)/../rtl/port_controller.sv
    VERILOG_SOURCES += $(PWD)/../rtl/packet_inspector.sv
    VERILOG_SOURCES += $(PWD)/../rtl/buffer_controller.sv
    VERILOG_SOURCES += $(PWD)/../rtl/flow_control_unit.sv
    VERILOG_SOURCES += $(PWD)/../rtl/additional_modules.sv
    # Compile options for SystemVerilog features
    ifeq ($(SIM),verilator)
        COMPILE_ARGS += --language 1800-2017
    else
        COMPILE_ARGS += -g2012
    endif
else
    $(error A valid value (verilog) was not provided for TOPLEVEL_LANG=$(TOPLEVEL_LANG))
endif

COCOTB_TOPLEVEL     := packet_processor
COCOTB_TEST_MODULES := test_packet_processor

# Use uv to run with cocotb 2.0
PYTHON ?= uv run python

include $(shell uv run cocotb-config --makefiles)/Makefile.sim 
