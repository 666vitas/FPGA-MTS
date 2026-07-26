`timescale 1ns/1ps

module tb_simple_lock_acquisition;
    localparam int ARM_PIPELINE_LATENCY = 6;
    localparam int CROSSING_PIPELINE_LATENCY = 4;
    localparam int EVENT_PIPELINE_LATENCY = 2;
    localparam int SUPERVISOR_PIPELINE_LATENCY = 3;
    localparam int HARD_FAULT_PIPELINE_LATENCY = 4;
    localparam int OBSERVE_LENGTH = 256;
    localparam logic [6:0] REG_VERSION = 7'h01;
    localparam logic [6:0] REG_MODE = 7'h02;
    localparam logic [6:0] REG_ENABLE = 7'h03;
    localparam logic [6:0] REG_POLARITY = 7'h0D;
    localparam logic [6:0] REG_LOCK_BIAS = 7'h0E;
    localparam logic [6:0] REG_TARGET_OUT2 = 7'h18;
    localparam logic [6:0] REG_TARGET_ERROR = 7'h19;
    localparam logic [6:0] REG_TARGET_WINDOW = 7'h1A;
    localparam logic [6:0] REG_TARGET_REQUIREMENTS = 7'h1B;
    localparam logic [6:0] REG_CORRECTION_LIMIT = 7'h1C;
    localparam logic [6:0] REG_ABSOLUTE_LIMIT = 7'h1D;
    localparam logic [6:0] REG_GENERATION = 7'h1E;
    localparam logic [6:0] REG_VALIDATION = 7'h1F;
    localparam logic [6:0] REG_ACQ_COMMAND = 7'h29;
    localparam logic [6:0] REG_ACQ_STATE = 7'h2A;
    localparam logic [6:0] REG_EVENT_OUT2 = 7'h2C;
    localparam logic [6:0] REG_EVENT_ERROR = 7'h2D;
    localparam logic [6:0] REG_EVENT_GENERATION = 7'h2E;
    localparam logic [6:0] REG_EVENT_INFO = 7'h2F;
    localparam logic [6:0] REG_L1_CAPABILITY = 7'h39;
    localparam logic [6:0] REG_CROSSING_CONFIG = 7'h3A;
    localparam logic [6:0] REG_KP_TARGET = 7'h3B;
    localparam logic [6:0] REG_KP_RAMP = 7'h3C;
    localparam logic [6:0] REG_TIMEOUT = 7'h3D;
    localparam logic [6:0] REG_SERVO_CONFIG = 7'h3E;
    localparam logic [6:0] REG_SUPERVISOR0 = 7'h3F;
    localparam logic [6:0] REG_SUPERVISOR1 = 7'h40;
    localparam logic [6:0] REG_EVENT_LOCK_ERROR = 7'h41;
    localparam logic [6:0] REG_VALIDATE_COUNT = 7'h42;
    localparam logic [6:0] REG_KP_EFFECTIVE = 7'h43;

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
    logic signed [13:0] kp_effective;
    logic polarity;
    logic signed [13:0] lock_bias;
    logic signed [13:0] lock_limit;
    logic signed [13:0] correction_limit;
    logic signed [13:0] error_setpoint;
    logic signed [13:0] ki;
    logic integral_reset;
    logic [15:0] servo_update_div;
    logic [13:0] out2_slew_limit;
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
    int i;

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

    task automatic bus_write(input logic [6:0] reg_addr, input logic [31:0] data);
        @(negedge clk);
        bus.addr = {23'd0, reg_addr, 2'b00};
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

    task automatic bus_read(input logic [6:0] reg_addr, output logic [31:0] data);
        @(negedge clk);
        bus.addr = {23'd0, reg_addr, 2'b00};
        bus.wen = 1'b0;
        bus.ren = 1'b1;
        @(posedge clk);
        @(negedge clk);
        bus.ren = 1'b0;
        data = bus.rdata;
        bus.addr = 32'd0;
        wait_cycles(1);
    endtask

    task automatic set_sample(
        input logic signed [13:0] out2_value,
        input logic signed [13:0] error_value
    );
        out2_monitor = out2_value;
        error_monitor = error_value;
        wait_cycles(1);
    endtask

    task automatic enter_scan;
        bus_write(REG_MODE, 32'd1);
        bus_write(REG_ENABLE, 32'd1);
        set_sample(14'sd80, 14'sd20);
        set_sample(14'sd81, 14'sd20);
    endtask

    task automatic preload(
        input logic [1:0] scan_dir,
        input logic [1:0] error_dir,
        input logic polarity_bit,
        input logic [31:0] generation
    );
        bus_write(REG_TARGET_OUT2, 32'd100);
        bus_write(REG_TARGET_ERROR, 32'd20);
        bus_write(REG_TARGET_WINDOW, 32'd10);
        bus_write(REG_TARGET_REQUIREMENTS,
                  {27'd0, polarity_bit, error_dir, scan_dir});
        bus_write(REG_CORRECTION_LIMIT, 32'd16);
        bus_write(REG_ABSOLUTE_LIMIT, 32'd300);
        bus_write(REG_GENERATION, generation);
    endtask

    task automatic rising_neg_to_pos_crossing;
        set_sample(14'sd91, 14'sd15);
        set_sample(14'sd92, 14'sd15);
        set_sample(14'sd93, 14'sd15);
        set_sample(14'sd94, 14'sd25);
        set_sample(14'sd95, 14'sd25);
        set_sample(14'sd96, 14'sd25);
    endtask

    custom_register_bank #(.LOCK_ACQ_IMPL(1)) dut (
        .clk_i(clk), .rstn_i(rstn),
        .out2_monitor_i(out2_monitor), .error_monitor_i(error_monitor),
        .control_monitor_i(out2_monitor), .saturated_i(saturated),
        .mode_o(mode), .enable_o(enable),
        .scan_offset_o(scan_offset), .scan_amp_o(scan_amp),
        .scan_step_o(scan_step), .scan_update_div_o(scan_update_div),
        .out2_limit_o(out2_limit), .hold_value_o(hold_value),
        .kp_o(kp), .kp_effective_o(kp_effective), .polarity_o(polarity),
        .lock_bias_o(lock_bias), .lock_limit_o(lock_limit),
        .lock_correction_limit_o(correction_limit),
        .error_setpoint_o(error_setpoint), .ki_o(ki),
        .integral_reset_o(integral_reset),
        .servo_update_div_o(servo_update_div),
        .out2_slew_limit_o(out2_slew_limit),
        .acq_trigger_o(acq_trigger), .acq_hold_o(acq_hold),
        .acq_abort_o(acq_abort), .acq_fault_o(acq_fault),
        .capture_start_o(capture_start),
        .capture_decimation_o(capture_decimation),
        .capture_length_o(capture_length),
        .capture_read_index_o(capture_read_index),
        .capture_busy_i(1'b0), .capture_done_i(1'b0),
        .lock_error_monitor_i(error_monitor),
        .capture_data_ch1_i(14'sd0), .capture_data_ch2_i(14'sd0),
        .capture_data_ch3_i(14'sd0), .capture_data_ch4_i(14'sd0),
        .bus(bus)
    );

    initial begin
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
        check("L1 preserves SIMPLE VERSION", read_data == 32'h00030200);
        bus_read(REG_L1_CAPABILITY, read_data);
        check("L1 capability distinguishes realtime crossing build",
              read_data == 32'h4C31_0001);

        bus_write(REG_CROSSING_CONFIG, {8'd0, 8'd3, 2'd0, 14'd4});
        bus_write(REG_KP_TARGET, 32'd4);
        bus_write(REG_KP_RAMP, {16'd1, 2'd0, 14'd1});
        bus_write(REG_TIMEOUT, 32'd5000);
        bus_write(REG_SERVO_CONFIG, {2'd0, 14'd8, 16'd1});
        bus_write(REG_SUPERVISOR0, {8'd0, 8'd3, 8'd2, 8'd8});
        bus_write(REG_SUPERVISOR1, {2'd0, 14'd12, 2'd0, 14'd8});

        enter_scan();
        preload(2'd1, 2'd1, 1'b1, 32'd11);
        bus_read(REG_VALIDATION, read_data);
        check("rising plus NEG_TO_POS requires polarity=1", read_data[16]);
        bus_write(REG_TARGET_REQUIREMENTS, {27'd0, 1'b0, 2'd1, 2'd1});
        bus_read(REG_VALIDATION, read_data);
        check("wrong polarity is rejected for positive local slope", !read_data[16]);
        bus_write(REG_TARGET_REQUIREMENTS, {27'd0, 1'b0, 2'd2, 2'd1});
        bus_read(REG_VALIDATION, read_data);
        check("rising plus POS_TO_NEG requires polarity=0", read_data[16]);
        bus_write(REG_TARGET_REQUIREMENTS, {27'd0, 1'b0, 2'd1, 2'd2});
        bus_read(REG_VALIDATION, read_data);
        check("falling plus NEG_TO_POS requires polarity=0", read_data[16]);
        bus_write(REG_TARGET_REQUIREMENTS, {27'd0, 1'b1, 2'd2, 2'd2});
        bus_read(REG_VALIDATION, read_data);
        check("falling plus POS_TO_NEG requires polarity=1", read_data[16]);

        // L1 uses a fixed 256-servo-tick observation window. A non-8 legacy
        // observe_shift value is retained in CSR but rejected at ARM.
        preload(2'd1, 2'd1, 1'b1, 32'd10);
        bus_write(REG_SUPERVISOR0, {8'd0, 8'd3, 8'd2, 8'd7});
        bus_write(REG_ACQ_COMMAND, 32'd8);
        wait_cycles(ARM_PIPELINE_LATENCY);
        bus_read(REG_ACQ_STATE, read_data);
        check("observe_shift other than 8 is rejected before ARM",
              read_data[2:0] == 3'd1);
        bus_read(REG_EVENT_INFO, read_data);
        check("observe_shift rejection produces CONFIG_REJECTED event",
              read_data[0] && read_data[3:1] == 3'd4);
        bus_write(REG_ACQ_COMMAND, 32'd4);
        bus_write(REG_SUPERVISOR0, {8'd0, 8'd3, 8'd2, 8'd8});

        // VALIDATE uses the same detector but never changes the control path.
        preload(2'd1, 2'd1, 1'b1, 32'd12);
        bus_write(REG_POLARITY, 32'd1);
        bus_write(REG_LOCK_BIAS, 32'd55);
        bus_write(REG_ACQ_COMMAND, 32'd8);
        wait_cycles(ARM_PIPELINE_LATENCY);
        bus_read(REG_ACQ_STATE, read_data);
        check("ARM_VALIDATE enters VALIDATING", read_data[2:0] == 3'd2);
        rising_neg_to_pos_crossing();
        wait_cycles(CROSSING_PIPELINE_LATENCY + EVENT_PIPELINE_LATENCY);
        check("VALIDATE leaves MODE SCAN and ENABLE unchanged",
              mode == 32'd1 && enable);
        check("VALIDATE does not change LOCK_BIAS or Kp",
              lock_bias == 14'sd55 && kp_effective == 14'sd0);
        bus_read(REG_VALIDATE_COUNT, read_data);
        check("VALIDATE increments event count", read_data == 32'd1);
        bus_read(REG_EVENT_INFO, read_data);
        check("VALIDATE event is typed and records directions",
              read_data[0] && read_data[3:1] == 3'd7 &&
              read_data[5:4] == 2'd1 && read_data[7:6] == 2'd1);
        bus_read(REG_EVENT_LOCK_ERROR, read_data);
        check("VALIDATE event records threshold-confirming lock_error",
              $signed(read_data) == 32'sd5);

        // A second pass is permitted only after leaving and re-entering guard.
        rising_neg_to_pos_crossing();
        bus_read(REG_VALIDATE_COUNT, read_data);
        check("one guard pass has only one validate event", read_data == 32'd1);
        set_sample(14'sd120, 14'sd15);
        set_sample(14'sd80, 14'sd15);
        rising_neg_to_pos_crossing();
        wait_cycles(CROSSING_PIPELINE_LATENCY + EVENT_PIPELINE_LATENCY);
        bus_read(REG_VALIDATE_COUNT, read_data);
        check("guard re-entry permits another validate event", read_data == 32'd2);

        // ACTIVE captures the actual crossing sample and starts FPGA Kp ramp.
        bus_write(REG_ACQ_COMMAND, 32'd2);
        check("ABORT does not wait for an observation window",
              mode == 32'd0 && !enable && kp_effective == 14'sd0);
        enter_scan();
        preload(2'd1, 2'd1, 1'b1, 32'd13);
        bus_write(REG_POLARITY, 32'd1);
        bus_write(REG_ACQ_COMMAND, 32'd1);
        wait_cycles(ARM_PIPELINE_LATENCY);
        bus_read(REG_ACQ_STATE, read_data);
        check("ARM_ACTIVE enters ARMED", read_data[2:0] == 3'd3);
        bus_write(REG_CROSSING_CONFIG, {8'd0, 8'd20, 2'd0, 14'd20});
        bus_write(REG_SERVO_CONFIG, {2'd0, 14'd9, 16'd9});
        check("post-ARM CSR writes do not alter committed servo/slew",
              servo_update_div == 16'd1 && out2_slew_limit == 14'd8);
        set_sample(14'sd91, 14'sd25);
        set_sample(14'sd92, 14'sd25);
        set_sample(14'sd93, 14'sd25);
        check("entering destination side first does not trigger", mode == 32'd1);
        set_sample(14'sd120, 14'sd15);
        set_sample(14'sd90, 14'sd15);
        rising_neg_to_pos_crossing();
        wait_cycles(CROSSING_PIPELINE_LATENCY + EVENT_PIPELINE_LATENCY);
        check("qualified ACTIVE crossing enters P_LOCK", mode == 32'd3 && enable);
        check("ACTIVE captures actual OUT2 rather than guard center",
              lock_bias == 14'sd96);
        check("ACTIVE atomically applies setpoint and limits",
              error_setpoint == 14'sd20 &&
              correction_limit == 14'sd16 && lock_limit == 14'sd300);
        bus_read(REG_EVENT_OUT2, read_data);
        check("ACTIVE event payload uses the crossing sample",
              $signed(read_data) == 32'sd96);
        bus_read(REG_EVENT_ERROR, read_data);
        check("ACTIVE event payload records raw ERROR",
              $signed(read_data) == 32'sd25);
        bus_read(REG_EVENT_OUT2, read_data);
        check("event OUT2 and ERROR are the aligned qualifying sample pair",
              $signed(read_data) == 32'sd96);
        bus_read(REG_EVENT_GENERATION, read_data);
        check("ACTIVE event payload records generation", read_data == 32'd13);

        for (i = 0; i < 12; i++) begin
            error_monitor = 14'sd20;
            wait_cycles(1);
        end
        bus_read(REG_KP_EFFECTIVE, read_data);
        check("FPGA soft-start reaches host-approved Kp target",
              $signed(read_data) == 32'sd4);
        wait_cycles((2 * OBSERVE_LENGTH) + SUPERVISOR_PIPELINE_LATENCY + 16);
        bus_read(REG_ACQ_STATE, read_data);
        check("converged windows enter P_LOCKED", read_data[2:0] == 3'd5);

        // Saturation is an immediate FPGA-authoritative fault and SAFE action.
        saturated = 1'b1;
        wait_cycles(HARD_FAULT_PIPELINE_LATENCY);
        check("runtime saturation forces SAFE and clears effective Kp",
              mode == 32'd0 && !enable && kp_effective == 14'sd0);
        saturated = 1'b0;

        // Timeout is a distinct FAILED path and also requests immediate SAFE.
        rstn = 1'b0;
        wait_cycles(3);
        rstn = 1'b1;
        wait_cycles(2);
        bus_write(REG_CROSSING_CONFIG, {8'd0, 8'd3, 2'd0, 14'd4});
        bus_write(REG_KP_TARGET, 32'd4);
        bus_write(REG_KP_RAMP, {16'd1, 2'd0, 14'd1});
        bus_write(REG_TIMEOUT, 32'd10);
        bus_write(REG_SERVO_CONFIG, {2'd0, 14'd8, 16'd1});
        bus_write(REG_SUPERVISOR0, {8'd0, 8'd255, 8'd255, 8'd8});
        bus_write(REG_SUPERVISOR1, {2'd0, 14'd8191, 2'd0, 14'd8191});
        enter_scan();
        preload(2'd1, 2'd1, 1'b1, 32'd14);
        bus_write(REG_POLARITY, 32'd1);
        bus_write(REG_ACQ_COMMAND, 32'd1);
        wait_cycles(ARM_PIPELINE_LATENCY);
        rising_neg_to_pos_crossing();
        error_monitor = 14'sd20;
        wait_cycles(20);
        bus_read(REG_ACQ_STATE, read_data);
        check("acquisition timeout enters FAILED and requests SAFE",
              read_data[2:0] == 3'd6 && mode == 32'd0 &&
              !enable && kp_effective == 14'sd0);

        $display("SUMMARY tb_simple_lock_acquisition tests=%0d pass=%0d fail=%0d",
                 tests, pass_count, fail_count);
        if (fail_count != 0)
            $finish(1);
        $finish;
    end
endmodule
