`timescale 1ns/1ps

module tb_laser_lock_core;

    logic               clk_i;
    logic               rstn_i;
    logic signed [13:0] pd_i;
    logic signed [13:0] ref_i;
    logic signed [13:0] error_o;
    logic signed [13:0] control_o;

    laser_lock_core dut (
        .clk_i     (clk_i),
        .rstn_i    (rstn_i),
        .pd_i      (pd_i),
        .ref_i     (ref_i),
        .error_o   (error_o),
        .control_o (control_o)
    );

    initial begin
        clk_i = 1'b0;
        forever #4 clk_i = ~clk_i;
    end

    task automatic check_sample(
        input logic signed [13:0] pd_value,
        input logic signed [13:0] ref_value
    );
        begin
            pd_i  = pd_value;
            ref_i = ref_value;
            @(posedge clk_i);
            #1;

            if (error_o !== pd_value) begin
                $error("error_o mismatch: pd_i=%0d error_o=%0d ref_i=%0d",
                       pd_value, error_o, ref_value);
            end

            if (control_o !== 14'sd0) begin
                $error("control_o is not zero: control_o=%0d", control_o);
            end
        end
    endtask

    initial begin
        rstn_i = 1'b0;
        pd_i   = 14'sd0;
        ref_i  = 14'sd0;

        repeat (3) @(posedge clk_i);
        rstn_i = 1'b1;

        check_sample(14'sd0,     14'sd0);
        check_sample(14'sd100,   14'sd0);
        check_sample(-14'sd100,  14'sd0);
        check_sample(14'sd2047,  14'sd321);
        check_sample(-14'sd2048, 14'sd1234);

        // Changing ref_i must not affect error_o in v1.
        check_sample(14'sd777,  -14'sd1);
        check_sample(14'sd777,   14'sd4095);
        check_sample(14'sd777,  -14'sd4096);

        $display("tb_laser_lock_core PASSED");
        $finish;
    end

endmodule: tb_laser_lock_core
