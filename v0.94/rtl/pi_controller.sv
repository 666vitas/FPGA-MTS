`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// v2a-2 PI controller with anti-windup.
//
// Data path:
// error_i -> signed extension -> polarity
//         -> P multiply -> KP_SHIFT
//         -> I multiply -> KI_SHIFT -> integrator clamp / conditional freeze
//         -> P + I + offset -> output limiter -> control_o.
//
// Parameter assumptions:
// ACC_WIDTH >= PRODUCT_WIDTH, ACC_WIDTH >= OUT_WIDTH, OUT_WIDTH <= 32,
// KP_SHIFT >= 0, KI_SHIFT >= 0.
//////////////////////////////////////////////////////////////////////////////////

module pi_controller #(
    parameter int ERROR_WIDTH = 14,
    parameter int GAIN_WIDTH  = 16,
    parameter int OUT_WIDTH   = 14,
    parameter int ACC_WIDTH   = 48,
    parameter int KP_SHIFT    = 12,
    parameter int KI_SHIFT    = 12
)(
    input  logic                              clk_i,
    input  logic                              rstn_i,
    input  logic                              pid_ce_i,
    input  logic                              enable_i,
    input  logic                              hold_i,
    input  logic                              reset_integrator_i,
    input  logic                              polarity_i,

    input  logic signed [ERROR_WIDTH-1:0]     error_i,
    input  logic signed [GAIN_WIDTH-1:0]      kp_i,
    input  logic signed [GAIN_WIDTH-1:0]      ki_i,
    input  logic signed [OUT_WIDTH-1:0]       offset_i,
    input  logic        [OUT_WIDTH-1:0]       output_limit_i,

    output logic signed [OUT_WIDTH-1:0]       control_o,
    output logic signed [31:0]                p_term_o,
    output logic signed [31:0]                i_term_o,
    output logic                              sat_o
);

    localparam int ERROR_EXT_WIDTH = ERROR_WIDTH + 1;
    localparam int PRODUCT_WIDTH   = ERROR_EXT_WIDTH + GAIN_WIDTH;

    localparam logic signed [OUT_WIDTH-1:0] OUT_POS_MAX =
        {1'b0, {(OUT_WIDTH-1){1'b1}}};
    localparam logic [OUT_WIDTH:0] OUT_POS_MAX_EXT =
        {1'b0, OUT_POS_MAX};
    localparam logic signed [ACC_WIDTH-1:0] ACC_ZERO = '0;

    logic signed [ERROR_EXT_WIDTH-1:0] error_ext_w;
    logic signed [ERROR_EXT_WIDTH-1:0] error_pol_w;
    logic signed [PRODUCT_WIDTH-1:0]   p_product_w;
    logic signed [PRODUCT_WIDTH-1:0]   i_product_w;
    logic signed [PRODUCT_WIDTH-1:0]   i_scaled_product_w;
    logic signed [ACC_WIDTH-1:0]       p_scaled_w;
    logic signed [ACC_WIDTH-1:0]       i_delta_w;
    logic signed [ACC_WIDTH-1:0]       offset_ext_w;
    logic signed [ACC_WIDTH-1:0]       current_control_pre_w;
    logic signed [ACC_WIDTH-1:0]       reset_control_pre_w;
    logic signed [ACC_WIDTH-1:0]       next_control_pre_w;
    logic signed [ACC_WIDTH-1:0]       limit_pos_w;
    logic signed [ACC_WIDTH-1:0]       limit_neg_w;
    logic signed [ACC_WIDTH-1:0]       reset_control_limited_w;
    logic signed [ACC_WIDTH-1:0]       next_control_limited_w;
    logic signed [ACC_WIDTH-1:0]       integrator_q;
    logic signed [ACC_WIDTH-1:0]       integrator_candidate_w;
    logic signed [ACC_WIDTH-1:0]       integrator_accepted_w;
    logic                              reset_sat_w;
    logic                              next_sat_w;
    logic                              freeze_integrator_w;
    logic        [OUT_WIDTH:0]         output_limit_ext_w;
    logic        [OUT_WIDTH:0]         limit_clamped_w;

    assign error_ext_w = {error_i[ERROR_WIDTH-1], error_i};
    assign error_pol_w = polarity_i ? -error_ext_w : error_ext_w;

    assign p_product_w = $signed(error_pol_w) * $signed(kp_i);
    assign i_product_w = $signed(error_pol_w) * $signed(ki_i);
    assign p_scaled_w  = p_product_w >>> KP_SHIFT;
    assign i_scaled_product_w = i_product_w >>> KI_SHIFT;
    assign i_delta_w = {{(ACC_WIDTH-PRODUCT_WIDTH){i_scaled_product_w[PRODUCT_WIDTH-1]}},
                        i_scaled_product_w};
    assign offset_ext_w = {{(ACC_WIDTH-OUT_WIDTH){offset_i[OUT_WIDTH-1]}}, offset_i};
    assign current_control_pre_w = p_scaled_w + integrator_q + offset_ext_w;
    assign reset_control_pre_w   = p_scaled_w + offset_ext_w;

    assign output_limit_ext_w = {1'b0, output_limit_i};
    assign limit_clamped_w = (output_limit_ext_w > OUT_POS_MAX_EXT)
                           ? OUT_POS_MAX_EXT
                           : output_limit_ext_w;
    assign limit_pos_w = {{(ACC_WIDTH-(OUT_WIDTH+1)){1'b0}}, limit_clamped_w};
    assign limit_neg_w = -limit_pos_w;

    assign freeze_integrator_w =
        ((current_control_pre_w >= limit_pos_w) && (i_delta_w > ACC_ZERO)) ||
        ((current_control_pre_w <= limit_neg_w) && (i_delta_w < ACC_ZERO));

    always_comb begin
        integrator_candidate_w = freeze_integrator_w
                               ? integrator_q
                               : (integrator_q + i_delta_w);

        if (integrator_candidate_w > limit_pos_w) begin
            integrator_accepted_w = limit_pos_w;
        end else if (integrator_candidate_w < limit_neg_w) begin
            integrator_accepted_w = limit_neg_w;
        end else begin
            integrator_accepted_w = integrator_candidate_w;
        end

        next_control_pre_w = p_scaled_w + integrator_accepted_w + offset_ext_w;

        if (reset_control_pre_w > limit_pos_w) begin
            reset_control_limited_w = limit_pos_w;
            reset_sat_w             = 1'b1;
        end else if (reset_control_pre_w < limit_neg_w) begin
            reset_control_limited_w = limit_neg_w;
            reset_sat_w             = 1'b1;
        end else begin
            reset_control_limited_w = reset_control_pre_w;
            reset_sat_w             = 1'b0;
        end

        if (next_control_pre_w > limit_pos_w) begin
            next_control_limited_w = limit_pos_w;
            next_sat_w             = 1'b1;
        end else if (next_control_pre_w < limit_neg_w) begin
            next_control_limited_w = limit_neg_w;
            next_sat_w             = 1'b1;
        end else begin
            next_control_limited_w = next_control_pre_w;
            next_sat_w             = 1'b0;
        end
    end

    always_ff @(posedge clk_i) begin
        if (!rstn_i) begin
            integrator_q <= '0;
            control_o <= '0;
            p_term_o  <= '0;
            i_term_o  <= '0;
            sat_o     <= 1'b0;
        end else if (!enable_i) begin
            integrator_q <= '0;
            control_o <= '0;
            p_term_o  <= '0;
            i_term_o  <= '0;
            sat_o     <= 1'b0;
        end else if (reset_integrator_i) begin
            integrator_q <= '0;
            control_o <= reset_control_limited_w[OUT_WIDTH-1:0];
            p_term_o  <= p_scaled_w[31:0];
            i_term_o  <= 32'sd0;
            sat_o     <= reset_sat_w;
        end else if (hold_i) begin
            integrator_q <= integrator_q;
            control_o <= control_o;
            p_term_o  <= p_term_o;
            i_term_o  <= i_term_o;
            sat_o     <= sat_o;
        end else if (pid_ce_i) begin
            integrator_q <= integrator_accepted_w;
            control_o <= next_control_limited_w[OUT_WIDTH-1:0];
            p_term_o  <= p_scaled_w[31:0];
            i_term_o  <= integrator_accepted_w[31:0];
            sat_o     <= next_sat_w;
        end else begin
            integrator_q <= integrator_q;
            control_o <= control_o;
            p_term_o  <= p_term_o;
            i_term_o  <= i_term_o;
            sat_o     <= sat_o;
        end
    end

endmodule
