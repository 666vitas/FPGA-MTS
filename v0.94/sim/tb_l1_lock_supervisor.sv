`timescale 1ns/1ps

module tb_l1_lock_supervisor;
    localparam int OBSERVE_LENGTH = 256;
    localparam int SUPERVISOR_PIPELINE_LATENCY = 3;
    logic clk = 1'b0;
    always #5 clk = ~clk;
    logic rstn;
    logic start;
    logic stop;
    logic servo_tick;
    logic signed [14:0] lock_error;
    logic [14:0] abs_error;
    logic kp_reached;
    logic [23:0] mean_limit;
    logic [23:0] abs_limit;
    logic [23:0] divergence_limit;
    logic [7:0] confirm_windows;
    logic [7:0] divergence_windows;
    logic window_done;
    logic observation_good;
    logic observation_diverged;
    logic observation_invalid;
    logic supervisor_lock;
    logic supervisor_fail;
    logic [31:0] metrics;
    integer tests;
    integer pass_count;
    integer fail_count;
    integer window_pulses;
    integer lock_cycle;
    integer cycle_index;
    logic fail_seen;
    logic invalid_seen;

    always @(posedge clk) begin
        if (!rstn || start) begin
            fail_seen <= 1'b0;
            invalid_seen <= 1'b0;
        end else begin
            if (supervisor_fail)
                fail_seen <= 1'b1;
            if (observation_invalid)
                invalid_seen <= 1'b1;
        end
    end

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

    task automatic run_ticks(input integer count, input logic signed [14:0] value);
        integer n;
        begin
            for (n = 0; n < count; n++) begin
                lock_error = value;
                abs_error = value[14] ? -value : value;
                servo_tick = 1'b1;
                @(posedge clk);
                #1;
                cycle_index++;
                if (window_done)
                    window_pulses++;
                if (supervisor_lock)
                    lock_cycle = cycle_index;
            end
            servo_tick = 1'b0;
        end
    endtask

    task automatic pulse_start;
        begin
            start = 1'b1;
            @(posedge clk);
            #1;
            start = 1'b0;
        end
    endtask

    l1_lock_supervisor dut (
        .clk_i(clk), .rstn_i(rstn), .start_i(start), .stop_i(stop),
        .servo_tick_i(servo_tick), .lock_error_i(lock_error),
        .abs_error_i(abs_error), .kp_target_reached_i(kp_reached),
        .mean_sum_limit_i(mean_limit), .abs_sum_limit_i(abs_limit),
        .divergence_sum_limit_i(divergence_limit),
        .confirm_windows_i(confirm_windows),
        .divergence_windows_i(divergence_windows),
        .window_done_o(window_done), .observation_good_o(observation_good),
        .observation_diverged_o(observation_diverged),
        .observation_invalid_o(observation_invalid),
        .supervisor_lock_o(supervisor_lock),
        .supervisor_fail_o(supervisor_fail), .metrics_o(metrics)
    );

    initial begin
        tests = 0;
        pass_count = 0;
        fail_count = 0;
        rstn = 1'b0;
        start = 1'b0;
        stop = 1'b0;
        servo_tick = 1'b0;
        lock_error = 15'sd0;
        abs_error = 15'd0;
        kp_reached = 1'b1;
        mean_limit = 24'd8 << 8;
        abs_limit = 24'd12 << 8;
        divergence_limit = 24'd12 << 10;
        confirm_windows = 8'd2;
        divergence_windows = 8'd2;
        window_pulses = 0;
        lock_cycle = -1;
        cycle_index = 0;
        repeat (3) @(posedge clk);
        rstn = 1'b1;
        pulse_start();
        run_ticks(OBSERVE_LENGTH - 1, 15'sd1);
        check("window does not finish before tick 256", window_pulses == 0);
        run_ticks(1, 15'sd1);
        check("window finishes exactly on tick 256", window_pulses == 1);
        run_ticks(OBSERVE_LENGTH, 15'sd1);
        repeat (SUPERVISOR_PIPELINE_LATENCY) begin
            @(posedge clk);
            #1;
            cycle_index++;
            if (supervisor_lock)
                lock_cycle = cycle_index;
        end
        check("two good windows produce registered lock decision",
              lock_cycle >= (2 * OBSERVE_LENGTH));

        pulse_start();
        window_pulses = 0;
        run_ticks(2 * OBSERVE_LENGTH, 15'sd100);
        repeat (SUPERVISOR_PIPELINE_LATENCY) begin
            @(posedge clk);
            #1;
        end
        check("consecutive divergent windows produce registered fail",
              fail_seen);

        pulse_start();
        force dut.error_abs_sum_q = 24'hFF_FFF0;
        force dut.abs_overflow_q = 1'b0;
        run_ticks(OBSERVE_LENGTH, 15'sd8191);
        release dut.error_abs_sum_q;
        release dut.abs_overflow_q;
        repeat (SUPERVISOR_PIPELINE_LATENCY) begin
            @(posedge clk);
            #1;
        end
        check("accumulator overflow is a safe failure",
              invalid_seen && fail_seen);

        $display("SUMMARY tb_l1_lock_supervisor tests=%0d pass=%0d fail=%0d",
                 tests, pass_count, fail_count);
        if (fail_count != 0)
            $finish(1);
        $finish;
    end
endmodule
