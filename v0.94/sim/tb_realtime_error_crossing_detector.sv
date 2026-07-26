`timescale 1ns/1ps

module tb_realtime_error_crossing_detector;
    localparam logic [1:0] RISING = 2'd1;
    localparam logic [1:0] FALLING = 2'd2;
    localparam logic [1:0] NEG_TO_POS = 2'd1;
    localparam logic [1:0] POS_TO_NEG = 2'd2;

    logic clk = 1'b0;
    always #5 clk = ~clk;

    logic rstn;
    logic clear;
    logic armed;
    logic runtime_ok;
    logic in_guard;
    logic [1:0] scan_direction;
    logic [1:0] required_scan_direction;
    logic [1:0] required_error_direction;
    logic signed [14:0] lock_error;
    logic [13:0] hysteresis;
    logic [7:0] consecutive_samples;
    logic crossing;
    logic source_confirmed;
    logic pass_consumed;

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

    task automatic sample(input logic signed [14:0] value);
        lock_error = value;
        @(posedge clk);
        #1;
    endtask

    realtime_error_crossing_detector dut (
        .clk_i(clk),
        .rstn_i(rstn),
        .clear_i(clear),
        .armed_i(armed),
        .runtime_ok_i(runtime_ok),
        .in_guard_i(in_guard),
        .scan_direction_i(scan_direction),
        .required_scan_direction_i(required_scan_direction),
        .required_error_direction_i(required_error_direction),
        .lock_error_i(lock_error),
        .hysteresis_i(hysteresis),
        .consecutive_samples_i(consecutive_samples),
        .crossing_o(crossing),
        .source_confirmed_o(source_confirmed),
        .pass_consumed_o(pass_consumed)
    );

    initial begin
        rstn = 1'b0;
        clear = 1'b0;
        armed = 1'b0;
        runtime_ok = 1'b1;
        in_guard = 1'b1;
        scan_direction = RISING;
        required_scan_direction = RISING;
        required_error_direction = NEG_TO_POS;
        lock_error = 15'sd0;
        hysteresis = 14'd4;
        consecutive_samples = 8'd3;
        repeat (3) @(posedge clk);
        rstn = 1'b1;

        sample(-15'sd8);
        sample(-15'sd8);
        sample(-15'sd8);
        check("no ARM never records source history", !source_confirmed && !crossing);

        armed = 1'b1;
        sample(15'sd8);
        sample(15'sd8);
        sample(15'sd8);
        check("entering guard on destination side does not trigger", !crossing && !source_confirmed);

        sample(-15'sd8);
        sample(-15'sd8);
        check("N-1 source samples are insufficient", !source_confirmed);
        sample(-15'sd8);
        check("N source samples arm the crossing", source_confirmed);
        sample(15'sd8);
        sample(15'sd8);
        check("N-1 destination samples do not trigger", !crossing);
        sample(15'sd8);
        check("NEG_TO_POS triggers after hysteresis and N samples", crossing);
        sample(-15'sd8);
        sample(-15'sd8);
        sample(-15'sd8);
        sample(15'sd8);
        sample(15'sd8);
        sample(15'sd8);
        check("one guard pass produces at most one event", !crossing && pass_consumed);

        in_guard = 1'b0;
        sample(-15'sd8);
        check("leaving guard clears source history and consumed latch",
              !source_confirmed && !pass_consumed);
        in_guard = 1'b1;
        sample(-15'sd8);
        sample(-15'sd8);
        sample(-15'sd8);
        sample(15'sd8);
        sample(15'sd8);
        sample(15'sd8);
        check("re-entering guard permits a new event", crossing);

        in_guard = 1'b0;
        sample(15'sd8);
        in_guard = 1'b1;
        required_error_direction = POS_TO_NEG;
        sample(15'sd8);
        sample(15'sd8);
        sample(15'sd8);
        sample(-15'sd8);
        sample(-15'sd8);
        sample(-15'sd8);
        check("POS_TO_NEG uses the inverse source/destination sides", crossing);

        in_guard = 1'b0;
        sample(-15'sd8);
        in_guard = 1'b1;
        scan_direction = FALLING;
        sample(15'sd8);
        sample(15'sd8);
        sample(15'sd8);
        check("direction mismatch clears history", !source_confirmed && !crossing);

        scan_direction = RISING;
        sample(15'sd2);
        sample(-15'sd2);
        sample(15'sd2);
        sample(-15'sd2);
        check("deadband noise never establishes a source side", !source_confirmed && !crossing);

        clear = 1'b1;
        sample(15'sd8);
        clear = 1'b0;
        check("explicit clear removes all crossing history",
              !source_confirmed && !pass_consumed && !crossing);

        $display("SUMMARY tb_realtime_error_crossing_detector tests=%0d pass=%0d fail=%0d",
                 tests, pass_count, fail_count);
        if (fail_count != 0)
            $finish(1);
        $finish;
    end
endmodule
