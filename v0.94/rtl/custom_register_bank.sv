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
    output logic signed [13:0] lock_correction_limit_o,
    output logic signed [13:0] error_setpoint_o,
    output logic signed [13:0] ki_o,
    output logic               integral_reset_o,
    output logic               acq_trigger_o,
    output logic               acq_abort_o,
    output logic               acq_fault_o,
    output logic               capture_start_o,
    output logic        [31:0] capture_decimation_o,
    output logic        [31:0] capture_length_o,
    output logic        [31:0] capture_read_index_o,
    input  logic               capture_busy_i,
    input  logic               capture_done_i,
    input  logic signed [13:0] lock_error_monitor_i,
    input  logic signed [13:0] capture_data_ch1_i,
    input  logic signed [13:0] capture_data_ch2_i,
    input  logic signed [13:0] capture_data_ch3_i,
    input  logic signed [13:0] capture_data_ch4_i,
    sys_bus_if.s               bus
);

    localparam logic [31:0] REG_MAGIC_VALUE   = 32'h4D545330;
    localparam logic [31:0] REG_VERSION_VALUE = 32'h00030100;

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
    localparam logic [5:0] REG_LOCK_CORRECTION_LIMIT = 6'h14;
    localparam logic [5:0] REG_ERROR_SETPOINT  = 6'h15;
    localparam logic [5:0] REG_LOCK_ERROR_MONITOR = 6'h16;
    localparam logic [5:0] REG_CAPTURE_LOCK_POINT = 6'h17;

    localparam logic [5:0] REG_TARGET_OUT2_SHADOW           = 6'h18;
    localparam logic [5:0] REG_TARGET_ERROR_SETPOINT_SHADOW = 6'h19;
    localparam logic [5:0] REG_TARGET_WINDOW_SHADOW         = 6'h1A;
    localparam logic [5:0] REG_TARGET_REQUIREMENTS_SHADOW   = 6'h1B;
    localparam logic [5:0] REG_CORRECTION_LIMIT_SHADOW      = 6'h1C;
    localparam logic [5:0] REG_ABSOLUTE_LIMIT_SHADOW        = 6'h1D;
    localparam logic [5:0] REG_CONFIG_GENERATION_SHADOW     = 6'h1E;
    localparam logic [5:0] REG_CONFIG_VALIDATION            = 6'h1F;

    localparam logic [5:0] REG_CAPTURE_CTRL       = 6'h20;
    localparam logic [5:0] REG_CAPTURE_STATUS     = 6'h21;
    localparam logic [5:0] REG_CAPTURE_DECIMATION = 6'h22;
    localparam logic [5:0] REG_CAPTURE_LENGTH     = 6'h23;
    localparam logic [5:0] REG_CAPTURE_READ_INDEX = 6'h24;
    localparam logic [5:0] REG_CAPTURE_DATA_CH1   = 6'h25;
    localparam logic [5:0] REG_CAPTURE_DATA_CH2   = 6'h26;
    localparam logic [5:0] REG_CAPTURE_DATA_CH3   = 6'h27;
    localparam logic [5:0] REG_CAPTURE_DATA_CH4   = 6'h28;

    localparam logic [5:0] REG_ACQ_COMMAND              = 6'h29;
    localparam logic [5:0] REG_ACQ_STATE                = 6'h2A;
    localparam logic [5:0] REG_EVENT_SEQUENCE           = 6'h2B;
    localparam logic [5:0] REG_EVENT_OUT2               = 6'h2C;
    localparam logic [5:0] REG_EVENT_ERROR              = 6'h2D;
    localparam logic [5:0] REG_EVENT_CONFIG_GENERATION  = 6'h2E;
    localparam logic [5:0] REG_EVENT_INFO               = 6'h2F;
    localparam logic [5:0] REG_EVENT_TIMESTAMP_LO       = 6'h30;
    localparam logic [5:0] REG_EVENT_TIMESTAMP_HI       = 6'h31;
    localparam logic [5:0] REG_ACTIVE_TARGET_OUT2       = 6'h32;
    localparam logic [5:0] REG_ACTIVE_ERROR_SETPOINT    = 6'h33;
    localparam logic [5:0] REG_ACTIVE_WINDOW            = 6'h34;
    localparam logic [5:0] REG_ACTIVE_REQUIREMENTS      = 6'h35;
    localparam logic [5:0] REG_ACTIVE_CORRECTION_LIMIT  = 6'h36;
    localparam logic [5:0] REG_ACTIVE_ABSOLUTE_LIMIT    = 6'h37;
    localparam logic [5:0] REG_FAULT_DETAIL             = 6'h38;

    localparam logic [31:0] MODE_SAFE   = 32'd0;
    localparam logic [31:0] MODE_SCAN   = 32'd1;
    localparam logic [31:0] MODE_HOLD   = 32'd2;
    localparam logic [31:0] MODE_P_LOCK = 32'd3;

    logic [5:0] reg_addr_w;
    logic sys_en_w;
    logic enabled_status_w;

    logic [31:0] target_out2_shadow_q;
    logic [31:0] target_error_setpoint_shadow_q;
    logic [31:0] target_window_shadow_q;
    logic [31:0] target_requirements_shadow_q;
    logic [31:0] correction_limit_shadow_q;
    logic [31:0] absolute_limit_shadow_q;
    logic [31:0] config_generation_shadow_q;
    logic  [6:0] shadow_written_mask_q;

    logic command_write_w;
    logic arm_pulse_w;
    logic abort_pulse_w;
    logic clear_event_pulse_w;
    logic command_reject_pulse_w;
    logic apply_p_pulse_w;

    logic [31:0] config_validation_w;
    logic [31:0] acq_state_w;
    logic [31:0] event_sequence_w;
    logic [31:0] event_out2_w;
    logic [31:0] event_error_w;
    logic [31:0] event_config_generation_w;
    logic [31:0] event_info_w;
    logic [31:0] event_timestamp_lo_w;
    logic [31:0] event_timestamp_hi_w;
    logic [31:0] fault_detail_w;
    logic signed [13:0] active_target_out2_w;
    logic signed [13:0] active_error_setpoint_w;
    logic [13:0] active_window_w;
    logic [31:0] active_requirements_w;
    logic [13:0] active_correction_limit_w;
    logic [13:0] active_absolute_limit_w;
    logic arm_accepted_w;

    assign reg_addr_w = bus.addr[2+:6];
    assign sys_en_w = bus.wen | bus.ren;
    assign enabled_status_w = enable_o && (mode_o != MODE_SAFE);

    assign command_write_w = bus.wen && (reg_addr_w == REG_ACQ_COMMAND);
    assign arm_pulse_w = command_write_w && (bus.wdata == 32'h0000_0001);
    assign abort_pulse_w = command_write_w && (bus.wdata == 32'h0000_0002);
    assign clear_event_pulse_w = command_write_w && (bus.wdata == 32'h0000_0004);
    assign command_reject_pulse_w = command_write_w &&
                                    (bus.wdata != 32'h0000_0001) &&
                                    (bus.wdata != 32'h0000_0002) &&
                                    (bus.wdata != 32'h0000_0004);
    assign apply_p_pulse_w = bus.wen && (reg_addr_w == REG_KP);
    assign acq_abort_o = abort_pulse_w;

    deterministic_lock_acquisition i_deterministic_lock_acquisition (
        .clk_i(clk_i),
        .rstn_i(rstn_i),
        .mode_i(mode_o),
        .enable_i(enable_o),
        .saturated_i(saturated_i),
        .out2_i(out2_monitor_i),
        .error_i(error_monitor_i),
        .shadow_target_out2_i(target_out2_shadow_q),
        .shadow_error_setpoint_i(target_error_setpoint_shadow_q),
        .shadow_window_i(target_window_shadow_q),
        .shadow_requirements_i(target_requirements_shadow_q),
        .shadow_correction_limit_i(correction_limit_shadow_q),
        .shadow_absolute_limit_i(absolute_limit_shadow_q),
        .shadow_generation_i(config_generation_shadow_q),
        .shadow_written_mask_i(shadow_written_mask_q),
        .arm_pulse_i(arm_pulse_w),
        .abort_pulse_i(abort_pulse_w),
        .clear_event_pulse_i(clear_event_pulse_w),
        .command_reject_pulse_i(command_reject_pulse_w),
        .apply_p_pulse_i(apply_p_pulse_w),
        .apply_p_kp_i(bus.wdata[13:0]),
        .trigger_o(acq_trigger_o),
        .fault_immediate_o(acq_fault_o),
        .arm_accepted_o(arm_accepted_w),
        .config_validation_o(config_validation_w),
        .state_readback_o(acq_state_w),
        .active_target_out2_o(active_target_out2_w),
        .active_error_setpoint_o(active_error_setpoint_w),
        .active_window_o(active_window_w),
        .active_requirements_o(active_requirements_w),
        .active_correction_limit_o(active_correction_limit_w),
        .active_absolute_limit_o(active_absolute_limit_w),
        .event_sequence_o(event_sequence_w),
        .event_out2_o(event_out2_w),
        .event_error_o(event_error_w),
        .event_config_generation_o(event_config_generation_w),
        .event_info_o(event_info_w),
        .event_timestamp_lo_o(event_timestamp_lo_w),
        .event_timestamp_hi_o(event_timestamp_hi_w),
        .fault_detail_o(fault_detail_w)
    );

    always_ff @(posedge clk_i) begin
        if (!rstn_i) begin
            mode_o            <= MODE_SAFE;
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
            lock_correction_limit_o <= 14'sd128;
            error_setpoint_o  <= 14'sd0;
            ki_o              <= 14'sd0;
            integral_reset_o  <= 1'b0;
            capture_start_o   <= 1'b0;
            capture_decimation_o <= 32'd1024;
            capture_length_o   <= 32'd2048;
            capture_read_index_o <= 32'd0;
            target_out2_shadow_q <= 32'd0;
            target_error_setpoint_shadow_q <= 32'd0;
            target_window_shadow_q <= 32'd0;
            target_requirements_shadow_q <= 32'd0;
            correction_limit_shadow_q <= 32'd0;
            absolute_limit_shadow_q <= 32'd0;
            config_generation_shadow_q <= 32'd0;
            shadow_written_mask_q <= 7'd0;
        end else begin
            integral_reset_o <= 1'b0;
            capture_start_o <= 1'b0;

            if (acq_abort_o || acq_fault_o) begin
                mode_o           <= MODE_SAFE;
                enable_o         <= 1'b0;
                kp_o             <= 14'sd0;
                ki_o             <= 14'sd0;
                integral_reset_o <= 1'b1;
            end else if (acq_trigger_o) begin
                lock_bias_o       <= out2_monitor_i;
                error_setpoint_o  <= active_error_setpoint_w;
                lock_correction_limit_o <= $signed({1'b0, active_correction_limit_w[12:0]});
                lock_limit_o      <= $signed({1'b0, active_absolute_limit_w[12:0]});
                kp_o              <= 14'sd0;
                ki_o              <= 14'sd0;
                integral_reset_o  <= 1'b1;
                mode_o            <= MODE_P_LOCK;
                enable_o          <= 1'b1;
            end else if (arm_accepted_w) begin
                kp_o             <= 14'sd0;
                ki_o             <= 14'sd0;
                integral_reset_o <= 1'b1;
            end else if (bus.wen) begin
                unique case (reg_addr_w)
                    REG_MODE: begin
                        unique case (bus.wdata)
                            MODE_SCAN,
                            MODE_HOLD,
                            MODE_P_LOCK,
                            32'd4: mode_o <= bus.wdata;
                            default: mode_o <= MODE_SAFE;
                        endcase
                    end
                    REG_ENABLE: enable_o <= bus.wdata[0];
                    REG_SCAN_OFFSET: scan_offset_o <= bus.wdata[13:0];
                    REG_SCAN_AMP: scan_amp_o <= bus.wdata[13:0];
                    REG_SCAN_STEP: scan_step_o <= bus.wdata[13:0];
                    REG_SCAN_UPDATE_DIV:
                        scan_update_div_o <= (bus.wdata == 32'd0) ? 32'd1 : bus.wdata;
                    REG_OUT2_LIMIT: begin
                        if ($signed({1'b0, bus.wdata[13:0]}) > 15'sd8191)
                            out2_limit_o <= 14'sd8191;
                        else
                            out2_limit_o <= bus.wdata[13:0];
                    end
                    REG_HOLD_VALUE: hold_value_o <= bus.wdata[13:0];
                    REG_KP: kp_o <= bus.wdata[13:0];
                    REG_POLARITY: polarity_o <= bus.wdata[0];
                    REG_LOCK_BIAS: lock_bias_o <= bus.wdata[13:0];
                    REG_LOCK_LIMIT: begin
                        if ($signed({1'b0, bus.wdata[13:0]}) > 15'sd8191)
                            lock_limit_o <= 14'sd8191;
                        else
                            lock_limit_o <= bus.wdata[13:0];
                    end
                    REG_LOCK_CORRECTION_LIMIT: begin
                        if ($signed({1'b0, bus.wdata[13:0]}) > 15'sd8191)
                            lock_correction_limit_o <= 14'sd8191;
                        else
                            lock_correction_limit_o <= bus.wdata[13:0];
                    end
                    REG_ERROR_SETPOINT: error_setpoint_o <= bus.wdata[13:0];
                    REG_CAPTURE_LOCK_POINT: begin
                        if (bus.wdata[0]) begin
                            error_setpoint_o <= error_monitor_i;
                            lock_bias_o      <= out2_monitor_i;
                            kp_o             <= 14'sd0;
                            ki_o             <= 14'sd0;
                            integral_reset_o <= 1'b1;
                            mode_o           <= MODE_P_LOCK;
                            enable_o         <= 1'b1;
                        end
                    end
                    REG_KI: ki_o <= bus.wdata[13:0];
                    REG_INTEGRAL_RESET: integral_reset_o <= bus.wdata[0];
                    REG_TARGET_OUT2_SHADOW: begin
                        target_out2_shadow_q <= bus.wdata;
                        shadow_written_mask_q[0] <= 1'b1;
                    end
                    REG_TARGET_ERROR_SETPOINT_SHADOW: begin
                        target_error_setpoint_shadow_q <= bus.wdata;
                        shadow_written_mask_q[1] <= 1'b1;
                    end
                    REG_TARGET_WINDOW_SHADOW: begin
                        target_window_shadow_q <= bus.wdata;
                        shadow_written_mask_q[2] <= 1'b1;
                    end
                    REG_TARGET_REQUIREMENTS_SHADOW: begin
                        target_requirements_shadow_q <= bus.wdata;
                        shadow_written_mask_q[3] <= 1'b1;
                    end
                    REG_CORRECTION_LIMIT_SHADOW: begin
                        correction_limit_shadow_q <= bus.wdata;
                        shadow_written_mask_q[4] <= 1'b1;
                    end
                    REG_ABSOLUTE_LIMIT_SHADOW: begin
                        absolute_limit_shadow_q <= bus.wdata;
                        shadow_written_mask_q[5] <= 1'b1;
                    end
                    REG_CONFIG_GENERATION_SHADOW: begin
                        config_generation_shadow_q <= bus.wdata;
                        shadow_written_mask_q[6] <= 1'b1;
                    end
                    REG_CAPTURE_CTRL: capture_start_o <= bus.wdata[0];
                    REG_CAPTURE_DECIMATION:
                        capture_decimation_o <= (bus.wdata == 32'd0) ? 32'd1 : bus.wdata;
                    REG_CAPTURE_LENGTH: begin
                        if (bus.wdata == 32'd0)
                            capture_length_o <= 32'd1;
                        else if (bus.wdata > 32'd4096)
                            capture_length_o <= 32'd4096;
                        else
                            capture_length_o <= bus.wdata;
                    end
                    REG_CAPTURE_READ_INDEX: capture_read_index_o <= bus.wdata;
                    default: begin
                    end
                endcase
            end
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
                    REG_MAGIC: bus.rdata <= REG_MAGIC_VALUE;
                    REG_VERSION: bus.rdata <= REG_VERSION_VALUE;
                    REG_MODE: bus.rdata <= mode_o;
                    REG_ENABLE: bus.rdata <= {31'd0, enable_o};
                    REG_SCAN_OFFSET: bus.rdata <= {{18{scan_offset_o[13]}}, scan_offset_o};
                    REG_SCAN_AMP: bus.rdata <= {{18{scan_amp_o[13]}}, scan_amp_o};
                    REG_SCAN_STEP: bus.rdata <= {{18{scan_step_o[13]}}, scan_step_o};
                    REG_SCAN_UPDATE_DIV: bus.rdata <= scan_update_div_o;
                    REG_OUT2_LIMIT: bus.rdata <= {{18{out2_limit_o[13]}}, out2_limit_o};
                    REG_STATUS: bus.rdata <= {30'd0, saturated_i, enabled_status_w};
                    REG_OUT2_MONITOR: bus.rdata <= {{18{out2_monitor_i[13]}}, out2_monitor_i};
                    REG_HOLD_VALUE: bus.rdata <= {{18{hold_value_o[13]}}, hold_value_o};
                    REG_KP: bus.rdata <= {{18{kp_o[13]}}, kp_o};
                    REG_POLARITY: bus.rdata <= {31'd0, polarity_o};
                    REG_LOCK_BIAS: bus.rdata <= {{18{lock_bias_o[13]}}, lock_bias_o};
                    REG_LOCK_LIMIT: bus.rdata <= {{18{lock_limit_o[13]}}, lock_limit_o};
                    REG_LOCK_CORRECTION_LIMIT:
                        bus.rdata <= {{18{lock_correction_limit_o[13]}}, lock_correction_limit_o};
                    REG_ERROR_SETPOINT: bus.rdata <= {{18{error_setpoint_o[13]}}, error_setpoint_o};
                    REG_LOCK_ERROR_MONITOR:
                        bus.rdata <= {{18{lock_error_monitor_i[13]}}, lock_error_monitor_i};
                    REG_CAPTURE_LOCK_POINT,
                    REG_ACQ_COMMAND: bus.rdata <= 32'd0;
                    REG_ERROR_MONITOR: bus.rdata <= {{18{error_monitor_i[13]}}, error_monitor_i};
                    REG_CONTROL_MONITOR:
                        bus.rdata <= {{18{control_monitor_i[13]}}, control_monitor_i};
                    REG_KI: bus.rdata <= {{18{ki_o[13]}}, ki_o};
                    REG_INTEGRAL_RESET: bus.rdata <= {31'd0, integral_reset_o};
                    REG_TARGET_OUT2_SHADOW: bus.rdata <= target_out2_shadow_q;
                    REG_TARGET_ERROR_SETPOINT_SHADOW:
                        bus.rdata <= target_error_setpoint_shadow_q;
                    REG_TARGET_WINDOW_SHADOW: bus.rdata <= target_window_shadow_q;
                    REG_TARGET_REQUIREMENTS_SHADOW:
                        bus.rdata <= target_requirements_shadow_q;
                    REG_CORRECTION_LIMIT_SHADOW: bus.rdata <= correction_limit_shadow_q;
                    REG_ABSOLUTE_LIMIT_SHADOW: bus.rdata <= absolute_limit_shadow_q;
                    REG_CONFIG_GENERATION_SHADOW: bus.rdata <= config_generation_shadow_q;
                    REG_CONFIG_VALIDATION: bus.rdata <= config_validation_w;
                    REG_CAPTURE_CTRL: bus.rdata <= 32'd0;
                    REG_CAPTURE_STATUS:
                        bus.rdata <= {30'd0, capture_done_i, capture_busy_i};
                    REG_CAPTURE_DECIMATION: bus.rdata <= capture_decimation_o;
                    REG_CAPTURE_LENGTH: bus.rdata <= capture_length_o;
                    REG_CAPTURE_READ_INDEX: bus.rdata <= capture_read_index_o;
                    REG_CAPTURE_DATA_CH1:
                        bus.rdata <= {{18{capture_data_ch1_i[13]}}, capture_data_ch1_i};
                    REG_CAPTURE_DATA_CH2:
                        bus.rdata <= {{18{capture_data_ch2_i[13]}}, capture_data_ch2_i};
                    REG_CAPTURE_DATA_CH3:
                        bus.rdata <= {{18{capture_data_ch3_i[13]}}, capture_data_ch3_i};
                    REG_CAPTURE_DATA_CH4:
                        bus.rdata <= {{18{capture_data_ch4_i[13]}}, capture_data_ch4_i};
                    REG_ACQ_STATE: bus.rdata <= acq_state_w;
                    REG_EVENT_SEQUENCE: bus.rdata <= event_sequence_w;
                    REG_EVENT_OUT2: bus.rdata <= event_out2_w;
                    REG_EVENT_ERROR: bus.rdata <= event_error_w;
                    REG_EVENT_CONFIG_GENERATION:
                        bus.rdata <= event_config_generation_w;
                    REG_EVENT_INFO: bus.rdata <= event_info_w;
                    REG_EVENT_TIMESTAMP_LO: bus.rdata <= event_timestamp_lo_w;
                    REG_EVENT_TIMESTAMP_HI: bus.rdata <= event_timestamp_hi_w;
                    REG_ACTIVE_TARGET_OUT2:
                        bus.rdata <= {{18{active_target_out2_w[13]}}, active_target_out2_w};
                    REG_ACTIVE_ERROR_SETPOINT:
                        bus.rdata <= {{18{active_error_setpoint_w[13]}}, active_error_setpoint_w};
                    REG_ACTIVE_WINDOW: bus.rdata <= {18'd0, active_window_w};
                    REG_ACTIVE_REQUIREMENTS: bus.rdata <= active_requirements_w;
                    REG_ACTIVE_CORRECTION_LIMIT:
                        bus.rdata <= {18'd0, active_correction_limit_w};
                    REG_ACTIVE_ABSOLUTE_LIMIT:
                        bus.rdata <= {18'd0, active_absolute_limit_w};
                    REG_FAULT_DETAIL: bus.rdata <= fault_detail_w;
                    default: bus.rdata <= 32'd0;
                endcase
            end
        end
    end

endmodule


module deterministic_lock_acquisition (
    input  logic               clk_i,
    input  logic               rstn_i,
    input  logic        [31:0] mode_i,
    input  logic               enable_i,
    input  logic               saturated_i,
    input  logic signed [13:0] out2_i,
    input  logic signed [13:0] error_i,
    input  logic        [31:0] shadow_target_out2_i,
    input  logic        [31:0] shadow_error_setpoint_i,
    input  logic        [31:0] shadow_window_i,
    input  logic        [31:0] shadow_requirements_i,
    input  logic        [31:0] shadow_correction_limit_i,
    input  logic        [31:0] shadow_absolute_limit_i,
    input  logic        [31:0] shadow_generation_i,
    input  logic         [6:0] shadow_written_mask_i,
    input  logic               arm_pulse_i,
    input  logic               abort_pulse_i,
    input  logic               clear_event_pulse_i,
    input  logic               command_reject_pulse_i,
    input  logic               apply_p_pulse_i,
    input  logic signed [13:0] apply_p_kp_i,
    output logic               trigger_o,
    output logic               fault_immediate_o,
    output logic               arm_accepted_o,
    output logic        [31:0] config_validation_o,
    output logic        [31:0] state_readback_o,
    output logic signed [13:0] active_target_out2_o,
    output logic signed [13:0] active_error_setpoint_o,
    output logic        [13:0] active_window_o,
    output logic        [31:0] active_requirements_o,
    output logic        [13:0] active_correction_limit_o,
    output logic        [13:0] active_absolute_limit_o,
    output logic        [31:0] event_sequence_o,
    output logic        [31:0] event_out2_o,
    output logic        [31:0] event_error_o,
    output logic        [31:0] event_config_generation_o,
    output logic        [31:0] event_info_o,
    output logic        [31:0] event_timestamp_lo_o,
    output logic        [31:0] event_timestamp_hi_o,
    output logic        [31:0] fault_detail_o
);

    localparam logic [31:0] MODE_SAFE   = 32'd0;
    localparam logic [31:0] MODE_SCAN   = 32'd1;
    localparam logic [31:0] MODE_P_LOCK = 32'd3;

    localparam logic [2:0] STATE_SAFE            = 3'd0;
    localparam logic [2:0] STATE_SCAN            = 3'd1;
    localparam logic [2:0] STATE_ARMED           = 3'd2;
    localparam logic [2:0] STATE_TRIGGER_CAPTURE = 3'd3;
    localparam logic [2:0] STATE_P_LOCK_KP0      = 3'd4;
    localparam logic [2:0] STATE_P_LOCK_ACTIVE   = 3'd5;
    localparam logic [2:0] STATE_FAULT           = 3'd6;

    localparam logic [1:0] SCAN_DIR_RISING  = 2'd1;
    localparam logic [1:0] SCAN_DIR_FALLING = 2'd2;
    localparam logic [1:0] ERROR_DIR_NEG_TO_POS = 2'd1;
    localparam logic [1:0] ERROR_DIR_POS_TO_NEG = 2'd2;

    localparam logic [2:0] EVENT_NONE             = 3'd0;
    localparam logic [2:0] EVENT_ARMED            = 3'd1;
    localparam logic [2:0] EVENT_TRIGGERED        = 3'd2;
    localparam logic [2:0] EVENT_ABORTED          = 3'd3;
    localparam logic [2:0] EVENT_CONFIG_REJECTED  = 3'd4;
    localparam logic [2:0] EVENT_COMMAND_REJECTED = 3'd5;
    localparam logic [2:0] EVENT_FAULT             = 3'd6;

    localparam logic [15:0] REJECT_MISSING_FIELD = 16'h0001;
    localparam logic [15:0] REJECT_SIGNED_FIELD  = 16'h0002;
    localparam logic [15:0] REJECT_DIRECTION     = 16'h0004;
    localparam logic [15:0] REJECT_WINDOW        = 16'h0008;
    localparam logic [15:0] REJECT_LIMITS        = 16'h0010;
    localparam logic [15:0] REJECT_TARGET_RANGE  = 16'h0020;
    localparam logic [15:0] REJECT_STATE         = 16'h0040;
    localparam logic [15:0] REJECT_SATURATION    = 16'h0080;
    localparam logic [15:0] REJECT_COMMAND       = 16'h0100;
    localparam logic [15:0] FAULT_RUNTIME_SAFETY = 16'h0001;

    logic [2:0] state_q;
    logic active_config_valid_q;
    logic signed [13:0] previous_error_q;
    logic previous_error_valid_q;
    logic signed [13:0] previous_out2_q;
    logic [1:0] scan_direction_q;
    logic scan_direction_valid_q;
    logic [63:0] cycle_counter_q;
    logic [2:0] event_type_q;
    logic event_valid_q;
    logic [1:0] event_scan_direction_q;
    logic [1:0] event_error_direction_q;
    logic [15:0] reject_code_q;
    logic [15:0] fault_code_q;

    logic fields_complete_w;
    logic signed_fields_valid_w;
    logic directions_valid_w;
    logic window_valid_w;
    logic limits_valid_w;
    logic target_range_valid_w;
    logic state_ready_w;
    logic config_valid_w;
    logic [15:0] config_reject_code_w;

    logic signed [15:0] shadow_target_ext_w;
    logic signed [15:0] shadow_window_ext_w;
    logic signed [15:0] shadow_target_low_w;
    logic signed [15:0] shadow_target_high_w;
    logic signed [15:0] shadow_absolute_ext_w;

    logic [1:0] scan_direction_now_w;
    logic scan_direction_now_valid_w;
    logic signed [15:0] active_delta_w;
    logic signed [15:0] active_delta_abs_w;
    logic inside_window_w;
    logic neg_to_pos_w;
    logic pos_to_neg_w;
    logic required_crossing_w;
    logic direction_match_w;

    always_comb begin
        fields_complete_w = (shadow_written_mask_i == 7'h7F);
        signed_fields_valid_w =
            (shadow_target_out2_i[31:14] == {18{shadow_target_out2_i[13]}}) &&
            (shadow_error_setpoint_i[31:14] == {18{shadow_error_setpoint_i[13]}});
        directions_valid_w =
            (shadow_requirements_i[31:5] == 27'd0) &&
            ((shadow_requirements_i[1:0] == SCAN_DIR_RISING) ||
             (shadow_requirements_i[1:0] == SCAN_DIR_FALLING)) &&
            ((shadow_requirements_i[3:2] == ERROR_DIR_NEG_TO_POS) ||
             (shadow_requirements_i[3:2] == ERROR_DIR_POS_TO_NEG));
        window_valid_w =
            (shadow_window_i[31:14] == 18'd0) &&
            (shadow_window_i[13:0] != 14'd0) &&
            (shadow_window_i[13:0] <= 14'd8191);
        limits_valid_w =
            (shadow_correction_limit_i[31:14] == 18'd0) &&
            (shadow_absolute_limit_i[31:14] == 18'd0) &&
            (shadow_correction_limit_i[13:0] <= shadow_absolute_limit_i[13:0]) &&
            (shadow_absolute_limit_i[13:0] <= 14'd8191);

        shadow_target_ext_w = {{2{shadow_target_out2_i[13]}}, shadow_target_out2_i[13:0]};
        shadow_window_ext_w = {2'd0, shadow_window_i[13:0]};
        shadow_target_low_w = shadow_target_ext_w - shadow_window_ext_w;
        shadow_target_high_w = shadow_target_ext_w + shadow_window_ext_w;
        shadow_absolute_ext_w = {2'd0, shadow_absolute_limit_i[13:0]};
        target_range_valid_w =
            (shadow_target_low_w >= -16'sd8191) &&
            (shadow_target_high_w <= 16'sd8191) &&
            (shadow_target_low_w >= -shadow_absolute_ext_w) &&
            (shadow_target_high_w <= shadow_absolute_ext_w);
        state_ready_w = (state_q == STATE_SCAN) && enable_i &&
                        (mode_i == MODE_SCAN) && !saturated_i && (fault_code_q == 16'd0);
        config_valid_w = fields_complete_w && signed_fields_valid_w &&
                         directions_valid_w && window_valid_w && limits_valid_w &&
                         target_range_valid_w && state_ready_w;

        config_reject_code_w = 16'd0;
        if (!fields_complete_w)
            config_reject_code_w = config_reject_code_w | REJECT_MISSING_FIELD;
        if (!signed_fields_valid_w)
            config_reject_code_w = config_reject_code_w | REJECT_SIGNED_FIELD;
        if (!directions_valid_w)
            config_reject_code_w = config_reject_code_w | REJECT_DIRECTION;
        if (!window_valid_w)
            config_reject_code_w = config_reject_code_w | REJECT_WINDOW;
        if (!limits_valid_w)
            config_reject_code_w = config_reject_code_w | REJECT_LIMITS;
        if (!target_range_valid_w)
            config_reject_code_w = config_reject_code_w | REJECT_TARGET_RANGE;
        if ((state_q != STATE_SCAN) || !enable_i || (mode_i != MODE_SCAN))
            config_reject_code_w = config_reject_code_w | REJECT_STATE;
        if (saturated_i)
            config_reject_code_w = config_reject_code_w | REJECT_SATURATION;
    end

    always_comb begin
        if (out2_i > previous_out2_q) begin
            scan_direction_now_w = SCAN_DIR_RISING;
            scan_direction_now_valid_w = 1'b1;
        end else if (out2_i < previous_out2_q) begin
            scan_direction_now_w = SCAN_DIR_FALLING;
            scan_direction_now_valid_w = 1'b1;
        end else begin
            scan_direction_now_w = scan_direction_q;
            scan_direction_now_valid_w = scan_direction_valid_q;
        end

        active_delta_w = {{2{out2_i[13]}}, out2_i} -
                         {{2{active_target_out2_o[13]}}, active_target_out2_o};
        if (active_delta_w < 16'sd0)
            active_delta_abs_w = -active_delta_w;
        else
            active_delta_abs_w = active_delta_w;
        inside_window_w = active_delta_abs_w <= $signed({2'd0, active_window_o});
        neg_to_pos_w = (previous_error_q < active_error_setpoint_o) &&
                       (error_i >= active_error_setpoint_o);
        pos_to_neg_w = (previous_error_q > active_error_setpoint_o) &&
                       (error_i <= active_error_setpoint_o);
        required_crossing_w =
            (active_requirements_o[3:2] == ERROR_DIR_NEG_TO_POS) ? neg_to_pos_w :
            (active_requirements_o[3:2] == ERROR_DIR_POS_TO_NEG) ? pos_to_neg_w :
            1'b0;
        direction_match_w = scan_direction_now_valid_w &&
                            (scan_direction_now_w == active_requirements_o[1:0]);
    end

    assign fault_immediate_o = (state_q == STATE_ARMED) &&
                               (saturated_i || !enable_i || (mode_i != MODE_SCAN) ||
                                !active_config_valid_q);
    assign trigger_o = (state_q == STATE_ARMED) &&
                       previous_error_valid_q &&
                       active_config_valid_q &&
                       !abort_pulse_i &&
                       !fault_immediate_o &&
                       direction_match_w &&
                       inside_window_w &&
                       required_crossing_w;
    assign arm_accepted_o = arm_pulse_i && config_valid_w;

    always_comb begin
        config_validation_o = 32'd0;
        config_validation_o[0] = fields_complete_w;
        config_validation_o[1] = signed_fields_valid_w;
        config_validation_o[2] = directions_valid_w;
        config_validation_o[3] = window_valid_w;
        config_validation_o[4] = limits_valid_w;
        config_validation_o[5] = target_range_valid_w;
        config_validation_o[6] = state_ready_w;
        config_validation_o[7] = config_valid_w;
        config_validation_o[14:8] = shadow_written_mask_i;
        config_validation_o[15] = 1'b1; // Host owns the user-approved PZT safe range.

        state_readback_o = 32'd0;
        state_readback_o[2:0] = state_q;
        state_readback_o[8] = event_valid_q;
        state_readback_o[9] = (state_q == STATE_ARMED);
        state_readback_o[10] = (state_q == STATE_P_LOCK_KP0) ||
                               (state_q == STATE_P_LOCK_ACTIVE);
        state_readback_o[11] = (state_q == STATE_FAULT);
        state_readback_o[12] = active_config_valid_q;
        state_readback_o[13] = scan_direction_now_valid_w;
        state_readback_o[15:14] = scan_direction_now_w;

        event_info_o = 32'd0;
        event_info_o[0] = event_valid_q;
        event_info_o[3:1] = event_type_q;
        event_info_o[5:4] = event_scan_direction_q;
        event_info_o[7:6] = event_error_direction_q;
        event_info_o[15:8] = reject_code_q[7:0];
        event_info_o[23:16] = fault_code_q[7:0];
        fault_detail_o = {fault_code_q, reject_code_q};
    end

    always_ff @(posedge clk_i) begin
        if (!rstn_i) begin
            state_q <= STATE_SAFE;
            active_config_valid_q <= 1'b0;
            active_target_out2_o <= 14'sd0;
            active_error_setpoint_o <= 14'sd0;
            active_window_o <= 14'd0;
            active_requirements_o <= 32'd0;
            active_correction_limit_o <= 14'd0;
            active_absolute_limit_o <= 14'd0;
            previous_error_q <= 14'sd0;
            previous_error_valid_q <= 1'b0;
            previous_out2_q <= 14'sd0;
            scan_direction_q <= SCAN_DIR_RISING;
            scan_direction_valid_q <= 1'b0;
            cycle_counter_q <= 64'd0;
            event_sequence_o <= 32'd0;
            event_out2_o <= 32'd0;
            event_error_o <= 32'd0;
            event_config_generation_o <= 32'd0;
            event_timestamp_lo_o <= 32'd0;
            event_timestamp_hi_o <= 32'd0;
            event_type_q <= EVENT_NONE;
            event_valid_q <= 1'b0;
            event_scan_direction_q <= 2'd0;
            event_error_direction_q <= 2'd0;
            reject_code_q <= 16'd0;
            fault_code_q <= 16'd0;
        end else begin
            cycle_counter_q <= cycle_counter_q + 64'd1;
            previous_out2_q <= out2_i;
            if (out2_i != previous_out2_q) begin
                scan_direction_q <= scan_direction_now_w;
                scan_direction_valid_q <= 1'b1;
            end

            if (clear_event_pulse_i) begin
                event_valid_q <= 1'b0;
                event_type_q <= EVENT_NONE;
                event_scan_direction_q <= 2'd0;
                event_error_direction_q <= 2'd0;
                reject_code_q <= 16'd0;
                if (state_q != STATE_FAULT)
                    fault_code_q <= 16'd0;
            end

            if (abort_pulse_i) begin
                state_q <= STATE_SAFE;
                active_config_valid_q <= 1'b0;
                previous_error_valid_q <= 1'b0;
                event_sequence_o <= event_sequence_o + 32'd1;
                event_type_q <= EVENT_ABORTED;
                event_valid_q <= 1'b1;
                event_out2_o <= {{18{out2_i[13]}}, out2_i};
                event_error_o <= {{18{error_i[13]}}, error_i};
                event_config_generation_o <= event_config_generation_o;
                event_scan_direction_q <= scan_direction_now_w;
                event_error_direction_q <= 2'd0;
                event_timestamp_lo_o <= cycle_counter_q[31:0];
                event_timestamp_hi_o <= cycle_counter_q[63:32];
            end else if (fault_immediate_o) begin
                state_q <= STATE_FAULT;
                active_config_valid_q <= 1'b0;
                previous_error_valid_q <= 1'b0;
                fault_code_q <= FAULT_RUNTIME_SAFETY;
                event_sequence_o <= event_sequence_o + 32'd1;
                event_type_q <= EVENT_FAULT;
                event_valid_q <= 1'b1;
                event_out2_o <= {{18{out2_i[13]}}, out2_i};
                event_error_o <= {{18{error_i[13]}}, error_i};
                event_config_generation_o <= event_config_generation_o;
                event_scan_direction_q <= scan_direction_now_w;
                event_error_direction_q <= active_requirements_o[3:2];
                event_timestamp_lo_o <= cycle_counter_q[31:0];
                event_timestamp_hi_o <= cycle_counter_q[63:32];
            end else begin
                unique case (state_q)
                    STATE_SAFE: begin
                        active_config_valid_q <= 1'b0;
                        previous_error_valid_q <= 1'b0;
                        if (enable_i && (mode_i == MODE_SCAN) && (fault_code_q == 16'd0))
                            state_q <= STATE_SCAN;
                    end
                    STATE_SCAN: begin
                        previous_error_valid_q <= 1'b0;
                        if (!enable_i || (mode_i == MODE_SAFE)) begin
                            state_q <= STATE_SAFE;
                            active_config_valid_q <= 1'b0;
                        end else if (mode_i == MODE_P_LOCK) begin
                            if (apply_p_kp_i == 14'sd0)
                                state_q <= STATE_P_LOCK_KP0;
                            else
                                state_q <= STATE_P_LOCK_ACTIVE;
                        end else if (command_reject_pulse_i) begin
                            reject_code_q <= REJECT_COMMAND;
                            event_sequence_o <= event_sequence_o + 32'd1;
                            event_type_q <= EVENT_COMMAND_REJECTED;
                            event_valid_q <= 1'b1;
                            event_timestamp_lo_o <= cycle_counter_q[31:0];
                            event_timestamp_hi_o <= cycle_counter_q[63:32];
                        end else if (arm_pulse_i) begin
                            if (config_valid_w) begin
                                active_target_out2_o <= shadow_target_out2_i[13:0];
                                active_error_setpoint_o <= shadow_error_setpoint_i[13:0];
                                active_window_o <= shadow_window_i[13:0];
                                active_requirements_o <= shadow_requirements_i;
                                active_correction_limit_o <= shadow_correction_limit_i[13:0];
                                active_absolute_limit_o <= shadow_absolute_limit_i[13:0];
                                active_config_valid_q <= 1'b1;
                                previous_error_q <= error_i;
                                previous_error_valid_q <= 1'b0;
                                state_q <= STATE_ARMED;
                                reject_code_q <= 16'd0;
                                event_sequence_o <= event_sequence_o + 32'd1;
                                event_type_q <= EVENT_ARMED;
                                event_valid_q <= 1'b1;
                                event_out2_o <= {{18{out2_i[13]}}, out2_i};
                                event_error_o <= {{18{error_i[13]}}, error_i};
                                event_config_generation_o <= shadow_generation_i;
                                event_scan_direction_q <= scan_direction_now_w;
                                event_error_direction_q <= shadow_requirements_i[3:2];
                                event_timestamp_lo_o <= cycle_counter_q[31:0];
                                event_timestamp_hi_o <= cycle_counter_q[63:32];
                            end else begin
                                reject_code_q <= config_reject_code_w;
                                event_sequence_o <= event_sequence_o + 32'd1;
                                event_type_q <= EVENT_CONFIG_REJECTED;
                                event_valid_q <= 1'b1;
                                event_out2_o <= {{18{out2_i[13]}}, out2_i};
                                event_error_o <= {{18{error_i[13]}}, error_i};
                                event_config_generation_o <= shadow_generation_i;
                                event_scan_direction_q <= scan_direction_now_w;
                                event_error_direction_q <= shadow_requirements_i[3:2];
                                event_timestamp_lo_o <= cycle_counter_q[31:0];
                                event_timestamp_hi_o <= cycle_counter_q[63:32];
                            end
                        end
                    end
                    STATE_ARMED: begin
                        if (command_reject_pulse_i) begin
                            reject_code_q <= REJECT_COMMAND;
                            event_sequence_o <= event_sequence_o + 32'd1;
                            event_type_q <= EVENT_COMMAND_REJECTED;
                            event_valid_q <= 1'b1;
                            event_timestamp_lo_o <= cycle_counter_q[31:0];
                            event_timestamp_hi_o <= cycle_counter_q[63:32];
                        end else if (arm_pulse_i) begin
                            reject_code_q <= REJECT_STATE;
                            event_sequence_o <= event_sequence_o + 32'd1;
                            event_type_q <= EVENT_CONFIG_REJECTED;
                            event_valid_q <= 1'b1;
                            event_out2_o <= {{18{out2_i[13]}}, out2_i};
                            event_error_o <= {{18{error_i[13]}}, error_i};
                            event_config_generation_o <= event_config_generation_o;
                            event_scan_direction_q <= scan_direction_now_w;
                            event_error_direction_q <= active_requirements_o[3:2];
                            event_timestamp_lo_o <= cycle_counter_q[31:0];
                            event_timestamp_hi_o <= cycle_counter_q[63:32];
                        end
                        if (!previous_error_valid_q) begin
                            previous_error_q <= error_i;
                            previous_error_valid_q <= 1'b1;
                        end else if (trigger_o) begin
                            previous_error_q <= error_i;
                            previous_error_valid_q <= 1'b0;
                            state_q <= STATE_TRIGGER_CAPTURE;
                            event_sequence_o <= event_sequence_o + 32'd1;
                            event_type_q <= EVENT_TRIGGERED;
                            event_valid_q <= 1'b1;
                            event_out2_o <= {{18{out2_i[13]}}, out2_i};
                            event_error_o <= {{18{error_i[13]}}, error_i};
                            event_config_generation_o <= event_config_generation_o;
                            event_scan_direction_q <= scan_direction_now_w;
                            event_error_direction_q <= active_requirements_o[3:2];
                            event_timestamp_lo_o <= cycle_counter_q[31:0];
                            event_timestamp_hi_o <= cycle_counter_q[63:32];
                        end else begin
                            previous_error_q <= error_i;
                        end
                    end
                    STATE_TRIGGER_CAPTURE: state_q <= STATE_P_LOCK_KP0;
                    STATE_P_LOCK_KP0: begin
                        if (!enable_i || (mode_i == MODE_SAFE)) begin
                            state_q <= STATE_SAFE;
                            active_config_valid_q <= 1'b0;
                        end else if (apply_p_pulse_i && (apply_p_kp_i != 14'sd0)) begin
                            state_q <= STATE_P_LOCK_ACTIVE;
                        end
                    end
                    STATE_P_LOCK_ACTIVE: begin
                        if (!enable_i || (mode_i == MODE_SAFE)) begin
                            state_q <= STATE_SAFE;
                            active_config_valid_q <= 1'b0;
                        end else if (apply_p_pulse_i && (apply_p_kp_i == 14'sd0)) begin
                            state_q <= STATE_P_LOCK_KP0;
                        end
                    end
                    STATE_FAULT: begin
                        active_config_valid_q <= 1'b0;
                        previous_error_valid_q <= 1'b0;
                        if (!enable_i && (mode_i == MODE_SAFE) && !event_valid_q) begin
                            state_q <= STATE_SAFE;
                            fault_code_q <= 16'd0;
                        end
                    end
                    default: begin
                        state_q <= STATE_FAULT;
                        active_config_valid_q <= 1'b0;
                        fault_code_q <= FAULT_RUNTIME_SAFETY;
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
    input  logic signed [13:0] lock_correction_limit_i,
    input  logic               integral_reset_i,
    input  logic               acq_trigger_i,
    input  logic               acq_abort_i,
    input  logic               acq_fault_i,
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
    logic signed [13:0] s0_correction_limit;

    logic               s1_enable;
    logic        [31:0] s1_mode;
    logic signed [14:0] s1_signed_error;
    logic signed [13:0] s1_kp;
    logic signed [13:0] s1_lock_bias;
    logic signed [13:0] s1_lock_limit;
    logic signed [13:0] s1_correction_limit;

    logic               s2_enable;
    logic        [31:0] s2_mode;
    logic signed [28:0] s2_p_product;
    logic signed [13:0] s2_lock_bias;
    logic signed [13:0] s2_lock_limit;
    logic signed [13:0] s2_correction_limit;

    logic               s3_enable;
    logic        [31:0] s3_mode;
    logic signed [31:0] s3_p_term;
    logic signed [13:0] s3_lock_bias;
    logic signed [13:0] s3_lock_limit;
    logic signed [13:0] s3_correction_limit;

    logic               s4_enable;
    logic        [31:0] s4_mode;
    logic signed [31:0] s4_correction;
    logic               s4_correction_saturated;
    logic signed [13:0] s4_lock_bias;
    logic signed [13:0] s4_lock_limit;

    logic               s5_enable;
    logic        [31:0] s5_mode;
    logic signed [31:0] s5_raw;
    logic               s5_correction_saturated;
    logic signed [13:0] s5_lock_limit;

    logic signed [31:0] abs_limit_w;
    logic signed [31:0] correction_limit_abs_w;

    always_comb begin
        if (s5_lock_limit < 14'sd0)
            abs_limit_w = -$signed({{18{s5_lock_limit[13]}}, s5_lock_limit});
        else
            abs_limit_w = $signed({{18{s5_lock_limit[13]}}, s5_lock_limit});
        if (abs_limit_w > 32'sd8191)
            abs_limit_w = 32'sd8191;

        if (s3_correction_limit < 14'sd0)
            correction_limit_abs_w =
                -$signed({{18{s3_correction_limit[13]}}, s3_correction_limit});
        else
            correction_limit_abs_w =
                $signed({{18{s3_correction_limit[13]}}, s3_correction_limit});
        if (correction_limit_abs_w > 32'sd8191)
            correction_limit_abs_w = 32'sd8191;
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
            s0_correction_limit <= 14'sd128;
            s1_enable       <= 1'b0;
            s1_mode         <= MODE_SAFE;
            s1_signed_error <= 15'sd0;
            s1_kp           <= 14'sd0;
            s1_lock_bias    <= 14'sd0;
            s1_lock_limit   <= 14'sd8191;
            s1_correction_limit <= 14'sd128;
            s2_enable       <= 1'b0;
            s2_mode         <= MODE_SAFE;
            s2_p_product    <= 29'sd0;
            s2_lock_bias    <= 14'sd0;
            s2_lock_limit   <= 14'sd8191;
            s2_correction_limit <= 14'sd128;
            s3_enable       <= 1'b0;
            s3_mode         <= MODE_SAFE;
            s3_p_term       <= 32'sd0;
            s3_lock_bias    <= 14'sd0;
            s3_lock_limit   <= 14'sd8191;
            s3_correction_limit <= 14'sd128;
            s4_enable       <= 1'b0;
            s4_mode         <= MODE_SAFE;
            s4_correction   <= 32'sd0;
            s4_correction_saturated <= 1'b0;
            s4_lock_bias    <= 14'sd0;
            s4_lock_limit   <= 14'sd8191;
            s5_enable       <= 1'b0;
            s5_mode         <= MODE_SAFE;
            s5_raw          <= 32'sd0;
            s5_correction_saturated <= 1'b0;
            s5_lock_limit   <= 14'sd8191;
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
            s0_correction_limit <= lock_correction_limit_i;

            s1_enable       <= s0_enable;
            s1_mode         <= s0_mode;
            s1_signed_error <= s0_polarity
                             ? -$signed({s0_error[13], s0_error})
                             :  $signed({s0_error[13], s0_error});
            s1_kp           <= s0_kp;
            s1_lock_bias    <= s0_lock_bias;
            s1_lock_limit   <= s0_lock_limit;
            s1_correction_limit <= s0_correction_limit;

            s2_enable     <= s1_enable;
            s2_mode       <= s1_mode;
            s2_p_product  <= $signed({{14{s1_signed_error[14]}}, s1_signed_error}) *
                             $signed({{15{s1_kp[13]}}, s1_kp});
            s2_lock_bias  <= s1_lock_bias;
            s2_lock_limit <= s1_lock_limit;
            s2_correction_limit <= s1_correction_limit;

            s3_enable     <= s2_enable;
            s3_mode       <= s2_mode;
            s3_p_term     <= $signed(s2_p_product) >>> 8;
            s3_lock_bias  <= s2_lock_bias;
            s3_lock_limit <= s2_lock_limit;
            s3_correction_limit <= s2_correction_limit;

            s4_enable     <= s3_enable;
            s4_mode       <= s3_mode;
            if (s3_p_term > correction_limit_abs_w) begin
                s4_correction <= correction_limit_abs_w;
                s4_correction_saturated <= 1'b1;
            end else if (s3_p_term < -correction_limit_abs_w) begin
                s4_correction <= -correction_limit_abs_w;
                s4_correction_saturated <= 1'b1;
            end else begin
                s4_correction <= s3_p_term;
                s4_correction_saturated <= 1'b0;
            end
            s4_lock_bias  <= s3_lock_bias;
            s4_lock_limit <= s3_lock_limit;

            s5_enable     <= s4_enable;
            s5_mode       <= s4_mode;
            s5_raw        <= $signed({{18{s4_lock_bias[13]}}, s4_lock_bias}) +
                             s4_correction;
            s5_correction_saturated <= s4_correction_saturated;
            s5_lock_limit <= s4_lock_limit;

            if (!enable_i || (mode_i == MODE_SAFE) || acq_abort_i || acq_fault_i) begin
                control_o   <= 14'sd0;
                saturated_o <= 1'b0;
            end else if (acq_trigger_i) begin
                control_o   <= control_o;
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
                        if (s5_enable &&
                            ((s5_mode == MODE_P_LOCK) || (s5_mode == MODE_PI_LOCK))) begin
                            if (s5_raw > abs_limit_w) begin
                                control_o   <= abs_limit_w[13:0];
                                saturated_o <= 1'b1;
                            end else if (s5_raw < -abs_limit_w) begin
                                control_o   <= -abs_limit_w[13:0];
                                saturated_o <= 1'b1;
                            end else begin
                                control_o   <= s5_raw[13:0];
                                saturated_o <= s5_correction_saturated;
                            end
                        end else begin
                            control_o   <= lock_bias_i;
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
