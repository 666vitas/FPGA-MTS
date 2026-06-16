// laser_lock_core.sv
//
// v1d_mixer_lpf status:
// - OUTPUT_MODE = 0: IN1 / pd_i -> OUT1 passthrough.
// - OUTPUT_MODE = 1: IN2 / ref_i -> OUT1 passthrough.
// - OUTPUT_MODE = 2: raw mixer output -> OUT1.
// - OUTPUT_MODE = 3: mixer + post-mixer LPF output -> OUT1.
//
// This module still does not implement pre-mixer 10 MHz LPF, 1.8 MHz HPF,
// digital gain, I/Q, sweep, AI, D2-125 drive, or laser feedback.
// v2B1 adds a Shadow Control path: the protected error signal is observed on
// OUT1 and also feeds the OUT2 shadow-control logic.
//
// Current v2B1 hardware meaning:
// - IN1 is the pre-mixer PD/MTS signal, kept within the Red Pitaya +/-1 V range.
// - IN2 is the external REF signal, also kept within +/-1 V.
// - OUT1 is the protected FPGA mixer+LPF error observation point.
// - OUT2 is only a small timing-safe P-only shadow control signal for
//   oscilloscope observation.
// This is not the old "D2-125 DC Error -> Red Pitaya IN1" route, and it is not
// a complete D2-125 replacement. Ramp, scan/lock switching, Aux Servo Output,
// relock, and lock-quality decisions belong to later stages.
//
// Timing note:
// A manual Vivado implementation run showed that directly placing the complete
// pi_controller in the v2B1 top-level path failed timing at 125 MHz
// (WNS about -10.995 ns). The worst path was inside
// i_laser_lock_core/i_pi_controller, through DSP48E1/CARRY4/integrator/
// anti-windup/control limiting logic. That PI core remains valuable as the
// v2A-verified complete PI module, but the default v2B1 board path now uses a
// small registered P-only shadow-control path. The complete PI branch is kept
// only for future pipeline work.

