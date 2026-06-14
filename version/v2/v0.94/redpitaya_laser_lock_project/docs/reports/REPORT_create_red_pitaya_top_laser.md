# REPORT_create_red_pitaya_top_laser

## 0. 本报告作用

本报告记录本次任务：采用“项目内 top 副本”方案，生成激光锁频项目专用 top 文件。

本次没有修改 Vivado 工程，没有运行 Vivado，没有生成 bitstream。

## 1. 是否成功复制 top

已成功复制。

原始 top 路径：

```text
E:\new\fpga_lock\v94\v0.94\rtl\red_pitaya_top.sv
```

新 top 路径：

```text
E:\new\fpga_lock\v94\v0.94\redpitaya_laser_lock_project\rtl\red_pitaya_top_laser.sv
```

说明：本次复制的是当前工作区中的 `rtl\red_pitaya_top.sv`。该文件在此前步骤中已经应用过 `v1ab_passthrough_debug` patch，因此复制版中已包含 v1ab 集成内容。

## 2. 模块名是否改为 red_pitaya_top_laser

已修改。

原模块名：

```systemverilog
module red_pitaya_top #(
```

已改为：

```systemverilog
module red_pitaya_top_laser #(
```

文件结尾也已从：

```systemverilog
endmodule: red_pitaya_top
```

改为：

```systemverilog
endmodule: red_pitaya_top_laser
```

## 3. v1ab 集成修改了哪些位置

`red_pitaya_top_laser.sv` 中包含以下 v1ab 集成内容。

### 3.1 新增参数

```systemverilog
localparam logic USE_LASER_LOCK_CORE = 1'b1;
localparam int   LASER_LOCK_OUTPUT_MODE = 0;
```

当前含义：

| 参数 | 当前值 | 含义 |
|---|---:|---|
| `USE_LASER_LOCK_CORE` | `1'b1` | 使用 `laser_lock_core` 输出路径 |
| `LASER_LOCK_OUTPUT_MODE` | `0` | 当前测试 `IN1 -> OUT1` |

如需测试 `IN2 -> OUT1`，后续将 `LASER_LOCK_OUTPUT_MODE` 改为 `1`，然后重新综合、实现、生成 bitstream。

### 3.2 新增信号

```systemverilog
logic signed [14-1:0] laser_error;
logic signed [14-1:0] laser_control;
```

| 信号 | 作用 |
|---|---|
| `laser_error` | 接收 `laser_lock_core.error_o`，送到 DAC A saturation 前 |
| `laser_control` | 接收 `laser_lock_core.control_o`，第一阶段保留但不输出有效控制量 |

### 3.3 实例化 laser_lock_core

集成接线：

```text
clk_i     -> adc_clk
rstn_i    -> adc_rstn
pd_i      -> adc_dat[0]
ref_i     -> adc_dat[1]
error_o   -> laser_error
control_o -> laser_control
```

### 3.4 修改 DAC A/B 求和路径

当：

```text
USE_LASER_LOCK_CORE = 0
```

保持官方路径：

```systemverilog
dac_a_sum = asg_dat[0] + pid_dat[0]
dac_b_sum = asg_dat[1] + pid_dat[1]
```

当：

```text
USE_LASER_LOCK_CORE = 1
```

使用：

```systemverilog
dac_a_sum = {laser_error[14-1], laser_error}
dac_b_sum = 15'sd0
```

## 4. 是否保留官方逻辑

已保留官方逻辑。

`red_pitaya_top_laser.sv` 中仍保留：

- saturation；
- signed-to-unsigned / negative-slope conversion；
- DAC ODDR；
- PLL；
- BUFG；
- ADC IO；
- PS/AXI/DDR；
- XDC 相关外部约束不在本文件中，未修改；
- `dac_dat_o`、`dac_wrt_o`、`dac_sel_o`、`dac_clk_o`、`dac_rst_o` 输出层。

本次只是在 DAC saturation 前选择 `laser_error` 或官方 `ASG + PID` 路径，没有直接驱动 DAC 输出管脚。

