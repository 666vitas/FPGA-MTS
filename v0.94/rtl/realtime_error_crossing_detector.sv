`ifndef REALTIME_ERROR_CROSSING_DETECTOR_SV
`define REALTIME_ERROR_CROSSING_DETECTOR_SV
`timescale 1ns/1ps

// Robust ERROR crossing detector for one OUT2 guard pass.
//
// A valid crossing requires N consecutive samples on the source side of the
// hysteresis band followed by N consecutive samples on the destination side.
// History is local to one direction-matched guard pass.  The consumed latch
// prevents retriggering until the scan leaves and later re-enters the guard.
module realtime_error_crossing_detector (
    input  logic               clk_i,
    input  logic               rstn_i,
    input  logic               clear_i,
    input  logic               armed_i,
    input  logic               runtime_ok_i,
    input  logic               in_guard_i,
    input  logic        [1:0]  scan_direction_i,
    input  logic        [1:0]  required_scan_direction_i,
    input  logic        [1:0]  required_error_direction_i,
    input  logic signed [14:0] lock_error_i,
    input  logic        [13:0] hysteresis_i,
    input  logic        [7:0]  consecutive_samples_i,
    output logic               crossing_o,
    output logic               crossing_candidate_o,
    output logic               source_confirmed_o,
    output logic               pass_consumed_o
);
    localparam logic [1:0] NEG_TO_POS = 2'd1;
    localparam logic [1:0] POS_TO_NEG = 2'd2;

    logic [7:0] source_count_q;
    logic [7:0] destination_count_q;
    logic [7:0] required_count_w;
    logic signed [14:0] hysteresis_w;
    logic source_side_w;
    logic destination_side_w;
    logic context_valid_w;

    always_comb begin
        required_count_w = (consecutive_samples_i == 8'd0)
                         ? 8'd1 : consecutive_samples_i;
        hysteresis_w = $signed({1'b0, hysteresis_i});
        source_side_w = 1'b0;
        destination_side_w = 1'b0;
        unique case (required_error_direction_i)
            NEG_TO_POS: begin
                source_side_w = (lock_error_i <= -hysteresis_w);
                destination_side_w = (lock_error_i >= hysteresis_w);
            end
            POS_TO_NEG: begin
                source_side_w = (lock_error_i >= hysteresis_w);
                destination_side_w = (lock_error_i <= -hysteresis_w);
            end
            default: begin
            end
        endcase
        context_valid_w =
            armed_i && runtime_ok_i && in_guard_i &&
            (scan_direction_i == required_scan_direction_i) &&
            ((required_error_direction_i == NEG_TO_POS) ||
             (required_error_direction_i == POS_TO_NEG));
        crossing_candidate_o =
            context_valid_w && !pass_consumed_o && source_confirmed_o &&
            destination_side_w &&
            (destination_count_q + 8'd1 >= required_count_w);
    end

    always_ff @(posedge clk_i) begin
        if (!rstn_i) begin
            source_count_q <= 8'd0;
            destination_count_q <= 8'd0;
            source_confirmed_o <= 1'b0;
            pass_consumed_o <= 1'b0;
            crossing_o <= 1'b0;
        end else begin
            crossing_o <= 1'b0;
            if (clear_i || !armed_i || !runtime_ok_i || !in_guard_i ||
                (scan_direction_i != required_scan_direction_i)) begin
                source_count_q <= 8'd0;
                destination_count_q <= 8'd0;
                source_confirmed_o <= 1'b0;
                pass_consumed_o <= 1'b0;
            end else if (!context_valid_w || pass_consumed_o) begin
                source_count_q <= 8'd0;
                destination_count_q <= 8'd0;
                source_confirmed_o <= 1'b0;
            end else if (!source_confirmed_o) begin
                destination_count_q <= 8'd0;
                if (source_side_w) begin
                    if (source_count_q + 8'd1 >= required_count_w) begin
                        source_count_q <= required_count_w;
                        source_confirmed_o <= 1'b1;
                    end else begin
                        source_count_q <= source_count_q + 8'd1;
                    end
                end else begin
                    source_count_q <= 8'd0;
                end
            end else begin
                if (destination_side_w) begin
                    if (crossing_candidate_o) begin
                        destination_count_q <= required_count_w;
                        crossing_o <= 1'b1;
                        pass_consumed_o <= 1'b1;
                        source_confirmed_o <= 1'b0;
                    end else begin
                        destination_count_q <= destination_count_q + 8'd1;
                    end
                end else begin
                    destination_count_q <= 8'd0;
                end
            end
        end
    end
endmodule
`endif
