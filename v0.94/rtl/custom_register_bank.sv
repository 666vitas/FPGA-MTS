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

    logic signed [31:0] integral_acc;
    logic signed [31:0] signed_error_w;
    logic signed [31:0] p_term_w;
    logic signed [31:0] i_term_w;
    logic signed [31:0] raw_lock_w;
    logic signed [13:0] clamped_lock_w;
    logic lock_saturated_w;

    function automatic logic signed [13:0] clamp14(input logic signed [31:0] value);
        if (value > 32'sd8191) begin
            clamp14 = 14'sd8191;
        end else if (value < -32'sd8191) begin
            clamp14 = -14'sd8191;
        end else begin
            clamp14 = value[13:0];
        end
    endfunction

    function automatic logic signed [13:0] clamp_to_limit(
        input logic signed [31:0] value,
        input logic signed [13:0] limit
    );
        logic signed [31:0] abs_limit;
        begin
            abs_limit = (limit < 14'sd0) ? -{{18{limit[13]}}, limit} : {{18{limit[13]}}, limit};
            if (abs_limit > 32'sd8191) begin
                abs_limit = 32'sd8191;
            end
            if (value > abs_limit) begin
                clamp_to_limit = abs_limit[13:0];
            end else if (value < -abs_limit) begin
                clamp_to_limit = -abs_limit[13:0];
            end else begin
                clamp_to_limit = value[13:0];
            end
        end
    endfunction

    assign signed_error_w = polarity_i ? -$signed({{18{error_i[13]}}, error_i}) : $signed({{18{error_i[13]}}, error_i});
    assign p_term_w = ($signed({{18{kp_i[13]}}, kp_i}) * signed_error_w) >>> 8;
    assign i_term_w = ($signed({{18{ki_i[13]}}, ki_i}) * integral_acc) >>> 8;
    assign raw_lock_w = $signed({{18{lock_bias_i[13]}}, lock_bias_i}) + p_term_w +
                        ((mode_i == MODE_PI_LOCK) ? i_term_w : 32'sd0);
    assign clamped_lock_w = clamp_to_limit(raw_lock_w, lock_limit_i);
    assign lock_saturated_w = ({{18{clamped_lock_w[13]}}, clamped_lock_w} != raw_lock_w);

    always_ff @(posedge clk_i) begin
        if (!rstn_i || !enable_i || (mode_i == MODE_SAFE) || integral_reset_i) begin
            integral_acc <= 32'sd0;
        end else if ((mode_i == MODE_PI_LOCK) && !lock_saturated_w) begin
            integral_acc <= integral_acc + signed_error_w;
        end
    end

    always_comb begin
        unique case (mode_i)
            MODE_SCAN: begin
                control_o = enable_i ? scan_i : 14'sd0;
                saturated_o = enable_i ? scan_saturated_i : 1'b0;
            end
            MODE_HOLD: begin
                control_o = enable_i ? clamp14({{18{hold_value_i[13]}}, hold_value_i}) : 14'sd0;
                saturated_o = 1'b0;
            end
            MODE_P_LOCK,
            MODE_PI_LOCK: begin
                control_o = enable_i ? clamped_lock_w : 14'sd0;
                saturated_o = enable_i ? lock_saturated_w : 1'b0;
            end
            default: begin
                control_o = 14'sd0;
                saturated_o = 1'b0;
            end
        endcase
    end

endmodule
