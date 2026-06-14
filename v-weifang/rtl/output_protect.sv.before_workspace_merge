// output_protect.sv
// 版本：v1ab_passthrough_debug
//
// 作用：
// - reset 时输出 0；
// - enable_i = 0 时输出 0；
// - enable_i = 1 时，把 14 bit signed 输入寄存后输出。
//
// 硬件大白话：
// 这个模块像 OUT1 前面的一道简单保险门。
// 现在第一版输入和输出都是 14 bit，所以不做复杂 saturation。
// 后续 mixer 版本会出现 28 bit 乘法结果，那时再扩展宽位宽 saturation。

`timescale 1ns/1ps

module output_protect (
    // clk_i：输出保护寄存器的时钟。
    input  logic               clk_i,

    // rstn_i：active-low reset，低电平有效。
    // rstn_i = 0 时 data_o 立刻清零。
    input  logic               rstn_i,

    // enable_i：输出使能。
    // enable_i = 0 时，即使 data_i 有信号，data_o 也输出 0。
    input  logic               enable_i,

    // data_i：待输出的 14 bit signed 信号。
    input  logic signed [13:0] data_i,

    // data_o：保护后的 14 bit signed 输出。
    output logic signed [13:0] data_o
);

    // 时序保护逻辑。
    // - negedge rstn_i：异步复位，方便系统 reset 时快速回到安全输出；
    // - posedge clk_i：正常工作时每个时钟更新一次输出。
    always_ff @(posedge clk_i or negedge rstn_i) begin
        if (!rstn_i) begin
            data_o <= 14'sd0;
        end else if (!enable_i) begin
            data_o <= 14'sd0;
        end else begin
            data_o <= data_i;
        end
    end

endmodule
