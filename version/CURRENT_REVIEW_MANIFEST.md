# CURRENT_REVIEW_MANIFEST

本文件定义当前 GitHub `main` 分支的审查清单。AI 审查时必须先读本文件，再审查当前 RTL、上位机和实验记录。

## 1. 仓库与主线

```text
Repository: 666vitas/FPGA-MTS
Primary branch: main
Current stage: PZT 基础稳频最小闭环；SCAN / LOCK HERE / P-only 小增益 / SAFE
Primary RTL root: v0.94/rtl
Primary Vivado project: v0.94/project/redpitaya.xpr
Primary status file: version/STATUS.md
Strict review rules: version/AI_STRICT_REVIEW_ENTRY.md
Root entrypoint: AI_REVIEW_README.md
```

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

v3REG-0 SAFE/SCAN 已由用户上板验证：base address `0x40600000`，`MAGIC=0x4D545330`，`VERSION=0x00030000`，GUI/monitor 可控制 OUT2 三角波，并可用 SAFE 关闭。

当前 OUT2 的目标执行器是激光器专用 PZT / Scan 输入。`MODE=1 SCAN` 输出三角波驱动同一个 PZT 扫描激光频率；`MODE=3 P_LOCK` 输出 `LOCK_BIAS + P correction` 驱动同一个 PZT 完成基础反馈；`MODE=0 SAFE` 退出扫描和锁定。必须默认小 Kp、小 `LOCK_CORRECTION_LIMIT`，失败必须 SAFE；禁止接入激光器电流调制、D2-125 Servo Output 或 D2-125 Aux Output，也禁止任何输出端并联。

## 3. 当前必须读取的文件

状态与规则：

```text
AI_REVIEW_README.md
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

## 6. 实验与工程状态判定规则

可以说“已经实现”的内容：

```text
代码层面已经加入 custom_register_bank
代码层面已经加入 ramp_generator
代码层面已经加入 out2_lock_controller
代码层面 OUT2 已经改为 selected_out2 SAFE/SCAN/HOLD/P_LOCK/PI_LOCK 候选
代码层面已经加入 P_LOCK correction limit
代码层面已经加入 custom_debug_capture 候选
上位机代码层面已经加入 ARM AUTO LOCK / ABORT AUTO LOCK 候选
v3REG-0 SAFE/SCAN 已有用户上板验证记录
```

只能说“等待验证”的内容：

```text
HOLD/P_LOCK/PI_LOCK 等待最新 Vivado synthesis
HOLD/P_LOCK/PI_LOCK 等待最新 implementation
HOLD/P_LOCK/PI_LOCK 等待最新 timing 检查
HOLD/P_LOCK/PI_LOCK 等待 bitstream 生成
HOLD/P_LOCK/PI_LOCK 等待烧录
HOLD/P_LOCK/PI_LOCK 等待上板示波器验证
Auto Lock candidate 等待 Vivado timing / bitstream / 烧录 / 上板验证
custom_debug_capture 单窗口波形等待 Vivado timing / bitstream / 烧录 / 上板验证
KI / integral 当前不要恢复
```

2026-07-11 资源修复基线：`custom_debug_capture` 初版四通道 4096 深度存储曾被 Vivado 推断为 LUTRAM / RAM64M / RAM64X1D，导致 place_design `[Place 30-484]`，`LUTRAM/SRL capable slices` 超限。本次已将 `mem_ch1..mem_ch4` 标记为 `(* ram_style = "block" *)`，并把 debug capture 读路径改为同步读，读数据允许 1 个 `clk_i` 周期延迟。四通道仍完整保留，默认 `DEPTH=4096` 未变。该修复尚需用户重新运行 Vivado synthesis / implementation 确认，不得声称 implementation 已通过。

2026-07-11 v3LOCK-P0 人工选点基线：当前第一版不是自动识峰、不是 AI 自动锁定。禁止把 `board(1).csv` 或任何历史实验中的 `54 counts`、`0.704 V`、`0.784 V`、`49.75 Hz`、峰值、基线、扫描位置写成生产默认值或锁点配置。当前候选协议版本为 `0x00030001`，新增 `ERROR_SETPOINT`、`LOCK_ERROR_MONITOR`、`CAPTURE_LOCK_POINT`。真实锁点必须来自当前扫描波形：用户点击当前目标后执行 `LOCK HERE`，FPGA 在同一 `clk_i` 域捕获 `ERROR_SETPOINT` 和 `LOCK_BIAS`，P_LOCK 使用校正后的 `lock_error`。该候选尚未完成 Vivado synthesis / implementation / timing / bitstream / 烧录 / 上板验证。

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
1. 不继续扩大 RTL。
2. 用户明确授权后，才允许手动进入 Vivado synthesis / implementation / timing 检查。
3. timing 通过后，才允许生成 bitstream。
4. 烧录后先用上位机读 MAGIC / VERSION。
5. OUT2 连接激光器专用 PZT / Scan 输入前，先确认幅度、偏置、limit、correction_limit 和 SAFE。
6. 按 `SCAN -> 选择锁点 -> LOCK HERE -> Kp=0 -> Apply Kp 小步 0/4/8/16/32 -> 判断 polarity -> SAFE` 验证。
7. 禁止接激光器电流调制输入、D2-125 Servo Output、D2-125 Aux Output，禁止任何输出端并联。
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
