// CPU Core Module
module cpu_core #(
    parameter DATA_WIDTH = 32,
    parameter ADDR_WIDTH = 32,
    parameter CACHE_SIZE = 1024,
    parameter CORE_ID = 0
) (
    input wire clk,
    input wire rst_n,
    input wire enable,
    output wire active,
    output wire halted,
    output wire error,
    
    // Instruction Fetch Interface
    output wire [ADDR_WIDTH-1:0] if_addr,
    input wire [DATA_WIDTH-1:0] if_rdata,
    output wire if_req,
    input wire if_ack,
    
    // Data Memory Interface
    output wire [ADDR_WIDTH-1:0] dm_addr,
    output wire [DATA_WIDTH-1:0] dm_wdata,
    input wire [DATA_WIDTH-1:0] dm_rdata,
    output wire dm_req,
    output wire dm_we,
    input wire dm_ack,
    
    // Interrupt Interface
    input wire [15:0] interrupts,
    output wire interrupt_ack,
    output wire [3:0] interrupt_id,
    
    // Debug Interface
    input wire debug_req,
    output wire debug_ack,
    input wire [ADDR_WIDTH-1:0] debug_addr,
    input wire [DATA_WIDTH-1:0] debug_wdata,
    output wire [DATA_WIDTH-1:0] debug_rdata,
    input wire debug_we,
    
    // Performance Counters
    output wire [31:0] perf_cycle_count,
    output wire [31:0] perf_instr_count,
    output wire [31:0] perf_cache_hits,
    output wire [31:0] perf_cache_misses,
    output wire [31:0] perf_branch_taken,
    output wire [31:0] perf_branch_mispred
);

    // Pipeline stage signals
    wire [DATA_WIDTH-1:0] if_instruction;
    wire [ADDR_WIDTH-1:0] if_pc;
    wire if_valid;
    
    wire [DATA_WIDTH-1:0] id_instruction;
    wire [ADDR_WIDTH-1:0] id_pc;
    wire id_valid;
    
    wire [DATA_WIDTH-1:0] ex_result;
    wire [ADDR_WIDTH-1:0] ex_pc;
    wire ex_valid;
    
    wire [DATA_WIDTH-1:0] mem_result;
    wire [ADDR_WIDTH-1:0] mem_pc;
    wire mem_valid;
    
    wire [DATA_WIDTH-1:0] wb_result;
    wire [ADDR_WIDTH-1:0] wb_pc;
    wire wb_valid;
    
    // Register file signals
    wire [4:0] rf_rs1_addr, rf_rs2_addr, rf_rd_addr;
    wire [DATA_WIDTH-1:0] rf_rs1_data, rf_rs2_data, rf_rd_data;
    wire rf_we;
    
    // Cache signals
    wire icache_hit, dcache_hit;
    wire icache_miss, dcache_miss;
    
    // Control signals
    wire pipeline_stall;
    wire pipeline_flush;
    wire branch_taken;
    wire branch_mispred;

    // Instruction Fetch Stage
    if_stage #(
        .DATA_WIDTH(DATA_WIDTH),
        .ADDR_WIDTH(ADDR_WIDTH),
        .CACHE_SIZE(CACHE_SIZE/2)
    ) u_if_stage (
        .clk(clk),
        .rst_n(rst_n),
        .enable(enable),
        .stall(pipeline_stall),
        .flush(pipeline_flush),
        .branch_target(ex_result[ADDR_WIDTH-1:0]),
        .branch_taken(branch_taken),
        
        // Memory interface
        .mem_addr(if_addr),
        .mem_rdata(if_rdata),
        .mem_req(if_req),
        .mem_ack(if_ack),
        
        // Output to ID stage
        .instruction(if_instruction),
        .pc(if_pc),
        .valid(if_valid),
        
        // Cache performance
        .cache_hit(icache_hit),
        .cache_miss(icache_miss)
    );
    
    // Instruction Decode Stage
    id_stage #(
        .DATA_WIDTH(DATA_WIDTH),
        .ADDR_WIDTH(ADDR_WIDTH)
    ) u_id_stage (
        .clk(clk),
        .rst_n(rst_n),
        .stall(pipeline_stall),
        .flush(pipeline_flush),
        
        // Input from IF stage
        .if_instruction(if_instruction),
        .if_pc(if_pc),
        .if_valid(if_valid),
        
        // Register file interface
        .rf_rs1_addr(rf_rs1_addr),
        .rf_rs2_addr(rf_rs2_addr),
        .rf_rs1_data(rf_rs1_data),
        .rf_rs2_data(rf_rs2_data),
        
        // Output to EX stage
        .id_instruction(id_instruction),
        .id_pc(id_pc),
        .valid(id_valid),
        
        // Interrupt handling
        .interrupts(interrupts),
        .interrupt_ack(interrupt_ack),
        .interrupt_id(interrupt_id)
    );
    
    // Execute Stage
    ex_stage #(
        .DATA_WIDTH(DATA_WIDTH),
        .ADDR_WIDTH(ADDR_WIDTH)
    ) u_ex_stage (
        .clk(clk),
        .rst_n(rst_n),
        .stall(pipeline_stall),
        .flush(pipeline_flush),
        
        // Input from ID stage
        .id_instruction(id_instruction),
        .id_pc(id_pc),
        .id_valid(id_valid),
        
        // Output to MEM stage
        .ex_result(ex_result),
        .ex_pc(ex_pc),
        .valid(ex_valid),
        
        // Branch control
        .branch_taken(branch_taken),
        .branch_mispred(branch_mispred)
    );
    
    // Memory Stage
    mem_stage #(
        .DATA_WIDTH(DATA_WIDTH),
        .ADDR_WIDTH(ADDR_WIDTH),
        .CACHE_SIZE(CACHE_SIZE/2)
    ) u_mem_stage (
        .clk(clk),
        .rst_n(rst_n),
        .stall(pipeline_stall),
        .flush(pipeline_flush),
        
        // Input from EX stage
        .ex_result(ex_result),
        .ex_pc(ex_pc),
        .ex_valid(ex_valid),
        
        // Memory interface
        .mem_addr(dm_addr),
        .mem_wdata(dm_wdata),
        .mem_rdata(dm_rdata),
        .mem_req(dm_req),
        .mem_we(dm_we),
        .mem_ack(dm_ack),
        
        // Output to WB stage
        .mem_result(mem_result),
        .mem_pc(mem_pc),
        .valid(mem_valid),
        
        // Cache performance
        .cache_hit(dcache_hit),
        .cache_miss(dcache_miss)
    );
    
    // Writeback Stage
    wb_stage #(
        .DATA_WIDTH(DATA_WIDTH),
        .ADDR_WIDTH(ADDR_WIDTH)
    ) u_wb_stage (
        .clk(clk),
        .rst_n(rst_n),
        .stall(pipeline_stall),
        .flush(pipeline_flush),
        
        // Input from MEM stage
        .mem_result(mem_result),
        .mem_pc(mem_pc),
        .mem_valid(mem_valid),
        
        // Register file write interface
        .rf_rd_addr(rf_rd_addr),
        .rf_rd_data(rf_rd_data),
        .rf_we(rf_we),
        
        // Output
        .wb_result(wb_result),
        .wb_pc(wb_pc),
        .valid(wb_valid)
    );
    
    // Register File
    register_file #(
        .DATA_WIDTH(DATA_WIDTH)
    ) u_register_file (
        .clk(clk),
        .rst_n(rst_n),
        
        // Read ports
        .rs1_addr(rf_rs1_addr),
        .rs2_addr(rf_rs2_addr),
        .rs1_data(rf_rs1_data),
        .rs2_data(rf_rs2_data),
        
        // Write port
        .rd_addr(rf_rd_addr),
        .rd_data(rf_rd_data),
        .we(rf_we),
        
        // Debug interface
        .debug_req(debug_req),
        .debug_ack(debug_ack),
        .debug_addr(debug_addr[4:0]),
        .debug_wdata(debug_wdata),
        .debug_rdata(debug_rdata),
        .debug_we(debug_we)
    );
    
    // Performance Counters
    performance_counters #(
        .CORE_ID(CORE_ID)
    ) u_perf_counters (
        .clk(clk),
        .rst_n(rst_n),
        .enable(enable),
        
        // Events
        .instruction_retired(wb_valid),
        .icache_hit(icache_hit),
        .icache_miss(icache_miss),
        .dcache_hit(dcache_hit),
        .dcache_miss(dcache_miss),
        .branch_taken(branch_taken),
        .branch_mispred(branch_mispred),
        
        // Counter outputs
        .cycle_count(perf_cycle_count),
        .instr_count(perf_instr_count),
        .cache_hits(perf_cache_hits),
        .cache_misses(perf_cache_misses),
        .branch_taken_count(perf_branch_taken),
        .branch_mispred_count(perf_branch_mispred)
    );
    
    // Core status
    assign active = enable & ~halted;
    assign halted = 1'b0; // Simplified - no halt condition
    assign error = 1'b0;  // Simplified - no error condition
    
    // Pipeline control
    assign pipeline_stall = ~if_ack | ~dm_ack;
    assign pipeline_flush = branch_mispred;

endmodule 