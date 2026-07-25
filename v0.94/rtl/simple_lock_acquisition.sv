`timescale 1ns/1ps

module simple_lock_acquisition (
    input  logic               clk_i,
    input  logic               rstn_i,
    input  logic        [31:0] mode_i,
    input  logic               enable_i,
    input  logic               saturated_i,
    input  logic signed [13:0] out2_i,
    input  logic signed [13:0] error_i,
    input  logic signed [13:0] kp_i,
    input  logic        [31:0] target_out2_i,
    input  logic        [31:0] target_error_setpoint_i,
    input  logic        [31:0] target_window_i,
    input  logic        [31:0] target_requirements_i,
    input  logic        [31:0] correction_limit_i,
    input  logic        [31:0] absolute_limit_i,
    input  logic        [31:0] config_generation_i,
    input  logic         [6:0] config_written_mask_i,
    input  logic               request_i,
    input  logic               abort_i,
    input  logic               clear_event_i,
    output logic               trigger_o,
    output logic               hold_o,
    output logic               fault_immediate_o,
    output logic               request_accepted_o,
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

    localparam logic [2:0] STATE_SAFE          = 3'd0;
    localparam logic [2:0] STATE_SCAN          = 3'd1;
    localparam logic [2:0] STATE_ARMED         = 3'd2;
    localparam logic [2:0] STATE_P_LOCK_KP0    = 3'd4;
    localparam logic [2:0] STATE_P_LOCK_ACTIVE = 3'd5;
    localparam logic [2:0] STATE_FAULT         = 3'd6;

    localparam logic [1:0] SCAN_DIR_RISING  = 2'd1;
    localparam logic [1:0] SCAN_DIR_FALLING = 2'd2;
    localparam logic [2:0] EVENT_TRIGGERED  = 3'd2;
    localparam logic [15:0] FAULT_RUNTIME_SAFETY = 16'h0001;

    logic [2:0] state_q;
    logic request_q;
    logic signed [13:0] previous_out2_q;
    logic [1:0] scan_direction_q;
    logic scan_direction_valid_q;
    logic event_valid_q;
    logic [15:0] fault_code_q;

    logic fields_complete_w;
    logic signed_fields_valid_w;
    logic directions_valid_w;
    logic window_valid_w;
    logic limits_valid_w;
    logic target_range_valid_w;
    logic runtime_ready_w;
    logic config_valid_w;
    logic signed [15:0] target_ext_w;
    logic signed [15:0] window_ext_w;
    logic signed [15:0] target_low_w;
    logic signed [15:0] target_high_w;
    logic signed [15:0] absolute_ext_w;
    logic signed [15:0] out2_ext_w;
    logic [1:0] scan_direction_now_w;
    logic scan_direction_now_valid_w;
    logic direction_match_w;
    logic inside_window_w;
    logic trigger_candidate_w;
    logic fault_candidate_w;

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
        config_valid_w =
            fields_complete_w && signed_fields_valid_w && directions_valid_w &&
            window_valid_w && limits_valid_w && target_range_valid_w &&
            runtime_ready_w;
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
        inside_window_w =
            (out2_ext_w >= target_low_w) && (out2_ext_w <= target_high_w);
        direction_match_w =
            scan_direction_now_valid_w &&
            (scan_direction_now_w == target_requirements_i[1:0]);
    end

    assign fault_candidate_w =
        (state_q == STATE_ARMED) &&
        (saturated_i || !enable_i || (mode_i != MODE_SCAN));
    assign trigger_candidate_w =
        (state_q == STATE_ARMED) && !abort_i && !fault_candidate_w &&
        direction_match_w && inside_window_w;
    assign hold_o = trigger_candidate_w || trigger_o;
    assign fault_immediate_o = fault_candidate_w;

    always_ff @(posedge clk_i) begin
        if (!rstn_i) begin
            state_q <= STATE_SAFE;
            request_q <= 1'b0;
            trigger_o <= 1'b0;
            request_accepted_o <= 1'b0;
            previous_out2_q <= 14'sd0;
            scan_direction_q <= 2'd0;
            scan_direction_valid_q <= 1'b0;
            trigger_out2_sample_o <= 14'sd0;
            trigger_error_sample_o <= 14'sd0;
            event_sequence_o <= 32'd0;
            event_out2_o <= 32'd0;
            event_error_o <= 32'd0;
            event_config_generation_o <= 32'd0;
            event_valid_q <= 1'b0;
            fault_code_q <= 16'd0;
        end else begin
            trigger_o <= 1'b0;
            request_accepted_o <= 1'b0;
            request_q <= request_i;
            previous_out2_q <= out2_i;

            if (out2_i != previous_out2_q) begin
                scan_direction_q <= scan_direction_now_w;
                scan_direction_valid_q <= 1'b1;
            end

            if (abort_i) begin
                state_q <= STATE_SAFE;
                request_q <= 1'b0;
                event_valid_q <= 1'b0;
                fault_code_q <= 16'd0;
            end else if (fault_candidate_w) begin
                state_q <= STATE_FAULT;
                request_q <= 1'b0;
                fault_code_q <= FAULT_RUNTIME_SAFETY;
            end else if (trigger_candidate_w) begin
                trigger_o <= 1'b1;
                trigger_out2_sample_o <= out2_i;
                trigger_error_sample_o <= error_i;
                event_sequence_o <= event_sequence_o + 32'd1;
                event_out2_o <= {{18{out2_i[13]}}, out2_i};
                event_error_o <= {{18{error_i[13]}}, error_i};
                event_config_generation_o <= config_generation_i;
                event_valid_q <= 1'b1;
                state_q <= (kp_i == 14'sd0) ?
                           STATE_P_LOCK_KP0 : STATE_P_LOCK_ACTIVE;
            end else begin
                unique case (state_q)
                    STATE_SAFE: begin
                        if (enable_i && (mode_i == MODE_SCAN) && !saturated_i)
                            state_q <= STATE_SCAN;
                    end
                    STATE_SCAN: begin
                        if (!enable_i || (mode_i == MODE_SAFE))
                            state_q <= STATE_SAFE;
                        else if (request_q && config_valid_w) begin
                            state_q <= STATE_ARMED;
                            request_accepted_o <= 1'b1;
                        end
                    end
                    STATE_ARMED: begin
                    end
                    STATE_P_LOCK_KP0,
                    STATE_P_LOCK_ACTIVE: begin
                        if (!enable_i || (mode_i == MODE_SAFE))
                            state_q <= STATE_SAFE;
                        else if (mode_i == MODE_P_LOCK)
                            state_q <= (kp_i == 14'sd0) ?
                                       STATE_P_LOCK_KP0 : STATE_P_LOCK_ACTIVE;
                    end
                    STATE_FAULT: begin
                    end
                    default: state_q <= STATE_SAFE;
                endcase
            end

            if (clear_event_i)
                event_valid_q <= 1'b0;
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
        config_validation_o[7] = config_valid_w;
        config_validation_o[14:8] = config_written_mask_i;
        config_validation_o[15] = 1'b1;

        state_readback_o = 32'd0;
        state_readback_o[2:0] = state_q;
        state_readback_o[8] = event_valid_q;
        state_readback_o[9] = (state_q == STATE_ARMED);
        state_readback_o[10] =
            (state_q == STATE_P_LOCK_KP0) ||
            (state_q == STATE_P_LOCK_ACTIVE);
        state_readback_o[11] = (state_q == STATE_FAULT);
        state_readback_o[12] = (state_q == STATE_ARMED) ||
                               (state_q == STATE_P_LOCK_KP0) ||
                               (state_q == STATE_P_LOCK_ACTIVE);
        state_readback_o[13] = scan_direction_now_valid_w;
        state_readback_o[15:14] = scan_direction_now_w;

        active_target_out2_o = target_out2_i[13:0];
        active_error_setpoint_o = target_error_setpoint_i[13:0];
        active_window_o = target_window_i[13:0];
        active_requirements_o = target_requirements_i;
        active_correction_limit_o = correction_limit_i[13:0];
        active_absolute_limit_o = absolute_limit_i[13:0];

        event_info_o = 32'd0;
        event_info_o[0] = event_valid_q;
        event_info_o[3:1] = event_valid_q ? EVENT_TRIGGERED : 3'd0;
        event_info_o[5:4] = event_valid_q ? scan_direction_q : 2'd0;
        event_info_o[23:16] = fault_code_q[7:0];
        event_timestamp_lo_o = 32'd0;
        event_timestamp_hi_o = 32'd0;
        fault_detail_o = {fault_code_q, 16'd0};
    end

endmodule
