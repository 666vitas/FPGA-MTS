`timescale 1ns/1ps

module tb_out2_lock_controller;

    localparam logic [31:0] MODE_SAFE   = 32'd0;
    localparam logic [31:0] MODE_SCAN   = 32'd1;
    localparam logic [31:0] MODE_HOLD   = 32'd2;
    localparam logic [31:0] MODE_P_LOCK = 32'd3;
    localparam logic [31:0] MODE_PI_LOCK = 32'd4;
    localparam int P_LOCK_LATENCY = 8;

    logic clk = 1'b0;
    always #5 clk = ~clk;

    logic rstn;
    logic enable;
    logic [31:0] mode;
    logic signed [13:0] scan_i;
    logic scan_saturated_i;
    logic signed [13:0] hold_value;
    logic signed [13:0] error_i;
    logic signed [13:0] kp;
    logic signed [13:0] ki;
    logic polarity;
    logic signed [13:0] lock_bias;
    logic signed [13:0] lock_limit;
    logic signed [13:0] lock_correction_limit;
    logic [15:0] servo_update_div;
    logic [13:0] out2_slew_limit;
    logic integral_reset;
    logic acq_hold_i;
    logic acq_abort_i;
    logic acq_fault_i;
    logic signed [13:0] control_o;
    logic saturated_o;

    int tests;
    int pass_count;
    int fail_count;
    int previous_control;
    int delta;
    int changed_cycles;
    bit slew_ok;
    bit divider_observed;
    bit pipeline_fill_ok;
    bit target_alignment_ok;

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

    out2_lock_controller dut (
        .clk_i(clk),
        .rstn_i(rstn),
        .enable_i(enable),
        .mode_i(mode),
        .scan_i(scan_i),
        .scan_saturated_i(scan_saturated_i),
        .hold_value_i(hold_value),
        .error_i(error_i),
        .kp_i(kp),
        .ki_i(ki),
        .polarity_i(polarity),
        .lock_bias_i(lock_bias),
        .lock_limit_i(lock_limit),
        .lock_correction_limit_i(lock_correction_limit),
        .servo_update_div_i(servo_update_div),
        .out2_slew_limit_i(out2_slew_limit),
        .integral_reset_i(integral_reset),
        .acq_hold_i(acq_hold_i),
        .acq_abort_i(acq_abort_i),
        .acq_fault_i(acq_fault_i),
        .control_o(control_o),
        .saturated_o(saturated_o)
    );

    initial begin
        rstn = 1'b0;
        enable = 1'b0;
        mode = MODE_SAFE;
        scan_i = 14'sd321;
        scan_saturated_i = 1'b0;
        hold_value = 14'sd1000;
        error_i = 14'sd0;
        kp = 14'sd0;
        ki = 14'sd0;
        polarity = 1'b0;
        lock_bias = 14'sd100;
        lock_limit = 14'sd8191;
        lock_correction_limit = 14'sd128;
        servo_update_div = 16'd1;
        out2_slew_limit = 14'd8191;
        integral_reset = 1'b0;
        acq_hold_i = 1'b0;
        acq_abort_i = 1'b0;
        acq_fault_i = 1'b0;

        wait_cycles(4);
        check("reset drives SAFE zero", control_o == 14'sd0);
        rstn = 1'b1;
        wait_cycles(2);
        check("disabled drives SAFE zero", control_o == 14'sd0);

        enable = 1'b1;
        mode = MODE_SCAN;
        scan_i = 14'sd321;
        wait_cycles(2);
        check("SCAN passes ramp output", control_o == 14'sd321);

        scan_i = 14'sd400;
        wait_cycles(1);
        check("SCAN reaches pre-trigger output", control_o == 14'sd400);
        acq_hold_i = 1'b1;
        scan_i = 14'sd401;
        wait_cycles(1);
        check("acquisition trigger edge holds exact current OUT2", control_o == 14'sd400);
        acq_hold_i = 1'b0;
        wait_cycles(1);
        check("SCAN resumes after isolated trigger pulse", control_o == 14'sd401);

        acq_abort_i = 1'b1;
        wait_cycles(1);
        check("acquisition ABORT drives SAFE zero immediately", control_o == 14'sd0);
        acq_abort_i = 1'b0;
        wait_cycles(1);
        check("SCAN resumes after isolated ABORT input", control_o == 14'sd401);

        acq_fault_i = 1'b1;
        wait_cycles(1);
        check("acquisition FAULT drives SAFE zero immediately", control_o == 14'sd0);
        acq_fault_i = 1'b0;
        scan_i = 14'sd321;
        wait_cycles(1);

        mode = MODE_HOLD;
        hold_value = -14'sd1234;
        wait_cycles(2);
        check("HOLD outputs fixed hold value", control_o == -14'sd1234);

        mode = MODE_P_LOCK;
        lock_bias = 14'sd777;
        kp = 14'sd0;
        polarity = 1'b0;
        error_i = 14'sd500;
        wait_cycles(1);
        check("P_LOCK transition holds lock_bias while pipeline fills", control_o == 14'sd777);

        mode = MODE_P_LOCK;
        lock_bias = 14'sd100;
        kp = 14'sd0;
        polarity = 1'b0;
        error_i = 14'sd500;
        wait_cycles(P_LOCK_LATENCY);
        check("P_LOCK Kp=0 outputs lock_bias", control_o == 14'sd100);

        kp = 14'sd256;
        error_i = 14'sd50;
        wait_cycles(P_LOCK_LATENCY);
        check("P_LOCK positive error increases output", control_o == 14'sd150);

        error_i = -14'sd50;
        wait_cycles(P_LOCK_LATENCY);
        check("P_LOCK negative error decreases output", control_o == 14'sd50);

        polarity = 1'b1;
        error_i = 14'sd50;
        wait_cycles(P_LOCK_LATENCY);
        check("P_LOCK polarity flip reverses direction", control_o == 14'sd50);

        polarity = 1'b0;
        lock_bias = 14'sd100;
        error_i = 14'sd1000;
        lock_correction_limit = 14'sd128;
        lock_limit = 14'sd8191;
        wait_cycles(P_LOCK_LATENCY);
        check("P_LOCK positive correction clamps before bias", control_o == 14'sd228);
        check("P_LOCK positive correction clamp asserts saturation", saturated_o == 1'b1);

        error_i = -14'sd1000;
        wait_cycles(P_LOCK_LATENCY);
        check("P_LOCK negative correction clamps before bias", control_o == -14'sd28);
        check("P_LOCK negative correction clamp asserts saturation", saturated_o == 1'b1);

        error_i = 14'sd100;
        lock_limit = 14'sd120;
        wait_cycles(P_LOCK_LATENCY);
        check("P_LOCK absolute limit clamps positive output", control_o == 14'sd120);
        check("P_LOCK absolute saturation flag asserts at limit", saturated_o == 1'b1);

        lock_bias = -14'sd100;
        error_i = -14'sd100;
        wait_cycles(P_LOCK_LATENCY);
        check("P_LOCK absolute limit clamps negative output", control_o == -14'sd120);
        check("P_LOCK negative absolute clamp asserts saturation", saturated_o == 1'b1);

        lock_bias = 14'sd100;
        error_i = 14'sd100;
        lock_limit = -14'sd120;
        wait_cycles(P_LOCK_LATENCY);
        check("negative lock limit is normalized before absolute clamp",
              control_o == 14'sd120 && saturated_o == 1'b1);

        lock_bias = 14'sd8100;
        error_i = 14'sd1000;
        lock_limit = -14'sd8192;
        wait_cycles(P_LOCK_LATENCY);
        check("lock_limit=-8192 saturates to absolute limit 8191",
              control_o == 14'sd8191 && saturated_o == 1'b1);

        lock_bias = 14'sd8100;
        lock_limit = 14'sd8191;
        error_i = 14'sd1000;
        wait_cycles(P_LOCK_LATENCY);
        check("P_LOCK output never exceeds positive DAC limit", control_o == 14'sd8191);
        check("P_LOCK positive DAC limit asserts saturation", saturated_o == 1'b1);

        lock_bias = -14'sd8100;
        error_i = -14'sd1000;
        wait_cycles(P_LOCK_LATENCY + 2);
        check("P_LOCK output never exceeds negative DAC limit", control_o == -14'sd8191);
        check("P_LOCK negative DAC limit asserts saturation", saturated_o == 1'b1);

        mode = MODE_HOLD;
        hold_value = 14'sd100;
        wait_cycles(1);
        mode = MODE_P_LOCK;
        lock_bias = 14'sd100;
        lock_limit = 14'sd120;
        error_i = 14'sd100;
        wait_cycles(P_LOCK_LATENCY);
        check("saturated target and written control are aligned",
              control_o == 14'sd120 && saturated_o == 1'b1);
        error_i = 14'sd0;
        wait_cycles(P_LOCK_LATENCY);
        check("unsaturated target clears saturation on its commit cycle",
              control_o == 14'sd100 && saturated_o == 1'b0);

        error_i = 14'sd1000;
        wait_cycles(3);
        mode = MODE_SCAN;
        scan_i = -14'sd222;
        wait_cycles(1);
        check("P_LOCK to SCAN bypasses and clears pending S6 data",
              control_o == -14'sd222 && dut.s6_valid == 1'b0);
        mode = MODE_P_LOCK;
        lock_bias = 14'sd333;
        lock_limit = 14'sd8191;
        kp = 14'sd0;
        pipeline_fill_ok = 1'b1;
        repeat (P_LOCK_LATENCY - 1) begin
            wait_cycles(1);
            if (control_o != 14'sd333)
                pipeline_fill_ok = 1'b0;
        end
        check("old P_LOCK target cannot commit after SCAN re-entry",
              pipeline_fill_ok);
        wait_cycles(1);
        check("fresh P_LOCK data commits after full refill", control_o == 14'sd333);

        kp = 14'sd256;
        error_i = 14'sd1000;
        wait_cycles(3);
        mode = MODE_HOLD;
        hold_value = -14'sd444;
        wait_cycles(1);
        check("P_LOCK to HOLD bypasses and clears pending S6 data",
              control_o == -14'sd444 && dut.s6_valid == 1'b0);
        mode = MODE_P_LOCK;
        lock_bias = 14'sd444;
        kp = 14'sd0;
        pipeline_fill_ok = 1'b1;
        repeat (P_LOCK_LATENCY - 1) begin
            wait_cycles(1);
            if (control_o != 14'sd444)
                pipeline_fill_ok = 1'b0;
        end
        check("old P_LOCK target cannot commit after HOLD re-entry",
              pipeline_fill_ok);

        kp = 14'sd256;
        error_i = 14'sd1000;
        wait_cycles(3);
        acq_abort_i = 1'b1;
        wait_cycles(1);
        check("P_LOCK abort clears output and pending valid immediately",
              control_o == 14'sd0 && dut.s6_valid == 1'b0);
        acq_abort_i = 1'b0;
        lock_bias = 14'sd555;
        kp = 14'sd0;
        pipeline_fill_ok = 1'b1;
        repeat (P_LOCK_LATENCY - 1) begin
            wait_cycles(1);
            if (control_o != 14'sd555)
                pipeline_fill_ok = 1'b0;
        end
        check("aborted pipeline cannot recover stale output", pipeline_fill_ok);

        kp = 14'sd256;
        error_i = -14'sd1000;
        wait_cycles(3);
        acq_fault_i = 1'b1;
        wait_cycles(1);
        check("P_LOCK fault clears output and pending valid immediately",
              control_o == 14'sd0 && dut.s6_valid == 1'b0);
        acq_fault_i = 1'b0;
        lock_bias = -14'sd555;
        kp = 14'sd0;
        pipeline_fill_ok = 1'b1;
        repeat (P_LOCK_LATENCY - 1) begin
            wait_cycles(1);
            if (control_o != -14'sd555)
                pipeline_fill_ok = 1'b0;
        end
        check("faulted pipeline cannot recover stale output", pipeline_fill_ok);

        lock_bias = 14'sd100;
        lock_limit = 14'sd8191;
        error_i = 14'sd0;

        enable = 1'b0;
        wait_cycles(2);
        check("ENABLE=0 has highest priority and clears output", control_o == 14'sd0);
        check("ENABLE=0 clears saturation", saturated_o == 1'b0);

        enable = 1'b1;
        mode = MODE_SAFE;
        wait_cycles(2);
        check("MODE=SAFE has highest priority and clears output", control_o == 14'sd0);

        mode = MODE_PI_LOCK;
        lock_bias = 14'sd100;
        lock_limit = 14'sd8191;
        kp = 14'sd0;
        ki = 14'sd256;
        polarity = 1'b0;
        error_i = 14'sd10;
        wait_cycles(P_LOCK_LATENCY);
        check("PI_LOCK Kp=0 ignores Ki and outputs lock_bias", control_o == 14'sd100);

        enable = 1'b0;
        wait_cycles(2);
        check("PI_LOCK ENABLE=0 clears output", control_o == 14'sd0);
        enable = 1'b1;
        wait_cycles(P_LOCK_LATENCY);
        check("PI_LOCK remains P-only after re-enable", control_o == 14'sd100);

        kp = 14'sd256;
        ki = 14'sd8191;
        error_i = 14'sd20;
        wait_cycles(P_LOCK_LATENCY);
        check("PI_LOCK ignores Ki but keeps P direction", control_o == 14'sd120);

        mode = MODE_SAFE;
        wait_cycles(2);
        check("PI_LOCK MODE=SAFE clears output", control_o == 14'sd0);
        mode = MODE_PI_LOCK;
        wait_cycles(P_LOCK_LATENCY);
        check("PI_LOCK recovers as P-only after SAFE", control_o == 14'sd120);

        integral_reset = 1'b1;
        wait_cycles(2);
        integral_reset = 1'b0;
        wait_cycles(P_LOCK_LATENCY);
        check("integral reset is accepted but no integral exists", control_o == 14'sd120);

        mode = MODE_HOLD;
        hold_value = 14'sd0;
        wait_cycles(2);
        mode = MODE_P_LOCK;
        lock_bias = 14'sd0;
        lock_limit = 14'sd30;
        lock_correction_limit = 14'sd50;
        kp = 14'sd256;
        polarity = 1'b0;
        servo_update_div = 16'd1;
        out2_slew_limit = 14'd8191;
        error_i = 14'sd10;
        wait_cycles(1);
        error_i = 14'sd100;
        wait_cycles(1);
        error_i = -14'sd10;
        wait_cycles(1);
        error_i = -14'sd100;
        wait_cycles(P_LOCK_LATENCY - 3);
        target_alignment_ok =
            (control_o == 14'sd10) && (saturated_o == 1'b0);
        wait_cycles(1);
        target_alignment_ok &=
            (control_o == 14'sd30) && (saturated_o == 1'b1);
        wait_cycles(1);
        target_alignment_ok &=
            (control_o == -14'sd10) && (saturated_o == 1'b0);
        wait_cycles(1);
        target_alignment_ok &=
            (control_o == -14'sd30) && (saturated_o == 1'b1);
        check("continuous target, saturation, and mode stay cycle-aligned",
              target_alignment_ok);

        mode = MODE_HOLD;
        hold_value = 14'sd0;
        wait_cycles(2);
        servo_update_div = 16'd3;
        out2_slew_limit = 14'd10;
        mode = MODE_P_LOCK;
        lock_bias = 14'sd0;
        lock_limit = 14'sd8191;
        lock_correction_limit = 14'sd256;
        kp = 14'sd256;
        polarity = 1'b0;
        error_i = 14'sd100;
        wait_cycles(P_LOCK_LATENCY);
        previous_control = $signed(control_o);
        changed_cycles = 0;
        slew_ok = 1'b1;
        divider_observed = 1'b0;
        repeat (15) begin
            wait_cycles(1);
            delta = $signed(control_o) - previous_control;
            if (delta < 0) delta = -delta;
            if (delta > 10) slew_ok = 1'b0;
            if (delta == 0) divider_observed = 1'b1;
            else changed_cycles++;
            previous_control = $signed(control_o);
        end
        check("P_LOCK slew limiter bounds every OUT2 update to configured counts",
              slew_ok && changed_cycles > 0);
        check("servo divider holds OUT2 between control updates",
              divider_observed && changed_cycles <= 5);
        mode = MODE_SAFE;
        wait_cycles(1);
        check("SAFE bypasses servo divider and slew limiter immediately",
              control_o == 14'sd0);

        $display("SUMMARY tb_out2_lock_controller tests=%0d pass=%0d fail=%0d", tests, pass_count, fail_count);
        if (fail_count != 0) begin
            $finish(1);
        end
        $finish;
    end

endmodule
