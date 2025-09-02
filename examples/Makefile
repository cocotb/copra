# Copyright cocotb contributors
# Licensed under the Revised BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-3-Clause

EXAMPLES := adder/tests \
            simple_dff \
            matrix_multiplier/tests \
            multi_dim_array/tests
ifeq ($(TOPLEVEL_LANG),verilog)
    ifeq ($(SIM),$(filter $(SIM),ius xcelium))
        ifeq (,$(shell which spectre))
            $(info Skipping example mixed_signal since Spectre is not available)
        else
            EXAMPLES += mixed_signal/tests
        endif
    else
        $(info Skipping example mixed_signal since only Xcelium is supported)
    endif
    EXAMPLES += doc_examples/quickstart
endif

.PHONY: $(EXAMPLES)

.PHONY: all
all: $(EXAMPLES)

$(EXAMPLES):
	@cd $@ && $(MAKE)

# there's a copra target in each example's Makefile
copra:
	$(foreach TEST, $(EXAMPLES), $(MAKE) -C $(TEST) copra;)

gen_stubs:
	$(foreach TEST, $(EXAMPLES), $(MAKE) -C $(TEST) gen_stubs;)

.PHONY: clean
clean:
	$(foreach TEST, $(EXAMPLES), $(MAKE) -C $(TEST) clean;)

regression:
	$(foreach TEST, $(EXAMPLES), $(MAKE) -C $(TEST) regression;)
