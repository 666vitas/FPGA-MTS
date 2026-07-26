`ifndef L1_EVENT_RECORDER_SV
`define L1_EVENT_RECORDER_SV
`timescale 1ns/1ps

module l1_event_recorder (
    input  logic               clk_i,
    input  logic               rstn_i,
    input  logic               clear_i,
    input  logic               request_i,
    input  logic         [2:0] type_i,
    input  logic signed [13:0] out2_i,
    input  logic signed [13:0] error_i,
    input  logic signed [14:0] lock_error_i,
    input  logic         [1:0] scan_direction_i,
    input  logic         [1:0] error_direction_i,
    input  logic        [31:0] generation_i,
    input  logic        [63:0] timestamp_i,
    input  logic        [15:0] reject_code_i,
    input  logic        [15:0] fault_code_i,
    output logic        [31:0] sequence_o,
    output logic        [31:0] out2_o,
    output logic        [31:0] error_o,
    output logic signed [31:0] lock_error_o,
    output logic        [31:0] generation_o,
    output logic        [31:0] info_o,
    output logic        [31:0] timestamp_lo_o,
    output logic        [31:0] timestamp_hi_o,
    output logic        [31:0] fault_detail_o
);
    logic event_valid_q;
    logic [2:0] event_type_q;
    logic [1:0] scan_direction_q;
    logic [1:0] error_direction_q;
    logic [15:0] reject_code_q;
    logic [15:0] fault_code_q;

    // Payload registers intentionally have no global reset. event_valid_q is
    // the sole authority for payload validity, reducing the reset network.
    always_ff @(posedge clk_i) begin
        if (!rstn_i) begin
            sequence_o <= 32'd0;
            event_valid_q <= 1'b0;
            event_type_q <= 3'd0;
            scan_direction_q <= 2'd0;
            error_direction_q <= 2'd0;
            reject_code_q <= 16'd0;
            fault_code_q <= 16'd0;
        end else if (request_i) begin
            sequence_o <= sequence_o + 32'd1;
            out2_o <= {{18{out2_i[13]}}, out2_i};
            error_o <= {{18{error_i[13]}}, error_i};
            lock_error_o <= {{17{lock_error_i[14]}}, lock_error_i};
            generation_o <= generation_i;
            timestamp_lo_o <= timestamp_i[31:0];
            timestamp_hi_o <= timestamp_i[63:32];
            event_valid_q <= 1'b1;
            event_type_q <= type_i;
            scan_direction_q <= scan_direction_i;
            error_direction_q <= error_direction_i;
            reject_code_q <= reject_code_i;
            fault_code_q <= fault_code_i;
        end else if (clear_i) begin
            event_valid_q <= 1'b0;
            event_type_q <= 3'd0;
            scan_direction_q <= 2'd0;
            error_direction_q <= 2'd0;
            reject_code_q <= 16'd0;
            fault_code_q <= 16'd0;
        end
    end

    always_comb begin
        info_o = 32'd0;
        info_o[0] = event_valid_q;
        info_o[3:1] = event_type_q;
        info_o[5:4] = scan_direction_q;
        info_o[7:6] = error_direction_q;
        info_o[23:16] = fault_code_q[7:0];
        fault_detail_o = {fault_code_q, reject_code_q};
    end
endmodule
`endif
