// Pipeline Stage Modules

// Instruction Fetch Stage
module if_stage #(
    parameter DATA_WIDTH = 32,
    parameter ADDR_WIDTH = 32,
    parameter CACHE_SIZE = 512
) (
    input wire clk,
    input wire rst_n,
    input wire enable,
    input wire stall,
    input wire flush,
    input wire [ADDR_WIDTH-1:0] branch_target,
    input wire branch_taken,
    
    // Memory interface
    output reg [ADDR_WIDTH-1:0] mem_addr,
    input wire [DATA_WIDTH-1:0] mem_rdata,
    output reg mem_req,
    input wire mem_ack,
    
    // Output to ID stage
    output reg [DATA_WIDTH-1:0] instruction,
    output reg [ADDR_WIDTH-1:0] pc,
    output reg valid,
    
    // Cache performance
    output wire cache_hit,
    output wire cache_miss
);

    reg [ADDR_WIDTH-1:0] pc_reg;
    reg [ADDR_WIDTH-1:0] next_pc;
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            pc_reg <= 32'h0000_1000; // Boot address
            instruction <= 32'h0000_0013; // NOP
            pc <= 32'h0000_1000;
            valid <= 1'b0;
            mem_req <= 1'b0;
        end else if (enable && !stall) begin
            if (flush) begin
                instruction <= 32'h0000_0013; // NOP
                valid <= 1'b0;
                pc_reg <= branch_target;
            end else if (mem_ack) begin
                instruction <= mem_rdata;
                pc <= pc_reg;
                valid <= 1'b1;
                pc_reg <= next_pc;
            end
            mem_req <= 1'b1;
        end
    end
    
    always @(*) begin
        if (branch_taken) begin
            next_pc = branch_target;
        end else begin
            next_pc = pc_reg + 4;
        end
        mem_addr = pc_reg;
    end
    
    // Simplified cache model
    assign cache_hit = mem_ack;
    assign cache_miss = mem_req & ~mem_ack;

endmodule

// Instruction Decode Stage
module id_stage #(
    parameter DATA_WIDTH = 32,
    parameter ADDR_WIDTH = 32
) (
    input wire clk,
    input wire rst_n,
    input wire stall,
    input wire flush,
    
    // Input from IF stage
    input wire [DATA_WIDTH-1:0] if_instruction,
    input wire [ADDR_WIDTH-1:0] if_pc,
    input wire if_valid,
    
    // Register file interface
    output reg [4:0] rf_rs1_addr,
    output reg [4:0] rf_rs2_addr,
    input wire [DATA_WIDTH-1:0] rf_rs1_data,
    input wire [DATA_WIDTH-1:0] rf_rs2_data,
    
    // Output to EX stage
    output reg [DATA_WIDTH-1:0] id_instruction,
    output reg [ADDR_WIDTH-1:0] id_pc,
    output reg valid,
    
    // Interrupt handling
    input wire [15:0] interrupts,
    output reg interrupt_ack,
    output reg [3:0] interrupt_id
);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            id_instruction <= 32'h0000_0013; // NOP
            id_pc <= 32'h0;
            valid <= 1'b0;
            rf_rs1_addr <= 5'b0;
            rf_rs2_addr <= 5'b0;
            interrupt_ack <= 1'b0;
            interrupt_id <= 4'b0;
        end else if (!stall) begin
            if (flush) begin
                id_instruction <= 32'h0000_0013; // NOP
                valid <= 1'b0;
            end else begin
                id_instruction <= if_instruction;
                id_pc <= if_pc;
                valid <= if_valid;
                
                // Decode register addresses
                rf_rs1_addr <= if_instruction[19:15];
                rf_rs2_addr <= if_instruction[24:20];
            end
            
            // Simple interrupt handling
            if (|interrupts) begin
                interrupt_ack <= 1'b1;
                interrupt_id <= 4'b0; // Simplified
            end else begin
                interrupt_ack <= 1'b0;
            end
        end
    end

endmodule

