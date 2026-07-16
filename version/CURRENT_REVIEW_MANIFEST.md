# CURRENT_REVIEW_MANIFEST

本文件定义当前 GitHub `main` 分支的审查清单。AI 审查时必须先读本文件，再审查当前 RTL、上位机和实验记录。

## 1. 仓库与主线

```text
Repository: 666vitas/FPGA-MTS
Primary branch: main
Current stage: v3LOCK-P0 / Stage 3 Hardware Verification
Current gate: HV-1 OUT2 fixed-count physical voltage calibration
Primary RTL root: v0.94/rtl
Primary Vivado project: v0.94/project/redpitaya.xpr
Primary status file: version/STATUS.md
Hardware validation record: version/HARDWARE_VALIDATION.md
Hardware calibration SOP: software/redpitaya_lock_host/docs/HARDWARE_CALIBRATION_SOP.md
Strict review rules: version/AI_STRICT_REVIEW_ENTRY.md
Root entrypoint: AI_REVIEW_README.md
Shared Codex/Claude Code rules: AGENTS.md
```

当前状态优先级：`version/STATUS.md` 顶部快照与本 Manifest 的“当前验证等级”优先于历史段落。`version/AI_STRICT_REVIEW_ENTRY.md` 目前含未解决合并标记和过期验证文字；在用户另行授权修复前，只能作为规则读取，不得将其中的旧验证结论覆盖当前快照。

当前 Git Baseline Gate：`main` clean，遗留 interactive rebase 已由用户结束，`HEAD=origin/main=0e13f2806d7a716d3e66d365babbe2b247e59d8b`；保险分支只作为恢复点，不影响 `main`。本轮不得因历史 rebase 再次尝试 rebase。

## 2. 当前结论基线

```text
OUT1 = laser_error = mixer + LPF error observation
OUT2 = selected_out2
MODE=0 SAFE
MODE=1 SCAN
MODE=2 HOLD
MODE=3 P_LOCK，下一步验证重点，当前 LOCK 目标缩小为 P-only
MODE=4 PI_LOCK，当前暂时退化为 P_LOCK，KI / integral 当前不要恢复
laser_control / pi_controller_seq = 内部候选或历史路径，不是当前 DAC B / OUT2 最终输出
```

历史 v3REG-0 的 `VERSION=0x00030000` SAFE/SCAN 记录已被后续 v3LOCK-P0 板上记录覆盖。当前已验证板端身份为 `MAGIC=0x4D545330`、`VERSION=0x00030001`；后续 `git fetch`、本地 `git rev-parse HEAD` 与用户 push 后的 GitHub `main` 用于确认代码版本，而不是把历史记录中的 commit 当作永久最新状态。

当前 OUT2 的目标执行器是激光器专用 PZT / Scan 输入。`MODE=1 SCAN` 输出三角波驱动同一个 PZT 扫描激光频率；`MODE=3 P_LOCK` 输出 `LOCK_BIAS + P correction` 驱动同一个 PZT 完成基础反馈；`MODE=0 SAFE` 退出扫描和锁定。必须默认小 Kp、小 `LOCK_CORRECTION_LIMIT`，失败必须 SAFE；禁止接入激光器电流调制、D2-125 Servo Output 或 D2-125 Aux Output，也禁止任何输出端并联。

## 3. 当前必须读取的文件

状态与规则：

```text
AI_REVIEW_README.md
AGENTS.md
version/AI_STRICT_REVIEW_ENTRY.md
version/CURRENT_REVIEW_MANIFEST.md
version/STATUS.md
version/rules/00_DOCUMENT_LANGUAGE_AND_STYLE_RULES.md
```

Vivado 工程：

```text
v0.94/project/redpitaya.xpr
```

当前 RTL：

