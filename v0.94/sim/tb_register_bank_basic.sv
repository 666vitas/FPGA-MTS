`timescale 1ns/1ps

module tb_register_bank_basic;

    logic clk = 1'b0;
    always #5 clk = ~clk;

    logic rstn;
    logic signed [13:0] out2_monitor;
    logic signed [13:0] error_monitor;
    logic signed [13:0] control_monitor;
    logic saturated;
    logic [31:0] mode;
    logic enable;
    logic signed [13:0] scan_offset;
    logic signed [13:0] scan_amp;
    logic signed [13:0] scan_step;
    logic [31:0] scan_update_div;
    logic signed [13:0] out2_limit;
    logic signed [13:0] hold_value;
    logic signed [13:0] kp;
    logic polarity;
    logic signed [13:0] lock_bias;
    logic signed [13:0] lock_limit;
    logic signed [13:0] lock_correction_limit;
    logic signed [13:0] ki;
    logic integral_reset;
    logic capture_start;
    logic [31:0] capture_decimation;
    logic [31:0] capture_length;
    logic [31:0] capture_read_index;

    sys_bus_if bus (.clk(clk), .rstn(rstn));

    int tests;
    int pass_count;
    int fail_count;
    logic [31:0] read_data;

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

    task automatic bus_write(input logic [5:0] reg_addr, input logic [31:0] data);
        @(negedge clk);
        bus.addr = {24'd0, reg_addr, 2'b00};
        bus.wdata = data;
        bus.wen = 1'b1;
        bus.ren = 1'b0;
        @(posedge clk);
        @(negedge clk);
        bus.wen = 1'b0;
        bus.addr = 32'd0;
        bus.wdata = 32'd0;
        wait_cycles(1);
    endtask

    task automatic bus_read(input logic [5:0] reg_addr, output logic [31:0] data);
        @(negedge clk);
        bus.addr = {24'd0, reg_addr, 2'b00};
        bus.wen = 1'b0;
        bus.ren = 1'b1;
        @(posedge clk);
        @(negedge clk);
        bus.ren = 1'b0;
        data = bus.rdata;
        bus.addr = 32'd0;
        wait_cycles(1);
    endtask

    custom_register_bank dut (
        .clk_i(clk),
        .rstn_i(rstn),
        .out2_monitor_i(out2_monitor),
        .error_monitor_i(error_monitor),
        .control_monitor_i(control_monitor),
        .saturated_i(saturated),
        .mode_o(mode),
        .enable_o(enable),
        .scan_offset_o(scan_offset),
        .scan_amp_o(scan_amp),
        .scan_step_o(scan_step),
        .scan_update_div_o(scan_update_div),
        .out2_limit_o(out2_limit),
        .hold_value_o(hold_value),
        .kp_o(kp),
        .polarity_o(polarity),
        .lock_bias_o(lock_bias),
        .lock_limit_o(lock_limit),
        .lock_correction_limit_o(lock_correction_limit),
        .ki_o(ki),
        .integral_reset_o(integral_reset),
        .capture_start_o(capture_start),
        .capture_decimation_o(capture_decimation),
        .capture_length_o(capture_length),
        .capture_read_index_o(capture_read_index),
        .capture_busy_i(1'b0),
        .capture_done_i(1'b0),
        .capture_data_ch1_i(14'sd0),
        .capture_data_ch2_i(14'sd0),
        .capture_data_ch3_i(14'sd0),
        .capture_data_ch4_i(14'sd0),
        .bus(bus)
    );

    initial begin
        rstn = 1'b0;
        out2_monitor = 14'sd0;
        error_monitor = 14'sd0;
        control_monitor = 14'sd0;
        saturated = 1'b0;
        bus.wen = 1'b0;
        bus.ren = 1'b0;
        bus.addr = 32'd0;
        bus.wdata = 32'd0;

        wait_cycles(4);
        rstn = 1'b1;
        wait_cycles(2);

        check("reset mode is SAFE", mode == 32'd0);
        check("reset enable is off", enable == 1'b0);
        check("reset offset default is 0.85 V counts", scan_offset == 14'sd6962);
        check("reset amp default is 0.05 V counts", scan_amp == 14'sd410);

        bus_read(6'h00, read_data);
        check("magic register is readable", read_data == 32'h4D545330);
        bus_read(6'h01, read_data);
        // The register bank's documented standalone default is the D1 build.
        check("version register is readable", read_data == 32'h00030100);

        bus_write(6'h04, 32'd6962);
        bus_write(6'h05, 32'd410);
        bus_write(6'h06, 32'd2);
        bus_write(6'h07, 32'd1000);
        bus_write(6'h08, 32'd8191);
        bus_write(6'h02, 32'd1);
        bus_write(6'h03, 32'd1);

        check("scan mode write takes effect", mode == 32'd1);
        check("enable write takes effect", enable == 1'b1);
        check("offset write takes effect", scan_offset == 14'sd6962);
        check("amp write takes effect", scan_amp == 14'sd410);
        check("step write takes effect", scan_step == 14'sd2);
        check("update divider write takes effect", scan_update_div == 32'd1000);
        check("limit write takes effect", out2_limit == 14'sd8191);

        out2_monitor = 14'sd7000;
        saturated = 1'b1;
        bus_read(6'h09, read_data);
        check("status reflects enable", read_data[0] == 1'b1);
        check("status reflects saturation", read_data[1] == 1'b1);
        bus_read(6'h0A, read_data);
        check("out2 monitor is readable", $signed(read_data) == 32'sd7000);

        bus_write(6'h03, 32'd0);
        saturated = 1'b0;
        bus_read(6'h09, read_data);
        check("status clears enable", read_data[0] == 1'b0);
        check("status clears saturation", read_data[1] == 1'b0);

        $display("SUMMARY tb_register_bank_basic tests=%0d pass=%0d fail=%0d", tests, pass_count, fail_count);
        if (fail_count != 0) begin
            $finish(1);
        end
        $finish;
    end

endmodule