// Execute Stage
module ex_stage #(
    parameter DATA_WIDTH = 32,
    parameter ADDR_WIDTH = 32
) (
    input wire clk,
    input wire rst_n,
    input wire stall,
    input wire flush,
    
    // Input from ID stage
    input wire [DATA_WIDTH-1:0] id_instruction,
    input wire [ADDR_WIDTH-1:0] id_pc,
    input wire id_valid,
    
    // Output to MEM stage
    output reg [DATA_WIDTH-1:0] ex_result,
    output reg [ADDR_WIDTH-1:0] ex_pc,
    output reg valid,
    
    // Branch control
    output reg branch_taken,
    output reg branch_mispred
);

    wire [6:0] opcode;
    wire [2:0] funct3;
    wire [6:0] funct7;
    wire [DATA_WIDTH-1:0] imm;
    
    assign opcode = id_instruction[6:0];
    assign funct3 = id_instruction[14:12];
    assign funct7 = id_instruction[31:25];
    
    // Simplified immediate generation
    assign imm = {{20{id_instruction[31]}}, id_instruction[31:20]};

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            ex_result <= 32'h0;
            ex_pc <= 32'h0;
            valid <= 1'b0;
            branch_taken <= 1'b0;
            branch_mispred <= 1'b0;
        end else if (!stall) begin
            if (flush) begin
                valid <= 1'b0;
                branch_taken <= 1'b0;
            end else begin
                ex_pc <= id_pc;
                valid <= id_valid;
                
                // Simplified ALU operation
                case (opcode)
                    7'b0010011: ex_result <= id_pc + imm; // ADDI
                    7'b0110011: ex_result <= id_pc + 4;   // R-type
                    7'b1100011: begin // Branch
                        ex_result <= id_pc + imm;
                        branch_taken <= 1'b1; // Simplified
                        branch_mispred <= 1'b0;
                    end
                    default: ex_result <= id_pc + 4;
                endcase
            end
        end
    end

endmodule

// Memory Stage
module mem_stage #(
    parameter DATA_WIDTH = 32,
    parameter ADDR_WIDTH = 32,
    parameter CACHE_SIZE = 512
) (
    input wire clk,
    input wire rst_n,
    input wire stall,
    input wire flush,
    
    // Input from EX stage
    input wire [DATA_WIDTH-1:0] ex_result,
    input wire [ADDR_WIDTH-1:0] ex_pc,
    input wire ex_valid,
    
    // Memory interface
    output reg [ADDR_WIDTH-1:0] mem_addr,
    output reg [DATA_WIDTH-1:0] mem_wdata,
    input wire [DATA_WIDTH-1:0] mem_rdata,
    output reg mem_req,
    output reg mem_we,
    input wire mem_ack,
    
    // Output to WB stage
    output reg [DATA_WIDTH-1:0] mem_result,
    output reg [ADDR_WIDTH-1:0] mem_pc,
    output reg valid,
    
    // Cache performance
    output wire cache_hit,
    output wire cache_miss
);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            mem_result <= 32'h0;
            mem_pc <= 32'h0;
            valid <= 1'b0;
            mem_req <= 1'b0;
            mem_we <= 1'b0;
        end else if (!stall) begin
            if (flush) begin
                valid <= 1'b0;
                mem_req <= 1'b0;
            end else begin
                mem_result <= ex_result;
                mem_pc <= ex_pc;
                valid <= ex_valid;
                
                // Simplified memory access
                mem_addr <= ex_result;
                mem_wdata <= 32'h0;
                mem_req <= ex_valid;
                mem_we <= 1'b0;
            end
        end
    end
    
    // Simplified cache model
    assign cache_hit = mem_ack;
    assign cache_miss = mem_req & ~mem_ack;

endmodule

// Writeback Stage
module wb_stage #(
    parameter DATA_WIDTH = 32,
    parameter ADDR_WIDTH = 32
) (
    input wire clk,
    input wire rst_n,
    input wire stall,
    input wire flush,
    
    // Input from MEM stage
    input wire [DATA_WIDTH-1:0] mem_result,
    input wire [ADDR_WIDTH-1:0] mem_pc,
    input wire mem_valid,
    
    // Register file write interface
    output reg [4:0] rf_rd_addr,
    output reg [DATA_WIDTH-1:0] rf_rd_data,
    output reg rf_we,
    
    // Output
    output reg [DATA_WIDTH-1:0] wb_result,
    output reg [ADDR_WIDTH-1:0] wb_pc,
    output reg valid
);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            wb_result <= 32'h0;
            wb_pc <= 32'h0;
            valid <= 1'b0;
            rf_rd_addr <= 5'b0;
            rf_rd_data <= 32'h0;
            rf_we <= 1'b0;
        end else if (!stall) begin
            if (flush) begin
                valid <= 1'b0;
                rf_we <= 1'b0;
            end else begin
                wb_result <= mem_result;
                wb_pc <= mem_pc;
                valid <= mem_valid;
                
                // Simplified register write
                rf_rd_addr <= 5'b0;
                rf_rd_data <= mem_result;
                rf_we <= mem_valid;
            end
        end
    end

endmodule 
