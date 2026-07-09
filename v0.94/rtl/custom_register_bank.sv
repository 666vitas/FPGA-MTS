`timescale 1ns/1ps

module custom_register_bank (
    input  logic               clk_i,
    input  logic               rstn_i,
    input  logic signed [13:0] out2_monitor_i,
    input  logic signed [13:0] error_monitor_i,
    input  logic signed [13:0] control_monitor_i,
    input  logic               saturated_i,
    output logic        [31:0] mode_o,
    output logic               enable_o,
    output logic signed [13:0] scan_offset_o,
    output logic signed [13:0] scan_amp_o,
    output logic signed [13:0] scan_step_o,
    output logic        [31:0] scan_update_div_o,
    output logic signed [13:0] out2_limit_o,
    output logic signed [13:0] hold_value_o,
    output logic signed [13:0] kp_o,
    output logic               polarity_o,
    output logic signed [13:0] lock_bias_o,
    output logic signed [13:0] lock_limit_o,
    output logic signed [13:0] ki_o,
    output logic               integral_reset_o,
    sys_bus_if.s               bus
);

    localparam logic [31:0] REG_MAGIC_VALUE   = 32'h4D545330;
    localparam logic [31:0] REG_VERSION_VALUE = 32'h00030000;

    localparam logic [5:0] REG_MAGIC           = 6'h00;
    localparam logic [5:0] REG_VERSION         = 6'h01;
    localparam logic [5:0] REG_MODE            = 6'h02;
    localparam logic [5:0] REG_ENABLE          = 6'h03;
    localparam logic [5:0] REG_SCAN_OFFSET     = 6'h04;
    localparam logic [5:0] REG_SCAN_AMP        = 6'h05;
    localparam logic [5:0] REG_SCAN_STEP       = 6'h06;
    localparam logic [5:0] REG_SCAN_UPDATE_DIV = 6'h07;
    localparam logic [5:0] REG_OUT2_LIMIT      = 6'h08;
    localparam logic [5:0] REG_STATUS          = 6'h09;
    localparam logic [5:0] REG_OUT2_MONITOR    = 6'h0A;
    localparam logic [5:0] REG_HOLD_VALUE      = 6'h0B;
    localparam logic [5:0] REG_KP              = 6'h0C;
    localparam logic [5:0] REG_POLARITY        = 6'h0D;
    localparam logic [5:0] REG_LOCK_BIAS       = 6'h0E;
    localparam logic [5:0] REG_LOCK_LIMIT      = 6'h0F;
    localparam logic [5:0] REG_ERROR_MONITOR   = 6'h10;
    localparam logic [5:0] REG_CONTROL_MONITOR = 6'h11;
    localparam logic [5:0] REG_KI              = 6'h12;
    localparam logic [5:0] REG_INTEGRAL_RESET  = 6'h13;

    logic [5:0] reg_addr_w;
    logic sys_en_w;
    logic enabled_status_w;

    assign reg_addr_w = bus.addr[2+:6];
    assign sys_en_w = bus.wen | bus.ren;
    assign enabled_status_w = enable_o && (mode_o != 32'd0);

    always_ff @(posedge clk_i) begin
        if (!rstn_i) begin
            mode_o            <= 32'd0;
            enable_o          <= 1'b0;
            scan_offset_o     <= 14'sd6962;
            scan_amp_o        <= 14'sd410;
            scan_step_o       <= 14'sd1;
            scan_update_div_o <= 32'd1524;
            out2_limit_o      <= 14'sd8191;
            hold_value_o      <= 14'sd0;
            kp_o              <= 14'sd0;
            polarity_o        <= 1'b0;
            lock_bias_o       <= 14'sd0;
            lock_limit_o      <= 14'sd8191;
            ki_o              <= 14'sd0;
            integral_reset_o  <= 1'b0;
        end else if (bus.wen) begin
            unique case (reg_addr_w)
                REG_MODE: begin
                    unique case (bus.wdata)
                        32'd1,
                        32'd2,
                        32'd3,
                        32'd4: mode_o <= bus.wdata;
                        default: mode_o <= 32'd0;
                    endcase
                end
                REG_ENABLE: begin
                    enable_o <= bus.wdata[0];
                end
                REG_SCAN_OFFSET: begin
                    scan_offset_o <= bus.wdata[13:0];
                end
                REG_SCAN_AMP: begin
                    scan_amp_o <= bus.wdata[13:0];
                end
                REG_SCAN_STEP: begin
                    scan_step_o <= bus.wdata[13:0];
                end
                REG_SCAN_UPDATE_DIV: begin
                    scan_update_div_o <= (bus.wdata == 32'd0) ? 32'd1 : bus.wdata;
                end
                REG_OUT2_LIMIT: begin
                    if ($signed({1'b0, bus.wdata[13:0]}) > 15'sd8191) begin
                        out2_limit_o <= 14'sd8191;
                    end else begin
                        out2_limit_o <= bus.wdata[13:0];
                    end
                end
                REG_HOLD_VALUE: begin
                    hold_value_o <= bus.wdata[13:0];
                end
                REG_KP: begin
                    kp_o <= bus.wdata[13:0];
                end
                REG_POLARITY: begin
                    polarity_o <= bus.wdata[0];
                end
                REG_LOCK_BIAS: begin
                    lock_bias_o <= bus.wdata[13:0];
                end
                REG_LOCK_LIMIT: begin
                    if ($signed({1'b0, bus.wdata[13:0]}) > 15'sd8191) begin
                        lock_limit_o <= 14'sd8191;
                    end else begin
                        lock_limit_o <= bus.wdata[13:0];
                    end
                end
                REG_KI: begin
                    ki_o <= bus.wdata[13:0];
                end
                REG_INTEGRAL_RESET: begin
                    integral_reset_o <= bus.wdata[0];
                end
                default: begin
                end
            endcase
        end else begin
            integral_reset_o <= 1'b0;
        end
    end

    always_ff @(posedge clk_i) begin
        if (!rstn_i) begin
            bus.ack   <= 1'b0;
            bus.err   <= 1'b0;
            bus.rdata <= 32'd0;
        end else begin
            bus.ack <= sys_en_w;
            bus.err <= 1'b0;

            if (bus.ren) begin
                unique case (reg_addr_w)
                    REG_MAGIC: begin
                        bus.rdata <= REG_MAGIC_VALUE;
                    end
                    REG_VERSION: begin
                        bus.rdata <= REG_VERSION_VALUE;
                    end
                    REG_MODE: begin
                        bus.rdata <= mode_o;
                    end
                    REG_ENABLE: begin
                        bus.rdata <= {31'd0, enable_o};
                    end
                    REG_SCAN_OFFSET: begin
                        bus.rdata <= {{18{scan_offset_o[13]}}, scan_offset_o};
                    end
                    REG_SCAN_AMP: begin
                        bus.rdata <= {{18{scan_amp_o[13]}}, scan_amp_o};
                    end
                    REG_SCAN_STEP: begin
                        bus.rdata <= {{18{scan_step_o[13]}}, scan_step_o};
                    end
                    REG_SCAN_UPDATE_DIV: begin
                        bus.rdata <= scan_update_div_o;
                    end
                    REG_OUT2_LIMIT: begin
                        bus.rdata <= {{18{out2_limit_o[13]}}, out2_limit_o};
                    end
                    REG_STATUS: begin
                        bus.rdata <= {30'd0, saturated_i, enabled_status_w};
                    end
                    REG_OUT2_MONITOR: begin
                        bus.rdata <= {{18{out2_monitor_i[13]}}, out2_monitor_i};
                    end
                    REG_HOLD_VALUE: begin
                        bus.rdata <= {{18{hold_value_o[13]}}, hold_value_o};
                    end
                    REG_KP: begin
                        bus.rdata <= {{18{kp_o[13]}}, kp_o};
                    end
                    REG_POLARITY: begin
                        bus.rdata <= {31'd0, polarity_o};
                    end
                    REG_LOCK_BIAS: begin
                        bus.rdata <= {{18{lock_bias_o[13]}}, lock_bias_o};
                    end
                    REG_LOCK_LIMIT: begin
                        bus.rdata <= {{18{lock_limit_o[13]}}, lock_limit_o};
                    end
                    REG_ERROR_MONITOR: begin
                        bus.rdata <= {{18{error_monitor_i[13]}}, error_monitor_i};
                    end
                    REG_CONTROL_MONITOR: begin
                        bus.rdata <= {{18{control_monitor_i[13]}}, control_monitor_i};
                    end
                    REG_KI: begin
                        bus.rdata <= {{18{ki_o[13]}}, ki_o};
                    end
                    REG_INTEGRAL_RESET: begin
                        bus.rdata <= {31'd0, integral_reset_o};
                    end
                    default: begin
                        bus.rdata <= 32'd0;
                    end
                endcase
            end
        end
    end

endmodule

module out2_lock_controller (
    input  logic               clk_i,
    input  logic               rstn_i,
    input  logic               enable_i,
    input  logic        [31:0] mode_i,
    input  logic signed [13:0] scan_i,
    input  logic               scan_saturated_i,
    input  logic signed [13:0] hold_value_i,
    input  logic signed [13:0] error_i,
    input  logic signed [13:0] kp_i,
    input  logic signed [13:0] ki_i,
    input  logic               polarity_i,
    input  logic signed [13:0] lock_bias_i,
    input  logic signed [13:0] lock_limit_i,
    input  logic               integral_reset_i,
    output logic signed [13:0] control_o,
    output logic               saturated_o
);

    localparam logic [31:0] MODE_SAFE    = 32'd0;
    localparam logic [31:0] MODE_SCAN    = 32'd1;
    localparam logic [31:0] MODE_HOLD    = 32'd2;
    localparam logic [31:0] MODE_P_LOCK  = 32'd3;
    localparam logic [31:0] MODE_PI_LOCK = 32'd4;

    logic               s0_enable;
    logic        [31:0] s0_mode;
    logic signed [13:0] s0_error;
    logic signed [13:0] s0_kp;
    logic               s0_polarity;
    logic signed [13:0] s0_lock_bias;
    logic signed [13:0] s0_lock_limit;

    logic               s1_enable;
    logic        [31:0] s1_mode;
    logic signed [14:0] s1_signed_error;
    logic signed [13:0] s1_kp;
    logic signed [13:0] s1_lock_bias;
    logic signed [13:0] s1_lock_limit;

    logic               s2_enable;
    logic        [31:0] s2_mode;
    logic signed [28:0] s2_p_product;
    logic signed [13:0] s2_lock_bias;
    logic signed [13:0] s2_lock_limit;

    logic               s3_enable;
    logic        [31:0] s3_mode;
    logic signed [31:0] s3_p_term;
    logic signed [13:0] s3_lock_bias;
    logic signed [13:0] s3_lock_limit;

    logic               s4_enable;
    logic        [31:0] s4_mode;
    logic signed [31:0] s4_raw;
    logic signed [13:0] s4_lock_limit;

    logic signed [31:0] abs_limit_w;

    always_comb begin
        if (s4_lock_limit < 14'sd0) begin
            abs_limit_w = -$signed({{18{s4_lock_limit[13]}}, s4_lock_limit});
        end else begin
            abs_limit_w = $signed({{18{s4_lock_limit[13]}}, s4_lock_limit});
        end

        if (abs_limit_w > 32'sd8191) begin
            abs_limit_w = 32'sd8191;
        end
    end

    always_ff @(posedge clk_i) begin
        if (!rstn_i) begin
            s0_enable       <= 1'b0;
            s0_mode         <= MODE_SAFE;
            s0_error        <= 14'sd0;
            s0_kp           <= 14'sd0;
            s0_polarity     <= 1'b0;
            s0_lock_bias    <= 14'sd0;
            s0_lock_limit   <= 14'sd8191;
            s1_enable       <= 1'b0;
            s1_mode         <= MODE_SAFE;
            s1_signed_error <= 15'sd0;
            s1_kp           <= 14'sd0;
            s1_lock_bias    <= 14'sd0;
            s1_lock_limit   <= 14'sd8191;
            s2_enable       <= 1'b0;
            s2_mode         <= MODE_SAFE;
            s2_p_product    <= 29'sd0;
            s2_lock_bias    <= 14'sd0;
            s2_lock_limit   <= 14'sd8191;
            s3_enable       <= 1'b0;
            s3_mode         <= MODE_SAFE;
            s3_p_term       <= 32'sd0;
            s3_lock_bias    <= 14'sd0;
            s3_lock_limit   <= 14'sd8191;
            s4_enable       <= 1'b0;
            s4_mode         <= MODE_SAFE;
            s4_raw          <= 32'sd0;
            s4_lock_limit   <= 14'sd8191;
            control_o       <= 14'sd0;
            saturated_o     <= 1'b0;
        end else begin
            s0_enable     <= enable_i;
            s0_mode       <= mode_i;
            s0_error      <= error_i;
            s0_kp         <= kp_i;
            s0_polarity   <= polarity_i;
            s0_lock_bias  <= lock_bias_i;
            s0_lock_limit <= lock_limit_i;

            s1_enable       <= s0_enable;
            s1_mode         <= s0_mode;
            s1_signed_error <= s0_polarity
                             ? -$signed({s0_error[13], s0_error})
                             :  $signed({s0_error[13], s0_error});
            s1_kp           <= s0_kp;
            s1_lock_bias    <= s0_lock_bias;
            s1_lock_limit   <= s0_lock_limit;

            s2_enable     <= s1_enable;
            s2_mode       <= s1_mode;
            s2_p_product  <= $signed({{14{s1_signed_error[14]}}, s1_signed_error}) *
                             $signed({{15{s1_kp[13]}}, s1_kp});
            s2_lock_bias  <= s1_lock_bias;
            s2_lock_limit <= s1_lock_limit;

            s3_enable     <= s2_enable;
            s3_mode       <= s2_mode;
            s3_p_term     <= $signed(s2_p_product) >>> 8;
            s3_lock_bias  <= s2_lock_bias;
            s3_lock_limit <= s2_lock_limit;

            s4_enable     <= s3_enable;
            s4_mode       <= s3_mode;
            s4_raw        <= $signed({{18{s3_lock_bias[13]}}, s3_lock_bias}) + s3_p_term;
            s4_lock_limit <= s3_lock_limit;

            if (!enable_i || (mode_i == MODE_SAFE)) begin
                control_o   <= 14'sd0;
                saturated_o <= 1'b0;
            end else begin
                unique case (mode_i)
                    MODE_SCAN: begin
                        control_o   <= scan_i;
                        saturated_o <= scan_saturated_i;
                    end
                    MODE_HOLD: begin
                        control_o   <= hold_value_i;
                        saturated_o <= 1'b0;
                    end
                    MODE_P_LOCK,
                    MODE_PI_LOCK: begin
                        if (s4_enable && ((s4_mode == MODE_P_LOCK) || (s4_mode == MODE_PI_LOCK))) begin
                            if (s4_raw > abs_limit_w) begin
                                control_o   <= abs_limit_w[13:0];
                                saturated_o <= 1'b1;
                            end else if (s4_raw < -abs_limit_w) begin
                                control_o   <= -abs_limit_w[13:0];
                                saturated_o <= 1'b1;
                            end else begin
                                control_o   <= s4_raw[13:0];
                                saturated_o <= 1'b0;
                            end
                        end else begin
                            control_o   <= 14'sd0;
                            saturated_o <= 1'b0;
                        end
                    end
                    default: begin
                        control_o   <= 14'sd0;
                        saturated_o <= 1'b0;
                    end
                endcase
            end
        end
    end

endmodule
