`timescale 1ns / 1ps

module tb_laser_lock_core_v1d;

    localparam int IN_WIDTH      = 14;
    localparam int OUT_WIDTH     = 14;
    localparam int SHIFT         = 13;
    localparam int PRODUCT_WIDTH = IN_WIDTH * 2;

    logic clk_i = 1'b0;
    logic rstn_i;
    logic signed [13:0] pd_i;
    logic signed [13:0] ref_i;

    logic signed [13:0] error_mode0;
    logic signed [13:0] control_mode0;
    logic signed [13:0] error_mode1;
    logic signed [13:0] control_mode1;
    logic signed [13:0] error_mode2;
    logic signed [13:0] control_mode2;
    logic signed [13:0] error_mode3;
    logic signed [13:0] control_mode3;
    logic signed [13:0] error_invalid;
    logic signed [13:0] control_invalid;

    localparam logic signed [OUT_WIDTH-1:0] OUT_MAX =
        {1'b0, {(OUT_WIDTH-1){1'b1}}};
    localparam logic signed [OUT_WIDTH-1:0] OUT_MIN =
        {1'b1, {(OUT_WIDTH-1){1'b0}}};
    localparam logic signed [PRODUCT_WIDTH-1:0] SAT_MAX =
        {{(PRODUCT_WIDTH-OUT_WIDTH){OUT_MAX[OUT_WIDTH-1]}}, OUT_MAX};
    localparam logic signed [PRODUCT_WIDTH-1:0] SAT_MIN =
        {{(PRODUCT_WIDTH-OUT_WIDTH){OUT_MIN[OUT_WIDTH-1]}}, OUT_MIN};

    always #5 clk_i = ~clk_i;

    laser_lock_core #(.OUTPUT_MODE(0)) dut_mode0 (
        .clk_i     (clk_i),
        .rstn_i    (rstn_i),
        .pd_i      (pd_i),
        .ref_i     (ref_i),
        .error_o   (error_mode0),
        .control_o (control_mode0)
    );

    laser_lock_core #(.OUTPUT_MODE(1)) dut_mode1 (
        .clk_i     (clk_i),
        .rstn_i    (rstn_i),
        .pd_i      (pd_i),
        .ref_i     (ref_i),
        .error_o   (error_mode1),
        .control_o (control_mode1)
    );

    laser_lock_core #(.OUTPUT_MODE(2)) dut_mode2 (
        .clk_i     (clk_i),
        .rstn_i    (rstn_i),
        .pd_i      (pd_i),
        .ref_i     (ref_i),
        .error_o   (error_mode2),
        .control_o (control_mode2)
    );

    laser_lock_core #(.OUTPUT_MODE(3)) dut_mode3 (
        .clk_i     (clk_i),
        .rstn_i    (rstn_i),
        .pd_i      (pd_i),
        .ref_i     (ref_i),
        .error_o   (error_mode3),
        .control_o (control_mode3)
    );

    laser_lock_core #(.OUTPUT_MODE(99)) dut_invalid (
        .clk_i     (clk_i),
        .rstn_i    (rstn_i),
        .pd_i      (pd_i),
        .ref_i     (ref_i),
        .error_o   (error_invalid),
        .control_o (control_invalid)
    );

    function automatic logic signed [OUT_WIDTH-1:0] expected_mix(
        input logic signed [IN_WIDTH-1:0] pd,
        input logic signed [IN_WIDTH-1:0] ref_sample
    );
        logic signed [PRODUCT_WIDTH-1:0] product;
        logic signed [PRODUCT_WIDTH-1:0] scaled;
        begin
            product = $signed(pd) * $signed(ref_sample);
            scaled  = product >>> SHIFT;
            if (scaled > SAT_MAX) begin
                expected_mix = OUT_MAX;
            end else if (scaled < SAT_MIN) begin
                expected_mix = OUT_MIN;
            end else begin
                expected_mix = scaled[OUT_WIDTH-1:0];
            end
        end
    endfunction

    task automatic check_equal(
        input string name,
        input logic signed [13:0] actual,
        input logic signed [13:0] expected
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

    task automatic check_controls_zero;
        begin
            check_equal("control mode0", control_mode0, 14'sd0);
            check_equal("control mode1", control_mode1, 14'sd0);
            check_equal("control mode2", control_mode2, 14'sd0);
            check_equal("control mode3", control_mode3, 14'sd0);
            check_equal("control invalid", control_invalid, 14'sd0);
        end
    endtask

    initial begin
        rstn_i = 1'b0;
        pd_i   = '0;
        ref_i  = '0;
        repeat (4) @(posedge clk_i);
        #1;
        check_equal("reset mode0", error_mode0, 14'sd0);
        check_equal("reset mode1", error_mode1, 14'sd0);
        check_equal("reset mode2", error_mode2, 14'sd0);
        check_equal("reset mode3", error_mode3, 14'sd0);
        check_equal("reset invalid", error_invalid, 14'sd0);
        check_controls_zero();

        rstn_i = 1'b1;
        @(negedge clk_i);
        pd_i  = 14'sd1234;
        ref_i = -14'sd2222;
        @(posedge clk_i);
        #1;
        check_equal("OUTPUT_MODE 0 pd passthrough", error_mode0, 14'sd1234);
        check_equal("OUTPUT_MODE 1 ref passthrough", error_mode1, -14'sd2222);
        check_equal("OUTPUT_MODE invalid", error_invalid, 14'sd0);
        check_controls_zero();

        repeat (2) @(posedge clk_i);
        #1;
        check_equal("OUTPUT_MODE 2 raw mixer", error_mode2, expected_mix(14'sd1234, -14'sd2222));
        check_controls_zero();

        @(negedge clk_i);
        pd_i  = 14'sd4096;
        ref_i = 14'sd4096;
        repeat (4) @(posedge clk_i);
        #1;
        check_equal("OUTPUT_MODE 2 raw mixer positive", error_mode2, 14'sd2048);
        check_true("OUTPUT_MODE 3 starts slower than raw mixer",
                   (error_mode3 >= 14'sd0) && (error_mode3 < error_mode2));

        repeat (40) @(posedge clk_i);
        #1;
        check_true("OUTPUT_MODE 3 lpf moves toward raw mixer",
                   (error_mode3 > 14'sd0) && (error_mode3 < error_mode2));
        check_controls_zero();

        @(negedge clk_i);
        rstn_i = 1'b0;
        repeat (3) @(posedge clk_i);
        #1;
        check_equal("reset mode3 after activity", error_mode3, 14'sd0);
        check_controls_zero();

        $display("PASS: tb_laser_lock_core_v1d");
        $finish;
    end

endmodule
