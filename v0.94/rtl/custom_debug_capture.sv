`timescale 1ns/1ps

module custom_debug_capture #(
    parameter int DEPTH = 4096
) (
    input  logic               clk_i,
    input  logic               rstn_i,
    input  logic               start_i,
    input  logic        [31:0] decimation_i,
    input  logic        [31:0] length_i,
    input  logic        [31:0] read_index_i,
    input  logic signed [13:0] ch1_i,
    input  logic signed [13:0] ch2_i,
    input  logic signed [13:0] ch3_i,
    input  logic signed [13:0] ch4_i,
    output logic               busy_o,
    output logic               done_o,
    output logic signed [13:0] data_ch1_o,
    output logic signed [13:0] data_ch2_o,
    output logic signed [13:0] data_ch3_o,
    output logic signed [13:0] data_ch4_o
);

    localparam int ADDR_WIDTH = $clog2(DEPTH);

    logic signed [13:0] mem_ch1 [0:DEPTH-1];
    logic signed [13:0] mem_ch2 [0:DEPTH-1];
    logic signed [13:0] mem_ch3 [0:DEPTH-1];
    logic signed [13:0] mem_ch4 [0:DEPTH-1];

    logic [31:0] decimation_q;
    logic [31:0] length_q;
    logic [31:0] decim_cnt_q;
    logic [ADDR_WIDTH-1:0] write_index_q;
    logic [ADDR_WIDTH-1:0] read_index_w;

    always_comb begin
        if (read_index_i >= DEPTH) begin
            read_index_w = {ADDR_WIDTH{1'b0}};
        end else begin
            read_index_w = read_index_i[ADDR_WIDTH-1:0];
        end

        data_ch1_o = mem_ch1[read_index_w];
        data_ch2_o = mem_ch2[read_index_w];
        data_ch3_o = mem_ch3[read_index_w];
        data_ch4_o = mem_ch4[read_index_w];
    end

    always_ff @(posedge clk_i) begin
        if (!rstn_i) begin
            busy_o        <= 1'b0;
            done_o        <= 1'b0;
            decimation_q  <= 32'd1;
            length_q      <= 32'd2048;
            decim_cnt_q   <= 32'd0;
            write_index_q <= {ADDR_WIDTH{1'b0}};
        end else begin
            if (start_i) begin
                busy_o        <= 1'b1;
                done_o        <= 1'b0;
                decimation_q  <= (decimation_i == 32'd0) ? 32'd1 : decimation_i;
                if (length_i == 32'd0) begin
                    length_q <= 32'd1;
                end else if (length_i > DEPTH) begin
                    length_q <= DEPTH;
                end else begin
                    length_q <= length_i;
                end
                decim_cnt_q   <= 32'd0;
                write_index_q <= {ADDR_WIDTH{1'b0}};
            end else if (busy_o) begin
                if (decim_cnt_q >= (decimation_q - 32'd1)) begin
                    decim_cnt_q <= 32'd0;
                    mem_ch1[write_index_q] <= ch1_i;
                    mem_ch2[write_index_q] <= ch2_i;
                    mem_ch3[write_index_q] <= ch3_i;
                    mem_ch4[write_index_q] <= ch4_i;

                    if ({20'd0, write_index_q} >= (length_q - 32'd1)) begin
                        busy_o <= 1'b0;
                        done_o <= 1'b1;
                    end else begin
                        write_index_q <= write_index_q + {{(ADDR_WIDTH-1){1'b0}}, 1'b1};
                    end
                end else begin
                    decim_cnt_q <= decim_cnt_q + 32'd1;
                end
            end
        end
    end

endmodule
