`timescale 1ns/1ps

// v2B1 FPGA MTS Error timing-safe Shadow Control behavior test.
//
// Historical naming note:
// The "dc_error" suffix in this filename is a historical name. The current
// valid test is NOT "D2-125 DC Error enters Red Pitaya IN1".
//
// Current valid chain under test:
// IN1 + IN2 -> mixer_core -> lpf_core -> error_o -> OUT1
// and the same error_o/protected_error -> timing-safe P-only control_o -> OUT2.
//
// The testbench verifies board-observable behavior through laser_lock_core's
// public ports: reset safety, OUT1 error visibility, OUT2 P-only scaling,
// output_limit, polarity, no-integrator default behavior, and pid_ce hold
// behavior.
//
// Board interpretation:
// - PASS here means the integrated RTL has the expected Shadow PI behavior in
//   simulation.
// - It does not mean Vivado synthesis/implementation/bitstream has been run.
// - It does not mean OUT2 may be connected to a laser. OUT2 remains
//   oscilloscope-only until later physical interface checks are complete.

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

    logic signed [13:0] error_seq;
    logic signed [13:0] control_seq;
    logic signed [13:0] pd_seq_i;
    logic signed [13:0] control_seq_i;
    logic signed [13:0] control_seq_limit;
    logic signed [13:0] control_seq_reverse;
    logic signed [13:0] error_seq_mode3;
    logic signed [13:0] control_seq_mode3;
    logic signed [13:0] pd_seq_mode3;
    logic signed [13:0] ref_seq_mode3;

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

    // dut_direct uses OUTPUT_MODE=0 as a simple passthrough source. It makes
    // the OUT1 error value exact, so the test can check default timing-safe
    // half-scale control and pid_ce hold behavior without depending on LPF
    // settling.
    laser_lock_core #(
        .OUTPUT_MODE(0),
        .CONTROL_PATH_MODE(0),
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

    // dut_limit checks that the Shadow Control output_limit protects OUT2 and
    // keeps the control signal small before any board experiment.
    laser_lock_core #(
        .OUTPUT_MODE(0),
        .CONTROL_PATH_MODE(0),
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

    // dut_reverse checks polarity reversal. This is the knob used if OUT2 is
    // observed to move opposite to the intended control direction.
    laser_lock_core #(
        .OUTPUT_MODE(0),
        .CONTROL_PATH_MODE(0),
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

    // dut_mode3 checks the real v2B1 mode: IN1/IN2 are mixed, post-mixer LPF
    // creates the error, OUT1 observes that error, and the same error feeds
    // the timing-safe P-only Shadow Control path.
    laser_lock_core #(
        .OUTPUT_MODE(3),
        .CONTROL_PATH_MODE(0),
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

    // v2B3 sequential PI path. This is an integration test only; mode 0
    // above remains the v2B1 timing-safe fallback path.
    laser_lock_core #(
        .OUTPUT_MODE(0),
        .CONTROL_PATH_MODE(1),
        .CLK_HZ(1),
        .PID_UPDATE_HZ(1),
        .PID_KP_DEFAULT(16'sd2048),
        .PID_KI_DEFAULT(16'sd0),
        .PID_OUTPUT_LIMIT_DEFAULT(14'd1500)
    ) dut_seq (
        .clk_i(clk),
        .rstn_i(rstn),
        .pd_i(pd_direct),
        .ref_i(ref_direct),
        .error_o(error_seq),
        .control_o(control_seq)
    );

    laser_lock_core #(
        .OUTPUT_MODE(0),
        .CONTROL_PATH_MODE(1),
        .CLK_HZ(1),
        .PID_UPDATE_HZ(1),
        .PID_KP_DEFAULT(16'sd0),
        .PID_KI_DEFAULT(16'sd16),
        .PID_OUTPUT_LIMIT_DEFAULT(14'd100)
    ) dut_seq_i (
        .clk_i(clk),
        .rstn_i(rstn),
        .pd_i(pd_seq_i),
        .ref_i(14'sd0),
        .error_o(),
        .control_o(control_seq_i)
    );

    laser_lock_core #(
        .OUTPUT_MODE(0),
        .CONTROL_PATH_MODE(1),
        .CLK_HZ(1),
        .PID_UPDATE_HZ(1),
        .PID_KP_DEFAULT(16'sd2048),
        .PID_KI_DEFAULT(16'sd0),
        .PID_OUTPUT_LIMIT_DEFAULT(14'd100)
    ) dut_seq_limit (
        .clk_i(clk),
        .rstn_i(rstn),
        .pd_i(14'sd4000),
        .ref_i(14'sd0),
        .error_o(),
        .control_o(control_seq_limit)
    );

    laser_lock_core #(
        .OUTPUT_MODE(0),
        .CONTROL_PATH_MODE(1),
        .CLK_HZ(1),
        .PID_UPDATE_HZ(1),
        .PID_POLARITY_DEFAULT(1'b1),
        .PID_KP_DEFAULT(16'sd2048),
        .PID_KI_DEFAULT(16'sd0),
        .PID_OUTPUT_LIMIT_DEFAULT(14'd1500)
    ) dut_seq_reverse (
        .clk_i(clk),
        .rstn_i(rstn),
        .pd_i(14'sd400),
        .ref_i(14'sd0),
        .error_o(),
        .control_o(control_seq_reverse)
    );

    laser_lock_core #(
        .OUTPUT_MODE(3),
        .CONTROL_PATH_MODE(1),
        .CLK_HZ(1),
        .PID_UPDATE_HZ(1),
        .PID_KP_DEFAULT(16'sd2048),
        .PID_KI_DEFAULT(16'sd0),
        .PID_OUTPUT_LIMIT_DEFAULT(14'd1500)
    ) dut_seq_mode3 (
        .clk_i(clk),
        .rstn_i(rstn),
        .pd_i(pd_seq_mode3),
        .ref_i(ref_seq_mode3),
        .error_o(error_seq_mode3),
        .control_o(control_seq_mode3)
    );

    initial begin
        rstn = 1'b0;
        pd_direct = 14'sd0;
        ref_direct = 14'sd0;
        pd_mode3 = 14'sd0;
        ref_mode3 = 14'sd0;
        pd_seq_i = 14'sd0;
        pd_seq_mode3 = 14'sd0;
        ref_seq_mode3 = 14'sd0;

        wait_cycles(4);
        // Reset safety corresponds to the first board check after programming:
        // both OUT1 error and OUT2 control must start from a known safe zero.
        check("reset clears direct control_o", control_direct == 14'sd0);
        check("reset clears mode3 error_o", error_mode3 == 14'sd0);

        rstn = 1'b1;
        pd_direct = 14'sd400;
        ref_direct = 14'sd0;
        wait_cycles(20);

        // OUTPUT_MODE=0 is a controlled input-to-OUT1 check. It proves that the
        // later OUT2 calculation uses the same visible error source.
        check("OUTPUT_MODE=0 exposes protected error source", error_direct == 14'sd400);
        // With Kp=2048 and KP_SHIFT=12, the board expectation is OUT2/CH4 at
        // about one half of OUT1/CH2, before any real actuator is connected.
        // In the default v2B1 timing-safe branch this is implemented as >>> 1,
        // not by instantiating the complete PI multiplier/integrator path.
        check("default timing-safe path is selected", dut_direct.CONTROL_PATH_MODE == 0);
        check("timing-safe P-only makes control_o half of positive error_o", control_direct == 14'sd200);
        check("sequential PI path is selected", dut_seq.CONTROL_PATH_MODE == 1);
        check("sequential PI keeps OUT1 error observation", error_seq == 14'sd400);
        check("sequential PI Ki=0 matches P-only half scale", control_seq == 14'sd200);
        check("sequential PI output_limit protects OUT2", control_seq_limit == 14'sd100);
        check("sequential PI polarity reverses OUT2", control_seq_reverse == -14'sd200);

        pd_direct = 14'sd600;
        wait_cycles(1);
        // Between pid_ce pulses, OUT2 should hold its previous value. This is
        // how the PI update-rate divider avoids a 125 MHz control update.
        check("control_o holds between pid_ce pulses", control_direct == 14'sd200);
        wait_cycles(4);
        check("control_o updates on next pid_ce pulse", control_direct == 14'sd300);

        pd_direct = -14'sd400;
        wait_cycles(8);
        check("OUTPUT_MODE=0 exposes negative protected error source", error_direct == -14'sd400);
        check("timing-safe P-only makes control_o half of negative error_o", control_direct == -14'sd200);

        pd_direct = 14'sd600;
        wait_cycles(8);
        check("timing-safe P-only recovers from negative to positive error", control_direct == 14'sd300);

        wait_cycles(16);
        // The default v2B1 branch does not instantiate the complete PI
        // integrator at all. This prevents a slow OUT2 climb while the signal
        // is only being observed on an oscilloscope.
        check("timing-safe P-only default has no integral climb at fixed error", control_direct == 14'sd300);

        // output_limit is the last simulation guard before board observation:
        // a large error must not make OUT2 approach full-scale.
        check("output_limit clamps positive OUT2 control", control_limit == 14'sd100);
        // polarity is the future safe direction switch. If a board test shows
        // the response is inverted, this parameter flips OUT2 without rewiring.
        check("polarity=1 reverses OUT2 control direction", control_reverse == -14'sd200);

        pd_mode3 = 14'sd4096;
        ref_mode3 = 14'sd4096;
        wait_cycles(128);
        // OUTPUT_MODE=3 is the current real v2B1 route: IN1/IN2 create an FPGA
        // error, OUT1 observes it, and OUT2 follows it through P-only control.
        check("OUTPUT_MODE=3 still produces mixer plus LPF error", error_mode3 > 14'sd0);
        check("OUTPUT_MODE=3 drives Shadow Control from error source", control_mode3 > 14'sd0);
        check("mode3 P-only control is approximately half the visible error", abs_int(control_mode3 - (error_mode3 >>> 1)) <= 2);
        check("default v2B1 limit keeps OUT2 below 1500 counts", abs_int(control_mode3) <= 1500);
        check("mode3 also uses timing-safe default path", dut_mode3.CONTROL_PATH_MODE == 0);

        pd_seq_i = 14'sd256;
        wait_cycles(128);
        check("sequential PI Ki positive accumulates control", control_seq_i > 14'sd0);
        check("sequential PI Ki positive remains limited", control_seq_i <= 14'sd100);

        pd_seq_mode3 = 14'sd4096;
        ref_seq_mode3 = 14'sd4096;
        wait_cycles(128);
        check("sequential PI mode3 keeps OUT1 error", error_seq_mode3 > 14'sd0);
        check("sequential PI mode3 drives OUT2", control_seq_mode3 > 14'sd0);

        $display("SUMMARY tests=%0d pass=%0d fail=%0d", tests, pass_count, fail_count);
        if (fail_count == 0) begin
            $display("V2B1_V2B3_CONTROL_PATH_SIM PASS");
            $finish;
        end else begin
            $display("V2B1_V2B3_CONTROL_PATH_SIM FAIL");
            $fatal(1);
        end
    end

endmodule
