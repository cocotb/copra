// Simple D Flip-Flop example
module dff (
    input wire clk,
    input wire rst_n,
    input wire d,
    output reg q
);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            q <= 1'b0;
        end else begin
            q <= d;
        end
    end

endmodule
