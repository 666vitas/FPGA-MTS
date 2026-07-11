`timescale 1ns/1ps

module error_setpoint_corrector (
    input  logic               clk_i,
    input  logic               rstn_i,
    input  logic signed [13:0] error_i,
    input  logic signed [13:0] setpoint_i,
    output logic signed [13:0] lock_error_o
);

    localparam logic signed [14:0] OUT_MAX = 15'sd8191;
    localparam logic signed [14:0] OUT_MIN = -15'sd8191;

    logic signed [14:0] diff_w;
    logic signed [13:0] saturated_w;

    always_comb begin
        diff_w = $signed({error_i[13], error_i}) - $signed({setpoint_i[13], setpoint_i});

        if (diff_w > OUT_MAX) begin
            saturated_w = 14'sd8191;
        end else if (diff_w < OUT_MIN) begin
            saturated_w = -14'sd8191;
        end else begin
            saturated_w = diff_w[13:0];
        end
    end

    always_ff @(posedge clk_i) begin
        if (!rstn_i) begin
            lock_error_o <= 14'sd0;
        end else begin
            lock_error_o <= saturated_w;
        end
    end

endmodule
