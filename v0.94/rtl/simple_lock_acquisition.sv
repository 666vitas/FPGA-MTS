`timescale 1ns/1ps
`include "realtime_error_crossing_detector.sv"

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
    localparam logic [15:0] FAULT_RUNTIME = 16'h0001;
    localparam logic [15:0] FAULT_TIMEOUT = 16'h0002;
    localparam logic [15:0] FAULT_DIVERGENCE = 16'h0004;

    logic [2:0] state_q;
    logic signed [13:0] previous_out2_q;
    logic [1:0] scan_direction_q;
    logic scan_direction_valid_q;
    logic signed [15:0] guard_low_q;
    logic signed [15:0] guard_high_q;
    logic signed [14:0] lock_error_w;
    logic signed [15:0] out2_ext_w;
    logic in_guard_w;
    logic direction_match_w;
    logic detector_runtime_ok_w;
    logic detector_clear_w;
    logic crossing_w;
    logic crossing_candidate_w;
    logic source_confirmed_w;
    logic pass_consumed_w;

    logic fields_complete_w;
    logic signed_fields_valid_w;
    logic directions_valid_w;
    logic window_valid_w;
    logic limits_valid_w;
    logic target_range_valid_w;
    logic runtime_ready_w;
    logic polarity_consistent_w;
    logic base_config_valid_w;
    logic active_config_valid_w;
    logic signed [15:0] target_ext_w;
    logic signed [15:0] window_ext_w;
    logic signed [15:0] target_low_w;
    logic signed [15:0] target_high_w;
    logic signed [15:0] absolute_ext_w;
    logic [1:0] scan_direction_now_w;

    logic active_validate_q;
    logic [13:0] active_crossing_hysteresis_q;
    logic [7:0] active_crossing_samples_q;
    logic signed [13:0] active_kp_target_q;
    logic [13:0] active_kp_ramp_step_q;
    logic [15:0] active_kp_ramp_div_q;
    logic [31:0] active_timeout_q;
    logic [15:0] active_servo_div_q;
    logic [7:0] active_observe_shift_q;
    logic [7:0] active_confirm_windows_q;
    logic [7:0] active_divergence_windows_q;
    logic [13:0] active_error_mean_limit_q;
    logic [13:0] active_error_abs_limit_q;

    logic [63:0] cycle_counter_q;
    logic [31:0] acquire_counter_q;
    logic [15:0] servo_counter_q;
    logic servo_tick_w;
    logic [15:0] kp_ramp_counter_q;
    logic [31:0] observe_count_q;
    logic signed [47:0] error_sum_q;
    logic [47:0] error_abs_sum_q;
    logic [7:0] confirm_count_q;
    logic [7:0] divergence_count_q;
    logic signed [15:0] lock_error_ext_w;
    logic [15:0] abs_lock_error_w;
    logic [31:0] observe_length_w;
    logic signed [47:0] error_mean_w;
    logic [47:0] error_abs_mean_w;
    logic signed [47:0] error_sum_next_w;
    logic [47:0] error_abs_sum_next_w;
    logic observation_good_w;
    logic observation_diverged_w;

    logic event_valid_q;
    logic [2:0] event_type_q;
    logic [1:0] event_scan_direction_q;
    logic [1:0] event_error_direction_q;
    logic [15:0] reject_code_q;
    logic [15:0] fault_code_q;

    always_comb begin
        fields_complete_w = (config_written_mask_i == 7'h7F);
        signed_fields_valid_w =
            (target_out2_i[31:14] == {18{target_out2_i[13]}}) &&
            (target_error_setpoint_i[31:14] == {18{target_error_setpoint_i[13]}});
        directions_valid_w =
            (target_requirements_i[31:5] == 27'd0) &&
            ((target_requirements_i[1:0] == SCAN_DIR_RISING) ||
             (target_requirements_i[1:0] == SCAN_DIR_FALLING)) &&
            ((target_requirements_i[3:2] == 2'd1) ||
             (target_requirements_i[3:2] == 2'd2));
        polarity_consistent_w =
            target_requirements_i[4] ==
            (target_requirements_i[1:0] == target_requirements_i[3:2]);
        window_valid_w =
            (target_window_i[31:14] == 18'd0) &&
            (target_window_i[13:0] != 14'd0) &&
            (target_window_i[13:0] <= 14'd8191);
        limits_valid_w =
            (correction_limit_i[31:14] == 18'd0) &&
            (absolute_limit_i[31:14] == 18'd0) &&
            (correction_limit_i[13:0] <= absolute_limit_i[13:0]) &&
            (absolute_limit_i[13:0] <= 14'd8191);
        target_ext_w = {{2{target_out2_i[13]}}, target_out2_i[13:0]};
        window_ext_w = {2'd0, target_window_i[13:0]};
        target_low_w = target_ext_w - window_ext_w;
        target_high_w = target_ext_w + window_ext_w;
        absolute_ext_w = {2'd0, absolute_limit_i[13:0]};
        target_range_valid_w =
            (target_low_w >= -16'sd8191) &&
            (target_high_w <= 16'sd8191) &&
            (target_low_w >= -absolute_ext_w) &&
            (target_high_w <= absolute_ext_w);
        runtime_ready_w =
            (state_q == STATE_SCAN) && enable_i && (mode_i == MODE_SCAN) &&
            !saturated_i;
        base_config_valid_w =
            fields_complete_w && signed_fields_valid_w && directions_valid_w &&
            window_valid_w && limits_valid_w && target_range_valid_w &&
            runtime_ready_w;
        active_config_valid_w = base_config_valid_w && polarity_consistent_w;
    end

    always_comb begin
        if (out2_i > previous_out2_q)
            scan_direction_now_w = SCAN_DIR_RISING;
        else if (out2_i < previous_out2_q)
            scan_direction_now_w = SCAN_DIR_FALLING;
        else
            scan_direction_now_w = scan_direction_q;
        out2_ext_w = {{2{out2_i[13]}}, out2_i};
        in_guard_w = (out2_ext_w >= guard_low_q) &&
                     (out2_ext_w <= guard_high_q);
        direction_match_w =
            scan_direction_valid_q &&
            (scan_direction_now_w == active_requirements_o[1:0]);
        lock_error_w =
            $signed({error_i[13], error_i}) -
            $signed({active_error_setpoint_o[13], active_error_setpoint_o});
        detector_runtime_ok_w =
            enable_i && (mode_i == MODE_SCAN) && !saturated_i &&
            direction_match_w;
        detector_clear_w =
            abort_i || (state_q == STATE_SAFE) || (state_q == STATE_SCAN) ||
            (state_q == STATE_FAILED) || (state_q == STATE_FAULT);
    end

    realtime_error_crossing_detector i_crossing_detector (
        .clk_i(clk_i),
        .rstn_i(rstn_i),
        .clear_i(detector_clear_w),
        .armed_i((state_q == STATE_VALIDATING) || (state_q == STATE_ARMED)),
        .runtime_ok_i(detector_runtime_ok_w),
        .in_guard_i(in_guard_w),
        .scan_direction_i(scan_direction_now_w),
        .required_scan_direction_i(active_requirements_o[1:0]),
        .required_error_direction_i(active_requirements_o[3:2]),
        .lock_error_i(lock_error_w),
        .hysteresis_i(active_crossing_hysteresis_q),
        .consecutive_samples_i(active_crossing_samples_q),
        .crossing_o(crossing_w),
        .crossing_candidate_o(crossing_candidate_w),
        .source_confirmed_o(source_confirmed_w),
        .pass_consumed_o(pass_consumed_w)
    );

    assign hold_o = trigger_o ||
                    ((state_q == STATE_ARMED) &&
                     (crossing_candidate_w || crossing_w));
    assign servo_tick_w = (servo_counter_q + 16'd1 >=
                           ((active_servo_div_q == 16'd0) ? 16'd1 : active_servo_div_q));

    always_comb begin
        lock_error_ext_w = {{1{lock_error_w[14]}}, lock_error_w};
        abs_lock_error_w = lock_error_ext_w[15] ? -lock_error_ext_w : lock_error_ext_w;
        observe_length_w = 32'd1 << ((active_observe_shift_q > 8'd20)
                                  ? 8'd20 : active_observe_shift_q);
        error_sum_next_w = error_sum_q + lock_error_ext_w;
        error_abs_sum_next_w = error_abs_sum_q + abs_lock_error_w;
        error_mean_w = error_sum_next_w >>> ((active_observe_shift_q > 8'd20)
                                     ? 8'd20 : active_observe_shift_q);
        error_abs_mean_w = error_abs_sum_next_w >> ((active_observe_shift_q > 8'd20)
                                            ? 8'd20 : active_observe_shift_q);
        observation_good_w =
            (($signed(error_mean_w) < $signed({1'b0, active_error_mean_limit_q})) &&
             ($signed(error_mean_w) > -$signed({1'b0, active_error_mean_limit_q}))) &&
            (error_abs_mean_w < active_error_abs_limit_q) && !saturated_i;
        observation_diverged_w =
            (error_abs_mean_w >= ({34'd0, active_error_abs_limit_q} << 2));
    end

    always_ff @(posedge clk_i) begin
        if (!rstn_i) begin
            state_q <= STATE_SAFE;
            previous_out2_q <= 14'sd0;
            scan_direction_q <= 2'd0;
            scan_direction_valid_q <= 1'b0;
            guard_low_q <= 16'sd0;
            guard_high_q <= 16'sd0;
            active_validate_q <= 1'b0;
            active_crossing_hysteresis_q <= 14'd4;
            active_crossing_samples_q <= 8'd3;
            active_target_out2_o <= 14'sd0;
            active_error_setpoint_o <= 14'sd0;
            active_window_o <= 14'd0;
            active_requirements_o <= 32'd0;
            active_correction_limit_o <= 14'd0;
            active_absolute_limit_o <= 14'd0;
            active_kp_target_q <= 14'sd0;
            active_kp_ramp_step_q <= 14'd1;
            active_kp_ramp_div_q <= 16'd1;
            active_timeout_q <= 32'd12500000;
            active_servo_div_q <= 16'd125;
            active_observe_shift_q <= 8'd8;
            active_confirm_windows_q <= 8'd4;
            active_divergence_windows_q <= 8'd4;
            active_error_mean_limit_q <= 14'd16;
            active_error_abs_limit_q <= 14'd32;
            trigger_o <= 1'b0;
            fault_immediate_o <= 1'b0;
            request_accepted_o <= 1'b0;
            trigger_out2_sample_o <= 14'sd0;
            trigger_error_sample_o <= 14'sd0;
            trigger_lock_error_sample_o <= 15'sd0;
            kp_effective_o <= 14'sd0;
            validate_event_count_o <= 32'd0;
            supervisor_metrics_o <= 32'd0;
            cycle_counter_q <= 64'd0;
            acquire_counter_q <= 32'd0;
            servo_counter_q <= 16'd0;
            kp_ramp_counter_q <= 16'd0;
            observe_count_q <= 32'd0;
            error_sum_q <= 48'sd0;
            error_abs_sum_q <= 48'd0;
            confirm_count_q <= 8'd0;
            divergence_count_q <= 8'd0;
            event_sequence_o <= 32'd0;
            event_out2_o <= 32'd0;
            event_error_o <= 32'd0;
            event_lock_error_o <= 32'sd0;
            event_config_generation_o <= 32'd0;
            event_timestamp_lo_o <= 32'd0;
            event_timestamp_hi_o <= 32'd0;
            event_valid_q <= 1'b0;
            event_type_q <= 3'd0;
            event_scan_direction_q <= 2'd0;
            event_error_direction_q <= 2'd0;
            reject_code_q <= 16'd0;
            fault_code_q <= 16'd0;
        end else begin
            cycle_counter_q <= cycle_counter_q + 64'd1;
            trigger_o <= 1'b0;
            fault_immediate_o <= 1'b0;
            request_accepted_o <= 1'b0;
            previous_out2_q <= out2_i;
            if (out2_i != previous_out2_q) begin
                scan_direction_q <= scan_direction_now_w;
                scan_direction_valid_q <= 1'b1;
            end

            if (abort_i) begin
                state_q <= STATE_SAFE;
                kp_effective_o <= 14'sd0;
                event_valid_q <= 1'b1;
                event_type_q <= EVENT_ABORTED;
                event_sequence_o <= event_sequence_o + 32'd1;
                event_out2_o <= {{18{out2_i[13]}}, out2_i};
                event_error_o <= {{18{error_i[13]}}, error_i};
                event_lock_error_o <= {{17{lock_error_w[14]}}, lock_error_w};
                event_timestamp_lo_o <= cycle_counter_q[31:0];
                event_timestamp_hi_o <= cycle_counter_q[63:32];
                fault_code_q <= 16'd0;
                reject_code_q <= 16'd0;
            end else if (((state_q == STATE_VALIDATING) || (state_q == STATE_ARMED)) &&
                         (saturated_i || !enable_i || (mode_i != MODE_SCAN))) begin
                state_q <= STATE_FAULT;
                kp_effective_o <= 14'sd0;
                fault_immediate_o <= 1'b1;
                fault_code_q <= FAULT_RUNTIME;
                event_valid_q <= 1'b1;
                event_type_q <= EVENT_FAULT;
                event_sequence_o <= event_sequence_o + 32'd1;
            end else if ((state_q == STATE_ACQUIRING || state_q == STATE_P_LOCKED) &&
                         (saturated_i || !enable_i ||
                          ((mode_i != MODE_P_LOCK) && (acquire_counter_q > 32'd2)))) begin
                state_q <= STATE_FAULT;
                kp_effective_o <= 14'sd0;
                fault_immediate_o <= 1'b1;
                fault_code_q <= FAULT_RUNTIME;
                event_valid_q <= 1'b1;
                event_type_q <= EVENT_FAULT;
                event_sequence_o <= event_sequence_o + 32'd1;
            end else begin
                unique case (state_q)
                    STATE_SAFE: begin
                        kp_effective_o <= 14'sd0;
                        if (enable_i && (mode_i == MODE_SCAN) && !saturated_i)
                            state_q <= STATE_SCAN;
                    end
                    STATE_SCAN: begin
                        kp_effective_o <= 14'sd0;
                        if (!enable_i || (mode_i == MODE_SAFE)) begin
                            state_q <= STATE_SAFE;
                        end else if (request_validate_i || request_active_i) begin
                            if (base_config_valid_w &&
                                (request_validate_i ||
                                 (active_config_valid_w && (kp_target_i >= 14'sd0)))) begin
                                active_validate_q <= request_validate_i;
                                active_crossing_hysteresis_q <=
                                    (crossing_hysteresis_i == 14'd0)
                                    ? 14'd1 : crossing_hysteresis_i;
                                active_crossing_samples_q <=
                                    (crossing_samples_i == 8'd0)
                                    ? 8'd1 : crossing_samples_i;
                                active_target_out2_o <= target_out2_i[13:0];
                                active_error_setpoint_o <= target_error_setpoint_i[13:0];
                                active_window_o <= target_window_i[13:0];
                                active_requirements_o <= target_requirements_i;
                                active_correction_limit_o <= correction_limit_i[13:0];
                                active_absolute_limit_o <= absolute_limit_i[13:0];
                                guard_low_q <= target_low_w;
                                guard_high_q <= target_high_w;
                                active_kp_target_q <= kp_target_i;
                                active_kp_ramp_step_q <= (kp_ramp_step_i == 14'd0)
                                                       ? 14'd1 : kp_ramp_step_i;
                                active_kp_ramp_div_q <= (kp_ramp_div_i == 16'd0)
                                                      ? 16'd1 : kp_ramp_div_i;
                                active_timeout_q <= (acquire_timeout_i == 32'd0)
                                                  ? 32'd1 : acquire_timeout_i;
                                active_servo_div_q <= (servo_update_div_i == 16'd0)
                                                    ? 16'd1 : servo_update_div_i;
                                active_observe_shift_q <= observe_shift_i;
                                active_confirm_windows_q <= (lock_confirm_windows_i == 8'd0)
                                                          ? 8'd1 : lock_confirm_windows_i;
                                active_divergence_windows_q <= (divergence_windows_i == 8'd0)
                                                             ? 8'd1 : divergence_windows_i;
                                active_error_mean_limit_q <= error_mean_limit_i;
                                active_error_abs_limit_q <= error_abs_limit_i;
                                event_config_generation_o <= config_generation_i;
                                request_accepted_o <= 1'b1;
                                reject_code_q <= 16'd0;
                                fault_code_q <= 16'd0;
                                state_q <= request_validate_i
                                         ? STATE_VALIDATING : STATE_ARMED;
                            end else begin
                                event_valid_q <= 1'b1;
                                event_type_q <= EVENT_CONFIG_REJECTED;
                                event_sequence_o <= event_sequence_o + 32'd1;
                                event_config_generation_o <= config_generation_i;
                                reject_code_q <= base_config_valid_w
                                               ? REJECT_POLARITY : REJECT_CONFIG;
                            end
                        end
                    end
                    STATE_VALIDATING: begin
                        if (crossing_candidate_w) begin
                            validate_event_count_o <= validate_event_count_o + 32'd1;
                            event_sequence_o <= event_sequence_o + 32'd1;
                            event_valid_q <= 1'b1;
                            event_type_q <= EVENT_VALIDATED;
                            event_out2_o <= {{18{out2_i[13]}}, out2_i};
                            event_error_o <= {{18{error_i[13]}}, error_i};
                            event_lock_error_o <= {{17{lock_error_w[14]}}, lock_error_w};
                            event_scan_direction_q <= scan_direction_now_w;
                            event_error_direction_q <= active_requirements_o[3:2];
                            event_timestamp_lo_o <= cycle_counter_q[31:0];
                            event_timestamp_hi_o <= cycle_counter_q[63:32];
                        end
                    end
                    STATE_ARMED: begin
                        if (crossing_candidate_w) begin
                            trigger_o <= 1'b1;
                            trigger_out2_sample_o <= out2_i;
                            trigger_error_sample_o <= error_i;
                            trigger_lock_error_sample_o <= lock_error_w;
                            kp_effective_o <= 14'sd0;
                            acquire_counter_q <= 32'd0;
                            servo_counter_q <= 16'd0;
                            kp_ramp_counter_q <= 16'd0;
                            observe_count_q <= 32'd0;
                            error_sum_q <= 48'sd0;
                            error_abs_sum_q <= 48'd0;
                            confirm_count_q <= 8'd0;
                            divergence_count_q <= 8'd0;
                            event_sequence_o <= event_sequence_o + 32'd1;
                            event_valid_q <= 1'b1;
                            event_type_q <= EVENT_TRIGGERED;
                            event_out2_o <= {{18{out2_i[13]}}, out2_i};
                            event_error_o <= {{18{error_i[13]}}, error_i};
                            event_lock_error_o <= {{17{lock_error_w[14]}}, lock_error_w};
                            event_scan_direction_q <= scan_direction_now_w;
                            event_error_direction_q <= active_requirements_o[3:2];
                            event_timestamp_lo_o <= cycle_counter_q[31:0];
                            event_timestamp_hi_o <= cycle_counter_q[63:32];
                            state_q <= STATE_ACQUIRING;
                        end
                    end
                    STATE_ACQUIRING: begin
                        acquire_counter_q <= acquire_counter_q + 32'd1;
                        if (acquire_counter_q >= active_timeout_q) begin
                            state_q <= STATE_FAILED;
                            kp_effective_o <= 14'sd0;
                            fault_immediate_o <= 1'b1;
                            fault_code_q <= FAULT_TIMEOUT;
                        end else if (servo_tick_w) begin
                            servo_counter_q <= 16'd0;
                            if (kp_ramp_counter_q + 16'd1 >= active_kp_ramp_div_q) begin
                                kp_ramp_counter_q <= 16'd0;
                                if (kp_effective_o < active_kp_target_q) begin
                                    if ($signed({1'b0, kp_effective_o}) +
                                        $signed({1'b0, active_kp_ramp_step_q}) >=
                                        $signed({1'b0, active_kp_target_q}))
                                        kp_effective_o <= active_kp_target_q;
                                    else
                                        kp_effective_o <= kp_effective_o +
                                                          active_kp_ramp_step_q;
                                end
                            end else begin
                                kp_ramp_counter_q <= kp_ramp_counter_q + 16'd1;
                            end

                            if (observe_count_q + 32'd1 >= observe_length_w) begin
                                observe_count_q <= 32'd0;
                                supervisor_metrics_o[13:0] <= error_abs_mean_w[13:0];
                                supervisor_metrics_o[21:14] <= confirm_count_q;
                                supervisor_metrics_o[29:22] <= divergence_count_q;
                                error_sum_q <= 48'sd0;
                                error_abs_sum_q <= 48'd0;
                                if (observation_good_w &&
                                    (kp_effective_o == active_kp_target_q)) begin
                                    divergence_count_q <= 8'd0;
                                    if (confirm_count_q + 8'd1 >= active_confirm_windows_q) begin
                                        confirm_count_q <= active_confirm_windows_q;
                                        state_q <= STATE_P_LOCKED;
                                    end else begin
                                        confirm_count_q <= confirm_count_q + 8'd1;
                                    end
                                end else begin
                                    confirm_count_q <= 8'd0;
                                    if (observation_diverged_w) begin
                                        if (divergence_count_q + 8'd1 >=
                                            active_divergence_windows_q) begin
                                            state_q <= STATE_FAILED;
                                            kp_effective_o <= 14'sd0;
                                            fault_immediate_o <= 1'b1;
                                            fault_code_q <= FAULT_DIVERGENCE;
                                        end else begin
                                            divergence_count_q <= divergence_count_q + 8'd1;
                                        end
                                    end else begin
                                        divergence_count_q <= 8'd0;
                                    end
                                end
                            end else begin
                                observe_count_q <= observe_count_q + 32'd1;
                                error_sum_q <= error_sum_q + lock_error_ext_w;
                                error_abs_sum_q <= error_abs_sum_q + abs_lock_error_w;
                            end
                        end else begin
                            servo_counter_q <= servo_counter_q + 16'd1;
                        end
                    end
                    STATE_P_LOCKED: begin
                        if (servo_tick_w)
                            servo_counter_q <= 16'd0;
                        else
                            servo_counter_q <= servo_counter_q + 16'd1;
                    end
                    STATE_FAILED,
                    STATE_FAULT: kp_effective_o <= 14'sd0;
                    default: state_q <= STATE_SAFE;
                endcase
            end

            if (clear_event_i) begin
                event_valid_q <= 1'b0;
                event_type_q <= 3'd0;
                reject_code_q <= 16'd0;
                if ((state_q != STATE_FAILED) && (state_q != STATE_FAULT))
                    fault_code_q <= 16'd0;
            end
        end
    end

    always_comb begin
        config_validation_o = 32'd0;
        config_validation_o[0] = fields_complete_w;
        config_validation_o[1] = signed_fields_valid_w;
        config_validation_o[2] = directions_valid_w;
        config_validation_o[3] = window_valid_w;
        config_validation_o[4] = limits_valid_w;
        config_validation_o[5] = target_range_valid_w;
        config_validation_o[6] = runtime_ready_w;
        config_validation_o[7] = active_config_valid_w;
        config_validation_o[14:8] = config_written_mask_i;
        config_validation_o[15] = 1'b1;
        config_validation_o[16] = polarity_consistent_w;

        state_readback_o = 32'd0;
        state_readback_o[2:0] = state_q;
        state_readback_o[8] = event_valid_q;
        state_readback_o[9] = (state_q == STATE_VALIDATING);
        state_readback_o[10] = (state_q == STATE_ARMED);
        state_readback_o[11] = (state_q == STATE_ACQUIRING);
        state_readback_o[12] = (state_q == STATE_P_LOCKED);
        state_readback_o[13] = scan_direction_valid_q;
        state_readback_o[15:14] = scan_direction_now_w;
        state_readback_o[16] = source_confirmed_w;
        state_readback_o[17] = pass_consumed_w;
        state_readback_o[18] = (state_q == STATE_FAILED);
        state_readback_o[19] = (state_q == STATE_FAULT);

        event_info_o = 32'd0;
        event_info_o[0] = event_valid_q;
        event_info_o[3:1] = event_type_q;
        event_info_o[5:4] = event_scan_direction_q;
        event_info_o[7:6] = event_error_direction_q;
        event_info_o[23:16] = fault_code_q[7:0];
        fault_detail_o = {fault_code_q, reject_code_q};
    end
endmodule
