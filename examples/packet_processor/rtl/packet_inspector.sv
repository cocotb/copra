module packet_inspector #(
    parameter int INSPECTOR_ID = 0,
    parameter int MAX_HEADER_SIZE = 128,
    parameter string INSPECTOR_NAME = "PKT_INSPECTOR"
) (
    input  logic            clk,
    input  logic            rst_n,
    input  logic            enable,
    
    // Packet input - LogicObject and LogicArrayObject
    input  logic            packet_valid,
    input  logic [63:0]     packet_data,
    input  logic [7:0]      packet_keep,
    input  logic            packet_last,
    output logic            packet_ready,
    
    // Inspection results - LogicObject and LogicArrayObject
    output logic            header_valid,
    output logic [127:0]    header_data,
    output logic [15:0]     payload_size,
    output logic            checksum_valid,
    
    // Error detection - LogicObject and EnumObject
    output logic            error_detected,
    output logic [3:0]      error_type,
    
    // Performance metrics - RealObject
    output real             inspection_latency,
    output real             throughput_mbps
);

// Error type enumeration - EnumObject
typedef enum logic [3:0] {
    ERROR_NONE       = 4'h0,
    ERROR_CHECKSUM   = 4'h1,
    ERROR_LENGTH     = 4'h2,
    ERROR_FORMAT     = 4'h3,
    ERROR_PROTOCOL   = 4'h4,
    ERROR_TIMEOUT    = 4'h5,
    ERROR_OVERFLOW   = 4'h6,
    ERROR_UNDERFLOW  = 4'h7,
    ERROR_UNKNOWN    = 4'hF
} error_type_t;

// Inspection state - EnumObject
typedef enum logic [2:0] {
    INSPECT_IDLE     = 3'b000,
    INSPECT_HEADER   = 3'b001,
    INSPECT_PAYLOAD  = 3'b010,
    INSPECT_CHECKSUM = 3'b011,
    INSPECT_COMPLETE = 3'b100,
    INSPECT_ERROR    = 3'b101
} inspection_state_t;

inspection_state_t current_inspection_state;
error_type_t current_error_type;

// Internal counters and metrics - IntegerObject
integer packets_inspected;
integer bytes_processed;
integer inspection_cycles;
integer error_count;
integer checksum_failures;

    // String debug information - StringObject - COMMENTED OUT FOR SIMULATOR COMPATIBILITY
    // string inspection_status;
    // string last_error_description;

// Header storage - ArrayObject of LogicArrayObject
logic [63:0] header_buffer [16-1:0];  // 16 x 64-bit = 1024 bits max header
logic [7:0]  header_byte_count;
logic [3:0]  header_word_count;

// Performance tracking - RealObject
real packets_per_second;
real bytes_per_second;
real error_percentage;

