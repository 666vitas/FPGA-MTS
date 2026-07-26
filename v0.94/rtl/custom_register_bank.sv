`timescale 1ns/1ps
`include "simple_lock_acquisition.sv"

module custom_register_bank #(
    // Standalone register-bank simulations retain the full D1 implementation.
    // The production red_pitaya_top explicitly selects the timing-light SIMPLE
    // implementation.
    parameter integer LOCK_ACQ_IMPL = 2
) (
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
    output logic signed [13:0] kp_effective_o,
    output logic               polarity_o,
    output logic signed [13:0] lock_bias_o,
    output logic signed [13:0] lock_limit_o,
    output logic signed [13:0] lock_correction_limit_o,
    output logic signed [13:0] error_setpoint_o,
    output logic signed [13:0] ki_o,
    output logic               integral_reset_o,
    output logic        [15:0] servo_update_div_o,
    output logic        [13:0] out2_slew_limit_o,
    output logic               acq_trigger_o,
    output logic               acq_hold_o,
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

    localparam integer LOCK_ACQ_NONE   = 0;
    localparam integer LOCK_ACQ_SIMPLE = 1;
    localparam integer LOCK_ACQ_D1     = 2;

    localparam logic [31:0] REG_MAGIC_VALUE = 32'h4D545330;
    localparam logic [31:0] REG_VERSION_VALUE =
        (LOCK_ACQ_IMPL == LOCK_ACQ_SIMPLE) ? 32'h00030200 :
        (LOCK_ACQ_IMPL == LOCK_ACQ_D1)     ? 32'h00030100 :
                                             32'h00030000;

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
    localparam logic [6:0] REG_L1_CAPABILITY            = 7'h39;
    localparam logic [6:0] REG_CROSSING_CONFIG          = 7'h3A;
    localparam logic [6:0] REG_KP_ACQUIRE_TARGET        = 7'h3B;
    localparam logic [6:0] REG_KP_RAMP_CONFIG           = 7'h3C;
    localparam logic [6:0] REG_ACQUIRE_TIMEOUT          = 7'h3D;
    localparam logic [6:0] REG_SERVO_CONFIG             = 7'h3E;
    localparam logic [6:0] REG_SUPERVISOR_CONFIG0       = 7'h3F;
    localparam logic [6:0] REG_SUPERVISOR_CONFIG1       = 7'h40;
    localparam logic [6:0] REG_EVENT_LOCK_ERROR         = 7'h41;
    localparam logic [6:0] REG_VALIDATE_EVENT_COUNT     = 7'h42;
    localparam logic [6:0] REG_KP_EFFECTIVE             = 7'h43;
    localparam logic [6:0] REG_SUPERVISOR_METRICS       = 7'h44;

    localparam logic [31:0] MODE_SAFE   = 32'd0;
    localparam logic [31:0] MODE_SCAN   = 32'd1;
    localparam logic [31:0] MODE_HOLD   = 32'd2;
    localparam logic [31:0] MODE_P_LOCK = 32'd3;

    logic [6:0] reg_addr_w;
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
    logic [31:0] crossing_config_q;
    logic signed [13:0] kp_acquire_target_q;
    logic [31:0] kp_ramp_config_q;
    logic [31:0] acquire_timeout_q;
    logic [31:0] servo_config_q;
    logic [31:0] supervisor_config0_q;
    logic [31:0] supervisor_config1_q;

    logic command_write_w;
    logic arm_pulse_w;
    logic validate_pulse_w;
    logic abort_pulse_w;
    logic clear_event_pulse_w;
    logic command_reject_pulse_w;
    logic apply_p_pulse_w;
    logic write_cycle_active_q;
    logic arm_command_q;
    logic validate_command_q;
    logic abort_command_q;
    logic clear_event_command_q;
    logic invalid_command_q;
    logic apply_p_command_q;
    logic signed [13:0] apply_p_kp_q;

    // These signals are registers only in the D1 generate branch. In SIMPLE
    // they are compile-time constants, so the seven snapshot pulse trees do
    // not exist in the production netlist.
    (* max_fanout = 64 *) logic arm_snapshot_target_values_en_q;
    (* max_fanout = 64 *) logic arm_snapshot_window_en_q;
    (* max_fanout = 64 *) logic arm_snapshot_limits_en_q;
    (* max_fanout = 64 *) logic arm_snapshot_metadata_en_q;
    (* max_fanout = 64 *) logic arm_snapshot_mask_en_q;
    (* max_fanout = 64 *) logic arm_snapshot_runtime_sample_en_q;
    (* max_fanout = 64 *) logic arm_snapshot_runtime_timestamp_en_q;

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
    logic signed [13:0] trigger_out2_sample_w;
    logic signed [13:0] trigger_error_sample_w;
    logic signed [14:0] trigger_lock_error_sample_w;
    logic signed [13:0] acq_kp_effective_w;
    logic [31:0] validate_event_count_w;
    logic [31:0] supervisor_metrics_w;
    logic signed [31:0] event_lock_error_w;

    assign reg_addr_w = bus.addr[2+:7];
    assign sys_en_w = bus.wen | bus.ren;
    assign enabled_status_w = enable_o && (mode_o != MODE_SAFE);

    assign command_write_w = bus.wen && (reg_addr_w == REG_ACQ_COMMAND);
    assign arm_pulse_w = command_write_w && (bus.wdata == 32'h0000_0001);
    assign abort_pulse_w = command_write_w && (bus.wdata == 32'h0000_0002);
    assign clear_event_pulse_w = command_write_w && (bus.wdata == 32'h0000_0004);
    assign validate_pulse_w = command_write_w && (bus.wdata == 32'h0000_0008);
    assign command_reject_pulse_w = command_write_w &&
                                    (bus.wdata != 32'h0000_0001) &&
                                    (bus.wdata != 32'h0000_0002) &&
                                    (bus.wdata != 32'h0000_0004) &&
                                    (bus.wdata != 32'h0000_0008);
    assign apply_p_pulse_w = bus.wen && (reg_addr_w == REG_KP);
    assign acq_abort_o = abort_command_q;
    assign kp_effective_o =
        (LOCK_ACQ_IMPL == LOCK_ACQ_SIMPLE) ? acq_kp_effective_w : kp_o;

    // Registered W1P command mailbox. write_cycle_active_q suppresses a
    // repeated command if the sys_bus master holds wen until the registered
    // acknowledge returns.
    always_ff @(posedge clk_i) begin
        if (!rstn_i) begin
            write_cycle_active_q                 <= 1'b0;
            arm_command_q                        <= 1'b0;
            validate_command_q                   <= 1'b0;
            abort_command_q                      <= 1'b0;
            clear_event_command_q                <= 1'b0;
            invalid_command_q                    <= 1'b0;
            apply_p_command_q                    <= 1'b0;
            apply_p_kp_q                         <= 14'sd0;
        end else begin
            write_cycle_active_q <= bus.wen;
            arm_command_q <= 1'b0;
            validate_command_q <= 1'b0;
            abort_command_q <= 1'b0;
            clear_event_command_q <= 1'b0;
            invalid_command_q <= 1'b0;
            apply_p_command_q <= 1'b0;

            if (!write_cycle_active_q) begin
                arm_command_q <= arm_pulse_w;
                validate_command_q <= validate_pulse_w;
                abort_command_q <= abort_pulse_w;
                clear_event_command_q <= clear_event_pulse_w;
                invalid_command_q <= command_reject_pulse_w;
                apply_p_command_q <= apply_p_pulse_w;

                if (apply_p_pulse_w)
                    apply_p_kp_q <= bus.wdata[13:0];
            end
        end
    end

    generate
        if (LOCK_ACQ_IMPL == LOCK_ACQ_D1) begin : g_lock_acq_d1
            assign trigger_lock_error_sample_w =
                $signed({trigger_error_sample_w[13], trigger_error_sample_w}) -
                $signed({active_error_setpoint_w[13], active_error_setpoint_w});
            assign acq_kp_effective_w = kp_o;
            assign validate_event_count_w = 32'd0;
            assign supervisor_metrics_w = 32'd0;
            assign event_lock_error_w =
                {{18{event_error_w[13]}}, event_error_w[13:0]};
            // D1 alone owns the snapshot start replicas. They preserve the
            // existing atomic D1 transaction and its legacy test hierarchy.
            always_ff @(posedge clk_i) begin
                if (!rstn_i) begin
                    arm_snapshot_target_values_en_q     <= 1'b0;
                    arm_snapshot_window_en_q            <= 1'b0;
                    arm_snapshot_limits_en_q            <= 1'b0;
                    arm_snapshot_metadata_en_q          <= 1'b0;
                    arm_snapshot_mask_en_q              <= 1'b0;
                    arm_snapshot_runtime_sample_en_q    <= 1'b0;
                    arm_snapshot_runtime_timestamp_en_q <= 1'b0;
                end else begin
                    arm_snapshot_target_values_en_q     <= 1'b0;
                    arm_snapshot_window_en_q            <= 1'b0;
                    arm_snapshot_limits_en_q            <= 1'b0;
                    arm_snapshot_metadata_en_q          <= 1'b0;
                    arm_snapshot_mask_en_q              <= 1'b0;
                    arm_snapshot_runtime_sample_en_q    <= 1'b0;
                    arm_snapshot_runtime_timestamp_en_q <= 1'b0;
                    if (!write_cycle_active_q && arm_pulse_w) begin
                        arm_snapshot_target_values_en_q     <= 1'b1;
                        arm_snapshot_window_en_q            <= 1'b1;
                        arm_snapshot_limits_en_q            <= 1'b1;
                        arm_snapshot_metadata_en_q          <= 1'b1;
                        arm_snapshot_mask_en_q              <= 1'b1;
                        arm_snapshot_runtime_sample_en_q    <= 1'b1;
                        arm_snapshot_runtime_timestamp_en_q <= 1'b1;
                    end
                end
            end

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
                .arm_pulse_i(arm_command_q),
                .arm_snapshot_target_values_en_i(arm_snapshot_target_values_en_q),
                .arm_snapshot_window_en_i(arm_snapshot_window_en_q),
                .arm_snapshot_limits_en_i(arm_snapshot_limits_en_q),
                .arm_snapshot_metadata_en_i(arm_snapshot_metadata_en_q),
                .arm_snapshot_mask_en_i(arm_snapshot_mask_en_q),
                .arm_snapshot_runtime_sample_en_i(arm_snapshot_runtime_sample_en_q),
                .arm_snapshot_runtime_timestamp_en_i(arm_snapshot_runtime_timestamp_en_q),
                .abort_pulse_i(abort_command_q),
                .clear_event_pulse_i(clear_event_command_q),
                .command_reject_pulse_i(invalid_command_q),
                .apply_p_pulse_i(apply_p_command_q),
                .apply_p_kp_i(apply_p_kp_q),
                .trigger_o(acq_trigger_o),
                .hold_o(acq_hold_o),
                .fault_immediate_o(acq_fault_o),
                .arm_accepted_o(arm_accepted_w),
                .trigger_out2_sample_o(trigger_out2_sample_w),
                .trigger_error_sample_o(trigger_error_sample_w),
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
        end else if (LOCK_ACQ_IMPL == LOCK_ACQ_SIMPLE) begin : g_lock_acq_simple
            assign arm_snapshot_target_values_en_q = 1'b0;
            assign arm_snapshot_window_en_q = 1'b0;
            assign arm_snapshot_limits_en_q = 1'b0;
            assign arm_snapshot_metadata_en_q = 1'b0;
            assign arm_snapshot_mask_en_q = 1'b0;
            assign arm_snapshot_runtime_sample_en_q = 1'b0;
            assign arm_snapshot_runtime_timestamp_en_q = 1'b0;

            simple_lock_acquisition i_simple_lock_acquisition (
                .clk_i(clk_i),
                .rstn_i(rstn_i),
                .mode_i(mode_o),
                .enable_i(enable_o),
                .saturated_i(saturated_i),
                .out2_i(out2_monitor_i),
                .error_i(error_monitor_i),
                .target_out2_i(target_out2_shadow_q),
                .target_error_setpoint_i(target_error_setpoint_shadow_q),
                .target_window_i(target_window_shadow_q),
                .target_requirements_i(target_requirements_shadow_q),
                .correction_limit_i(correction_limit_shadow_q),
                .absolute_limit_i(absolute_limit_shadow_q),
                .config_generation_i(config_generation_shadow_q),
                .config_written_mask_i(shadow_written_mask_q),
                .request_active_i(arm_command_q),
                .request_validate_i(validate_command_q),
                .abort_i(abort_command_q),
                .clear_event_i(clear_event_command_q),
                .crossing_hysteresis_i(crossing_config_q[13:0]),
                .crossing_samples_i(crossing_config_q[23:16]),
                .kp_target_i(kp_acquire_target_q),
                .kp_ramp_step_i(kp_ramp_config_q[13:0]),
                .kp_ramp_div_i(kp_ramp_config_q[31:16]),
                .acquire_timeout_i(acquire_timeout_q),
                .servo_update_div_i(servo_config_q[15:0]),
                .observe_shift_i(supervisor_config0_q[7:0]),
                .lock_confirm_windows_i(supervisor_config0_q[15:8]),
                .divergence_windows_i(supervisor_config0_q[23:16]),
                .error_mean_limit_i(supervisor_config1_q[13:0]),
                .error_abs_limit_i(supervisor_config1_q[29:16]),
                .trigger_o(acq_trigger_o),
                .hold_o(acq_hold_o),
                .fault_immediate_o(acq_fault_o),
                .request_accepted_o(arm_accepted_w),
                .trigger_out2_sample_o(trigger_out2_sample_w),
                .trigger_error_sample_o(trigger_error_sample_w),
                .trigger_lock_error_sample_o(trigger_lock_error_sample_w),
                .kp_effective_o(acq_kp_effective_w),
                .validate_event_count_o(validate_event_count_w),
                .supervisor_metrics_o(supervisor_metrics_w),
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
                .event_lock_error_o(event_lock_error_w),
                .event_config_generation_o(event_config_generation_w),
                .event_info_o(event_info_w),
                .event_timestamp_lo_o(event_timestamp_lo_w),
                .event_timestamp_hi_o(event_timestamp_hi_w),
                .fault_detail_o(fault_detail_w)
            );
        end else begin : g_lock_acq_none
            assign arm_snapshot_target_values_en_q = 1'b0;
            assign arm_snapshot_window_en_q = 1'b0;
            assign arm_snapshot_limits_en_q = 1'b0;
            assign arm_snapshot_metadata_en_q = 1'b0;
            assign arm_snapshot_mask_en_q = 1'b0;
            assign arm_snapshot_runtime_sample_en_q = 1'b0;
            assign arm_snapshot_runtime_timestamp_en_q = 1'b0;
            assign acq_trigger_o = 1'b0;
            assign acq_hold_o = 1'b0;
            assign acq_fault_o = 1'b0;
            assign arm_accepted_w = 1'b0;
            assign trigger_out2_sample_w = 14'sd0;
            assign trigger_error_sample_w = 14'sd0;
            assign trigger_lock_error_sample_w = 15'sd0;
            assign acq_kp_effective_w = kp_o;
            assign validate_event_count_w = 32'd0;
            assign supervisor_metrics_w = 32'd0;
            assign config_validation_w = 32'd0;
            assign acq_state_w = 32'd0;
            assign active_target_out2_w = 14'sd0;
            assign active_error_setpoint_w = 14'sd0;
            assign active_window_w = 14'd0;
            assign active_requirements_w = 32'd0;
            assign active_correction_limit_w = 14'd0;
            assign active_absolute_limit_w = 14'd0;
            assign event_sequence_w = 32'd0;
            assign event_out2_w = 32'd0;
            assign event_error_w = 32'd0;
            assign event_lock_error_w = 32'sd0;
            assign event_config_generation_w = 32'd0;
            assign event_info_w = 32'd0;
            assign event_timestamp_lo_w = 32'd0;
            assign event_timestamp_hi_w = 32'd0;
            assign fault_detail_w = 32'd0;
        end
    endgenerate

    // Acquisition fast-control registers are the only register group whose
    // clock enables depend on the real-time acquisition decisions.
    always_ff @(posedge clk_i) begin
        if (!rstn_i) begin
            mode_o                      <= MODE_SAFE;
            enable_o                    <= 1'b0;
            kp_o                        <= 14'sd0;
            ki_o                        <= 14'sd0;
            integral_reset_o            <= 1'b0;
            lock_bias_o                 <= 14'sd0;
            error_setpoint_o            <= 14'sd0;
            lock_limit_o                <= 14'sd8191;
            lock_correction_limit_o     <= 14'sd128;
        end else begin
            integral_reset_o <= 1'b0;

            if (acq_abort_o || acq_fault_o) begin
                mode_o           <= MODE_SAFE;
                enable_o         <= 1'b0;
                kp_o             <= 14'sd0;
                ki_o             <= 14'sd0;
                integral_reset_o <= 1'b1;
            end else if (acq_trigger_o) begin
                lock_bias_o       <= trigger_out2_sample_w;
                error_setpoint_o  <= active_error_setpoint_w;
                lock_correction_limit_o <= $signed({1'b0, active_correction_limit_w[12:0]});
                lock_limit_o      <= $signed({1'b0, active_absolute_limit_w[12:0]});
                ki_o              <= 14'sd0;
                integral_reset_o  <= 1'b1;
                mode_o            <= MODE_P_LOCK;
                enable_o          <= 1'b1;
                if (LOCK_ACQ_IMPL == LOCK_ACQ_D1)
                    kp_o <= 14'sd0;
            end else if (arm_accepted_w) begin
                if (LOCK_ACQ_IMPL == LOCK_ACQ_D1) begin
                    kp_o             <= 14'sd0;
                    ki_o             <= 14'sd0;
                    integral_reset_o <= 1'b1;
                end
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
                    REG_KP: kp_o <= bus.wdata[13:0];
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
                    default: begin
                    end
                endcase
            end
        end
    end

    // The controller sees only ARM-committed servo timing/slew values.  Later
    // sys_bus writes prepare the next transaction and cannot perturb a live
    // acquisition.
    always_ff @(posedge clk_i) begin
        if (!rstn_i) begin
            servo_update_div_o <= 16'd125;
            out2_slew_limit_o <= 14'd1;
        end else if ((LOCK_ACQ_IMPL == LOCK_ACQ_SIMPLE) && arm_accepted_w) begin
            servo_update_div_o <= servo_config_q[15:0];
            out2_slew_limit_o <= servo_config_q[29:16];
        end
    end

    // Shadow configuration is bus-owned. Acquisition activity must not enter
    // these registers' clock-enable or reset cones.
    always_ff @(posedge clk_i) begin
        if (!rstn_i) begin
            target_out2_shadow_q           <= 32'd0;
            target_error_setpoint_shadow_q <= 32'd0;
            target_window_shadow_q         <= 32'd0;
            target_requirements_shadow_q   <= 32'd0;
            correction_limit_shadow_q      <= 32'd0;
            absolute_limit_shadow_q        <= 32'd0;
            config_generation_shadow_q     <= 32'd0;
            shadow_written_mask_q          <= 7'd0;
        end else if (bus.wen) begin
            unique case (reg_addr_w)
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
                default: begin
                end
            endcase
        end
    end

    // Ordinary scan/hold configuration is bus-owned and independent of the
    // deterministic acquisition control path.
    always_ff @(posedge clk_i) begin
        if (!rstn_i) begin
            scan_offset_o     <= 14'sd6962;
            scan_amp_o        <= 14'sd410;
            scan_step_o       <= 14'sd1;
            scan_update_div_o <= 32'd1524;
            out2_limit_o      <= 14'sd8191;
            hold_value_o      <= 14'sd0;
            polarity_o        <= 1'b0;
        end else if (bus.wen) begin
            unique case (reg_addr_w)
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
                REG_POLARITY: polarity_o <= bus.wdata[0];
                default: begin
                end
            endcase
        end
    end

    // Capture configuration is bus-owned. capture_start_o remains a one-cycle
    // pulse even when unrelated bus writes occur.
    always_ff @(posedge clk_i) begin
        if (!rstn_i) begin
            capture_start_o      <= 1'b0;
            capture_decimation_o <= 32'd1024;
            capture_length_o     <= 32'd2048;
            capture_read_index_o <= 32'd0;
        end else begin
            capture_start_o <= 1'b0;
            if (bus.wen) begin
                unique case (reg_addr_w)
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

    // LOCK-MVP-L1 configuration is bus-owned and only snapshots into the
    // SIMPLE real-time acquisition block on a legal ARM transaction.
    always_ff @(posedge clk_i) begin
        if (!rstn_i) begin
            crossing_config_q <= {8'd0, 8'd3, 2'd0, 14'd4};
            kp_acquire_target_q <= 14'sd4;
            kp_ramp_config_q <= {16'd1, 2'd0, 14'd1};
            acquire_timeout_q <= 32'd12500000;
            servo_config_q <= {2'd0, 14'd1, 16'd125};
            supervisor_config0_q <= {8'd0, 8'd4, 8'd4, 8'd8};
            supervisor_config1_q <= {2'd0, 14'd32, 2'd0, 14'd16};
        end else if (bus.wen) begin
            unique case (reg_addr_w)
                REG_CROSSING_CONFIG: begin
                    crossing_config_q[13:0] <=
                        (bus.wdata[13:0] == 14'd0) ? 14'd1 : bus.wdata[13:0];
                    crossing_config_q[23:16] <=
                        (bus.wdata[23:16] == 8'd0) ? 8'd1 : bus.wdata[23:16];
                end
                REG_KP_ACQUIRE_TARGET:
                    kp_acquire_target_q <= bus.wdata[13:0];
                REG_KP_RAMP_CONFIG: begin
                    kp_ramp_config_q[13:0] <=
                        (bus.wdata[13:0] == 14'd0) ? 14'd1 : bus.wdata[13:0];
                    kp_ramp_config_q[31:16] <=
                        (bus.wdata[31:16] == 16'd0) ? 16'd1 : bus.wdata[31:16];
                end
                REG_ACQUIRE_TIMEOUT:
                    acquire_timeout_q <= (bus.wdata == 32'd0) ? 32'd1 : bus.wdata;
                REG_SERVO_CONFIG: begin
                    servo_config_q[15:0] <=
                        (bus.wdata[15:0] == 16'd0) ? 16'd1 : bus.wdata[15:0];
                    servo_config_q[29:16] <=
                        (bus.wdata[29:16] == 14'd0) ? 14'd1 : bus.wdata[29:16];
                end
                REG_SUPERVISOR_CONFIG0: begin
                    supervisor_config0_q[7:0] <=
                        (bus.wdata[7:0] > 8'd20) ? 8'd20 : bus.wdata[7:0];
                    supervisor_config0_q[15:8] <=
                        (bus.wdata[15:8] == 8'd0) ? 8'd1 : bus.wdata[15:8];
                    supervisor_config0_q[23:16] <=
                        (bus.wdata[23:16] == 8'd0) ? 8'd1 : bus.wdata[23:16];
                end
                REG_SUPERVISOR_CONFIG1:
                    supervisor_config1_q <= bus.wdata;
                default: begin
                end
            endcase
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
                    REG_L1_CAPABILITY:
                        bus.rdata <= (LOCK_ACQ_IMPL == LOCK_ACQ_SIMPLE)
                                   ? 32'h4C31_0001 : 32'd0;
                    REG_CROSSING_CONFIG: bus.rdata <= crossing_config_q;
                    REG_KP_ACQUIRE_TARGET:
                        bus.rdata <= {{18{kp_acquire_target_q[13]}},
                                      kp_acquire_target_q};
                    REG_KP_RAMP_CONFIG: bus.rdata <= kp_ramp_config_q;
                    REG_ACQUIRE_TIMEOUT: bus.rdata <= acquire_timeout_q;
                    REG_SERVO_CONFIG:
                        bus.rdata <= servo_config_q;
                    REG_SUPERVISOR_CONFIG0: bus.rdata <= supervisor_config0_q;
                    REG_SUPERVISOR_CONFIG1: bus.rdata <= supervisor_config1_q;
                    REG_EVENT_LOCK_ERROR: bus.rdata <= event_lock_error_w;
                    REG_VALIDATE_EVENT_COUNT: bus.rdata <= validate_event_count_w;
                    REG_KP_EFFECTIVE:
                        bus.rdata <= {{18{kp_effective_o[13]}}, kp_effective_o};
                    REG_SUPERVISOR_METRICS: bus.rdata <= supervisor_metrics_w;
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
    input  logic               arm_snapshot_target_values_en_i,
    input  logic               arm_snapshot_window_en_i,
    input  logic               arm_snapshot_limits_en_i,
    input  logic               arm_snapshot_metadata_en_i,
    input  logic               arm_snapshot_mask_en_i,
    input  logic               arm_snapshot_runtime_sample_en_i,
    input  logic               arm_snapshot_runtime_timestamp_en_i,
    input  logic               abort_pulse_i,
    input  logic               clear_event_pulse_i,
    input  logic               command_reject_pulse_i,
    input  logic               apply_p_pulse_i,
    input  logic signed [13:0] apply_p_kp_i,
    output logic               trigger_o,
    output logic               hold_o,
    output logic               fault_immediate_o,
    output logic               arm_accepted_o,
    output logic signed [13:0] trigger_out2_sample_o,
    output logic signed [13:0] trigger_error_sample_o,
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

    typedef enum logic [2:0] {
        ARM_IDLE,
        ARM_VALIDATE,
        ARM_DECIDE,
        ARM_COMMIT,
        ARM_FINISH
    } arm_phase_t;

    logic [2:0] state_q;
    arm_phase_t arm_phase_q;
    logic active_config_valid_q;
    logic [31:0] active_generation_q;
    logic signed [15:0] active_target_low_q;
    logic signed [15:0] active_target_high_q;
    logic signed [13:0] previous_error_q;
    logic previous_error_valid_q;
    logic signed [13:0] previous_out2_q;
    logic [1:0] scan_direction_q;
    logic scan_direction_valid_q;
    logic trigger_pending_q;
    logic [63:0] cycle_counter_q;
    logic [2:0] event_type_q;
    logic event_valid_q;
    logic [1:0] event_scan_direction_q;
    logic [1:0] event_error_direction_q;
    logic [15:0] reject_code_q;
    logic [15:0] fault_code_q;
    logic event_commit_pulse_q;
    logic [2:0] event_stage_type_q;
    logic signed [13:0] event_stage_out2_q;
    logic signed [13:0] event_stage_error_q;
    logic [31:0] event_stage_generation_q;
    logic [1:0] event_stage_scan_direction_q;
    logic [1:0] event_stage_error_direction_q;
    logic [63:0] event_stage_timestamp_q;
    logic [15:0] event_stage_reject_code_q;
    logic [15:0] event_stage_fault_code_q;

    logic        [31:0] arm_target_out2_q;
    logic        [31:0] arm_error_setpoint_q;
    logic        [31:0] arm_window_q;
    logic        [31:0] arm_requirements_q;
    logic        [31:0] arm_correction_limit_q;
    logic        [31:0] arm_absolute_limit_q;
    logic        [31:0] arm_generation_q;
    logic         [6:0] arm_written_mask_q;
    logic               arm_request_scan_valid_q;
    logic               arm_request_saturated_q;
    logic signed [13:0] arm_request_out2_q;
    logic signed [13:0] arm_request_error_q;
    logic         [1:0] arm_request_scan_direction_q;
    logic        [63:0] arm_request_timestamp_q;

    logic         [6:0] arm_validation_bits_q;
    logic        [15:0] arm_reject_code_q;
    logic signed [15:0] arm_target_low_q;
    logic signed [15:0] arm_target_high_q;
    logic               arm_accept_decision_q;
    logic               arm_reject_decision_q;
    logic        [15:0] arm_decision_reject_code_q;

    logic arm_commit_target_q;
    logic arm_commit_boundary_q;
    logic arm_commit_limits_q;
    logic arm_commit_requirements_q;
    logic arm_commit_generation_q;
    logic arm_commit_control_q;
    logic arm_commit_event_payload_q;
    logic arm_commit_event_timestamp_q;
    logic arm_commit_event_status_q;
    logic arm_commit_reject_q;

    logic fields_complete_w;
    logic signed_fields_valid_w;
    logic directions_valid_w;
    logic window_valid_w;
    logic limits_valid_w;
    logic target_range_valid_w;
    logic state_ready_w;
    logic config_valid_w;

    logic signed [15:0] shadow_target_ext_w;
    logic signed [15:0] shadow_window_ext_w;
    logic signed [15:0] shadow_target_low_w;
    logic signed [15:0] shadow_target_high_w;
    logic signed [15:0] shadow_absolute_ext_w;

    logic [1:0] scan_direction_now_w;
    logic scan_direction_now_valid_w;
    logic signed [15:0] out2_ext_w;
    logic inside_window_w;
    logic neg_to_pos_w;
    logic pos_to_neg_w;
    logic required_crossing_w;
    logic direction_match_w;
    logic trigger_candidate_w;
    logic fault_candidate_w;

    logic signed [15:0] arm_target_ext_w;
    logic signed [15:0] arm_window_ext_w;
    logic signed [15:0] arm_target_low_next_w;
    logic signed [15:0] arm_target_high_next_w;
    logic signed [15:0] arm_absolute_ext_w;
    logic         [6:0] arm_validation_bits_next_w;
    logic        [15:0] arm_reject_code_next_w;
    logic               arm_current_runtime_valid_w;
    logic        [15:0] arm_final_reject_code_w;
    logic               arm_commit_runtime_ok_w;
    logic               arm_commit_target_w;
    logic               arm_commit_boundary_w;
    logic               arm_commit_limits_w;
    logic               arm_commit_requirements_w;
    logic               arm_commit_generation_w;
    logic               arm_commit_control_w;
    logic               arm_commit_event_payload_w;
    logic               arm_commit_event_timestamp_w;
    logic               arm_commit_event_status_w;

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
    end

    // ARM validation is sourced only from the registered transaction snapshot.
    // Each reject bit is an independent Boolean result; there is no accumulated
    // priority chain from raw shadow inputs into active-register control.
    always_comb begin
        arm_target_ext_w = {{2{arm_target_out2_q[13]}}, arm_target_out2_q[13:0]};
        arm_window_ext_w = {2'd0, arm_window_q[13:0]};
        arm_target_low_next_w = arm_target_ext_w - arm_window_ext_w;
        arm_target_high_next_w = arm_target_ext_w + arm_window_ext_w;
        arm_absolute_ext_w = {2'd0, arm_absolute_limit_q[13:0]};

        arm_validation_bits_next_w[0] = (arm_written_mask_q == 7'h7F);
        arm_validation_bits_next_w[1] =
            (arm_target_out2_q[31:14] == {18{arm_target_out2_q[13]}}) &&
            (arm_error_setpoint_q[31:14] == {18{arm_error_setpoint_q[13]}});
        arm_validation_bits_next_w[2] =
            (arm_requirements_q[31:5] == 27'd0) &&
            ((arm_requirements_q[1:0] == SCAN_DIR_RISING) ||
             (arm_requirements_q[1:0] == SCAN_DIR_FALLING)) &&
            ((arm_requirements_q[3:2] == ERROR_DIR_NEG_TO_POS) ||
             (arm_requirements_q[3:2] == ERROR_DIR_POS_TO_NEG));
        arm_validation_bits_next_w[3] =
            (arm_window_q[31:14] == 18'd0) &&
            (arm_window_q[13:0] != 14'd0) &&
            (arm_window_q[13:0] <= 14'd8191);
        arm_validation_bits_next_w[4] =
            (arm_correction_limit_q[31:14] == 18'd0) &&
            (arm_absolute_limit_q[31:14] == 18'd0) &&
            (arm_correction_limit_q[13:0] <= arm_absolute_limit_q[13:0]) &&
            (arm_absolute_limit_q[13:0] <= 14'd8191);
        arm_validation_bits_next_w[5] =
            (arm_target_low_next_w >= -16'sd8191) &&
            (arm_target_high_next_w <= 16'sd8191) &&
            (arm_target_low_next_w >= -arm_absolute_ext_w) &&
            (arm_target_high_next_w <= arm_absolute_ext_w);
        arm_validation_bits_next_w[6] = arm_request_scan_valid_q;

        arm_reject_code_next_w = 16'd0;
        arm_reject_code_next_w[0] = !arm_validation_bits_next_w[0];
        arm_reject_code_next_w[1] = !arm_validation_bits_next_w[1];
        arm_reject_code_next_w[2] = !arm_validation_bits_next_w[2];
        arm_reject_code_next_w[3] = !arm_validation_bits_next_w[3];
        arm_reject_code_next_w[4] = !arm_validation_bits_next_w[4];
        arm_reject_code_next_w[5] = !arm_validation_bits_next_w[5];
        arm_reject_code_next_w[6] = !arm_validation_bits_next_w[6];
        arm_reject_code_next_w[7] = arm_request_saturated_q;
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

        out2_ext_w = {{2{out2_i[13]}}, out2_i};
        inside_window_w = (out2_ext_w >= active_target_low_q) &&
                          (out2_ext_w <= active_target_high_q);
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

    assign fault_candidate_w = (state_q == STATE_ARMED) &&
                               (saturated_i || !enable_i || (mode_i != MODE_SCAN) ||
                                !active_config_valid_q);
    assign trigger_candidate_w = (state_q == STATE_ARMED) &&
                                 !trigger_pending_q &&
                                 previous_error_valid_q &&
                                 active_config_valid_q &&
                                 !abort_pulse_i &&
                                 !fault_candidate_w &&
                                 direction_match_w &&
                                 inside_window_w &&
                                 required_crossing_w;
    assign hold_o = trigger_pending_q || trigger_o;

    assign arm_current_runtime_valid_w =
        (state_q == STATE_SCAN) && enable_i && (mode_i == MODE_SCAN) &&
        !saturated_i && (fault_code_q == 16'd0) &&
        !abort_pulse_i && !fault_candidate_w;

    // Each qualified commit net has one local registered source and only drives
    // its own active-register group. Runtime qualification is shallow and is
    // replicated at the group boundary rather than broadcast as one CE.
    assign arm_commit_runtime_ok_w = arm_current_runtime_valid_w;
    assign arm_commit_target_w =
        arm_commit_target_q && arm_commit_runtime_ok_w;
    assign arm_commit_boundary_w =
        arm_commit_boundary_q && arm_commit_runtime_ok_w;
    assign arm_commit_limits_w =
        arm_commit_limits_q && arm_commit_runtime_ok_w;
    assign arm_commit_requirements_w =
        arm_commit_requirements_q && arm_commit_runtime_ok_w;
    assign arm_commit_generation_w =
        arm_commit_generation_q && arm_commit_runtime_ok_w;
    assign arm_commit_control_w =
        arm_commit_control_q && arm_commit_runtime_ok_w;
    assign arm_commit_event_payload_w = arm_commit_event_payload_q;
    assign arm_commit_event_timestamp_w = arm_commit_event_timestamp_q;
    assign arm_commit_event_status_w = arm_commit_event_status_q;
    assign arm_accepted_o = arm_commit_control_w;

    always_comb begin
        arm_final_reject_code_w = arm_decision_reject_code_q;
        arm_final_reject_code_w[6] =
            arm_decision_reject_code_q[6] ||
            (state_q != STATE_SCAN) || !enable_i || (mode_i != MODE_SCAN) ||
            (fault_code_q != 16'd0);
        arm_final_reject_code_w[7] =
            arm_decision_reject_code_q[7] || saturated_i;
    end

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

    // ARM snapshot groups use independent registered mailbox enables. Every
    // enable is produced by the same accepted sys_bus write, so all groups
    // capture one atomic transaction without a shared 327-load CE.
    always_ff @(posedge clk_i) begin
        if (!rstn_i) begin
            arm_target_out2_q <= 32'd0;
            arm_error_setpoint_q <= 32'd0;
        end else if (arm_snapshot_target_values_en_i) begin
            arm_target_out2_q <= shadow_target_out2_i;
            arm_error_setpoint_q <= shadow_error_setpoint_i;
        end
    end

    always_ff @(posedge clk_i) begin
        if (!rstn_i) begin
            arm_window_q <= 32'd0;
        end else if (arm_snapshot_window_en_i) begin
            arm_window_q <= shadow_window_i;
        end
    end

    always_ff @(posedge clk_i) begin
        if (!rstn_i) begin
            arm_correction_limit_q <= 32'd0;
            arm_absolute_limit_q <= 32'd0;
        end else if (arm_snapshot_limits_en_i) begin
            arm_correction_limit_q <= shadow_correction_limit_i;
            arm_absolute_limit_q <= shadow_absolute_limit_i;
        end
    end

    always_ff @(posedge clk_i) begin
        if (!rstn_i) begin
            arm_requirements_q <= 32'd0;
            arm_generation_q <= 32'd0;
        end else if (arm_snapshot_metadata_en_i) begin
            arm_requirements_q <= shadow_requirements_i;
            arm_generation_q <= shadow_generation_i;
        end
    end

    always_ff @(posedge clk_i) begin
        if (!rstn_i) begin
            arm_written_mask_q <= 7'd0;
        end else if (arm_snapshot_mask_en_i) begin
            arm_written_mask_q <= shadow_written_mask_i;
        end
    end

    always_ff @(posedge clk_i) begin
        if (!rstn_i) begin
            arm_request_scan_valid_q <= 1'b0;
            arm_request_saturated_q <= 1'b0;
            arm_request_out2_q <= 14'sd0;
            arm_request_error_q <= 14'sd0;
            arm_request_scan_direction_q <= 2'd0;
        end else if (arm_snapshot_runtime_sample_en_i) begin
            arm_request_scan_valid_q <= (fault_code_q == 16'd0);
            arm_request_saturated_q <= saturated_i;
            arm_request_out2_q <= out2_i;
            arm_request_error_q <= error_i;
            arm_request_scan_direction_q <= scan_direction_now_w;
        end
    end

    always_ff @(posedge clk_i) begin
        if (!rstn_i) begin
            arm_request_timestamp_q <= 64'd0;
        end else if (arm_snapshot_runtime_timestamp_en_i) begin
            arm_request_timestamp_q <= cycle_counter_q;
        end
    end

    // ARM validation, decision, and commit each consume only the preceding
    // registered transaction stage.
    always_ff @(posedge clk_i) begin
        if (!rstn_i) begin
            arm_phase_q <= ARM_IDLE;
            arm_validation_bits_q <= 7'd0;
            arm_reject_code_q <= 16'd0;
            arm_target_low_q <= 16'sd0;
            arm_target_high_q <= 16'sd0;
            arm_accept_decision_q <= 1'b0;
            arm_reject_decision_q <= 1'b0;
            arm_decision_reject_code_q <= 16'd0;
            arm_commit_target_q <= 1'b0;
            arm_commit_boundary_q <= 1'b0;
            arm_commit_limits_q <= 1'b0;
            arm_commit_requirements_q <= 1'b0;
            arm_commit_generation_q <= 1'b0;
            arm_commit_control_q <= 1'b0;
            arm_commit_event_payload_q <= 1'b0;
            arm_commit_event_timestamp_q <= 1'b0;
            arm_commit_event_status_q <= 1'b0;
            arm_commit_reject_q <= 1'b0;
        end else begin
            arm_commit_target_q <= 1'b0;
            arm_commit_boundary_q <= 1'b0;
            arm_commit_limits_q <= 1'b0;
            arm_commit_requirements_q <= 1'b0;
            arm_commit_generation_q <= 1'b0;
            arm_commit_control_q <= 1'b0;
            arm_commit_event_payload_q <= 1'b0;
            arm_commit_event_timestamp_q <= 1'b0;
            arm_commit_event_status_q <= 1'b0;
            arm_commit_reject_q <= 1'b0;

            if (abort_pulse_i || fault_candidate_w) begin
                arm_phase_q <= ARM_IDLE;
                arm_accept_decision_q <= 1'b0;
                arm_reject_decision_q <= 1'b0;
            end else begin
                unique case (arm_phase_q)
                    ARM_IDLE: begin
                        if (arm_pulse_i && (state_q == STATE_SCAN) &&
                            enable_i && (mode_i == MODE_SCAN)) begin
                            arm_phase_q <= ARM_VALIDATE;
                        end
                    end
                    ARM_VALIDATE: begin
                        arm_validation_bits_q <= arm_validation_bits_next_w;
                        arm_reject_code_q <= arm_reject_code_next_w;
                        arm_target_low_q <= arm_target_low_next_w;
                        arm_target_high_q <= arm_target_high_next_w;
                        arm_phase_q <= ARM_DECIDE;
                    end
                    ARM_DECIDE: begin
                        arm_accept_decision_q <=
                            (&arm_validation_bits_q) &&
                            !arm_request_saturated_q &&
                            arm_current_runtime_valid_w;
                        arm_reject_decision_q <=
                            !((&arm_validation_bits_q) &&
                              !arm_request_saturated_q &&
                              arm_current_runtime_valid_w);
                        arm_decision_reject_code_q <= arm_reject_code_q;
                        arm_decision_reject_code_q[6] <=
                            arm_reject_code_q[6] ||
                            (state_q != STATE_SCAN) || !enable_i ||
                            (mode_i != MODE_SCAN) || (fault_code_q != 16'd0);
                        arm_decision_reject_code_q[7] <=
                            arm_reject_code_q[7] || saturated_i;
                        arm_phase_q <= ARM_COMMIT;
                    end
                    ARM_COMMIT: begin
                        if (arm_accept_decision_q &&
                            arm_current_runtime_valid_w) begin
                            arm_commit_target_q <= 1'b1;
                            arm_commit_boundary_q <= 1'b1;
                            arm_commit_limits_q <= 1'b1;
                            arm_commit_requirements_q <= 1'b1;
                            arm_commit_generation_q <= 1'b1;
                            arm_commit_control_q <= 1'b1;
                        end else begin
                            arm_commit_reject_q <= 1'b1;
                        end
                        arm_commit_event_payload_q <= 1'b1;
                        arm_commit_event_timestamp_q <= 1'b1;
                        arm_commit_event_status_q <= 1'b1;
                        arm_phase_q <= ARM_FINISH;
                    end
                    ARM_FINISH: begin
                        arm_phase_q <= ARM_IDLE;
                        arm_accept_decision_q <= 1'b0;
                        arm_reject_decision_q <= 1'b0;
                    end
                    default: arm_phase_q <= ARM_IDLE;
                endcase
            end
        end
    end

    // Active target group: 42 register bits, one local commit pulse.
    always_ff @(posedge clk_i) begin
        if (!rstn_i) begin
            active_target_out2_o <= 14'sd0;
            active_error_setpoint_o <= 14'sd0;
            active_window_o <= 14'd0;
        end else if (arm_commit_target_w) begin
            active_target_out2_o <= arm_target_out2_q[13:0];
            active_error_setpoint_o <= arm_error_setpoint_q[13:0];
            active_window_o <= arm_window_q[13:0];
        end
    end

    // Precomputed signed boundaries: 32 register bits.
    always_ff @(posedge clk_i) begin
        if (!rstn_i) begin
            active_target_low_q <= 16'sd0;
            active_target_high_q <= 16'sd0;
        end else if (arm_commit_boundary_w) begin
            active_target_low_q <= arm_target_low_q;
            active_target_high_q <= arm_target_high_q;
        end
    end

    // Active limit group: 28 register bits.
    always_ff @(posedge clk_i) begin
        if (!rstn_i) begin
            active_correction_limit_o <= 14'd0;
            active_absolute_limit_o <= 14'd0;
        end else if (arm_commit_limits_w) begin
            active_correction_limit_o <= arm_correction_limit_q[13:0];
            active_absolute_limit_o <= arm_absolute_limit_q[13:0];
        end
    end

    // Requirements metadata: 32 register bits.
    always_ff @(posedge clk_i) begin
        if (!rstn_i) begin
            active_requirements_o <= 32'd0;
        end else if (arm_commit_requirements_w) begin
            active_requirements_o <= arm_requirements_q;
        end
    end

    // Generation/valid metadata: 33 register bits.
    always_ff @(posedge clk_i) begin
        if (!rstn_i) begin
            active_generation_q <= 32'd0;
            active_config_valid_q <= 1'b0;
        end else if (abort_pulse_i || fault_candidate_w) begin
            active_config_valid_q <= 1'b0;
        end else if (arm_commit_generation_w) begin
            active_generation_q <= arm_generation_q;
            active_config_valid_q <= 1'b1;
        end else if ((state_q == STATE_SAFE) || (state_q == STATE_FAULT) ||
                     !enable_i || (mode_i == MODE_SAFE)) begin
            active_config_valid_q <= 1'b0;
        end
    end

    // Acquisition state, trigger pipeline, and non-ARM event sources. The
    // real-time comparator tree terminates at trigger_pending_q.
    always_ff @(posedge clk_i) begin
        if (!rstn_i) begin
            state_q <= STATE_SAFE;
            previous_error_q <= 14'sd0;
            previous_error_valid_q <= 1'b0;
            previous_out2_q <= 14'sd0;
            scan_direction_q <= SCAN_DIR_RISING;
            scan_direction_valid_q <= 1'b0;
            trigger_pending_q <= 1'b0;
            trigger_o <= 1'b0;
            fault_immediate_o <= 1'b0;
            trigger_out2_sample_o <= 14'sd0;
            trigger_error_sample_o <= 14'sd0;
            cycle_counter_q <= 64'd0;
            event_commit_pulse_q <= 1'b0;
            event_stage_type_q <= EVENT_NONE;
            event_stage_out2_q <= 14'sd0;
            event_stage_error_q <= 14'sd0;
            event_stage_generation_q <= 32'd0;
            event_stage_scan_direction_q <= 2'd0;
            event_stage_error_direction_q <= 2'd0;
            event_stage_timestamp_q <= 64'd0;
            event_stage_reject_code_q <= 16'd0;
            event_stage_fault_code_q <= 16'd0;
        end else begin
            cycle_counter_q <= cycle_counter_q + 64'd1;
            trigger_o <= 1'b0;
            fault_immediate_o <= 1'b0;
            event_commit_pulse_q <= 1'b0;

            previous_out2_q <= out2_i;
            if (out2_i != previous_out2_q) begin
                scan_direction_q <= scan_direction_now_w;
                scan_direction_valid_q <= 1'b1;
            end

            if (abort_pulse_i) begin
                state_q <= STATE_SAFE;
                previous_error_valid_q <= 1'b0;
                trigger_pending_q <= 1'b0;
                event_commit_pulse_q <= 1'b1;
                event_stage_type_q <= EVENT_ABORTED;
                event_stage_out2_q <= out2_i;
                event_stage_error_q <= error_i;
                event_stage_generation_q <= active_generation_q;
                event_stage_scan_direction_q <= scan_direction_now_w;
                event_stage_error_direction_q <= 2'd0;
                event_stage_timestamp_q <= cycle_counter_q;
                event_stage_reject_code_q <= reject_code_q;
                event_stage_fault_code_q <= fault_code_q;
            end else if (fault_candidate_w) begin
                state_q <= STATE_FAULT;
                previous_error_valid_q <= 1'b0;
                trigger_pending_q <= 1'b0;
                fault_immediate_o <= 1'b1;
                event_commit_pulse_q <= 1'b1;
                event_stage_type_q <= EVENT_FAULT;
                event_stage_out2_q <= out2_i;
                event_stage_error_q <= error_i;
                event_stage_generation_q <= active_generation_q;
                event_stage_scan_direction_q <= scan_direction_now_w;
                event_stage_error_direction_q <= active_requirements_o[3:2];
                event_stage_timestamp_q <= cycle_counter_q;
                event_stage_reject_code_q <= reject_code_q;
                event_stage_fault_code_q <= FAULT_RUNTIME_SAFETY;
            end else if (arm_commit_event_status_w) begin
                event_commit_pulse_q <= 1'b1;
                if (arm_commit_event_payload_w) begin
                    event_stage_type_q <= arm_commit_control_w
                                        ? EVENT_ARMED
                                        : EVENT_CONFIG_REJECTED;
                    event_stage_out2_q <= arm_request_out2_q;
                    event_stage_error_q <= arm_request_error_q;
                    event_stage_generation_q <= arm_generation_q;
                end
                if (arm_commit_event_timestamp_w)
                    event_stage_timestamp_q <= arm_request_timestamp_q;
                event_stage_scan_direction_q <= arm_request_scan_direction_q;
                event_stage_error_direction_q <= arm_requirements_q[3:2];
                event_stage_reject_code_q <= arm_commit_control_w
                                           ? 16'd0
                                           : arm_final_reject_code_w;
                event_stage_fault_code_q <= fault_code_q;

                previous_error_valid_q <= 1'b0;
                trigger_pending_q <= 1'b0;
                if (arm_commit_control_w) begin
                    previous_error_q <= arm_request_error_q[13:0];
                    state_q <= STATE_ARMED;
                end else if (!enable_i || (mode_i == MODE_SAFE)) begin
                    state_q <= STATE_SAFE;
                end else if (mode_i == MODE_P_LOCK) begin
                    if (apply_p_kp_i == 14'sd0)
                        state_q <= STATE_P_LOCK_KP0;
                    else
                        state_q <= STATE_P_LOCK_ACTIVE;
                end else begin
                    state_q <= STATE_SCAN;
                end
            end else begin
                unique case (state_q)
                    STATE_SAFE: begin
                        previous_error_valid_q <= 1'b0;
                        trigger_pending_q <= 1'b0;
                        if (enable_i && (mode_i == MODE_SCAN) &&
                            (fault_code_q == 16'd0))
                            state_q <= STATE_SCAN;
                    end
                    STATE_SCAN: begin
                        previous_error_valid_q <= 1'b0;
                        trigger_pending_q <= 1'b0;
                        if (!enable_i || (mode_i == MODE_SAFE)) begin
                            state_q <= STATE_SAFE;
                        end else if (mode_i == MODE_P_LOCK) begin
                            if (apply_p_kp_i == 14'sd0)
                                state_q <= STATE_P_LOCK_KP0;
                            else
                                state_q <= STATE_P_LOCK_ACTIVE;
                        end else if (command_reject_pulse_i) begin
                            event_commit_pulse_q <= 1'b1;
                            event_stage_type_q <= EVENT_COMMAND_REJECTED;
                            event_stage_out2_q <= event_out2_o[13:0];
                            event_stage_error_q <= event_error_o[13:0];
                            event_stage_generation_q <= event_config_generation_o;
                            event_stage_scan_direction_q <= event_scan_direction_q;
                            event_stage_error_direction_q <= event_error_direction_q;
                            event_stage_timestamp_q <= cycle_counter_q;
                            event_stage_reject_code_q <= REJECT_COMMAND;
                            event_stage_fault_code_q <= fault_code_q;
                        end
                    end
                    STATE_ARMED: begin
                        if (trigger_pending_q) begin
                            trigger_pending_q <= 1'b0;
                            previous_error_q <= error_i;
                            if (inside_window_w && direction_match_w) begin
                                trigger_o <= 1'b1;
                                trigger_out2_sample_o <= out2_i;
                                trigger_error_sample_o <= error_i;
                                previous_error_valid_q <= 1'b0;
                                state_q <= STATE_TRIGGER_CAPTURE;
                                event_commit_pulse_q <= 1'b1;
                                event_stage_type_q <= EVENT_TRIGGERED;
                                event_stage_out2_q <= out2_i;
                                event_stage_error_q <= error_i;
                                event_stage_generation_q <= active_generation_q;
                                event_stage_scan_direction_q <= scan_direction_now_w;
                                event_stage_error_direction_q <= active_requirements_o[3:2];
                                event_stage_timestamp_q <= cycle_counter_q;
                                event_stage_reject_code_q <= reject_code_q;
                                event_stage_fault_code_q <= fault_code_q;
                            end else begin
                                previous_error_valid_q <= 1'b1;
                            end
                        end else begin
                            if (command_reject_pulse_i) begin
                                event_commit_pulse_q <= 1'b1;
                                event_stage_type_q <= EVENT_COMMAND_REJECTED;
                                event_stage_out2_q <= event_out2_o[13:0];
                                event_stage_error_q <= event_error_o[13:0];
                                event_stage_generation_q <= event_config_generation_o;
                                event_stage_scan_direction_q <= event_scan_direction_q;
                                event_stage_error_direction_q <= event_error_direction_q;
                                event_stage_timestamp_q <= cycle_counter_q;
                                event_stage_reject_code_q <= REJECT_COMMAND;
                                event_stage_fault_code_q <= fault_code_q;
                            end else if (arm_pulse_i) begin
                                event_commit_pulse_q <= 1'b1;
                                event_stage_type_q <= EVENT_CONFIG_REJECTED;
                                event_stage_out2_q <= out2_i;
                                event_stage_error_q <= error_i;
                                event_stage_generation_q <= active_generation_q;
                                event_stage_scan_direction_q <= scan_direction_now_w;
                                event_stage_error_direction_q <= active_requirements_o[3:2];
                                event_stage_timestamp_q <= cycle_counter_q;
                                event_stage_reject_code_q <= REJECT_STATE;
                                event_stage_fault_code_q <= fault_code_q;
                            end

                            if (!previous_error_valid_q) begin
                                previous_error_q <= error_i;
                                previous_error_valid_q <= 1'b1;
                            end else begin
                                previous_error_q <= error_i;
                                if (trigger_candidate_w)
                                    trigger_pending_q <= 1'b1;
                            end
                        end
                    end
                    STATE_TRIGGER_CAPTURE: state_q <= STATE_P_LOCK_KP0;
                    STATE_P_LOCK_KP0: begin
                        if (!enable_i || (mode_i == MODE_SAFE)) begin
                            state_q <= STATE_SAFE;
                        end else if (apply_p_pulse_i &&
                                     (apply_p_kp_i != 14'sd0)) begin
                            state_q <= STATE_P_LOCK_ACTIVE;
                        end
                    end
                    STATE_P_LOCK_ACTIVE: begin
                        if (!enable_i || (mode_i == MODE_SAFE)) begin
                            state_q <= STATE_SAFE;
                        end else if (apply_p_pulse_i &&
                                     (apply_p_kp_i == 14'sd0)) begin
                            state_q <= STATE_P_LOCK_KP0;
                        end
                    end
                    STATE_FAULT: begin
                        previous_error_valid_q <= 1'b0;
                        trigger_pending_q <= 1'b0;
                        if (!enable_i && (mode_i == MODE_SAFE) && !event_valid_q)
                            state_q <= STATE_SAFE;
                    end
                    default: begin
                        state_q <= STATE_FAULT;
                        trigger_pending_q <= 1'b0;
                    end
                endcase
            end
        end
    end

    // Sticky event commit is intentionally one registered stage after the
    // acquisition decision. Real-time comparators never drive event CE/D.
    always_ff @(posedge clk_i) begin
        if (!rstn_i) begin
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
        end else if (event_commit_pulse_q) begin
            event_sequence_o <= event_sequence_o + 32'd1;
            event_out2_o <= {{18{event_stage_out2_q[13]}}, event_stage_out2_q};
            event_error_o <= {{18{event_stage_error_q[13]}}, event_stage_error_q};
            event_config_generation_o <= event_stage_generation_q;
            event_timestamp_lo_o <= event_stage_timestamp_q[31:0];
            event_timestamp_hi_o <= event_stage_timestamp_q[63:32];
            event_type_q <= event_stage_type_q;
            event_valid_q <= 1'b1;
            event_scan_direction_q <= event_stage_scan_direction_q;
            event_error_direction_q <= event_stage_error_direction_q;
            reject_code_q <= event_stage_reject_code_q;
            fault_code_q <= event_stage_fault_code_q;
        end else if (clear_event_pulse_i) begin
            event_valid_q <= 1'b0;
            event_type_q <= EVENT_NONE;
            event_scan_direction_q <= 2'd0;
            event_error_direction_q <= 2'd0;
            reject_code_q <= 16'd0;
            if (state_q != STATE_FAULT)
                fault_code_q <= 16'd0;
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
    input  logic        [15:0] servo_update_div_i,
    input  logic        [13:0] out2_slew_limit_i,
    input  logic               integral_reset_i,
    input  logic               acq_hold_i,
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
    logic        [12:0] s5_abs_limit;

    logic               s6_enable;
    logic        [31:0] s6_mode;
    logic signed [13:0] s6_target;
    logic               s6_saturated;
    logic               s6_valid;
    logic signed [14:0] s6_slew_limit;

    logic        [12:0] s4_abs_limit_w;
    logic signed [31:0] s5_abs_limit_ext_w;
    logic signed [31:0] correction_limit_abs_w;
    logic signed [31:0] s6_target_next_w;
    logic               s6_saturated_next_w;
    logic signed [14:0] slew_delta_w;
    logic        [15:0] servo_count_q;
    logic               servo_tick_w;

    always_comb begin
        if (s4_lock_limit == -14'sd8192)
            s4_abs_limit_w = 13'd8191;
        else if (s4_lock_limit < 14'sd0)
            s4_abs_limit_w = $unsigned(-s4_lock_limit);
        else
            s4_abs_limit_w = $unsigned(s4_lock_limit[12:0]);

        if (s3_correction_limit < 14'sd0)
            correction_limit_abs_w =
                -$signed({{18{s3_correction_limit[13]}}, s3_correction_limit});
        else
            correction_limit_abs_w =
                $signed({{18{s3_correction_limit[13]}}, s3_correction_limit});
        if (correction_limit_abs_w > 32'sd8191)
            correction_limit_abs_w = 32'sd8191;

        s5_abs_limit_ext_w = $signed({19'd0, s5_abs_limit});
        if (s5_raw > s5_abs_limit_ext_w) begin
            s6_target_next_w = s5_abs_limit_ext_w;
            s6_saturated_next_w = 1'b1;
        end else if (s5_raw < -s5_abs_limit_ext_w) begin
            s6_target_next_w = -s5_abs_limit_ext_w;
            s6_saturated_next_w = 1'b1;
        end else begin
            s6_target_next_w = s5_raw;
            s6_saturated_next_w = s5_correction_saturated;
        end
        slew_delta_w =
            $signed({s6_target[13], s6_target}) -
            $signed({control_o[13], control_o});
    end

    assign servo_tick_w =
        (servo_count_q + 16'd1 >=
         ((servo_update_div_i == 16'd0) ? 16'd1 : servo_update_div_i));

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
            s5_abs_limit    <= 13'd8191;
            s6_enable       <= 1'b0;
            s6_mode         <= MODE_SAFE;
            s6_target       <= 14'sd0;
            s6_saturated    <= 1'b0;
            s6_valid        <= 1'b0;
            s6_slew_limit   <= 15'sd1;
            control_o       <= 14'sd0;
            saturated_o     <= 1'b0;
            servo_count_q    <= 16'd0;
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
            s5_abs_limit  <= s4_abs_limit_w;

            s6_enable     <= s5_enable;
            s6_mode       <= s5_mode;
            s6_target     <= s6_target_next_w[13:0];
            s6_saturated  <= s6_saturated_next_w;
            s6_valid      <= s5_enable &&
                             ((s5_mode == MODE_P_LOCK) ||
                              (s5_mode == MODE_PI_LOCK));
            s6_slew_limit <= (out2_slew_limit_i == 14'd0)
                           ? 15'sd1
                           : $signed({1'b0, out2_slew_limit_i});

            if (!enable_i ||
                ((mode_i != MODE_P_LOCK) && (mode_i != MODE_PI_LOCK)) ||
                acq_abort_i || acq_fault_i) begin
                s0_enable <= 1'b0;
                s1_enable <= 1'b0;
                s2_enable <= 1'b0;
                s3_enable <= 1'b0;
                s4_enable <= 1'b0;
                s5_enable <= 1'b0;
                s6_enable <= 1'b0;
                s6_valid  <= 1'b0;
            end

            if (!enable_i || (mode_i == MODE_SAFE) || acq_abort_i || acq_fault_i) begin
                control_o   <= 14'sd0;
                saturated_o <= 1'b0;
                servo_count_q <= 16'd0;
            end else if (acq_hold_i) begin
                control_o   <= control_o;
                saturated_o <= 1'b0;
            end else begin
                unique case (mode_i)
                    MODE_SCAN: begin
                        control_o   <= scan_i;
                        saturated_o <= scan_saturated_i;
                        servo_count_q <= 16'd0;
                    end
                    MODE_HOLD: begin
                        control_o   <= hold_value_i;
                        saturated_o <= 1'b0;
                        servo_count_q <= 16'd0;
                    end
                    MODE_P_LOCK,
                    MODE_PI_LOCK: begin
                        if (!servo_tick_w) begin
                            servo_count_q <= servo_count_q + 16'd1;
                        end else if (s6_valid && s6_enable &&
                            ((s6_mode == MODE_P_LOCK) || (s6_mode == MODE_PI_LOCK))) begin
                            servo_count_q <= 16'd0;
                            if (slew_delta_w > s6_slew_limit) begin
                                control_o <= control_o + s6_slew_limit[13:0];
                                saturated_o <= s6_saturated;
                            end else if (slew_delta_w < -s6_slew_limit) begin
                                control_o <= control_o - s6_slew_limit[13:0];
                                saturated_o <= s6_saturated;
                            end else begin
                                control_o <= s6_target;
                                saturated_o <= s6_saturated;
                            end
                        end else begin
                            servo_count_q <= 16'd0;
                            control_o   <= lock_bias_i;
                            saturated_o <= 1'b0;
                        end
                    end
                    default: begin
                        control_o   <= 14'sd0;
                        saturated_o <= 1'b0;
                        servo_count_q <= 16'd0;
                    end
                endcase
            end
        end
    end

endmodule
