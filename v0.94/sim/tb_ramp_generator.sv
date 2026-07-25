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
    int expected_scan [0:12];
    bit range_ok;

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

    task automatic load_disabled_config(
        input logic signed [13:0] new_offset,
        input logic signed [13:0] new_amp,
        input logic signed [13:0] new_step,
        input logic        [31:0] new_update_div,
        input logic signed [13:0] new_limit
    );
        enable = 1'b0;
        offset = new_offset;
        amp = new_amp;
        step = new_step;
        update_div = new_update_div;
        limit = new_limit;
        wait_cycles(4);
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
        expected_scan[0]  = -3;
        expected_scan[1]  = -3;
        expected_scan[2]  = -1;
        expected_scan[3]  = -1;
        expected_scan[4]  = 1;
        expected_scan[5]  = 1;
        expected_scan[6]  = 3;
        expected_scan[7]  = 3;
        expected_scan[8]  = 1;
        expected_scan[9]  = 1;
        expected_scan[10] = -1;
        expected_scan[11] = -1;
        expected_scan[12] = -3;

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

        // Keep this exact cycle-by-cycle sequence as the latency/rhythm
        // contract. update_div=1 advances the two-stage triangle state every
        // two clocks; scan_o must not gain another output register.
        load_disabled_config(14'sd0, 14'sd3, 14'sd2, 32'd1, 14'sd8191);
        enable = 1'b1;
        range_ok = 1'b1;
        for (i = 0; i < 13; i++) begin
            wait_cycles(1);
            if ($signed(scan) != expected_scan[i]) begin
                range_ok = 1'b0;
            end
        end
        check("triangle rise/fall/reversal rhythm and output latency unchanged", range_ok);
        check("triangle returns to negative endpoint after direction reversal",
              $signed(scan) == -3);
        check("limit=8191 does not saturate in-range triangle",
              saturated == 1'b0);

        load_disabled_config(14'sd6962, 14'sd410, 14'sd41, 32'd2, 14'sd8191);
        enable = 1'b1;
        min_seen = 20000;
        max_seen = -20000;
        range_ok = 1'b1;
        for (i = 0; i < 120; i++) begin
            wait_cycles(1);
            if ($signed(scan) < min_seen) min_seen = $signed(scan);
            if ($signed(scan) > max_seen) max_seen = $signed(scan);
            if (($signed(scan) > 8191) || ($signed(scan) < -8191)) begin
                range_ok = 1'b0;
            end
        end
        check("scan always remains inside [-8191,8191]", range_ok);
        check("triangle reaches about 0.80 V", min_seen <= 14'sd6552);
        check("triangle reaches about 0.90 V", max_seen >= 14'sd7372);
        check("triangle remains near 0.80 to 0.90 V", (min_seen >= 14'sd6500) && (max_seen <= 14'sd7420));

        load_disabled_config(14'sd7000, 14'sd0, 14'sd1, 32'd1, 14'sd6500);
        enable = 1'b1;
        wait_cycles(2);
        check("limit=6500 clamps positive side", $signed(scan) == 6500);
        check("positive clamp asserts saturation", saturated == 1'b1);

        offset = -14'sd7000;
        wait_cycles(2);
        check("limit=6500 clamps negative side", $signed(scan) == -6500);
        check("negative clamp asserts saturation", saturated == 1'b1);

        offset = 14'sd1000;
        wait_cycles(1);
        check("offset update preserves existing one-cycle scan output latency",
              $signed(scan) == -6500);
        wait_cycles(1);
        check("returning inside limit restores raw scan", $signed(scan) == 1000);
        check("returning inside limit clears saturation", saturated == 1'b0);

        load_disabled_config(14'sd7000, 14'sd0, 14'sd1, 32'd1, -14'sd6500);
        enable = 1'b1;
        wait_cycles(2);
        check("negative limit matches positive limit on positive side",
              $signed(scan) == 6500);
        offset = -14'sd7000;
        wait_cycles(2);
        check("negative limit matches positive limit on negative side",
              $signed(scan) == -6500);

        load_disabled_config(-14'sd8192, 14'sd0, 14'sd1, 32'd1, -14'sd8192);
        enable = 1'b1;
        wait_cycles(2);
        check("limit=-8192 normalizes safely to 8191",
              $signed(scan) == -8191);
        check("limit=-8192 clamp asserts saturation", saturated == 1'b1);

        load_disabled_config(14'sd7000, 14'sd0, 14'sd1, 32'd1, 14'sd8191);
        enable = 1'b1;
        wait_cycles(2);
        check("wide limit initially passes raw scan", $signed(scan) == 7000);
        limit = 14'sd6500;
        wait_cycles(1);
        check("limit input capture does not add scan output latency",
              $signed(scan) == 7000);
        wait_cycles(1);
        check("registered limit applies on the existing following cycle",
              $signed(scan) == 6500);

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
