`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// v1c_mixer_only digital mixer.
//
// This module is the FPGA equivalent of the ZFM-3+ mixer for the first v1c step:
// signed PD samples times signed REF samples, then scale and saturate back to
// the DAC/core sample width. It does not include the post-mixer LPF.
//////////////////////////////////////////////////////////////////////////////////

module mixer_core #(
    parameter int IN_WIDTH  = 14,
    parameter int OUT_WIDTH = 14,
    parameter int SHIFT     = 13
)(
    input  logic clk_i,
    input  logic rstn_i,
    input  logic enable_i,
    input  logic signed [IN_WIDTH-1:0] pd_i,
    input  logic signed [IN_WIDTH-1:0] ref_i,
    output logic signed [OUT_WIDTH-1:0] mix_o
);

    localparam int PRODUCT_WIDTH = IN_WIDTH * 2;

    localparam logic signed [OUT_WIDTH-1:0] OUT_MAX =
        {1'b0, {(OUT_WIDTH-1){1'b1}}};
    localparam logic signed [OUT_WIDTH-1:0] OUT_MIN =
        {1'b1, {(OUT_WIDTH-1){1'b0}}};

    localparam logic signed [PRODUCT_WIDTH-1:0] SAT_MAX =
        {{(PRODUCT_WIDTH-OUT_WIDTH){OUT_MAX[OUT_WIDTH-1]}}, OUT_MAX};
    localparam logic signed [PRODUCT_WIDTH-1:0] SAT_MIN =
        {{(PRODUCT_WIDTH-OUT_WIDTH){OUT_MIN[OUT_WIDTH-1]}}, OUT_MIN};

    logic signed [PRODUCT_WIDTH-1:0] product_w;
    logic signed [PRODUCT_WIDTH-1:0] scaled_w;
    logic signed [OUT_WIDTH-1:0] saturated_w;

    assign product_w = pd_i * ref_i;
    assign scaled_w  = product_w >>> SHIFT;

    always_comb begin
        if (scaled_w > SAT_MAX) begin
            saturated_w = OUT_MAX;
        end else if (scaled_w < SAT_MIN) begin
            saturated_w = OUT_MIN;
        end else begin
            saturated_w = scaled_w[OUT_WIDTH-1:0];
        end
    end

    always_ff @(posedge clk_i) begin
        if (!rstn_i) begin
            mix_o <= '0;
        end else if (!enable_i) begin
            mix_o <= '0;
        end else begin
            mix_o <= saturated_w;
        end
    end

endmodule
