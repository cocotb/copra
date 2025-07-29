// This file is public domain, it can be freely copied without restrictions.
// SPDX-License-Identifier: CC0-1.0
// Adder DUT
`timescale 1ns/1ps

module adder #(
  parameter integer DATA_WIDTH = 4
) (
  input  logic unsigned [DATA_WIDTH-1:0] A,
  input  logic unsigned [DATA_WIDTH-1:0] B,
  output logic unsigned [DATA_WIDTH:0]   X
);

  assign X = A + B;

  generate
    for (genvar i = 0; i < DATA_WIDTH; i++) begin : gen_debug_regs
      logic [DATA_WIDTH-1:0] debug_a_local;
      logic [DATA_WIDTH-1:0] debug_b_local;
      logic debug_valid;
      always_ff @(posedge 1'b1) begin
        debug_a_local <= A;
        debug_b_local <= B;
        debug_valid <= 1'b1;
      end
    end
  endgenerate

  // Dump waves
  initial begin
    $dumpfile("dump.vcd");
    $dumpvars(1, adder);
  end

endmodule
