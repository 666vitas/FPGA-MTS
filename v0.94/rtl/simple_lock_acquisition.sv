`timescale 1ns/1ps
`include "realtime_error_crossing_detector.sv"
`include "l1_kp_ramp.sv"
`include "l1_lock_supervisor.sv"
`include "l1_event_recorder.sv"

module simple_lock_acquisition (
    input  logic               clk_i,
    input  logic               rstn_i,
    input  logic        [31:0] mode_i,
    input  logic               enable_i,
    input  logic               saturated_i,
    input  logic signed [13:0] out2_i,
    input  logic signed [13:0] error_i,
    input  logic        [31:0] target_out2_i,
    input  logic        [31:0] target_error_setpoint_i,
    input  logic        [31:0] target_window_i,
    input  logic        [31:0] target_requirements_i,
    input  logic        [31:0] correction_limit_i,
    input  logic        [31:0] absolute_limit_i,
    input  logic        [31:0] config_generation_i,
    input  logic         [6:0] config_written_mask_i,
    input  logic               request_active_i,
    input  logic               request_validate_i,
    input  logic               abort_i,
    input  logic               clear_event_i,
    input  logic        [13:0] crossing_hysteresis_i,
    input  logic         [7:0] crossing_samples_i,
    input  logic signed [13:0] kp_target_i,
    input  logic        [13:0] kp_ramp_step_i,
    input  logic        [15:0] kp_ramp_div_i,
    input  logic        [31:0] acquire_timeout_i,
    input  logic        [15:0] servo_update_div_i,
    input  logic         [7:0] observe_shift_i,
    input  logic         [7:0] lock_confirm_windows_i,
    input  logic         [7:0] divergence_windows_i,
    input  logic        [13:0] error_mean_limit_i,
    input  logic        [13:0] error_abs_limit_i,
    output logic               trigger_o,
    output logic               hold_o,
    output logic               fault_immediate_o,
    output logic               request_accepted_o,
    output logic signed [13:0] trigger_out2_sample_o,
    output logic signed [13:0] trigger_error_sample_o,
    output logic signed [14:0] trigger_lock_error_sample_o,
    output logic signed [13:0] kp_effective_o,
    output logic        [31:0] validate_event_count_o,
    output logic        [31:0] supervisor_metrics_o,
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
    output logic signed [31:0] event_lock_error_o,
    output logic        [31:0] event_config_generation_o,
    output logic        [31:0] event_info_o,
    output logic        [31:0] event_timestamp_lo_o,
    output logic        [31:0] event_timestamp_hi_o,
    output logic        [31:0] fault_detail_o
);
    localparam integer SAMPLE_PIPELINE_LATENCY = 1;
    localparam integer CROSSING_PIPELINE_LATENCY = 2;
    localparam integer SUPERVISOR_PIPELINE_LATENCY = 3;
    localparam integer EVENT_PIPELINE_LATENCY = 1;
    localparam logic [7:0] EFFECTIVE_OBSERVE_SHIFT = 8'd8;

    localparam logic [31:0] MODE_SAFE = 32'd0;
    localparam logic [31:0] MODE_SCAN = 32'd1;
    localparam logic [31:0] MODE_P_LOCK = 32'd3;

    localparam logic [2:0] STATE_SAFE       = 3'd0;
    localparam logic [2:0] STATE_SCAN       = 3'd1;
    localparam logic [2:0] STATE_VALIDATING = 3'd2;
    localparam logic [2:0] STATE_ARMED      = 3'd3;
    localparam logic [2:0] STATE_ACQUIRING  = 3'd4;
    localparam logic [2:0] STATE_P_LOCKED   = 3'd5;
    localparam logic [2:0] STATE_FAILED     = 3'd6;
    localparam logic [2:0] STATE_FAULT      = 3'd7;

    localparam logic [1:0] SCAN_DIR_RISING = 2'd1;
    localparam logic [1:0] SCAN_DIR_FALLING = 2'd2;
    localparam logic [2:0] EVENT_TRIGGERED = 3'd2;
    localparam logic [2:0] EVENT_ABORTED = 3'd3;
    localparam logic [2:0] EVENT_CONFIG_REJECTED = 3'd4;
    localparam logic [2:0] EVENT_FAULT = 3'd6;
    localparam logic [2:0] EVENT_VALIDATED = 3'd7;
    localparam logic [15:0] REJECT_CONFIG = 16'h0001;
    localparam logic [15:0] REJECT_POLARITY = 16'h0002;
    localparam logic [15:0] REJECT_OBSERVE_SHIFT = 16'h0004;
    localparam logic [15:0] FAULT_RUNTIME = 16'h0001;
    localparam logic [15:0] FAULT_TIMEOUT = 16'h0002;
    localparam logic [15:0] FAULT_DIVERGENCE = 16'h0004;
    localparam logic [15:0] FAULT_OVERFLOW = 16'h0008;

    logic [2:0] state_q;
    logic [63:0] cycle_counter_q;

    // ARM request mailbox and registered validation/commit pipeline.
    logic arm_capture_pending_q;
    logic arm_decide_pending_q;
    logic arm_decision_valid_q;
    logic arm_accept_pulse_q;
    logic arm_reject_pulse_q;
    logic arm_kind_validate_q;
    logic pending_validate_q;
    logic [31:0] pending_target_out2_q;
    logic [31:0] pending_error_setpoint_q;
    logic [31:0] pending_window_q;
    logic [31:0] pending_requirements_q;
    logic [31:0] pending_correction_limit_q;
    logic [31:0] pending_absolute_limit_q;
    logic [31:0] pending_generation_q;
    logic [6:0] pending_written_mask_q;
    logic [13:0] pending_hysteresis_q;
    logic [7:0] pending_crossing_samples_q;
    logic signed [13:0] pending_kp_target_q;
    logic [13:0] pending_kp_step_q;
    logic [15:0] pending_kp_div_q;
    logic [31:0] pending_timeout_q;
    logic [15:0] pending_servo_div_q;
    logic [7:0] pending_observe_shift_q;
    logic [7:0] pending_confirm_windows_q;
    logic [7:0] pending_divergence_windows_q;
    logic [13:0] pending_error_mean_limit_q;
    logic [13:0] pending_error_abs_limit_q;

    logic pending_fields_complete_w;
    logic pending_signed_fields_valid_w;
    logic pending_directions_valid_w;
    logic pending_polarity_consistent_w;
    logic pending_window_valid_w;
    logic pending_limits_valid_w;
    logic pending_target_range_valid_w;
    logic pending_runtime_ready_w;
    logic pending_observe_shift_valid_w;
    logic pending_config_valid_w;
    logic signed [15:0] pending_target_ext_w;
    logic signed [15:0] pending_window_ext_w;
    logic signed [15:0] pending_target_low_w;
    logic signed [15:0] pending_target_high_w;
    logic signed [15:0] pending_absolute_ext_w;

    logic raw_fields_complete_w;
    logic raw_signed_fields_valid_w;
    logic raw_directions_valid_w;
    logic raw_polarity_consistent_w;
    logic raw_window_valid_w;
    logic raw_limits_valid_w;
    logic raw_target_range_valid_w;
    logic raw_runtime_ready_w;
    logic raw_observe_shift_valid_w;
    logic raw_base_config_valid_w;
    logic raw_active_config_valid_w;
    logic signed [15:0] raw_target_ext_w;
    logic signed [15:0] raw_window_ext_w;
    logic signed [15:0] raw_target_low_w;
    logic signed [15:0] raw_target_high_w;
    logic signed [15:0] raw_absolute_ext_w;

    // ARM-committed active configuration.
    logic active_validate_q;
    logic active_config_valid_q;
    logic signed [15:0] guard_low_q;
    logic signed [15:0] guard_high_q;
    logic [13:0] active_hysteresis_q;
    logic [7:0] active_crossing_samples_q;
    logic signed [13:0] active_kp_target_q;
    logic [13:0] active_kp_step_q;
    logic [15:0] active_kp_div_q;
    logic [31:0] active_timeout_q;
    logic [15:0] active_servo_div_q;
    logic [7:0] active_confirm_windows_q;
    logic [7:0] active_divergence_windows_q;
    logic [23:0] active_mean_sum_limit_q;
    logic [23:0] active_abs_sum_limit_q;
    logic [23:0] active_divergence_sum_limit_q;
    logic [31:0] active_generation_q;

    // Unified aligned sampling stage.
    logic signed [13:0] previous_out2_q;
    logic signed [13:0] sample_out2_q;
    logic signed [13:0] sample_error_q;
    logic signed [13:0] sample_setpoint_q;
    logic signed [14:0] sample_lock_error_q;
    logic [14:0] sample_abs_error_q;
    logic [1:0] sample_scan_direction_q;
    logic in_guard_q;
    logic direction_match_q;
    logic runtime_ok_q;
    logic sample_valid_q;
    logic [1:0] scan_direction_now_w;
    logic scan_direction_valid_q;
    logic signed [14:0] raw_lock_error_w;
    logic [14:0] raw_abs_error_w;
    logic signed [15:0] raw_out2_ext_w;
    logic raw_in_guard_w;
    logic raw_direction_match_w;
    logic raw_runtime_ok_w;

    // Detector output and payload alignment.
    logic detector_clear_w;
    logic crossing_w;
    logic crossing_candidate_unused_w;
    logic source_confirmed_w;
    logic pass_consumed_w;
    logic signed [13:0] detector_out2_q;
    logic signed [13:0] detector_error_q;
    logic signed [14:0] detector_lock_error_q;
    logic [1:0] detector_scan_direction_q;
    logic crossing_event_q;
    logic signed [13:0] crossing_out2_q;
    logic signed [13:0] crossing_error_q;
    logic signed [14:0] crossing_lock_error_q;
    logic [1:0] crossing_scan_direction_q;

    // Small registered engines.
    logic [15:0] servo_counter_q;
    logic servo_tick_w;
    logic kp_start_q;
    logic kp_stop_w;
    logic kp_target_reached_w;
    logic supervisor_start_q;
    logic supervisor_stop_w;
    logic supervisor_window_done_w;
    logic supervisor_observation_good_w;
    logic supervisor_observation_diverged_w;
    logic supervisor_observation_invalid_w;
    logic supervisor_lock_w;
    logic supervisor_fail_w;
    logic [31:0] acquire_counter_q;
    logic timeout_q;
    logic runtime_fault_q;

    // Registered event request boundary.
    logic event_request_q;
    logic [2:0] event_type_q;
    logic signed [13:0] event_snapshot_out2_q;
    logic signed [13:0] event_snapshot_error_q;
    logic signed [14:0] event_snapshot_lock_error_q;
    logic [1:0] event_snapshot_scan_direction_q;
    logic [1:0] event_snapshot_error_direction_q;
    logic [31:0] event_snapshot_generation_q;
    logic [63:0] event_snapshot_timestamp_q;
    logic [15:0] event_snapshot_reject_q;
    logic [15:0] event_snapshot_fault_q;

    // Raw validation is readback-only. It never drives active-register enables.
    always_comb begin
        raw_fields_complete_w = (config_written_mask_i == 7'h7F);
        raw_signed_fields_valid_w =
            (target_out2_i[31:14] == {18{target_out2_i[13]}}) &&
            (target_error_setpoint_i[31:14] ==
             {18{target_error_setpoint_i[13]}});
        raw_directions_valid_w =
            (target_requirements_i[31:5] == 27'd0) &&
            ((target_requirements_i[1:0] == SCAN_DIR_RISING) ||
             (target_requirements_i[1:0] == SCAN_DIR_FALLING)) &&
            ((target_requirements_i[3:2] == 2'd1) ||
             (target_requirements_i[3:2] == 2'd2));
        raw_polarity_consistent_w =
            target_requirements_i[4] ==
            (target_requirements_i[1:0] == target_requirements_i[3:2]);
        raw_window_valid_w =
            (target_window_i[31:14] == 18'd0) &&
            (target_window_i[13:0] != 14'd0) &&
            (target_window_i[13:0] <= 14'd8191);
        raw_limits_valid_w =
            (correction_limit_i[31:14] == 18'd0) &&
            (absolute_limit_i[31:14] == 18'd0) &&
            (correction_limit_i[13:0] <= absolute_limit_i[13:0]) &&
            (absolute_limit_i[13:0] <= 14'd8191);
        raw_target_ext_w = {{2{target_out2_i[13]}}, target_out2_i[13:0]};
        raw_window_ext_w = {2'd0, target_window_i[13:0]};
        raw_target_low_w = raw_target_ext_w - raw_window_ext_w;
        raw_target_high_w = raw_target_ext_w + raw_window_ext_w;
        raw_absolute_ext_w = {2'd0, absolute_limit_i[13:0]};
        raw_target_range_valid_w =
            (raw_target_low_w >= -16'sd8191) &&
            (raw_target_high_w <= 16'sd8191) &&
            (raw_target_low_w >= -raw_absolute_ext_w) &&
            (raw_target_high_w <= raw_absolute_ext_w);
        raw_runtime_ready_w =
            (state_q == STATE_SCAN) && enable_i && (mode_i == MODE_SCAN) &&
            !saturated_i;
        raw_observe_shift_valid_w =
            (observe_shift_i == EFFECTIVE_OBSERVE_SHIFT);
        raw_base_config_valid_w =
            raw_fields_complete_w && raw_signed_fields_valid_w &&
            raw_directions_valid_w && raw_window_valid_w &&
            raw_limits_valid_w && raw_target_range_valid_w &&
            raw_runtime_ready_w && raw_observe_shift_valid_w;
        raw_active_config_valid_w =
            raw_base_config_valid_w && raw_polarity_consistent_w &&
            (kp_target_i >= 14'sd0);
    end

    // Registered mailbox validation. Only pending registers enter this cone.
    always_comb begin
        pending_fields_complete_w = (pending_written_mask_q == 7'h7F);
        pending_signed_fields_valid_w =
            (pending_target_out2_q[31:14] ==
             {18{pending_target_out2_q[13]}}) &&
            (pending_error_setpoint_q[31:14] ==
             {18{pending_error_setpoint_q[13]}});
        pending_directions_valid_w =
            (pending_requirements_q[31:5] == 27'd0) &&
            ((pending_requirements_q[1:0] == SCAN_DIR_RISING) ||
             (pending_requirements_q[1:0] == SCAN_DIR_FALLING)) &&
            ((pending_requirements_q[3:2] == 2'd1) ||
             (pending_requirements_q[3:2] == 2'd2));
        pending_polarity_consistent_w =
            pending_requirements_q[4] ==
            (pending_requirements_q[1:0] == pending_requirements_q[3:2]);
        pending_window_valid_w =
            (pending_window_q[31:14] == 18'd0) &&
            (pending_window_q[13:0] != 14'd0) &&
            (pending_window_q[13:0] <= 14'd8191);
        pending_limits_valid_w =
            (pending_correction_limit_q[31:14] == 18'd0) &&
            (pending_absolute_limit_q[31:14] == 18'd0) &&
            (pending_correction_limit_q[13:0] <=
             pending_absolute_limit_q[13:0]) &&
            (pending_absolute_limit_q[13:0] <= 14'd8191);
        pending_target_ext_w =
            {{2{pending_target_out2_q[13]}}, pending_target_out2_q[13:0]};
        pending_window_ext_w = {2'd0, pending_window_q[13:0]};
        pending_target_low_w = pending_target_ext_w - pending_window_ext_w;
        pending_target_high_w = pending_target_ext_w + pending_window_ext_w;
        pending_absolute_ext_w = {2'd0, pending_absolute_limit_q[13:0]};
        pending_target_range_valid_w =
            (pending_target_low_w >= -16'sd8191) &&
            (pending_target_high_w <= 16'sd8191) &&
            (pending_target_low_w >= -pending_absolute_ext_w) &&
            (pending_target_high_w <= pending_absolute_ext_w);
        pending_runtime_ready_w =
            (state_q == STATE_SCAN) && enable_i && (mode_i == MODE_SCAN) &&
            !saturated_i;
        pending_observe_shift_valid_w =
            (pending_observe_shift_q == EFFECTIVE_OBSERVE_SHIFT);
        pending_config_valid_w =
            pending_fields_complete_w && pending_signed_fields_valid_w &&
            pending_directions_valid_w && pending_window_valid_w &&
            pending_limits_valid_w && pending_target_range_valid_w &&
            pending_runtime_ready_w && pending_observe_shift_valid_w &&
            (pending_validate_q ||
             (pending_polarity_consistent_w &&
              (pending_kp_target_q >= 14'sd0)));
    end

    // Capture -> registered decision -> accepted commit. Active fields update
    // atomically from one registered transaction and share only arm_accept_pulse.
    always_ff @(posedge clk_i) begin
        if (!rstn_i) begin
            arm_capture_pending_q <= 1'b0;
            arm_decide_pending_q <= 1'b0;
            arm_decision_valid_q <= 1'b0;
            arm_accept_pulse_q <= 1'b0;
            arm_reject_pulse_q <= 1'b0;
            request_accepted_o <= 1'b0;
            active_config_valid_q <= 1'b0;
        end else begin
            arm_capture_pending_q <= 1'b0;
            arm_decide_pending_q <= 1'b0;
            arm_accept_pulse_q <= 1'b0;
            arm_reject_pulse_q <= 1'b0;
            request_accepted_o <= 1'b0;

            if (abort_i || runtime_fault_q) begin
                active_config_valid_q <= 1'b0;
            end else begin
                if ((state_q == STATE_SCAN) &&
                    (request_validate_i || request_active_i)) begin
                    pending_validate_q <= request_validate_i;
                    pending_target_out2_q <= target_out2_i;
                    pending_error_setpoint_q <= target_error_setpoint_i;
                    pending_window_q <= target_window_i;
                    pending_requirements_q <= target_requirements_i;
                    pending_correction_limit_q <= correction_limit_i;
                    pending_absolute_limit_q <= absolute_limit_i;
                    pending_generation_q <= config_generation_i;
                    pending_written_mask_q <= config_written_mask_i;
                    pending_hysteresis_q <=
                        (crossing_hysteresis_i == 14'd0)
                        ? 14'd1 : crossing_hysteresis_i;
                    pending_crossing_samples_q <=
                        (crossing_samples_i == 8'd0)
                        ? 8'd1 : crossing_samples_i;
                    pending_kp_target_q <= kp_target_i;
                    pending_kp_step_q <=
                        (kp_ramp_step_i == 14'd0) ? 14'd1 : kp_ramp_step_i;
                    pending_kp_div_q <=
                        (kp_ramp_div_i == 16'd0) ? 16'd1 : kp_ramp_div_i;
                    pending_timeout_q <=
                        (acquire_timeout_i == 32'd0)
                        ? 32'd1 : acquire_timeout_i;
                    pending_servo_div_q <=
                        (servo_update_div_i == 16'd0)
                        ? 16'd1 : servo_update_div_i;
                    pending_observe_shift_q <= observe_shift_i;
                    pending_confirm_windows_q <=
                        (lock_confirm_windows_i == 8'd0)
                        ? 8'd1 : lock_confirm_windows_i;
                    pending_divergence_windows_q <=
                        (divergence_windows_i == 8'd0)
                        ? 8'd1 : divergence_windows_i;
                    pending_error_mean_limit_q <= error_mean_limit_i;
                    pending_error_abs_limit_q <= error_abs_limit_i;
                    arm_capture_pending_q <= 1'b1;
                end

                if (arm_capture_pending_q) begin
                    arm_decision_valid_q <= pending_config_valid_w;
                    arm_kind_validate_q <= pending_validate_q;
                    arm_decide_pending_q <= 1'b1;
                end

                if (arm_decide_pending_q) begin
                    if (arm_decision_valid_q && pending_runtime_ready_w) begin
                        active_validate_q <= arm_kind_validate_q;
                        active_target_out2_o <= pending_target_out2_q[13:0];
                        active_error_setpoint_o <=
                            pending_error_setpoint_q[13:0];
                        active_window_o <= pending_window_q[13:0];
                        active_requirements_o <= pending_requirements_q;
                        active_correction_limit_o <=
                            pending_correction_limit_q[13:0];
                        active_absolute_limit_o <=
                            pending_absolute_limit_q[13:0];
                        guard_low_q <= pending_target_low_w;
                        guard_high_q <= pending_target_high_w;
                        active_hysteresis_q <= pending_hysteresis_q;
                        active_crossing_samples_q <=
                            pending_crossing_samples_q;
                        active_kp_target_q <= pending_kp_target_q;
                        active_kp_step_q <= pending_kp_step_q;
                        active_kp_div_q <= pending_kp_div_q;
                        active_timeout_q <= pending_timeout_q;
                        active_servo_div_q <= pending_servo_div_q;
                        active_confirm_windows_q <=
                            pending_confirm_windows_q;
                        active_divergence_windows_q <=
                            pending_divergence_windows_q;
                        active_mean_sum_limit_q <=
                            {10'd0, pending_error_mean_limit_q} << 8;
                        active_abs_sum_limit_q <=
                            {10'd0, pending_error_abs_limit_q} << 8;
                        active_divergence_sum_limit_q <=
                            {10'd0, pending_error_abs_limit_q} << 10;
                        active_generation_q <= pending_generation_q;
                        active_config_valid_q <= 1'b1;
                        request_accepted_o <= 1'b1;
                        arm_accept_pulse_q <= 1'b1;
                    end else begin
                        arm_reject_pulse_q <= 1'b1;
                    end
                end
            end
        end
    end

    always_comb begin
        if (out2_i > previous_out2_q)
            scan_direction_now_w = SCAN_DIR_RISING;
        else if (out2_i < previous_out2_q)
            scan_direction_now_w = SCAN_DIR_FALLING;
        else
            scan_direction_now_w = sample_scan_direction_q;

        raw_lock_error_w =
            $signed({error_i[13], error_i}) -
            $signed({active_error_setpoint_o[13],
                     active_error_setpoint_o});
        raw_abs_error_w = raw_lock_error_w[14]
                        ? -raw_lock_error_w : raw_lock_error_w;
        raw_out2_ext_w = {{2{out2_i[13]}}, out2_i};
        raw_in_guard_w = (raw_out2_ext_w >= guard_low_q) &&
                         (raw_out2_ext_w <= guard_high_q);
        raw_direction_match_w =
            scan_direction_valid_q &&
            (scan_direction_now_w == active_requirements_o[1:0]);
        raw_runtime_ok_w =
            enable_i && (mode_i == MODE_SCAN) && !saturated_i &&
            raw_direction_match_w;
    end

    // S0 sample alignment. ERROR, OUT2, setpoint, guard and direction context
    // are captured on the same edge. lock_error and abs are each computed once.
    always_ff @(posedge clk_i) begin
        if (!rstn_i) begin
            previous_out2_q <= 14'sd0;
            sample_scan_direction_q <= 2'd0;
            scan_direction_valid_q <= 1'b0;
            sample_valid_q <= 1'b0;
            in_guard_q <= 1'b0;
            direction_match_q <= 1'b0;
            runtime_ok_q <= 1'b0;
        end else begin
            previous_out2_q <= out2_i;
            sample_out2_q <= out2_i;
            sample_error_q <= error_i;
            sample_setpoint_q <= active_error_setpoint_o;
            sample_lock_error_q <= raw_lock_error_w;
            sample_abs_error_q <= raw_abs_error_w;
            sample_scan_direction_q <= scan_direction_now_w;
            in_guard_q <= raw_in_guard_w;
            direction_match_q <= raw_direction_match_w;
            runtime_ok_q <= raw_runtime_ok_w;
            sample_valid_q <= active_config_valid_q;
            if (out2_i != previous_out2_q)
                scan_direction_valid_q <= 1'b1;
        end
    end

    assign detector_clear_w =
        abort_i || (state_q == STATE_SAFE) || (state_q == STATE_SCAN) ||
        (state_q == STATE_FAILED) || (state_q == STATE_FAULT);

    realtime_error_crossing_detector i_crossing_detector (
        .clk_i(clk_i),
        .rstn_i(rstn_i),
        .clear_i(detector_clear_w),
        .armed_i((state_q == STATE_VALIDATING) ||
                 (state_q == STATE_ARMED)),
        .runtime_ok_i(runtime_ok_q && direction_match_q && sample_valid_q),
        .in_guard_i(in_guard_q),
        .scan_direction_i(sample_scan_direction_q),
        .required_scan_direction_i(active_requirements_o[1:0]),
        .required_error_direction_i(active_requirements_o[3:2]),
        .lock_error_i(sample_lock_error_q),
        .hysteresis_i(active_hysteresis_q),
        .consecutive_samples_i(active_crossing_samples_q),
        .crossing_o(crossing_w),
        .crossing_candidate_o(crossing_candidate_unused_w),
        .source_confirmed_o(source_confirmed_w),
        .pass_consumed_o(pass_consumed_w)
    );

    // Delay the aligned sample beside the detector, then register the detector
    // event once more before the FSM consumes it.
    always_ff @(posedge clk_i) begin
        if (!rstn_i) begin
            crossing_event_q <= 1'b0;
        end else begin
            detector_out2_q <= sample_out2_q;
            detector_error_q <= sample_error_q;
            detector_lock_error_q <= sample_lock_error_q;
            detector_scan_direction_q <= sample_scan_direction_q;
            crossing_event_q <= crossing_w;
            if (crossing_w) begin
                crossing_out2_q <= detector_out2_q;
                crossing_error_q <= detector_error_q;
                crossing_lock_error_q <= detector_lock_error_q;
                crossing_scan_direction_q <= detector_scan_direction_q;
            end
        end
    end

    assign hold_o =
        ((state_q == STATE_ARMED) &&
         (crossing_candidate_unused_w || crossing_w ||
          crossing_event_q || trigger_o)) ||
        ((state_q == STATE_ACQUIRING) && (mode_i == MODE_SCAN));

    assign servo_tick_w =
        (servo_counter_q + 16'd1 >= active_servo_div_q);

    always_ff @(posedge clk_i) begin
        if (!rstn_i) begin
            servo_counter_q <= 16'd0;
        end else if ((state_q != STATE_ACQUIRING) &&
                     (state_q != STATE_P_LOCKED)) begin
            servo_counter_q <= 16'd0;
        end else if (servo_tick_w) begin
            servo_counter_q <= 16'd0;
        end else begin
            servo_counter_q <= servo_counter_q + 16'd1;
        end
    end

    assign kp_stop_w =
        abort_i || runtime_fault_q || timeout_q || supervisor_fail_w ||
        ((state_q != STATE_ACQUIRING) && (state_q != STATE_P_LOCKED));

    l1_kp_ramp i_kp_ramp (
        .clk_i(clk_i),
        .rstn_i(rstn_i),
        .start_i(kp_start_q),
        .stop_i(kp_stop_w),
        .servo_tick_i(servo_tick_w),
        .kp_target_i(active_kp_target_q),
        .kp_step_i(active_kp_step_q),
        .kp_ramp_div_i(active_kp_div_q),
        .kp_effective_o(kp_effective_o),
        .kp_target_reached_o(kp_target_reached_w)
    );

    assign supervisor_stop_w =
        abort_i || runtime_fault_q || timeout_q ||
        (state_q != STATE_ACQUIRING);

    l1_lock_supervisor i_lock_supervisor (
        .clk_i(clk_i),
        .rstn_i(rstn_i),
        .start_i(supervisor_start_q),
        .stop_i(supervisor_stop_w),
        .servo_tick_i(servo_tick_w),
        .lock_error_i(sample_lock_error_q),
        .abs_error_i(sample_abs_error_q),
        .kp_target_reached_i(kp_target_reached_w),
        .mean_sum_limit_i(active_mean_sum_limit_q),
        .abs_sum_limit_i(active_abs_sum_limit_q),
        .divergence_sum_limit_i(active_divergence_sum_limit_q),
        .confirm_windows_i(active_confirm_windows_q),
        .divergence_windows_i(active_divergence_windows_q),
        .window_done_o(supervisor_window_done_w),
        .observation_good_o(supervisor_observation_good_w),
        .observation_diverged_o(supervisor_observation_diverged_w),
        .observation_invalid_o(supervisor_observation_invalid_w),
        .supervisor_lock_o(supervisor_lock_w),
        .supervisor_fail_o(supervisor_fail_w),
        .metrics_o(supervisor_metrics_o)
    );

    // Timeout and runtime hard fault terminate at dedicated registers.
    always_ff @(posedge clk_i) begin
        if (!rstn_i) begin
            acquire_counter_q <= 32'd0;
            timeout_q <= 1'b0;
            runtime_fault_q <= 1'b0;
        end else begin
            runtime_fault_q <=
                (((state_q == STATE_VALIDATING) ||
                  (state_q == STATE_ARMED)) &&
                 (saturated_i || !enable_i || (mode_i != MODE_SCAN))) ||
                (((state_q == STATE_ACQUIRING) ||
                  (state_q == STATE_P_LOCKED)) &&
                 (saturated_i || !enable_i ||
                  ((mode_i != MODE_P_LOCK) &&
                   (acquire_counter_q > 32'd2))));
            if (state_q != STATE_ACQUIRING) begin
                acquire_counter_q <= 32'd0;
                timeout_q <= 1'b0;
            end else if (!timeout_q) begin
                acquire_counter_q <= acquire_counter_q + 32'd1;
                if (acquire_counter_q >= active_timeout_q)
                    timeout_q <= 1'b1;
            end
        end
    end

    // Small acquisition FSM: only registered decisions are consumed here.
    always_ff @(posedge clk_i) begin
        if (!rstn_i) begin
            state_q <= STATE_SAFE;
            cycle_counter_q <= 64'd0;
            trigger_o <= 1'b0;
            fault_immediate_o <= 1'b0;
            trigger_out2_sample_o <= 14'sd0;
            trigger_error_sample_o <= 14'sd0;
            trigger_lock_error_sample_o <= 15'sd0;
            validate_event_count_o <= 32'd0;
            kp_start_q <= 1'b0;
            supervisor_start_q <= 1'b0;
            event_request_q <= 1'b0;
        end else begin
            cycle_counter_q <= cycle_counter_q + 64'd1;
            trigger_o <= 1'b0;
            fault_immediate_o <= 1'b0;
            kp_start_q <= 1'b0;
            supervisor_start_q <= 1'b0;
            event_request_q <= 1'b0;

            if (abort_i) begin
                state_q <= STATE_SAFE;
                event_request_q <= 1'b1;
                event_type_q <= EVENT_ABORTED;
                event_snapshot_out2_q <= sample_out2_q;
                event_snapshot_error_q <= sample_error_q;
                event_snapshot_lock_error_q <= sample_lock_error_q;
                event_snapshot_scan_direction_q <= sample_scan_direction_q;
                event_snapshot_error_direction_q <= 2'd0;
                event_snapshot_generation_q <= active_generation_q;
                event_snapshot_timestamp_q <= cycle_counter_q;
                event_snapshot_reject_q <= 16'd0;
                event_snapshot_fault_q <= 16'd0;
            end else if (runtime_fault_q) begin
                state_q <= STATE_FAULT;
                fault_immediate_o <= 1'b1;
                event_request_q <= 1'b1;
                event_type_q <= EVENT_FAULT;
                event_snapshot_out2_q <= sample_out2_q;
                event_snapshot_error_q <= sample_error_q;
                event_snapshot_lock_error_q <= sample_lock_error_q;
                event_snapshot_scan_direction_q <= sample_scan_direction_q;
                event_snapshot_error_direction_q <=
                    active_requirements_o[3:2];
                event_snapshot_generation_q <= active_generation_q;
                event_snapshot_timestamp_q <= cycle_counter_q;
                event_snapshot_reject_q <= 16'd0;
                event_snapshot_fault_q <= FAULT_RUNTIME;
            end else if (timeout_q) begin
                state_q <= STATE_FAILED;
                fault_immediate_o <= 1'b1;
                event_request_q <= 1'b1;
                event_type_q <= EVENT_FAULT;
                event_snapshot_out2_q <= sample_out2_q;
                event_snapshot_error_q <= sample_error_q;
                event_snapshot_lock_error_q <= sample_lock_error_q;
                event_snapshot_scan_direction_q <= sample_scan_direction_q;
                event_snapshot_error_direction_q <=
                    active_requirements_o[3:2];
                event_snapshot_generation_q <= active_generation_q;
                event_snapshot_timestamp_q <= cycle_counter_q;
                event_snapshot_reject_q <= 16'd0;
                event_snapshot_fault_q <= FAULT_TIMEOUT;
            end else if (supervisor_fail_w) begin
                state_q <= STATE_FAILED;
                fault_immediate_o <= 1'b1;
                event_request_q <= 1'b1;
                event_type_q <= EVENT_FAULT;
                event_snapshot_out2_q <= sample_out2_q;
                event_snapshot_error_q <= sample_error_q;
                event_snapshot_lock_error_q <= sample_lock_error_q;
                event_snapshot_scan_direction_q <= sample_scan_direction_q;
                event_snapshot_error_direction_q <=
                    active_requirements_o[3:2];
                event_snapshot_generation_q <= active_generation_q;
                event_snapshot_timestamp_q <= cycle_counter_q;
                event_snapshot_reject_q <= 16'd0;
                event_snapshot_fault_q <= supervisor_observation_invalid_w
                                       ? FAULT_OVERFLOW
                                       : FAULT_DIVERGENCE;
            end else begin
                unique case (state_q)
                    STATE_SAFE: begin
                        if (enable_i && (mode_i == MODE_SCAN) &&
                            !saturated_i)
                            state_q <= STATE_SCAN;
                    end
                    STATE_SCAN: begin
                        if (!enable_i || (mode_i == MODE_SAFE)) begin
                            state_q <= STATE_SAFE;
                        end else if (arm_accept_pulse_q) begin
                            state_q <= active_validate_q
                                     ? STATE_VALIDATING : STATE_ARMED;
                        end else if (arm_reject_pulse_q) begin
                            event_request_q <= 1'b1;
                            event_type_q <= EVENT_CONFIG_REJECTED;
                            event_snapshot_out2_q <= sample_out2_q;
                            event_snapshot_error_q <= sample_error_q;
                            event_snapshot_lock_error_q <= sample_lock_error_q;
                            event_snapshot_scan_direction_q <=
                                sample_scan_direction_q;
                            event_snapshot_error_direction_q <=
                                pending_requirements_q[3:2];
                            event_snapshot_generation_q <= pending_generation_q;
                            event_snapshot_timestamp_q <= cycle_counter_q;
                            event_snapshot_reject_q <=
                                pending_observe_shift_valid_w
                                ? (pending_polarity_consistent_w
                                   ? REJECT_CONFIG : REJECT_POLARITY)
                                : REJECT_OBSERVE_SHIFT;
                            event_snapshot_fault_q <= 16'd0;
                        end
                    end
                    STATE_VALIDATING: begin
                        if (crossing_event_q) begin
                            validate_event_count_o <=
                                validate_event_count_o + 32'd1;
                            event_request_q <= 1'b1;
                            event_type_q <= EVENT_VALIDATED;
                            event_snapshot_out2_q <= crossing_out2_q;
                            event_snapshot_error_q <= crossing_error_q;
                            event_snapshot_lock_error_q <=
                                crossing_lock_error_q;
                            event_snapshot_scan_direction_q <=
                                crossing_scan_direction_q;
                            event_snapshot_error_direction_q <=
                                active_requirements_o[3:2];
                            event_snapshot_generation_q <= active_generation_q;
                            event_snapshot_timestamp_q <= cycle_counter_q;
                            event_snapshot_reject_q <= 16'd0;
                            event_snapshot_fault_q <= 16'd0;
                        end
                    end
                    STATE_ARMED: begin
                        if (crossing_event_q) begin
                            trigger_o <= 1'b1;
                            trigger_out2_sample_o <= crossing_out2_q;
                            trigger_error_sample_o <= crossing_error_q;
                            trigger_lock_error_sample_o <=
                                crossing_lock_error_q;
                            kp_start_q <= 1'b1;
                            supervisor_start_q <= 1'b1;
                            event_request_q <= 1'b1;
                            event_type_q <= EVENT_TRIGGERED;
                            event_snapshot_out2_q <= crossing_out2_q;
                            event_snapshot_error_q <= crossing_error_q;
                            event_snapshot_lock_error_q <=
                                crossing_lock_error_q;
                            event_snapshot_scan_direction_q <=
                                crossing_scan_direction_q;
                            event_snapshot_error_direction_q <=
                                active_requirements_o[3:2];
                            event_snapshot_generation_q <= active_generation_q;
                            event_snapshot_timestamp_q <= cycle_counter_q;
                            event_snapshot_reject_q <= 16'd0;
                            event_snapshot_fault_q <= 16'd0;
                            state_q <= STATE_ACQUIRING;
                        end
                    end
                    STATE_ACQUIRING: begin
                        if (supervisor_lock_w)
                            state_q <= STATE_P_LOCKED;
                    end
                    STATE_P_LOCKED: begin
                    end
                    STATE_FAILED,
                    STATE_FAULT: begin
                    end
                    default: state_q <= STATE_SAFE;
                endcase
            end
        end
    end

    l1_event_recorder i_event_recorder (
        .clk_i(clk_i),
        .rstn_i(rstn_i),
        .clear_i(clear_event_i),
        .request_i(event_request_q),
        .type_i(event_type_q),
        .out2_i(event_snapshot_out2_q),
        .error_i(event_snapshot_error_q),
        .lock_error_i(event_snapshot_lock_error_q),
        .scan_direction_i(event_snapshot_scan_direction_q),
        .error_direction_i(event_snapshot_error_direction_q),
        .generation_i(event_snapshot_generation_q),
        .timestamp_i(event_snapshot_timestamp_q),
        .reject_code_i(event_snapshot_reject_q),
        .fault_code_i(event_snapshot_fault_q),
        .sequence_o(event_sequence_o),
        .out2_o(event_out2_o),
        .error_o(event_error_o),
        .lock_error_o(event_lock_error_o),
        .generation_o(event_config_generation_o),
        .info_o(event_info_o),
        .timestamp_lo_o(event_timestamp_lo_o),
        .timestamp_hi_o(event_timestamp_hi_o),
        .fault_detail_o(fault_detail_o)
    );

    always_comb begin
        config_validation_o = 32'd0;
        config_validation_o[0] = raw_fields_complete_w;
        config_validation_o[1] = raw_signed_fields_valid_w;
        config_validation_o[2] = raw_directions_valid_w;
        config_validation_o[3] = raw_window_valid_w;
        config_validation_o[4] = raw_limits_valid_w;
        config_validation_o[5] = raw_target_range_valid_w;
        config_validation_o[6] = raw_runtime_ready_w;
        config_validation_o[7] = raw_active_config_valid_w;
        config_validation_o[14:8] = config_written_mask_i;
        config_validation_o[15] = 1'b1;
        config_validation_o[16] = raw_polarity_consistent_w;

        state_readback_o = 32'd0;
        state_readback_o[2:0] = state_q;
        state_readback_o[8] = event_info_o[0];
        state_readback_o[9] = (state_q == STATE_VALIDATING);
        state_readback_o[10] = (state_q == STATE_ARMED);
        state_readback_o[11] = (state_q == STATE_ACQUIRING);
        state_readback_o[12] = (state_q == STATE_P_LOCKED);
        state_readback_o[13] = scan_direction_valid_q;
        state_readback_o[15:14] = sample_scan_direction_q;
        state_readback_o[16] = source_confirmed_w;
        state_readback_o[17] = pass_consumed_w;
        state_readback_o[18] = (state_q == STATE_FAILED);
        state_readback_o[19] = (state_q == STATE_FAULT);
        state_readback_o[20] = active_config_valid_q;
        state_readback_o[21] = supervisor_window_done_w;
    end
endmodule
