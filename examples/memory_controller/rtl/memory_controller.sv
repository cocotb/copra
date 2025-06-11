module memory_controller #(
    parameter CHANNELS = 4,
    parameter ADDR_WIDTH = 32,
    parameter DATA_WIDTH = 64,
    parameter BURST_LEN = 8,
    parameter MAX_OUTSTANDING = 16
) (
    input wire clk,
    input wire rst_n,
    
    // Control and Status
    input wire enable,
    output reg ready,
    output reg [1:0] error_status,
    
    // Configuration
    input [31:0] refresh_interval,
    input [31:0] bank_count,
    
    // Memory Interface Channels (generate loop - HierarchyArrayObject)
    input wire [CHANNELS-1:0] ch_req,
    input wire [CHANNELS*ADDR_WIDTH-1:0] ch_addr_packed,
    input wire [CHANNELS*DATA_WIDTH-1:0] ch_wdata_packed,
    input wire [CHANNELS-1:0] ch_wr_en,
    output reg [CHANNELS-1:0] ch_ack,
    output reg [CHANNELS*DATA_WIDTH-1:0] ch_rdata_packed,
    output reg [CHANNELS-1:0] ch_valid,
    
    // Memory Banks (for ArrayObject testing)
    output reg [7:0] bank_addr [0:3],
    output reg [3:0] bank_sel,
    output reg [DATA_WIDTH-1:0] bank_wdata [0:3],
    input wire [DATA_WIDTH-1:0] bank_rdata [0:3],
    
    // DDR Interface
    output reg ddr_ck_p,
    output reg ddr_ck_n,
    output reg [15:0] ddr_addr,
    output reg [31:0] ddr_dq,
    output reg [3:0] ddr_dm,
    output reg ddr_ras_n,
    output reg ddr_cas_n,
    output reg ddr_we_n
);

    // State machine enumeration (will create EnumObject)
    parameter [2:0] IDLE     = 3'b000;
    parameter [2:0] DECODE   = 3'b001;
    parameter [2:0] READ     = 3'b010;
    parameter [2:0] WRITE    = 3'b011;
    parameter [2:0] REFRESH  = 3'b100;
    parameter [2:0] ERROR    = 3'b101;
    
    reg [2:0] current_state, next_state;
    
    // Priority encoder state (another enum)
    parameter [1:0] ROUND_ROBIN = 2'b00;
    parameter [1:0] FIXED_PRIO  = 2'b01;
    parameter [1:0] WEIGHTED    = 2'b10;
    
    reg [1:0] arb_mode;
    
    // Internal signals
    reg [CHANNELS-1:0] internal_req_mask;
    reg [DATA_WIDTH-1:0] data_buffer [0:BURST_LEN-1];  // Unpacked array
    reg [ADDR_WIDTH-1:0] addr_queue [0:MAX_OUTSTANDING-1];  // Another unpacked array
    reg [3:0] queue_head, queue_tail;
    
    // Timing and performance counters (integers)
    integer cycle_counter;
    integer refresh_counter;
    integer error_counter;
    integer bandwidth_counter;
    
    // Real number calculations for timing
    real actual_frequency;
    real power_consumption;
    real temperature;
    real timing_parameter;
    
    // String objects for debugging and status (StringObject)
    reg [8*32-1:0] debug_status;   // 32 characters 
    reg [8*64-1:0] error_msg;      // 64 characters
    reg [8*16-1:0] version_info;   // 16 characters
    
    // Generate blocks for channel controllers (HierarchyArrayObject)
    genvar i;
    generate
        for (i = 0; i < CHANNELS; i = i + 1) begin : gen_channel_ctrl
            channel_controller #(
                .ADDR_WIDTH(ADDR_WIDTH),
                .DATA_WIDTH(DATA_WIDTH)
            ) ch_ctrl_inst (
                .clk(clk),
                .rst_n(rst_n),
                .req(ch_req[i]),
                .addr(ch_addr_packed[(i+1)*ADDR_WIDTH-1:i*ADDR_WIDTH]),
                .wdata(ch_wdata_packed[(i+1)*DATA_WIDTH-1:i*DATA_WIDTH]),
                .wr_en(ch_wr_en[i]),
                .ack(ch_ack[i]),
                .rdata(ch_rdata_packed[(i+1)*DATA_WIDTH-1:i*DATA_WIDTH]),
                .valid(ch_valid[i])
            );
        end
    endgenerate
    
    // Generate blocks for memory banks
    generate
        for (i = 0; i < 4; i = i + 1) begin : gen_memory_banks
            memory_bank #(
                .ADDR_WIDTH(8),
                .DATA_WIDTH(DATA_WIDTH)
            ) bank_inst (
                .clk(clk),
                .rst_n(rst_n),
                .addr(bank_addr[i]),
                .sel(bank_sel[i]),
                .wdata(bank_wdata[i]),
                .rdata(bank_rdata[i])
            );
        end
    endgenerate
    
    // Arbitration logic
    arbiter #(
        .CHANNELS(CHANNELS)
    ) arb_inst (
        .clk(clk),
        .rst_n(rst_n),
        .req(ch_req),
        .grant(internal_req_mask),
        .mode(arb_mode)
    );
    
    // State machine
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            current_state <= IDLE;
            cycle_counter <= 0;
            refresh_counter <= 0;
            error_counter <= 0;
            bandwidth_counter <= 0;
            queue_head <= 0;
            queue_tail <= 0;
            actual_frequency <= 100.0;
            power_consumption <= 1.5;
            temperature <= 25.0;
            timing_parameter <= 2.5;
            arb_mode <= ROUND_ROBIN;
            
            // Initialize string objects
            debug_status <= "INIT";
            error_msg <= "NO_ERROR";
            version_info <= "v2.0";
        end else begin
            current_state <= next_state;
            cycle_counter <= cycle_counter + 1;
            
            // Update real number calculations
            if (cycle_counter > 1000) begin
                actual_frequency <= 1000000.0 / cycle_counter * timing_parameter;
            end else begin
                actual_frequency <= 100.0;
            end
            power_consumption <= 1.5 + (temperature - 25.0) * 0.01;
            temperature <= 25.0 + bandwidth_counter * 0.001;
            
            // Update debug status based on state
            case (current_state)
                IDLE: debug_status <= "IDLE";
                DECODE: debug_status <= "DECODE";
                READ: debug_status <= "READ";
                WRITE: debug_status <= "WRITE";
                REFRESH: debug_status <= "REFRESH";
                ERROR: debug_status <= "ERROR";
                default: debug_status <= "UNKNOWN";
            endcase
            
            // Refresh logic
            if (refresh_counter >= refresh_interval) begin
                refresh_counter <= 0;
            end else begin
                refresh_counter <= refresh_counter + 1;
            end
        end
    end
    
    // State machine logic
    always @(*) begin
        next_state = current_state;
        ready = 1'b0;
        error_status = 2'b00;
        
        case (current_state)
            IDLE: begin
                ready = 1'b1;
                if (enable && |ch_req) begin
                    next_state = DECODE;
                end
            end
            
            DECODE: begin
                if (refresh_counter >= refresh_interval) begin
                    next_state = REFRESH;
                end else if (|internal_req_mask) begin
                    next_state = ch_wr_en[0] ? WRITE : READ;
                end
            end
            
            READ: begin
                next_state = IDLE;
            end
            
            WRITE: begin
                next_state = IDLE;
            end
            
            REFRESH: begin
                next_state = IDLE;
            end
            
            ERROR: begin
                error_status = 2'b11;
                next_state = IDLE;
            end
            
            default: begin
                next_state = ERROR;
            end
        endcase
    end

    // Update counters and error messages
    always @(posedge clk) begin
        if (current_state == READ || current_state == WRITE) begin
            bandwidth_counter <= bandwidth_counter + 1;
        end
        if (current_state == ERROR) begin
            error_counter <= error_counter + 1;
            error_msg <= "STATE_ERROR";
        end else if (error_counter == 0) begin
            error_msg <= "NO_ERROR";
        end else begin
            error_msg <= "PREV_ERROR";
        end
    end

endmodule