## 5. 是否没有修改官方 red_pitaya_top.sv

本次任务没有再次修改官方：

```text
E:\new\fpga_lock\v94\v0.94\rtl\red_pitaya_top.sv
```

本次只新增/修改项目目录内文件：

```text
redpitaya_laser_lock_project\rtl\red_pitaya_top_laser.sv
redpitaya_laser_lock_project\docs\reports\REPORT_create_red_pitaya_top_laser.md
```

注意：官方 `rtl\red_pitaya_top.sv` 在此前步骤中已经应用过 v1ab patch。如果后续想让官方 top 回到原始状态，可以使用：

```text
rtl\red_pitaya_top.sv.before_v1ab
```

恢复官方 top。

## 6. Vivado 中下一步如何 Add Sources

后续如果决定使用项目内 top 副本，需要在 Vivado 中添加这些 `Design Sources`：

```text
redpitaya_laser_lock_project\rtl\red_pitaya_top_laser.sv
redpitaya_laser_lock_project\rtl\laser_lock_core.sv
redpitaya_laser_lock_project\rtl\output_protect.sv
```

Vivado GUI 大致步骤：

1. 打开 Vivado 工程；
2. 在 `Sources` 窗口右键；
3. 选择 `Add Sources`；
4. 选择 `Add or create design sources`；
5. 添加上面三个 `.sv` 文件；
6. 确认文件加入 `Design Sources`。

新手注意：不要把 testbench 加到 `Design Sources`。testbench 应该放在 `Simulation Sources`。

## 7. 如何 Set as Top

如果要让 Vivado 使用激光锁频项目专用 top：

1. 在 Vivado `Sources` 窗口中找到：

```text
red_pitaya_top_laser
```

2. 右键 `red_pitaya_top_laser`；
3. 选择 `Set as Top`；
4. 确认 Vivado 顶层模块变为：

```text
red_pitaya_top_laser
```

然后再运行：

```text
Run Synthesis
Run Implementation
Generate Bitstream
```

## 8. 如何回退到官方 top

### 8.1 Vivado 中回退

如果只是在 Vivado 中切换 top，回退方法是：

1. 在 `Sources` 中找到官方：

```text
red_pitaya_top
```

2. 右键；
3. 选择 `Set as Top`；
4. 确认顶层模块回到：

```text
red_pitaya_top
```

### 8.2 移除项目 top 副本

也可以从 Vivado 工程中移除：

```text
redpitaya_laser_lock_project\rtl\red_pitaya_top_laser.sv
```

注意：从 Vivado 工程移除即可，不要随便删除文件，除非已经确认不需要。

### 8.3 恢复官方 top 到 v1ab 前状态

如果想让官方 `rtl\red_pitaya_top.sv` 回到 v1ab patch 前状态，可以用备份：

```text
rtl\red_pitaya_top.sv.before_v1ab
```

恢复：

```text
rtl\red_pitaya_top.sv
```

## 9. 本次没有做的事

本次没有：

- 修改 Vivado 工程；
- 运行 Vivado；
- 运行 `Run Synthesis`；
- 运行 `Run Implementation`；
- 运行 `Generate Bitstream`；
- 生成 bitstream；
- 开始 `v1c mixer`；
- 修改 XDC；
- 修改 PS/AXI/DDR；
- 修改 PLL/ODDR。

## 10. 下一步建议

下一步建议先让 GPT 审查：

```text
redpitaya_laser_lock_project\rtl\red_pitaya_top_laser.sv
```

重点审查：

1. 模块名 `red_pitaya_top_laser` 是否正确；
2. `laser_lock_core` 接线是否正确；
3. DAC A/B mux 是否安全；
4. 是否保留官方 DAC 后级；
5. Vivado 中是否应该用 `red_pitaya_top_laser` 作为 top；
6. 是否需要先恢复官方 `red_pitaya_top.sv` 到备份状态，再只使用项目 top 副本。
