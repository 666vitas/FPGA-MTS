`timescale 1ns / 1ps

module tb_lpf_core;

    localparam int IN_WIDTH  = 14;
    localparam int OUT_WIDTH = 14;
    localparam int ACC_WIDTH = 32;
    localparam int LPF_SHIFT = 4;

    logic clk_i = 1'b0;
    logic rstn_i;
    logic enable_i;
    logic signed [IN_WIDTH-1:0] x_i;
    logic signed [OUT_WIDTH-1:0] y_o;
    logic signed [OUT_WIDTH-1:0] y_fast;

    logic signed [IN_WIDTH-1:0] prev_y;
    int abs_sum_input;
    int abs_sum_output;

    always #5 clk_i = ~clk_i;

    lpf_core #(
        .IN_WIDTH  (IN_WIDTH),
        .OUT_WIDTH (OUT_WIDTH),
        .ACC_WIDTH (ACC_WIDTH),
        .LPF_SHIFT (LPF_SHIFT)
    ) dut (
        .clk_i    (clk_i),
        .rstn_i   (rstn_i),
        .enable_i (enable_i),
        .x_i      (x_i),
        .y_o      (y_o)
    );

    lpf_core #(
        .IN_WIDTH  (IN_WIDTH),
        .OUT_WIDTH (OUT_WIDTH),
        .ACC_WIDTH (ACC_WIDTH),
        .LPF_SHIFT (0)
    ) dut_fast (
        .clk_i    (clk_i),
        .rstn_i   (rstn_i),
        .enable_i (enable_i),
        .x_i      (x_i),
        .y_o      (y_fast)
    );

    function automatic int abs_int(input int value);
        begin
            abs_int = (value < 0) ? -value : value;
        end
    endfunction

    task automatic check_equal(
        input string name,
        input logic signed [OUT_WIDTH-1:0] actual,
        input logic signed [OUT_WIDTH-1:0] expected
    );
        begin
            if (actual !== expected) begin
                $fatal(1, "%s failed: actual=%0d expected=%0d", name, actual, expected);
            end
        end
    endtask

    task automatic check_true(input string name, input bit condition);
        begin
            if (!condition) begin
                $fatal(1, "%s failed", name);
            end
        end
    endtask

    task automatic apply_reset;
        begin
            rstn_i   = 1'b0;
            enable_i = 1'b1;
            x_i      = '0;
            repeat (3) @(posedge clk_i);
            #1;
            check_equal("reset output", y_o, '0);
            rstn_i = 1'b1;
            repeat (2) @(posedge clk_i);
        end
    endtask

    initial begin
        apply_reset();

        @(negedge clk_i);
        enable_i = 1'b0;
        x_i      = 14'sd3000;
        repeat (3) @(posedge clk_i);
        #1;
        check_equal("enable low output", y_o, 14'sd0);

        @(negedge clk_i);
        enable_i = 1'b1;
        x_i      = 14'sd4096;
        @(posedge clk_i);
        #1;
        check_true("positive step starts below input", (y_o > 14'sd0) && (y_o < 14'sd4096));
        prev_y = y_o;
        repeat (20) begin
            @(posedge clk_i);
            #1;
            check_true("positive step monotonic", y_o >= prev_y);
            check_true("positive step below input", y_o < 14'sd4096);
            prev_y = y_o;
        end
        check_true("positive step approaches input", y_o > 14'sd2500);

        @(negedge clk_i);
        enable_i = 1'b0;
        x_i      = '0;
        @(posedge clk_i);
        #1;
        check_equal("clear before negative test", y_o, 14'sd0);

        @(negedge clk_i);
        enable_i = 1'b1;
        x_i      = -14'sd4096;
        @(posedge clk_i);
        #1;
        check_true("negative step starts below zero", y_o < 14'sd0);
        prev_y = y_o;
        repeat (20) begin
            @(posedge clk_i);
            #1;
            check_true("negative step monotonic", y_o <= prev_y);
            check_true("negative step above input", y_o > -14'sd4096);
            prev_y = y_o;
        end
        check_true("negative step approaches input", y_o < -14'sd2500);

        @(negedge clk_i);
        enable_i = 1'b0;
        x_i      = '0;
        @(posedge clk_i);
        #1;
        check_equal("clear before alternating test", y_o, 14'sd0);

        enable_i       = 1'b1;
        abs_sum_input  = 0;
        abs_sum_output = 0;
        repeat (32) begin
            @(negedge clk_i);
            x_i = (x_i >= 0) ? -14'sd4096 : 14'sd4096;
            abs_sum_input += abs_int(x_i);
            @(posedge clk_i);
            #1;
            abs_sum_output += abs_int(y_o);
        end
        check_true("high frequency alternating input is smoothed",
                   abs_sum_output < (abs_sum_input / 2));

        @(negedge clk_i);
        enable_i = 1'b0;
        x_i      = '0;
        @(posedge clk_i);
        #1;
        check_equal("clear before endpoint test", y_o, 14'sd0);

        @(negedge clk_i);
        enable_i = 1'b1;
        x_i      = 14'sd8191;
        repeat (2) @(posedge clk_i);
        #1;
        check_true("positive endpoint has correct sign", y_o > 14'sd0);
        check_equal("positive endpoint does not wrap", y_fast, 14'sd8191);

        @(negedge clk_i);
        x_i = -14'sd8192;
        repeat (2) @(posedge clk_i);
        #1;
        check_equal("negative endpoint does not wrap", y_fast, -14'sd8192);
        repeat (38) @(posedge clk_i);
        #1;
        check_true("negative endpoint has correct sign", y_o < 14'sd0);

        $display("PASS: tb_lpf_core");
        $finish;
    end

endmodule
