module buffer_controller #(
    parameter int CONTROLLER_ID = 0,
    parameter int DEPTH = 64
) (
    input  logic            clk,
    input  logic            rst_n,
    input  logic            enable,
    
    // Buffer interface - LogicObject and LogicArrayObject
    input  logic            wr_req,
    input  logic [31:0]     wr_data,
    output logic            wr_ack,
    input  logic            rd_req,
    output logic [31:0]     rd_data,
    output logic            rd_ack,
    
    // Status - LogicObject and LogicArrayObject
    output logic            buffer_full,
    output logic            buffer_empty,
    output logic [7:0]      buffer_count,
    
    // Performance - RealObject
    output real             access_efficiency,
    output real             utilization_percent
);

// Buffer state enumeration - EnumObject
typedef enum logic [1:0] {
    BUF_IDLE   = 2'b00,
    BUF_WRITE  = 2'b01,
    BUF_READ   = 2'b10,
    BUF_FULL   = 2'b11
} buffer_state_t;

buffer_state_t current_buffer_state;

// Internal storage - ArrayObject of LogicArrayObject
logic [31:0] memory_array [DEPTH-1:0];
logic [7:0]  wr_pointer;
logic [7:0]  rd_pointer;
logic [7:0]  current_count;

// Performance counters - IntegerObject
integer write_operations;
integer read_operations;
integer total_accesses;
integer stall_cycles;

// Performance metrics - RealObject
real write_bandwidth;
real read_bandwidth;
real average_latency;

// Control logic
always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        current_buffer_state <= BUF_IDLE;
        wr_pointer <= 8'h0;
        rd_pointer <= 8'h0;
        current_count <= 8'h0;
        wr_ack <= 1'b0;
        rd_ack <= 1'b0;
        rd_data <= 32'h0;
        
        // Initialize performance counters
        write_operations <= 0;
        read_operations <= 0;
        total_accesses <= 0;
        stall_cycles <= 0;
        
        // Initialize performance metrics
        write_bandwidth <= 0.0;
        read_bandwidth <= 0.0;
        average_latency <= 0.0;
        access_efficiency <= 100.0;
        utilization_percent <= 0.0;
        
    end else if (enable) begin
        // Default acknowledgment clearing
        wr_ack <= 1'b0;
        rd_ack <= 1'b0;
        
        case (current_buffer_state)
            BUF_IDLE: begin
                if (wr_req && !buffer_full) begin
                    current_buffer_state <= BUF_WRITE;
                end else if (rd_req && !buffer_empty) begin
                    current_buffer_state <= BUF_READ;
                end else if ((wr_req && buffer_full) || (rd_req && buffer_empty)) begin
                    stall_cycles <= stall_cycles + 1;
                end
            end
            
            BUF_WRITE: begin
                memory_array[wr_pointer] <= wr_data;
                wr_pointer <= wr_pointer + 1;
                current_count <= current_count + 1;
                wr_ack <= 1'b1;
                write_operations <= write_operations + 1;
                total_accesses <= total_accesses + 1;
                
                if (current_count >= DEPTH - 1) begin
                    current_buffer_state <= BUF_FULL;
                end else begin
                    current_buffer_state <= BUF_IDLE;
                end
            end
            
            BUF_READ: begin
                rd_data <= memory_array[rd_pointer];
                rd_pointer <= rd_pointer + 1;
                current_count <= current_count - 1;
                rd_ack <= 1'b1;
                read_operations <= read_operations + 1;
                total_accesses <= total_accesses + 1;
                current_buffer_state <= BUF_IDLE;
            end
            
            BUF_FULL: begin
                if (rd_req && !rd_ack) begin
                    current_buffer_state <= BUF_READ;
                end
            end
        endcase
        
        // Calculate performance metrics
        if (total_accesses > 0) begin
            write_bandwidth <= real'(write_operations) / real'(total_accesses + stall_cycles) * 100.0;
            read_bandwidth <= real'(read_operations) / real'(total_accesses + stall_cycles) * 100.0;
            access_efficiency <= real'(total_accesses) / real'(total_accesses + stall_cycles) * 100.0;
            average_latency <= real'(stall_cycles) / real'(total_accesses);
        end
        
        utilization_percent <= real'(current_count) / real'(DEPTH) * 100.0;
    end
end

// Status outputs
assign buffer_full = (current_count >= DEPTH);
assign buffer_empty = (current_count == 0);
assign buffer_count = current_count;

endmodule 