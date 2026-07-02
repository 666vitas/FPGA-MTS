# V2 实验 SOP

## 当前总规则：中文 SOP 和小白实验边界

本文档面向小白实验用户，默认使用中文表达；文件路径、RTL 模块名、信号名、寄存器名和 Vivado timing 术语保留英文原名。

每个实验阶段都必须写清：

```text
目标
接线
正常现象
停止条件
通过标准
是否允许烧录
是否允许接激光器
是否允许接 Scan/PZT
保存哪些数据
```

## 当前允许接线

```text
Red Pitaya IN1 <- PD + BPF + Amp，必须在 +/-1 V 内
Red Pitaya IN2 <- REF，必须在 +/-1 V 内
Red Pitaya OUT1 -> 示波器，或后续在专门 SOP 下接 D2-125 Error Input
Red Pitaya OUT2 -> 示波器
```

## 当前禁止接线

```text
OUT2 不能接激光器
OUT2 不能接 D2-125 Servo Output 三通
OUT2 不能接激光器电源 Scan / PZT
OUT2 不能和 D2-125 输出并联
D2-125 DC Error 不能接 Red Pitaya IN1
IN1 / IN2 不能超过 +/-1 V
```

## 2026-07-02 v2B3_scope_safe 示波器复测 SOP

本 SOP 覆盖最新 `only-pi.csv` 后的下一次实验。由于本次 OUT2 长期贴在约 `-0.2 V` 附近，v2B3 不能关闭，也不能进入真实反馈测试。

### v2B3_scope_safe 通过标准和 only-p.csv 结论

PASS 条件：

```text
OUT1 error 正常；
OUT2 不贴 -0.2 V；
OUT2 不贴 output_limit；
OUT2 不随机跳变；
OUT2 不快速饱和；
OUT2 不接近 +/-1 V；
OUT2 / OUT1 比例可解释；
OUT2 只接示波器。
```

本次 `only-p.csv` 满足这些条件，记录为：

```text
PASS WITH NOTES
```

本次关键数据：

```text
OUT1 / CH1:
Vpp ≈ 0.04874 V
min ≈ -0.01209 V
max ≈ +0.03665 V
RMS ≈ 0.01007 V
mean ≈ +0.00868 V

OUT2 / CH4:
Vpp ≈ 0.02410 V
min ≈ -0.00177 V
max ≈ +0.02233 V
RMS ≈ 0.00888 V
mean ≈ +0.00850 V
OUT2 / OUT1 Vpp ≈ 0.494
```

说明：

```text
Ki=0 修正有效。
OUT2 不再贴 -0.2 V。
OUT2 仍只能接示波器。
这不是闭环锁定，也不代表 FPGA 已经替代 D2-125。
```

### 本次 only-pi 结论

```text
OUT1 正常：
Board OUT1 / CH1 能看到 FPGA mixer + LPF 后的 error-like 信号。
Vpp ≈ 0.05385 V，min ≈ -0.02714 V，max ≈ +0.02671 V，RMS ≈ 0.009618 V。

OUT2 未通过：
Board OUT2 / CH4 长期贴在约 -0.2 V 附近。
Vpp ≈ 0.01497 V，min ≈ -0.2036 V，max ≈ -0.1886 V，RMS ≈ 0.1991 V，mean ≈ -0.199 V。
```

可能原因：

```text
OUT1 error 存在 DC 偏置或平均误差；
PID_KI_DEFAULT 当前非零；
积分器在一段时间内累积同号误差；
control_o 被推到负向 output_limit；
导致 OUT2 动态范围只剩约 15 mVpp。
```

### v2B3_scope_safe 修正含义

下一版只做安全收敛，不增加新功能：

```text
CONTROL_PATH_MODE=1 仍然使用 pi_controller_seq。
OUTPUT_MODE=3 仍然让 OUT1 显示 mixer + LPF error。
PID_KI_DEFAULT = 16'sd0。
PID_OUTPUT_LIMIT_DEFAULT = 14'd819，约 +/-0.10 V。
```

专业说法：
本轮关闭 I 项并降低 `output_limit`，用 `pi_controller_seq` 的 P 路径先证明 OUT2 可解释、可限幅、不贴边。

小白理解：
先把会慢慢累积的那一部分刹住，只看 OUT2 能不能跟着 OUT1 小幅变化，不要再一直靠在负边界。