`timescale 1ns/1ps

module laser_lock_core #(
    // OUTPUT_MODE 是编译时参数。
    // 0: IN1 / pd_i -> OUT1, used to confirm the IN1 ADC to OUT1 DAC path.
    // 1: IN2 / ref_i -> OUT1, used to confirm the IN2 ADC to OUT1 DAC path.
    // 2: raw mixer output, used to observe IN1 x IN2 before LPF.
    // 3: mixer + post-mixer LPF output, used to observe low/difference/baseband output.
    // other: output 0, so an invalid mode does not drive an unknown signal.
    // In the current v2B1 board test, OUTPUT_MODE=3 means OUT1/CH2 should show
    // the FPGA-generated error, about 0.12 to 0.15 V in the user's present
    // observation. OUT2/CH4 should show the P-only control derived from it.
    parameter int OUTPUT_MODE = 0,
    // USE_FULL_PI_CONTROLLER selects which OUT2 control path is elaborated.
    // 0: timing-safe P-only Shadow Control. This is the current v2B1 default.
    //    It is only for OUT2 oscilloscope observation.
    // 1: instantiate the complete v2A pi_controller. This is preserved for
    //    future pipeline work; direct use in the 125 MHz main project has
    //    already shown timing failure and is not the default board path.
    parameter bit USE_FULL_PI_CONTROLLER = 1'b0,
    // CLK_HZ is the input clock rate. In the real Red Pitaya top level this is
    // the ADC clock domain, about 125 MHz. The PI path must stay in this clock
    // domain; do not create a separate PI clock.
    parameter int CLK_HZ = 125_000_000,
    // PID_UPDATE_HZ is the PI update rate. A one-cycle clock-enable pulse is
    // generated from CLK_HZ so pi_controller updates at this slower rate.
    parameter int PID_UPDATE_HZ = 10_000,
    // v2B1 enables the controller only because OUT2 is restricted to an
    // oscilloscope-only Shadow PI test. Before OUT2 is connected to any real
    // actuator, the enable strategy must be reviewed and made safe again.
    parameter bit PID_ENABLE_DEFAULT = 1'b1,
    parameter bit PID_HOLD_DEFAULT = 1'b0,
    parameter bit PID_RESET_INTEGRATOR_DEFAULT = 1'b0,
    parameter bit PID_POLARITY_DEFAULT = 1'b0,
    // Kp=2048 with KP_SHIFT=12 makes OUT2 approximately one half of error_o.
    // If OUT1 error is about 0.12 to 0.15 V, the expected OUT2 control is about
    // 0.06 to 0.075 V.
    parameter logic signed [15:0] PID_KP_DEFAULT = 16'sd2048,
    // Ki=0 makes this first Shadow PI integration a P-only board observation.
    // This avoids a slow integrator climb while the output is only being viewed.
    parameter logic signed [15:0] PID_KI_DEFAULT = 16'sd0,
    parameter logic signed [13:0] PID_OFFSET_DEFAULT = 14'sd0,
    // 1500 counts is roughly +/-0.18 V on the Red Pitaya output scale. It keeps
    // OUT2 far below the +/-1 V full-scale range during the oscilloscope test.
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

    // control_o：Shadow Control 输出。
    // v2B1 只接 OUT2 示波器观察，不直接控制激光器、不接 D2-125
    // Servo Output、不接 Scan。If this signal is ever routed to a real actuator,
    // the physical voltage range, polarity, bandwidth, and initial pid_ce rate
    // must be reviewed first.
    output logic signed [13:0] control_o
);

    logic signed [13:0] selected_signal;
    logic signed [13:0] mixer_signal;
    logic signed [13:0] lpf_signal;
    // protected_error is the 14-bit signed error after output_protect.
    // OUT1 shows this same protected_error, and the OUT2 Shadow Control
    // calculation uses it too. This makes the oscilloscope-visible OUT1 error
    // and the OUT2 control calculation come from the same FPGA signal.
    logic signed [13:0] protected_error;

    // Divide the ADC clock into a single-cycle clock-enable pulse for PI
    // updates. This is not a new clock. It prevents PI/I-term updates from
    // happening on every 125 MHz sample.
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

    // OUT1 继续观察保护后的 error；同一个 protected_error 也进入 Shadow PI。
    // Board expectation: OUT1/CH2 is the "can I still see the FPGA error?"
    // safety channel. If OUT1 disappears or changes meaning, v2B1 must stop.
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

    generate
        if (USE_FULL_PI_CONTROLLER) begin : g_full_pi_controller
            // Complete PI path, preserved but not used by the default v2B1
            // board build.
            //
            // Hardware meaning:
            // pi_controller is the FPGA version of the D2-125 servo core's
            // basic Error Input -> Servo PI/PID -> Servo Output path. It is not
            // the full D2-125: there is no ramp, Aux Servo Output, scan/lock
            // FSM, peak search, relock, or lock-quality logic here.
            //
            // Timing warning:
            // Directly using this complete PI branch in the 125 MHz main
            // project caused implementation timing failure. Future v2B2/v2B3
            // work should pipeline this PI path before making it the default
            // OUT2 route again.
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
        end else begin : g_timing_safe_p_only
            localparam logic [13:0] P_ONLY_OUT_POS_MAX_U = 14'd8191;
            localparam logic signed [14:0] P_ONLY_LIMIT_POS =
                (PID_OUTPUT_LIMIT_DEFAULT > P_ONLY_OUT_POS_MAX_U)
                    ? 15'sd8191
                    : $signed({1'b0, PID_OUTPUT_LIMIT_DEFAULT});
            localparam logic signed [14:0] P_ONLY_LIMIT_NEG = -P_ONLY_LIMIT_POS;

            logic signed [14:0] p_only_error_ext_w;
            logic signed [14:0] p_only_error_pol_w;
            logic signed [14:0] p_only_scaled_w;
            logic signed [13:0] p_only_limited_w;

            // Timing-safe v2B1 default path:
            //
            // protected_error -> optional polarity -> arithmetic right shift by
            // one -> output_limit -> registered control_o.
            //
            // This is deliberately much smaller than the complete PI path:
            // no DSP multiplier, no 48-bit integrator, no anti-windup freeze
            // tree, and no long P+I+offset limiter chain. OUT2 is about half
            // of OUT1 because of the >>> 1 scale, so a 0.12~0.15 V OUT1 error
            // should produce about 0.06~0.075 V on OUT2. The 1500-count limit
            // keeps OUT2 near +/-0.18 V and far from the +/-1 V Red Pitaya
            // output range. OUT2 remains oscilloscope-only: do not connect it
            // to a laser, D2-125 Servo Output, or Scan input.
            assign p_only_error_ext_w = {protected_error[13], protected_error};
            assign p_only_error_pol_w = PID_POLARITY_DEFAULT
                                      ? -p_only_error_ext_w
                                      :  p_only_error_ext_w;
            assign p_only_scaled_w = p_only_error_pol_w >>> 1;

            always_comb begin
                if (p_only_scaled_w > P_ONLY_LIMIT_POS) begin
                    p_only_limited_w = P_ONLY_LIMIT_POS[13:0];
                end else if (p_only_scaled_w < P_ONLY_LIMIT_NEG) begin
                    p_only_limited_w = P_ONLY_LIMIT_NEG[13:0];
                end else begin
                    p_only_limited_w = p_only_scaled_w[13:0];
                end
            end

            always_ff @(posedge clk_i) begin
                if (!rstn_i) begin
                    control_o <= 14'sd0;
                end else if (!PID_ENABLE_DEFAULT) begin
                    control_o <= 14'sd0;
                end else if (PID_HOLD_DEFAULT) begin
                    control_o <= control_o;
                end else if (pid_ce_q) begin
                    control_o <= p_only_limited_w;
                end else begin
                    control_o <= control_o;
                end
            end

            assign p_term_unused = {{18{p_only_limited_w[13]}}, p_only_limited_w};
            assign i_term_unused = 32'sd0;
            assign sat_unused    = (p_only_scaled_w > P_ONLY_LIMIT_POS) ||
                                   (p_only_scaled_w < P_ONLY_LIMIT_NEG);
        end
    endgenerate

endmodule
