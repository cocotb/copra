module flow_control_unit #(
    parameter int UNIT_ID = 0,
    parameter int BUFFER_SIZE = 64,
    parameter string UNIT_NAME = "FLOW_CTRL"
) (
    input  logic            clk,
    input  logic            rst_n,
    input  logic            enable,
    
    // Flow control interface - LogicObject
    output logic            pause_req,
    input  logic            pause_ack,
    output logic            resume_req,
    input  logic            resume_ack,
    
    // Buffer status - LogicArrayObject
    output logic [7:0]      buffer_level,
    input  logic [7:0]      high_watermark,
    input  logic [7:0]      low_watermark,
    
    // Performance monitoring - RealObject
    output real             flow_efficiency,
    output real             pause_duration
);

// Internal state - EnumObject
typedef enum logic [1:0] {
    FLOW_NORMAL = 2'b00,
    FLOW_PAUSE  = 2'b01,
    FLOW_RESUME = 2'b10,
    FLOW_ERROR  = 2'b11
} flow_state_t;

flow_state_t current_flow_state;

// Integer counters - IntegerObject
integer pause_count;
integer resume_count;
integer total_cycles;
integer pause_cycles;

    // String for debug - StringObject - COMMENTED OUT FOR SIMULATOR COMPATIBILITY
    // string flow_status;

// Internal buffer simulation - ArrayObject
logic [31:0] internal_buffer [BUFFER_SIZE-1:0];
logic [7:0]  buffer_wr_ptr;
logic [7:0]  buffer_rd_ptr;
logic [7:0]  current_buffer_level;

// Buffer Controller - HierarchyObject (Level 4)
buffer_controller #(
    .CONTROLLER_ID(UNIT_ID),
    .DEPTH(BUFFER_SIZE)
) buffer_ctrl_inst (
    .clk(clk),
    .rst_n(rst_n),
    .enable(enable),
    
    // Buffer interface
    .wr_req(),
    .wr_data(),
    .wr_ack(),
    .rd_req(),
    .rd_data(),
    .rd_ack(),
    
    // Status
    .buffer_full(),
    .buffer_empty(),
    .buffer_count(),
    
    // Performance
    .access_efficiency(),
    .utilization_percent()
);

// Main flow control logic
always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        current_flow_state <= FLOW_NORMAL;
        pause_req <= 1'b0;
        resume_req <= 1'b0;
        buffer_wr_ptr <= 8'h0;
        buffer_rd_ptr <= 8'h0;
        current_buffer_level <= 8'h0;
        
        // Initialize counters
        pause_count <= 0;
        resume_count <= 0;
        total_cycles <= 0;
        pause_cycles <= 0;
        
        // Initialize string - COMMENTED OUT FOR SIMULATOR COMPATIBILITY
        // flow_status <= "INITIALIZING";
        
        // Initialize real values
        flow_efficiency <= 100.0;
        pause_duration <= 0.0;
        
    end else if (enable) begin
        total_cycles <= total_cycles + 1;
        
        case (current_flow_state)
            FLOW_NORMAL: begin
                // flow_status <= "NORMAL_FLOW"; // COMMENTED OUT FOR SIMULATOR COMPATIBILITY
                pause_req <= 1'b0;
                resume_req <= 1'b0;
                
                if (current_buffer_level >= high_watermark) begin
                    current_flow_state <= FLOW_PAUSE;
                    pause_req <= 1'b1;
                    pause_count <= pause_count + 1;
                end
            end
            
            FLOW_PAUSE: begin
                // flow_status <= "PAUSED"; // COMMENTED OUT FOR SIMULATOR COMPATIBILITY
                pause_cycles <= pause_cycles + 1;
                
                if (pause_ack) begin
                    pause_req <= 1'b0;
                end
                
                if (current_buffer_level <= low_watermark) begin
                    current_flow_state <= FLOW_RESUME;
                    resume_req <= 1'b1;
                end
            end
            
            FLOW_RESUME: begin
                // flow_status <= "RESUMING"; // COMMENTED OUT FOR SIMULATOR COMPATIBILITY
                
                if (resume_ack) begin
                    resume_req <= 1'b0;
                    current_flow_state <= FLOW_NORMAL;
                    resume_count <= resume_count + 1;
                end
            end
            
            FLOW_ERROR: begin
                // flow_status <= "ERROR_STATE"; // COMMENTED OUT FOR SIMULATOR COMPATIBILITY
                current_flow_state <= FLOW_NORMAL;
            end
        endcase
        
        // Calculate performance metrics
        if (total_cycles > 0) begin
            flow_efficiency <= (real'(total_cycles - pause_cycles) / real'(total_cycles)) * 100.0;
            pause_duration <= real'(pause_cycles) / real'(total_cycles + 1) * 100.0;
        end
        
        // Simulate buffer level changes
        if ($random % 10 == 0) begin
            if (current_buffer_level < BUFFER_SIZE - 1) begin
                current_buffer_level <= current_buffer_level + 1;
            end
        end else if ($random % 15 == 0) begin
            if (current_buffer_level > 0) begin
                current_buffer_level <= current_buffer_level - 1;
            end
        end
    end
end

// Output assignments
assign buffer_level = current_buffer_level;

endmodule 