在本项目中的对应关系：
OUT1 继续看 error，OUT2 继续只接示波器，下一次只判断 `Ki=0` 后 OUT2 是否离开 `-0.2 V` 附近。

如果做错的风险：
如果 OUT2 仍贴 limit 或随机跳变，说明还不能接任何真实控制端。

### 用户手动 Vivado 步骤

Codex 不运行 Vivado。用户手动执行：

```text
1. 用户手动打开 Vivado。
2. 确认 red_pitaya_top 是 Design Top。
3. 确认 pi_controller_seq.sv 在 Design Sources。
4. 确认 tb_*.sv 不在 Design Sources。
5. Run Synthesis。
6. Run Implementation。
7. 检查 WNS >= 0，TNS = 0，Failing Endpoints = 0。
8. timing 通过后才 Generate Bitstream。
9. 生成 bit/bin 后烧录 Red Pitaya。
```

### 复测接线

只允许：

```text
Red Pitaya IN1 <- PD + BPF + Amp 后的 MTS/PD 信号，必须在 +/-1 V 内
Red Pitaya IN2 <- 外部 REF，必须在 +/-1 V 内
OUT1 -> 示波器 CH1 或 CH2
OUT2 -> 示波器 CH4
```

禁止：

```text
OUT2 -> 激光器
OUT2 -> D2-125 Servo Output
OUT2 -> D2-125 Aux Output
OUT2 -> Scan/PZT
OUT2 与任何 D2-125 输出并联
CH3 外部 D2-125 / analog error 直接进入 Red Pitaya IN1/IN2
```

### 正常现象

```text
OUT1 仍然是 FPGA mixer + LPF error。
OUT1 波形应与 only-pi.csv 中 CH1 类似。
OUT1 Vpp 可以是几十 mV 量级。
OUT1 不应消失。
OUT1 不应明显削顶。

OUT2 不应再长期贴在 -0.2 V 附近。
OUT2 应围绕 0 V 附近小幅变化，或至少不应长期贴近 output_limit。
OUT2 应跟随 OUT1 error 的变化趋势。
因为 Ki=0，OUT2 不应发生积分导致的慢慢爬升。
OUT2 不应随机跳变。
OUT2 不应快速饱和。
OUT2 不应接近 +/-1 V。
如果 output_limit=819，则 OUT2 不应超过约 +/-0.10 V。
```

### 异常判断和停止条件

```text
如果 OUT2 仍贴在负向 limit：
可能存在 offset_i、polarity、error DC 偏置、符号处理或 pi_controller_seq 状态问题。

如果 OUT2 严格等于 OUT1 的一半：
说明当前可能退回到 CONTROL_PATH_MODE=0 P-only fallback，需检查 top 参数是否实际为 mode=1。

如果 OUT2 始终为 0：
可能 CONTROL_PATH_MODE 没生效、pi_controller_seq.sv 未加入 Design Sources、reset/enable 问题或顶层未重新综合。

如果 OUT2 随机跳：
停止，检查时序、未初始化寄存器、CDC 或 reset。

如果 OUT1 消失：
停止，说明 error 链路被破坏，不能继续。
```

### 保存数据

```text
Vivado timing 截图
OUT1/OUT2 示波器截图
CSV 数据
文件命名建议：v2b3_scope_safe_ki0_limit819.csv
```

### v2B3 关闭条件

只有当 `v2B3_scope_safe` 满足以下条件，才可以关闭 v2B3：

```text
1. timing 通过；
2. OUT1 error 正常；
3. OUT2 不再贴 limit；
4. OUT2 不随机跳变；
5. OUT2 不接近 +/-1 V；
6. OUT2 行为能用 Ki=0 的 P-only through pi_controller_seq 解释；
7. 所有数据已保存。
```

v2B3 关闭后，才讨论 v2D / v2E 或后续 v2PZT。

## 当前阶段统一结论

```text
是否允许烧录：只有用户手动 Vivado timing 通过并确认后才允许。
是否允许接激光器：当前默认不允许。
是否允许接 Scan/PZT：当前默认不允许。
OUT2 当前状态：只允许接示波器。
当前能否声称锁定：不能。当前还不是 FPGA 独立真实激光闭环。
必须保存的数据：示波器截图、CSV、Vivado timing、bitstream 对应源码/参数记录。
```

## 2026-07-02 Aux/PZT 实测数据记录后的实验边界

