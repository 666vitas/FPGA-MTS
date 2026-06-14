// tb_laser_lock_core_v1ab.sv
// v1ab_passthrough_debug 自检 testbench。
//
// 这个文件不会进入 FPGA。
// 它像一个虚拟实验台：产生 125 MHz 时钟、reset、pd_i/ref_i 测试输入，
// 然后自动检查两个模式是否正确。

`timescale 1ns/1ps

module tb_laser_lock_core_v1ab;

    logic               clk_i;
    logic               rstn_i;
    logic signed [13:0] pd_i;
    logic signed [13:0] ref_i;

    logic signed [13:0] error_pd_o;
    logic signed [13:0] control_pd_o;
    logic signed [13:0] error_ref_o;
    logic signed [13:0] control_ref_o;

    // 125 MHz clock：周期 8 ns。
    // Red Pitaya STEMlab 125-14 的 ADC 典型采样节拍就是 125 MS/s 量级。
    initial begin
        clk_i = 1'b0;
        forever #4 clk_i = ~clk_i;
    end

    // DUT 1：OUTPUT_MODE = 0，验证 pd_i -> error_o。
    laser_lock_core #(
        .OUTPUT_MODE(0)
    ) dut_pd (
        .clk_i    (clk_i),
        .rstn_i   (rstn_i),
        .pd_i     (pd_i),
        .ref_i    (ref_i),
        .error_o  (error_pd_o),
        .control_o(control_pd_o)
    );

    // DUT 2：OUTPUT_MODE = 1，验证 ref_i -> error_o。
    laser_lock_core #(
        .OUTPUT_MODE(1)
    ) dut_ref (
        .clk_i    (clk_i),
        .rstn_i   (rstn_i),
        .pd_i     (pd_i),
        .ref_i    (ref_i),
        .error_o  (error_ref_o),
        .control_o(control_ref_o)
    );

    task automatic check_equal_14(
        input logic signed [13:0] actual,
        input logic signed [13:0] expected,
        input string              name
    );
        begin
            if (actual !== expected) begin
                $fatal(1, "%s failed: expected=%0d actual=%0d",
                       name, expected, actual);
            end
        end
    endtask

    task automatic check_controls_zero(input string name);
        begin
            check_equal_14(control_pd_o,  14'sd0, {name, " dut_pd.control_o"});
            check_equal_14(control_ref_o, 14'sd0, {name, " dut_ref.control_o"});
        end
    endtask

    task automatic check_reset_outputs(input string name);
        begin
            check_equal_14(error_pd_o,   14'sd0, {name, " dut_pd.error_o"});
            check_equal_14(error_ref_o,  14'sd0, {name, " dut_ref.error_o"});
            check_controls_zero(name);
        end
    endtask

    task automatic drive_and_check(
        input logic signed [13:0] pd_value,
        input logic signed [13:0] ref_value,
        input string              name
    );
        begin
            pd_i  = pd_value;
            ref_i = ref_value;

            // output_protect 是时序寄存输出，所以等一个 clk_i 上升沿后检查。
            @(posedge clk_i);
            #1;

            check_equal_14(error_pd_o,  pd_value,  {name, " dut_pd.error_o follows pd_i"});
            check_equal_14(error_ref_o, ref_value, {name, " dut_ref.error_o follows ref_i"});
            check_controls_zero(name);
        end
    endtask

    initial begin
        rstn_i = 1'b0;
        pd_i   = 14'sd1234;
        ref_i  = -14'sd567;

        // reset 期间检查两个 DUT 输出都为 0。
        #2;
        check_reset_outputs("reset_low");

        // 释放 reset。
        rstn_i = 1'b1;

        // pd_i 正数、ref_i 正数。
        drive_and_check(14'sd1000, 14'sd2000, "positive_pd_positive_ref");

        // pd_i 负数、ref_i 保持正数。
        drive_and_check(-14'sd1000, 14'sd2000, "negative_pd_positive_ref");

        // pd_i 为 0，ref_i 为正数。
        drive_and_check(14'sd0, 14'sd2000, "zero_pd_positive_ref");

        // ref_i 负数，同时 pd_i 为正数。
        drive_and_check(14'sd123, -14'sd2048, "positive_pd_negative_ref");

        // ref_i 为 0，同时 pd_i 为负数。
        drive_and_check(-14'sd321, 14'sd0, "negative_pd_zero_ref");

        // pd_i 和 ref_i 都为 0。
        drive_and_check(14'sd0, 14'sd0, "zero_pd_zero_ref");

        // 运行中再次 reset，确认输出清零。
        rstn_i = 1'b0;
        #2;
        check_reset_outputs("reset_again");

        $display("V1AB PASSTHROUGH DEBUG TEST PASSED");
        $finish;
    end

endmodule
