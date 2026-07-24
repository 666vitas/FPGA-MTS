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
    localparam logic [5:0] REG_LOCK_CORRECTION_LIMIT = 6'h14;
    localparam logic [5:0] REG_ERROR_SETPOINT  = 6'h15;
    localparam logic [5:0] REG_LOCK_ERROR_MONITOR = 6'h16;
    localparam logic [5:0] REG_CAPTURE_LOCK_POINT = 6'h17;
    localparam logic [5:0] REG_TARGET_OUT2_SHADOW = 6'h18;
    localparam logic [5:0] REG_TARGET_ERROR_SETPOINT_SHADOW = 6'h19;
    localparam logic [5:0] REG_TARGET_WINDOW_SHADOW = 6'h1A;
    localparam logic [5:0] REG_TARGET_REQUIREMENTS_SHADOW = 6'h1B;
    localparam logic [5:0] REG_CORRECTION_LIMIT_SHADOW = 6'h1C;
    localparam logic [5:0] REG_ABSOLUTE_LIMIT_SHADOW = 6'h1D;
    localparam logic [5:0] REG_CONFIG_GENERATION_SHADOW = 6'h1E;
    localparam logic [5:0] REG_CONFIG_VALIDATION = 6'h1F;
    localparam logic [5:0] REG_CAPTURE_CTRL       = 6'h20;
    localparam logic [5:0] REG_CAPTURE_STATUS     = 6'h21;
    localparam logic [5:0] REG_CAPTURE_DECIMATION = 6'h22;
    localparam logic [5:0] REG_CAPTURE_LENGTH     = 6'h23;
    localparam logic [5:0] REG_CAPTURE_READ_INDEX = 6'h24;
    localparam logic [5:0] REG_CAPTURE_DATA_CH1   = 6'h25;
    localparam logic [5:0] REG_CAPTURE_DATA_CH2   = 6'h26;
    localparam logic [5:0] REG_CAPTURE_DATA_CH3   = 6'h27;
    localparam logic [5:0] REG_CAPTURE_DATA_CH4   = 6'h28;
    localparam logic [5:0] REG_ACQ_COMMAND = 6'h29;
    localparam logic [5:0] REG_ACQ_STATE = 6'h2A;
    localparam logic [5:0] REG_EVENT_SEQUENCE = 6'h2B;
    localparam logic [5:0] REG_EVENT_OUT2 = 6'h2C;
    localparam logic [5:0] REG_EVENT_ERROR = 6'h2D;
    localparam logic [5:0] REG_EVENT_CONFIG_GENERATION = 6'h2E;
    localparam logic [5:0] REG_EVENT_INFO = 6'h2F;
    localparam logic [5:0] REG_EVENT_TIMESTAMP_LO = 6'h30;
    localparam logic [5:0] REG_EVENT_TIMESTAMP_HI = 6'h31;
    localparam logic [5:0] REG_ACTIVE_TARGET_OUT2 = 6'h32;
    localparam logic [5:0] REG_ACTIVE_ERROR_SETPOINT = 6'h33;
    localparam logic [5:0] REG_ACTIVE_WINDOW = 6'h34;
    localparam logic [5:0] REG_ACTIVE_REQUIREMENTS = 6'h35;
    localparam logic [5:0] REG_ACTIVE_CORRECTION_LIMIT = 6'h36;
    localparam logic [5:0] REG_ACTIVE_ABSOLUTE_LIMIT = 6'h37;
    localparam logic [5:0] REG_FAULT_DETAIL = 6'h38;

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
    logic signed [13:0] error_setpoint;
    logic signed [13:0] ki;
    logic integral_reset;
    logic acq_trigger;
    logic acq_hold;
    logic acq_abort;
    logic acq_fault;
    logic capture_start;
    logic [31:0] capture_decimation;
    logic [31:0] capture_length;
    logic [31:0] capture_read_index;
    logic capture_busy;
    logic capture_done;
    logic signed [13:0] lock_error_monitor;
    logic signed [13:0] capture_data_ch1;
    logic signed [13:0] capture_data_ch2;
    logic signed [13:0] capture_data_ch3;
    logic signed [13:0] capture_data_ch4;

    sys_bus_if bus (.clk(clk), .rstn(rstn));

    int tests;
    int pass_count;
    int fail_count;
    logic [31:0] read_data;
    bit capture_pulse_seen;

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

    task automatic arm_and_check_fixed_pipeline;
        @(negedge clk);
        bus.addr = {24'd0, REG_ACQ_COMMAND, 2'b00};
        bus.wdata = 32'h0000_0001;
        bus.wen = 1'b1;
        bus.ren = 1'b0;
        @(posedge clk);
        #1;
        check(
            "ARM request cycle only snapshots and remains SCAN",
            dut.i_deterministic_lock_acquisition.state_q == 3'd1
        );
        check(
            "ARM request cycle does not update active target",
            dut.i_deterministic_lock_acquisition.active_target_out2_o == 14'sd0
        );
        @(negedge clk);
        bus.wen = 1'b0;
        bus.addr = 32'd0;
        bus.wdata = 32'd0;

        wait_cycles(1);
        check(
            "ARM validate cycle remains SCAN",
            dut.i_deterministic_lock_acquisition.state_q == 3'd1
        );
        wait_cycles(1);
        check(
            "ARM decide cycle remains SCAN",
            dut.i_deterministic_lock_acquisition.state_q == 3'd1
        );
        wait_cycles(1);
        check(
            "ARM commit preparation remains SCAN",
            dut.i_deterministic_lock_acquisition.state_q == 3'd1
        );
        wait_cycles(1);
        check(
            "ARM accepts at fixed four-cycle latency",
            dut.i_deterministic_lock_acquisition.state_q == 3'd2
        );
    endtask

    task automatic bus_write_during_forced_acquisition(
        input logic [5:0] reg_addr,
        input logic [31:0] data,
        output bit capture_start_seen
    );
        @(negedge clk);
        force dut.acq_abort_o = 1'b1;
        force dut.acq_fault_o = 1'b1;
        force dut.acq_trigger_o = 1'b1;
        force dut.arm_accepted_w = 1'b1;
        bus.addr = {24'd0, reg_addr, 2'b00};
        bus.wdata = data;
        bus.wen = 1'b1;
        bus.ren = 1'b0;
        @(posedge clk);
        #1;
        capture_start_seen = capture_start;
        @(negedge clk);
        bus.wen = 1'b0;
        bus.addr = 32'd0;
        bus.wdata = 32'd0;
        release dut.acq_abort_o;
        release dut.acq_fault_o;
        release dut.acq_trigger_o;
        release dut.arm_accepted_w;
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
        .error_setpoint_o(error_setpoint),
        .ki_o(ki),
        .integral_reset_o(integral_reset),
        .acq_trigger_o(acq_trigger),
        .acq_hold_o(acq_hold),
        .acq_abort_o(acq_abort),
        .acq_fault_o(acq_fault),
        .capture_start_o(capture_start),
        .capture_decimation_o(capture_decimation),
        .capture_length_o(capture_length),
        .capture_read_index_o(capture_read_index),
        .capture_busy_i(capture_busy),
        .capture_done_i(capture_done),
        .lock_error_monitor_i(lock_error_monitor),
        .capture_data_ch1_i(capture_data_ch1),
        .capture_data_ch2_i(capture_data_ch2),
        .capture_data_ch3_i(capture_data_ch3),
        .capture_data_ch4_i(capture_data_ch4),
        .bus(bus)
    );

    initial begin
        rstn = 1'b0;
        out2_monitor = 14'sd0;
        error_monitor = 14'sd0;
        control_monitor = 14'sd0;
        saturated = 1'b0;
        capture_busy = 1'b0;
        capture_done = 1'b0;
        lock_error_monitor = 14'sd0;
        capture_data_ch1 = 14'sd11;
        capture_data_ch2 = -14'sd22;
        capture_data_ch3 = 14'sd33;
        capture_data_ch4 = -14'sd44;
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
        check("reset LOCK_CORRECTION_LIMIT is 128", lock_correction_limit == 14'sd128);
        check("reset ERROR_SETPOINT is 0", error_setpoint == 14'sd0);
        check("reset KI is 0", ki == 14'sd0);
        check("reset CAPTURE_DECIMATION is 1024", capture_decimation == 32'd1024);
        check("reset CAPTURE_LENGTH is 2048", capture_length == 32'd2048);

        bus_read(REG_MAGIC, read_data);
        check("read MAGIC", read_data == 32'h4D545330);
        bus_read(REG_VERSION, read_data);
        check("read VERSION", read_data == 32'h00030100);

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
        bus_write(REG_LOCK_CORRECTION_LIMIT, 32'd128);
        bus_write(REG_ERROR_SETPOINT, 32'hFFFF_FF9C);
        bus_write(REG_KI, 32'd8);
        bus_write(REG_INTEGRAL_RESET, 32'd1);
        bus_write(REG_CAPTURE_DECIMATION, 32'd64);
        bus_write(REG_CAPTURE_LENGTH, 32'd4096);
        bus_write(REG_CAPTURE_READ_INDEX, 32'd7);

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
        check("write LOCK_CORRECTION_LIMIT=128 reaches output", lock_correction_limit == 14'sd128);
        check("write ERROR_SETPOINT=-100 reaches output", error_setpoint == -14'sd100);
        check("write KI=8 reaches output", ki == 14'sd8);
        check("write CAPTURE_DECIMATION=64 reaches output", capture_decimation == 32'd64);
        check("write CAPTURE_LENGTH=4096 reaches output", capture_length == 32'd4096);
        check("write CAPTURE_READ_INDEX=7 reaches output", capture_read_index == 32'd7);
        wait_cycles(2);
        check("INTEGRAL_RESET self clears", integral_reset == 1'b0);
        bus_write(REG_CAPTURE_CTRL, 32'd1);
        check("CAPTURE_CTRL self clears after write", capture_start == 1'b0);

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
        bus_read(REG_LOCK_CORRECTION_LIMIT, read_data);
        check("read back LOCK_CORRECTION_LIMIT=128", $signed(read_data) == 32'sd128);
        bus_read(REG_ERROR_SETPOINT, read_data);
        check("read back ERROR_SETPOINT=-100", $signed(read_data) == -32'sd100);
        lock_error_monitor = -14'sd321;
        wait_cycles(2);
        bus_read(REG_LOCK_ERROR_MONITOR, read_data);
        check("read LOCK_ERROR_MONITOR", $signed(read_data) == -32'sd321);
        bus_read(REG_KI, read_data);
        check("read back KI=8", $signed(read_data) == 32'sd8);
        bus_read(REG_CAPTURE_DECIMATION, read_data);
        check("read back CAPTURE_DECIMATION=64", read_data == 32'd64);
        bus_read(REG_CAPTURE_LENGTH, read_data);
        check("read back CAPTURE_LENGTH=4096", read_data == 32'd4096);
        bus_read(REG_CAPTURE_READ_INDEX, read_data);
        check("read back CAPTURE_READ_INDEX=7", read_data == 32'd7);
        capture_busy = 1'b1;
        capture_done = 1'b1;
        bus_read(REG_CAPTURE_STATUS, read_data);
        check("read CAPTURE_STATUS busy", read_data[0] == 1'b1);
        check("read CAPTURE_STATUS done", read_data[1] == 1'b1);
        bus_read(REG_CAPTURE_DATA_CH1, read_data);
        check("read CAPTURE_DATA_CH1", $signed(read_data) == 32'sd11);
        bus_read(REG_CAPTURE_DATA_CH2, read_data);
        check("read CAPTURE_DATA_CH2", $signed(read_data) == -32'sd22);
        bus_read(REG_CAPTURE_DATA_CH3, read_data);
        check("read CAPTURE_DATA_CH3", $signed(read_data) == 32'sd33);
        bus_read(REG_CAPTURE_DATA_CH4, read_data);
        check("read CAPTURE_DATA_CH4", $signed(read_data) == -32'sd44);

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

        bus_write(REG_MODE, 32'd1);
        bus_write(REG_ENABLE, 32'd1);
        out2_monitor = 14'sd2345;
        error_monitor = -14'sd456;
        wait_cycles(2);
        bus_write(REG_KP, 32'd0);
        bus_write(REG_KI, 32'd0);
        bus_write(REG_CAPTURE_LOCK_POINT, 32'd1);
        check("CAPTURE_LOCK_POINT latches current ERROR_SETPOINT", error_setpoint == -14'sd456);
        check("CAPTURE_LOCK_POINT latches current LOCK_BIAS", lock_bias == 14'sd2345);
        check("CAPTURE_LOCK_POINT forces KP=0", kp == 14'sd0);
        check("CAPTURE_LOCK_POINT forces KI=0", ki == 14'sd0);
        check("CAPTURE_LOCK_POINT switches to P_LOCK", mode == 32'd3);
        check("CAPTURE_LOCK_POINT keeps enable asserted", enable == 1'b1);
        bus_read(REG_ERROR_SETPOINT, read_data);
        check("read captured ERROR_SETPOINT", $signed(read_data) == -32'sd456);
        bus_read(REG_LOCK_BIAS, read_data);
        check("read captured LOCK_BIAS", $signed(read_data) == 32'sd2345);

        saturated = 1'b1;
        bus_read(REG_STATUS, read_data);
        check("STATUS bit0 reflects enabled scan", read_data[0] == 1'b1);
        check("STATUS bit1 reflects saturation", read_data[1] == 1'b1);

        saturated = 1'b0;
        bus_write(REG_ENABLE, 32'd0);
        bus_read(REG_STATUS, read_data);
        check("STATUS bit0 clears when disabled", read_data[0] == 1'b0);
        check("STATUS bit1 clears when not saturated", read_data[1] == 1'b0);

        bus_write(REG_ACQ_COMMAND, 32'h2);
        check("ABORT command forces MODE SAFE", mode == 32'd0);
        check("ABORT command clears ENABLE", enable == 1'b0);
        bus_read(REG_ACQ_COMMAND, read_data);
        check("ACQ_COMMAND is write-only and reads zero", read_data == 32'd0);

        bus_write(REG_MODE, 32'd1);
        bus_write(REG_ENABLE, 32'd1);
        wait_cycles(2);
        bus_read(REG_ACQ_STATE, read_data);
        check("acquisition state follows enabled SCAN", read_data[2:0] == 3'd1);

        bus_write(REG_TARGET_OUT2_SHADOW, 32'd100);
        bus_read(REG_CONFIG_VALIDATION, read_data);
        check("partial shadow write is incomplete", read_data[0] == 1'b0);
        check("partial shadow written mask records target only", read_data[14:8] == 7'b0000001);
        bus_write(REG_ACQ_COMMAND, 32'h1);
        wait_cycles(3);
        bus_read(REG_ACQ_STATE, read_data);
        check("invalid ARM remains in SCAN", read_data[2:0] == 3'd1);
        bus_read(REG_EVENT_INFO, read_data);
        check("invalid ARM reports CONFIG_REJECTED", read_data[3:1] == 3'd4);
        bus_read(REG_FAULT_DETAIL, read_data);
        check("invalid ARM reports missing-field reject bit", read_data[0] == 1'b1);

        bus_write(REG_ACQ_COMMAND, 32'h4);
        bus_write(REG_ACQ_COMMAND, 32'h3);
        bus_read(REG_EVENT_INFO, read_data);
        check("multi-command is rejected atomically", read_data[3:1] == 3'd5);
        bus_read(REG_ACQ_STATE, read_data);
        check("multi-command executes no partial command", read_data[2:0] == 3'd1);
        bus_write(REG_ACQ_COMMAND, 32'h4);

        bus_write(REG_TARGET_OUT2_SHADOW, 32'd100);
        bus_write(REG_TARGET_ERROR_SETPOINT_SHADOW, 32'd0);
        bus_write(REG_TARGET_WINDOW_SHADOW, 32'd10);
        bus_write(REG_TARGET_REQUIREMENTS_SHADOW, 32'h0000_0005);
        bus_write(REG_CORRECTION_LIMIT_SHADOW, 32'd8);
        bus_write(REG_ABSOLUTE_LIMIT_SHADOW, 32'd200);
        bus_write(REG_CONFIG_GENERATION_SHADOW, 32'd42);
        bus_read(REG_CONFIG_VALIDATION, read_data);
        check("complete shadow config has all written bits", read_data[14:8] == 7'h7F);
        check("complete shadow config is ARM-valid", read_data[7] == 1'b1);
        check("CONFIG_VALIDATION marks host PZT range responsibility", read_data[15] == 1'b1);

        out2_monitor = 14'sd95;
        error_monitor = -14'sd10;
        wait_cycles(2);
        arm_and_check_fixed_pipeline();
        bus_read(REG_ACQ_STATE, read_data);
        check("valid ARM enters ARMED", read_data[2:0] == 3'd2);
        check("valid ARM clears Kp", kp == 14'sd0);
        check("valid ARM clears Ki", ki == 14'sd0);
        bus_read(REG_ACTIVE_TARGET_OUT2, read_data);
        check("ARM snapshots active target", $signed(read_data) == 32'sd100);
        bus_read(REG_ACTIVE_ERROR_SETPOINT, read_data);
        check("ARM snapshots active error setpoint", $signed(read_data) == 32'sd0);
        bus_read(REG_ACTIVE_WINDOW, read_data);
        check("ARM snapshots active window", read_data == 32'd10);
        bus_read(REG_ACTIVE_REQUIREMENTS, read_data);
        check("ARM snapshots independent direction requirements", read_data == 32'h5);
        bus_read(REG_ACTIVE_CORRECTION_LIMIT, read_data);
        check("ARM snapshots correction limit", read_data == 32'd8);
        bus_read(REG_ACTIVE_ABSOLUTE_LIMIT, read_data);
        check("ARM snapshots absolute limit", read_data == 32'd200);

        bus_write(REG_ACQ_COMMAND, 32'h1);
        bus_read(REG_ACQ_STATE, read_data);
        check("repeated ARM remains ARMED", read_data[2:0] == 3'd2);
        bus_read(REG_EVENT_INFO, read_data);
        check("repeated ARM reports CONFIG_REJECTED", read_data[3:1] == 3'd4);
        bus_read(REG_FAULT_DETAIL, read_data);
        check("repeated ARM reports state reject bit", read_data[6] == 1'b1);
        bus_write(REG_ACQ_COMMAND, 32'h4);

        bus_write(REG_TARGET_OUT2_SHADOW, 32'd150);
        bus_read(REG_ACTIVE_TARGET_OUT2, read_data);
        check("shadow writes after ARM do not alter active target", $signed(read_data) == 32'sd100);

        out2_monitor = 14'sd96;
        error_monitor = -14'sd5;
        wait_cycles(1);
        check("ARMED does not trigger without crossing", mode == 32'd1);
        out2_monitor = 14'sd100;
        error_monitor = 14'sd1;
        wait_cycles(3);
        check("matching direction/window/crossing atomically enters P_LOCK", mode == 32'd3);
        check("trigger captures actual OUT2 as LOCK_BIAS", lock_bias == 14'sd100);
        check("trigger applies active setpoint rather than current error", error_setpoint == 14'sd0);
        check("trigger applies active correction limit", lock_correction_limit == 14'sd8);
        check("trigger applies active absolute limit", lock_limit == 14'sd200);
        wait_cycles(2);
        bus_read(REG_ACQ_STATE, read_data);
        check("trigger commit reaches P_LOCK_KP0", read_data[2:0] == 3'd4);
        check("P_LOCK_KP0 readback marks lock active", read_data[10] == 1'b1);
        bus_read(REG_EVENT_OUT2, read_data);
        check("trigger event records actual OUT2", $signed(read_data) == 32'sd100);
        bus_read(REG_EVENT_ERROR, read_data);
        check("trigger event records actual ERROR", $signed(read_data) == 32'sd1);
        bus_read(REG_EVENT_CONFIG_GENERATION, read_data);
        check("trigger event records active generation", read_data == 32'd42);
        bus_read(REG_EVENT_INFO, read_data);
        check("trigger event is sticky and typed TRIGGERED", read_data[0] && (read_data[3:1] == 3'd2));
        check("trigger event records RISING scan direction", read_data[5:4] == 2'd1);
        check("trigger event records NEG_TO_POS crossing", read_data[7:6] == 2'd1);
        bus_read(REG_EVENT_TIMESTAMP_LO, read_data);
        check("trigger event timestamp is nonzero", read_data != 32'd0);
        bus_read(REG_EVENT_SEQUENCE, read_data);
        check("event sequence advances monotonically", read_data >= 32'd4);

        bus_write(REG_ACQ_COMMAND, 32'h4);
        bus_read(REG_ACQ_STATE, read_data);
        check("CLEAR_EVENT clears sticky event only", (read_data[8] == 1'b0) && (read_data[2:0] == 3'd4));
        check("CLEAR_EVENT preserves P_LOCK mode", mode == 32'd3);

        bus_write(REG_KP, 32'd4);
        wait_cycles(2);
        bus_read(REG_ACQ_STATE, read_data);
        check("explicit nonzero Kp enters P_LOCK_ACTIVE", read_data[2:0] == 3'd5);
        check("explicit Apply P writes requested Kp", kp == 14'sd4);

        bus_write(REG_ACQ_COMMAND, 32'h2);
        check("ABORT from P_LOCK_ACTIVE returns MODE SAFE", mode == 32'd0);
        check("ABORT from P_LOCK_ACTIVE clears Kp", kp == 14'sd0);

        bus_write(REG_MODE, 32'd1);
        bus_write(REG_ENABLE, 32'd1);
        wait_cycles(2);
        bus_write(REG_TARGET_OUT2_SHADOW, -32'sd100);
        bus_write(REG_TARGET_ERROR_SETPOINT_SHADOW, -32'sd7);
        bus_write(REG_TARGET_WINDOW_SHADOW, 32'd10);
        bus_write(REG_TARGET_REQUIREMENTS_SHADOW, 32'h0000_000A);
        bus_write(REG_CORRECTION_LIMIT_SHADOW, 32'd8);
        bus_write(REG_ABSOLUTE_LIMIT_SHADOW, 32'd200);
        bus_write(REG_CONFIG_GENERATION_SHADOW, 32'd43);
        bus_read(REG_CONFIG_VALIDATION, read_data);
        check("negative target and setpoint are valid signed 14-bit fields", read_data[7] == 1'b1);
        out2_monitor = -14'sd90;
        error_monitor = 14'sd5;
        bus_write(REG_ACQ_COMMAND, 32'h1);
        wait_cycles(3);
        bus_read(REG_ACTIVE_TARGET_OUT2, read_data);
        check("ARM snapshots negative active target with sign extension", $signed(read_data) == -32'sd100);
        bus_read(REG_ACTIVE_ERROR_SETPOINT, read_data);
        check("ARM snapshots negative active error setpoint with sign extension", $signed(read_data) == -32'sd7);
        check("ARM precomputes signed negative target low boundary",
              dut.i_deterministic_lock_acquisition.active_target_low_q == -16'sd110);
        check("ARM precomputes signed negative target high boundary",
              dut.i_deterministic_lock_acquisition.active_target_high_q == -16'sd90);
        bus_write(REG_CONFIG_GENERATION_SHADOW, 32'd99);
        bus_write(REG_ACQ_COMMAND, 32'h2);
        bus_read(REG_EVENT_CONFIG_GENERATION, read_data);
        check("ABORT event retains active generation after shadow mutation", read_data == 32'd43);

        bus_write_during_forced_acquisition(REG_TARGET_OUT2_SHADOW, 32'd321, capture_pulse_seen);
        bus_read(REG_TARGET_OUT2_SHADOW, read_data);
        check("shadow bus write is independent of acquisition controls", read_data == 32'd321);

        bus_write_during_forced_acquisition(REG_SCAN_OFFSET, 32'd7011, capture_pulse_seen);
        check("scan bus write is independent of acquisition controls", scan_offset == 14'sd7011);

        bus_write_during_forced_acquisition(REG_CAPTURE_DECIMATION, 32'd77, capture_pulse_seen);
        check("capture config write is independent of acquisition controls",
              capture_decimation == 32'd77);

        bus_write_during_forced_acquisition(REG_CAPTURE_CTRL, 32'd1, capture_pulse_seen);
        check("capture start pulse is independent of acquisition controls", capture_pulse_seen);
        wait_cycles(1);
        check("capture start remains a one-cycle pulse", capture_start == 1'b0);

        $display("SUMMARY tb_custom_register_bank_basic tests=%0d pass=%0d fail=%0d", tests, pass_count, fail_count);
        if (fail_count != 0) begin
            $finish(1);
        end
        $finish;
    end

endmodule
