// This file is public domain, it can be freely copied without restrictions.
// SPDX-License-Identifier: CC0-1.0

`timescale 1us/1us

module dff (
  input logic clk, d,
  input logic _reset_n,  // starts with underscore hence needs __getitem__ access
  output logic q,
  output logic \!special!\  // escaped identifier hence needs __getitem__ access
);

always @(posedge clk) begin
  if (!_reset_n) begin
    q <= 1'b0;
    \!special!\ <= 1'b0;
  end else begin
    q <= d;
    \!special!\ <= ~d;  // invert d for the special signal
  end
end

endmodule
