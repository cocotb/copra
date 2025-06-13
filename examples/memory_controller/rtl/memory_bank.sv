module memory_bank #(
    parameter ADDR_WIDTH = 8,
    parameter DATA_WIDTH = 64
) (
    input wire clk,
    input wire rst_n,
    input wire [ADDR_WIDTH-1:0] addr,
    input wire sel,
    input wire [DATA_WIDTH-1:0] wdata,
    output reg [DATA_WIDTH-1:0] rdata
);

    reg [DATA_WIDTH-1:0] memory [0:(1<<ADDR_WIDTH)-1];
    integer access_count;
    real efficiency;
    
    always @(posedge clk) begin
        if (rst_n) begin
            if (sel) begin
                if (wdata != 0) begin  // Write operation
                    memory[addr] <= wdata;
                end
                rdata <= memory[addr];
                access_count <= access_count + 1;
                efficiency <= access_count * 100.0 / (1<<ADDR_WIDTH);
            end
        end else begin
            access_count <= 0;
            efficiency <= 0.0;
        end
    end

endmodule
