`timescale 1ns/1ps

module tb_custom_register_bank_basic;

    localparam logic [5:0] REG_MAGIC           = 6'h00;
    localparam logic [5:0] REG_VERSION         = 6'h01;
    localparam logic [5:0] REG_MODE            = 6'h02;
    localparam logic [5:0] REG_ENABLE          = 6'h03;
    localparam logic [5:0] REG_SCAN_OFFSET     = 6'h04;
    localparam logic [5:0] REG_SCAN_AMP        = 6'h05;
    localparam logic [5:0] REG_SCAN_STEP       = 6'h06;
    localparam logic [5:0] REG_SCAN_UPDATE_DIV = 6'h07;
    localparam logic [5:0] REG_OUT2_LIMIT      = 6'h08;
    localparam logic [5:0] REG_STATUS          = 6'h09;

    logic clk = 1'b0;
    always #5 clk = ~clk;

    logic rstn;
    logic signed [13:0] out2_monitor;
    logic saturated;
    logic [31:0] mode;
    logic enable;
    logic signed [13:0] scan_offset;
    logic signed [13:0] scan_amp;
    logic signed [13:0] scan_step;
    logic [31:0] scan_update_div;
    logic signed [13:0] out2_limit;

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
        .saturated_i(saturated),
        .mode_o(mode),
        .enable_o(enable),
        .scan_offset_o(scan_offset),
        .scan_amp_o(scan_amp),
        .scan_step_o(scan_step),
        .scan_update_div_o(scan_update_div),
        .out2_limit_o(out2_limit),
        .bus(bus)
    );

    initial begin
        rstn = 1'b0;
        out2_monitor = 14'sd0;
        saturated = 1'b0;
        bus.wen = 1'b0;
        bus.ren = 1'b0;
        bus.addr = 32'd0;
        bus.wdata = 32'd0;

        wait_cycles(4);
        rstn = 1'b1;
        wait_cycles(2);

        check("reset MODE is SAFE", mode == 32'd0);
        check("reset ENABLE is disabled", enable == 1'b0);
        check("reset SCAN_OFFSET is 6962", scan_offset == 14'sd6962);
        check("reset SCAN_AMP is 410", scan_amp == 14'sd410);
        check("reset SCAN_STEP is 1", scan_step == 14'sd1);
        check("reset SCAN_UPDATE_DIV is 1524", scan_update_div == 32'd1524);
        check("reset OUT2_LIMIT is 8191", out2_limit == 14'sd8191);

        bus_read(REG_MAGIC, read_data);
        check("read MAGIC", read_data == 32'h4D545330);
        bus_read(REG_VERSION, read_data);
        check("read VERSION", read_data == 32'h00030000);

        bus_write(REG_MODE, 32'd1);
        bus_write(REG_ENABLE, 32'd1);
        bus_write(REG_SCAN_OFFSET, 32'd7000);
        bus_write(REG_SCAN_AMP, 32'd300);
        bus_write(REG_SCAN_STEP, 32'd2);
        bus_write(REG_SCAN_UPDATE_DIV, 32'd2000);
        bus_write(REG_OUT2_LIMIT, 32'd7000);

        check("write MODE=1 reaches output", mode == 32'd1);
        check("write ENABLE=1 reaches output", enable == 1'b1);
        check("write SCAN_OFFSET=7000 reaches output", scan_offset == 14'sd7000);
        check("write SCAN_AMP=300 reaches output", scan_amp == 14'sd300);
        check("write SCAN_STEP=2 reaches output", scan_step == 14'sd2);
        check("write SCAN_UPDATE_DIV=2000 reaches output", scan_update_div == 32'd2000);
        check("write OUT2_LIMIT=7000 reaches output", out2_limit == 14'sd7000);

        bus_read(REG_MODE, read_data);
        check("read back MODE=1", read_data == 32'd1);
        bus_read(REG_ENABLE, read_data);
        check("read back ENABLE=1", read_data == 32'd1);
        bus_read(REG_SCAN_OFFSET, read_data);
        check("read back SCAN_OFFSET=7000", $signed(read_data) == 32'sd7000);
        bus_read(REG_SCAN_AMP, read_data);
        check("read back SCAN_AMP=300", $signed(read_data) == 32'sd300);
        bus_read(REG_SCAN_STEP, read_data);
        check("read back SCAN_STEP=2", $signed(read_data) == 32'sd2);
        bus_read(REG_SCAN_UPDATE_DIV, read_data);
        check("read back SCAN_UPDATE_DIV=2000", read_data == 32'd2000);
        bus_read(REG_OUT2_LIMIT, read_data);
        check("read back OUT2_LIMIT=7000", $signed(read_data) == 32'sd7000);

        saturated = 1'b1;
        bus_read(REG_STATUS, read_data);
        check("STATUS bit0 reflects enabled scan", read_data[0] == 1'b1);
        check("STATUS bit1 reflects saturation", read_data[1] == 1'b1);

        saturated = 1'b0;
        bus_write(REG_ENABLE, 32'd0);
        bus_read(REG_STATUS, read_data);
        check("STATUS bit0 clears when disabled", read_data[0] == 1'b0);
        check("STATUS bit1 clears when not saturated", read_data[1] == 1'b0);

        $display("SUMMARY tb_custom_register_bank_basic tests=%0d pass=%0d fail=%0d", tests, pass_count, fail_count);
        if (fail_count != 0) begin
            $finish(1);
        end
        $finish;
    end

endmodule
