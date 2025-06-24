# Copyright cocotb contributors
# Licensed under the Revised BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-3-Clause

TOPLEVEL_LANG ?= verilog

PWD=$(shell pwd)

ifeq ($(TOPLEVEL_LANG),verilog)
    VERILOG_SOURCES = $(PWD)/../rtl/dsp_pipeline.sv
    VERILOG_SOURCES += $(PWD)/../rtl/processing_stage.sv
    VERILOG_SOURCES += $(PWD)/../rtl/channel_processor.sv
    VERILOG_SOURCES += $(PWD)/../rtl/filter_tap.sv
    VERILOG_SOURCES += $(PWD)/../rtl/fft_butterfly.sv
    # Note: fft_butterfly module is defined within filter_tap.sv
    # Compile options for SystemVerilog features
    COMPILE_ARGS += -g2012
else
    $(error A valid value (verilog) was not provided for TOPLEVEL_LANG=$(TOPLEVEL_LANG))
endif

COCOTB_TOPLEVEL     := dsp_pipeline
COCOTB_TEST_MODULES := copra.integration.autostub,test_dsp_pipeline

# Use uv to run with cocotb 2.0
PYTHON ?= uv run python

export COPRA_STUB_DIR=$(PWD)/copra_stubs

include $(shell uv run cocotb-config --makefiles)/Makefile.sim 