```text
v0.94/rtl/red_pitaya_top.sv
v0.94/rtl/laser_lock_core.sv
v0.94/rtl/custom_register_bank.sv
v0.94/rtl/ramp_generator.sv
v0.94/rtl/mixer_core.sv
v0.94/rtl/lpf_core.sv
v0.94/rtl/output_protect.sv
v0.94/rtl/pi_controller_seq.sv
v0.94/rtl/pi_controller.sv
```

## 4. 默认禁止作为当前依据的路径

```text
v-weifang/**
version-weifang/**
version/v1/**
version/v2/**
v0.94/redpitaya_laser_lock_project/docs/old/**
**/old/**
**/*.before_*
**/*before*
```

这些路径只能回答历史问题，不能作为当前 main 主线结论。

## 5. 当前 RTL 审查点

### red_pitaya_top.sv

必须确认：

```text
USE_LASER_LOCK_CORE = 1
LASER_LOCK_OUTPUT_MODE = 3
LASER_LOCK_CONTROL_PATH_MODE = 1
laser_lock_core 实例化存在
custom_register_bank 实例化存在并接 sys[6]
ramp_generator 实例化存在
selected_out2 由 out2_lock_controller 根据 MODE/ENABLE 选择 SAFE / SCAN / HOLD / P_LOCK / PI_LOCK
DAC A / OUT1 接 laser_error
DAC B / OUT2 接 selected_out2
```

### custom_register_bank.sv

必须确认寄存器：

```text
MAGIC
VERSION
MODE
ENABLE
SCAN_OFFSET
SCAN_AMP
SCAN_STEP
SCAN_UPDATE_DIV
OUT2_LIMIT
STATUS
OUT2_MONITOR
HOLD_VALUE
KP
POLARITY
LOCK_BIAS
LOCK_LIMIT
ERROR_MONITOR
CONTROL_MONITOR
KI
INTEGRAL_RESET
LOCK_CORRECTION_LIMIT
ERROR_SETPOINT
LOCK_ERROR_MONITOR
CAPTURE_LOCK_POINT
CAPTURE_CTRL
CAPTURE_STATUS
CAPTURE_DECIMATION
CAPTURE_LENGTH
CAPTURE_READ_INDEX
CAPTURE_DATA_CH1
CAPTURE_DATA_CH2
CAPTURE_DATA_CH3
CAPTURE_DATA_CH4
```

必须确认默认值：

```text
mode = 0
enable = 0
offset = 6962
amp = 410
step = 1
update_div = 1524
out2_limit = 8191
hold_value = 0
kp = 0
polarity = 0
lock_bias = 0
lock_limit = 8191
ki = 0
lock_correction_limit = 128
error_setpoint = 0
capture_decimation = 1024
capture_length = 2048
```

### ramp_generator.sv

必须确认：

```text
enable=0 时 scan_o = 0
enable=1 时 scan_o = offset + triangle
amp / step / limit 有保护
输出限制在 Red Pitaya DAC 安全范围内
saturated_o 可读回
```

### laser_lock_core.sv

必须确认：

```text
OUTPUT_MODE=3 时 OUT1 为 mixer + post-mixer LPF
control_o / pi_controller_seq 仍存在，但不是当前 OUT2 的最终来源
```

## 6. 当前验证等级与工程状态

### FPGA / bitstream 已验证

```text
代码层面已经加入 custom_register_bank
代码层面已经加入 ramp_generator
代码层面已经加入 out2_lock_controller
代码层面 OUT2 已经改为 selected_out2 SAFE/SCAN/HOLD/P_LOCK/PI_LOCK 候选
代码层面已经加入 P_LOCK correction limit
代码层面已经加入 custom_debug_capture
v3LOCK-P0 synthesis / implementation / timing 已完成
对应 bitstream 已生成并由用户烧录
MAGIC = 0x4D545330
VERSION = 0x00030001
用户截图已证明 custom_debug_capture 可返回 CH1/IN1、CH2/IN2、CH3/OUT1、CH4/OUT2 四通道非零 capture 数据
当前 GUI 已可显示真实 capture 曲线；空白 plot 问题已修复
```

