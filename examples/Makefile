# Copyright cocotb contributors
# Licensed under the Revised BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-3-Clause

EXAMPLES := dff \
            memory_controller \
            dsp_pipeline \
            packet_processor \
            cpu

EXAMPLE_TESTS := $(addsuffix /tests,$(EXAMPLES))

.PHONY: $(EXAMPLE_TESTS)

.PHONY: all
all: $(EXAMPLE_TESTS)

$(EXAMPLE_TESTS):
	@cd $@ && $(MAKE)

copra:
	for example in $(EXAMPLES); do \
		uv run copra generate $$example --top $$example; \
	done

.PHONY: clean
clean:
	$(foreach TEST, $(EXAMPLE_TESTS), $(MAKE) -C $(TEST) clean;)