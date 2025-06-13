module channel_controller #(
    parameter ADDR_WIDTH = 32,
    parameter DATA_WIDTH = 64
) (
    input wire clk,
    input wire rst_n,
    input wire req,
    input wire [ADDR_WIDTH-1:0] addr,
    input wire [DATA_WIDTH-1:0] wdata,
    input wire wr_en,
    output reg ack,
    output reg [DATA_WIDTH-1:0] rdata,
    output reg valid
);

    reg [DATA_WIDTH-1:0] internal_buffer;
    reg [1:0] state;
    integer delay_counter;
    real utilization;
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            ack <= 1'b0;
            valid <= 1'b0;
            rdata <= 0;
            state <= 2'b00;
            delay_counter <= 0;
            utilization <= 0.0;
        end else begin
            case (state)
                2'b00: begin // IDLE
                    if (req) begin
                        state <= 2'b01;
                        delay_counter <= 3; // 3 cycle delay
                        utilization <= utilization + 0.1;
                    end
                end
                
                2'b01: begin // PROCESSING
                    if (delay_counter > 0) begin
                        delay_counter <= delay_counter - 1;
                    end else begin
                        ack <= 1'b1;
                        if (!wr_en) begin
                            rdata <= addr ^ wdata; // Simple read pattern
                            valid <= 1'b1;
                        end
                        state <= 2'b10;
                    end
                end
                
                2'b10: begin // COMPLETE
                    ack <= 1'b0;
                    valid <= 1'b0;
                    state <= 2'b00;
                end
                
                default: state <= 2'b00;
            endcase
        end
    end

endmodule
