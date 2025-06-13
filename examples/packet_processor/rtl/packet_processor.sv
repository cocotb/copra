module packet_processor #(
    // Parameters to exercise IntegerObject
    parameter int NUM_PORTS = 8,
    parameter int PACKET_BUFFER_DEPTH = 1024,
    parameter int MAX_PACKET_SIZE = 1500,
    parameter int FIFO_DEPTH = 256,
    parameter int NUM_PRIORITY_LEVELS = 4,
    parameter int STATS_COUNTER_WIDTH = 32,
    parameter int ROUTING_TABLE_SIZE = 256,
    
    // Parameters to exercise RealObject  
    parameter real CLOCK_FREQUENCY = 156.25e6,  // 156.25 MHz
    parameter real BANDWIDTH_GBPS = 10.0,
    parameter real LATENCY_TARGET_NS = 50.0,
    parameter real POWER_BUDGET_WATTS = 25.5,
    parameter real TEMPERATURE_THRESHOLD = 85.0,
    
    // String parameters to exercise StringObject
    parameter string DEVICE_NAME = "NPP-1000",
    parameter string VERSION_STRING = "v2.1.0",
    parameter string BUILD_DATE = "2024-01-15",
    parameter string VENDOR_ID = "ACME_CORP"
) (
    // Clock and reset
    input  logic                    clk,
    input  logic                    rst_n,
    
    // Enable and control signals - LogicObject
    input  logic                    enable,
    input  logic                    bypass_mode,
    input  logic                    debug_enable,
    input  logic                    test_mode,
    input  logic                    power_save_mode,
    
    // Status outputs - LogicObject  
    output logic                    ready,
    output logic                    error,
    output logic                    overflow,
    output logic                    underflow,
    output logic                    link_up,
    
    // Configuration - LogicArrayObject
    input  logic [15:0]            config_addr,
    input  logic [31:0]            config_data,
    input  logic [3:0]             config_strobe,
    output logic [31:0]            config_readdata,
    
    // Network Interface Arrays - will create ArrayObject of LogicArrayObject
    input  logic [NUM_PORTS-1:0]   port_rx_valid,
    input  logic [NUM_PORTS-1:0]   port_tx_ready,
    output logic [NUM_PORTS-1:0]   port_rx_ready,
    output logic [NUM_PORTS-1:0]   port_tx_valid,
    
    // Packet data buses - LogicArrayObject  
    input  logic [NUM_PORTS*64-1:0] port_rx_data,
    input  logic [NUM_PORTS*8-1:0]  port_rx_keep,
    input  logic [NUM_PORTS-1:0]    port_rx_last,
    output logic [NUM_PORTS*64-1:0] port_tx_data,
    output logic [NUM_PORTS*8-1:0]  port_tx_keep,
    output logic [NUM_PORTS-1:0]    port_tx_last,
    
    // Statistics and monitoring - IntegerObject when accessed individually
    output logic [STATS_COUNTER_WIDTH-1:0] total_packets_rx,
    output logic [STATS_COUNTER_WIDTH-1:0] total_packets_tx,
    output logic [STATS_COUNTER_WIDTH-1:0] total_bytes_rx,
    output logic [STATS_COUNTER_WIDTH-1:0] total_bytes_tx,
    output logic [STATS_COUNTER_WIDTH-1:0] dropped_packets,
    output logic [STATS_COUNTER_WIDTH-1:0] error_packets,
    
    // Real-time monitoring - RealObject
    output real                     current_throughput_gbps,
    output real                     average_latency_ns,
    output real                     current_power_watts,
    output real                     junction_temperature,
    output real                     link_utilization_percent,
    
    // Debug and identification strings - StringObject
    output logic [8*32-1:0]        device_name_out,      // 32 char string
    output logic [8*16-1:0]        version_string_out,   // 16 char string  
    output logic [8*12-1:0]        build_date_out,       // 12 char string
    output logic [8*16-1:0]        vendor_id_out,        // 16 char string
    output logic [8*64-1:0]        debug_message,        // 64 char debug string
    
    // Memory interface for external packet buffer
    output logic                    mem_clk,
    output logic [31:0]            mem_addr,
    output logic [511:0]           mem_wdata,
    output logic [63:0]            mem_wstrb,
    output logic                   mem_we,
    output logic                   mem_req,
    input  logic [511:0]           mem_rdata,
    input  logic                   mem_ack,
    input  logic                   mem_err
);

    // Enumeration types - will create EnumObject in cocotb
    typedef enum logic [2:0] {
        PKT_STATE_IDLE    = 3'b000,
        PKT_STATE_RECEIVE = 3'b001,
        PKT_STATE_PARSE   = 3'b010,
        PKT_STATE_ROUTE   = 3'b011,
        PKT_STATE_FORWARD = 3'b100,
        PKT_STATE_DROP    = 3'b101,
        PKT_STATE_ERROR   = 3'b110
    } packet_state_t;

    typedef enum logic [1:0] {
        PRIORITY_LOW    = 2'b00,
        PRIORITY_NORMAL = 2'b01,
        PRIORITY_HIGH   = 2'b10,
        PRIORITY_URGENT = 2'b11
    } priority_level_t;

    typedef enum logic [3:0] {
        PROTO_UNKNOWN = 4'h0,
        PROTO_IPV4    = 4'h1,
        PROTO_IPV6    = 4'h2,
        PROTO_ARP     = 4'h3,
        PROTO_ICMP    = 4'h4,
        PROTO_TCP     = 4'h5,
        PROTO_UDP     = 4'h6,
        PROTO_VLAN    = 4'h7,
        PROTO_MPLS    = 4'h8
    } protocol_type_t;

    typedef enum logic [2:0] {
        PORT_MODE_DISABLED = 3'b000,
        PORT_MODE_ACCESS   = 3'b001,
        PORT_MODE_TRUNK    = 3'b010,
        PORT_MODE_HYBRID   = 3'b011,
        PORT_MODE_MIRROR   = 3'b100,
        PORT_MODE_LOOPBACK = 3'b101
    } port_mode_t;

    // Internal state machines and control - EnumObject
    packet_state_t   current_packet_state;
    priority_level_t packet_priority;
    protocol_type_t  detected_protocol;
    port_mode_t      port_config [NUM_PORTS-1:0];  // ArrayObject of EnumObject
    
    // Additional internal registers for assignments
    logic [31:0] current_packet_state_reg;
    logic [1:0]  packet_priority_reg;
    logic [3:0]  detected_protocol_reg;

    // Internal integer counters and controls - IntegerObject  
    integer cycle_count;
    integer packet_id_counter;
    integer error_injection_counter;
    integer performance_cycle_count;
    integer debug_trace_level;

    // Internal real-valued monitoring - RealObject
    real internal_clock_freq;
    real measured_bandwidth;
    real packet_loss_rate;
    real jitter_measurement;
    real power_consumption;

    // String identifiers and debug info - StringObject
    string current_operation;
    string last_error_message;
    string port_names [NUM_PORTS-1:0];  // ArrayObject of StringObject

    // Complex internal signal arrays - ArrayObject and LogicArrayObject
    logic [63:0]  packet_headers [FIFO_DEPTH-1:0];      // ArrayObject of LogicArrayObject
    logic [31:0]  routing_table [ROUTING_TABLE_SIZE-1:0]; // ArrayObject of LogicArrayObject
    logic [15:0]  vlan_table [4096-1:0];                // ArrayObject of LogicArrayObject
    logic [7:0]   mac_address_table [1024-1:0][6-1:0];  // Multi-dimensional ArrayObject

    // Internal control and status registers
    logic [31:0]  control_register;
    logic [31:0]  status_register;
    logic [31:0]  interrupt_mask_register;
    logic [31:0]  interrupt_status_register;

    // Per-port statistics arrays - ArrayObject
    logic [STATS_COUNTER_WIDTH-1:0] port_rx_packets [NUM_PORTS-1:0];
    logic [STATS_COUNTER_WIDTH-1:0] port_tx_packets [NUM_PORTS-1:0];
    logic [STATS_COUNTER_WIDTH-1:0] port_rx_bytes [NUM_PORTS-1:0];
    logic [STATS_COUNTER_WIDTH-1:0] port_tx_bytes [NUM_PORTS-1:0];
    logic [STATS_COUNTER_WIDTH-1:0] port_dropped_packets [NUM_PORTS-1:0];
    logic [STATS_COUNTER_WIDTH-1:0] port_error_packets [NUM_PORTS-1:0];

    // FIFO and buffer management
    logic [9:0]   rx_fifo_wr_ptr [NUM_PORTS-1:0];  // ArrayObject
    logic [9:0]   rx_fifo_rd_ptr [NUM_PORTS-1:0];  // ArrayObject  
    logic [9:0]   tx_fifo_wr_ptr [NUM_PORTS-1:0];  // ArrayObject
    logic [9:0]   tx_fifo_rd_ptr [NUM_PORTS-1:0];  // ArrayObject
    logic         fifo_full [NUM_PORTS-1:0];       // ArrayObject
    logic         fifo_empty [NUM_PORTS-1:0];      // ArrayObject

    // Generate block for port controllers - HierarchyArrayObject
    genvar i;
    generate
        for (i = 0; i < NUM_PORTS; i++) begin : gen_port_controllers
            // Port Controller instances - HierarchyObject
            port_controller #(
                .PORT_ID(i),
                .FIFO_DEPTH(FIFO_DEPTH),
                .MAX_PACKET_SIZE(MAX_PACKET_SIZE)
            ) port_ctrl_inst (
                .clk(clk),
                .rst_n(rst_n),
                .enable(enable),
                
                // Port-specific signals
                .rx_valid(port_rx_valid[i]),
                .rx_data(port_rx_data[i*64 +: 64]),
                .rx_keep(port_rx_keep[i*8 +: 8]),
                .rx_last(port_rx_last[i]),
                .rx_ready(port_rx_ready[i]),
                
                .tx_valid(port_tx_valid[i]),
                .tx_data(port_tx_data[i*64 +: 64]),
                .tx_keep(port_tx_keep[i*8 +: 8]),
                .tx_last(port_tx_last[i]),
                .tx_ready(port_tx_ready[i]),
                
                // Configuration and status
                .port_mode(port_config[i]),
                .fifo_full(fifo_full[i]),
                .fifo_empty(fifo_empty[i]),
                
                // Statistics
                .rx_packet_count(port_rx_packets[i]),
                .tx_packet_count(port_tx_packets[i]),
                .rx_byte_count(port_rx_bytes[i]),
                .tx_byte_count(port_tx_bytes[i]),
                .dropped_packet_count(port_dropped_packets[i]),
                .error_packet_count(port_error_packets[i])
            );
        end
    endgenerate

    // Generate block for packet processing pipelines - HierarchyArrayObject
    generate
        for (i = 0; i < NUM_PRIORITY_LEVELS; i++) begin : gen_packet_pipelines
            // Packet Processing Pipeline instances - HierarchyObject  
            packet_processing_pipeline #(
                .PIPELINE_ID(i),
                .PRIORITY_LEVEL(i),
                .BUFFER_DEPTH(PACKET_BUFFER_DEPTH),
                .ROUTING_TABLE_SIZE(ROUTING_TABLE_SIZE)
            ) packet_pipeline_inst (
                .clk(clk),
                .rst_n(rst_n),
                .enable(enable),
                
                // Pipeline control
                .pipeline_ready(),
                .pipeline_busy(),
                .pipeline_error(),
                
                // Packet interface
                .packet_in_valid(),
                .packet_in_data(),
                .packet_in_ready(),
                .packet_out_valid(),
                .packet_out_data(),
                .packet_out_ready(),
                
                // Routing table access
                .routing_table_addr(),
                .routing_table_data(),
                .routing_table_valid(),
                
                // Statistics
                .processed_packets(),
                .processing_latency(),
                .pipeline_utilization()
            );
        end
    endgenerate

    // Generate block for memory controllers - HierarchyArrayObject
    generate
        for (i = 0; i < 4; i++) begin : gen_memory_controllers
            // Memory Controller instances - HierarchyObject
            memory_controller #(
                .CONTROLLER_ID(i),
                .MEMORY_DEPTH(PACKET_BUFFER_DEPTH/4),
                .DATA_WIDTH(512)
            ) mem_ctrl_inst (
                .clk(clk),
                .rst_n(rst_n),
                .enable(enable),
                
                // Memory interface
                .mem_addr(),
                .mem_wdata(),
                .mem_wstrb(),
                .mem_we(),
                .mem_req(),
                .mem_rdata(),
                .mem_ack(),
                .mem_err(),
                
                // Controller status
                .controller_ready(),
                .controller_busy(),
                .memory_full(),
                .memory_empty(),
                
                // Performance monitoring
                .bandwidth_utilization(),
                .access_latency(),
                .error_rate()
            );
        end
    endgenerate

    // Central Packet Classifier - HierarchyObject
    packet_classifier #(
        .NUM_CLASSIFICATION_RULES(256),
        .RULE_WIDTH(128)
    ) classifier_inst (
        .clk(clk),
        .rst_n(rst_n),
        .enable(enable),
        
        // Packet input
        .packet_valid(),
        .packet_data(),
        .packet_ready(),
        
        // Classification result
        .classification_valid(),
        .protocol_type(detected_protocol),
        .priority_level(packet_priority),
        .destination_port(),
        .classification_ready(),
        
        // Configuration
        .classification_rules(),
        .rule_update_enable(),
        
        // Statistics
        .classified_packets(),
        .classification_accuracy(),
        .classification_latency()
    );

    // Traffic Manager - HierarchyObject
    traffic_manager #(
        .NUM_QUEUES(16),
        .QUEUE_DEPTH(512),
        .NUM_SCHEDULERS(4)
    ) traffic_mgr_inst (
        .clk(clk),
        .rst_n(rst_n),
        .enable(enable),
        
        // Packet input from classifier
        .input_valid(),
        .input_data(),
        .input_priority(packet_priority),
        .input_ready(),
        
        // Packet output to ports
        .output_valid(),
        .output_data(),
        .output_port(),
        .output_ready(),
        
        // Queue status
        .queue_full(),
        .queue_empty(),
        .queue_occupancy(),
        
        // Scheduler configuration
        .scheduler_weights(),
        .scheduler_enable(),
        
        // Performance metrics
        .throughput_measurement(),
        .latency_measurement(),
        .queue_utilization()
    );

    // Statistics Aggregator - HierarchyObject
    statistics_aggregator #(
        .NUM_COUNTERS(64),
        .COUNTER_WIDTH(STATS_COUNTER_WIDTH)
    ) stats_aggregator_inst (
        .clk(clk),
        .rst_n(rst_n),
        .enable(enable),
        
        // Counter inputs from various modules
        .counter_increments(),
        .counter_values(),
        
        // Aggregated outputs
        .total_packets_rx(total_packets_rx),
        .total_packets_tx(total_packets_tx),
        .total_bytes_rx(total_bytes_rx),
        .total_bytes_tx(total_bytes_tx),
        .dropped_packets(dropped_packets),
        .error_packets(error_packets),
        
        // Real-time metrics
        .current_throughput(current_throughput_gbps),
        .average_latency(average_latency_ns),
        .utilization_percent(link_utilization_percent)
    );

    // Main packet processing state machine
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            current_packet_state <= PKT_STATE_IDLE;
            cycle_count <= 0;
            packet_id_counter <= 0;
            error_injection_counter <= 0;
            performance_cycle_count <= 0;
            debug_trace_level <= 0;
            
            // Initialize real values
            internal_clock_freq <= CLOCK_FREQUENCY;
            measured_bandwidth <= 0.0;
            packet_loss_rate <= 0.0;
            jitter_measurement <= 0.0;
            power_consumption <= 0.0;
            
            // Initialize string values - COMMENTED OUT FOR SIMULATOR COMPATIBILITY
            // current_operation <= "INITIALIZING";
            // last_error_message <= "NO_ERROR";
            
            // Initialize port names - COMMENTED OUT FOR SIMULATOR COMPATIBILITY
            // for (int j = 0; j < NUM_PORTS; j++) begin
            //     port_names[j] = $sformatf("PORT_%0d", j);
            // end
            
            // Initialize control registers
            control_register <= 32'h0;
            status_register <= 32'h0;
            interrupt_mask_register <= 32'h0;
            interrupt_status_register <= 32'h0;
            
        end else if (enable) begin
            cycle_count <= cycle_count + 1;
            performance_cycle_count <= performance_cycle_count + 1;
            
            // State machine progression
            case (current_packet_state)
                PKT_STATE_IDLE: begin
                    // current_operation <= "IDLE"; // COMMENTED OUT FOR SIMULATOR COMPATIBILITY
                    if (|port_rx_valid) begin
                        current_packet_state <= PKT_STATE_RECEIVE;
                        packet_id_counter <= packet_id_counter + 1;
                    end
                end
                
                PKT_STATE_RECEIVE: begin
                    // current_operation <= "RECEIVING"; // COMMENTED OUT FOR SIMULATOR COMPATIBILITY
                    current_packet_state <= PKT_STATE_PARSE;
                end
                
                PKT_STATE_PARSE: begin
                    // current_operation <= "PARSING"; // COMMENTED OUT FOR SIMULATOR COMPATIBILITY
                    // Protocol detection simulation
                    detected_protocol_reg <= PROTO_IPV4; // Use intermediate register
                    packet_priority_reg <= PRIORITY_NORMAL; // Use intermediate register
                    current_packet_state <= PKT_STATE_ROUTE;
                end
                
                PKT_STATE_ROUTE: begin
                    // current_operation <= "ROUTING"; // COMMENTED OUT FOR SIMULATOR COMPATIBILITY
                    current_packet_state <= PKT_STATE_FORWARD;
                end
                
                PKT_STATE_FORWARD: begin
                    // current_operation <= "FORWARDING"; // COMMENTED OUT FOR SIMULATOR COMPATIBILITY
                    current_packet_state <= PKT_STATE_IDLE;
                end
                
                PKT_STATE_DROP: begin
                    // current_operation <= "DROPPING"; // COMMENTED OUT FOR SIMULATOR COMPATIBILITY
                    // last_error_message <= "PACKET_DROPPED"; // COMMENTED OUT FOR SIMULATOR COMPATIBILITY
                    current_packet_state <= PKT_STATE_IDLE;
                end
                
                PKT_STATE_ERROR: begin
                    // current_operation <= "ERROR_HANDLING"; // COMMENTED OUT FOR SIMULATOR COMPATIBILITY
                    // last_error_message <= "PROCESSING_ERROR"; // COMMENTED OUT FOR SIMULATOR COMPATIBILITY
                    error_injection_counter <= error_injection_counter + 1;
                    current_packet_state <= PKT_STATE_IDLE;
                end
            endcase
            
            // Real-time measurements simulation
            measured_bandwidth <= BANDWIDTH_GBPS * ($sin($time / 1000000.0) * 0.2 + 0.8);
            packet_loss_rate <= $random % 1000 / 100000.0; // 0-0.01%
            jitter_measurement <= $random % 100 / 10.0; // 0-10ns
            power_consumption <= POWER_BUDGET_WATTS * ($cos($time / 500000.0) * 0.1 + 0.9);
            
            // Update status register
            status_register <= {
                18'h0,
                detected_protocol_reg,
                packet_priority_reg,
                current_packet_state[2:0],
                link_up,
                underflow,
                overflow,
                error,
                ready
            };
        end
    end

    // Configuration register interface
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            config_readdata <= 32'h0;
        end else begin
            case (config_addr)
                16'h0000: config_readdata <= control_register;
                16'h0004: config_readdata <= status_register;
                16'h0008: config_readdata <= interrupt_mask_register;
                16'h000C: config_readdata <= interrupt_status_register;
                16'h0010: config_readdata <= cycle_count;
                16'h0014: config_readdata <= packet_id_counter;
                16'h0018: config_readdata <= error_injection_counter;
                16'h001C: config_readdata <= debug_trace_level;
                default:  config_readdata <= 32'hDEADBEEF;
            endcase
            
            // Write operations
            if (|config_strobe) begin
                case (config_addr)
                    16'h0000: control_register <= config_data;
                    16'h0008: interrupt_mask_register <= config_data;
                    16'h001C: debug_trace_level <= config_data;
                endcase
            end
        end
    end

    // String output assignments - StringObject handling
    always_comb begin
        // Convert parameter strings to output logic vectors
        device_name_out = {DEVICE_NAME, {(32-$bits(DEVICE_NAME)/8){8'h00}}};
        version_string_out = {VERSION_STRING, {(16-$bits(VERSION_STRING)/8){8'h00}}};
        build_date_out = {BUILD_DATE, {(12-$bits(BUILD_DATE)/8){8'h00}}};
        vendor_id_out = {VENDOR_ID, {(16-$bits(VENDOR_ID)/8){8'h00}}};
        
        // Dynamic debug message based on current state
        case (current_packet_state)
            PKT_STATE_IDLE:    debug_message = {"IDLE_STATE", {56{8'h00}}};
            PKT_STATE_RECEIVE: debug_message = {"RECEIVING_PACKETS", {49{8'h00}}};
            PKT_STATE_PARSE:   debug_message = {"PARSING_HEADERS", {50{8'h00}}};
            PKT_STATE_ROUTE:   debug_message = {"ROUTING_DECISION", {49{8'h00}}};
            PKT_STATE_FORWARD: debug_message = {"FORWARDING_PACKET", {48{8'h00}}};
            PKT_STATE_DROP:    debug_message = {"DROPPING_PACKET", {49{8'h00}}};
            PKT_STATE_ERROR:   debug_message = {"ERROR_RECOVERY", {50{8'h00}}};
            default:           debug_message = {"UNKNOWN_STATE", {51{8'h00}}};
        endcase
    end
    // Protocol and priority signals are driven by classifier_inst outputs
    // No intermediate registers needed to avoid multiple drivers
    
    // Status output assignments
    assign ready = (current_packet_state == PKT_STATE_IDLE) && enable;
    assign error = (current_packet_state == PKT_STATE_ERROR);
    assign overflow = fifo_full[0];  // Single bit access
    assign underflow = fifo_empty[0]; // Single bit access
    assign link_up = enable && rst_n;

    // Power and thermal monitoring
    assign current_power_watts = power_consumption;
    assign junction_temperature = TEMPERATURE_THRESHOLD - 15.0 + ($random % 20);

    // Memory interface clock
    assign mem_clk = clk;

endmodule
