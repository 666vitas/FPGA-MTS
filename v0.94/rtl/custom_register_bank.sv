`timescale 1ns/1ps

module custom_register_bank (
    input  logic               clk_i,
    input  logic               rstn_i,
    input  logic signed [13:0] out2_monitor_i,
    input  logic               saturated_i,
    output logic        [31:0] mode_o,
    output logic               enable_o,
    output logic signed [13:0] scan_offset_o,
    output logic signed [13:0] scan_amp_o,
    output logic signed [13:0] scan_step_o,
    output logic        [31:0] scan_update_div_o,
    output logic signed [13:0] out2_limit_o,
    sys_bus_if.s               bus
);

    localparam logic [31:0] REG_MAGIC_VALUE   = 32'h4D545330;
    localparam logic [31:0] REG_VERSION_VALUE = 32'h00030000;

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

    logic [5:0] reg_addr_w;
    logic sys_en_w;
    logic enabled_status_w;

    assign reg_addr_w = bus.addr[2+:6];
    assign sys_en_w = bus.wen | bus.ren;
    assign enabled_status_w = enable_o && (mode_o == 32'd1);

    always_ff @(posedge clk_i) begin
        if (!rstn_i) begin
            mode_o            <= 32'd0;
            enable_o          <= 1'b0;
            scan_offset_o     <= 14'sd6962;
            scan_amp_o        <= 14'sd410;
            scan_step_o       <= 14'sd1;
            scan_update_div_o <= 32'd1524;
            out2_limit_o      <= 14'sd8191;
        end else if (bus.wen) begin
            unique case (reg_addr_w)
                REG_MODE: begin
                    if (bus.wdata == 32'd1) begin
                        mode_o <= 32'd1;
                    end else begin
                        mode_o <= 32'd0;
                    end
                end
                REG_ENABLE: begin
                    enable_o <= bus.wdata[0];
                end
                REG_SCAN_OFFSET: begin
                    scan_offset_o <= bus.wdata[13:0];
                end
                REG_SCAN_AMP: begin
                    scan_amp_o <= bus.wdata[13:0];
                end
                REG_SCAN_STEP: begin
                    scan_step_o <= bus.wdata[13:0];
                end
                REG_SCAN_UPDATE_DIV: begin
                    scan_update_div_o <= (bus.wdata == 32'd0) ? 32'd1 : bus.wdata;
                end
                REG_OUT2_LIMIT: begin
                    if ($signed({1'b0, bus.wdata[13:0]}) > 15'sd8191) begin
                        out2_limit_o <= 14'sd8191;
                    end else begin
                        out2_limit_o <= bus.wdata[13:0];
                    end
                end
                default: begin
                end
            endcase
        end
    end

    always_ff @(posedge clk_i) begin
        if (!rstn_i) begin
            bus.ack   <= 1'b0;
            bus.err   <= 1'b0;
            bus.rdata <= 32'd0;
        end else begin
            bus.ack <= sys_en_w;
            bus.err <= 1'b0;

            if (bus.ren) begin
                unique case (reg_addr_w)
                    REG_MAGIC: begin
                        bus.rdata <= REG_MAGIC_VALUE;
                    end
                    REG_VERSION: begin
                        bus.rdata <= REG_VERSION_VALUE;
                    end
                    REG_MODE: begin
                        bus.rdata <= mode_o;
                    end
                    REG_ENABLE: begin
                        bus.rdata <= {31'd0, enable_o};
                    end
                    REG_SCAN_OFFSET: begin
                        bus.rdata <= {{18{scan_offset_o[13]}}, scan_offset_o};
                    end
                    REG_SCAN_AMP: begin
                        bus.rdata <= {{18{scan_amp_o[13]}}, scan_amp_o};
                    end
                    REG_SCAN_STEP: begin
                        bus.rdata <= {{18{scan_step_o[13]}}, scan_step_o};
                    end
                    REG_SCAN_UPDATE_DIV: begin
                        bus.rdata <= scan_update_div_o;
                    end
                    REG_OUT2_LIMIT: begin
                        bus.rdata <= {{18{out2_limit_o[13]}}, out2_limit_o};
                    end
                    REG_STATUS: begin
                        bus.rdata <= {30'd0, saturated_i, enabled_status_w};
                    end
                    REG_OUT2_MONITOR: begin
                        bus.rdata <= {{18{out2_monitor_i[13]}}, out2_monitor_i};
                    end
                    default: begin
                        bus.rdata <= 32'd0;
                    end
                endcase
            end
        end
    end

endmodule
