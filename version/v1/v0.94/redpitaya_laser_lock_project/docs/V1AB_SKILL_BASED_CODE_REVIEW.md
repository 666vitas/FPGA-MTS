# V1AB_SKILL_BASED_CODE_REVIEW

## 1. 使用的 skills

本次按用户要求使用了两个 Codex skills：

- `zoom-out`：先从项目结构、RTL 位置、Vivado top、`IN1/IN2 -> ADC -> laser_lock_core -> DAC A -> OUT1` 的整体数据通路建立地图。
- `diagnose`：按代码链路、Vivado 工程、bitstream、上板测试风险分层审查，不直接改代码。

同时参考了 `grill-with-docs` 的思路：当文档和代码/工程状态存在不一致时，不擅自判断为已经安全，而是在“必须人工确认的问题”中列出。

本次没有使用：

- `tdd`：本次不开发新 RTL；
- `to-prd`：本次不写需求文档；
- `improve-codebase-architecture`：`v1ab` 还没有物理测试通过；
- `prototype`：本次不做离线试算。

## 2. 总体结论

当前 `v1ab_passthrough_debug` 结论：

```text
部分可以
```

用于明天上板测试的判断：

- 可以作为 `v1ab IN1 -> OUT1` 和后续 `v1ab IN2 -> OUT1` 的候选 bitstream/工程基础；
- 代码链路从 `adc_dat[0]/adc_dat[1]` 到 `laser_lock_core`，再到 `laser_error -> dac_a_sum -> DAC A` 的设计意图是清楚的；
- `laser_lock_core.sv` 和 `output_protect.sv` 的 v1ab 逻辑本身可行；
- 但还不能说 v1ab 已经完整通过，因为尚未完成示波器物理验证；
- 还存在 Vivado Sources 路径需要人工确认的问题：`.xpr` 当前指向 `E:\new\fpga_lock\v94\v0.94\rtl\laser_lock_core.sv` 和 `E:\new\fpga_lock\v94\v0.94\rtl\output_protect.sv`，不是本次重点审查清单中的项目资料库路径。不过两组文件 SHA256 一致，当前内容相同。

明天建议只做：

```text
Step 1: OUTPUT_MODE=0, IN1 -> OUT1
Step 2: OUTPUT_MODE=1, IN2 -> OUT1
```

不允许直接进入 mixer。

## 3. 已阅读文件

已阅读/检查：

```text
E:\new\fpga_lock\v94\v0.94\redpitaya_laser_lock_project\docs\PROJECT_REVIEW_V0_94.md
E:\new\fpga_lock\v94\v0.94\rtl\red_pitaya_top.sv
E:\new\fpga_lock\v94\v0.94\redpitaya_laser_lock_project\rtl\laser_lock_core.sv
E:\new\fpga_lock\v94\v0.94\redpitaya_laser_lock_project\rtl\output_protect.sv
E:\new\fpga_lock\v94\v0.94\redpitaya_laser_lock_project\sim\tb_laser_lock_core_v1ab.sv
E:\new\fpga_lock\v94\v0.94\project\redpitaya.xpr
E:\new\fpga_lock\v94\v0.94\project\redpitaya.srcs\sources_1\imports\RedPitaya-FPGA-master\prj\v0.94\rtl\red_pitaya_top.sv
E:\new\fpga_lock\v94\v0.94\redpitaya_laser_lock_project\rtl\red_pitaya_top_laser.sv
```

同时检查到以下实际 Vivado source 路径：

```text
E:\new\fpga_lock\v94\v0.94\rtl\laser_lock_core.sv
E:\new\fpga_lock\v94\v0.94\rtl\output_protect.sv
E:\new\fpga_lock\v94\v0.94\rtl\red_pitaya_top.sv
```

需要人工确认：

```text
Vivado GUI 的 Sources 中实际启用的 laser_lock_core.sv / output_protect.sv 是否确实是 v0.94\rtl 下的这两份。
```

本次 hash 检查结果：

```text
v0.94\rtl\laser_lock_core.sv
  == redpitaya_laser_lock_project\rtl\laser_lock_core.sv

v0.94\rtl\output_protect.sv
  == redpitaya_laser_lock_project\rtl\output_protect.sv
```

因此内容目前一致，但路径仍要在 Vivado 中人工确认。

## 4. 信号链路审查表