最新 Aux/PZT 数据确认：D2-125 Aux Output 在 Ramp / Unlock 状态约为 `0.81 V DC offset + 0.063~0.117 Vpp triangle`，主频约 `52.7 Hz`；在 Lock 状态约为 `0.813 V hold + 0.0169 Vpp residual / slow correction`。

这些数据只作为后续 v3/v4/v5 的设计参考。当前阶段不能因为测得 Aux 数据就直接把 OUT2 接 Scan/PZT。

### 当前禁止执行

```text
禁止把当前 OUT2 直接接 Scan/PZT。
禁止把 Red Pitaya OUT2 和 D2-125 Aux Output 并联。
禁止把 Red Pitaya OUT2 和 D2-125 Servo Output 并联。
禁止把当前 sequential PI candidate 说成已经实现 PZT 锁定。
```

### 未来 Scan/PZT 替代前必须检查

```text
1. Scan/PZT 输入允许电压范围；
2. Red Pitaya OUT2 输出范围；
3. scan_offset 是否需要 0.81 V 附近；
4. scan_amp 是否从 0.03 V 起步；
5. scan_freq 是否约 52.7 Hz；
6. Vlock 初始范围是否在 0.80~0.82 V 附近；
7. slow output limit 是否参考 0.0169 Vpp 的 Lock 状态扰动；
8. D2-125 Aux Output 是否已断开；
9. OUT2 是否会和 D2-125 Aux Output 并联；
10. OUT2 是否会和 D2-125 Servo Output 并联。
```

### v2PZT-1 首次目标

只实现并验证：

```text
SAFE: OUT2 = 0
SCAN: OUT2 = scan_offset + triangle
HOLD: OUT2 = captured_vlock
```

第一轮示波器参数建议：

```text
scan_offset 约 0.81 V
scan_amp 约 0.03 V
scan_freq 约 52.7 Hz
```

### 后续真正接 Scan/PZT 前的顺序

```text
1. OUT2 先只接示波器，验证 SAFE = 0。
2. OUT2 只接示波器，验证 SCAN = 0.81 V offset + 小三角波。
3. OUT2 只接示波器，验证 HOLD = captured_vlock。
4. 确认 OUT2 始终在 +/-1 V 内。
5. 确认 D2-125 Aux Output 已从激光器 Scan/PZT 断开。
6. 只允许 Red Pitaya OUT2 或 D2-125 Aux Output 其中一个连接 Scan/PZT，不能并联。
7. 首次 Red Pitaya OUT2 -> Scan/PZT 只做开环扫谱，不做 P_LOCK / PI_LOCK。
8. 扫谱确认后，才进入 P_LOCK，且 Ki=0、Kp 很小、output_limit 很小。
9. P_LOCK 方向确认后，才允许考虑 PI_LOCK。
```

### 立即停止条件

```text
OUT2 接近 +/-1 V。
OUT2 不是预期的 0.81 V offset + 小三角波。
Scan/PZT 上同时接了 Red Pitaya OUT2 和 D2-125 Aux Output。
OUT2 和 D2-125 Servo Output 有任何并联风险。
谱线扫描方向不明确。
P_LOCK 后出现发散、跳变、饱和或拉飞锁点。
```

## 2026-06-30 v2B3 timing clean 与首次 scan/lock SOP 边界

用户手动 Vivado Implementation 时序记录：

```text
WNS = +0.107 ns
TNS = 0.000 ns
Failing Endpoints = 0
WHS = 0.054 ns
THS = 0
结论：mode=1 sequential PI 候选版本 timing clean。
```

这个结果只说明当前 `mode=1 sequential PI` 候选版本通过了时序。
它不代表激光已经锁定，也不代表允许把 OUT2 接到激光器、D2-125 Servo Output、
D2-125 Aux/Scan 或任何真实执行器。

当前允许的检查：

```text
OUT1 -> 示波器：观察 FPGA laser_error / error observation。
OUT2 -> 示波器：观察 FPGA laser_control / sequential PI 候选输出。
```

未来首次 scan/lock 实验 SOP。注意：只有在 register/mode RTL 已实现、
并且另行确认可以进入该阶段后，才执行下面步骤：

