`timescale 1ns / 1ps

// v2B2 timing-clean sequential PI controller.
//
// This module preserves the fixed-point intent of pi_controller.sv while
// splitting one PI update over seven clk_i states. pid_ce_i starts a
// transaction; it is a clock-enable pulse, not another clock. The public
// outputs update only in S_LIMIT, seven clk_i edges after pid_ce_i is sampled.
//
// Data path per transaction:
// capture inputs -> P multiply -> I multiply/P scale -> I update -> sum
// -> limit/register outputs. The short registered stages avoid the old direct
// 125 MHz P+I+anti-windup limiter path. This controller is still for OUT2
// oscilloscope observation until separate Vivado timing and board checks pass.

module pi_controller_seq #(
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
        {1'b0, {(OUT_WIDTH - 1){1'b1}}};
    localparam logic [OUT_WIDTH:0] OUT_POS_MAX_EXT = {1'b0, OUT_POS_MAX};
    localparam logic signed [ACC_WIDTH-1:0] ACC_ZERO = '0;

    typedef enum logic [2:0] {
        S_IDLE,
        S_CAPTURE,
        S_P_CALC,
        S_I_CALC,
        S_I_UPDATE,
        S_SUM,
        S_LIMIT
    } state_t;

    state_t state_q;

    logic signed [ERROR_EXT_WIDTH-1:0] error_pol_q;
    logic signed [GAIN_WIDTH-1:0]      kp_q;
    logic signed [GAIN_WIDTH-1:0]      ki_q;
    logic signed [ACC_WIDTH-1:0]       offset_ext_q;
    logic        [OUT_WIDTH-1:0]       output_limit_q;
    logic                              reset_integrator_q;

    logic signed [PRODUCT_WIDTH-1:0] p_product_q;
    logic signed [PRODUCT_WIDTH-1:0] i_product_q;
    logic signed [ACC_WIDTH-1:0]     p_scaled_q;
    logic signed [ACC_WIDTH-1:0]     integrator_q;
    logic signed [ACC_WIDTH-1:0]     integrator_next_q;
    logic signed [ACC_WIDTH-1:0]     control_pre_q;

    logic        [OUT_WIDTH:0]         output_limit_ext_w;
    logic        [OUT_WIDTH:0]         limit_clamped_w;
    logic signed [ACC_WIDTH-1:0]       limit_pos_w;
    logic signed [ACC_WIDTH-1:0]       limit_neg_w;
    logic signed [ACC_WIDTH-1:0]       p_scaled_from_product_w;
    logic signed [ACC_WIDTH-1:0]       i_delta_w;
    logic signed [ACC_WIDTH-1:0]       current_control_pre_w;
    logic signed [ACC_WIDTH-1:0]       integrator_candidate_w;
    logic signed [ACC_WIDTH-1:0]       integrator_accepted_w;
    logic                              freeze_integrator_w;

    // output_limit_i is unsigned. Clamp it before converting to the signed
    // positive/negative bounds so no implicit signed conversion controls the
    // limiter behavior.
    assign output_limit_ext_w = {1'b0, output_limit_q};
    assign limit_clamped_w = (output_limit_ext_w > OUT_POS_MAX_EXT)
                           ? OUT_POS_MAX_EXT
                           : output_limit_ext_w;
    assign limit_pos_w = $signed({{(ACC_WIDTH - (OUT_WIDTH + 1)){1'b0}}, limit_clamped_w});
    assign limit_neg_w = -$signed(limit_pos_w);

    assign p_scaled_from_product_w =
        $signed({{(ACC_WIDTH - PRODUCT_WIDTH){p_product_q[PRODUCT_WIDTH-1]}}, p_product_q}) >>> KP_SHIFT;
    assign i_delta_w =
        $signed({{(ACC_WIDTH - PRODUCT_WIDTH){i_product_q[PRODUCT_WIDTH-1]}}, i_product_q}) >>> KI_SHIFT;
    assign current_control_pre_w = $signed(p_scaled_q) + $signed(integrator_q) + $signed(offset_ext_q);
    assign freeze_integrator_w =
        (($signed(current_control_pre_w) >= $signed(limit_pos_w)) && ($signed(i_delta_w) > ACC_ZERO)) ||
        (($signed(current_control_pre_w) <= $signed(limit_neg_w)) && ($signed(i_delta_w) < ACC_ZERO));

    always_comb begin
        integrator_candidate_w = freeze_integrator_w
                               ? integrator_q
                               : (integrator_q + i_delta_w);

        if ($signed(integrator_candidate_w) > $signed(limit_pos_w)) begin
            integrator_accepted_w = limit_pos_w;
        end else if ($signed(integrator_candidate_w) < $signed(limit_neg_w)) begin
            integrator_accepted_w = limit_neg_w;
        end else begin
            integrator_accepted_w = integrator_candidate_w;
        end
    end

    always_ff @(posedge clk_i) begin
        if (!rstn_i) begin
            state_q              <= S_IDLE;
            error_pol_q          <= '0;
            kp_q                 <= '0;
            ki_q                 <= '0;
            offset_ext_q         <= '0;
            output_limit_q       <= '0;
            reset_integrator_q   <= 1'b0;
            p_product_q          <= '0;
            i_product_q          <= '0;
            p_scaled_q           <= '0;
            integrator_q         <= '0;
            integrator_next_q    <= '0;
            control_pre_q        <= '0;
            control_o            <= '0;
            p_term_o             <= '0;
            i_term_o             <= '0;
            sat_o                <= 1'b0;
        end else if (!enable_i) begin
            // Disable is an immediate output safety action, matching the
            // reference PI controller. Any incomplete transaction is dropped.
            state_q              <= S_IDLE;
            integrator_q         <= '0;
            integrator_next_q    <= '0;
            control_o            <= '0;
            p_term_o             <= '0;
            i_term_o             <= '0;
            sat_o                <= 1'b0;
        end else if (hold_i) begin
            // Hold keeps all visible outputs and the integrator unchanged, and
            // returns the FSM to IDLE so a later pid_ce starts a fresh sample.
            state_q              <= S_IDLE;
            integrator_q         <= integrator_q;
            integrator_next_q    <= integrator_next_q;
            control_o            <= control_o;
            p_term_o             <= p_term_o;
            i_term_o             <= i_term_o;
            sat_o                <= sat_o;
        end else begin
            case (state_q)
                S_IDLE: begin
                    if (pid_ce_i) begin
                        state_q <= S_CAPTURE;
                    end
                end

                S_CAPTURE: begin
                    // Latch the whole transaction so mid-transaction input
                    // changes cannot alter a calculation already in flight.
                    error_pol_q        <= polarity_i
                                        ? -$signed({error_i[ERROR_WIDTH-1], error_i})
                                        :  $signed({error_i[ERROR_WIDTH-1], error_i});
                    kp_q               <= kp_i;
                    ki_q               <= ki_i;
                    offset_ext_q       <= {{(ACC_WIDTH - OUT_WIDTH){offset_i[OUT_WIDTH-1]}}, offset_i};
                    output_limit_q     <= output_limit_i;
                    reset_integrator_q <= reset_integrator_i;
                    state_q            <= S_P_CALC;
                end

                S_P_CALC: begin
                    p_product_q <= $signed(error_pol_q) * $signed(kp_q);
                    state_q     <= S_I_CALC;
                end

                S_I_CALC: begin
                    p_scaled_q  <= p_scaled_from_product_w;
                    i_product_q <= $signed(error_pol_q) * $signed(ki_q);
                    state_q     <= S_I_UPDATE;
                end

                S_I_UPDATE: begin
                    if (reset_integrator_q) begin
                        integrator_q      <= '0;
                        integrator_next_q <= '0;
                    end else begin
                        integrator_q      <= integrator_accepted_w;
                        integrator_next_q <= integrator_accepted_w;
                    end
                    state_q <= S_SUM;
                end

                S_SUM: begin
                    // integrator_next_q is the accepted value from this same
                    // transaction, including reset_integrator handling.
                    control_pre_q <= $signed(p_scaled_q) + $signed(integrator_next_q) + $signed(offset_ext_q);
                    state_q       <= S_LIMIT;
                end

                S_LIMIT: begin
                    if ($signed(control_pre_q) > $signed(limit_pos_w)) begin
                        control_o <= limit_pos_w[OUT_WIDTH-1:0];
                        sat_o     <= 1'b1;
                    end else if ($signed(control_pre_q) < $signed(limit_neg_w)) begin
                        control_o <= limit_neg_w[OUT_WIDTH-1:0];
                        sat_o     <= 1'b1;
                    end else begin
                        control_o <= control_pre_q[OUT_WIDTH-1:0];
                        sat_o     <= 1'b0;
                    end
                    p_term_o <= p_scaled_q[31:0];
                    i_term_o <= integrator_next_q[31:0];
                    state_q  <= S_IDLE;
                end

                default: state_q <= S_IDLE;
            endcase
        end
    end

endmodule
