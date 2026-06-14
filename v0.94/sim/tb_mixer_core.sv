`timescale 1ns / 1ps

module tb_mixer_core;

    localparam int IN_WIDTH      = 14;
    localparam int OUT_WIDTH     = 14;
    localparam int SHIFT         = 13;
    localparam int PRODUCT_WIDTH = IN_WIDTH * 2;

    logic clk_i = 1'b0;
    logic rstn_i;
    logic enable_i;
    logic signed [IN_WIDTH-1:0] pd_i;
    logic signed [IN_WIDTH-1:0] ref_i;
    logic signed [OUT_WIDTH-1:0] mix_o;

    localparam logic signed [IN_WIDTH-1:0] IN_MAX =
        {1'b0, {(IN_WIDTH-1){1'b1}}};
    localparam logic signed [IN_WIDTH-1:0] IN_MIN =
        {1'b1, {(IN_WIDTH-1){1'b0}}};

    localparam logic signed [OUT_WIDTH-1:0] OUT_MAX =
        {1'b0, {(OUT_WIDTH-1){1'b1}}};
    localparam logic signed [OUT_WIDTH-1:0] OUT_MIN =
        {1'b1, {(OUT_WIDTH-1){1'b0}}};
    localparam logic signed [PRODUCT_WIDTH-1:0] SAT_MAX =
        {{(PRODUCT_WIDTH-OUT_WIDTH){OUT_MAX[OUT_WIDTH-1]}}, OUT_MAX};
    localparam logic signed [PRODUCT_WIDTH-1:0] SAT_MIN =
        {{(PRODUCT_WIDTH-OUT_WIDTH){OUT_MIN[OUT_WIDTH-1]}}, OUT_MIN};

    always #5 clk_i = ~clk_i;

    mixer_core #(
        .IN_WIDTH  (IN_WIDTH),
        .OUT_WIDTH (OUT_WIDTH),
        .SHIFT     (SHIFT)
    ) dut (
        .clk_i    (clk_i),
        .rstn_i   (rstn_i),
        .enable_i (enable_i),
        .pd_i     (pd_i),
        .ref_i    (ref_i),
        .mix_o    (mix_o)
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
        input logic signed [OUT_WIDTH-1:0] actual,
        input logic signed [OUT_WIDTH-1:0] expected
    );
        begin
            if (actual !== expected) begin
                $fatal(1, "%s failed: actual=%0d expected=%0d", name, actual, expected);
            end
        end
    endtask

    task automatic apply_reset;
        begin
            rstn_i   = 1'b0;
            enable_i = 1'b1;
            pd_i     = '0;
            ref_i    = '0;
            repeat (2) @(posedge clk_i);
            #1;
            check_equal("reset output", mix_o, '0);
            rstn_i = 1'b1;
            @(posedge clk_i);
        end
    endtask

    task automatic drive_and_check(
        input string name,
        input logic signed [IN_WIDTH-1:0] pd,
        input logic signed [IN_WIDTH-1:0] ref_sample
    );
        logic signed [OUT_WIDTH-1:0] expected;
        begin
            expected = expected_mix(pd, ref_sample);
            @(negedge clk_i);
            enable_i = 1'b1;
            pd_i     = pd;
            ref_i    = ref_sample;
            @(posedge clk_i);
            #1;
            check_equal(name, mix_o, expected);
        end
    endtask

    initial begin
        apply_reset();

        @(negedge clk_i);
        enable_i = 1'b0;
        pd_i     = 14'sd4096;
        ref_i    = 14'sd4096;
        @(posedge clk_i);
        #1;
        check_equal("enable low output", mix_o, '0);

        drive_and_check("positive times positive", 14'sd4096, 14'sd2048);
        drive_and_check("positive times negative", 14'sd4096, -14'sd4096);
        drive_and_check("negative times positive", -14'sd4096, 14'sd4096);
        drive_and_check("negative times negative", -14'sd4096, -14'sd4096);
        drive_and_check("zero times signal", 14'sd0, -14'sd4096);
        drive_and_check("max positive inputs", IN_MAX, IN_MAX);
        drive_and_check("negative saturation", IN_MIN, IN_MAX);
        drive_and_check("positive saturation", IN_MIN, IN_MIN);

        $display("PASS: tb_mixer_core");
        $finish;
    end

endmodule
