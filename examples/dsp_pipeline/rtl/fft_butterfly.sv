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