# REPORT_apply_patch_v1ab_passthrough_debug

## 0. 本报告作用

本报告记录本次任务：应用 `v1ab_passthrough_debug` 的 top 修改 patch。

本次已经按用户要求修改：

```text
rtl\red_pitaya_top.sv
```

本次没有修改 Vivado 工程，没有运行 Vivado，没有生成 bitstream，没有开始 `v1c`。

## 1. 是否成功备份 red_pitaya_top.sv

已成功备份。

原文件：

```text
rtl\red_pitaya_top.sv
```

备份文件：

```text
rtl\red_pitaya_top.sv.before_v1ab
```

备份后检查结果：

```text
red_pitaya_top.sv.before_v1ab 已存在
```

## 2. patch 检查结果

应用前已执行：

```text
git apply --check redpitaya_laser_lock_project\patches\PATCH_v1ab_passthrough_debug.diff
```

结果：

```text
PATCH_CHECK_OK
```

说明：patch 能匹配当前 `rtl\red_pitaya_top.sv`。

## 3. 是否成功应用 patch

已成功应用。

执行命令：

```text
git apply redpitaya_laser_lock_project\patches\PATCH_v1ab_passthrough_debug.diff
```

结果：

```text
PATCH_APPLY_OK
```

## 4. red_pitaya_top.sv 修改了哪些位置

相对于备份文件 `rtl\red_pitaya_top.sv.before_v1ab`，本次修改了以下位置。

### 4.1 新增 v1ab 控制参数

新增：

```systemverilog
localparam logic USE_LASER_LOCK_CORE = 1'b1;
localparam int   LASER_LOCK_OUTPUT_MODE = 0;
```

当前含义：

| 参数 | 当前值 | 含义 |
|---|---:|---|
| `USE_LASER_LOCK_CORE` | `1'b1` | 当前走 `laser_lock_core` 输出路径 |
| `LASER_LOCK_OUTPUT_MODE` | `0` | 当前测试 `IN1 -> OUT1` |

如果要测试 `IN2 -> OUT1`，需要把：

```systemverilog
localparam int   LASER_LOCK_OUTPUT_MODE = 1;
```

然后重新综合、实现、生成 bitstream。

### 4.2 新增 laser_lock_core 输出信号

新增：

```systemverilog
logic signed [14-1:0] laser_error;
logic signed [14-1:0] laser_control;
```

说明：

| 信号 | 作用 |
|---|---|
| `laser_error` | 接收 `laser_lock_core.error_o`，送入 DAC A saturation 前 |
| `laser_control` | 接收 `laser_lock_core.control_o`，第一阶段保留但不输出有效控制量 |

### 4.3 新增 laser_lock_core 实例化

新增实例：

```systemverilog
laser_lock_core #(
  .OUTPUT_MODE(LASER_LOCK_OUTPUT_MODE)
) i_laser_lock_core (
  .clk_i     (adc_clk      ),
  .rstn_i    (adc_rstn     ),
  .pd_i      (adc_dat[0]   ),
  .ref_i     (adc_dat[1]   ),
  .error_o   (laser_error  ),
  .control_o (laser_control)
);
```

接线关系：

```text
clk_i     <- adc_clk
rstn_i    <- adc_rstn
pd_i      <- adc_dat[0]
ref_i     <- adc_dat[1]
error_o   -> laser_error
control_o -> laser_control
```

### 4.4 修改 DAC 求和路径

原官方路径：

```systemverilog
assign dac_a_sum = asg_dat[0] + pid_dat[0];
assign dac_b_sum = asg_dat[1] + pid_dat[1];
```

修改为：

```systemverilog
assign dac_a_sum = USE_LASER_LOCK_CORE
                 ? {laser_error[14-1], laser_error}
                 : asg_dat[0] + pid_dat[0];

assign dac_b_sum = USE_LASER_LOCK_CORE
                 ? 15'sd0
                 : asg_dat[1] + pid_dat[1];
```

含义：

| `USE_LASER_LOCK_CORE` | DAC A | DAC B |
|---:|---|---|
| 0 | 官方 `asg_dat[0] + pid_dat[0]` | 官方 `asg_dat[1] + pid_dat[1]` |
| 1 | `laser_error` 符号扩展后送 DAC A | `15'sd0` |