| 检查项 | 文件 | 关键信号/代码 | 当前判断 | 是否通过 | 风险 |
|---|---|---|---|---|---|
| `adc_dat_i[0]` 是否进入 `adc_dat[0]` | `rtl\red_pitaya_top.sv` | `adc_dat_raw[0] = adc_dat_i[0][15:2]`，`adc_dat[0] <= ... converted adc_dat_raw[0]` | 代码上成立，经过官方 negative-slope 转换后进入 `adc_dat[0]` | 通过 | 物理 IN1 是否确实对应 `adc_dat_i[0]` 仍需示波器确认 |
| `adc_dat_i[1]` 是否进入 `adc_dat[1]` | `rtl\red_pitaya_top.sv` | `adc_dat_raw[1] = adc_dat_i[1][15:2]`，`adc_dat[1] <= ... converted adc_dat_raw[1]` | 代码上成立，经过官方 negative-slope 转换后进入 `adc_dat[1]` | 通过 | 物理 IN2 是否确实对应 `adc_dat_i[1]` 仍需示波器确认 |
| `adc_dat[0]` 是否连接 `laser_lock_core.pd_i` | `rtl\red_pitaya_top.sv` | `.pd_i(adc_dat[0])` | 已连接 | 通过 | 若 Vivado 未使用此 top，则需要人工确认 |
| `adc_dat[1]` 是否连接 `laser_lock_core.ref_i` | `rtl\red_pitaya_top.sv` | `.ref_i(adc_dat[1])` | 已连接 | 通过 | 若 Vivado 未使用此 top，则需要人工确认 |
| `OUTPUT_MODE=0` 是否选择 `pd_i` | `laser_lock_core.sv` | `0: selected_signal = pd_i;` | 逻辑正确 | 通过 | `OUTPUT_MODE` 是编译期参数，不能运行时切换 |
| `OUTPUT_MODE=1` 是否选择 `ref_i` | `laser_lock_core.sv` | `1: selected_signal = ref_i;` | 逻辑正确 | 通过 | 从 IN1 测试切到 IN2 测试必须重新生成 bitstream |
| `output_protect` 是否可能导致输出恒为 0 | `output_protect.sv` / `laser_lock_core.sv` | `enable_i(1'b1)`；`if (!rstn_i) data_o<=0; else if (!enable_i) data_o<=0; else data_o<=data_i;` | 正常工作时不会因 enable 恒为 0 导致输出恒为 0；reset 未释放时会输出 0 | 通过 | 若 `adc_rstn` 未释放或 PLL 未锁定，输出会保持 0 |
| `error_o` 是否进入 `laser_error` | `rtl\red_pitaya_top.sv` | `.error_o(laser_error)` | 已连接 | 通过 | 仍需确认实际 top 是该文件 |
| `laser_error` 是否进入 `dac_a_sum_laser` | `rtl\red_pitaya_top.sv` | `assign dac_a_sum_laser = {laser_error[13], laser_error};` | 已符号扩展到 15-bit | 通过 | 输出幅度和极性仍需示波器确认 |
| `dac_a_sum_laser` 是否进入 `dac_a_sum` | `rtl\red_pitaya_top.sv` | `assign dac_a_sum = USE_LASER_LOCK_CORE ? dac_a_sum_laser : dac_a_sum_official;` | 当 `USE_LASER_LOCK_CORE=1'b1` 时进入 `dac_a_sum` | 通过 | 若误用 `USE=0` 旧 bitstream，则不会走 laser path |
| `dac_a_sum` 是否经过官方 DAC saturation / conversion | `rtl\red_pitaya_top.sv` | `assign dac_a = saturation(dac_a_sum)`；`dac_dat_a <= {dac_a[13], ~dac_a[12:0]}` | 继续经过官方 saturation 和 signed-to-unsigned / negative-slope conversion | 通过 | 波形可能反相、幅度不同，这是预期风险 |
| `dac_dat_o` 是否最终输出到 DAC A / OUT1 | `rtl\red_pitaya_top.sv` | `ODDR oddr_dac_dat ... .D1(dac_dat_b), .D2(dac_dat_a)` | 代码进入官方 ODDR DAC 输出结构 | 部分通过 | DAC A 是否物理对应 OUT1、D1/D2 时序对应关系，需要通过板级示波器确认 |

