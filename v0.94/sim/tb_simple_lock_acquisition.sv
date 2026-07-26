`timescale 1ns/1ps

module tb_simple_lock_acquisition;

    localparam logic [5:0] REG_VERSION = 6'h01;
    localparam logic [5:0] REG_MODE = 6'h02;
    localparam logic [5:0] REG_ENABLE = 6'h03;
    localparam logic [5:0] REG_KP = 6'h0C;
    localparam logic [5:0] REG_POLARITY = 6'h0D;
    localparam logic [5:0] REG_TARGET_OUT2 = 6'h18;
    localparam logic [5:0] REG_TARGET_ERROR = 6'h19;
    localparam logic [5:0] REG_TARGET_WINDOW = 6'h1A;
    localparam logic [5:0] REG_TARGET_REQUIREMENTS = 6'h1B;
    localparam logic [5:0] REG_CORRECTION_LIMIT = 6'h1C;
    localparam logic [5:0] REG_ABSOLUTE_LIMIT = 6'h1D;
    localparam logic [5:0] REG_GENERATION = 6'h1E;
    localparam logic [5:0] REG_CONFIG_VALIDATION = 6'h1F;
    localparam logic [5:0] REG_ACQ_COMMAND = 6'h29;
    localparam logic [5:0] REG_ACQ_STATE = 6'h2A;
    localparam logic [5:0] REG_EVENT_OUT2 = 6'h2C;
    localparam logic [5:0] REG_EVENT_ERROR = 6'h2D;
    localparam logic [5:0] REG_EVENT_GENERATION = 6'h2E;
    localparam logic [5:0] REG_EVENT_INFO = 6'h2F;
    localparam logic [5:0] REG_EVENT_TIMESTAMP_LO = 6'h30;
    localparam logic [5:0] REG_EVENT_TIMESTAMP_HI = 6'h31;

    localparam logic [1:0] SCAN_DIR_RISING = 2'd1;
    localparam logic [1:0] SCAN_DIR_FALLING = 2'd2;
    localparam logic [1:0] ERROR_DIR_NEG_TO_POS = 2'd1;
    localparam logic [1:0] ERROR_DIR_POS_TO_NEG = 2'd2;

    logic clk = 1'b0;
    always #5 clk = ~clk;

    logic rstn;
    logic signed [13:0] out2_monitor;
    logic signed [13:0] error_monitor;
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
    logic signed [13:0] correction_limit;
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
    logic [31:0] read_data;
    int tests;
    int pass_count;
    int fail_count;

    sys_bus_if bus (.clk(clk), .rstn(rstn));

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

    task automatic preload_target(
        input logic signed [13:0] target,
        input logic [13:0] window,
        input logic [1:0] scan_direction,
        input logic [1:0] crossing_direction,
        input logic signed [13:0] setpoint,
        input logic [31:0] generation
    );
        bus_write(REG_TARGET_OUT2, {{18{target[13]}}, target});
        bus_write(REG_TARGET_ERROR, {{18{setpoint[13]}}, setpoint});
        bus_write(REG_TARGET_WINDOW, {18'd0, window});
        bus_write(
            REG_TARGET_REQUIREMENTS,
            {27'd0, 1'b0, crossing_direction, scan_direction}
        );
        bus_write(REG_CORRECTION_LIMIT, 32'd12);
        bus_write(REG_ABSOLUTE_LIMIT, 32'd300);
        bus_write(REG_GENERATION, generation);
    endtask

    task automatic enter_scan(input logic signed [13:0] initial_out2);
        out2_monitor = initial_out2;
        error_monitor = 14'sd0;
        bus_write(REG_MODE, 32'd1);
        bus_write(REG_ENABLE, 32'd1);
        wait_cycles(3);
    endtask

    task automatic wait_for_trigger;
        int count;
        count = 0;
        while (!acq_trigger && count < 16) begin
            @(posedge clk);
            #1;
            count++;
        end
        check("qualified realtime crossing produces registered trigger", acq_trigger);
    endtask

    custom_register_bank #(
        .LOCK_ACQ_IMPL(1)
    ) dut (
        .clk_i(clk),
        .rstn_i(rstn),
        .out2_monitor_i(out2_monitor),
        .error_monitor_i(error_monitor),
        .control_monitor_i(out2_monitor),
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
        .lock_correction_limit_o(correction_limit),
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
        .capture_busy_i(1'b0),
        .capture_done_i(1'b0),
        .lock_error_monitor_i(error_monitor),
        .capture_data_ch1_i(14'sd0),
        .capture_data_ch2_i(14'sd0),
        .capture_data_ch3_i(14'sd0),
        .capture_data_ch4_i(14'sd0),
        .bus(bus)
    );

    initial begin
        tests = 0;
        pass_count = 0;
        fail_count = 0;
        rstn = 1'b0;
        out2_monitor = 14'sd0;
        error_monitor = 14'sd0;
        saturated = 1'b0;
        bus.addr = 32'd0;
        bus.wdata = 32'd0;
        bus.wen = 1'b0;
        bus.ren = 1'b0;
        wait_cycles(4);
        rstn = 1'b1;
        wait_cycles(2);

        bus_read(REG_VERSION, read_data);
        check("SIMPLE build reports VERSION 0x00030200", read_data == 32'h00030200);

        preload_target(
            14'sd100, 14'd5, SCAN_DIR_RISING, ERROR_DIR_NEG_TO_POS,
            -14'sd3, 32'd17
        );
        enter_scan(14'sd80);
        out2_monitor = 14'sd90;
        wait_cycles(2);
        out2_monitor = 14'sd100;
        error_monitor = 14'sd20;
        wait_cycles(2);
        check(
            "without request target window and ERROR level do not trigger",
            !acq_trigger && mode == 32'd1
        );

        bus_write(REG_ENABLE, 32'd0);
        bus_write(REG_MODE, 32'd0);
        bus_write(REG_ACQ_COMMAND, 32'd1);
        wait_cycles(3);
        bus_read(REG_ACQ_STATE, read_data);
        check("non-SCAN request is not accepted", read_data[2:0] == 3'd0);

        enter_scan(14'sd80);
        saturated = 1'b1;
        bus_write(REG_ACQ_COMMAND, 32'd1);
        wait_cycles(3);
        bus_read(REG_ACQ_STATE, read_data);
        check("saturated request is not accepted", read_data[2:0] != 3'd2);
        saturated = 1'b0;

        bus_write(REG_ACQ_COMMAND, 32'd2);
        enter_scan(14'sd120);
        preload_target(
            14'sd100, 14'd5, SCAN_DIR_RISING, ERROR_DIR_NEG_TO_POS,
            14'sd0, 32'd18
        );
        out2_monitor = 14'sd110;
        wait_cycles(2);
        bus_write(REG_ACQ_COMMAND, 32'd1);
        wait_cycles(3);
        error_monitor = -14'sd10;
        out2_monitor = 14'sd100;
        wait_cycles(2);
        error_monitor = 14'sd10;
        wait_cycles(3);
        check(
            "wrong scan direction blocks a valid ERROR crossing",
            !acq_trigger && mode == 32'd1
        );

        bus_write(REG_ACQ_COMMAND, 32'd2);
        check("abort returns fast control to SAFE", mode == 32'd0 && !enable);

        // Realtime NEG_TO_POS acquisition. Entering the guard on the destination
        // side alone must not trigger; the source side must first be observed.
        enter_scan(14'sd80);
        preload_target(
            14'sd100, 14'd5, SCAN_DIR_RISING, ERROR_DIR_NEG_TO_POS,
            -14'sd7, 32'd19
        );
        out2_monitor = 14'sd90;
        wait_cycles(2);
        bus_write(REG_KP, 32'd0);
        bus_write(REG_POLARITY, 32'd1);
        bus_write(REG_ACQ_COMMAND, 32'd1);
        wait_cycles(3);
        bus_read(REG_ACQ_STATE, read_data);
        check("valid realtime request enters ARMED", read_data[9] && (read_data[2:0] == 3'd2));
        bus_read(REG_CONFIG_VALIDATION, read_data);
        check("config advertises realtime crossing capability", read_data[16]);

        out2_monitor = 14'sd96;
        error_monitor = 14'sd2;
        wait_cycles(3);
        check(
            "guard-window hit without source-side history does not trigger",
            !acq_trigger && mode == 32'd1
        );

        error_monitor = -14'sd20;
        wait_cycles(2);
        bus_read(REG_ACQ_STATE, read_data);
        check("source-side hysteresis state is visible", read_data[16]);

        error_monitor = -14'sd8;
        wait_cycles(2);
        check("hysteresis deadband does not trigger", !acq_trigger && mode == 32'd1);

        out2_monitor = 14'sd100;
        error_monitor = 14'sd0;
        wait_for_trigger();
        check("trigger captures current OUT2 sample", dut.trigger_out2_sample_w == 14'sd100);
        check("trigger captures current ERROR sample", dut.trigger_error_sample_w == 14'sd0);
        check("trigger is held for one cycle", acq_hold);
        @(posedge clk);
        #1;
        check("registered trigger is exactly one cycle", !acq_trigger);
        check("trigger atomically enters P_LOCK", mode == 32'd3 && enable);
        check("Kp=0 remains debug no-feedback setting", kp == 14'sd0);
        check(
            "atomic transaction captures bias/setpoint/limits",
            (lock_bias == 14'sd100) &&
            (error_setpoint == -14'sd7) &&
            (correction_limit == 14'sd12) &&
            (lock_limit == 14'sd300)
        );
        bus_read(REG_EVENT_OUT2, read_data);
        check("trigger readback contains OUT2", $signed(read_data) == 32'sd100);
        bus_read(REG_EVENT_ERROR, read_data);
        check("trigger readback contains ERROR", $signed(read_data) == 32'sd0);
        bus_read(REG_EVENT_GENERATION, read_data);
        check("trigger readback contains generation", read_data == 32'd19);
        bus_read(REG_EVENT_INFO, read_data);
        check("event records rising scan direction", read_data[5:4] == SCAN_DIR_RISING);
        check(
            "event records NEG_TO_POS ERROR crossing direction",
            read_data[7:6] == ERROR_DIR_NEG_TO_POS
        );
        bus_read(REG_EVENT_TIMESTAMP_LO, read_data);
        check("unsupported SIMPLE timestamp low is deterministic zero", read_data == 32'd0);
        bus_read(REG_EVENT_TIMESTAMP_HI, read_data);
        check("unsupported SIMPLE timestamp high is deterministic zero", read_data == 32'd0);

        // POS_TO_NEG must reject the opposite crossing and then accept the
        // requested source-to-destination traversal.
        bus_write(REG_ACQ_COMMAND, 32'd2);
        enter_scan(14'sd80);
        preload_target(
            14'sd100, 14'd5, SCAN_DIR_RISING, ERROR_DIR_POS_TO_NEG,
            14'sd0, 32'd20
        );
        out2_monitor = 14'sd90;
        wait_cycles(2);
        bus_write(REG_KP, 32'd0);
        bus_write(REG_ACQ_COMMAND, 32'd1);
        wait_cycles(3);
        out2_monitor = 14'sd96;
        error_monitor = -14'sd10;
        wait_cycles(2);
        error_monitor = 14'sd10;
        wait_cycles(2);
        check(
            "opposite NEG_TO_POS traversal does not satisfy POS_TO_NEG request",
            !acq_trigger && mode == 32'd1
        );
        error_monitor = 14'sd1;
        wait_cycles(1);
        error_monitor = -14'sd10;
        out2_monitor = 14'sd100;
        wait_for_trigger();
        bus_read(REG_EVENT_INFO, read_data);
        check(
            "event records POS_TO_NEG ERROR crossing direction",
            read_data[7:6] == ERROR_DIR_POS_TO_NEG
        );

        // Preloaded nonzero Kp remains supported, but it is now entered only
        // after a qualified realtime ERROR crossing.
        bus_write(REG_ACQ_COMMAND, 32'd2);
        enter_scan(14'sd80);
        preload_target(
            14'sd100, 14'd4, SCAN_DIR_RISING, ERROR_DIR_NEG_TO_POS,
            14'sd2, 32'd21
        );
        out2_monitor = 14'sd90;
        wait_cycles(2);
        bus_write(REG_KP, 32'd4);
        bus_write(REG_ACQ_COMMAND, 32'd1);
        wait_cycles(3);
        out2_monitor = 14'sd97;
        error_monitor = -14'sd10;
        wait_cycles(2);
        out2_monitor = 14'sd100;
        error_monitor = 14'sd10;
        wait_for_trigger();
        @(posedge clk);
        #1;
        check(
            "preloaded Kp=4 is preserved after qualified realtime crossing",
            mode == 32'd3 && enable && (kp == 14'sd4)
        );
        bus_read(REG_ACQ_STATE, read_data);
        check("Kp=4 lock reports P_LOCK_ACTIVE", read_data[2:0] == 3'd5);

        check(
            "SIMPLE generate branch is elaborated",
            dut.g_lock_acq_simple.i_simple_lock_acquisition.state_q == 3'd5
        );

        $display(
            "SUMMARY tb_simple_lock_acquisition tests=%0d pass=%0d fail=%0d",
            tests,
            pass_count,
            fail_count
        );
        if (fail_count != 0)
            $finish(1);
        $finish;
    end

endmodule
