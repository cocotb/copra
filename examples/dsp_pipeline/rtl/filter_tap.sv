module filter_tap #(
    parameter DATA_WIDTH = 32,
    parameter COEFF_WIDTH = 16,
    parameter TAP_ID = 0
) (
    input wire clk,
    input wire rst_n,
    input wire [DATA_WIDTH-1:0] data_in,
    input wire [COEFF_WIDTH-1:0] coeff,
    output reg [DATA_WIDTH-1:0] data_out,
    input wire enable
);

    // Tap-specific enums
    typedef enum logic [1:0] {
        TAP_IDLE    = 2'b00,
        TAP_ACTIVE  = 2'b01,
        TAP_BYPASS  = 2'b10,
        TAP_ERROR   = 2'b11
    } tap_state_t;
    
    tap_state_t tap_state;

    reg [DATA_WIDTH-1:0] tap_buffer;
    integer multiply_operations;
    real tap_utilization;
    string tap_status;
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            data_out <= 0;
            tap_buffer <= 0;
            multiply_operations <= 0;
            tap_utilization <= 0.0;
            tap_state <= TAP_IDLE;
            tap_status = "INIT";
        end else begin
            if (enable) begin
                tap_buffer <= data_in;
                // Simple multiply-accumulate
                data_out <= (data_in * coeff) >> (COEFF_WIDTH - 8);
                multiply_operations <= multiply_operations + 1;
                tap_utilization <= multiply_operations * 100.0 / (multiply_operations + TAP_ID + 1);
                tap_state <= TAP_ACTIVE;
                tap_status = "ACTIVE";
            end else begin
                data_out <= data_in; // Pass through when disabled
                tap_state <= TAP_BYPASS;
                tap_status = "BYPASS";
            end
        end
    end

endmodule