## 5. 参数与开关审查

### `USE_LASER_LOCK_CORE`

当前开发 top：

```text
localparam logic USE_LASER_LOCK_CORE = 1'b1;
```

判断：通过。当前 top 代码启用 `laser_lock_core` 路径。

风险：如果加载了旧的 `USE=0` bitstream，则 OUT1 仍走官方 ASG/PID 路径，不是 v1ab 测试 bit。

### `LASER_LOCK_OUTPUT_MODE`

当前开发 top：

```text
localparam int LASER_LOCK_OUTPUT_MODE = 0;
```

判断：当前 bitstream 目标应是 `IN1 -> OUT1`。

风险：这不是 `IN2 -> OUT1` bit。测试 IN2 前必须改为 1 并重新完整生成和加载。

### `OUTPUT_MODE` 是编译期参数还是运行时可切换

`laser_lock_core.sv` 中：

```text
parameter int OUTPUT_MODE = 0
```

判断：这是编译期参数，不是运行时寄存器，不支持上板后用 SSH 命令切换。

从 `IN1 -> OUT1` 切到 `IN2 -> OUT1` 必须：

```text
LASER_LOCK_OUTPUT_MODE = 1
Run Synthesis
Run Implementation
Generate Bitstream
转 .bit.bin
scp 上传
fpgautil 加载
```

### `output_protect` 的 `enable_i` 和 `rstn_i`

`enable_i` 在 `laser_lock_core.sv` 中固定为：

```text
enable_i(1'b1)
```

判断：不会因为 enable 未打开而恒为 0。

`rstn_i` 来自 top 的 `adc_rstn`。`adc_rstn` 由 `frstn[0] & pll_locked` 生成。

判断：设计合理。

风险：如果 PLL 未锁定或系统 reset 未释放，`output_protect` 会输出 0。上板如果 OUT1 为 0，需要把 reset/PLL/bitstream 加载也纳入排查。

### `control_o`

`laser_lock_core.sv` 中：

```text
assign control_o = 14'sd0;
```

判断：通过。当前 v1ab 不做 PID，`control_o` 固定为 0。

### DAC B / OUT2 当前路径

当前开发 top：

```text
assign dac_b_sum = dac_b_sum_official;
```

判断：DAC B 保持官方 ASG + PID 路径，不由 `laser_control` 控制，也没有被 v1ab 强制清零。

风险：

- `laser_control` 当前没有接入 DAC B；
- OUT2 不是当前 REF 直通判断依据；
- 不能期待 `IN2 -> OUT2`；
- 如果官方 ASG/PID 对 OUT2 有配置，OUT2 可能不是 0。明天测试不应把 OUT2 当作 v1ab 通过/失败标准。

### 是否存在 OUT2 被强制清零或异常改动风险

当前开发 top 中 DAC B 保持官方路径，未见 `USE_LASER_LOCK_CORE ? 15'sd0 : ...` 的强制清零写法。

但项目资料库中的 `red_pitaya_top_laser.sv` 历史变体中存在旧式 DAC B mux 写法，需要避免误用。

结论：当前 `rtl\red_pitaya_top.sv` 风险较低；若 Vivado 误用 `red_pitaya_top_laser.sv`，需要人工确认。

## 6. Vivado 工程风险

### 当前 top 是否应该是 `red_pitaya_top.sv`

`.xpr` 中 top module 为：

```text
TopModule = red_pitaya_top
```

`.xpr` active source 中有：

```text
<File Path="$PPRDIR/../rtl/red_pitaya_top.sv">
```

判断：从 `.xpr` 文本看，当前 top 应该是：

```text
E:\new\fpga_lock\v94\v0.94\rtl\red_pitaya_top.sv
```

仍需人工确认：Vivado GUI 中 `red_pitaya_top.sv` 是否为实际 top，且没有被手动切换。

### 是否存在 `red_pitaya_top_laser.sv` 与 `red_pitaya_top.sv` 混用风险

存在。

项目资料库中有：

```text
E:\new\fpga_lock\v94\v0.94\redpitaya_laser_lock_project\rtl\red_pitaya_top_laser.sv
```

它的 module 名是：

```text
red_pitaya_top_laser
```

不是 `.xpr` 当前 top module `red_pitaya_top`。

