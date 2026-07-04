`timescale 1ns/1ps

module tb_ramp_generator;

    logic clk = 1'b0;
    always #5 clk = ~clk;

    logic rstn;
    logic enable;
    logic signed [13:0] offset;
    logic signed [13:0] amp;
    logic signed [13:0] step;
    logic [31:0] update_div;
    logic signed [13:0] limit;
    logic signed [13:0] scan;
    logic saturated;

    int tests;
    int pass_count;
    int fail_count;
    int min_seen;
    int max_seen;
    int i;

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

    ramp_generator dut (
        .clk_i(clk),
        .rstn_i(rstn),
        .enable_i(enable),
        .offset_i(offset),
        .amp_i(amp),
        .step_i(step),
        .update_div_i(update_div),
        .limit_i(limit),
        .scan_o(scan),
        .saturated_o(saturated)
    );

    initial begin
        rstn = 1'b0;
        enable = 1'b0;
        offset = 14'sd6962;
        amp = 14'sd410;
        step = 14'sd41;
        update_div = 32'd2;
        limit = 14'sd8191;

        wait_cycles(4);
        check("reset drives safe value", scan == 14'sd0);
        rstn = 1'b1;
        wait_cycles(4);
        check("disabled drives safe value", scan == 14'sd0);

        enable = 1'b1;
        min_seen = 20000;
        max_seen = -20000;
        for (i = 0; i < 120; i++) begin
            wait_cycles(1);
            if ($signed(scan) < min_seen) min_seen = $signed(scan);
            if ($signed(scan) > max_seen) max_seen = $signed(scan);
            check("OUT2 never exceeds +1 V", $signed(scan) <= 8191);
            check("OUT2 never exceeds -1 V", $signed(scan) >= -8191);
        end
        check("triangle reaches about 0.80 V", min_seen <= 14'sd6552);
        check("triangle reaches about 0.90 V", max_seen >= 14'sd7372);
        check("triangle remains near 0.80 to 0.90 V", (min_seen >= 14'sd6500) && (max_seen <= 14'sd7420));

        limit = 14'sd6500;
        wait_cycles(40);
        check("saturation flag asserts when limited", saturated == 1'b1);
        check("limited output respects custom limit", $signed(scan) <= 6500);

        enable = 1'b0;
        wait_cycles(4);
        check("disable returns to safe value", scan == 14'sd0);
        check("disable clears saturation", saturated == 1'b0);

        $display("SUMMARY tb_ramp_generator tests=%0d pass=%0d fail=%0d", tests, pass_count, fail_count);
        if (fail_count != 0) begin
            $finish(1);
        end
        $finish;
    end

endmodule
