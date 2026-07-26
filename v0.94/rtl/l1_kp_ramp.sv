`ifndef L1_KP_RAMP_SV
`define L1_KP_RAMP_SV
`timescale 1ns/1ps

module l1_kp_ramp (
    input  logic               clk_i,
    input  logic               rstn_i,
    input  logic               start_i,
    input  logic               stop_i,
    input  logic               servo_tick_i,
    input  logic signed [13:0] kp_target_i,
    input  logic        [13:0] kp_step_i,
    input  logic        [15:0] kp_ramp_div_i,
    output logic signed [13:0] kp_effective_o,
    output logic               kp_target_reached_o
);
    logic [15:0] ramp_count_q;
    logic [15:0] ramp_div_w;
    logic signed [14:0] kp_next_w;

    always_comb begin
        ramp_div_w = (kp_ramp_div_i == 16'd0) ? 16'd1 : kp_ramp_div_i;
        kp_next_w = $signed({kp_effective_o[13], kp_effective_o}) +
                    $signed({1'b0, (kp_step_i == 14'd0) ? 14'd1 : kp_step_i});
        kp_target_reached_o = (kp_effective_o == kp_target_i);
    end

    always_ff @(posedge clk_i) begin
        if (!rstn_i) begin
            kp_effective_o <= 14'sd0;
            ramp_count_q <= 16'd0;
        end else if (stop_i) begin
            kp_effective_o <= 14'sd0;
            ramp_count_q <= 16'd0;
        end else if (start_i) begin
            kp_effective_o <= 14'sd0;
            ramp_count_q <= 16'd0;
        end else if (servo_tick_i && !kp_target_reached_o) begin
            if (ramp_count_q + 16'd1 >= ramp_div_w) begin
                ramp_count_q <= 16'd0;
                if (kp_next_w >= $signed({kp_target_i[13], kp_target_i}))
                    kp_effective_o <= kp_target_i;
                else
                    kp_effective_o <= kp_next_w[13:0];
            end else begin
                ramp_count_q <= ramp_count_q + 16'd1;
            end
        end
    end
endmodule
`endif
