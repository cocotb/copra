module arbiter #(
    parameter CHANNELS = 4
) (
    input wire clk,
    input wire rst_n,
    input wire [CHANNELS-1:0] req,
    output reg [CHANNELS-1:0] grant,
    input wire [1:0] mode
);

    reg [CHANNELS-1:0] last_grant;
    integer round_robin_ptr;
    real channel_weights [0:CHANNELS-1];
    integer j;
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            grant <= 0;
            last_grant <= 0;
            round_robin_ptr <= 0;
            for (j = 0; j < CHANNELS; j = j + 1) begin
                channel_weights[j] <= 1.0;
            end
        end else begin
            grant <= 0;
            
            case (mode)
                2'b00: begin // ROUND_ROBIN
                    for (j = 0; j < CHANNELS; j = j + 1) begin
                        if (req[(round_robin_ptr + j) % CHANNELS]) begin
                            grant[(round_robin_ptr + j) % CHANNELS] <= 1'b1;
                            round_robin_ptr <= (round_robin_ptr + j + 1) % CHANNELS;
                            j = CHANNELS; // Break loop
                        end
                    end
                end
                
                2'b01: begin // FIXED_PRIORITY
                    for (j = CHANNELS-1; j >= 0; j = j - 1) begin
                        if (req[j]) begin
                            grant[j] <= 1'b1;
                            j = -1; // Break loop
                        end
                    end
                end
                
                2'b10: begin // WEIGHTED
                    // Simple weighted round robin
                    for (j = 0; j < CHANNELS; j = j + 1) begin
                        if (req[j] && channel_weights[j] > 0.5) begin
                            grant[j] <= 1'b1;
                            channel_weights[j] <= channel_weights[j] - 0.5;
                            j = CHANNELS; // Break loop
                        end else if (req[j]) begin
                            channel_weights[j] <= channel_weights[j] + 0.1;
                        end
                    end
                end
                
                default: grant <= req; // Pass through
            endcase
            
            last_grant <= grant;
        end
    end

endmodule 