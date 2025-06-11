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

// Sub-module: FFT Butterfly
module fft_butterfly #(
    parameter DATA_WIDTH = 32,
    parameter BUTTERFLY_ID = 0
) (
    input wire clk,
    input wire rst_n,
    input wire [DATA_WIDTH-1:0] real_in,
    input wire [DATA_WIDTH-1:0] imag_in,
    output reg [DATA_WIDTH-1:0] real_out,
    output reg [DATA_WIDTH-1:0] imag_out,
    input wire enable
);

    // Butterfly-specific enums
    typedef enum logic [1:0] {
        BF_IDLE = 2'b00,
        BF_CALC = 2'b01,
        BF_DONE = 2'b10,
        BF_ERR  = 2'b11
    } butterfly_state_t;
    
    butterfly_state_t bf_state;

    integer computation_cycles;
    real butterfly_efficiency;
    string butterfly_status;
    string computation_mode;
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            real_out <= 0;
            imag_out <= 0;
            computation_cycles <= 0;
            butterfly_efficiency <= 100.0;
            bf_state <= BF_IDLE;
            butterfly_status = "INIT";
            computation_mode = "RADIX2";
        end else begin
            if (enable) begin
                // Simple butterfly computation
                real_out <= real_in + imag_in;
                imag_out <= real_in - imag_in;
                computation_cycles <= computation_cycles + 1;
                butterfly_efficiency <= computation_cycles * 100.0 / (computation_cycles + BUTTERFLY_ID + 1);
                bf_state <= BF_CALC;
                butterfly_status = "COMPUTING";
                computation_mode = "ACTIVE";
            end else begin
                real_out <= 0;
                imag_out <= 0;
                bf_state <= BF_IDLE;
                butterfly_status = "IDLE";
                computation_mode = "STANDBY";
            end
        end
    end

endmodule 