## 5. 是否只修改了 red_pitaya_top.sv

本次实际应用 patch 的目标文件只有：

```text
rtl\red_pitaya_top.sv
```

同时按用户要求创建了备份文件：

```text
rtl\red_pitaya_top.sv.before_v1ab
```

除上述目标文件和备份文件外，本次没有修改其他官方设计文件。

## 6. 是否没有修改 ODDR/PLL/PS/AXI/DDR/XDC

没有修改以下内容：

```text
ODDR
PLL
BUFG
ADC 输入格式转换
PS/AXI/DDR
XDC
dac_dat_o
dac_wrt_o
dac_sel_o
dac_clk_o
dac_rst_o
```

本次修改保留了官方 DAC 后级：

```text
saturation
signed-to-unsigned / negative-slope conversion
DAC ODDR
```

也就是说，`laser_error` 只接入 `dac_a_sum` 前的选择路径，不直接驱动 DAC 输出管脚。

## 7. 下一步 Vivado 需要添加哪些文件

后续进入 Vivado 前，需要把以下自定义 RTL 加入 `Design Sources`：

```text
redpitaya_laser_lock_project\rtl\laser_lock_core.sv
redpitaya_laser_lock_project\rtl\output_protect.sv
```

原因：

- `red_pitaya_top.sv` 现在实例化了 `laser_lock_core`；
- `laser_lock_core.sv` 内部实例化了 `output_protect`；
- 如果不加入这两个文件，Vivado 综合时会找不到模块。

## 8. 当前 OUTPUT_MODE 是多少

当前：

```systemverilog
localparam int   LASER_LOCK_OUTPUT_MODE = 0;
```

含义：

```text
OUTPUT_MODE = 0
测试 IN1 -> OUT1
```

如果要测试 `IN2 -> OUT1`，需要改为：

```systemverilog
localparam int   LASER_LOCK_OUTPUT_MODE = 1;
```

然后重新运行：

```text
Run Synthesis
Run Implementation
Generate Bitstream
```

## 9. 当前 USE_LASER_LOCK_CORE 是多少

当前：

```systemverilog
localparam logic USE_LASER_LOCK_CORE = 1'b1;
```

含义：

```text
DAC A 使用 laser_error
DAC B 输出 0
```

如果要回退官方路径，改为：

```systemverilog
localparam logic USE_LASER_LOCK_CORE = 1'b0;
```

## 10. 如何回退

### 10.1 方法 1：关闭 laser_lock_core 路径

把：

```systemverilog
localparam logic USE_LASER_LOCK_CORE = 1'b1;
```

改为：

```systemverilog
localparam logic USE_LASER_LOCK_CORE = 1'b0;
```

这样 DAC A/B 回到官方 `ASG + PID` 路径。

### 10.2 方法 2：用备份恢复 red_pitaya_top.sv

用：

```text
rtl\red_pitaya_top.sv.before_v1ab
```

恢复：

```text
rtl\red_pitaya_top.sv
```

### 10.3 方法 3：反向应用 patch

如果文件只经历了本次 patch 修改，可以使用：

```text
git apply -R redpitaya_laser_lock_project\patches\PATCH_v1ab_passthrough_debug.diff
```

注意：如果后续又手动改过 `red_pitaya_top.sv`，反向 patch 可能失败，此时优先用备份恢复。

## 11. 本次没有做的事

本次没有：

- 修改 Vivado 工程；
- 运行 Vivado；
- 运行 `Run Synthesis`；
- 运行 `Run Implementation`；
- 运行 `Generate Bitstream`；
- 生成 bitstream；
- 开始 `v1c mixer`；
- 接 `D2-125`；
- 接激光器反馈。

## 12. 下一步建议

下一步进入 Vivado 前，建议先让 GPT 审查本次实际 diff。

审查通过后，再进行：

1. 打开 Vivado 工程；
2. 把 `laser_lock_core.sv` 和 `output_protect.sv` 加入 `Design Sources`；
3. 确认 `LASER_LOCK_OUTPUT_MODE = 0`；
4. 确认 `USE_LASER_LOCK_CORE = 1'b1`；
5. 运行 `Run Synthesis`；
6. 运行 `Run Implementation`；
7. 运行 `Generate Bitstream`；
8. 上板时只接示波器，不接 `D2-125`，不接激光器反馈。