### 仍等待实验验证

```text
HV-1 OUT2 count=0 对应示波器真实 DC 电压
HOLD 的真实行为
LOCK HERE 的真实切换
P_LOCK 的真实 PZT 闭环效果
polarity 与小 Kp 的实验效果
长时间稳频
FSM 自动重锁
AI 参数优化
当前 GUI 的剩余问题是示波器式分层显示布局；不是 FPGA capture 数据链路失效
```

### 当前不启用

```text
KI
integral
PI_LOCK 实验主线
自动 polarity
自动增加 Kp
自动重锁
AI 自动识峰
```

纯上位机 GUI 修改判定：只要不修改 RTL、Vivado 工程、寄存器地址或寄存器语义、bitstream，就不需要重新运行 Vivado、不需要重新生成 bitstream、不需要重新烧录。GUI 显示验证与 FPGA bitstream 验证必须分开记录，不得相互替代或混写。

### 历史阶段记录（已被后续验证覆盖，不再作为当前待办）

2026-07-11 资源修复基线：`custom_debug_capture` 初版四通道 4096 深度存储曾被 Vivado 推断为 LUTRAM / RAM64M / RAM64X1D，导致 place_design `[Place 30-484]`，`LUTRAM/SRL capable slices` 超限。本次已将 `mem_ch1..mem_ch4` 标记为 `(* ram_style = "block" *)`，并把 debug capture 读路径改为同步读，读数据允许 1 个 `clk_i` 周期延迟。该“等待 Vivado 验证”的阶段结论已被后续 timing PASS、bitstream 生成与烧录、`VERSION=0x00030001` 读回及四通道非零 capture 实验覆盖，不再作为当前待办。

2026-07-11 v3LOCK-P0 人工选点基线：当前第一版不是自动识峰、不是 AI 自动锁定。禁止把 `board(1).csv` 或任何历史实验中的 `54 counts`、`0.704 V`、`0.784 V`、`49.75 Hz`、峰值、基线、扫描位置写成生产默认值或锁点配置。`VERSION=0x00030001` 的“候选仍等待 synthesis / implementation / timing / bitstream / 烧录”阶段结论，已被后续 timing PASS、bitstream、烧录、`VERSION` 读回和四通道 capture 覆盖，不再作为当前待办；`LOCK HERE` 与 `P_LOCK` 的真实 PZT 闭环效果仍属于当前待验证事项。

禁止说的内容：

```text
已经可以接激光器电流调制输入
已经可以替代 D2-125 Aux Output
已经闭环锁定
已经完成 D2-125 替代
```

除非出现明确实验记录和安全评审文件，否则不得推进这些结论。

## 7. 下一步最小安全动作

```text
1. 当前只允许 HV-1 的 count=0 单点；不得执行非零点、SCAN、LOCK HERE 或 P-only。
2. PZT 必须断开，OUT2 只能连接示波器，禁止任何有源输出并联。
3. 按 `software/redpitaya_lock_host/docs/HARDWARE_CALIBRATION_SOP.md` 执行 `Probe Registers -> Status -> SAFE -> HOLD count=0 -> readback -> CH4 capture -> scope DC mean -> SAFE`。
4. 记录 requested count、OUT2_MONITOR、CH4、MODE、ENABLE、saturation、scope load/coupling/probe 和真实 mean/min/max；nominal V 不能作为真实 V。
5. 身份、通信、readback、saturation、接线或输出行为任何异常，立即请求 SAFE 并停止当前 Gate。
```

## 8. 审查输出必须包含

```text
A. 本次读取文件列表
B. 当前主线判断
C. 当前 RTL 直接证据
D. 当前文档证据
E. 未验证事项
F. 旧版本污染风险
G. 禁止动作
H. 下一步安全动作
```

## 9. 文档语言

审查输出默认使用中文。代码标识符、文件路径、命令、寄存器名、模块名、信号名和英文缩写保留英文原文。
