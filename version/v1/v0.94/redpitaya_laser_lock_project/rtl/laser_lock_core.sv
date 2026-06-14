// laser_lock_core.sv
// 版本：v1ab_passthrough_debug
//
// 本版本只做输入直通调试：
// - OUTPUT_MODE = 0：error_o 输出 pd_i，用来验证 IN1 -> OUT1
// - OUTPUT_MODE = 1：error_o 输出 ref_i，用来验证 IN2 -> OUT1
//
// 硬件大白话：
// 这个模块现在还不是 MTS mixer，也不是 PID。
// 它像一个“二选一调试开关”：
//   选择 pd_i 这根线，或者选择 ref_i 这根线，
//   然后经过 output_protect 保护寄存器送到 error_o。
//
// 本版本不实现：
// mixer、LPF、BPF、PID、sweep、AI。

`timescale 1ns/1ps

module laser_lock_core #(
    // OUTPUT_MODE 是编译时参数。
    // 0：选择 pd_i，用于 v1a_pd_passthrough
    // 1：选择 ref_i，用于 v1b_ref_passthrough
    // 其他值：输出 0，避免误用时输出未知信号
    parameter int OUTPUT_MODE = 0
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

    // 组合选择逻辑。
    // 硬件上等价于一个小 mux：
    // OUTPUT_MODE 选 0 时接 pd_i，选 1 时接 ref_i，其他情况接 0。
    always_comb begin
        unique case (OUTPUT_MODE)
            0:       selected_signal = pd_i;
            1:       selected_signal = ref_i;
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
        .data_o  (error_o)
    );

    // control_o 在第一阶段始终为 0。
    // 这在硬件上等价于把 DAC B 候选控制量固定接地到数字 0。
    assign control_o = 14'sd0;

endmodule
