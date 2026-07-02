`timescale 1ns / 1ps

// v2B3 timing-repair sequential PI controller.
//
// This module preserves the fixed-point intent of pi_controller.sv while
// splitting one PI update over fifteen clk_i states. pid_ce_i starts a
// transaction; it is a clock-enable pulse, not another clock. The public
// outputs update only in S_OUTPUT, fifteen clk_i edges after pid_ce_i is
// sampled.
//
// Data path per transaction:
// capture inputs -> limit prep -> P multiply -> P scale/I multiply -> I scale
// -> freeze prep -> freeze decide -> I candidate -> I clamp -> I commit
// -> sum prep -> final sum -> output limit compare -> register outputs.
//
// Hardware meaning for FPGA beginners:
// each state is one row of flip-flops. The old seven-state version still left
// the integrator feedback update as one long combinational route through
// current_control_pre, freeze_integrator, integrator_candidate, and
// integrator_accepted. This version registers those intermediate decisions so
// Vivado has much shorter logic to place between two clk_i edges. This
// controller is still for OUT2 oscilloscope observation until separate Vivado
// timing and board checks pass.

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

    typedef enum logic [3:0] {
        S_IDLE,
        S_CAPTURE,
        S_LIMIT_PREP,
        S_P_MUL,
        S_P_SCALE_I_MUL,
        S_I_SCALE,
        S_FREEZE_PREP,
        S_FREEZE_DECIDE,
        S_I_CANDIDATE,
        S_I_CLAMP,
        S_I_COMMIT,
        S_SUM_PRE,
        S_SUM_FINAL,
        S_LIMIT_COMPARE,
        S_OUTPUT
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
    logic signed [ACC_WIDTH-1:0]     limit_pos_q;
    logic signed [ACC_WIDTH-1:0]     limit_neg_q;
    logic signed [ACC_WIDTH-1:0]     p_scaled_q;
    logic signed [ACC_WIDTH-1:0]     i_delta_q;
    logic signed [ACC_WIDTH-1:0]     integrator_q;
    logic signed [ACC_WIDTH-1:0]     integrator_next_q;
    logic signed [ACC_WIDTH-1:0]     control_pre_for_freeze_q;
    logic                            freeze_integrator_q;
    logic signed [ACC_WIDTH-1:0]     integrator_candidate_q;
    logic signed [ACC_WIDTH-1:0]     integrator_accepted_q;
    logic signed [ACC_WIDTH-1:0]     sum_pre_q;
    logic signed [ACC_WIDTH-1:0]     control_pre_q;
    logic signed [OUT_WIDTH-1:0]     control_limited_q;
    logic                            sat_next_q;

    logic        [OUT_WIDTH:0]         output_limit_ext_w;
    logic        [OUT_WIDTH:0]         limit_clamped_w;

    // output_limit_i is unsigned. Clamp it before converting to the signed
    // positive/negative bounds so no implicit signed conversion controls the
    // limiter behavior.
    assign output_limit_ext_w = {1'b0, output_limit_q};
    assign limit_clamped_w = (output_limit_ext_w > OUT_POS_MAX_EXT)
                           ? OUT_POS_MAX_EXT
                           : output_limit_ext_w;

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
            limit_pos_q          <= '0;
            limit_neg_q          <= '0;
            p_scaled_q           <= '0;
            i_delta_q            <= '0;
            integrator_q         <= '0;
            integrator_next_q    <= '0;
            control_pre_for_freeze_q <= '0;
            freeze_integrator_q  <= 1'b0;
            integrator_candidate_q <= '0;
            integrator_accepted_q <= '0;
            sum_pre_q            <= '0;
            control_pre_q        <= '0;
            control_limited_q    <= '0;
            sat_next_q           <= 1'b0;
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
            freeze_integrator_q  <= 1'b0;
            control_limited_q    <= '0;
            sat_next_q           <= 1'b0;
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
                    state_q            <= S_LIMIT_PREP;
                end

                S_LIMIT_PREP: begin
                    limit_pos_q <= $signed({{(ACC_WIDTH - (OUT_WIDTH + 1)){1'b0}}, limit_clamped_w});
                    limit_neg_q <= -$signed({{(ACC_WIDTH - (OUT_WIDTH + 1)){1'b0}}, limit_clamped_w});
                    state_q     <= S_P_MUL;
                end

                S_P_MUL: begin
                    p_product_q <= $signed(error_pol_q) * $signed(kp_q);
                    state_q     <= S_P_SCALE_I_MUL;
                end

                S_P_SCALE_I_MUL: begin
                    p_scaled_q  <= $signed({{(ACC_WIDTH - PRODUCT_WIDTH){p_product_q[PRODUCT_WIDTH-1]}}, p_product_q}) >>> KP_SHIFT;
                    i_product_q <= $signed(error_pol_q) * $signed(ki_q);
                    state_q     <= S_I_SCALE;
                end

                S_I_SCALE: begin
                    i_delta_q <= $signed({{(ACC_WIDTH - PRODUCT_WIDTH){i_product_q[PRODUCT_WIDTH-1]}}, i_product_q}) >>> KI_SHIFT;
                    state_q   <= S_FREEZE_PREP;
                end

                S_FREEZE_PREP: begin
                    control_pre_for_freeze_q <= $signed(p_scaled_q) + $signed(integrator_q) + $signed(offset_ext_q);
                    state_q                  <= S_FREEZE_DECIDE;
                end

                S_FREEZE_DECIDE: begin
                    freeze_integrator_q <=
                        (($signed(control_pre_for_freeze_q) >= $signed(limit_pos_q)) && ($signed(i_delta_q) > ACC_ZERO)) ||
                        (($signed(control_pre_for_freeze_q) <= $signed(limit_neg_q)) && ($signed(i_delta_q) < ACC_ZERO));
                    state_q <= S_I_CANDIDATE;
                end

                S_I_CANDIDATE: begin
                    integrator_candidate_q <= freeze_integrator_q
                                            ? integrator_q
                                            : (integrator_q + i_delta_q);
                    state_q <= S_I_CLAMP;
                end

                S_I_CLAMP: begin
                    if ($signed(integrator_candidate_q) > $signed(limit_pos_q)) begin
                        integrator_accepted_q <= limit_pos_q;
                    end else if ($signed(integrator_candidate_q) < $signed(limit_neg_q)) begin
                        integrator_accepted_q <= limit_neg_q;
                    end else begin
                        integrator_accepted_q <= integrator_candidate_q;
                    end
                    state_q <= S_I_COMMIT;
                end

                S_I_COMMIT: begin
                    if (reset_integrator_q) begin
                        integrator_q      <= '0;
                        integrator_next_q <= '0;
                    end else begin
                        integrator_q      <= integrator_accepted_q;
                        integrator_next_q <= integrator_accepted_q;
                    end
                    state_q <= S_SUM_PRE;
                end

                S_SUM_PRE: begin
                    // integrator_next_q is the accepted value from this
                    // transaction, including reset_integrator handling.
                    sum_pre_q <= $signed(p_scaled_q) + $signed(integrator_next_q);
                    state_q   <= S_SUM_FINAL;
                end

                S_SUM_FINAL: begin
                    control_pre_q <= $signed(sum_pre_q) + $signed(offset_ext_q);
                    state_q       <= S_LIMIT_COMPARE;
                end

                S_LIMIT_COMPARE: begin
                    if ($signed(control_pre_q) > $signed(limit_pos_q)) begin
                        control_limited_q <= limit_pos_q[OUT_WIDTH-1:0];
                        sat_next_q        <= 1'b1;
                    end else if ($signed(control_pre_q) < $signed(limit_neg_q)) begin
                        control_limited_q <= limit_neg_q[OUT_WIDTH-1:0];
                        sat_next_q        <= 1'b1;
                    end else begin
                        control_limited_q <= control_pre_q[OUT_WIDTH-1:0];
                        sat_next_q        <= 1'b0;
                    end
                    state_q <= S_OUTPUT;
                end

                S_OUTPUT: begin
                    control_o <= control_limited_q;
                    sat_o     <= sat_next_q;
                    p_term_o  <= p_scaled_q[31:0];
                    i_term_o  <= integrator_next_q[31:0];
                    state_q   <= S_IDLE;
                end

                default: state_q <= S_IDLE;
            endcase
        end
    end

endmodule
