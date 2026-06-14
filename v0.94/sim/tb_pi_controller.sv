`timescale 1ns / 1ps

module tb_pi_controller;

    localparam int ERROR_WIDTH = 14;
    localparam int GAIN_WIDTH  = 16;
    localparam int OUT_WIDTH   = 14;
    localparam int ACC_WIDTH   = 48;
    localparam int KP_SHIFT    = 4;
    localparam int KI_SHIFT    = 4;

    logic clk_i = 1'b0;
    logic rstn_i;
    logic pid_ce_i;
    logic enable_i;
    logic hold_i;
    logic reset_integrator_i;
    logic polarity_i;

    logic signed [ERROR_WIDTH-1:0] error_i;
    logic signed [GAIN_WIDTH-1:0]  kp_i;
    logic signed [GAIN_WIDTH-1:0]  ki_i;
    logic signed [OUT_WIDTH-1:0]   offset_i;
    logic        [OUT_WIDTH-1:0]   output_limit_i;

    logic signed [OUT_WIDTH-1:0]   control_o;
    logic signed [31:0]            p_term_o;
    logic signed [31:0]            i_term_o;
    logic                          sat_o;

    int test_count = 0;
    int error_count = 0;

    always #5 clk_i = ~clk_i;

    pi_controller #(
        .ERROR_WIDTH (ERROR_WIDTH),
        .GAIN_WIDTH  (GAIN_WIDTH),
        .OUT_WIDTH   (OUT_WIDTH),
        .ACC_WIDTH   (ACC_WIDTH),
        .KP_SHIFT    (KP_SHIFT),
        .KI_SHIFT    (KI_SHIFT)
    ) dut (
        .clk_i              (clk_i),
        .rstn_i             (rstn_i),
        .pid_ce_i           (pid_ce_i),
        .enable_i           (enable_i),
        .hold_i             (hold_i),
        .reset_integrator_i (reset_integrator_i),
        .polarity_i         (polarity_i),
        .error_i            (error_i),
        .kp_i               (kp_i),
        .ki_i               (ki_i),
        .offset_i           (offset_i),
        .output_limit_i     (output_limit_i),
        .control_o          (control_o),
        .p_term_o           (p_term_o),
        .i_term_o           (i_term_o),
        .sat_o              (sat_o)
    );

    function automatic logic signed [OUT_WIDTH-1:0] expected_control(
        input logic signed [ERROR_WIDTH-1:0] err,
        input logic signed [GAIN_WIDTH-1:0] gain,
        input logic polarity,
        input logic signed [OUT_WIDTH-1:0] offset,
        input logic [OUT_WIDTH-1:0] limit
    );
        logic signed [ERROR_WIDTH:0] error_ext;
        logic signed [ERROR_WIDTH:0] error_pol;
        logic signed [ERROR_WIDTH+GAIN_WIDTH:0] product;
        logic signed [ACC_WIDTH-1:0] scaled;
        logic signed [ACC_WIDTH-1:0] pre_limit;
        logic signed [ACC_WIDTH-1:0] limit_pos;
        logic signed [ACC_WIDTH-1:0] limit_neg;
        begin
            error_ext = {err[ERROR_WIDTH-1], err};
            error_pol = polarity ? -error_ext : error_ext;
            product = $signed(error_pol) * $signed(gain);
            scaled = product >>> KP_SHIFT;
            pre_limit = scaled + {{(ACC_WIDTH-OUT_WIDTH){offset[OUT_WIDTH-1]}}, offset};
            limit_pos = (limit > 14'd8191) ? 48'sd8191 : {{(ACC_WIDTH-OUT_WIDTH){1'b0}}, limit};
            limit_neg = -limit_pos;

            if (pre_limit > limit_pos) begin
                expected_control = limit_pos[OUT_WIDTH-1:0];
            end else if (pre_limit < limit_neg) begin
                expected_control = limit_neg[OUT_WIDTH-1:0];
            end else begin
                expected_control = pre_limit[OUT_WIDTH-1:0];
            end
        end
    endfunction

    function automatic bit expected_sat(
        input logic signed [ERROR_WIDTH-1:0] err,
        input logic signed [GAIN_WIDTH-1:0] gain,
        input logic polarity,
        input logic signed [OUT_WIDTH-1:0] offset,
        input logic [OUT_WIDTH-1:0] limit
    );
        logic signed [ERROR_WIDTH:0] error_ext;
        logic signed [ERROR_WIDTH:0] error_pol;
        logic signed [ERROR_WIDTH+GAIN_WIDTH:0] product;
        logic signed [ACC_WIDTH-1:0] scaled;
        logic signed [ACC_WIDTH-1:0] pre_limit;
        logic signed [ACC_WIDTH-1:0] limit_pos;
        logic signed [ACC_WIDTH-1:0] limit_neg;
        begin
            error_ext = {err[ERROR_WIDTH-1], err};
            error_pol = polarity ? -error_ext : error_ext;
            product = $signed(error_pol) * $signed(gain);
            scaled = product >>> KP_SHIFT;
            pre_limit = scaled + {{(ACC_WIDTH-OUT_WIDTH){offset[OUT_WIDTH-1]}}, offset};
            limit_pos = (limit > 14'd8191) ? 48'sd8191 : {{(ACC_WIDTH-OUT_WIDTH){1'b0}}, limit};
            limit_neg = -limit_pos;
            expected_sat = (pre_limit > limit_pos) || (pre_limit < limit_neg);
        end
    endfunction

    task automatic pass(input string name);
        begin
            $display("[PASS] %s", name);
        end
    endtask

    task automatic fail_equal(
        input string name,
        input integer expected,
        input integer actual
    );
        begin
            $display("[FAIL] %s expected=%0d actual=%0d", name, expected, actual);
            error_count++;
        end
    endtask

    task automatic check_equal(
        input string name,
        input integer actual,
        input integer expected
    );
        begin
            test_count++;
            if (actual !== expected) begin
                fail_equal(name, expected, actual);
            end else begin
                pass(name);
            end
        end
    endtask

    task automatic check_true(input string name, input bit condition);
        begin
            test_count++;
            if (!condition) begin
                $display("[FAIL] %s expected=1 actual=0", name);
                error_count++;
            end else begin
                pass(name);
            end
        end
    endtask

    task automatic set_defaults;
        begin
            pid_ce_i           = 1'b0;
            enable_i           = 1'b1;
            hold_i             = 1'b0;
            reset_integrator_i = 1'b0;
            polarity_i         = 1'b0;
            error_i            = '0;
            kp_i               = 16'sd16;
            ki_i               = '0;
            offset_i           = '0;
            output_limit_i     = 14'd8191;
        end
    endtask

    task automatic apply_reset;
        begin
            rstn_i = 1'b0;
            set_defaults();
            repeat (2) @(posedge clk_i);
            #1;
            rstn_i = 1'b1;
            @(posedge clk_i);
        end
    endtask

    task automatic update_once;
        begin
            @(negedge clk_i);
            pid_ce_i = 1'b1;
            @(posedge clk_i);
            #1;
            @(negedge clk_i);
            pid_ce_i = 1'b0;
        end
    endtask

    task automatic drive_and_check(
        input string name,
        input logic signed [ERROR_WIDTH-1:0] err,
        input logic signed [GAIN_WIDTH-1:0] gain,
        input logic polarity,
        input logic signed [OUT_WIDTH-1:0] offset,
        input logic [OUT_WIDTH-1:0] limit
    );
        logic signed [OUT_WIDTH-1:0] expected;
        begin
            expected = expected_control(err, gain, polarity, offset, limit);
            @(negedge clk_i);
            enable_i       = 1'b1;
            reset_integrator_i = 1'b0;
            hold_i         = 1'b0;
            polarity_i     = polarity;
            error_i        = err;
            kp_i           = gain;
            ki_i           = '0;
            offset_i       = offset;
            output_limit_i = limit;
            update_once();
            check_equal(name, control_o, expected);
            check_equal({name, " i_term_zero"}, i_term_o, 0);
            check_equal({name, " sat"}, sat_o, expected_sat(err, gain, polarity, offset, limit));
        end
    endtask

    task automatic drive_raw(
        input logic signed [ERROR_WIDTH-1:0] err,
        input logic signed [GAIN_WIDTH-1:0] gain,
        input logic polarity,
        input logic signed [OUT_WIDTH-1:0] offset,
        input logic [OUT_WIDTH-1:0] limit
    );
        begin
            @(negedge clk_i);
            enable_i       = 1'b1;
            reset_integrator_i = 1'b0;
            hold_i         = 1'b0;
            polarity_i     = polarity;
            error_i        = err;
            kp_i           = gain;
            ki_i           = '0;
            offset_i       = offset;
            output_limit_i = limit;
            update_once();
        end
    endtask

    task automatic drive_pi_raw(
        input logic signed [ERROR_WIDTH-1:0] err,
        input logic signed [GAIN_WIDTH-1:0] gain_p,
        input logic signed [GAIN_WIDTH-1:0] gain_i,
        input logic polarity,
        input logic signed [OUT_WIDTH-1:0] offset,
        input logic [OUT_WIDTH-1:0] limit
    );
        begin
            @(negedge clk_i);
            enable_i           = 1'b1;
            reset_integrator_i = 1'b0;
            hold_i             = 1'b0;
            polarity_i         = polarity;
            error_i            = err;
            kp_i               = gain_p;
            ki_i               = gain_i;
            offset_i           = offset;
            output_limit_i     = limit;
            update_once();
        end
    endtask

    task automatic do_reset_integrator(
        input logic signed [ERROR_WIDTH-1:0] err,
        input logic signed [GAIN_WIDTH-1:0] gain_p,
        input logic polarity,
        input logic signed [OUT_WIDTH-1:0] offset,
        input logic [OUT_WIDTH-1:0] limit,
        input bit hold_value
    );
        begin
            @(negedge clk_i);
            enable_i           = 1'b1;
            reset_integrator_i = 1'b1;
            hold_i             = hold_value;
            polarity_i         = polarity;
            error_i            = err;
            kp_i               = gain_p;
            offset_i           = offset;
            output_limit_i     = limit;
            pid_ce_i           = 1'b1;
            @(posedge clk_i);
            #1;
            @(negedge clk_i);
            reset_integrator_i = 1'b0;
            hold_i             = 1'b0;
            pid_ce_i           = 1'b0;
        end
    endtask

    initial begin
        apply_reset();
        check_equal("low active reset clears control", control_o, 0);
        check_equal("low active reset clears p_term", p_term_o, 0);
        check_equal("low active reset clears i_term", i_term_o, 0);
        check_equal("low active reset clears sat", sat_o, 0);

        drive_and_check("positive error positive kp", 14'sd100, 16'sd16, 1'b0, 14'sd0, 14'd8191);

        @(negedge clk_i);
        enable_i = 1'b0;
        error_i  = 14'sd500;
        kp_i     = 16'sd16;
        pid_ce_i = 1'b1;
        @(posedge clk_i);
        #1;
        check_equal("enable low clears control", control_o, 0);
        check_equal("enable low clears i_term", i_term_o, 0);

        @(negedge clk_i);
        enable_i = 1'b1;
        pid_ce_i = 1'b0;
        error_i  = 14'sd1200;
        repeat (3) @(posedge clk_i);
        #1;
        check_equal("pid_ce low holds control", control_o, 0);

        drive_and_check("negative error positive kp", -14'sd100, 16'sd16, 1'b0, 14'sd0, 14'd8191);
        drive_and_check("polarity flips sign", -14'sd100, 16'sd16, 1'b1, 14'sd0, 14'd8191);
        drive_and_check("positive offset", 14'sd100, 16'sd16, 1'b0, 14'sd25, 14'd8191);
        drive_and_check("negative offset", 14'sd100, 16'sd16, 1'b0, -14'sd25, 14'd8191);
        drive_and_check("positive saturation", 14'sd8191, 16'sd128, 1'b0, 14'sd0, 14'd200);
        drive_and_check("negative saturation", -14'sd8192, 16'sd128, 1'b0, 14'sd0, 14'd200);
        drive_and_check("output limit zero", 14'sd100, 16'sd16, 1'b0, 14'sd0, 14'd0);

        drive_and_check("hold setup", 14'sd200, 16'sd16, 1'b0, 14'sd0, 14'd8191);
        @(negedge clk_i);
        hold_i   = 1'b1;
        error_i  = -14'sd700;
        kp_i     = 16'sd64;
        pid_ce_i = 1'b1;
        @(posedge clk_i);
        #1;
        check_equal("hold keeps control", control_o, 200);
        check_equal("hold keeps i_term", i_term_o, 0);
        @(negedge clk_i);
        hold_i = 1'b0;
        pid_ce_i = 1'b0;

        drive_and_check("maximum positive error", 14'sd8191, 16'sd16, 1'b0, 14'sd0, 14'd8191);
        drive_and_check("minimum negative error", -14'sd8192, 16'sd16, 1'b0, 14'sd0, 14'd8191);
        drive_and_check("minimum negative error polarity no overflow", -14'sd8192, 16'sd16, 1'b1, 14'sd0, 14'd8191);

        drive_and_check("enable priority setup", 14'sd300, 16'sd16, 1'b0, 14'sd0, 14'd8191);
        @(negedge clk_i);
        enable_i = 1'b0;
        hold_i   = 1'b1;
        error_i  = 14'sd700;
        pid_ce_i = 1'b1;
        @(posedge clk_i);
        #1;
        check_equal("enable priority over hold", control_o, 0);

        drive_and_check("reset priority setup", 14'sd300, 16'sd16, 1'b0, 14'sd0, 14'd8191);
        @(negedge clk_i);
        rstn_i   = 1'b0;
        enable_i = 1'b0;
        hold_i   = 1'b1;
        pid_ce_i = 1'b1;
        @(posedge clk_i);
        #1;
        check_equal("reset priority highest", control_o, 0);
        rstn_i = 1'b1;
        set_defaults();

        drive_and_check("consecutive pid_ce update 1", 14'sd100, 16'sd16, 1'b0, 14'sd0, 14'd8191);
        drive_and_check("consecutive pid_ce update 2", 14'sd200, 16'sd16, 1'b0, 14'sd0, 14'd8191);
        drive_and_check("consecutive pid_ce update 3", -14'sd300, 16'sd16, 1'b0, 14'sd0, 14'd8191);

        @(negedge clk_i);
        ki_i = 16'sd1234;
        error_i = 14'sd0;
        kp_i = 16'sd16;
        update_once();
        check_equal("ki change leaves i_term zero", i_term_o, 0);

        @(negedge clk_i);
        reset_integrator_i = 1'b1;
        error_i = -14'sd400;
        update_once();
        check_equal("reset_integrator placeholder leaves i_term zero", i_term_o, 0);
        check_equal("reset_integrator placeholder allows P behavior", control_o, -400);

        drive_raw(14'sd123, 16'sd0, 1'b0, 14'sd0, 14'd8191);
        check_equal("kp zero no offset control", control_o, 0);
        check_equal("kp zero no offset p_term", p_term_o, 0);
        check_equal("kp zero no offset sat", sat_o, 0);

        drive_raw(-14'sd321, 16'sd0, 1'b0, 14'sd55, 14'd100);
        check_equal("kp zero positive offset control", control_o, 55);
        check_equal("kp zero positive offset p_term", p_term_o, 0);
        check_equal("kp zero positive offset sat", sat_o, 0);

        drive_raw(14'sd321, 16'sd0, 1'b0, 14'sd150, 14'd100);
        check_equal("kp zero offset limited control", control_o, 100);
        check_equal("kp zero offset limited p_term", p_term_o, 0);
        check_equal("kp zero offset limited sat", sat_o, 1);

        drive_raw(14'sd16, -16'sd8, 1'b0, 14'sd0, 14'd8191);
        check_equal("positive error negative kp control", control_o, -8);
        check_equal("positive error negative kp p_term", p_term_o, -8);

        drive_raw(-14'sd16, -16'sd8, 1'b0, 14'sd0, 14'd8191);
        check_equal("negative error negative kp control", control_o, 8);
        check_equal("negative error negative kp p_term", p_term_o, 8);

        drive_raw(14'sd16, -16'sd8, 1'b1, 14'sd0, 14'd8191);
        check_equal("polarity with negative kp control", control_o, 8);
        check_equal("polarity with negative kp p_term", p_term_o, 8);

        drive_raw(14'sd16, 16'sd8, 1'b0, 14'sd0, 14'd8191);
        check_equal("manual p_term positive P", p_term_o, 8);

        drive_raw(-14'sd16, 16'sd8, 1'b0, 14'sd0, 14'd8191);
        check_equal("manual p_term negative P", p_term_o, -8);

        drive_raw(-14'sd16, 16'sd8, 1'b1, 14'sd0, 14'd8191);
        check_equal("manual p_term polarity flipped P", p_term_o, 8);

        drive_raw(14'sd8191, 16'sd128, 1'b0, 14'sd0, 14'd200);
        check_equal("hold complete setup control", control_o, 200);
        check_true("hold complete setup p_term nonzero", p_term_o != 0);
        check_equal("hold complete setup i_term", i_term_o, 0);
        check_equal("hold complete setup sat", sat_o, 1);
        @(negedge clk_i);
        hold_i         = 1'b1;
        error_i        = -14'sd16;
        kp_i           = -16'sd8;
        offset_i       = -14'sd99;
        polarity_i     = 1'b1;
        output_limit_i = 14'd8191;
        pid_ce_i       = 1'b1;
        @(posedge clk_i);
        #1;
        check_equal("hold complete keeps control", control_o, 200);
        check_equal("hold complete keeps p_term", p_term_o, 65528);
        check_equal("hold complete keeps i_term", i_term_o, 0);
        check_equal("hold complete keeps sat", sat_o, 1);
        @(negedge clk_i);
        hold_i   = 1'b0;
        pid_ce_i = 1'b0;

        drive_raw(14'sd64, 16'sd16, 1'b0, 14'sd0, 14'd8191);
        check_equal("disable re-enable setup control", control_o, 64);
        @(negedge clk_i);
        enable_i = 1'b0;
        error_i  = 14'sd4096;
        kp_i     = 16'sd64;
        pid_ce_i = 1'b0;
        @(posedge clk_i);
        #1;
        check_equal("disable clears control before re-enable", control_o, 0);
        check_equal("disable clears p_term before re-enable", p_term_o, 0);
        check_equal("disable clears i_term before re-enable", i_term_o, 0);
        check_equal("disable clears sat before re-enable", sat_o, 0);
        @(negedge clk_i);
        enable_i = 1'b1;
        error_i  = -14'sd32;
        kp_i     = 16'sd16;
        offset_i = 14'sd0;
        output_limit_i = 14'd8191;
        update_once();
        check_equal("re-enable computes new control", control_o, -32);
        check_equal("re-enable computes new p_term", p_term_o, -32);

        drive_raw(14'sd0, 16'sd0, 1'b0, 14'sd300, 14'd100);
        check_equal("positive offset alone saturates control", control_o, 100);
        check_equal("positive offset alone p_term", p_term_o, 0);
        check_equal("positive offset alone sat", sat_o, 1);

        drive_raw(14'sd0, 16'sd0, 1'b0, -14'sd300, 14'd100);
        check_equal("negative offset alone saturates control", control_o, -100);
        check_equal("negative offset alone p_term", p_term_o, 0);
        check_equal("negative offset alone sat", sat_o, 1);

        apply_reset();

        drive_pi_raw(14'sd16, 16'sd0, 16'sd8, 1'b0, 14'sd0, 14'd8191);
        check_equal("i-only positive accumulation 1", i_term_o, 8);
        check_equal("i-only positive control 1", control_o, 8);
        drive_pi_raw(14'sd16, 16'sd0, 16'sd8, 1'b0, 14'sd0, 14'd8191);
        check_equal("i-only positive accumulation 2", i_term_o, 16);
        drive_pi_raw(14'sd16, 16'sd0, 16'sd8, 1'b0, 14'sd0, 14'd8191);
        check_equal("i-only positive accumulation 3", i_term_o, 24);

        apply_reset();
        drive_pi_raw(-14'sd16, 16'sd0, 16'sd8, 1'b0, 14'sd0, 14'd8191);
        check_equal("i-only negative accumulation 1", i_term_o, -8);
        drive_pi_raw(-14'sd16, 16'sd0, 16'sd8, 1'b0, 14'sd0, 14'd8191);
        check_equal("i-only negative accumulation 2", i_term_o, -16);
        drive_pi_raw(-14'sd16, 16'sd0, 16'sd8, 1'b0, 14'sd0, 14'd8191);
        check_equal("i-only negative accumulation 3", i_term_o, -24);

        apply_reset();
        drive_pi_raw(14'sd16, 16'sd0, -16'sd8, 1'b0, 14'sd0, 14'd8191);
        check_equal("positive error negative ki", i_term_o, -8);
        apply_reset();
        drive_pi_raw(-14'sd16, 16'sd0, -16'sd8, 1'b0, 14'sd0, 14'd8191);
        check_equal("negative error negative ki", i_term_o, 8);

        apply_reset();
        drive_pi_raw(-14'sd16, 16'sd0, 16'sd8, 1'b1, 14'sd0, 14'd8191);
        check_equal("polarity flips i direction", i_term_o, 8);

        @(negedge clk_i);
        error_i = 14'sd64;
        ki_i    = 16'sd64;
        repeat (3) @(posedge clk_i);
        #1;
        check_equal("pid_ce low keeps integrator", i_term_o, 8);
        check_equal("pid_ce low keeps control", control_o, 8);

        drive_pi_raw(14'sd16, 16'sd0, 16'sd8, 1'b0, 14'sd0, 14'd8191);
        check_equal("hold freeze setup i", i_term_o, 16);
        @(negedge clk_i);
        hold_i   = 1'b1;
        error_i  = 14'sd64;
        ki_i     = 16'sd64;
        pid_ce_i = 1'b1;
        repeat (4) @(posedge clk_i);
        #1;
        check_equal("hold freezes integrator", i_term_o, 16);
        check_equal("hold freezes control", control_o, 16);
        @(negedge clk_i);
        hold_i   = 1'b0;
        pid_ce_i = 1'b0;

        do_reset_integrator(14'sd16, 16'sd8, 1'b0, 14'sd5, 14'd8191, 1'b0);
        check_equal("reset_integrator clears i", i_term_o, 0);
        check_equal("reset_integrator keeps P plus offset", control_o, 13);
        check_equal("reset_integrator updates p_term", p_term_o, 8);

        drive_pi_raw(14'sd16, 16'sd0, 16'sd8, 1'b0, 14'sd0, 14'd8191);
        check_equal("disable clear setup i", i_term_o, 8);
        @(negedge clk_i);
        enable_i = 1'b0;
        @(posedge clk_i);
        #1;
        check_equal("disable clears integrator", i_term_o, 0);
        check_equal("disable clears control after i", control_o, 0);
        @(negedge clk_i);
        enable_i = 1'b1;
        error_i  = 14'sd0;
        kp_i     = 16'sd0;
        ki_i     = 16'sd0;
        pid_ce_i = 1'b1;
        @(posedge clk_i);
        #1;
        check_equal("re-enable does not restore old i", i_term_o, 0);
        @(negedge clk_i);
        pid_ce_i = 1'b0;

        apply_reset();
        drive_pi_raw(14'sd16, 16'sd8, 16'sd8, 1'b0, 14'sd0, 14'd8191);
        check_equal("pi fixed point 1 p_term", p_term_o, 8);
        check_equal("pi fixed point 1 i_term", i_term_o, 8);
        check_equal("pi fixed point 1 control", control_o, 16);
        drive_pi_raw(14'sd16, 16'sd8, 16'sd8, 1'b0, 14'sd0, 14'd8191);
        check_equal("pi fixed point 2 i_term", i_term_o, 16);
        check_equal("pi fixed point 2 control", control_o, 24);
        drive_pi_raw(14'sd16, 16'sd8, 16'sd8, 1'b0, -14'sd4, 14'd8191);
        check_equal("pi fixed point 3 p_term", p_term_o, 8);
        check_equal("pi fixed point 3 i_term", i_term_o, 24);
        check_equal("pi fixed point 3 control", control_o, 28);

        apply_reset();
        drive_pi_raw(14'sd16, 16'sd0, 16'sd8, 1'b0, 14'sd0, 14'd20);
        drive_pi_raw(14'sd16, 16'sd0, 16'sd8, 1'b0, 14'sd0, 14'd20);
        drive_pi_raw(14'sd16, 16'sd0, 16'sd8, 1'b0, 14'sd0, 14'd20);
        check_equal("positive integrator clamp", i_term_o, 20);
        check_equal("positive integrator clamp control", control_o, 20);
        drive_pi_raw(14'sd16, 16'sd0, 16'sd8, 1'b0, 14'sd0, 14'd20);
        check_equal("positive integrator stays clamped", i_term_o, 20);

        apply_reset();
        drive_pi_raw(-14'sd16, 16'sd0, 16'sd8, 1'b0, 14'sd0, 14'd20);
        drive_pi_raw(-14'sd16, 16'sd0, 16'sd8, 1'b0, 14'sd0, 14'd20);
        drive_pi_raw(-14'sd16, 16'sd0, 16'sd8, 1'b0, 14'sd0, 14'd20);
        check_equal("negative integrator clamp", i_term_o, -20);
        check_equal("negative integrator clamp control", control_o, -20);
        drive_pi_raw(-14'sd16, 16'sd0, 16'sd8, 1'b0, 14'sd0, 14'd20);
        check_equal("negative integrator stays clamped", i_term_o, -20);

        apply_reset();
        drive_pi_raw(14'sd16, 16'sd64, 16'sd8, 1'b0, 14'sd0, 14'd20);
        check_equal("positive saturation freezes i", i_term_o, 0);
        check_equal("positive saturation freezes control", control_o, 20);
        drive_pi_raw(14'sd16, 16'sd64, 16'sd8, 1'b0, 14'sd0, 14'd20);
        check_equal("positive saturation keeps i frozen", i_term_o, 0);

        apply_reset();
        drive_pi_raw(-14'sd16, 16'sd64, 16'sd8, 1'b0, 14'sd0, 14'd20);
        check_equal("negative saturation freezes i", i_term_o, 0);
        check_equal("negative saturation freezes control", control_o, -20);
        drive_pi_raw(-14'sd16, 16'sd64, 16'sd8, 1'b0, 14'sd0, 14'd20);
        check_equal("negative saturation keeps i frozen", i_term_o, 0);

        apply_reset();
        drive_pi_raw(14'sd16, 16'sd24, 16'sd8, 1'b0, 14'sd0, 14'd20);
        check_equal("positive saturation recovery starts frozen", i_term_o, 0);
        drive_pi_raw(14'sd16, 16'sd24, -16'sd8, 1'b0, 14'sd0, 14'd20);
        check_equal("positive saturation recovery allows i down", i_term_o, -8);
        check_equal("positive saturation recovery exits limit", control_o, 16);
        check_equal("positive saturation recovery clears sat", sat_o, 0);

        apply_reset();
        drive_pi_raw(-14'sd16, 16'sd24, 16'sd8, 1'b0, 14'sd0, 14'd20);
        check_equal("negative saturation recovery starts frozen", i_term_o, 0);
        drive_pi_raw(-14'sd16, 16'sd24, -16'sd8, 1'b0, 14'sd0, 14'd20);
        check_equal("negative saturation recovery allows i up", i_term_o, 8);
        check_equal("negative saturation recovery exits limit", control_o, -16);
        check_equal("negative saturation recovery clears sat", sat_o, 0);

        apply_reset();
        repeat (5) begin
            drive_pi_raw(14'sd16, 16'sd0, 16'sd8, 1'b0, 14'sd0, 14'd100);
        end
        check_equal("dynamic limit setup i", i_term_o, 40);
        drive_pi_raw(14'sd16, 16'sd0, 16'sd8, 1'b0, 14'sd0, 14'd15);
        check_equal("dynamic limit decrease clamps i", i_term_o, 15);
        check_equal("dynamic limit decrease clamps control", control_o, 15);

        drive_pi_raw(14'sd16, 16'sd0, 16'sd8, 1'b0, 14'sd0, 14'd0);
        check_equal("output limit zero clamps i", i_term_o, 0);
        check_equal("output limit zero clamps control after i", control_o, 0);

        apply_reset();
        repeat (1000) begin
            drive_pi_raw(14'sd16, 16'sd0, 16'sd8, 1'b0, 14'sd0, 14'd20);
        end
        check_true("long positive integration no unknown", !$isunknown(i_term_o) && !$isunknown(control_o));
        check_true("long positive integration within limit", (i_term_o <= 20) && (i_term_o >= -20) && (control_o <= 20));

        apply_reset();
        repeat (1000) begin
            drive_pi_raw(-14'sd16, 16'sd0, 16'sd8, 1'b0, 14'sd0, 14'd20);
        end
        check_true("long negative integration no unknown", !$isunknown(i_term_o) && !$isunknown(control_o));
        check_true("long negative integration within limit", (i_term_o >= -20) && (i_term_o <= 20) && (control_o >= -20));

        do_reset_integrator(14'sd16, 16'sd8, 1'b0, 14'sd1, 14'd8191, 1'b1);
        check_equal("reset_integrator priority over hold i", i_term_o, 0);
        check_equal("reset_integrator priority over hold control", control_o, 9);

        $display("tb_pi_controller summary: tests=%0d pass=%0d fail=%0d",
                 test_count, test_count - error_count, error_count);
        if (error_count != 0) begin
            $fatal(1, "tb_pi_controller failed: error_count=%0d", error_count);
        end
        $finish;
    end

endmodule
