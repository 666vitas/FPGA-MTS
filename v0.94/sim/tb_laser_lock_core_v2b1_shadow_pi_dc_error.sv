`timescale 1ns/1ps

module tb_laser_lock_core_v2b1_shadow_pi_dc_error;

    logic clk = 1'b0;
    always #5 clk = ~clk;

    logic rstn;
    logic signed [13:0] pd_direct;
    logic signed [13:0] ref_direct;
    logic signed [13:0] error_direct;
    logic signed [13:0] control_direct;

    logic signed [13:0] error_limit;
    logic signed [13:0] control_limit;

    logic signed [13:0] error_reverse;
    logic signed [13:0] control_reverse;

    logic signed [13:0] pd_mode3;
    logic signed [13:0] ref_mode3;
    logic signed [13:0] error_mode3;
    logic signed [13:0] control_mode3;

    int tests;
    int pass_count;
    int fail_count;

    task automatic check(input string name, input bit condition);
        tests++;
        if (condition) begin
            pass_count++;
            $display("PASS: %s", name);
        end else begin
            fail_count++;
            $display("FAIL: %s", name);
        end
    endtask

    task automatic wait_cycles(input int n);
        repeat (n) @(posedge clk);
        #1;
    endtask

    function automatic int abs_int(input int value);
        abs_int = (value < 0) ? -value : value;
    endfunction

    laser_lock_core #(
        .OUTPUT_MODE(0),
        .CLK_HZ(8),
        .PID_UPDATE_HZ(2),
        .PID_KP_DEFAULT(16'sd2048),
        .PID_KI_DEFAULT(16'sd0),
        .PID_OUTPUT_LIMIT_DEFAULT(14'd1500)
    ) dut_direct (
        .clk_i(clk),
        .rstn_i(rstn),
        .pd_i(pd_direct),
        .ref_i(ref_direct),
        .error_o(error_direct),
        .control_o(control_direct)
    );

    laser_lock_core #(
        .OUTPUT_MODE(0),
        .CLK_HZ(1),
        .PID_UPDATE_HZ(1),
        .PID_KP_DEFAULT(16'sd2048),
        .PID_KI_DEFAULT(16'sd0),
        .PID_OUTPUT_LIMIT_DEFAULT(14'd100)
    ) dut_limit (
        .clk_i(clk),
        .rstn_i(rstn),
        .pd_i(14'sd4000),
        .ref_i(14'sd0),
        .error_o(error_limit),
        .control_o(control_limit)
    );

    laser_lock_core #(
        .OUTPUT_MODE(0),
        .CLK_HZ(1),
        .PID_UPDATE_HZ(1),
        .PID_POLARITY_DEFAULT(1'b1),
        .PID_KP_DEFAULT(16'sd2048),
        .PID_KI_DEFAULT(16'sd0),
        .PID_OUTPUT_LIMIT_DEFAULT(14'd1500)
    ) dut_reverse (
        .clk_i(clk),
        .rstn_i(rstn),
        .pd_i(14'sd400),
        .ref_i(14'sd0),
        .error_o(error_reverse),
        .control_o(control_reverse)
    );

    laser_lock_core #(
        .OUTPUT_MODE(3),
        .CLK_HZ(1),
        .PID_UPDATE_HZ(1),
        .PID_KP_DEFAULT(16'sd2048),
        .PID_KI_DEFAULT(16'sd0),
        .PID_OUTPUT_LIMIT_DEFAULT(14'd1500)
    ) dut_mode3 (
        .clk_i(clk),
        .rstn_i(rstn),
        .pd_i(pd_mode3),
        .ref_i(ref_mode3),
        .error_o(error_mode3),
        .control_o(control_mode3)
    );

    initial begin
        rstn = 1'b0;
        pd_direct = 14'sd0;
        ref_direct = 14'sd0;
        pd_mode3 = 14'sd0;
        ref_mode3 = 14'sd0;

        wait_cycles(4);
        check("reset clears direct control_o", control_direct == 14'sd0);
        check("reset clears mode3 error_o", error_mode3 == 14'sd0);

        rstn = 1'b1;
        pd_direct = 14'sd400;
        ref_direct = 14'sd0;
        wait_cycles(12);

        check("OUTPUT_MODE=0 exposes protected error source", error_direct == 14'sd400);
        check("Kp=2048 makes control_o half of error_o", control_direct == 14'sd200);

        pd_direct = 14'sd600;
        wait_cycles(1);
        check("control_o holds between pid_ce pulses", control_direct == 14'sd200);
        wait_cycles(4);
        check("control_o updates on next pid_ce pulse", control_direct == 14'sd300);

        wait_cycles(16);
        check("Ki=0 prevents integral climb at fixed error", control_direct == 14'sd300);

        check("output_limit clamps positive OUT2 control", control_limit == 14'sd100);
        check("polarity=1 reverses OUT2 control direction", control_reverse == -14'sd200);

        pd_mode3 = 14'sd4096;
        ref_mode3 = 14'sd4096;
        wait_cycles(128);
        check("OUTPUT_MODE=3 still produces mixer plus LPF error", error_mode3 > 14'sd0);
        check("OUTPUT_MODE=3 drives Shadow PI control from error source", control_mode3 > 14'sd0);
        check("mode3 P-only control is approximately half the visible error", abs_int(control_mode3 - (error_mode3 >>> 1)) <= 2);
        check("default v2B1 limit keeps OUT2 below 1500 counts", abs_int(control_mode3) <= 1500);

        $display("SUMMARY tests=%0d pass=%0d fail=%0d", tests, pass_count, fail_count);
        if (fail_count == 0) begin
            $display("V2B1_SHADOW_PI_SIM PASS");
            $finish;
        end else begin
            $display("V2B1_SHADOW_PI_SIM FAIL");
            $fatal(1);
        end
    end

endmodule
