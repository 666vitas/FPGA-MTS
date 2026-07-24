`timescale 1ns/1ps

module tb_deterministic_lock_acquisition;

    localparam logic [5:0] REG_MODE = 6'h02;
    localparam logic [5:0] REG_ENABLE = 6'h03;
    localparam logic [5:0] REG_KP = 6'h0C;
    localparam logic [5:0] REG_TARGET_OUT2_SHADOW = 6'h18;
    localparam logic [5:0] REG_TARGET_ERROR_SETPOINT_SHADOW = 6'h19;
    localparam logic [5:0] REG_TARGET_WINDOW_SHADOW = 6'h1A;
    localparam logic [5:0] REG_TARGET_REQUIREMENTS_SHADOW = 6'h1B;
    localparam logic [5:0] REG_CORRECTION_LIMIT_SHADOW = 6'h1C;
    localparam logic [5:0] REG_ABSOLUTE_LIMIT_SHADOW = 6'h1D;
    localparam logic [5:0] REG_CONFIG_GENERATION_SHADOW = 6'h1E;
    localparam logic [5:0] REG_CONFIG_VALIDATION = 6'h1F;
    localparam logic [5:0] REG_ACQ_COMMAND = 6'h29;
    localparam logic [5:0] REG_ACQ_STATE = 6'h2A;
    localparam logic [5:0] REG_EVENT_OUT2 = 6'h2C;
    localparam logic [5:0] REG_EVENT_ERROR = 6'h2D;
    localparam logic [5:0] REG_EVENT_CONFIG_GENERATION = 6'h2E;
    localparam logic [5:0] REG_EVENT_INFO = 6'h2F;

    logic clk = 1'b0;
    always #5 clk = ~clk;

    logic rstn;
    logic signed [13:0] laser_error;
    logic signed [13:0] scan_command;
    logic scan_saturated;
    logic controller_saturated;
    logic out2_saturated;
    logic signed [13:0] selected_out2;

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

    logic signed [13:0] out2_before_candidate;
    logic signed [13:0] out2_before_trigger;
    logic signed [13:0] out2_on_trigger_edge;
    logic signed [13:0] captured_bias_on_rising_trigger;
    logic signed [13:0] first_kp0_out2;
    logic signed [13:0] subsequent_kp0_out2;
    logic [31:0] read_data;
    int tests;
    int pass_count;
    int fail_count;

    sys_bus_if bus (.clk(clk), .rstn(rstn));

    assign out2_saturated = scan_saturated | controller_saturated;

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

    task automatic enter_scan(input logic signed [13:0] initial_scan);
        scan_command = initial_scan;
        bus_write(REG_MODE, 32'd1);
        bus_write(REG_ENABLE, 32'd1);
        wait_cycles(2);
    endtask

    task automatic preload_target(
        input logic signed [13:0] target,
        input logic [13:0] window,
        input logic [1:0] scan_direction,
        input logic [1:0] error_direction,
        input logic [31:0] generation
    );
        bus_write(REG_TARGET_OUT2_SHADOW, {{18{target[13]}}, target});
        bus_write(REG_TARGET_ERROR_SETPOINT_SHADOW, 32'd0);
        bus_write(REG_TARGET_WINDOW_SHADOW, {18'd0, window});
        bus_write(
            REG_TARGET_REQUIREMENTS_SHADOW,
            {27'd0, 1'b0, error_direction, scan_direction}
        );
        bus_write(REG_CORRECTION_LIMIT_SHADOW, 32'd8);
        bus_write(REG_ABSOLUTE_LIMIT_SHADOW, 32'd200);
        bus_write(REG_CONFIG_GENERATION_SHADOW, generation);
        bus_read(REG_CONFIG_VALIDATION, read_data);
        check("preloaded target validates before ARM", read_data[7] == 1'b1);
    endtask

    custom_register_bank i_register_bank (
        .clk_i(clk),
        .rstn_i(rstn),
        .out2_monitor_i(selected_out2),
        .error_monitor_i(laser_error),
        .control_monitor_i(selected_out2),
        .saturated_i(out2_saturated),
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
        .lock_error_monitor_i(laser_error),
        .capture_data_ch1_i(14'sd0),
        .capture_data_ch2_i(14'sd0),
        .capture_data_ch3_i(14'sd0),
        .capture_data_ch4_i(14'sd0),
        .bus(bus)
    );

    out2_lock_controller i_controller (
        .clk_i(clk),
        .rstn_i(rstn),
        .enable_i(enable),
        .mode_i(mode),
        .scan_i(scan_command),
        .scan_saturated_i(scan_saturated),
        .hold_value_i(hold_value),
        .error_i(laser_error),
        .kp_i(kp),
        .ki_i(ki),
        .polarity_i(polarity),
        .lock_bias_i(lock_bias),
        .lock_limit_i(lock_limit),
        .lock_correction_limit_i(correction_limit),
        .integral_reset_i(integral_reset),
        .acq_hold_i(acq_hold),
        .acq_abort_i(acq_abort),
        .acq_fault_i(acq_fault),
        .control_o(selected_out2),
        .saturated_o(controller_saturated)
    );

    initial begin
        rstn = 1'b0;
        laser_error = 14'sd0;
        scan_command = 14'sd0;
        scan_saturated = 1'b0;
        bus.addr = 32'd0;
        bus.wdata = 32'd0;
        bus.wen = 1'b0;
        bus.ren = 1'b0;
        wait_cycles(4);
        rstn = 1'b1;
        wait_cycles(2);

        enter_scan(14'sd80);
        check("integrated SCAN drives selected_out2", selected_out2 == 14'sd80);
        scan_command = 14'sd90;
        wait_cycles(2);
        bus_read(REG_ACQ_STATE, read_data);
        check("selected_out2 delta reports RISING", read_data[15:14] == 2'd1);
        scan_command = 14'sd90;
        wait_cycles(2);
        bus_read(REG_ACQ_STATE, read_data);
        check("equal selected_out2 samples retain RISING", read_data[15:14] == 2'd1);
        scan_command = 14'sd89;
        wait_cycles(2);
        bus_read(REG_ACQ_STATE, read_data);
        check("triangle reversal reports FALLING", read_data[15:14] == 2'd2);

        enter_scan(14'sd80);
        laser_error = -14'sd10;
        preload_target(14'sd100, 14'd5, 2'd2, 2'd1, 32'd5);
        bus_write(REG_ACQ_COMMAND, 32'h1);
        wait_cycles(4);
        scan_command = 14'sd100;
        laser_error = -14'sd1;
        wait_cycles(2);
        @(negedge clk);
        laser_error = 14'sd1;
        #1;
        check("matching window/crossing does not trigger with wrong scan direction", !acq_trigger);
        @(posedge clk);
        #1;
        check("wrong scan direction leaves acquisition ARMED", mode == 32'd1);
        bus_write(REG_ACQ_COMMAND, 32'h2);

        enter_scan(14'sd80);
        laser_error = -14'sd10;
        preload_target(14'sd100, 14'd2, 2'd1, 2'd1, 32'd6);
        bus_write(REG_ACQ_COMMAND, 32'h1);
        wait_cycles(4);
        scan_command = 14'sd99;
        laser_error = -14'sd1;
        wait_cycles(2);
        @(negedge clk);
        laser_error = 14'sd1;
        scan_command = 14'sd103;
        #1;
        check("inside-window raw decision remains internal", !acq_trigger);
        @(posedge clk);
        #1;
        check("raw decision enters registered hold before commit", acq_hold && !acq_trigger);
        @(posedge clk);
        #1;
        check("hold sample outside target window cancels trigger commit", !acq_trigger && !acq_hold);
        check("outside-window hold sample leaves acquisition ARMED", mode == 32'd1);
        bus_write(REG_ACQ_COMMAND, 32'h2);

        enter_scan(14'sd80);
        laser_error = -14'sd10;
        wait_cycles(2);
        preload_target(14'sd100, 14'd6, 2'd1, 2'd1, 32'd7);
        bus_write(REG_ACQ_COMMAND, 32'h1);
        wait_cycles(4);
        bus_read(REG_ACQ_STATE, read_data);
        check("rising transaction enters ARMED", read_data[2:0] == 3'd2);
        check("ARM precomputes positive target low boundary",
              i_register_bank.i_deterministic_lock_acquisition.active_target_low_q == 16'sd94);
        check("ARM precomputes positive target high boundary",
              i_register_bank.i_deterministic_lock_acquisition.active_target_high_q == 16'sd106);

        scan_command = 14'sd90;
        laser_error = -14'sd5;
        wait_cycles(2);
        scan_command = 14'sd105;
        laser_error = -14'sd1;
        wait_cycles(2);
        out2_before_candidate = selected_out2;
        @(negedge clk);
        laser_error = 14'sd1;
        scan_command = 14'sd106;
        #1;
        check("raw rising conditions do not escape as a combinational trigger", acq_trigger == 1'b0);
        @(posedge clk);
        #1;
        check("rising decision is registered before trigger commit", acq_trigger == 1'b0);
        out2_before_trigger = selected_out2;
        check("update_div=1 model permits only the final normal scan step before hold",
              out2_before_trigger == (out2_before_candidate + 14'sd1));
        scan_command = 14'sd107;
        laser_error = 14'sd2;
        @(posedge clk);
        #1;
        check("registered rising trigger is a commit pulse", acq_trigger == 1'b1);
        out2_on_trigger_edge = selected_out2;
        check("trigger edge holds selected_out2 exactly", out2_on_trigger_edge == out2_before_trigger);
        scan_command = 14'sd108;
        @(posedge clk);
        #1;
        check("registered rising trigger is exactly one cycle", acq_trigger == 1'b0);
        check("captured lock bias equals trigger-edge OUT2", lock_bias == out2_before_trigger);
        captured_bias_on_rising_trigger = lock_bias;
        check("cycle-by-cycle scan changes remain held through trigger commit",
              selected_out2 == out2_before_trigger);
        first_kp0_out2 = selected_out2;
        @(posedge clk);
        #1;
        subsequent_kp0_out2 = selected_out2;
        check("first P_LOCK_KP0 output equals trigger OUT2", first_kp0_out2 == out2_before_trigger);
        check("subsequent P_LOCK_KP0 output remains exact", subsequent_kp0_out2 == out2_before_trigger);
        check(
            "bumpless digital jump is exactly zero counts",
            (out2_on_trigger_edge - out2_before_trigger == 14'sd0) &&
            (first_kp0_out2 - out2_before_trigger == 14'sd0) &&
            (subsequent_kp0_out2 - out2_before_trigger == 14'sd0)
        );
        bus_read(REG_EVENT_OUT2, read_data);
        check("trigger event uses the actual held OUT2 sample",
              $signed(read_data) == $signed(out2_before_trigger));
        bus_read(REG_EVENT_ERROR, read_data);
        check("trigger event uses the actual trigger-edge ERROR sample",
              $signed(read_data) == 32'sd2);
        bus_read(REG_EVENT_CONFIG_GENERATION, read_data);
        check("trigger event retains active generation", read_data == 32'd7);

        bus_write(REG_ACQ_COMMAND, 32'h2);
        enter_scan(14'sd120);
        laser_error = 14'sd10;
        preload_target(14'sd100, 14'd5, 2'd2, 2'd2, 32'd8);
        bus_write(REG_ACQ_COMMAND, 32'h1);
        wait_cycles(4);
        scan_command = 14'sd110;
        laser_error = 14'sd5;
        wait_cycles(2);
        scan_command = 14'sd95;
        laser_error = 14'sd1;
        wait_cycles(2);
        @(negedge clk);
        laser_error = -14'sd1;
        #1;
        check("falling raw conditions do not assert combinational trigger", acq_trigger == 1'b0);
        @(posedge clk);
        #1;
        check("falling decision waits for registered commit", acq_trigger == 1'b0);
        scan_command = 14'sd99;
        @(posedge clk);
        #1;
        check("falling POS_TO_NEG transaction asserts registered trigger", acq_trigger == 1'b1);
        @(posedge clk);
        #1;
        check("falling low-window boundary captures actual OUT2", lock_bias == 14'sd95);
        bus_read(REG_EVENT_INFO, read_data);
        check("falling event records FALLING direction", read_data[5:4] == 2'd2);
        check("falling event records POS_TO_NEG crossing", read_data[7:6] == 2'd2);

        bus_write(REG_ACQ_COMMAND, 32'h2);
        enter_scan(14'sd80);
        laser_error = -14'sd10;
        preload_target(14'sd100, 14'd5, 2'd1, 2'd1, 32'd9);
        bus_write(REG_ACQ_COMMAND, 32'h1);
        wait_cycles(4);
        scan_command = 14'sd100;
        laser_error = -14'sd1;
        wait_cycles(2);
        @(negedge clk);
        laser_error = 14'sd1;
        bus.addr = {24'd0, REG_ACQ_COMMAND, 2'b00};
        bus.wdata = 32'h2;
        bus.wen = 1'b1;
        #1;
        check("raw ABORT write does not bypass registered mailbox", !acq_trigger && !acq_abort);
        @(posedge clk);
        #1;
        check("registered ABORT pulse suppresses pending trigger commit", !acq_trigger && acq_abort);
        @(negedge clk);
        bus.wen = 1'b0;
        bus.addr = 32'd0;
        bus.wdata = 32'd0;
        @(posedge clk);
        #1;
        check("registered ABORT drives exact SAFE output one cycle later", selected_out2 == 14'sd0);
        check("registered ABORT remains higher priority than pending trigger", mode == 32'd0);
        wait_cycles(1);
        bus_read(REG_EVENT_INFO, read_data);
        check("registered ABORT records ABORTED rather than TRIGGERED", read_data[3:1] == 3'd3);

        enter_scan(14'sd80);
        laser_error = -14'sd10;
        preload_target(14'sd100, 14'd5, 2'd1, 2'd1, 32'd10);
        bus_write(REG_ACQ_COMMAND, 32'h1);
        wait_cycles(4);
        scan_command = 14'sd100;
        laser_error = -14'sd1;
        wait_cycles(2);
        @(negedge clk);
        laser_error = 14'sd1;
        @(posedge clk);
        #1;
        check("fault test creates a pending registered decision", acq_hold && !acq_trigger);
        scan_saturated = 1'b1;
        wait_cycles(2);
        check("FAULT suppresses a pending trigger commit", acq_trigger == 1'b0);
        check("ARMED saturation drives SAFE output", selected_out2 == 14'sd0);
        check("ARMED saturation forces MODE SAFE", mode == 32'd0);
        scan_saturated = 1'b0;
        bus_read(REG_ACQ_STATE, read_data);
        check("ARMED saturation enters sticky FAULT", read_data[2:0] == 3'd6);
        bus_read(REG_EVENT_INFO, read_data);
        check("runtime safety violation records FAULT event", read_data[3:1] == 3'd6);

        $display(
            "BUMPLESS out2_before=%0d out2_trigger=%0d captured_bias=%0d first_kp0=%0d subsequent_kp0=%0d digital_jump=%0d",
            out2_before_trigger,
            out2_on_trigger_edge,
            captured_bias_on_rising_trigger,
            first_kp0_out2,
            subsequent_kp0_out2,
            first_kp0_out2 - out2_before_trigger
        );
        $display(
            "SUMMARY tb_deterministic_lock_acquisition tests=%0d pass=%0d fail=%0d",
            tests,
            pass_count,
            fail_count
        );
        if (fail_count != 0)
            $finish(1);
        $finish;
    end

endmodule
