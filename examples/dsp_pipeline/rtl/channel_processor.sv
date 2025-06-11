module channel_processor #(
    parameter DATA_WIDTH = 32,
    parameter CHANNEL_ID = 0
) (
    input wire clk,
    input wire rst_n,
    input wire [DATA_WIDTH-1:0] data_in,
    input wire valid_in,
    output reg [DATA_WIDTH-1:0] data_out,
    output reg valid_out,
    input wire [1:0] filter_type,
    input real gain
);

    // Channel-specific enums
    typedef enum logic [1:0] {
        CH_MODE_NORMAL = 2'b00,
        CH_MODE_BYPASS = 2'b01,
        CH_MODE_MUTE   = 2'b10,
        CH_MODE_TEST   = 2'b11
    } channel_mode_t;
    
    channel_mode_t channel_mode;

    reg [DATA_WIDTH-1:0] channel_buffer;
    integer samples_processed;
    real channel_gain;
    real channel_offset;
    string channel_name;
    string channel_status;
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            data_out <= 0;
            valid_out <= 1'b0;
            channel_buffer <= 0;
            samples_processed <= 0;
            channel_gain <= 1.0;
            channel_offset <= 0.0;
            channel_mode <= CH_MODE_NORMAL;
            case (CHANNEL_ID)
                0: begin
                    channel_name = "CH0_LEFT";
                    channel_status = "LEFT_ACTIVE";
                end
                1: begin
                    channel_name = "CH1_RIGHT";
                    channel_status = "RIGHT_ACTIVE";
                end
                2: begin
                    channel_name = "CH2_AUX1";
                    channel_status = "AUX1_ACTIVE";
                end
                3: begin
                    channel_name = "CH3_AUX2";
                    channel_status = "AUX2_ACTIVE";
                end
                default: begin
                    channel_name = "CH_UNKNOWN";
                    channel_status = "UNKNOWN_STATE";
                end
            endcase
        end else begin
            if (valid_in) begin
                channel_buffer <= data_in;
                // Apply channel-specific gain
                data_out <= $rtoi(data_in * gain * channel_gain);
                valid_out <= 1'b1;
                samples_processed <= samples_processed + 1;
                channel_gain <= gain + (CHANNEL_ID * 0.1);
                channel_offset <= $sin(samples_processed * 0.01) * 0.1;
                channel_status = "PROCESSING";
            end else begin
                valid_out <= 1'b0;
                channel_status = "IDLE";
            end
        end
    end

endmodule