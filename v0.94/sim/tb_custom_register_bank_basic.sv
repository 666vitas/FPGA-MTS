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
    localparam logic [5:0] REG_OUT2_MONITOR    = 6'h0A;
    localparam logic [5:0] REG_HOLD_VALUE      = 6'h0B;
    localparam logic [5:0] REG_KP              = 6'h0C;
    localparam logic [5:0] REG_POLARITY        = 6'h0D;
    localparam logic [5:0] REG_LOCK_BIAS       = 6'h0E;
    localparam logic [5:0] REG_LOCK_LIMIT      = 6'h0F;
    localparam logic [5:0] REG_ERROR_MONITOR   = 6'h10;
    localparam logic [5:0] REG_CONTROL_MONITOR = 6'h11;
    localparam logic [5:0] REG_KI              = 6'h12;
    localparam logic [5:0] REG_INTEGRAL_RESET  = 6'h13;

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
    logic signed [13:0] ki;
    logic integral_reset;

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
        .ki_o(ki),
        .integral_reset_o(integral_reset),
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

        check("reset MODE is SAFE", mode == 32'd0);
        check("reset ENABLE is disabled", enable == 1'b0);
        check("reset SCAN_OFFSET is 6962", scan_offset == 14'sd6962);
        check("reset SCAN_AMP is 410", scan_amp == 14'sd410);
        check("reset SCAN_STEP is 1", scan_step == 14'sd1);
        check("reset SCAN_UPDATE_DIV is 1524", scan_update_div == 32'd1524);
        check("reset OUT2_LIMIT is 8191", out2_limit == 14'sd8191);
        check("reset HOLD_VALUE is 0", hold_value == 14'sd0);
        check("reset KP is 0", kp == 14'sd0);
        check("reset POLARITY is normal", polarity == 1'b0);
        check("reset LOCK_BIAS is 0", lock_bias == 14'sd0);
        check("reset LOCK_LIMIT is 8191", lock_limit == 14'sd8191);
        check("reset KI is 0", ki == 14'sd0);

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
        bus_write(REG_HOLD_VALUE, 32'hFFFF_FC18);
        bus_write(REG_KP, 32'd256);
        bus_write(REG_POLARITY, 32'd1);
        bus_write(REG_LOCK_BIAS, 32'd1234);
        bus_write(REG_LOCK_LIMIT, 32'd6000);
        bus_write(REG_KI, 32'd8);
        bus_write(REG_INTEGRAL_RESET, 32'd1);

        check("write MODE=1 reaches output", mode == 32'd1);
        check("write ENABLE=1 reaches output", enable == 1'b1);
        check("write SCAN_OFFSET=7000 reaches output", scan_offset == 14'sd7000);
        check("write SCAN_AMP=300 reaches output", scan_amp == 14'sd300);
        check("write SCAN_STEP=2 reaches output", scan_step == 14'sd2);
        check("write SCAN_UPDATE_DIV=2000 reaches output", scan_update_div == 32'd2000);
        check("write OUT2_LIMIT=7000 reaches output", out2_limit == 14'sd7000);
        check("write HOLD_VALUE=-1000 reaches output", hold_value == -14'sd1000);
        check("write KP=256 reaches output", kp == 14'sd256);
        check("write POLARITY=1 reaches output", polarity == 1'b1);
        check("write LOCK_BIAS=1234 reaches output", lock_bias == 14'sd1234);
        check("write LOCK_LIMIT=6000 reaches output", lock_limit == 14'sd6000);
        check("write KI=8 reaches output", ki == 14'sd8);
        wait_cycles(2);
        check("INTEGRAL_RESET self clears", integral_reset == 1'b0);

        bus_read(REG_MODE, read_data);
        check("read back MODE=1", read_data == 32'd1);
        bus_write(REG_MODE, 32'd2);
        bus_read(REG_MODE, read_data);
        check("read back MODE=2 HOLD", read_data == 32'd2);
        bus_write(REG_MODE, 32'd3);
        bus_read(REG_MODE, read_data);
        check("read back MODE=3 P_LOCK", read_data == 32'd3);
        bus_write(REG_MODE, 32'd4);
        bus_read(REG_MODE, read_data);
        check("read back MODE=4 PI_LOCK", read_data == 32'd4);
        bus_write(REG_MODE, 32'd99);
        bus_read(REG_MODE, read_data);
        check("invalid MODE returns SAFE", read_data == 32'd0);
        bus_write(REG_MODE, 32'd1);
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
        bus_read(REG_HOLD_VALUE, read_data);
        check("read back HOLD_VALUE=-1000", $signed(read_data) == -32'sd1000);
        bus_read(REG_KP, read_data);
        check("read back KP=256", $signed(read_data) == 32'sd256);
        bus_read(REG_POLARITY, read_data);
        check("read back POLARITY=1", read_data == 32'd1);
        bus_read(REG_LOCK_BIAS, read_data);
        check("read back LOCK_BIAS=1234", $signed(read_data) == 32'sd1234);
        bus_read(REG_LOCK_LIMIT, read_data);
        check("read back LOCK_LIMIT=6000", $signed(read_data) == 32'sd6000);
        bus_read(REG_KI, read_data);
        check("read back KI=8", $signed(read_data) == 32'sd8);

        out2_monitor = 14'sd111;
        error_monitor = -14'sd222;
        control_monitor = 14'sd333;
        wait_cycles(2);
        bus_read(REG_OUT2_MONITOR, read_data);
        check("read OUT2_MONITOR", $signed(read_data) == 32'sd111);
        bus_read(REG_ERROR_MONITOR, read_data);
        check("read ERROR_MONITOR", $signed(read_data) == -32'sd222);
        bus_read(REG_CONTROL_MONITOR, read_data);
        check("read CONTROL_MONITOR", $signed(read_data) == 32'sd333);

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