```text
1. IN1 <- PD BPF/amp 信号，确认不超过 +/-1 V。
2. IN2 <- REF 信号，确认不超过 +/-1 V。
3. OUT1 -> 示波器 CH2：观察 FPGA error。
4. OUT2 -> 示波器 CH4：此时仍然不要接激光器。
5. SAFE：确认 OUT2 = 0。
6. SCAN：确认 OUT2 上有小幅三角波。
7. 断开 D2-125 Aux Servo Output 到激光器 Scan 的连接。
8. 只有完成第 7 步后，才允许考虑 RP OUT2 -> laser power Scan/PZT。
9. 确认能看到光谱扫描。
10. 在接近过零点的位置执行 Capture Vlock。
11. HOLD。
12. 后续经过复核后，再进入 P_LOCK，然后才是 PI_LOCK。
```

出现以下情况立即停止：

```text
IN1/IN2 超过 +/-1 V。
OUT1 异常消失或异常饱和。
OUT2 超过 output_limit，或接近 +/-1 V。
OUT2 随机跳变、异常爬升，或控制方向不明确。
考虑连接 RP OUT2 时，D2-125 Aux/Scan 仍然连接在激光器上。
```

> Active baseline: only the GitHub project `666vitas/FPGA-MTS` `v0.94` mainline plus `version/v2` documentation are valid. Do not read, reference, sync, copy, or modify any `weifang` or `version-weifang` directory for this route.

## 0. Current real D2-125 wiring model

Current analog optical and error chain:

```text
Laser
-> Rb / MTS optical path
-> PD
-> analog band-pass filter
-> Mini-Circuits RF amplifier
-> analog mixer x 4.6 MHz REF
-> MTS error
-> D2-125 Error Input
```

D2-125 practical states:

```text
Ramp
Unlock
Lock
```

Ramp state:

```text
D2-125 Auxiliary Servo Output
-> laser power supply Scan / PZT
-> triangular scan
-> sweep saturated absorption / MTS spectrum
```

Ramp is for finding peaks, observing the spectrum, and locating candidate lock points. It is not closed-loop locking.

Unlock state:

```text
D2-125 does not close the loop.
The user manually adjusts laser current, temperature, interference-filter angle, Scan offset, and optics.
Outputs should be treated as open-loop or safe-state outputs.
```

Lock state:

```text
MTS error
-> D2-125 Error Input
-> D2-125 internal PI/PID
-> Servo Output
-> tee splitter
   |-> laser power supply: slow current feedback
   `-> potentiometer gain adjust -> interference-filter laser: fast current feedback
```

The Servo Output is one main PID current-feedback signal. The tee splits the same voltage into two current-feedback branches. The potentiometer adjusts the fast branch gain; it does not change the feedback type.

Aux Servo Output in Lock state:

```text
D2-125 Auxiliary Servo Output
-> laser power supply Scan / PZT
-> auxiliary PI / slow Scan-PZT control
-> maintain lock center and compensate slow drift
```

## 1. Current allowed Red Pitaya wiring

Current active FPGA mainline:

```text
IN1 + IN2
-> mixer_core
-> lpf_core
-> output_protect
-> error_o
-> OUT1

