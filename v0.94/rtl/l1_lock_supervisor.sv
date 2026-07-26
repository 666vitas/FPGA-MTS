`ifndef L1_LOCK_SUPERVISOR_SV
`define L1_LOCK_SUPERVISOR_SV
`timescale 1ns/1ps

module l1_lock_supervisor (
    input  logic               clk_i,
    input  logic               rstn_i,
    input  logic               start_i,
    input  logic               stop_i,
    input  logic               servo_tick_i,
    input  logic signed [14:0] lock_error_i,
    input  logic        [14:0] abs_error_i,
    input  logic               kp_target_reached_i,
    input  logic        [23:0] mean_sum_limit_i,
    input  logic        [23:0] abs_sum_limit_i,
    input  logic        [23:0] divergence_sum_limit_i,
    input  logic         [7:0] confirm_windows_i,
    input  logic         [7:0] divergence_windows_i,
    output logic               window_done_o,
    output logic               observation_good_o,
    output logic               observation_diverged_o,
    output logic               observation_invalid_o,
    output logic               supervisor_lock_o,
    output logic               supervisor_fail_o,
    output logic        [31:0] metrics_o
);
    localparam logic signed [23:0] SUM_MAX = 24'sh7F_FFFF;
    localparam logic signed [23:0] SUM_MIN = -24'sh80_0000;
    localparam logic        [23:0] ABS_MAX = 24'hFF_FFFF;

    logic active_q;
    logic [7:0] sample_count_q;
    logic signed [23:0] error_sum_q;
    logic [23:0] error_abs_sum_q;
    logic error_overflow_q;
    logic abs_overflow_q;

    logic signed [23:0] sum_snapshot_q;
    logic [23:0] abs_sum_snapshot_q;
    logic overflow_snapshot_q;
    logic target_reached_snapshot_q;
    logic compare_valid_q;
    logic [7:0] confirm_count_q;
    logic [7:0] divergence_count_q;

    logic signed [24:0] error_sum_ext_w;
    logic [24:0] error_abs_sum_ext_w;
    logic signed [23:0] error_sum_next_w;
    logic [23:0] error_abs_sum_next_w;
    logic error_overflow_next_w;
    logic abs_overflow_next_w;
    logic [7:0] confirm_limit_w;
    logic [7:0] divergence_limit_w;

    always_comb begin
        error_sum_ext_w =
            $signed({error_sum_q[23], error_sum_q}) +
            $signed({{10{lock_error_i[14]}}, lock_error_i});
        if (error_sum_ext_w > $signed({SUM_MAX[23], SUM_MAX})) begin
            error_sum_next_w = SUM_MAX;
            error_overflow_next_w = 1'b1;
        end else if (error_sum_ext_w < $signed({SUM_MIN[23], SUM_MIN})) begin
            error_sum_next_w = SUM_MIN;
            error_overflow_next_w = 1'b1;
        end else begin
            error_sum_next_w = error_sum_ext_w[23:0];
            error_overflow_next_w = error_overflow_q;
        end

        error_abs_sum_ext_w = {1'b0, error_abs_sum_q} +
                              {{10{1'b0}}, abs_error_i};
        if (error_abs_sum_ext_w > {1'b0, ABS_MAX}) begin
            error_abs_sum_next_w = ABS_MAX;
            abs_overflow_next_w = 1'b1;
        end else begin
            error_abs_sum_next_w = error_abs_sum_ext_w[23:0];
            abs_overflow_next_w = abs_overflow_q;
        end

        confirm_limit_w = (confirm_windows_i == 8'd0)
                        ? 8'd1 : confirm_windows_i;
        divergence_limit_w = (divergence_windows_i == 8'd0)
                           ? 8'd1 : divergence_windows_i;
    end

    // S1/S2: one 24-bit saturating accumulate per servo tick, followed by a
    // registered 256-sample snapshot. Data registers use local start/window
    // clears; only validity/control state uses the global reset.
    always_ff @(posedge clk_i) begin
        if (!rstn_i) begin
            active_q <= 1'b0;
            sample_count_q <= 8'd0;
            error_overflow_q <= 1'b0;
            abs_overflow_q <= 1'b0;
            window_done_o <= 1'b0;
        end else begin
            window_done_o <= 1'b0;
            if (stop_i) begin
                active_q <= 1'b0;
                sample_count_q <= 8'd0;
                error_overflow_q <= 1'b0;
                abs_overflow_q <= 1'b0;
            end else if (start_i) begin
                active_q <= 1'b1;
                sample_count_q <= 8'd0;
                error_sum_q <= 24'sd0;
                error_abs_sum_q <= 24'd0;
                error_overflow_q <= 1'b0;
                abs_overflow_q <= 1'b0;
            end else if (active_q && servo_tick_i) begin
                if (sample_count_q == 8'hFF) begin
                    sum_snapshot_q <= error_sum_next_w;
                    abs_sum_snapshot_q <= error_abs_sum_next_w;
                    overflow_snapshot_q <= error_overflow_next_w |
                                           abs_overflow_next_w;
                    target_reached_snapshot_q <= kp_target_reached_i;
                    window_done_o <= 1'b1;
                    sample_count_q <= 8'd0;
                    error_sum_q <= 24'sd0;
                    error_abs_sum_q <= 24'd0;
                    error_overflow_q <= 1'b0;
                    abs_overflow_q <= 1'b0;
                end else begin
                    sample_count_q <= sample_count_q + 8'd1;
                    error_sum_q <= error_sum_next_w;
                    error_abs_sum_q <= error_abs_sum_next_w;
                    error_overflow_q <= error_overflow_next_w;
                    abs_overflow_q <= abs_overflow_next_w;
                end
            end
        end
    end

    // S3: compare only registered snapshots. There is no dynamic shift,
    // multiplication, or accumulator carry chain beyond this stage.
    always_ff @(posedge clk_i) begin
        if (!rstn_i) begin
            compare_valid_q <= 1'b0;
            observation_good_o <= 1'b0;
            observation_diverged_o <= 1'b0;
            observation_invalid_o <= 1'b0;
        end else begin
            compare_valid_q <= window_done_o;
            if (window_done_o) begin
                observation_invalid_o <= overflow_snapshot_q;
                observation_good_o <=
                    !overflow_snapshot_q && target_reached_snapshot_q &&
                    ($signed(sum_snapshot_q) <
                     $signed({1'b0, mean_sum_limit_i[22:0]})) &&
                    ($signed(sum_snapshot_q) >
                     -$signed({1'b0, mean_sum_limit_i[22:0]})) &&
                    (abs_sum_snapshot_q < abs_sum_limit_i);
                observation_diverged_o <=
                    overflow_snapshot_q ||
                    (abs_sum_snapshot_q >= divergence_sum_limit_i);
            end
        end
    end

    // S4: registered window counters and registered terminal decisions.
    always_ff @(posedge clk_i) begin
        if (!rstn_i) begin
            confirm_count_q <= 8'd0;
            divergence_count_q <= 8'd0;
            supervisor_lock_o <= 1'b0;
            supervisor_fail_o <= 1'b0;
            metrics_o <= 32'd0;
        end else begin
            supervisor_lock_o <= 1'b0;
            supervisor_fail_o <= 1'b0;
            if (stop_i || start_i) begin
                confirm_count_q <= 8'd0;
                divergence_count_q <= 8'd0;
                metrics_o <= 32'd0;
            end else if (compare_valid_q) begin
                metrics_o[13:0] <= abs_sum_snapshot_q[21:8];
                metrics_o[21:14] <= confirm_count_q;
                metrics_o[29:22] <= divergence_count_q;
                metrics_o[31:30] <= 2'd0;
                if (observation_invalid_o) begin
                    confirm_count_q <= 8'd0;
                    divergence_count_q <= divergence_limit_w;
                    supervisor_fail_o <= 1'b1;
                end else if (observation_good_o) begin
                    divergence_count_q <= 8'd0;
                    if (confirm_count_q + 8'd1 >= confirm_limit_w) begin
                        confirm_count_q <= confirm_limit_w;
                        supervisor_lock_o <= 1'b1;
                    end else begin
                        confirm_count_q <= confirm_count_q + 8'd1;
                    end
                end else begin
                    confirm_count_q <= 8'd0;
                    if (observation_diverged_o) begin
                        if (divergence_count_q + 8'd1 >= divergence_limit_w) begin
                            divergence_count_q <= divergence_limit_w;
                            supervisor_fail_o <= 1'b1;
                        end else begin
                            divergence_count_q <= divergence_count_q + 8'd1;
                        end
                    end else begin
                        divergence_count_q <= 8'd0;
                    end
                end
            end
        end
    end
endmodule
`endif