判断：当前 `.xpr` 未显示使用该文件作为 top，但该文件存在历史混淆风险。

需要人工确认：Vivado Sources 中不要把 `red_pitaya_top_laser.sv` 设为 top。

### 是否存在两个 rtl 目录重复文件但内容不同的风险

存在路径风险，但当前核心文件内容一致。

检查结果：

```text
v0.94\rtl\laser_lock_core.sv
  与 redpitaya_laser_lock_project\rtl\laser_lock_core.sv SHA256 相同

v0.94\rtl\output_protect.sv
  与 redpitaya_laser_lock_project\rtl\output_protect.sv SHA256 相同
```

但是 `.xpr` 实际 source 指向：

```text
E:\new\fpga_lock\v94\v0.94\rtl\laser_lock_core.sv
E:\new\fpga_lock\v94\v0.94\rtl\output_protect.sv
```

不是用户重点审查清单中的项目资料库路径。

结论：需要人工确认。

### 是否存在 `.sv` 文件没有加入 Vivado Sources 的风险

从 `.xpr` 文本看，`laser_lock_core.sv` 和 `output_protect.sv` 已加入 synthesis / implementation / simulation：

```text
$PPRDIR/../rtl/laser_lock_core.sv
$PPRDIR/../rtl/output_protect.sv
```

判断：文本检查通过。

需要人工确认：Vivado GUI 中 `Design Sources` 是否实际显示这两个文件，且没有黄色/灰色 disabled 状态。

### 是否存在 bitstream 不是当前代码生成的风险

存在。

原因：

- `.bit.bin` 是外部生成/上传/加载产物；
- 本次只静态审查文件，没有运行 Vivado；
- 无法从代码文件本身证明板上当前 FPGA 仍是最新 bitstream；
- Red Pitaya 断电/重启或打开官方网页应用可能覆盖 FPGA。

需要人工确认：

```text
当前板子是否仍然加载目标 red_pitaya_top.bit.bin
当前 bit.bin 是否来自 USE_LASER_LOCK_CORE=1, LASER_LOCK_OUTPUT_MODE=0 的 bitstream
```

### 是否存在 `USE=0` 旧 bitstream 被误用风险

存在。

如果误用 `USE_LASER_LOCK_CORE=0` 的 bitstream，则 `laser_error` 不会进入 DAC A，无法测试 v1ab passthrough。

### 是否存在 `OUTPUT_MODE=0/1` 混淆风险

存在。

当前 top 是：

```text
LASER_LOCK_OUTPUT_MODE = 0
```

它只适合：

```text
IN1 -> OUT1
```

如果明天直接拿同一个 bit 去测 `IN2 -> OUT1`，会失败或看不到预期 REF 直通。

## 7. 仿真覆盖范围

`tb_laser_lock_core_v1ab.sv` 已验证：

- `OUTPUT_MODE=0: pd_i -> error_o`；
- `OUTPUT_MODE=1: ref_i -> error_o`；
- reset 后 `error_o` 输出为 0；
- enable 后输出正常，因为 `output_protect` 在 reset 释放后透传；
- `control_o` 为 0；
- 正数、负数、0 输入组合均有覆盖。

关键证据：

```text
OUTPUT_MODE(0)
OUTPUT_MODE(1)
check_reset_outputs
drive_and_check
check_controls_zero
V1AB PASSTHROUGH DEBUG TEST PASSED
```

同时必须明确，它没有验证：

- ADC 物理输入；
- `adc_dat_i -> adc_dat_raw -> adc_dat` 的完整 top 级物理链路；
- 完整 `red_pitaya_top.sv`；
- DAC A saturation / conversion / ODDR 的物理输出；
- OUT1 BNC；
- OUT2 BNC；
- 4.6 MHz 真实输入；
- Red Pitaya 当前 bitstream 是否仍在板上；
- 示波器接线和幅度安全。

结论：testbench 对 `laser_lock_core` 单模块足够有用，但不能替代明天的示波器物理测试。

## 8. 明天上板测试建议

只允许建议以下两项：

### Step 1：`IN1 -> OUT1`

当前 `LASER_LOCK_OUTPUT_MODE = 0`，建议先测：

```text
信号发生器 OUT -> Red Pitaya IN1
Red Pitaya OUT1 -> 示波器 CH1
信号发生器 OUT -> 示波器 CH2

1 kHz sine
100 mVpp
0 V offset
```