same error_o / protected_error
-> pi_controller or pi_controller_seq
-> control_o
-> OUT2
```

Allowed current wiring:

```text
Red Pitaya IN1 <- PD + BPF + amplifier, within +/-1 V.
Red Pitaya IN2 <- external REF, within +/-1 V.
Red Pitaya OUT1 -> oscilloscope, or later D2-125 Error Input after a dedicated SOP.
Red Pitaya OUT2 -> oscilloscope only.
```

Current meanings:

```text
OUT1 = FPGA mixer+LPF error observation.
OUT2 = FPGA control candidate / shadow control / sequential PI candidate.
```

## 2. Current forbidden wiring

```text
OUT2 must not connect to the laser.
OUT2 must not connect to the D2-125 Servo Output tee.
OUT2 must not connect to the laser power supply Scan / PZT.
OUT2 must not be paralleled with any D2-125 output.
D2-125 DC Error must not be used as Red Pitaya IN1.
D2-125 Servo Output must not be used as Red Pitaya IN1.
IN1/IN2 must never exceed +/-1 V.
```

The current FPGA has not fully replaced D2-125 and has not independently completed a real laser closed loop.

## 3. v2B3 sequential PI oscilloscope SOP

Purpose:

```text
Verify that mode=1 sequential PI is timing-clean and safe on OUT2 while OUT2 is still connected only to the oscilloscope.
```

Pre-board checks:

```text
1. Confirm only v0.94 mainline sources are used.
2. Confirm red_pitaya_top is the Design Top.
3. Confirm pi_controller_seq.sv is in Design Sources.
4. Confirm tb_*.sv files are not in Design Sources.
5. Run Synthesis and Implementation manually.
6. Timing must pass: WNS >= 0 and TNS = 0.
7. Only after timing passes, Generate Bitstream.
```

Scope wiring:

```text
OUT1 -> CH2
OUT2 -> CH4
```

Normal phenomena:

```text
OUT1/CH2: FPGA mixer+LPF error remains visible.
OUT2/CH4: sequential PI candidate follows the error trend.
OUT2 may look close to P-only over a short time.
Small Ki may produce slow baseline movement only when same-sign error persists.
OUT2 remains limited and does not approach +/-1 V.
```

Stop conditions:

```text
OUT1 disappears.
OUT2 remains zero when mode=1 is expected.
OUT2 is exactly OUT1/2, suggesting fallback mode still active.
OUT2 randomly jumps.
OUT2 rapidly climbs or saturates.
OUT2 approaches +/-1 V.
Vivado timing fails.
Any attempt is made to connect OUT2 to laser, Servo Output, Aux Output, Scan/PZT, or current feedback.
```

Passing v2B3 does not mean the FPGA has locked the laser. It only means the OUT2 control candidate is safe enough to continue staged development.

## 4. Future OUT1 -> D2-125 Error Input SOP boundary

A later stage may test:

```text
FPGA OUT1 error
-> D2-125 Error Input
```

Purpose:

```text
Use FPGA mixer+LPF to replace the analog error-generation chain while D2-125 still performs the real lock.
```

Preconditions:

```text
OUT1 amplitude and offset are measured.
D2-125 Error Input range is confirmed.
OUT1 does not clip or disappear.
A quick rollback to the analog mixer error is available.
OUT2 remains on the oscilloscope only.
```

This test must not be confused with FPGA independent locking.

## 5. Future v2F low-gain single-branch closed-loop safety check

v2F is not a full D2-125 replacement. It is only a first low-gain single-branch real actuator test.

Before v2F, confirm:

```text
1. Which single actuator branch is being tested.
2. The D2-125 output is disconnected from that same terminal.
3. Red Pitaya OUT2 voltage range is safe for that input.
4. Feedback polarity is known or starts with a reversible low-gain test.
5. The potentiometer / feedback gain is initially low.
6. Kp is small.
7. Ki is zero at first.
8. output_limit is small.
9. enable defaults to safe/off where appropriate.
10. reset drives OUT2 to a documented safe value.
11. The user can immediately disconnect or return to D2-125.
```

Allowed v2F concept:

```text
Red Pitaya OUT2 -> one selected real feedback branch only
```

Forbidden v2F concept:

```text
Red Pitaya OUT2 -> fast current + slow current + Aux/Scan simultaneously
Red Pitaya OUT2 paralleled with D2-125 Servo Output
Red Pitaya OUT2 paralleled with D2-125 Aux Servo Output
```

## 6. Future v3 / v4 / v5 boundary

v3 begins the replacement of D2-125 workflow functions:

```text
ramp_generator
scan_lock_fsm
Ramp / Unlock / Lock state switching
Aux Servo Output replacement
slow Scan/PZT control
relock
lock quality judgment
```

v4/v5 are for host and AI:

```text
host spectrum selection
automatic peak recognition
AI / 1D-CNN peak recognition
Kp/Ki suggestions
lock/unlock judgment
automatic Rescan decision
```

AI is not the high-speed PID loop. The FPGA remains responsible for real-time mixer, LPF, PI/PID candidate, output limiting, and reset-safe actuator outputs.

## 7. Data to save after each experiment

For every experiment, save:

```text
Vivado timing screenshot or report if bitstream was generated.
Bit/bin source commit or file version.
Oscilloscope screenshot.
CSV waveform data.
Exact wiring photo or text record.
IN1/IN2 voltage range.
OUT1/OUT2 Vpp, RMS, offset.
Whether OUT2 was oscilloscope-only or connected to an actuator.
Pass / stop decision.
```

## 8. Historical notes

Older SOP sections that describe `D2-125 DC Error -> Red Pitaya IN1`, full direct D2 replacement, or simultaneous multi-branch actuator connection are historical only and must not be executed as the current route.
