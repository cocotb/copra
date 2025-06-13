// Support Modules

// Register File
module register_file #(
    parameter DATA_WIDTH = 32
) (
    input wire clk,
    input wire rst_n,
    
    // Read ports
    input wire [4:0] rs1_addr,
    input wire [4:0] rs2_addr,
    output wire [DATA_WIDTH-1:0] rs1_data,
    output wire [DATA_WIDTH-1:0] rs2_data,
    
    // Write port
    input wire [4:0] rd_addr,
    input wire [DATA_WIDTH-1:0] rd_data,
    input wire we,
    
    // Debug interface
    input wire debug_req,
    output reg debug_ack,
    input wire [4:0] debug_addr,
    input wire [DATA_WIDTH-1:0] debug_wdata,
    output reg [DATA_WIDTH-1:0] debug_rdata,
    input wire debug_we
);

    reg [DATA_WIDTH-1:0] registers [0:31];
    integer i;
    
    // Initialize registers
    initial begin
        for (i = 0; i < 32; i = i + 1) begin
            registers[i] = 32'h0;
        end
    end
    
    // Read ports
    assign rs1_data = (rs1_addr == 5'b0) ? 32'h0 : registers[rs1_addr];
    assign rs2_data = (rs2_addr == 5'b0) ? 32'h0 : registers[rs2_addr];
    
    // Write port and debug interface combined
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            debug_ack <= 1'b0;
            debug_rdata <= 32'h0;
        end else begin
            debug_ack <= debug_req;
            
            // Normal write port
            if (we && rd_addr != 5'b0) begin
                registers[rd_addr] <= rd_data;
            end
            
            // Debug interface
            if (debug_req) begin
                if (debug_we) begin
                    if (debug_addr != 5'b0) begin
                        registers[debug_addr] <= debug_wdata;
                    end
                end else begin
                    debug_rdata <= (debug_addr == 5'b0) ? 32'h0 : registers[debug_addr];
                end
            end
        end
    end

endmodule

// Performance Counters
module performance_counters #(
    parameter CORE_ID = 0
) (
    input wire clk,
    input wire rst_n,
    input wire enable,
    
    // Events
    input wire instruction_retired,
    input wire icache_hit,
    input wire icache_miss,
    input wire dcache_hit,
    input wire dcache_miss,
    input wire branch_taken,
    input wire branch_mispred,
    
    // Counter outputs
    output reg [31:0] cycle_count,
    output reg [31:0] instr_count,
    output reg [31:0] cache_hits,
    output reg [31:0] cache_misses,
    output reg [31:0] branch_taken_count,
    output reg [31:0] branch_mispred_count
);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            cycle_count <= 32'h0;
            instr_count <= 32'h0;
            cache_hits <= 32'h0;
            cache_misses <= 32'h0;
            branch_taken_count <= 32'h0;
            branch_mispred_count <= 32'h0;
        end else if (enable) begin
            cycle_count <= cycle_count + 1;
            
            if (instruction_retired) begin
                instr_count <= instr_count + 1;
            end
            
            if (icache_hit || dcache_hit) begin
                cache_hits <= cache_hits + 1;
            end
            
            if (icache_miss || dcache_miss) begin
                cache_misses <= cache_misses + 1;
            end
            
            if (branch_taken) begin
                branch_taken_count <= branch_taken_count + 1;
            end
            
            if (branch_mispred) begin
                branch_mispred_count <= branch_mispred_count + 1;
            end
        end
    end

endmodule

// Instruction Fetch Arbiter with AXI Interface
module if_arbiter_axi #(
    parameter DATA_WIDTH = 32,
    parameter ADDR_WIDTH = 32,
    parameter NUM_CORES = 4
) (
    input wire clk,
    input wire rst_n,
    
    // Core interfaces
    input wire [NUM_CORES-1:0][ADDR_WIDTH-1:0] core_addr,
    output reg [NUM_CORES-1:0][DATA_WIDTH-1:0] core_rdata,
    input wire [NUM_CORES-1:0] core_req,
    output reg [NUM_CORES-1:0] core_ack,
    
    // AXI Master Interface
    output reg [3:0] m_axi_awid,
    output reg [ADDR_WIDTH-1:0] m_axi_awaddr,
    output reg [7:0] m_axi_awlen,
    output reg [2:0] m_axi_awsize,
    output reg [1:0] m_axi_awburst,
    output reg m_axi_awlock,
    output reg [3:0] m_axi_awcache,
    output reg [2:0] m_axi_awprot,
    output reg m_axi_awvalid,
    input wire m_axi_awready,
    output reg [DATA_WIDTH-1:0] m_axi_wdata,
    output reg [DATA_WIDTH/8-1:0] m_axi_wstrb,
    output reg m_axi_wlast,
    output reg m_axi_wvalid,
    input wire m_axi_wready,
    input wire [3:0] m_axi_bid,
    input wire [1:0] m_axi_bresp,
    input wire m_axi_bvalid,
    output reg m_axi_bready,
    output reg [3:0] m_axi_arid,
    output reg [ADDR_WIDTH-1:0] m_axi_araddr,
    output reg [7:0] m_axi_arlen,
    output reg [2:0] m_axi_arsize,
    output reg [1:0] m_axi_arburst,
    output reg m_axi_arlock,
    output reg [3:0] m_axi_arcache,
    output reg [2:0] m_axi_arprot,
    output reg m_axi_arvalid,
    input wire m_axi_arready,
    input wire [3:0] m_axi_rid,
    input wire [DATA_WIDTH-1:0] m_axi_rdata,
    input wire [1:0] m_axi_rresp,
    input wire m_axi_rlast,
    input wire m_axi_rvalid,
    output reg m_axi_rready
);

    // Simplified round-robin arbiter
    reg [1:0] current_core;
    reg [1:0] next_core;
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            current_core <= 2'b0;
            core_ack <= 4'b0;
            core_rdata <= {32'h0, 32'h0, 32'h0, 32'h0};
            
            // AXI signals
            m_axi_arid <= 4'b0;
            m_axi_araddr <= 32'h0;
            m_axi_arlen <= 8'h0;
            m_axi_arsize <= 3'b010; // 4 bytes
            m_axi_arburst <= 2'b01; // INCR
            m_axi_arlock <= 1'b0;
            m_axi_arcache <= 4'b0010;
            m_axi_arprot <= 3'b000;
            m_axi_arvalid <= 1'b0;
            m_axi_rready <= 1'b1;
            
            // Write channels (not used for instruction fetch)
            m_axi_awid <= 4'b0;
            m_axi_awaddr <= 32'h0;
            m_axi_awlen <= 8'h0;
            m_axi_awsize <= 3'b010;
            m_axi_awburst <= 2'b01;
            m_axi_awlock <= 1'b0;
            m_axi_awcache <= 4'b0010;
            m_axi_awprot <= 3'b000;
            m_axi_awvalid <= 1'b0;
            m_axi_wdata <= 32'h0;
            m_axi_wstrb <= 4'hF;
            m_axi_wlast <= 1'b1;
            m_axi_wvalid <= 1'b0;
            m_axi_bready <= 1'b1;
        end else begin
            // Simple round-robin arbitration
            if (core_req[current_core]) begin
                m_axi_arid <= {2'b0, current_core};
                m_axi_araddr <= core_addr[current_core];
                m_axi_arvalid <= 1'b1;
                
                if (m_axi_arready) begin
                    m_axi_arvalid <= 1'b0;
                end
                
                if (m_axi_rvalid && m_axi_rlast) begin
                    core_rdata[current_core] <= m_axi_rdata;
                    core_ack[current_core] <= 1'b1;
                    current_core <= next_core;
                end else begin
                    core_ack[current_core] <= 1'b0;
                end
            end else begin
                current_core <= next_core;
                core_ack <= 4'b0;
                m_axi_arvalid <= 1'b0;
            end
        end
    end
    
    // Next core selection
    always @(*) begin
        case (current_core)
            2'b00: next_core = 2'b01;
            2'b01: next_core = 2'b10;
            2'b10: next_core = 2'b11;
            2'b11: next_core = 2'b00;
        endcase
    end

endmodule

// Data Memory Arbiter with AXI Interface
module dm_arbiter_axi #(
    parameter DATA_WIDTH = 32,
    parameter ADDR_WIDTH = 32,
    parameter NUM_CORES = 4
) (
    input wire clk,
    input wire rst_n,
    
    // Core interfaces
    input wire [NUM_CORES-1:0][ADDR_WIDTH-1:0] core_addr,
    input wire [NUM_CORES-1:0][DATA_WIDTH-1:0] core_wdata,
    output reg [NUM_CORES-1:0][DATA_WIDTH-1:0] core_rdata,
    input wire [NUM_CORES-1:0] core_req,
    input wire [NUM_CORES-1:0] core_we,
    output reg [NUM_CORES-1:0] core_ack,
    
    // AXI Master Interface (same as IF arbiter but used for data)
    output reg [3:0] m_axi_awid,
    output reg [ADDR_WIDTH-1:0] m_axi_awaddr,
    output reg [7:0] m_axi_awlen,
    output reg [2:0] m_axi_awsize,
    output reg [1:0] m_axi_awburst,
    output reg m_axi_awlock,
    output reg [3:0] m_axi_awcache,
    output reg [2:0] m_axi_awprot,
    output reg m_axi_awvalid,
    input wire m_axi_awready,
    output reg [DATA_WIDTH-1:0] m_axi_wdata,
    output reg [DATA_WIDTH/8-1:0] m_axi_wstrb,
    output reg m_axi_wlast,
    output reg m_axi_wvalid,
    input wire m_axi_wready,
    input wire [3:0] m_axi_bid,
    input wire [1:0] m_axi_bresp,
    input wire m_axi_bvalid,
    output reg m_axi_bready,
    output reg [3:0] m_axi_arid,
    output reg [ADDR_WIDTH-1:0] m_axi_araddr,
    output reg [7:0] m_axi_arlen,
    output reg [2:0] m_axi_arsize,
    output reg [1:0] m_axi_arburst,
    output reg m_axi_arlock,
    output reg [3:0] m_axi_arcache,
    output reg [2:0] m_axi_arprot,
    output reg m_axi_arvalid,
    input wire m_axi_arready,
    input wire [3:0] m_axi_rid,
    input wire [DATA_WIDTH-1:0] m_axi_rdata,
    input wire [1:0] m_axi_rresp,
    input wire m_axi_rlast,
    input wire m_axi_rvalid,
    output reg m_axi_rready
);

    // Similar to IF arbiter but handles both read and write
    reg [1:0] current_core;
    reg [1:0] next_core;
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            current_core <= 2'b0;
            core_ack <= 4'b0;
            core_rdata <= {32'h0, 32'h0, 32'h0, 32'h0};
            
            // Initialize AXI signals
            m_axi_awid <= 4'b0;
            m_axi_awaddr <= 32'h0;
            m_axi_awlen <= 8'h0;
            m_axi_awsize <= 3'b010;
            m_axi_awburst <= 2'b01;
            m_axi_awlock <= 1'b0;
            m_axi_awcache <= 4'b0010;
            m_axi_awprot <= 3'b000;
            m_axi_awvalid <= 1'b0;
            m_axi_wdata <= 32'h0;
            m_axi_wstrb <= 4'hF;
            m_axi_wlast <= 1'b1;
            m_axi_wvalid <= 1'b0;
            m_axi_bready <= 1'b1;
            m_axi_arid <= 4'b0;
            m_axi_araddr <= 32'h0;
            m_axi_arlen <= 8'h0;
            m_axi_arsize <= 3'b010;
            m_axi_arburst <= 2'b01;
            m_axi_arlock <= 1'b0;
            m_axi_arcache <= 4'b0010;
            m_axi_arprot <= 3'b000;
            m_axi_arvalid <= 1'b0;
            m_axi_rready <= 1'b1;
        end else begin
            // Simplified data memory arbitration
            if (core_req[current_core]) begin
                if (core_we[current_core]) begin
                    // Write operation
                    m_axi_awid <= {2'b0, current_core};
                    m_axi_awaddr <= core_addr[current_core];
                    m_axi_awvalid <= 1'b1;
                    m_axi_wdata <= core_wdata[current_core];
                    m_axi_wvalid <= 1'b1;
                    
                    if (m_axi_bvalid) begin
                        core_ack[current_core] <= 1'b1;
                        current_core <= next_core;
                        m_axi_awvalid <= 1'b0;
                        m_axi_wvalid <= 1'b0;
                    end
                end else begin
                    // Read operation
                    m_axi_arid <= {2'b0, current_core};
                    m_axi_araddr <= core_addr[current_core];
                    m_axi_arvalid <= 1'b1;
                    
                    if (m_axi_rvalid && m_axi_rlast) begin
                        core_rdata[current_core] <= m_axi_rdata;
                        core_ack[current_core] <= 1'b1;
                        current_core <= next_core;
                        m_axi_arvalid <= 1'b0;
                    end
                end
            end else begin
                current_core <= next_core;
                core_ack <= 4'b0;
                m_axi_arvalid <= 1'b0;
                m_axi_awvalid <= 1'b0;
                m_axi_wvalid <= 1'b0;
            end
        end
    end
    
    // Next core selection
    always @(*) begin
        case (current_core)
            2'b00: next_core = 2'b01;
            2'b01: next_core = 2'b10;
            2'b10: next_core = 2'b11;
            2'b11: next_core = 2'b00;
        endcase
    end

endmodule

// Control and Status Register Block
module csr_block #(
    parameter DATA_WIDTH = 32,
    parameter ADDR_WIDTH = 32,
    parameter NUM_CORES = 4
) (
    input wire clk,
    input wire rst_n,
    
    // APB Interface
    input wire [ADDR_WIDTH-1:0] paddr,
    input wire psel,
    input wire penable,
    input wire pwrite,
    input wire [DATA_WIDTH-1:0] pwdata,
    input wire [DATA_WIDTH/8-1:0] pstrb,
    output reg [DATA_WIDTH-1:0] prdata,
    output reg pready,
    output reg pslverr,
    
    // Status inputs
    input wire [NUM_CORES-1:0] core_active,
    input wire [NUM_CORES-1:0] core_halted,
    input wire [NUM_CORES-1:0] core_error,
    input wire [31:0] perf_cycle_count,
    input wire [31:0] perf_instr_count,
    input wire [31:0] perf_cache_hits,
    input wire [31:0] perf_cache_misses,
    input wire [31:0] perf_branch_taken,
    input wire [31:0] perf_branch_mispred
);

    // CSR Address Map
    localparam CSR_CORE_STATUS    = 32'h0000;
    localparam CSR_PERF_CYCLES    = 32'h0010;
    localparam CSR_PERF_INSTRS    = 32'h0014;
    localparam CSR_PERF_CACHE_HITS = 32'h0018;
    localparam CSR_PERF_CACHE_MISS = 32'h001C;
    localparam CSR_PERF_BRANCH_TKN = 32'h0020;
    localparam CSR_PERF_BRANCH_MIS = 32'h0024;
    
    // Internal registers
    reg [DATA_WIDTH-1:0] control_reg;
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            prdata <= 32'h0;
            pready <= 1'b0;
            pslverr <= 1'b0;
            control_reg <= 32'h0;
        end else begin
            pready <= psel;
            pslverr <= 1'b0;
            
            if (psel && penable) begin
                if (pwrite) begin
                    // Write operation
                    case (paddr)
                        CSR_CORE_STATUS: control_reg <= pwdata;
                        default: pslverr <= 1'b1;
                    endcase
                end else begin
                    // Read operation
                    case (paddr)
                        CSR_CORE_STATUS: prdata <= {20'h0, core_error, core_halted, core_active};
                        CSR_PERF_CYCLES: prdata <= perf_cycle_count;
                        CSR_PERF_INSTRS: prdata <= perf_instr_count;
                        CSR_PERF_CACHE_HITS: prdata <= perf_cache_hits;
                        CSR_PERF_CACHE_MISS: prdata <= perf_cache_misses;
                        CSR_PERF_BRANCH_TKN: prdata <= perf_branch_taken;
                        CSR_PERF_BRANCH_MIS: prdata <= perf_branch_mispred;
                        default: begin
                            prdata <= 32'h0;
                            pslverr <= 1'b1;
                        end
                    endcase
                end
            end
        end
    end

endmodule 