通过标准：

- CH2 能看到输入参考；
- CH1/OUT1 能看到同频 1 kHz 波形；
- 幅度可以不同；
- 可以反相；
- 不应长期顶死或严重削顶。

### Step 2：`IN2 -> OUT1`

只有 Step 1 通过后才做。

必须重新设置：

```text
LASER_LOCK_OUTPUT_MODE = 1
```

并重新：

```text
Run Synthesis
Run Implementation
Generate Bitstream
转 .bit.bin
scp 上传
fpgautil 加载
```

接线：

```text
4.6 MHz REF 安全幅度 -> Red Pitaya IN2
Red Pitaya OUT1 -> 示波器 CH1
REF 同时 -> 示波器 CH2
```

信号：

```text
4.6 MHz sine
100 mVpp 到 500 mVpp 起步
0 V offset
严禁 6.32 Vpp 直接进 IN2
不要第一次就直接 ±1 V
```

不允许建议：

- `IN2 -> OUT2`；
- `OUT1` 接 `D2-125`；
- `OUT1` 接激光器反馈；
- Red Pitaya 驱动 EOM；
- 直接进入 mixer；
- 用 OUT2 作为 REF 直通判断依据。

## 9. 必须人工确认的问题

以下内容必须人工确认：

1. Vivado GUI 中 `Design Sources` 实际启用的 `laser_lock_core.sv` 是否是：

```text
E:\new\fpga_lock\v94\v0.94\rtl\laser_lock_core.sv
```

而不是其他路径。

2. Vivado GUI 中 `Design Sources` 实际启用的 `output_protect.sv` 是否是：

```text
E:\new\fpga_lock\v94\v0.94\rtl\output_protect.sv
```

而不是其他路径。

3. 当前 Vivado top 是否确实是：

```text
red_pitaya_top
E:\new\fpga_lock\v94\v0.94\rtl\red_pitaya_top.sv
```

4. 是否没有误用：

```text
E:\new\fpga_lock\v94\v0.94\redpitaya_laser_lock_project\rtl\red_pitaya_top_laser.sv
```

5. 当前板上已加载的 `.bit.bin` 是否确实来自：

```text
USE_LASER_LOCK_CORE = 1'b1
LASER_LOCK_OUTPUT_MODE = 0
```

6. Red Pitaya 是否在加载 bitstream 后断电、重启，或打开过可能覆盖 FPGA 的官方网页应用。

7. DAC A 是否物理对应 `OUT1`，DAC B 是否物理对应 `OUT2`。代码和文档候选判断是这样，但最终以示波器为准。

8. IN1/IN2 与 `adc_dat[0]/adc_dat[1]` 的物理对应关系是否与代码候选一致。必须通过 `IN1 -> OUT1` 和 `IN2 -> OUT1` 实验确认。

9. Red Pitaya 当前输入量程、跳线/设置、信号发生器 50 ohm/Hi-Z 幅度标定是否安全。

10. `IN2` 的 4.6 MHz REF 是否已经衰减到安全范围，且不是原模拟 mixer 的 `6.32 Vpp` 直接输入。

## 10. 最终建议

下一步最小动作：

```text
保持当前 OUTPUT_MODE=0 bitstream。
确认板子仍加载目标 bit.bin。
信号发生器输出先在示波器 CH2 看见 1 kHz / 100 mVpp / 0 V offset。
再接 Red Pitaya IN1。
OUT1 接示波器 CH1。
观察 OUT1 是否有 1 kHz 同频波形。
记录幅度、极性、是否削顶、是否顶死。
```

如果 `IN1 -> OUT1` 通过，再准备 `OUTPUT_MODE=1` 的新 bitstream，测试 `IN2 -> OUT1`。

最终建议：

```text
当前 v1ab 代码链路“部分可以”，适合进入明天的 IN1 -> OUT1 候选上板测试。
但不允许进入 v1c。
必须先完成 v1ab IN1->OUT1 和 IN2->OUT1 的真实示波器验证。
```

本次审查限制已遵守：

- 未修改代码；
- 未移动文件；
- 未删除文件；
- 未复制文件；
- 未生成新 RTL；
- 未实现 mixer；
- 未实现 LPF；
- 未实现 PID；
- 未做 AI；
- 未声称 v1 已完成。
