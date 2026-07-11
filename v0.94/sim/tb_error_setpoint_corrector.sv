`timescale 1ns/1ps

module tb_error_setpoint_corrector;

    logic clk = 1'b0;
    always #5 clk = ~clk;

    logic rstn;
    logic signed [13:0] error_i;
    logic signed [13:0] setpoint_i;
    logic signed [13:0] lock_error_o;

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

    task automatic apply_and_check(
        input string name,
        input logic signed [13:0] error_value,
        input logic signed [13:0] setpoint_value,
        input logic signed [13:0] expected
    );
        error_i = error_value;
        setpoint_i = setpoint_value;
        wait_cycles(1);
        check(name, lock_error_o == expected);
    endtask

    error_setpoint_corrector dut (
        .clk_i(clk),
        .rstn_i(rstn),
        .error_i(error_i),
        .setpoint_i(setpoint_i),
        .lock_error_o(lock_error_o)
    );

    initial begin
        rstn = 1'b0;
        error_i = 14'sd123;
        setpoint_i = 14'sd45;
        wait_cycles(3);
        check("reset output is zero", lock_error_o == 14'sd0);

        rstn = 1'b1;
        apply_and_check("positive error minus setpoint", 14'sd120, 14'sd20, 14'sd100);
        apply_and_check("negative corrected error", 14'sd20, 14'sd120, -14'sd100);
        apply_and_check("zero at captured setpoint", -14'sd77, -14'sd77, 14'sd0);
        apply_and_check("positive saturation", 14'sd8191, -14'sd8191, 14'sd8191);
        apply_and_check("negative saturation", -14'sd8191, 14'sd8191, -14'sd8191);

        $display("SUMMARY tb_error_setpoint_corrector tests=%0d pass=%0d fail=%0d", tests, pass_count, fail_count);
        if (fail_count != 0) begin
            $finish(1);
        end
        $finish;
    end

endmodule
