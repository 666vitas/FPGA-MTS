`timescale 1ns/1ps

module ramp_generator (
    input  logic               clk_i,
    input  logic               rstn_i,
    input  logic               enable_i,
    input  logic signed [13:0] offset_i,
    input  logic signed [13:0] amp_i,
    input  logic signed [13:0] step_i,
    input  logic        [31:0] update_div_i,
    input  logic signed [13:0] limit_i,
    output logic signed [13:0] scan_o,
    output logic               saturated_o
);

    localparam logic signed [13:0] SAFE_VALUE = 14'sd0;
    localparam logic signed [14:0] DAC_POS_LIMIT = 15'sd8191;
    localparam logic signed [14:0] DAC_NEG_LIMIT = -15'sd8191;

    logic [31:0] update_cnt_q;
    logic signed [14:0] pos_q;
    logic direction_up_q;

    logic signed [14:0] amp_abs_w;
    logic signed [14:0] step_abs_w;
    logic signed [14:0] limit_abs_w;
    logic signed [14:0] effective_limit_w;
    logic signed [14:0] next_pos_w;
    logic signed [14:0] raw_scan_w;
    logic signed [14:0] limited_scan_w;
    logic saturated_w;
    logic tick_w;

    always_comb begin
        amp_abs_w = {amp_i[13], amp_i};
        if (amp_abs_w < 15'sd0) begin
            amp_abs_w = -amp_abs_w;
        end
        if (amp_abs_w > DAC_POS_LIMIT) begin
            amp_abs_w = DAC_POS_LIMIT;
        end

        step_abs_w = {step_i[13], step_i};
        if (step_abs_w < 15'sd0) begin
            step_abs_w = -step_abs_w;
        end
        if (step_abs_w < 15'sd1) begin
            step_abs_w = 15'sd1;
        end

        limit_abs_w = {limit_i[13], limit_i};
        if (limit_abs_w < 15'sd0) begin
            limit_abs_w = -limit_abs_w;
        end
        if (limit_abs_w > DAC_POS_LIMIT) begin
            effective_limit_w = DAC_POS_LIMIT;
        end else begin
            effective_limit_w = limit_abs_w;
        end

        if (direction_up_q) begin
            next_pos_w = pos_q + step_abs_w;
            if (next_pos_w >= amp_abs_w) begin
                next_pos_w = amp_abs_w;
            end
        end else begin
            next_pos_w = pos_q - step_abs_w;
            if (next_pos_w <= -amp_abs_w) begin
                next_pos_w = -amp_abs_w;
            end
        end

        raw_scan_w = {offset_i[13], offset_i} + pos_q;

        if (raw_scan_w > effective_limit_w) begin
            limited_scan_w = effective_limit_w;
            saturated_w = 1'b1;
        end else if (raw_scan_w < -effective_limit_w) begin
            limited_scan_w = -effective_limit_w;
            saturated_w = 1'b1;
        end else begin
            limited_scan_w = raw_scan_w;
            saturated_w = 1'b0;
        end

        if (limited_scan_w > DAC_POS_LIMIT) begin
            limited_scan_w = DAC_POS_LIMIT;
            saturated_w = 1'b1;
        end else if (limited_scan_w < DAC_NEG_LIMIT) begin
            limited_scan_w = DAC_NEG_LIMIT;
            saturated_w = 1'b1;
        end
    end

    assign tick_w = (update_div_i <= 32'd1) || (update_cnt_q >= update_div_i - 32'd1);

    always_ff @(posedge clk_i) begin
        if (!rstn_i) begin
            update_cnt_q   <= 32'd0;
            pos_q          <= 15'sd0;
            direction_up_q <= 1'b1;
            scan_o         <= SAFE_VALUE;
            saturated_o    <= 1'b0;
        end else if (!enable_i) begin
            update_cnt_q   <= 32'd0;
            pos_q          <= -amp_abs_w;
            direction_up_q <= 1'b1;
            scan_o         <= SAFE_VALUE;
            saturated_o    <= 1'b0;
        end else begin
            if (tick_w) begin
                update_cnt_q <= 32'd0;
                pos_q <= next_pos_w;
                if (direction_up_q && (next_pos_w >= amp_abs_w)) begin
                    direction_up_q <= 1'b0;
                end else if (!direction_up_q && (next_pos_w <= -amp_abs_w)) begin
                    direction_up_q <= 1'b1;
                end
            end else begin
                update_cnt_q <= update_cnt_q + 32'd1;
            end

            scan_o      <= limited_scan_w[13:0];
            saturated_o <= saturated_w;
        end
    end

endmodule
