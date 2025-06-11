// Complex CPU Top-Level Module
// This is an extensive example to test copra's capabilities
module cpu_top #(
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
    
    // Multi-Core CPU Complex
    cpu #(
        .DATA_WIDTH(DATA_WIDTH),
        .ADDR_WIDTH(ADDR_WIDTH),
        .NUM_CORES(NUM_CORES),
        .CACHE_SIZE(CACHE_SIZE)
    ) u_cpu (
        .clk(core_clk),
        .rst_n(core_rst_n),
        .core_enable(core_enable),
        .core_active(core_active),
        .core_halted(core_halted),
        .core_error(core_error),
        
        // Instruction Fetch AXI Interface
        .m_axi_if_awid(m_axi_if_awid),
        .m_axi_if_awaddr(m_axi_if_awaddr),
        .m_axi_if_awlen(m_axi_if_awlen),
        .m_axi_if_awsize(m_axi_if_awsize),
        .m_axi_if_awburst(m_axi_if_awburst),
        .m_axi_if_awlock(m_axi_if_awlock),
        .m_axi_if_awcache(m_axi_if_awcache),
        .m_axi_if_awprot(m_axi_if_awprot),
        .m_axi_if_awvalid(m_axi_if_awvalid),
        .m_axi_if_awready(m_axi_if_awready),
        .m_axi_if_wdata(m_axi_if_wdata),
        .m_axi_if_wstrb(m_axi_if_wstrb),
        .m_axi_if_wlast(m_axi_if_wlast),
        .m_axi_if_wvalid(m_axi_if_wvalid),
        .m_axi_if_wready(m_axi_if_wready),
        .m_axi_if_bid(m_axi_if_bid),
        .m_axi_if_bresp(m_axi_if_bresp),
        .m_axi_if_bvalid(m_axi_if_bvalid),
        .m_axi_if_bready(m_axi_if_bready),
        .m_axi_if_arid(m_axi_if_arid),
        .m_axi_if_araddr(m_axi_if_araddr),
        .m_axi_if_arlen(m_axi_if_arlen),
        .m_axi_if_arsize(m_axi_if_arsize),
        .m_axi_if_arburst(m_axi_if_arburst),
        .m_axi_if_arlock(m_axi_if_arlock),
        .m_axi_if_arcache(m_axi_if_arcache),
        .m_axi_if_arprot(m_axi_if_arprot),
        .m_axi_if_arvalid(m_axi_if_arvalid),
        .m_axi_if_arready(m_axi_if_arready),
        .m_axi_if_rid(m_axi_if_rid),
        .m_axi_if_rdata(m_axi_if_rdata),
        .m_axi_if_rresp(m_axi_if_rresp),
        .m_axi_if_rlast(m_axi_if_rlast),
        .m_axi_if_rvalid(m_axi_if_rvalid),
        .m_axi_if_rready(m_axi_if_rready),
        
        // Data Memory AXI Interface
        .m_axi_dm_awid(m_axi_dm_awid),
        .m_axi_dm_awaddr(m_axi_dm_awaddr),
        .m_axi_dm_awlen(m_axi_dm_awlen),
        .m_axi_dm_awsize(m_axi_dm_awsize),
        .m_axi_dm_awburst(m_axi_dm_awburst),
        .m_axi_dm_awlock(m_axi_dm_awlock),
        .m_axi_dm_awcache(m_axi_dm_awcache),
        .m_axi_dm_awprot(m_axi_dm_awprot),
        .m_axi_dm_awvalid(m_axi_dm_awvalid),
        .m_axi_dm_awready(m_axi_dm_awready),
        .m_axi_dm_wdata(m_axi_dm_wdata),
        .m_axi_dm_wstrb(m_axi_dm_wstrb),
        .m_axi_dm_wlast(m_axi_dm_wlast),
        .m_axi_dm_wvalid(m_axi_dm_wvalid),
        .m_axi_dm_wready(m_axi_dm_wready),
        .m_axi_dm_bid(m_axi_dm_bid),
        .m_axi_dm_bresp(m_axi_dm_bresp),
        .m_axi_dm_bvalid(m_axi_dm_bvalid),
        .m_axi_dm_bready(m_axi_dm_bready),
        .m_axi_dm_arid(m_axi_dm_arid),
        .m_axi_dm_araddr(m_axi_dm_araddr),
        .m_axi_dm_arlen(m_axi_dm_arlen),
        .m_axi_dm_arsize(m_axi_dm_arsize),
        .m_axi_dm_arburst(m_axi_dm_arburst),
        .m_axi_dm_arlock(m_axi_dm_arlock),
        .m_axi_dm_arcache(m_axi_dm_arcache),
        .m_axi_dm_arprot(m_axi_dm_arprot),
        .m_axi_dm_arvalid(m_axi_dm_arvalid),
        .m_axi_dm_arready(m_axi_dm_arready),
        .m_axi_dm_rid(m_axi_dm_rid),
        .m_axi_dm_rdata(m_axi_dm_rdata),
        .m_axi_dm_rresp(m_axi_dm_rresp),
        .m_axi_dm_rlast(m_axi_dm_rlast),
        .m_axi_dm_rvalid(m_axi_dm_rvalid),
        .m_axi_dm_rready(m_axi_dm_rready),
        
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
        
        // Performance Monitoring
        .perf_cycle_count(perf_cycle_count),
        .perf_instr_count(perf_instr_count),
        .perf_cache_hits(perf_cache_hits),
        .perf_cache_misses(perf_cache_misses),
        .perf_branch_taken(perf_branch_taken),
        .perf_branch_mispred(perf_branch_mispred)
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

endmodule 