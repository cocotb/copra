module port_controller #(
    parameter int PORT_ID = 0,
    parameter int FIFO_DEPTH = 256,
    parameter int MAX_PACKET_SIZE = 1500,
    parameter real LINK_SPEED_GBPS = 1.0
) (
    input  logic                clk,
    input  logic                rst_n,
    input  logic                enable,
    
    // Port interface - LogicObject and LogicArrayObject
    input  logic                rx_valid,
    input  logic [63:0]         rx_data,
    input  logic [7:0]          rx_keep,
    input  logic                rx_last,
    output logic                rx_ready,
    
    output logic                tx_valid,
    output logic [63:0]         tx_data,
    output logic [7:0]          tx_keep,
    output logic                tx_last,
    input  logic                tx_ready,
    
    // Configuration - EnumObject  
    input  logic [2:0]          port_mode,
    output logic                fifo_full,
    output logic                fifo_empty,
    
    // Statistics - IntegerObject and ArrayObject
    output logic [31:0]         rx_packet_count,
    output logic [31:0]         tx_packet_count,
    output logic [31:0]         rx_byte_count,
    output logic [31:0]         tx_byte_count,
    output logic [31:0]         dropped_packet_count,
    output logic [31:0]         error_packet_count
);

// Define local enum types - EnumObject
typedef enum logic [2:0] {
    PORT_MODE_DISABLED = 3'b000,
    PORT_MODE_ACCESS   = 3'b001,
    PORT_MODE_TRUNK    = 3'b010,
    PORT_MODE_HYBRID   = 3'b011,
    PORT_MODE_MIRROR   = 3'b100,
    PORT_MODE_LOOPBACK = 3'b101
} port_mode_t;

// Internal state enumeration - EnumObject
typedef enum logic [1:0] {
    PORT_STATE_IDLE  = 2'b00,
    PORT_STATE_RX    = 2'b01,
    PORT_STATE_TX    = 2'b10,
    PORT_STATE_ERROR = 2'b11
} port_state_t;

// Internal signals
port_state_t current_state;

// Integer counters - IntegerObject
integer internal_cycle_count;
integer packet_size_accumulator;
integer error_threshold;

// Real-valued monitoring - RealObject  
real current_utilization;
real average_packet_size;
real error_rate;
real bandwidth_efficiency;

// FIFO storage arrays - ArrayObject of LogicArrayObject
logic [63:0] rx_fifo_data [FIFO_DEPTH-1:0];
logic [7:0]  rx_fifo_keep [FIFO_DEPTH-1:0];
logic        rx_fifo_last [FIFO_DEPTH-1:0];
logic [63:0] tx_fifo_data [FIFO_DEPTH-1:0];
logic [7:0]  tx_fifo_keep [FIFO_DEPTH-1:0];
logic        tx_fifo_last [FIFO_DEPTH-1:0];

// FIFO pointers - LogicArrayObject
logic [7:0] rx_wr_ptr, rx_rd_ptr;
logic [7:0] tx_wr_ptr, tx_rd_ptr;
logic [7:0] rx_count, tx_count;

// Internal signals for packet inspector
logic inspector_ready;
logic inspector_header_valid;
logic [127:0] inspector_header_data;
logic [15:0] inspector_payload_size;
logic inspector_checksum_valid;
logic inspector_error_detected;
logic [3:0] inspector_error_type;
real inspector_inspection_latency;
real inspector_throughput_mbps;

// Generate block for flow control units - HierarchyArrayObject
genvar i;
generate
    for (i = 0; i < 4; i++) begin : gen_flow_control
        // Flow Control Unit instances - HierarchyObject
        flow_control_unit #(
            .UNIT_ID(i),
            .BUFFER_SIZE(FIFO_DEPTH/4)
        ) flow_ctrl_inst (
            .clk(clk),
            .rst_n(rst_n),
            .enable(enable),
            
            // Flow control signals
            .pause_req(),
            .pause_ack(),
            .resume_req(),
            .resume_ack(),
            
            // Buffer status
            .buffer_level(),
            .high_watermark(),
            .low_watermark(),
            
            // Performance monitoring
            .flow_efficiency(),
            .pause_duration()
        );
    end
endgenerate