// Main inspection logic
always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        current_inspection_state <= INSPECT_IDLE;
        current_error_type <= ERROR_NONE;
        header_valid <= 1'b0;
        checksum_valid <= 1'b0;
        error_detected <= 1'b0;
        // packet_ready handled by continuous assignment
        
        header_data <= 128'h0;
        payload_size <= 16'h0;
        error_type <= 4'h0;
        header_byte_count <= 8'h0;
        header_word_count <= 4'h0;
        
        // Initialize counters
        packets_inspected <= 0;
        bytes_processed <= 0;
        inspection_cycles <= 0;
        error_count <= 0;
        checksum_failures <= 0;
        
        // Initialize strings - COMMENTED OUT FOR SIMULATOR COMPATIBILITY
        // inspection_status <= "IDLE";
        // last_error_description <= "NO_ERROR";
        
        // Initialize performance metrics
        inspection_latency <= 0.0;
        throughput_mbps <= 0.0;
        packets_per_second <= 0.0;
        bytes_per_second <= 0.0;
        error_percentage <= 0.0;
        
    end else if (enable) begin
        inspection_cycles <= inspection_cycles + 1;
        
        case (current_inspection_state)
            INSPECT_IDLE: begin
                // inspection_status <= "WAITING"; // COMMENTED OUT FOR SIMULATOR COMPATIBILITY
                // packet_ready handled by continuous assignment
                header_valid <= 1'b0;
                error_detected <= 1'b0;
                
                if (packet_valid) begin
                    current_inspection_state <= INSPECT_HEADER;
                    header_word_count <= 4'h0;
                    header_byte_count <= 8'h0;
                    // inspection_status <= "INSPECTING_HEADER"; // COMMENTED OUT FOR SIMULATOR COMPATIBILITY
                end
            end
            
            INSPECT_HEADER: begin
                if (packet_valid && packet_ready) begin
                    // Store header data
                    header_buffer[header_word_count] <= packet_data;
                    header_word_count <= header_word_count + 1;
                    header_byte_count <= header_byte_count + $countones(packet_keep);
                    bytes_processed <= bytes_processed + $countones(packet_keep);
                    
                    // Simple header validation (check for valid Ethernet header)
                    if (header_word_count == 0) begin
                        // Check if first 6 bytes look like a MAC address (not all zeros or all ones)
                        if (packet_data[47:0] == 48'h0 || packet_data[47:0] == 48'hFFFFFFFFFFFF) begin
                            current_error_type <= ERROR_FORMAT;
                            current_inspection_state <= INSPECT_ERROR;
                            // last_error_description <= "INVALID_MAC"; // COMMENTED OUT FOR SIMULATOR COMPATIBILITY
                        end
                    end
                    
                    // Move to payload inspection after reasonable header size
                    if (header_byte_count >= 64 || packet_last) begin
                        current_inspection_state <= INSPECT_PAYLOAD;
                        // inspection_status <= "INSPECTING_PAYLOAD"; // COMMENTED OUT FOR SIMULATOR COMPATIBILITY
                        header_data <= {header_buffer[1], header_buffer[0]};
                        header_valid <= 1'b1;
                    end
                end
            end
            
            INSPECT_PAYLOAD: begin
                if (packet_valid && packet_ready) begin
                    bytes_processed <= bytes_processed + $countones(packet_keep);
                    
                    if (packet_last) begin
                        current_inspection_state <= INSPECT_CHECKSUM;
                        // inspection_status <= "CHECKING_CHECKSUM"; // COMMENTED OUT FOR SIMULATOR COMPATIBILITY
                        payload_size <= bytes_processed - header_byte_count;
                    end
                end
            end
            
            INSPECT_CHECKSUM: begin
                // Simple checksum validation (simplified for demo)
                if (($random % 100) < 95) begin  // 95% pass rate
                    checksum_valid <= 1'b1;
                    current_inspection_state <= INSPECT_COMPLETE;
                    // inspection_status <= "CHECKSUM_VALID"; // COMMENTED OUT FOR SIMULATOR COMPATIBILITY
                end else begin
                    current_error_type <= ERROR_CHECKSUM;
                    current_inspection_state <= INSPECT_ERROR;
                    checksum_failures <= checksum_failures + 1;
                    // last_error_description <= "CHECKSUM_FAIL"; // COMMENTED OUT FOR SIMULATOR COMPATIBILITY
                end
            end
            
            INSPECT_COMPLETE: begin
                // inspection_status <= "COMPLETE"; // COMMENTED OUT FOR SIMULATOR COMPATIBILITY
                packets_inspected <= packets_inspected + 1;
                current_inspection_state <= INSPECT_IDLE;
            end
            
            INSPECT_ERROR: begin
                // inspection_status <= "ERROR_DETECTED"; // COMMENTED OUT FOR SIMULATOR COMPATIBILITY
                error_detected <= 1'b1;
                error_type <= current_error_type;
                error_count <= error_count + 1;
                current_inspection_state <= INSPECT_IDLE;
            end
        endcase
        
        // Calculate performance metrics
        if (inspection_cycles > 1000) begin  // After some warm-up time
            packets_per_second <= real'(packets_inspected) / (real'(inspection_cycles) / 156.25e6) ;
            bytes_per_second <= real'(bytes_processed) / (real'(inspection_cycles) / 156.25e6);
            throughput_mbps <= bytes_per_second * 8.0 / 1e6;
            inspection_latency <= real'(inspection_cycles) / real'(packets_inspected + 1);
            
            if (packets_inspected > 0) begin
                error_percentage <= real'(error_count) / real'(packets_inspected) * 100.0;
            end
        end
    end
end

// Output assignments
assign packet_ready = (current_inspection_state == INSPECT_IDLE) || 
                     (current_inspection_state == INSPECT_HEADER) || 
                     (current_inspection_state == INSPECT_PAYLOAD);

endmodule 
