// Complex CPU Top-Level Module
// This is an extensive example to test copra's capabilities
module cpu #(
    parameter DATA_WIDTH = 32,
    parameter ADDR_WIDTH = 32,
    parameter CACHE_SIZE = 1024,
    parameter NUM_CORES = 4,
    parameter NUM_INTERRUPTS = 16
) (
    // Clock and Reset
    input wire clk,
    input wire rst_n,
    input wire test_mode,
    
    // AXI4 Master Interface (Instruction Fetch)
    output wire [3:0]           m_axi_if_awid,
    output wire [ADDR_WIDTH-1:0] m_axi_if_awaddr,
    output wire [7:0]           m_axi_if_awlen,
    output wire [2:0]           m_axi_if_awsize,
    output wire [1:0]           m_axi_if_awburst,
    output wire                 m_axi_if_awlock,
    output wire [3:0]           m_axi_if_awcache,
    output wire [2:0]           m_axi_if_awprot,
    output wire                 m_axi_if_awvalid,
    input wire                  m_axi_if_awready,
    output wire [DATA_WIDTH-1:0] m_axi_if_wdata,
    output wire [DATA_WIDTH/8-1:0] m_axi_if_wstrb,
    output wire                 m_axi_if_wlast,
    output wire                 m_axi_if_wvalid,
    input wire                  m_axi_if_wready,
    input wire [3:0]            m_axi_if_bid,
    input wire [1:0]            m_axi_if_bresp,
    input wire                  m_axi_if_bvalid,
    output wire                 m_axi_if_bready,
    output wire [3:0]           m_axi_if_arid,
    output wire [ADDR_WIDTH-1:0] m_axi_if_araddr,
    output wire [7:0]           m_axi_if_arlen,
    output wire [2:0]           m_axi_if_arsize,
    output wire [1:0]           m_axi_if_arburst,
    output wire                 m_axi_if_arlock,
    output wire [3:0]           m_axi_if_arcache,
    output wire [2:0]           m_axi_if_arprot,
    output wire                 m_axi_if_arvalid,
    input wire                  m_axi_if_arready,
    input wire [3:0]            m_axi_if_rid,
    input wire [DATA_WIDTH-1:0] m_axi_if_rdata,
    input wire [1:0]            m_axi_if_rresp,
    input wire                  m_axi_if_rlast,
    input wire                  m_axi_if_rvalid,
    output wire                 m_axi_if_rready,
    
    // AXI4 Master Interface (Data Memory)
    output wire [3:0]           m_axi_dm_awid,
    output wire [ADDR_WIDTH-1:0] m_axi_dm_awaddr,
    output wire [7:0]           m_axi_dm_awlen,
    output wire [2:0]           m_axi_dm_awsize,
    output wire [1:0]           m_axi_dm_awburst,
    output wire                 m_axi_dm_awlock,
    output wire [3:0]           m_axi_dm_awcache,
    output wire [2:0]           m_axi_dm_awprot,
    output wire                 m_axi_dm_awvalid,
    input wire                  m_axi_dm_awready,
    output wire [DATA_WIDTH-1:0] m_axi_dm_wdata,
    output wire [DATA_WIDTH/8-1:0] m_axi_dm_wstrb,
    output wire                 m_axi_dm_wlast,
    output wire                 m_axi_dm_wvalid,
    input wire                  m_axi_dm_wready,
    input wire [3:0]            m_axi_dm_bid,
    input wire [1:0]            m_axi_dm_bresp,
    input wire                  m_axi_dm_bvalid,
    output wire                 m_axi_dm_bready,
    output wire [3:0]           m_axi_dm_arid,
    output wire [ADDR_WIDTH-1:0] m_axi_dm_araddr,
    output wire [7:0]           m_axi_dm_arlen,
    output wire [2:0]           m_axi_dm_arsize,
    output wire [1:0]           m_axi_dm_arburst,
    output wire                 m_axi_dm_arlock,
    output wire [3:0]           m_axi_dm_arcache,
    output wire [2:0]           m_axi_dm_arprot,
    output wire                 m_axi_dm_arvalid,
    input wire                  m_axi_dm_arready,
    input wire [3:0]            m_axi_dm_rid,
    input wire [DATA_WIDTH-1:0] m_axi_dm_rdata,
    input wire [1:0]            m_axi_dm_rresp,
    input wire                  m_axi_dm_rlast,
    input wire                  m_axi_dm_rvalid,
    output wire                 m_axi_dm_rready,
    
    // APB Slave Interface (Control/Status Registers)
    input wire                  s_apb_pclk,
    input wire                  s_apb_presetn,
    input wire [ADDR_WIDTH-1:0] s_apb_paddr,
    input wire                  s_apb_psel,
    input wire                  s_apb_penable,
    input wire                  s_apb_pwrite,
    input wire [DATA_WIDTH-1:0] s_apb_pwdata,
    input wire [DATA_WIDTH/8-1:0] s_apb_pstrb,
    output wire [DATA_WIDTH-1:0] s_apb_prdata,
    output wire                 s_apb_pready,
    output wire                 s_apb_pslverr,
    
    // Interrupt Interface
    input wire [NUM_INTERRUPTS-1:0] interrupts,
    output wire                 interrupt_ack,
    output wire [3:0]           interrupt_id,
    
    // Debug Interface
    input wire                  debug_req,
    output wire                 debug_ack,
    input wire [ADDR_WIDTH-1:0] debug_addr,
    input wire [DATA_WIDTH-1:0] debug_wdata,
    output wire [DATA_WIDTH-1:0] debug_rdata,
    input wire                  debug_we,
    
    // Performance Monitoring
    output wire [31:0]          perf_cycle_count,
    output wire [31:0]          perf_instr_count,
    output wire [31:0]          perf_cache_hits,
    output wire [31:0]          perf_cache_misses,
    output wire [31:0]          perf_branch_taken,
    output wire [31:0]          perf_branch_mispred,
    
    // Status and Control
    output wire [NUM_CORES-1:0] core_active,
    output wire [NUM_CORES-1:0] core_halted,
    output wire [NUM_CORES-1:0] core_error,
    input wire [NUM_CORES-1:0]  core_enable,
    input wire                  global_enable,
    output wire                 system_ready
);

    // Internal signals
    wire [NUM_CORES-1:0] core_clk;
    wire [NUM_CORES-1:0] core_rst_n;
    
    // Internal signals for each core
    wire [NUM_CORES-1:0][ADDR_WIDTH-1:0] core_if_addr;
    wire [NUM_CORES-1:0][DATA_WIDTH-1:0] core_if_rdata;
    wire [NUM_CORES-1:0] core_if_req;
    wire [NUM_CORES-1:0] core_if_ack;
    
    wire [NUM_CORES-1:0][ADDR_WIDTH-1:0] core_dm_addr;
    wire [NUM_CORES-1:0][DATA_WIDTH-1:0] core_dm_wdata;
    wire [NUM_CORES-1:0][DATA_WIDTH-1:0] core_dm_rdata;
    wire [NUM_CORES-1:0] core_dm_req;
    wire [NUM_CORES-1:0] core_dm_we;
    wire [NUM_CORES-1:0] core_dm_ack;
    
    // Performance counters for each core
    wire [NUM_CORES-1:0][31:0] core_cycle_count;
    wire [NUM_CORES-1:0][31:0] core_instr_count;
    wire [NUM_CORES-1:0][31:0] core_cache_hits;
    wire [NUM_CORES-1:0][31:0] core_cache_misses;
    wire [NUM_CORES-1:0][31:0] core_branch_taken;
    wire [NUM_CORES-1:0][31:0] core_branch_mispred;
    
    // Clock and Reset Generation
    clock_gen #(
        .NUM_CORES(NUM_CORES)
    ) u_clock_gen (
        .clk_in(clk),
        .rst_n_in(rst_n),
        .test_mode(test_mode),
        .core_enable(core_enable),
        .global_enable(global_enable),
        .core_clk(core_clk),
        .core_rst_n(core_rst_n),
        .system_ready(system_ready)
    );
    
    // Generate CPU cores
    genvar i;
    generate
        for (i = 0; i < NUM_CORES; i = i + 1) begin : gen_cpu_cores
            core #(
                .DATA_WIDTH(DATA_WIDTH),
                .ADDR_WIDTH(ADDR_WIDTH),
                .CACHE_SIZE(CACHE_SIZE),
                .CORE_ID(i)
            ) u_core (
                .clk(core_clk[i]),
                .rst_n(core_rst_n[i]),
                .enable(core_enable[i]),
                .active(core_active[i]),
                .halted(core_halted[i]),
                .error(core_error[i]),
                
                // Instruction Fetch Interface
                .if_addr(core_if_addr[i]),
                .if_rdata(core_if_rdata[i]),
                .if_req(core_if_req[i]),
                .if_ack(core_if_ack[i]),
                
                // Data Memory Interface
                .dm_addr(core_dm_addr[i]),
                .dm_wdata(core_dm_wdata[i]),
                .dm_rdata(core_dm_rdata[i]),
                .dm_req(core_dm_req[i]),
                .dm_we(core_dm_we[i]),
                .dm_ack(core_dm_ack[i]),
                
                // Interrupt Interface
                .interrupts(interrupts),
                .interrupt_ack(interrupt_ack),
                .interrupt_id(interrupt_id),
                
                // Debug Interface
                .debug_req(debug_req),
                .debug_ack(debug_ack),
                .debug_addr(debug_addr),
                .debug_wdata(debug_wdata),
                .debug_rdata(debug_rdata),
                .debug_we(debug_we),
                
                // Performance Counters
                .perf_cycle_count(core_cycle_count[i]),
                .perf_instr_count(core_instr_count[i]),
                .perf_cache_hits(core_cache_hits[i]),
                .perf_cache_misses(core_cache_misses[i]),
                .perf_branch_taken(core_branch_taken[i]),
                .perf_branch_mispred(core_branch_mispred[i])
            );
        end
    endgenerate
    
    // Instruction Fetch Arbiter and AXI Bridge
    if_arbiter_axi #(
        .DATA_WIDTH(DATA_WIDTH),
        .ADDR_WIDTH(ADDR_WIDTH),
        .NUM_CORES(NUM_CORES)
    ) u_if_arbiter (
        .clk(core_clk[0]), // Use core 0 clock for arbiter
        .rst_n(core_rst_n[0]),
        
        // Core interfaces
        .core_addr(core_if_addr),
        .core_rdata(core_if_rdata),
        .core_req(core_if_req),
        .core_ack(core_if_ack),
        
        // AXI Master Interface
        .m_axi_awid(m_axi_if_awid),
        .m_axi_awaddr(m_axi_if_awaddr),
        .m_axi_awlen(m_axi_if_awlen),
        .m_axi_awsize(m_axi_if_awsize),
        .m_axi_awburst(m_axi_if_awburst),
        .m_axi_awlock(m_axi_if_awlock),
        .m_axi_awcache(m_axi_if_awcache),
        .m_axi_awprot(m_axi_if_awprot),
        .m_axi_awvalid(m_axi_if_awvalid),
        .m_axi_awready(m_axi_if_awready),
        .m_axi_wdata(m_axi_if_wdata),
        .m_axi_wstrb(m_axi_if_wstrb),
        .m_axi_wlast(m_axi_if_wlast),
        .m_axi_wvalid(m_axi_if_wvalid),
        .m_axi_wready(m_axi_if_wready),
        .m_axi_bid(m_axi_if_bid),
        .m_axi_bresp(m_axi_if_bresp),
        .m_axi_bvalid(m_axi_if_bvalid),
        .m_axi_bready(m_axi_if_bready),
        .m_axi_arid(m_axi_if_arid),
        .m_axi_araddr(m_axi_if_araddr),
        .m_axi_arlen(m_axi_if_arlen),
        .m_axi_arsize(m_axi_if_arsize),
        .m_axi_arburst(m_axi_if_arburst),
        .m_axi_arlock(m_axi_if_arlock),
        .m_axi_arcache(m_axi_if_arcache),
        .m_axi_arprot(m_axi_if_arprot),
        .m_axi_arvalid(m_axi_if_arvalid),
        .m_axi_arready(m_axi_if_arready),
        .m_axi_rid(m_axi_if_rid),
        .m_axi_rdata(m_axi_if_rdata),
        .m_axi_rresp(m_axi_if_rresp),
        .m_axi_rlast(m_axi_if_rlast),
        .m_axi_rvalid(m_axi_if_rvalid),
        .m_axi_rready(m_axi_if_rready)
    );
    
    // Data Memory Arbiter and AXI Bridge
    dm_arbiter_axi #(
        .DATA_WIDTH(DATA_WIDTH),
        .ADDR_WIDTH(ADDR_WIDTH),
        .NUM_CORES(NUM_CORES)
    ) u_dm_arbiter (
        .clk(core_clk[0]), // Use core 0 clock for arbiter
        .rst_n(core_rst_n[0]),
        
        // Core interfaces
        .core_addr(core_dm_addr),
        .core_wdata(core_dm_wdata),
        .core_rdata(core_dm_rdata),
        .core_req(core_dm_req),
        .core_we(core_dm_we),
        .core_ack(core_dm_ack),
        
        // AXI Master Interface
        .m_axi_awid(m_axi_dm_awid),
        .m_axi_awaddr(m_axi_dm_awaddr),
        .m_axi_awlen(m_axi_dm_awlen),
        .m_axi_awsize(m_axi_dm_awsize),
        .m_axi_awburst(m_axi_dm_awburst),
        .m_axi_awlock(m_axi_dm_awlock),
        .m_axi_awcache(m_axi_dm_awcache),
        .m_axi_awprot(m_axi_dm_awprot),
        .m_axi_awvalid(m_axi_dm_awvalid),
        .m_axi_awready(m_axi_dm_awready),
        .m_axi_wdata(m_axi_dm_wdata),
        .m_axi_wstrb(m_axi_dm_wstrb),
        .m_axi_wlast(m_axi_dm_wlast),
        .m_axi_wvalid(m_axi_dm_wvalid),
        .m_axi_wready(m_axi_dm_wready),
        .m_axi_bid(m_axi_dm_bid),
        .m_axi_bresp(m_axi_dm_bresp),
        .m_axi_bvalid(m_axi_dm_bvalid),
        .m_axi_bready(m_axi_dm_bready),
        .m_axi_arid(m_axi_dm_arid),
        .m_axi_araddr(m_axi_dm_araddr),
        .m_axi_arlen(m_axi_dm_arlen),
        .m_axi_arsize(m_axi_dm_arsize),
        .m_axi_arburst(m_axi_dm_arburst),
        .m_axi_arlock(m_axi_dm_arlock),
        .m_axi_arcache(m_axi_dm_arcache),
        .m_axi_arprot(m_axi_dm_arprot),
        .m_axi_arvalid(m_axi_dm_arvalid),
        .m_axi_arready(m_axi_dm_arready),
        .m_axi_rid(m_axi_dm_rid),
        .m_axi_rdata(m_axi_dm_rdata),
        .m_axi_rresp(m_axi_dm_rresp),
        .m_axi_rlast(m_axi_dm_rlast),
        .m_axi_rvalid(m_axi_dm_rvalid),
        .m_axi_rready(m_axi_dm_rready)
    );
    
    // Control and Status Register Block
    csr_block #(
        .DATA_WIDTH(DATA_WIDTH),
        .ADDR_WIDTH(ADDR_WIDTH),
        .NUM_CORES(NUM_CORES)
    ) u_csr_block (
        .clk(s_apb_pclk),
        .rst_n(s_apb_presetn),
        
        // APB Interface
        .paddr(s_apb_paddr),
        .psel(s_apb_psel),
        .penable(s_apb_penable),
        .pwrite(s_apb_pwrite),
        .pwdata(s_apb_pwdata),
        .pstrb(s_apb_pstrb),
        .prdata(s_apb_prdata),
        .pready(s_apb_pready),
        .pslverr(s_apb_pslverr),
        
        // Status inputs
        .core_active(core_active),
        .core_halted(core_halted),
        .core_error(core_error),
        .perf_cycle_count(perf_cycle_count),
        .perf_instr_count(perf_instr_count),
        .perf_cache_hits(perf_cache_hits),
        .perf_cache_misses(perf_cache_misses),
        .perf_branch_taken(perf_branch_taken),
        .perf_branch_mispred(perf_branch_mispred)
    );
    
    // Aggregate performance counters
    assign perf_cycle_count = core_cycle_count[0] + core_cycle_count[1] + 
                             core_cycle_count[2] + core_cycle_count[3];
    assign perf_instr_count = core_instr_count[0] + core_instr_count[1] + 
                             core_instr_count[2] + core_instr_count[3];
    assign perf_cache_hits = core_cache_hits[0] + core_cache_hits[1] + 
                            core_cache_hits[2] + core_cache_hits[3];
    assign perf_cache_misses = core_cache_misses[0] + core_cache_misses[1] + 
                              core_cache_misses[2] + core_cache_misses[3];
    assign perf_branch_taken = core_branch_taken[0] + core_branch_taken[1] + 
                              core_branch_taken[2] + core_branch_taken[3];
    assign perf_branch_mispred = core_branch_mispred[0] + core_branch_mispred[1] + 
                                core_branch_mispred[2] + core_branch_mispred[3];

endmodule 
