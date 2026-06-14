# REPORT fix dac mux USE_LASER_LOCK_CORE=1 apply

## 0. 本报告作用

本报告记录根据 `FIX_PLAN_dac_mux_use1_bitstream.md` 应用的最小 DAC mux 修正。

目标是让 `USE_LASER_LOCK_CORE=1` 时可以重新尝试 `Generate Bitstream`，用于后续 `v1ab IN1 -> OUT1` 测试。

## 1. 是否备份 red_pitaya_top.sv

已在修改前备份：

```text
E:\new\fpga_lock\v94\v0.94\rtl\red_pitaya_top.sv.before_fix_dac_mux_use1
```

被修改文件：

```text
E:\new\fpga_lock\v94\v0.94\rtl\red_pitaya_top.sv
```

## 2. 修改了 dac mux 哪些代码

本次只修改 `red_pitaya_top.sv` 中 `dac_a_sum / dac_b_sum` mux 附近的代码。

新增明确的 15-bit signed 中间信号：

```systemverilog
logic signed [15-1:0] dac_a_sum_official;
logic signed [15-1:0] dac_b_sum_official;
logic signed [15-1:0] dac_a_sum_laser;
```

官方路径拆出为：

```systemverilog
assign dac_a_sum_official = asg_dat[0] + pid_dat[0];
assign dac_b_sum_official = asg_dat[1] + pid_dat[1];
```

laser 路径拆出为：

```systemverilog
assign dac_a_sum_laser    = {laser_error[13], laser_error};
```

最终 DAC mux 改为：

```systemverilog
assign dac_a_sum = USE_LASER_LOCK_CORE ? dac_a_sum_laser : dac_a_sum_official;
assign dac_b_sum = dac_b_sum_official;
```

## 3. 是否保持 DAC B 官方路径

是。

本次按照要求，`DAC B / dac_b_sum` 暂时保持官方路径：

```systemverilog
assign dac_b_sum = dac_b_sum_official;
```

也就是说，当前 `v1ab` 只尝试让 `laser_error` 接入 DAC A / `OUT1`，不再把 `dac_b_sum` 强制为 `15'sd0`。

## 4. 是否保留 ODDR/PLL/ADC/PS/XDC

已保留。

本次没有修改：

- DAC ODDR；
- `dac_dat_o`；
- `dac_wrt_o`；
- `dac_sel_o`；
- `dac_clk_o`；
- `dac_rst_o`；
- PLL；
- BUFG；
- ADC IO；
- PS/AXI/DDR；
- XDC/SDC；
- `laser_lock_core.sv`；
- `output_protect.sv`。

只读 diff 核对显示，本次变更只集中在：

- `USE_LASER_LOCK_CORE` 参数值；
- `dac_a_sum / dac_b_sum` 附近中间信号声明；
- `dac_a_sum / dac_b_sum` mux 赋值。

## 5. 当前 USE_LASER_LOCK_CORE 的值

当前值：

```systemverilog
localparam logic USE_LASER_LOCK_CORE = 1'b1;
```

## 6. 当前 LASER_LOCK_OUTPUT_MODE 的值

当前值保持为：

```systemverilog
localparam int   LASER_LOCK_OUTPUT_MODE = 0;
```

含义：

```text
OUTPUT_MODE = 0: IN1 / pd_i -> error_o -> DAC A / OUT1
```

## 7. 下一步操作

下一步不要直接上板。

建议在 Vivado 中执行：

```text
Reset Runs
Run Synthesis
Run Implementation
Generate Bitstream
```

如果 `USE_LASER_LOCK_CORE=1` bitstream 成功，再进入：

```text
v1ab IN1 -> OUT1 上板测试
```

在 bitstream 成功前：

- 不开始 `v1c mixer`；
- 不接板子；
- 不接 `D2-125`；
- 不接真实 `PD`；
- 不接激光器反馈。
