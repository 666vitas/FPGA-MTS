`timescale 1ns/1ps

module tb_l1_error_crossing_plant;
    localparam logic [6:0] REG_MODE = 7'h02;
    localparam logic [6:0] REG_ENABLE = 7'h03;
    localparam logic [6:0] REG_POLARITY = 7'h0D;
    localparam logic [6:0] REG_TARGET_OUT2 = 7'h18;
    localparam logic [6:0] REG_TARGET_ERROR = 7'h19;
    localparam logic [6:0] REG_TARGET_WINDOW = 7'h1A;
    localparam logic [6:0] REG_TARGET_REQUIREMENTS = 7'h1B;
    localparam logic [6:0] REG_CORRECTION_LIMIT = 7'h1C;
    localparam logic [6:0] REG_ABSOLUTE_LIMIT = 7'h1D;
    localparam logic [6:0] REG_GENERATION = 7'h1E;
    localparam logic [6:0] REG_COMMAND = 7'h29;
    localparam logic [6:0] REG_STATE = 7'h2A;
    localparam logic [6:0] REG_EVENT_OUT2 = 7'h2C;
    localparam logic [6:0] REG_CROSSING = 7'h3A;
    localparam logic [6:0] REG_KP_TARGET = 7'h3B;
    localparam logic [6:0] REG_KP_RAMP = 7'h3C;
    localparam logic [6:0] REG_TIMEOUT = 7'h3D;
    localparam logic [6:0] REG_SERVO = 7'h3E;
    localparam logic [6:0] REG_SUPERVISOR0 = 7'h3F;
    localparam logic [6:0] REG_SUPERVISOR1 = 7'h40;

    logic clk = 1'b0;
    always #5 clk = ~clk;
    logic rstn;
    sys_bus_if bus (.clk(clk), .rstn(rstn));

    logic [31:0] mode;
    logic enable;
    logic signed [13:0] scan_value;
    logic scan_up;
    logic signed [13:0] selected_out2;
    logic selected_saturated;
    logic signed [13:0] error_sample;
    logic signed [13:0] lock_error;
    logic signed [31:0] raw_error_model;
    logic signed [13:0] plant_zero;
    logic signed [13:0] plant_actuator_q;
    logic signed [14:0] plant_delta_w;
    logic signed [13:0] lock_kp;
    logic signed [13:0] kp_effective;
    logic polarity;
    logic signed [13:0] lock_bias;
    logic signed [13:0] lock_limit;
    logic signed [13:0] correction_limit;
    logic signed [13:0] error_setpoint;
    logic signed [13:0] ki;
    logic integral_reset;
    logic [15:0] servo_div;
    logic [13:0] slew_limit;
    logic acq_trigger;
    logic acq_hold;
    logic acq_abort;
    logic acq_fault;
    logic [31:0] read_data;
    logic signed [13:0] last_scan_sample;
    logic signed [13:0] first_lock_sample;
    logic trigger_seen;
    logic first_lock_seen;
    logic force_large_creep;
    logic wrong_feedback_after_trigger;
    integer creep_count;
    integer cycle_count;
    integer tests;
    integer pass_count;
    integer fail_count;
    integer wait_count;

    logic signed [13:0] unused_scan_offset;
    logic signed [13:0] unused_scan_amp;
    logic signed [13:0] unused_scan_step;
    logic [31:0] unused_scan_div;
    logic signed [13:0] unused_out2_limit;
    logic signed [13:0] unused_hold;
    logic unused_capture_start;
    logic [31:0] unused_capture_decimation;
    logic [31:0] unused_capture_length;
    logic [31:0] unused_capture_index;

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

    task automatic wait_cycles(input integer count);
        repeat (count) @(posedge clk);
        #1;
    endtask

    task automatic bus_write(input logic [6:0] addr, input logic [31:0] data);
        @(negedge clk);
        bus.addr = {23'd0, addr, 2'b00};
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

    task automatic bus_read(input logic [6:0] addr, output logic [31:0] data);
        @(negedge clk);
        bus.addr = {23'd0, addr, 2'b00};
        bus.wen = 1'b0;
        bus.ren = 1'b1;
        @(posedge clk);
        @(negedge clk);
        bus.ren = 1'b0;
        data = bus.rdata;
        bus.addr = 32'd0;
        wait_cycles(1);
    endtask

    always_ff @(posedge clk) begin
        if (!rstn) begin
            scan_value <= 14'sd70;
            scan_up <= 1'b1;
            cycle_count <= 0;
            creep_count <= 0;
            trigger_seen <= 1'b0;
            first_lock_seen <= 1'b0;
            last_scan_sample <= 14'sd0;
            first_lock_sample <= 14'sd0;
            plant_actuator_q <= 14'sd0;
        end else begin
            cycle_count <= cycle_count + 1;
            if (enable && mode == 32'd1) begin
                if (scan_up) begin
                    if (scan_value >= 14'sd130) begin
                        scan_value <= 14'sd129;
                        scan_up <= 1'b0;
                    end else begin
                        scan_value <= scan_value + 14'sd1;
                    end
                end else begin
                    if (scan_value <= 14'sd70) begin
                        scan_value <= 14'sd71;
                        scan_up <= 1'b1;
                    end else begin
                        scan_value <= scan_value - 14'sd1;
                    end
                end
            end
            if (acq_trigger) begin
                trigger_seen <= 1'b1;
                last_scan_sample <= selected_out2;
            end
            if (trigger_seen && !first_lock_seen && mode == 32'd3) begin
                first_lock_seen <= 1'b1;
                first_lock_sample <= selected_out2;
            end
            if (mode == 32'd3 && (cycle_count % 80 == 0) && creep_count < 3)
                creep_count <= creep_count + 1;
            // First-order-like actuator lag: close half of the remaining
            // digital command error per clock, with exact one-count settling.
            if (plant_delta_w > 15'sd1)
                plant_actuator_q <= plant_actuator_q +
                                    (($signed(plant_delta_w) + 15'sd1) >>> 1);
            else if (plant_delta_w < -15'sd1)
                plant_actuator_q <= plant_actuator_q +
                                    ($signed(plant_delta_w) >>> 1);
            else
                plant_actuator_q <= selected_out2;
        end
    end

    always_comb begin
        // The captured guard is centred at 100, but the current rising zero is
        // 110.  After scan stop, hysteresis/static motion moves it four counts
        // beyond the actual trigger bias, then slow creep adds three counts.
        if (mode == 32'd1)
            plant_zero = scan_up ? 14'sd110 : 14'sd90;
        else if (force_large_creep)
            plant_zero = lock_bias + 14'sd80;
        else
            plant_zero = lock_bias + 14'sd4 + creep_count;

        plant_delta_w =
            $signed({selected_out2[13], selected_out2}) -
            $signed({plant_actuator_q[13], plant_actuator_q});
        if (wrong_feedback_after_trigger && mode == 32'd3)
            raw_error_model =
                -32'sd2 * ($signed(plant_actuator_q) - $signed(plant_zero));
        else
            raw_error_model =
                32'sd2 * ($signed(plant_actuator_q) - $signed(plant_zero));
        // Deterministic +/-1 count noise exercises the supervisor without
        // hiding a wrong feedback sign.
        if (cycle_count[2:0] == 3'd0)
            raw_error_model = raw_error_model + 32'sd1;
        else if (cycle_count[2:0] == 3'd4)
            raw_error_model = raw_error_model - 32'sd1;
        if (raw_error_model > 32'sd8191)
            error_sample = 14'sd8191;
        else if (raw_error_model < -32'sd8191)
            error_sample = -14'sd8191;
        else
            error_sample = raw_error_model[13:0];
        lock_error = error_sample - error_setpoint;
    end

    custom_register_bank #(.LOCK_ACQ_IMPL(1)) bank (
        .clk_i(clk), .rstn_i(rstn),
        .out2_monitor_i(selected_out2), .error_monitor_i(error_sample),
        .control_monitor_i(selected_out2), .saturated_i(selected_saturated),
        .mode_o(mode), .enable_o(enable),
        .scan_offset_o(unused_scan_offset), .scan_amp_o(unused_scan_amp),
        .scan_step_o(unused_scan_step), .scan_update_div_o(unused_scan_div),
        .out2_limit_o(unused_out2_limit), .hold_value_o(unused_hold),
        .kp_o(lock_kp), .kp_effective_o(kp_effective),
        .polarity_o(polarity), .lock_bias_o(lock_bias),
        .lock_limit_o(lock_limit),
        .lock_correction_limit_o(correction_limit),
        .error_setpoint_o(error_setpoint), .ki_o(ki),
        .integral_reset_o(integral_reset),
        .servo_update_div_o(servo_div), .out2_slew_limit_o(slew_limit),
        .acq_trigger_o(acq_trigger), .acq_hold_o(acq_hold),
        .acq_abort_o(acq_abort), .acq_fault_o(acq_fault),
        .capture_start_o(unused_capture_start),
        .capture_decimation_o(unused_capture_decimation),
        .capture_length_o(unused_capture_length),
        .capture_read_index_o(unused_capture_index),
        .capture_busy_i(1'b0), .capture_done_i(1'b0),
        .lock_error_monitor_i(lock_error),
        .capture_data_ch1_i(14'sd0), .capture_data_ch2_i(14'sd0),
        .capture_data_ch3_i(14'sd0), .capture_data_ch4_i(14'sd0),
        .bus(bus)
    );

    out2_lock_controller controller (
        .clk_i(clk), .rstn_i(rstn), .enable_i(enable), .mode_i(mode),
        .scan_i(scan_value), .scan_saturated_i(1'b0),
        .hold_value_i(unused_hold), .error_i(lock_error),
        .kp_i(kp_effective), .ki_i(ki), .polarity_i(polarity),
        .lock_bias_i(lock_bias), .lock_limit_i(lock_limit),
        .lock_correction_limit_i(correction_limit),
        .servo_update_div_i(servo_div), .out2_slew_limit_i(slew_limit),
        .integral_reset_i(integral_reset), .acq_hold_i(acq_hold),
        .acq_abort_i(acq_abort), .acq_fault_i(acq_fault),
        .control_o(selected_out2), .saturated_o(selected_saturated)
    );

    initial begin
        tests = 0;
        pass_count = 0;
        fail_count = 0;
        rstn = 1'b0;
        force_large_creep = 1'b0;
        wrong_feedback_after_trigger = 1'b0;
        bus.addr = 32'd0;
        bus.wdata = 32'd0;
        bus.wen = 1'b0;
        bus.ren = 1'b0;
        wait_cycles(5);
        rstn = 1'b1;

        bus_write(REG_CROSSING, {8'd0, 8'd3, 2'd0, 14'd2});
        bus_write(REG_KP_TARGET, 32'd128);
        bus_write(REG_KP_RAMP, {16'd1, 2'd0, 14'd16});
        bus_write(REG_TIMEOUT, 32'd2000);
        bus_write(REG_SERVO, {2'd0, 14'd1, 16'd1});
        bus_write(REG_SUPERVISOR0, {8'd0, 8'd8, 8'd3, 8'd3});
        bus_write(REG_SUPERVISOR1, {2'd0, 14'd12, 2'd0, 14'd10});
        bus_write(REG_TARGET_OUT2, 32'd100);
        bus_write(REG_TARGET_ERROR, 32'd0);
        bus_write(REG_TARGET_WINDOW, 32'd20);
        // rising + NEG_TO_POS => positive slope => polarity bit 1.
        bus_write(REG_TARGET_REQUIREMENTS, 32'h15);
        bus_write(REG_CORRECTION_LIMIT, 32'd24);
        bus_write(REG_ABSOLUTE_LIMIT, 32'd300);
        bus_write(REG_GENERATION, 32'd77);
        bus_write(REG_POLARITY, 32'd1);
        bus_write(REG_MODE, 32'd1);
        bus_write(REG_ENABLE, 32'd1);
        wait_cycles(8);
        bus_write(REG_COMMAND, 32'd1);

        wait_count = 0;
        while (!trigger_seen && wait_count < 300) begin
            wait_cycles(1);
            wait_count++;
        end
        check("plant waits for current ERROR zero rather than guard center",
              trigger_seen && last_scan_sample >= 14'sd111 &&
              last_scan_sample <= 14'sd118);
        bus_read(REG_EVENT_OUT2, read_data);
        check("plant event stores actual trigger OUT2",
              $signed(read_data) == $signed(last_scan_sample));
        wait_cycles(4);
        check("SCAN to lock first output is bumpless within one count",
              first_lock_seen &&
              (($signed(first_lock_sample) - $signed(last_scan_sample) <= 1) &&
               ($signed(first_lock_sample) - $signed(last_scan_sample) >= -1)));

        wait_count = 0;
        bus_read(REG_STATE, read_data);
        while ((read_data[2:0] != 3'd5) && wait_count < 1200) begin
            wait_cycles(4);
            bus_read(REG_STATE, read_data);
            wait_count += 4;
        end
        check("correct-polarity soft-start converges to P_LOCKED",
              read_data[2:0] == 3'd5);
        check("small PZT creep remains inside correction range",
              mode == 32'd3 && enable && !selected_saturated &&
              (($signed(error_sample) <= 12) && ($signed(error_sample) >= -12)));

        force_large_creep = 1'b1;
        wait_count = 0;
        while (mode != 32'd0 && wait_count < 200) begin
            wait_cycles(1);
            wait_count++;
        end
        check("out-of-range plant motion produces FPGA SAFE failure",
              mode == 32'd0 && !enable && kp_effective == 14'sd0);

        // A plant whose sign changes after capture emulates an incorrect
        // physical feedback direction despite internally consistent metadata.
        // The supervisor must never report P_LOCKED and must request SAFE.
        rstn = 1'b0;
        force_large_creep = 1'b0;
        wrong_feedback_after_trigger = 1'b1;
        wait_cycles(4);
        rstn = 1'b1;
        bus_write(REG_CROSSING, {8'd0, 8'd3, 2'd0, 14'd2});
        bus_write(REG_KP_TARGET, 32'd128);
        bus_write(REG_KP_RAMP, {16'd1, 2'd0, 14'd16});
        bus_write(REG_TIMEOUT, 32'd1000);
        bus_write(REG_SERVO, {2'd0, 14'd1, 16'd1});
        bus_write(REG_SUPERVISOR0, {8'd0, 8'd2, 8'd3, 8'd3});
        bus_write(REG_SUPERVISOR1, {2'd0, 14'd8, 2'd0, 14'd6});
        bus_write(REG_TARGET_OUT2, 32'd100);
        bus_write(REG_TARGET_ERROR, 32'd0);
        bus_write(REG_TARGET_WINDOW, 32'd20);
        bus_write(REG_TARGET_REQUIREMENTS, 32'h15);
        bus_write(REG_CORRECTION_LIMIT, 32'd24);
        bus_write(REG_ABSOLUTE_LIMIT, 32'd300);
        bus_write(REG_GENERATION, 32'd78);
        bus_write(REG_POLARITY, 32'd1);
        bus_write(REG_MODE, 32'd1);
        bus_write(REG_ENABLE, 32'd1);
        wait_cycles(8);
        bus_write(REG_COMMAND, 32'd1);
        wait_count = 0;
        while (!trigger_seen && wait_count < 300) begin
            wait_cycles(1);
            wait_count++;
        end
        check("wrong-feedback scenario still arms on a valid current crossing",
              trigger_seen);
        wait_count = 0;
        while (mode != 32'd0 && wait_count < 500) begin
            wait_cycles(1);
            wait_count++;
        end
        check("wrong physical feedback sign diverges and enters SAFE",
              mode == 32'd0 && !enable && kp_effective == 14'sd0);

        $display("SUMMARY tb_l1_error_crossing_plant tests=%0d pass=%0d fail=%0d",
                 tests, pass_count, fail_count);
        if (fail_count != 0)
            $finish(1);
        $finish;
    end
endmodule
