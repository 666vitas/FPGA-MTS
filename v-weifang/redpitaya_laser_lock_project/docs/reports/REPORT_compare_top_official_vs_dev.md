# REPORT compare top official vs dev

## 0. 本报告作用

本报告比较两个 top 文件的差异：

官方干净 top：

```text
E:\new\fpga_lock\v94\guanfang-v0.94\v0.94\rtl\red_pitaya_top.sv
```

当前开发 top：

```text
E:\new\fpga_lock\v94\v0.94\rtl\red_pitaya_top.sv
```

本次只比较差异并生成报告，没有修改任何 top、RTL、Vivado 工程或约束文件。

## 1. 总体结论

完整 diff 显示，当前开发 top 相比官方干净 top 主要有两类差异：

1. `v1ab_passthrough_debug` 预期修改；
2. 非预期 LED/HK 相关修改。

当前判断：

- `USE_LASER_LOCK_CORE`、`LASER_LOCK_OUTPUT_MODE`、`laser_error`、`laser_control`、`i_laser_lock_core`、`dac_a_sum / dac_b_sum mux` 属于 `v1ab_passthrough_debug` 预期修改；
- `led_o` 从 `output` 改成 `inout`，以及 `red_pitaya_hk.led_o` 从注释状态改为实际连接，不属于本次 v1ab MTS passthrough 预期修改；
- ADC IO、PLL、BUFG、ODDR、DAC 底层输出、XADC/AMS、PS/AXI/DDR 未发现除行号后移之外的功能性差异；
- top 文件中没有发现 XDC/约束相关引用被修改。

特别注意：

当前开发 top 中：

```text
USE_LASER_LOCK_CORE = 1'b0
LASER_LOCK_OUTPUT_MODE = 0
```

这表示 v1ab 接入代码存在，但当前开关设置为不走 `laser_lock_core` 路径，而是保留官方 ASG + PID DAC 路径。

## 2. v1ab_passthrough_debug 预期修改

### 2.1 新增开关参数

当前开发 top：

```text
line 132: // USE_LASER_LOCK_CORE = 0 keeps the official ASG + PID DAC path.
line 133: // LASER_LOCK_OUTPUT_MODE: 0 = IN1/pd_i -> OUT1, 1 = IN2/ref_i -> OUT1.
line 134: localparam logic USE_LASER_LOCK_CORE = 1'b0;
line 135: localparam int   LASER_LOCK_OUTPUT_MODE = 0;
```

判断：

- 属于 v1ab 预期修改；
- 但当前 `USE_LASER_LOCK_CORE = 1'b0`，不是启用 laser lock core 的状态。

### 2.2 新增 laser_lock_core 输出信号

当前开发 top：

```text
line 205: logic signed [14-1:0] laser_error;
line 206: logic signed [14-1:0] laser_control;
```

判断：

- 属于 v1ab 预期修改。

### 2.3 新增 i_laser_lock_core 实例

当前开发 top：

```text
line 421:   .OUTPUT_MODE(LASER_LOCK_OUTPUT_MODE)
line 422: ) i_laser_lock_core (
line 427:   .error_o   (laser_error  ),
line 428:   .control_o (laser_control)
```

判断：

- 属于 v1ab 预期修改；
- 该实例接在 ADC 数据转换之后、DAC IO 之前，符合之前 v1ab 集成方案。

### 2.4 修改 dac_a_sum / dac_b_sum mux

官方干净 top：

```text
line 411: assign dac_a_sum = asg_dat[0] + pid_dat[0];
line 412: assign dac_b_sum = asg_dat[1] + pid_dat[1];
```

当前开发 top：

```text
line 436: assign dac_a_sum = USE_LASER_LOCK_CORE
line 437:                  ? {laser_error[14-1], laser_error}
line 440: assign dac_b_sum = USE_LASER_LOCK_CORE
```

判断：

- 属于 v1ab 预期修改；
- 修改点位于官方 DAC saturation 之前；
- 官方 DAC saturation 和后续 ODDR 输出逻辑仍保留。

## 3. 非预期修改

发现 2 处非预期修改。

### 3.1 led_o 端口方向被修改

官方干净 top：

```text
line 119:   output   logic [ 8-1:0] led_o
```

当前开发 top：

```text
line 119:   inout  logic [ 8-1:0] led_o
```

判断：

- 这是非预期修改；
- 不属于 `v1ab_passthrough_debug` 需要的 MTS passthrough 修改；
- 该修改改变了顶层 LED 端口方向，属于 I/O 接口层面的变化，建议优先复查。

### 3.2 red_pitaya_hk.led_o 从注释改为连接

官方干净 top：

```text
line 450:   //.led_o           (  led_o                      ),  // LED output
```

当前开发 top：

```text
line 480:   .led_o           (  led_o                      ),  // LED output
```

判断：

- 这是非预期修改；
- 不属于 `v1ab_passthrough_debug` 需要的 MTS passthrough 修改；
- 与 `led_o` 端口方向修改相关，建议一起检查；
- 若当前正在排查 bitstream DRC 或 I/O 相关问题，该差异值得优先关注。

## 4. 敏感区域检查

| 区域 | 检查结果 | 说明 |
|---|---|---|
| ADC IO | 未发现非预期功能性修改 | `adc_dat_raw` 和 `adc_dat` 转换逻辑保持官方结构；v1ab 实例插入在 ADC 数据转换之后 |
| PLL | 未发现非预期修改 | `red_pitaya_pll` 实例和 `pll_*` 信号未见功能性 diff |
| BUFG | 未发现非预期修改 | BUFG 实例未见功能性 diff |
| ODDR | 未发现非预期修改 | ADC clock ODDR 与 DAC ODDR 未见功能性 diff |
| `dac_dat_o/dac_wrt_o/dac_sel_o/dac_clk_o/dac_rst_o` | 未发现非预期修改 | 底层 DAC 输出 ODDR 仍保留官方结构 |
| XADC/AMS | 未发现非预期修改 | `red_pitaya_ams i_ams` 区域未见功能性 diff |
| PS/AXI/DDR | 未发现非预期修改 | DDR 端口、PS 连接、AXI master/system bus 区域未见功能性 diff |
| XDC/约束相关引用 | top 内未发现相关引用被修改 | 本次只比较 `red_pitaya_top.sv`，没有比较外部 `.xdc/.sdc` 文件 |

## 5. 对 PDRC-158 排查的意义

当前 top diff 显示，除 v1ab 预期修改外，确实存在 LED/HK 相关非预期 I/O 修改。

因此在继续怀疑 `laser_lock_core` 之前，建议优先确认：

```text
led_o 是否应保持官方 output logic
red_pitaya_hk.led_o 是否应继续保持注释
```

原因：

- `PDRC-158 Routing mux contention` 属于 DRC/布线资源冲突类错误；
- 错误此前记录集中在 `ILOGIC_X0Y*`；
- `led_o` 端口方向和 HK LED 连接属于 I/O 层面的差异；
- 这类差异比 `laser_lock_core` 的 passthrough 逻辑更值得优先排查。

## 6. 建议的下一步

建议下一步不要继续写 `v1c_mixer`，也不要修改 MTS RTL。

建议顺序：

1. 先记录本报告；
2. 与用户/GPT 确认 `led_o` 两处差异是否应回退到官方写法；
3. 若允许修正，再单独生成修正计划；
4. 修正前不要接板子，不要接 `D2-125`；
5. 修正后再 Reset Runs 并重新跑 bitstream。

本报告只做比较，不执行任何修正。
