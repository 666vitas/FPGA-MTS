# CURRENT_REVIEW_MANIFEST

本文件定义当前 GitHub main 分支的唯一审查清单。AI 审查时必须先读本文件，再审查当前 RTL。

## 1. 仓库与主线

```text
Repository: 666vitas/FPGA-MTS
Primary branch: main
Current stage: v3REG-0 SAFE/SCAN board-verified; v3REG-1/v3REG-2 HOLD/P_LOCK/PI_LOCK are RTL/software candidates only
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
MODE=0 SAFE, MODE=1 SCAN, MODE=2 HOLD, MODE=3 P_LOCK, MODE=4 PI_LOCK are present in current RTL
laser_control / pi_controller_seq = 内部候选/历史路径，不是当前 DAC B / OUT2 最终输出
```

v3REG-0 SAFE/SCAN 已由用户上板验证：base address `0x40600000`，`MAGIC=0x4D545330`，`VERSION=0x00030000`，GUI/monitor 可控制 OUT2 三角波并可 SAFE 关闭。

HOLD/P_LOCK/PI_LOCK 当前只表示 GitHub main 中的 RTL/software 候选已经存在；尚未完成 Vivado synthesis / implementation / timing / bitstream / 上板验证。

当前阶段只允许示波器验证，不允许接入 PZT、Scan input、激光器电流调制、D2-125 Servo Output 或 D2-125 Aux Output。

## 3. 当前必须读取的文件

### 状态与规则

```text
AI_REVIEW_README.md
version/AI_STRICT_REVIEW_ENTRY.md
version/CURRENT_REVIEW_MANIFEST.md
version/STATUS.md
```

### Vivado 工程

```text
v0.94/project/redpitaya.xpr
```

审查目标：确认当前新增 RTL 是否已经加入 synthesis / implementation / simulation 文件集。

### 当前 RTL

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

## 4. 默认禁止读取为当前依据的路径

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

### 可以说“已经实现”的内容

只有当 RTL 直接存在并且 xpr 已加入时，才可以说：

```text
代码层面已经加入 register_bank
代码层面已经加入 ramp_generator
代码层面 OUT2 已经改为 selected_out2 SAFE/SCAN/HOLD/P_LOCK/PI_LOCK 候选
```

### 只能说“等待验证”的内容

没有 Vivado / bitstream / 上板记录时，只能说：

```text
等待 Vivado synthesis
等待 implementation
等待 timing 检查
等待 bitstream 生成
等待烧录
v3REG-0 SAFE/SCAN 已有用户上板示波器验证记录
等待 HOLD/P_LOCK/PI_LOCK 的 Vivado timing / bitstream / 上板示波器验证
```

### 禁止说的内容

```text
已经可以接 PZT
已经可以接 Scan
已经可以替代 D2-125 Aux Output
已经闭环锁定
已经完成 D2-125 替代
```

除非出现明确实验记录和安全评审文件。

## 7. 下一步最小安全动作

```text
1. 不继续大改 RTL。
2. 先运行 Vivado synthesis。
3. 再运行 implementation。
4. 检查 timing，尤其是 WNS/TNS/Failing Endpoints。
5. 生成 bitstream。
6. 烧录 Red Pitaya。
7. 用上位机读 MAGIC / VERSION。
8. 只把 OUT2 接示波器，先复核 SAFE/SCAN。
9. 再以 Kp=0 / Ki=0 复核 HOLD/P_LOCK/PI_LOCK 候选模式。
10. HOLD/P_LOCK/PI_LOCK scope-only 验证通过后，仍需单独安全评审，才能讨论 PZT/Scan 接入。
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
