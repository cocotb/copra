# Copyright cocotb contributors
# Licensed under the Revised BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-3-Clause

TOPLEVEL_LANG ?= verilog

PWD=$(shell pwd)

# Use uv to run with cocotb 2.0
PYTHON ?= uv run python

ifeq ($(TOPLEVEL_LANG),verilog)
    VERILOG_SOURCES = $(PWD)/../rtl/dff.sv
else
    $(error A valid value (verilog) was not provided for TOPLEVEL_LANG=$(TOPLEVEL_LANG))
endif

COCOTB_TOPLEVEL     := dff
COCOTB_TEST_MODULES := copra.integration.autostub,test_dff

export COPRA_STUB_DIR=$(PWD)/copra_stubs

include $(shell uv run cocotb-config --makefiles)/Makefile.sim 