// Packet Inspector - HierarchyObject
packet_inspector #(
    .INSPECTOR_ID(PORT_ID),
    .MAX_HEADER_SIZE(128)
) inspector_inst (
    .clk(clk),
    .rst_n(rst_n),
    .enable(enable),
    
    // Packet input
    .packet_valid(rx_valid),
    .packet_data(rx_data),
    .packet_keep(rx_keep),
    .packet_last(rx_last),
    .packet_ready(inspector_ready),
    
    // Inspection results
    .header_valid(inspector_header_valid),
    .header_data(inspector_header_data),
    .payload_size(inspector_payload_size),
    .checksum_valid(inspector_checksum_valid),
    
    // Error detection
    .error_detected(inspector_error_detected),
    .error_type(inspector_error_type),
    
    // Performance metrics
    .inspection_latency(inspector_inspection_latency),
    .throughput_mbps(inspector_throughput_mbps)
);

// Main state machine
always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        current_state <= PORT_STATE_IDLE;
        rx_wr_ptr <= 8'h0;
        rx_rd_ptr <= 8'h0;
        tx_wr_ptr <= 8'h0;
        tx_rd_ptr <= 8'h0;
        rx_count <= 8'h0;
        tx_count <= 8'h0;
        
        // Initialize counters
        rx_packet_count <= 32'h0;
        tx_packet_count <= 32'h0;
        rx_byte_count <= 32'h0;
        tx_byte_count <= 32'h0;
        dropped_packet_count <= 32'h0;
        error_packet_count <= 32'h0;
        
        internal_cycle_count <= 0;
        packet_size_accumulator <= 0;
        error_threshold <= 100;
        
        // Initialize real values
        current_utilization <= 0.0;
        average_packet_size <= 0.0;
        error_rate <= 0.0;
        bandwidth_efficiency <= 0.0;
        
    end else if (enable && port_mode != 3'b000) begin
        internal_cycle_count <= internal_cycle_count + 1;
        
        case (current_state)
            PORT_STATE_IDLE: begin
                if (rx_valid && !fifo_full) begin
                    current_state <= PORT_STATE_RX;
                end else if (tx_count > 0 && tx_ready) begin
                    current_state <= PORT_STATE_TX;
                end
            end
            
            PORT_STATE_RX: begin
                if (rx_valid && rx_ready) begin
                    // Store data in RX FIFO
                    rx_fifo_data[rx_wr_ptr] <= rx_data;
                    rx_fifo_keep[rx_wr_ptr] <= rx_keep;
                    rx_fifo_last[rx_wr_ptr] <= rx_last;
                    rx_wr_ptr <= rx_wr_ptr + 1;
                    rx_count <= rx_count + 1;
                    
                    // Update statistics
                    rx_byte_count <= rx_byte_count + $countones(rx_keep);
                    
                    if (rx_last) begin
                        rx_packet_count <= rx_packet_count + 1;
                        current_state <= PORT_STATE_IDLE;
                    end
                end
            end
            
            PORT_STATE_TX: begin
                if (tx_valid && tx_ready) begin
                    tx_rd_ptr <= tx_rd_ptr + 1;
                    tx_count <= tx_count - 1;
                    
                    // Update statistics
                    tx_byte_count <= tx_byte_count + $countones(tx_keep);
                    
                    if (tx_last) begin
                        tx_packet_count <= tx_packet_count + 1;
                        current_state <= PORT_STATE_IDLE;
                    end
                end
            end
            
            PORT_STATE_ERROR: begin
                error_packet_count <= error_packet_count + 1;
                current_state <= PORT_STATE_IDLE;
            end
        endcase
        
        // Real-time calculations
        if (internal_cycle_count > 0) begin
            current_utilization <= (real'(rx_count + tx_count) / real'(FIFO_DEPTH)) * 100.0;
            if (rx_packet_count > 0) begin
                average_packet_size <= real'(rx_byte_count) / real'(rx_packet_count);
            end
            error_rate <= real'(error_packet_count) / real'(rx_packet_count + 1) * 100.0;
            bandwidth_efficiency <= LINK_SPEED_GBPS * current_utilization / 100.0;
        end
    end
end

// FIFO control logic
assign fifo_full = (rx_count >= FIFO_DEPTH - 1);
assign fifo_empty = (rx_count == 0);
assign rx_ready = !fifo_full && (port_mode != PORT_MODE_DISABLED);

// TX data output from FIFO
assign tx_valid = (tx_count > 0) && (current_state == PORT_STATE_TX);
assign tx_data = tx_fifo_data[tx_rd_ptr];
assign tx_keep = tx_fifo_keep[tx_rd_ptr];
assign tx_last = tx_fifo_last[tx_rd_ptr];

endmodule 
