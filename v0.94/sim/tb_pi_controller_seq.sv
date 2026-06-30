`timescale 1ns/1ps

// v2B3 tracer test: sequential PI must accept a pid_ce pulse and publish a
// registered PI result after a fixed number of clk_i cycles.
module tb_pi_controller_seq;

    localparam int UPDATE_LATENCY_CYCLES = 15;

    logic clk = 1'b0;
    always #5 clk = ~clk;

    logic rstn;
    logic pid_ce;
    logic enable;
    logic hold;
    logic reset_integrator;
    logic polarity;
    logic signed [13:0] error;
    logic signed [15:0] kp;
    logic signed [15:0] ki;
    logic signed [13:0] offset;
    logic        [13:0] output_limit;
    logic signed [13:0] control;
    logic signed [31:0] p_term;
    logic signed [31:0] i_term;
    logic sat;

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

    task automatic wait_cycles(input int count);
        repeat (count) @(posedge clk);
        #1;
    endtask

    task automatic start_update;
        @(negedge clk);
        pid_ce = 1'b1;
        @(posedge clk);
        @(negedge clk);
        pid_ce = 1'b0;
    endtask

    task automatic run_update;
        start_update();
        wait_cycles(UPDATE_LATENCY_CYCLES - 1);
    endtask

    task automatic apply_reset;
        @(negedge clk);
        rstn = 1'b0;
        pid_ce = 1'b0;
        wait_cycles(2);
        @(negedge clk);
        rstn = 1'b1;
    endtask

    pi_controller_seq #(
        .ERROR_WIDTH(14),
        .GAIN_WIDTH (16),
        .OUT_WIDTH  (14),
        .ACC_WIDTH  (48),
        .KP_SHIFT   (12),
        .KI_SHIFT   (12)
    ) dut (
        .clk_i             (clk),
        .rstn_i            (rstn),
        .pid_ce_i          (pid_ce),
        .enable_i          (enable),
        .hold_i            (hold),
        .reset_integrator_i(reset_integrator),
        .polarity_i        (polarity),
        .error_i           (error),
        .kp_i              (kp),
        .ki_i              (ki),
        .offset_i          (offset),
        .output_limit_i    (output_limit),
        .control_o         (control),
        .p_term_o          (p_term),
        .i_term_o          (i_term),
        .sat_o             (sat)
    );

    initial begin
        rstn = 1'b0;
        pid_ce = 1'b0;
        enable = 1'b1;
        hold = 1'b0;
        reset_integrator = 1'b0;
        polarity = 1'b0;
        error = 14'sd0;
        kp = 16'sd0;
        ki = 16'sd0;
        offset = 14'sd0;
        output_limit = 14'd8191;

        wait_cycles(2);
        check("reset clears registered control", control == 14'sd0);

        rstn = 1'b1;
        error = 14'sd16;
        kp = 16'sd2048;
        start_update();
        wait_cycles(UPDATE_LATENCY_CYCLES - 1);
        check("positive P-only update has fixed latency", control == 14'sd8);
        check("positive P-only update publishes p term", p_term == 32'sd8);
        check("positive P-only update has zero i term", i_term == 32'sd0);

        // enable=0 is an immediate safety action, independent of pid_ce.
        @(negedge clk);
        enable = 1'b0;
        wait_cycles(1);
        check("enable low clears control", control == 14'sd0);
        check("enable low clears P term", p_term == 32'sd0);
        check("enable low clears I term", i_term == 32'sd0);
        @(negedge clk);
        enable = 1'b1;

        // Hold discards an in-flight update and keeps the public outputs.
        error = 14'sd16;
        kp = 16'sd2048;
        ki = 16'sd0;
        run_update();
        @(negedge clk);
        hold = 1'b1;
        error = 14'sd64;
        start_update();
        wait_cycles(UPDATE_LATENCY_CYCLES);
        check("hold keeps control unchanged", control == 14'sd8);
        check("hold keeps P term unchanged", p_term == 32'sd8);
        @(negedge clk);
        hold = 1'b0;

        apply_reset();
        error = -14'sd16;
        kp = 16'sd2048;
        ki = 16'sd0;
        polarity = 1'b0;
        offset = 14'sd0;
        output_limit = 14'd8191;
        run_update();
        check("negative P-only error produces negative control", control == -14'sd8);
        check("negative P-only error produces negative P term", p_term == -32'sd8);

        apply_reset();
        error = -14'sd16;
        kp = 16'sd2048;
        polarity = 1'b1;
        run_update();
        check("polarity reverses control direction", control == 14'sd8);
        check("polarity reverses P term direction", p_term == 32'sd8);
        polarity = 1'b0;

        // error=256 and Ki=16 make one integer I count per update:
        // (256 * 16) >>> 12 = 1.
        apply_reset();
        error = 14'sd256;
        kp = 16'sd0;
        ki = 16'sd16;
        run_update();
        check("small Ki accumulates one count", i_term == 32'sd1);
        check("small Ki control follows integrator", control == 14'sd1);
        run_update();
        check("constant error accumulates slowly", i_term == 32'sd2);

        // reset_integrator is sampled with the transaction. Its output is P
        // plus offset, rather than a forced zero control output.
        error = 14'sd16;
        kp = 16'sd2048;
        ki = 16'sd2048;
        offset = 14'sd5;
        run_update();
        run_update();
        check("integration setup reaches nonzero I", i_term == 32'sd18);
        @(negedge clk);
        reset_integrator = 1'b1;
        run_update();
        check("reset_integrator clears I term", i_term == 32'sd0);
        check("reset_integrator keeps P plus offset", control == 14'sd13);
        @(negedge clk);
        reset_integrator = 1'b0;

        apply_reset();
        error = 14'sd0;
        kp = 16'sd0;
        ki = 16'sd0;
        offset = 14'sd7;
        output_limit = 14'd8191;
        run_update();
        check("offset is added to control", control == 14'sd7);
        check("offset without limit leaves sat low", sat == 1'b0);

        apply_reset();
        error = 14'sd16;
        kp = 16'sd8192;
        ki = 16'sd0;
        offset = 14'sd0;
        output_limit = 14'd20;
        run_update();
        check("positive output limit clamps control", control == 14'sd20);
        check("positive output limit asserts saturation", sat == 1'b1);

        apply_reset();
        error = -14'sd16;
        kp = 16'sd8192;
        ki = 16'sd0;
        output_limit = 14'd20;
        run_update();
        check("negative output limit clamps control", control == -14'sd20);
        check("negative output limit asserts saturation", sat == 1'b1);

        // A saturated P term must not keep integrating in the saturating
        // direction. Reverse Ki is allowed to unwind and recover the output.
        apply_reset();
        error = 14'sd16;
        kp = 16'sd8192;
        ki = 16'sd2048;
        output_limit = 14'd20;
        run_update();
        run_update();
        check("anti-windup freezes positive integrator", i_term == 32'sd0);
        @(negedge clk);
        kp = 16'sd6144;
        ki = -16'sd2048;
        run_update();
        check("anti-windup permits reverse integration", i_term == -32'sd8);
        check("anti-windup recovery clears saturation", sat == 1'b0);
        check("anti-windup recovery leaves limit", control == 14'sd16);

        apply_reset();
        error = 14'sd16;
        kp = 16'sd2048;
        ki = 16'sd0;
        output_limit = 14'd8191;
        run_update();
        @(negedge clk);
        error = 14'sd32;
        wait_cycles(3);
        check("pid_ce low keeps registered output", control == 14'sd8);
        run_update();
        check("separated pid_ce updates with new sample", control == 14'sd16);

        // A start pulse while the FSM is busy is intentionally ignored.
        apply_reset();
        error = 14'sd16;
        kp = 16'sd2048;
        ki = 16'sd0;
        start_update();
        @(negedge clk);
        pid_ce = 1'b1;
        @(posedge clk);
        @(negedge clk);
        pid_ce = 1'b0;
        wait_cycles(UPDATE_LATENCY_CYCLES - 2);
        check("busy pid_ce does not create a second update", control == 14'sd8);
        wait_cycles(UPDATE_LATENCY_CYCLES);
        check("busy pid_ce leaves controller idle after one update", control == 14'sd8);

        // Long repeated updates remain bounded and deterministic.
        apply_reset();
        error = 14'sd16;
        kp = 16'sd0;
        ki = 16'sd2048;
        output_limit = 14'd20;
        repeat (100) begin
            run_update();
        end
        check("long integration has no unknown outputs", !$isunknown(control) && !$isunknown(i_term));
        check("long integration remains within limit", control == 14'sd20 && i_term == 32'sd20);

        $display("SUMMARY tests=%0d pass=%0d fail=%0d", tests, pass_count, fail_count);
        if (fail_count == 0) begin
            $display("V2B3_PI_CONTROLLER_SEQ_SIM PASS");
            $finish;
        end else begin
            $display("V2B3_PI_CONTROLLER_SEQ_SIM FAIL");
            $fatal(1);
        end
    end

endmodule
