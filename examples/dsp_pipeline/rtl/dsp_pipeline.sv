module dsp_pipeline #(
    parameter STAGES = 8,
    parameter DATA_WIDTH = 32,
    parameter COEFF_WIDTH = 16,
    parameter NUM_TAPS = 16,
    parameter FFT_SIZE = 64,
    parameter CHANNELS = 4
) (
    input wire clk,
    input wire rst_n,
    
    // Control and Configuration
    input wire enable,
    input wire bypass_mode,
    output reg pipeline_ready,
    output reg [2:0] status_flags,
    
    // Input/Output Data Streams
    input wire [DATA_WIDTH-1:0] data_in,
    input wire data_valid_in,
    output reg [DATA_WIDTH-1:0] data_out,
    output reg data_valid_out,
    
    // Multi-channel inputs (for ArrayObject testing)
    input wire [DATA_WIDTH-1:0] ch_data_in [0:CHANNELS-1],
    input wire [CHANNELS-1:0] ch_valid_in,
    output reg [DATA_WIDTH-1:0] ch_data_out [0:CHANNELS-1],
    output reg [CHANNELS-1:0] ch_valid_out,
    
    // Filter coefficients (for different array types)
    input wire [COEFF_WIDTH-1:0] fir_coeffs [0:NUM_TAPS-1],
    input wire [COEFF_WIDTH-1:0] iir_coeffs_a [0:7],
    input wire [COEFF_WIDTH-1:0] iir_coeffs_b [0:7],
    
    // Configuration registers
    input wire [31:0] sample_rate,
    input wire [31:0] filter_order,
    input wire [31:0] decimation_factor,
    
    // Status and debug outputs
    output reg [63:0] processed_samples,
    output reg [31:0] overflow_count,
    output reg [31:0] underflow_count
);

    // Processing stage enumeration (EnumObject) - use typedef enum for better type recognition
    typedef enum logic [2:0] {
        STAGE_IDLE       = 3'b000,
        STAGE_FILTER     = 3'b001,
        STAGE_FFT        = 3'b010,
        STAGE_MODULATE   = 3'b011,
        STAGE_DECIMATE   = 3'b100,
        STAGE_OUTPUT     = 3'b101,
        STAGE_ERROR      = 3'b110
    } stage_state_t;
    
    stage_state_t current_stage, next_stage;
    
    // Filter type enumeration (EnumObject)
    typedef enum logic [1:0] {
        FILTER_BYPASS = 2'b00,
        FILTER_FIR    = 2'b01,
        FILTER_IIR    = 2'b10,
        FILTER_CIC    = 2'b11
    } filter_type_t;
    
    filter_type_t filter_type;
    
    // Window type enumeration for FFT (EnumObject)
    typedef enum logic [2:0] {
        WINDOW_RECT     = 3'b000,
        WINDOW_HANNING  = 3'b001,
        WINDOW_HAMMING  = 3'b010,
        WINDOW_BLACKMAN = 3'b011,
        WINDOW_KAISER   = 3'b100
    } window_type_t;
    
    window_type_t window_type;
    
    // Internal data pipeline (unpacked arrays for ArrayObject)
    reg [DATA_WIDTH-1:0] stage_data [0:STAGES-1];
    reg [STAGES-1:0] stage_valid;
    reg [DATA_WIDTH-1:0] delay_line [0:NUM_TAPS-1];
    
    // FFT data structures (multiple array types)
    reg [DATA_WIDTH-1:0] fft_real [0:FFT_SIZE-1];
    reg [DATA_WIDTH-1:0] fft_imag [0:FFT_SIZE-1];
    reg [DATA_WIDTH-1:0] fft_magnitude [0:FFT_SIZE-1];
    reg [DATA_WIDTH-1:0] fft_phase [0:FFT_SIZE-1];
    
    // Performance counters and metrics (integers)
    integer clock_cycles;
    integer samples_processed;
    integer filter_operations;
    integer fft_operations;
    
    // Real-valued processing parameters
    real gain_factor;
    real noise_floor;
    real snr_estimate;
    real power_spectral_density;
    real processing_load;
    real temperature_coefficient;
    
    // String-based debug and status information (StringObject)
    // Use specific string lengths to ensure proper string type recognition
    string debug_message;      // SystemVerilog string type
    string filter_status;      // SystemVerilog string type  
    string pipeline_mode;      // SystemVerilog string type
    string error_description;  // SystemVerilog string type
    string version_info;       // SystemVerilog string type
    
    // Additional string arrays for comprehensive coverage
    string stage_names [0:STAGES-1];
    string channel_labels [0:CHANNELS-1];
    
    // Generate blocks for processing stages (HierarchyArrayObject)
    genvar i;
    generate
        for (i = 0; i < STAGES; i = i + 1) begin : gen_processing_stages
            processing_stage #(
                .DATA_WIDTH(DATA_WIDTH),
                .STAGE_ID(i)
            ) stage_inst (
                .clk(clk),
                .rst_n(rst_n),
                .data_in(i == 0 ? data_in : stage_data[i-1]),
                .valid_in(i == 0 ? data_valid_in : stage_valid[i-1]),
                .data_out(stage_data[i]),
                .valid_out(stage_valid[i]),
                .enable(enable && !bypass_mode),
                .stage_type(current_stage)
            );
        end
    endgenerate
    
    // Generate blocks for multi-channel processing (HierarchyArrayObject)
    generate
        for (i = 0; i < CHANNELS; i = i + 1) begin : gen_channel_processors
            channel_processor #(
                .DATA_WIDTH(DATA_WIDTH),
                .CHANNEL_ID(i)
            ) ch_proc_inst (
                .clk(clk),
                .rst_n(rst_n),
                .data_in(ch_data_in[i]),
                .valid_in(ch_valid_in[i]),
                .data_out(ch_data_out[i]),
                .valid_out(ch_valid_out[i]),
                .filter_type(filter_type),
                .gain(gain_factor)
            );
        end
    endgenerate
    
    // Generate blocks for filter taps (HierarchyArrayObject)
    generate
        for (i = 0; i < NUM_TAPS; i = i + 1) begin : gen_filter_taps
            filter_tap #(
                .DATA_WIDTH(DATA_WIDTH),
                .COEFF_WIDTH(COEFF_WIDTH),
                .TAP_ID(i)
            ) tap_inst (
                .clk(clk),
                .rst_n(rst_n),
                .data_in(i == 0 ? data_in : delay_line[i-1]),
                .coeff(fir_coeffs[i]),
                .data_out(delay_line[i]),
                .enable(filter_type == FILTER_FIR)
            );
        end
    endgenerate
    
    // Generate blocks for FFT butterfly units (HierarchyArrayObject)
    generate
        for (i = 0; i < FFT_SIZE/2; i = i + 1) begin : gen_fft_butterflies
            fft_butterfly #(
                .DATA_WIDTH(DATA_WIDTH),
                .BUTTERFLY_ID(i)
            ) butterfly_inst (
                .clk(clk),
                .rst_n(rst_n),
                .real_in(fft_real[i]),
                .imag_in(fft_imag[i]),
                .real_out(fft_real[i+FFT_SIZE/2]),
                .imag_out(fft_imag[i+FFT_SIZE/2]),
                .enable(current_stage == STAGE_FFT)
            );
        end
    endgenerate
    
    // Main DSP control logic
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            current_stage <= STAGE_IDLE;
            filter_type <= FILTER_BYPASS;
            window_type <= WINDOW_RECT;
            clock_cycles <= 0;
            samples_processed <= 0;
            filter_operations <= 0;
            fft_operations <= 0;
            gain_factor <= 1.0;
            noise_floor <= -90.0;
            snr_estimate <= 40.0;
            power_spectral_density <= 0.0;
            processing_load <= 0.0;
            temperature_coefficient <= 0.001;
            
            // Initialize string objects with proper SystemVerilog string assignments
            debug_message = "DSP_INIT";
            filter_status = "IDLE";
            pipeline_mode = "NORMAL";
            error_description = "";
            version_info = "DSP_v2.0";
            
            // Initialize string arrays
            stage_names[0] = "IDLE_STAGE";
            stage_names[1] = "FILTER_STAGE";
            stage_names[2] = "FFT_STAGE";
            stage_names[3] = "MOD_STAGE";
            stage_names[4] = "DEC_STAGE";
            stage_names[5] = "OUT_STAGE";
            stage_names[6] = "ERR_STAGE";
            stage_names[7] = "SPARE_STAGE";
            
            channel_labels[0] = "LEFT_CH";
            channel_labels[1] = "RIGHT_CH";
            channel_labels[2] = "AUX1_CH";
            channel_labels[3] = "AUX2_CH";
            
            processed_samples <= 0;
            overflow_count <= 0;
            underflow_count <= 0;
        end else begin
            current_stage <= next_stage;
            clock_cycles <= clock_cycles + 1;
            
            // Update performance metrics
            if (data_valid_in) begin
                samples_processed <= samples_processed + 1;
                processed_samples <= processed_samples + 1;
            end
            
            // Update real-time calculations
            if (samples_processed > 0) begin
                processing_load <= (filter_operations + fft_operations) * 100.0 / samples_processed;
                snr_estimate <= 40.0 + (gain_factor - 1.0) * 6.0;
                power_spectral_density <= noise_floor + 20.0 * $log10(gain_factor);
            end
            
            // Update status strings based on current stage (using SystemVerilog string assignment)
            case (current_stage)
                STAGE_IDLE: begin
                    debug_message = "WAITING_FOR_DATA";
                    filter_status = "IDLE";
                end
                STAGE_FILTER: begin
                    debug_message = "FILTERING_IN_PROGRESS";
                    filter_status = "ACTIVE";
                    filter_operations <= filter_operations + 1;
                end
                STAGE_FFT: begin
                    debug_message = "FFT_PROCESSING";
                    filter_status = "FFT";
                    fft_operations <= fft_operations + 1;
                end
                STAGE_MODULATE: begin
                    debug_message = "MODULATION_ACTIVE";
                    filter_status = "MOD";
                end
                STAGE_DECIMATE: begin
                    debug_message = "DECIMATION_ACTIVE";
                    filter_status = "DEC";
                end
                STAGE_OUTPUT: begin
                    debug_message = "OUTPUT_GENERATION";
                    filter_status = "OUT";
                end
                STAGE_ERROR: begin
                    debug_message = "ERROR_STATE_DETECTED";
                    filter_status = "ERROR";
                    error_description = "PROCESSING_ERROR";
                end
                default: begin
                    debug_message = "UNKNOWN_STATE";
                    filter_status = "UNK";
                end
            endcase
            
            // Update pipeline mode based on bypass setting
            if (bypass_mode) begin
                pipeline_mode = "BYPASS";
            end else if (enable) begin
                pipeline_mode = "ACTIVE";
            end else begin
                pipeline_mode = "DISABLED";
            end
        end
    end
    
    // State machine for pipeline control
    always @(*) begin
        next_stage = current_stage;
        pipeline_ready = 1'b0;
        status_flags = 3'b000;
        data_out = 32'h0;
        data_valid_out = 1'b0;
        
        case (current_stage)
            STAGE_IDLE: begin
                pipeline_ready = 1'b1;
                if (enable && data_valid_in) begin
                    if (bypass_mode) begin
                        next_stage = STAGE_OUTPUT;
                    end else begin
                        next_stage = STAGE_FILTER;
                    end
                end
            end
            
            STAGE_FILTER: begin
                status_flags[0] = 1'b1; // Filter active
                if (filter_type == FILTER_BYPASS) begin
                    next_stage = STAGE_FFT;
                end else begin
                    next_stage = STAGE_FFT;
                end
            end
            
            STAGE_FFT: begin
                status_flags[1] = 1'b1; // FFT active
                next_stage = STAGE_MODULATE;
            end
            
            STAGE_MODULATE: begin
                next_stage = STAGE_DECIMATE;
            end
            
            STAGE_DECIMATE: begin
                next_stage = STAGE_OUTPUT;
            end
            
            STAGE_OUTPUT: begin
                status_flags[2] = 1'b1; // Output active
                data_out = bypass_mode ? data_in : stage_data[STAGES-1];
                data_valid_out = 1'b1;
                next_stage = STAGE_IDLE;
            end
            
            STAGE_ERROR: begin
                status_flags = 3'b111; // All error flags
                next_stage = STAGE_IDLE;
            end
            
            default: begin
                next_stage = STAGE_ERROR;
            end
        endcase
    end

endmodule