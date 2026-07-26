`timescale 1ns/1ps

module tb_l1_kp_ramp;
    logic clk = 1'b0;
    always #5 clk = ~clk;
    logic rstn;
    logic start;
    logic stop;
    logic servo_tick;
    logic signed [13:0] target;
    logic [13:0] step;
    logic [15:0] ramp_div;
    logic signed [13:0] effective;
    logic reached;
    integer tests;
    integer pass_count;
    integer fail_count;

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

    task automatic tick(input bit active);
        servo_tick = active;
        @(posedge clk);
        #1;
        servo_tick = 1'b0;
    endtask

    l1_kp_ramp dut (
        .clk_i(clk), .rstn_i(rstn), .start_i(start), .stop_i(stop),
        .servo_tick_i(servo_tick), .kp_target_i(target), .kp_step_i(step),
        .kp_ramp_div_i(ramp_div), .kp_effective_o(effective),
        .kp_target_reached_o(reached)
    );

    initial begin
        tests = 0;
        pass_count = 0;
        fail_count = 0;
        rstn = 1'b0;
        start = 1'b0;
        stop = 1'b0;
        servo_tick = 1'b0;
        target = 14'sd10;
        step = 14'd3;
        ramp_div = 16'd2;
        repeat (3) @(posedge clk);
        rstn = 1'b1;
        start = 1'b1;
        @(posedge clk);
        #1;
        start = 1'b0;
        check("start clears effective Kp", effective == 14'sd0);
        tick(1'b0);
        check("no servo tick means no Kp update", effective == 14'sd0);
        tick(1'b1);
        check("divider holds first servo tick", effective == 14'sd0);
        tick(1'b1);
        check("second servo tick applies one step", effective == 14'sd3);
        tick(1'b1);
        tick(1'b1);
        tick(1'b1);
        tick(1'b1);
        tick(1'b1);
        tick(1'b1);
        check("ramp clamps exactly at target", effective == 14'sd10 && reached);
        stop = 1'b1;
        @(posedge clk);
        #1;
        check("registered stop clears Kp on next edge", effective == 14'sd0);
        stop = 1'b0;
        $display("SUMMARY tb_l1_kp_ramp tests=%0d pass=%0d fail=%0d",
                 tests, pass_count, fail_count);
        if (fail_count != 0)
            $finish(1);
        $finish;
    end
endmodule
