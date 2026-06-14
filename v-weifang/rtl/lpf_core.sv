`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// v1d_mixer_lpf post-mixer low-pass filter.
//
// This module is the FPGA equivalent of the low-pass stage after the mixer:
// it keeps the slow / difference-frequency / baseband part and suppresses the
// fast 2f term from the raw mixer output. It is not the pre-mixer 10 MHz LPF or
// the 1.8 MHz HPF; those belong to a later v1f stage.
//////////////////////////////////////////////////////////////////////////////////

module lpf_core #(
    parameter int IN_WIDTH  = 14,
    parameter int OUT_WIDTH = 14,
    parameter int ACC_WIDTH = 32,
    parameter int LPF_SHIFT = 12
)(
    input  logic clk_i,
    input  logic rstn_i,
    input  logic enable_i,
    input  logic signed [IN_WIDTH-1:0] x_i,
    output logic signed [OUT_WIDTH-1:0] y_o
);

    localparam logic signed [OUT_WIDTH-1:0] OUT_MAX =
        {1'b0, {(OUT_WIDTH-1){1'b1}}};
    localparam logic signed [OUT_WIDTH-1:0] OUT_MIN =
        {1'b1, {(OUT_WIDTH-1){1'b0}}};

    localparam logic signed [ACC_WIDTH-1:0] ACC_MAX =
        {{(ACC_WIDTH-OUT_WIDTH){OUT_MAX[OUT_WIDTH-1]}}, OUT_MAX};
    localparam logic signed [ACC_WIDTH-1:0] ACC_MIN =
        {{(ACC_WIDTH-OUT_WIDTH){OUT_MIN[OUT_WIDTH-1]}}, OUT_MIN};

    logic signed [ACC_WIDTH-1:0] acc_q;
    logic signed [ACC_WIDTH-1:0] x_scaled_w;
    logic signed [ACC_WIDTH-1:0] delta_w;
    logic signed [ACC_WIDTH-1:0] step_w;
    logic signed [ACC_WIDTH-1:0] acc_next_w;
    logic signed [ACC_WIDTH-1:0] y_unscaled_w;
    logic signed [OUT_WIDTH-1:0] y_saturated_w;

    // Hardware meaning for beginners:
    // acc_q is not a software variable. It is a bank of flip-flops that stores
    // the current filtered value. The lower LPF_SHIFT bits act like fractional
    // bits, so small mixer outputs can still accumulate over many adc_clk cycles.
    //
    // LPF_SHIFT larger:
    // - stronger low-pass filtering;
    // - smoother output;
    // - slower response.
    //
    // LPF_SHIFT smaller:
    // - weaker low-pass filtering;
    // - more high-frequency content remains;
    // - faster response.
    assign x_scaled_w   = {{(ACC_WIDTH-IN_WIDTH-LPF_SHIFT){x_i[IN_WIDTH-1]}}, x_i, {LPF_SHIFT{1'b0}}};
    assign delta_w      = x_scaled_w - acc_q;
    assign step_w       = delta_w >>> LPF_SHIFT;
    assign acc_next_w   = acc_q + step_w;
    assign y_unscaled_w = acc_next_w >>> LPF_SHIFT;

    always_comb begin
        if (y_unscaled_w > ACC_MAX) begin
            y_saturated_w = OUT_MAX;
        end else if (y_unscaled_w < ACC_MIN) begin
            y_saturated_w = OUT_MIN;
        end else begin
            y_saturated_w = y_unscaled_w[OUT_WIDTH-1:0];
        end
    end

    always_ff @(posedge clk_i) begin
        if (!rstn_i) begin
            acc_q <= '0;
            y_o   <= '0;
        end else if (!enable_i) begin
            acc_q <= '0;
            y_o   <= '0;
        end else begin
            acc_q <= acc_next_w;
            y_o   <= y_saturated_w;
        end
    end

endmodule
