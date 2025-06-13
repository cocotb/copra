module processing_stage #(
    parameter DATA_WIDTH = 32,
    parameter STAGE_ID = 0
) (
    input wire clk,
    input wire rst_n,
    input wire [DATA_WIDTH-1:0] data_in,
    input wire valid_in,
    output reg [DATA_WIDTH-1:0] data_out,
    output reg valid_out,
    input wire enable,
    input wire [2:0] stage_type
);

    // Stage-specific enums
    typedef enum logic [1:0] {
        STAGE_STATE_IDLE = 2'b00,
        STAGE_STATE_PROC = 2'b01,
        STAGE_STATE_DONE = 2'b10,
        STAGE_STATE_ERR  = 2'b11
    } stage_state_t;
    
    stage_state_t internal_state;
    
    reg [DATA_WIDTH-1:0] internal_register;
    integer operation_count;
    real stage_efficiency;
    string stage_status;
    string processing_mode;
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            data_out <= 0;
            valid_out <= 1'b0;
            internal_register <= 0;
            operation_count <= 0;
            stage_efficiency <= 100.0;
            internal_state <= STAGE_STATE_IDLE;
            stage_status = "INIT";
            processing_mode = "NORMAL";
        end else begin
            if (enable && valid_in) begin
                // Simple processing - add stage ID to data
                data_out <= data_in + STAGE_ID;
                valid_out <= 1'b1;
                internal_register <= data_in;
                operation_count <= operation_count + 1;
                stage_efficiency <= operation_count * 100.0 / (operation_count + 1);
                internal_state <= STAGE_STATE_PROC;
                stage_status = "PROCESSING";
                processing_mode = "ACTIVE";
            end else begin
                valid_out <= 1'b0;
                internal_state <= STAGE_STATE_IDLE;
                if (!enable) begin
                    stage_status = "DISABLED";
                    processing_mode = "STANDBY";
                end else begin
                    stage_status = "WAITING";
                    processing_mode = "IDLE";
                end
            end
        end
    end

endmodule
