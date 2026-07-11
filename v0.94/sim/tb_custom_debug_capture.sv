`timescale 1ns/1ps

module tb_custom_debug_capture;

    logic clk = 1'b0;
    always #5 clk = ~clk;

    logic rstn;
    logic start;
    logic [31:0] decimation;
    logic [31:0] length;
    logic [31:0] read_index;
    logic signed [13:0] ch1;
    logic signed [13:0] ch2;
    logic signed [13:0] ch3;
    logic signed [13:0] ch4;
    logic busy;
    logic done;
    logic signed [13:0] data_ch1;
    logic signed [13:0] data_ch2;
    logic signed [13:0] data_ch3;
    logic signed [13:0] data_ch4;

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

    custom_debug_capture #(.DEPTH(16)) dut (
        .clk_i(clk),
        .rstn_i(rstn),
        .start_i(start),
        .decimation_i(decimation),
        .length_i(length),
        .read_index_i(read_index),
        .ch1_i(ch1),
        .ch2_i(ch2),
        .ch3_i(ch3),
        .ch4_i(ch4),
        .busy_o(busy),
        .done_o(done),
        .data_ch1_o(data_ch1),
        .data_ch2_o(data_ch2),
        .data_ch3_o(data_ch3),
        .data_ch4_o(data_ch4)
    );

    initial begin
        rstn = 1'b0;
        start = 1'b0;
        decimation = 32'd2;
        length = 32'd4;
        read_index = 32'd0;
        ch1 = 14'sd0;
        ch2 = 14'sd0;
        ch3 = 14'sd0;
        ch4 = 14'sd0;

        wait_cycles(3);
        check("reset idle", busy == 1'b0 && done == 1'b0);
        rstn = 1'b1;

        @(negedge clk);
        start = 1'b1;
        @(negedge clk);
        start = 1'b0;

        repeat (20) begin
            @(negedge clk);
            ch1 = ch1 + 14'sd1;
            ch2 = ch2 - 14'sd1;
            ch3 = ch3 + 14'sd2;
            ch4 = ch4 - 14'sd2;
        end
        #1;

        check("capture completes", busy == 1'b0 && done == 1'b1);

        read_index = 32'd0;
        #1;
        check("CH1 index 0 captured", data_ch1 != 14'sd0);
        check("CH2 index 0 captured", data_ch2 != 14'sd0);
        check("CH3 index 0 captured", data_ch3 != 14'sd0);
        check("CH4 index 0 captured", data_ch4 != 14'sd0);

        read_index = 32'd3;
        #1;
        check("CH1 index 3 later than index 0", data_ch1 > 14'sd0);
        check("CH2 index 3 later negative", data_ch2 < 14'sd0);
        check("CH3 index 3 later positive", data_ch3 > 14'sd0);
        check("CH4 index 3 later negative", data_ch4 < 14'sd0);

        @(negedge clk);
        decimation = 32'd0;
        length = 32'd0;
        start = 1'b1;
        @(negedge clk);
        start = 1'b0;
        wait_cycles(3);
        check("zero decimation and length are sanitized", busy == 1'b0 && done == 1'b1);

        $display("SUMMARY tb_custom_debug_capture tests=%0d pass=%0d fail=%0d", tests, pass_count, fail_count);
        if (fail_count != 0) begin
            $finish(1);
        end
        $finish;
    end

endmodule
