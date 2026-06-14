// tb_laser_lock_core.sv
// v1_pd_passthrough 的最小 testbench。
//
// 硬件大白话：
// testbench 不是要综合进 FPGA 的电路。
// 它像一个“虚拟实验台”：产生时钟、复位、输入信号，然后检查输出是否符合预期。

`timescale 1ns/1ps

module tb_laser_lock_core;

    logic               clk_i;
    logic               rstn_i;
    logic signed [13:0] pd_i;
    logic signed [13:0] ref_i;
    logic signed [13:0] error_o;
    logic signed [13:0] control_o;

    int error_count;

    // 实例化待测试模块。
    // 这里的连线方式和未来 top 里的连线思想类似：
    // testbench 给输入，观察 error_o/control_o 输出。
    laser_lock_core dut (
        .clk_i    (clk_i),
        .rstn_i   (rstn_i),
        .pd_i     (pd_i),
        .ref_i    (ref_i),
        .error_o  (error_o),
        .control_o(control_o)
    );

    // 生成 100 MHz 仿真时钟：周期 10 ns。
    // 真实 Red Pitaya 的 adc_clk 频率由官方 PLL 决定；
    // 本 testbench 只需要一个稳定时钟来验证时序逻辑。
    initial begin
        clk_i = 1'b0;
        forever #5 clk_i = ~clk_i;
    end

    // 检查输出是否等于预期值。
    task automatic check_outputs(
        input logic signed [13:0] expected_error,
        input logic signed [13:0] expected_control,
        input string              test_name
    );
        begin
            if (error_o !== expected_error) begin
                $error("%s: error_o mismatch, expected=%0d actual=%0d",
                       test_name, expected_error, error_o);
                error_count++;
            end

            if (control_o !== expected_control) begin
                $error("%s: control_o mismatch, expected=%0d actual=%0d",
                       test_name, expected_control, control_o);
                error_count++;
            end
        end
    endtask

    initial begin
        error_count = 0;

        // 初始输入。
        rstn_i = 1'b0;
        pd_i   = 14'sd123;
        ref_i  = -14'sd456;

        // 测试 1：复位行为。
        // rstn_i 拉低时，error_o 和 control_o 必须归零。
        #2;
        check_outputs(14'sd0, 14'sd0, "reset_low_clears_outputs");

        // 释放复位。
        rstn_i = 1'b1;

        // 测试 2：pd_i 为正数时，error_o 在下一个 clk_i 上升沿跟随。
        pd_i  = 14'sd1000;
        ref_i = 14'sd111;
        @(posedge clk_i);
        #1;
        check_outputs(14'sd1000, 14'sd0, "positive_pd_passthrough");

        // 测试 3：pd_i 为负数时，error_o 正确跟随 signed 数据。
        pd_i  = -14'sd2048;
        ref_i = 14'sd222;
        @(posedge clk_i);
        #1;
        check_outputs(-14'sd2048, 14'sd0, "negative_pd_passthrough");

        // 测试 4：pd_i 为 0 时，error_o 为 0。
        pd_i  = 14'sd0;
        ref_i = -14'sd333;
        @(posedge clk_i);
        #1;
        check_outputs(14'sd0, 14'sd0, "zero_pd_passthrough");

        // 测试 5：ref_i 变化不影响 error_o。
        // pd_i 保持不变，只改变 ref_i；v1 中 error_o 应继续等于 pd_i。
        pd_i  = 14'sd321;
        ref_i = 14'sd10;
        @(posedge clk_i);
        #1;
        check_outputs(14'sd321, 14'sd0, "ref_change_step_1");

        ref_i = -14'sd4096;
        @(posedge clk_i);
        #1;
        check_outputs(14'sd321, 14'sd0, "ref_change_step_2");

        ref_i = 14'sd4095;
        @(posedge clk_i);
        #1;
        check_outputs(14'sd321, 14'sd0, "ref_change_step_3");

        // 测试 6：运行过程中再次复位，输出必须清零。
        rstn_i = 1'b0;
        #2;
        check_outputs(14'sd0, 14'sd0, "reset_again_clears_outputs");

        if (error_count == 0) begin
            $display("PASS: tb_laser_lock_core v1_pd_passthrough all checks passed.");
        end else begin
            $display("FAIL: tb_laser_lock_core found %0d error(s).", error_count);
        end

        $finish;
    end

endmodule
