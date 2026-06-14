// laser_lock_core.sv
//
// v1d_mixer_lpf status:
// - OUTPUT_MODE = 0: IN1 / pd_i -> OUT1 passthrough.
// - OUTPUT_MODE = 1: IN2 / ref_i -> OUT1 passthrough.
// - OUTPUT_MODE = 2: raw mixer output -> OUT1.
// - OUTPUT_MODE = 3: mixer + post-mixer LPF output -> OUT1.
//
// This module still does not implement pre-mixer 10 MHz LPF, 1.8 MHz HPF,
// digital gain, I/Q, PID, sweep, AI, D2-125 drive, or laser feedback.

`timescale 1ns/1ps

module laser_lock_core #(
    // OUTPUT_MODE 是编译时参数。
    // 0: IN1 / pd_i -> OUT1, used to confirm the IN1 ADC to OUT1 DAC path.
    // 1: IN2 / ref_i -> OUT1, used to confirm the IN2 ADC to OUT1 DAC path.
    // 2: raw mixer output, used to observe IN1 x IN2 before LPF.
    // 3: mixer + post-mixer LPF output, used to observe low/difference/baseband output.
    // other: output 0, so an invalid mode does not drive an unknown signal.
    parameter int OUTPUT_MODE = 0,
    parameter int CLK_HZ = 125_000_000,
    parameter int PID_UPDATE_HZ = 10_000,
    parameter bit PID_ENABLE_DEFAULT = 1'b1,
    parameter bit PID_HOLD_DEFAULT = 1'b0,
    parameter bit PID_RESET_INTEGRATOR_DEFAULT = 1'b0,
    parameter bit PID_POLARITY_DEFAULT = 1'b0,
    parameter logic signed [15:0] PID_KP_DEFAULT = 16'sd2048,
    parameter logic signed [15:0] PID_KI_DEFAULT = 16'sd0,
    parameter logic signed [13:0] PID_OFFSET_DEFAULT = 14'sd0,
    parameter logic [13:0] PID_OUTPUT_LIMIT_DEFAULT = 14'd1500
) (
    // clk_i：模块时钟。
    // 未来接官方 adc_clk，让本模块和 adc_dat[0]/adc_dat[1] 在同一个时钟域。
    input  logic               clk_i,

    // rstn_i：active-low reset，低电平有效。
    // 未来接官方 adc_rstn。rstn_i = 0 时 error_o/control_o 都归零。
    input  logic               rstn_i,

    // pd_i：PD 光强信号输入。
    // 未来来自 adc_dat[0]，对应 Red Pitaya IN1。
    input  logic signed [13:0] pd_i,

    // ref_i：外部 4.6 MHz REF 输入。
    // 未来来自 adc_dat[1]，对应 Red Pitaya IN2。
    input  logic signed [13:0] ref_i,

    // error_o：调试输出。
    // v1ab 中输出 pd_i 或 ref_i 的保护后结果，未来接 DAC A / OUT1 候选路径。
    output logic signed [13:0] error_o,

    // control_o：控制输出。
    // 第一阶段不做 PID，不控制激光器，所以始终为 0。
    output logic signed [13:0] control_o
);

    logic signed [13:0] selected_signal;
    logic signed [13:0] mixer_signal;
    logic signed [13:0] lpf_signal;
    logic signed [13:0] protected_error;

    localparam int PID_CE_DIV = (PID_UPDATE_HZ <= 0) ? 1 : ((CLK_HZ / PID_UPDATE_HZ) < 1 ? 1 : (CLK_HZ / PID_UPDATE_HZ));
    localparam int PID_CE_COUNT_WIDTH = (PID_CE_DIV <= 1) ? 1 : $clog2(PID_CE_DIV);

    logic [PID_CE_COUNT_WIDTH-1:0] pid_ce_cnt_q;
    logic pid_ce_q;
    logic signed [31:0] p_term_unused;
    logic signed [31:0] i_term_unused;
    logic sat_unused;

    mixer_core #(
        .IN_WIDTH  (14),
        .OUT_WIDTH (14),
        .SHIFT     (13)
    ) i_mixer_core (
        .clk_i    (clk_i),
        .rstn_i   (rstn_i),
        .enable_i (1'b1),
        .pd_i     (pd_i),
        .ref_i    (ref_i),
        .mix_o    (mixer_signal)
    );

    // v1d post-mixer LPF.
    // Hardware meaning:
    // mixer_core still only does pd_i x ref_i. The LPF is a separate bank of
    // flip-flops and add/subtract/shift logic after the mixer, matching the
    // "mixer output -> low-pass" part of the real MTS chain.
    lpf_core #(
        .IN_WIDTH  (14),
        .OUT_WIDTH (14),
        .ACC_WIDTH (32),
        .LPF_SHIFT (12)
    ) i_lpf_core (
        .clk_i    (clk_i),
        .rstn_i   (rstn_i),
        .enable_i (1'b1),
        .x_i      (mixer_signal),
        .y_o      (lpf_signal)
    );

    // 组合选择逻辑。
    // 硬件上等价于一个小 mux：
    // OUTPUT_MODE 选 0 时接 pd_i，选 1 时接 ref_i，
    // 选 2 时接 raw mixer，选 3 时接 mixer + LPF，其他情况接 0。
    always_comb begin
        unique case (OUTPUT_MODE)
            0:       selected_signal = pd_i;
            1:       selected_signal = ref_i;
            2:       selected_signal = mixer_signal;
            3:       selected_signal = lpf_signal;
            default: selected_signal = 14'sd0;
        endcase
    end

    // output_protect 是最后一级输出保护。
    // v1ab 中 enable_i 固定为 1，表示正常透传 selected_signal。
    // rstn_i 拉低时，output_protect 会让 error_o 清零。
    output_protect u_output_protect (
        .clk_i   (clk_i),
        .rstn_i  (rstn_i),
        .enable_i(1'b1),
        .data_i  (selected_signal),
        .data_o  (protected_error)
    );

    // control_o 在第一阶段始终为 0。
    // 这在硬件上等价于把 DAC B 候选控制量固定接地到数字 0。
    assign error_o = protected_error;

    always_ff @(posedge clk_i) begin
        if (!rstn_i) begin
            pid_ce_cnt_q <= '0;
            pid_ce_q     <= 1'b0;
        end else if (PID_CE_DIV <= 1) begin
            pid_ce_cnt_q <= '0;
            pid_ce_q     <= 1'b1;
        end else if (pid_ce_cnt_q == PID_CE_DIV - 1) begin
            pid_ce_cnt_q <= '0;
            pid_ce_q     <= 1'b1;
        end else begin
            pid_ce_cnt_q <= pid_ce_cnt_q + 1'b1;
            pid_ce_q     <= 1'b0;
        end
    end

    pi_controller #(
        .ERROR_WIDTH(14),
        .GAIN_WIDTH (16),
        .OUT_WIDTH  (14),
        .ACC_WIDTH  (48),
        .KP_SHIFT   (12),
        .KI_SHIFT   (12)
    ) i_pi_controller (
        .clk_i             (clk_i),
        .rstn_i            (rstn_i),
        .pid_ce_i          (pid_ce_q),
        .enable_i          (PID_ENABLE_DEFAULT),
        .hold_i            (PID_HOLD_DEFAULT),
        .reset_integrator_i(PID_RESET_INTEGRATOR_DEFAULT),
        .polarity_i        (PID_POLARITY_DEFAULT),
        .error_i           (protected_error),
        .kp_i              (PID_KP_DEFAULT),
        .ki_i              (PID_KI_DEFAULT),
        .offset_i          (PID_OFFSET_DEFAULT),
        .output_limit_i    (PID_OUTPUT_LIMIT_DEFAULT),
        .control_o         (control_o),
        .p_term_o          (p_term_unused),
        .i_term_o          (i_term_unused),
        .sat_o             (sat_unused)
    );

endmodule
