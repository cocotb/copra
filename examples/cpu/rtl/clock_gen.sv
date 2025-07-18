// Clock Generation Module
module clock_gen #(
    parameter NUM_CORES = 4
) (
    input wire clk_in,
    input wire rst_n_in,
    input wire test_mode,
    input wire [NUM_CORES-1:0] core_enable,
    input wire global_enable,
    output wire [NUM_CORES-1:0] core_clk,
    output wire [NUM_CORES-1:0] core_rst_n,
    output wire system_ready
);

    // Clock gating for each core
    genvar i;
    generate
        for (i = 0; i < NUM_CORES; i = i + 1) begin : gen_core_clocks  // gen_core_clocks: cocotb.handle.HierarchyArrayObject[GenCoreClocks]
            wire gated_enable;
            assign gated_enable = global_enable & core_enable[i];
            
            // Clock gating cell (simplified)
            assign core_clk[i] = clk_in & (gated_enable | test_mode);
            
            // Reset synchronizer
            reg [2:0] reset_sync;
            always @(posedge core_clk[i] or negedge rst_n_in) begin
                if (!rst_n_in) begin
                    reset_sync <= 3'b000;
                end else begin
                    reset_sync <= {reset_sync[1:0], 1'b1};
                end
            end
            assign core_rst_n[i] = reset_sync[2];
        end
    endgenerate
    
    // System ready when all enabled cores are out of reset
    assign system_ready = &(core_rst_n | ~core_enable) & global_enable;

endmodule 
