# REPORT_patch_v1ab_passthrough_debug

## 0. 本报告作用

本报告记录本次任务：生成 `v1ab_passthrough_debug` 的 top 修改 patch 和说明。

本次只生成 patch 文件和文档，没有应用 patch。

## 1. 本次生成的文件

| 文件 | 作用 |
|---|---|
| `redpitaya_laser_lock_project\patches\PATCH_v1ab_passthrough_debug.diff` | 针对官方 `rtl\red_pitaya_top.sv` 的待审查 patch |
| `redpitaya_laser_lock_project\docs\integration\PATCH_GUIDE_v1ab_passthrough_debug.md` | 说明如何审查、应用和回退 patch |
| `redpitaya_laser_lock_project\docs\reports\REPORT_patch_v1ab_passthrough_debug.md` | 本报告 |

## 2. patch 涉及哪些文件

patch 目标文件只有：

```text
rtl\red_pitaya_top.sv
```

patch 计划做的事：

1. 新增 `laser_error` 和 `laser_control`；
2. 新增 `USE_LASER_LOCK_CORE` 和 `LASER_LOCK_OUTPUT_MODE`；
3. 实例化 `laser_lock_core`；
4. 在 `dac_a_sum/dac_b_sum` 位置增加 mux；
5. 保留官方 saturation、格式转换和 DAC ODDR。

## 3. 是否修改官方工程

本次没有修改官方工程。

明确没有修改：

```text
rtl\red_pitaya_top.sv
project
sim
ip
sdc
Vivado 工程
```

本次也没有运行 Vivado，没有复制 top，没有生成 bitstream。

## 3.1 patch 格式检查

已执行非破坏性检查：

```text
git apply --check redpitaya_laser_lock_project\patches\PATCH_v1ab_passthrough_debug.diff
```

检查结果：

```text
PATCH_CHECK_OK
```

说明：patch 可以匹配当前 `rtl\red_pitaya_top.sv` 的文本位置，但本次没有应用 patch。

## 4. 必须保留的官方逻辑

patch 说明中明确要求保留：

- 官方 saturation；
- signed-to-unsigned / negative-slope conversion；
- DAC ODDR；
- PLL；
- BUFG；
- ADC IO；
- PS/AXI/DDR；
- XDC；
- `dac_dat_o`、`dac_wrt_o`、`dac_sel_o`、`dac_clk_o`、`dac_rst_o` 输出层。

## 5. 当前 patch 的安全边界

当前 patch 只应该触碰：

- top 内部 localparam；
- top 内部 `laser_error/laser_control` 信号；
- `laser_lock_core` 实例化；
- `dac_a_sum/dac_b_sum` 的 mux。

如果审查时发现 patch 修改了 ODDR、PLL、BUFG、ADC 输入格式转换、PS/AXI/DDR、XDC 或 DAC 输出层，应停止应用。

## 6. 下一步需要 GPT 审查 patch

下一步请把以下文件交给 GPT 审查：

```text
redpitaya_laser_lock_project\patches\PATCH_v1ab_passthrough_debug.diff
redpitaya_laser_lock_project\docs\integration\PATCH_GUIDE_v1ab_passthrough_debug.md
```

重点审查：

1. `laser_lock_core` 接线是否正确；
2. `dac_a_sum` 是否接在 saturation 前；
3. `dac_b_sum = 15'sd0` 是否适合 v1ab；
4. 是否保留官方 DAC 后级；
5. 是否存在破坏官方工程的风险；
6. 是否需要调整 patch 位置或注释。

## 7. 审查通过后才允许应用 patch

审查通过前，不允许：

- 应用 patch；
- 修改官方 `red_pitaya_top.sv`；
- 修改 Vivado 工程；
- 运行 Vivado 集成；
- 上板测试。

审查通过后，建议顺序：

1. 备份 `rtl\red_pitaya_top.sv`；
2. 应用 patch；
3. 在 Vivado 中加入：

```text
redpitaya_laser_lock_project\rtl\laser_lock_core.sv
redpitaya_laser_lock_project\rtl\output_protect.sv
```

4. 运行 `Run Synthesis`；
5. 运行 `Run Implementation`；
6. 运行 `Generate Bitstream`；
7. 只用示波器验证 `OUT1`，不接 `D2-125`，不接激光器反馈。
