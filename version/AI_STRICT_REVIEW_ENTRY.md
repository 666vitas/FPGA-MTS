# AI_STRICT_REVIEW_ENTRY

本文件是 `666vitas/FPGA-MTS` 的强约束审查规则。用于防止 AI 审查混用旧版本、历史文档、备份文件和当前 RTL。

## 0. 审查原则

```text
只审当前主线，不拼接历史版本。
先读入口和 manifest，再读 STATUS，再读当前 RTL。
没有 fetch 到当前文件，就不能下结论。
没有 RTL 或实验记录证据，就不能声称已经实现或已经通过。
```

## 1. 数据源优先级

### Tier 0：当前代码事实

这些文件是判断“当前代码实际做了什么”的最高优先级：

```text
v0.94/rtl/red_pitaya_top.sv
v0.94/rtl/laser_lock_core.sv
v0.94/rtl/custom_register_bank.sv
v0.94/rtl/ramp_generator.sv
v0.94/rtl/mixer_core.sv
v0.94/rtl/lpf_core.sv
v0.94/rtl/output_protect.sv
v0.94/rtl/pi_controller_seq.sv
v0.94/project/redpitaya.xpr
```

### Tier 1：当前状态事实

```text
version/STATUS.md
version/CURRENT_REVIEW_MANIFEST.md
AI_REVIEW_README.md
```

### Tier 2：当前阶段辅助文档

只有当用户明确要求时才读取。读取后也不能覆盖 Tier 0 / Tier 1。

### Tier 9：历史资料，默认禁止作为当前结论依据

```text
v-weifang/**
version-weifang/**
version/v1/**
version/v2/**
**/old/**
**/*.before_*
**/*before*
```

这些文件只允许回答“历史上做过什么”，不能回答“当前 main 分支是什么状态”。

## 2. 强制读取顺序

AI 审查必须按下面顺序读取：

```text
1. AI_REVIEW_README.md
2. version/AI_STRICT_REVIEW_ENTRY.md
3. version/CURRENT_REVIEW_MANIFEST.md
4. version/STATUS.md
5. v0.94/project/redpitaya.xpr
6. v0.94/rtl/red_pitaya_top.sv
7. v0.94/rtl/custom_register_bank.sv
8. v0.94/rtl/ramp_generator.sv
9. v0.94/rtl/laser_lock_core.sv
10. 其他 manifest 中列出的当前 RTL
```

如果工具支持精确读取文件，必须使用精确读取。不要先用全仓库搜索来猜当前主线。

## 3. 当前主线判定

截至 2026-07-10，当前主线为：

```text
v3REG-0 register-controlled OUT2 SAFE/SCAN 已由用户上板验证；
GitHub main 已包含 HOLD / P_LOCK / PI_LOCK 候选，但尚未完成最新 Vivado synthesis / implementation / timing / bitstream / 烧录 / 上板示波器验证。
```

必须使用下面判断：

```text
OUT1 = laser_error = mixer + LPF error observation
OUT2 = selected_out2
MODE=0 SAFE: OUT2 = 0
MODE=1 SCAN: OUT2 = custom_register_bank + ramp_generator
MODE=2 HOLD: GitHub main 候选，尚未完成最新 Vivado 和上板验证
MODE=3 P_LOCK: 下一步验证重点，当前 LOCK 目标缩小为 P-only
MODE=4 PI_LOCK: 当前暂时退化为 P_LOCK，KI / integral 当前不要恢复
laser_control / pi_controller_seq = 内部候选或历史路径，不是当前 DAC B / OUT2 最终输出
```

v3REG-0 已验证基线：

```text
base address = 0x40600000
MAGIC = 0x4D545330
VERSION = 0x00030000
GUI / monitor 已可控制 OUT2 三角波并 SAFE 关闭
```

如果某个旧文档写着“还没有 register_bank”或“OUT2 仍是 PI shadow control”，只能判定为历史阶段描述，不能覆盖当前主线。

## 4. 当前安全边界

任何审查都必须保留下面结论：

```text
本阶段只允许 OUT2 接示波器。
禁止 OUT2 接 Scan/PZT。
禁止 OUT2 接激光器。
禁止 OUT2 接 D2-125 Servo Output。
禁止 OUT2 接 D2-125 Aux Output。
禁止 OUT2 与任何 D2-125 输出并联。
禁止声称已经闭环锁定。
```

HOLD / P_LOCK / PI_LOCK 只有在最新 Vivado synthesis、implementation、timing、bitstream、烧录、示波器验证都有证据后，才允许进入下一阶段评审。
禁止声称 FPGA 已经闭环锁定或已经替代 D2-125。

## 5. 审查输出模板

每次审查必须按下面格式输出：

```text
A. 本次实际读取的文件
B. 当前主线结论
C. 已由 RTL 直接确认的事实
D. 已由文档记录确认但尚未实验验证的事实
E. 不能确认 / 仍有风险的事实
F. 发现的旧注释或旧文档污染
G. 禁止推进的动作
H. 下一步最小安全动作
```

## 6. 典型错误结论纠正

### 错误 1：把 version/v2 当当前主线

纠正：`version/v2/**` 是历史资料。当前主线看 `version/STATUS.md` 当前主线段落、`v0.94/rtl/**` 和 `redpitaya.xpr`。

### 错误 2：把 version-weifang 或 v-weifang 当当前主线

纠正：这些路径不是当前 GitHub main 审查依据。

### 错误 3：看到 `pi_controller_seq` 就说 OUT2 是 PI 输出

纠正：是否作为 OUT2 最终输出，必须看 `red_pitaya_top.sv` 的 DAC B 选择逻辑。当前 OUT2 是 `selected_out2`，不是 `laser_control`。

### 错误 4：看到 register_bank 就说已经能接 PZT

纠正：register_bank 只是让上位机控制 OUT2 SAFE/SCAN 的第一步。没有 Vivado、bitstream、上板示波器验证前，不能接 PZT。

## 7. 给 AI 的最短调用指令

用户可以直接复制下面这段给任何审查窗口：

```text
请按强约束审查系统审查 666vitas/FPGA-MTS main。
先读 AI_REVIEW_README.md、version/AI_STRICT_REVIEW_ENTRY.md、version/CURRENT_REVIEW_MANIFEST.md、version/STATUS.md。
只以 v0.94/rtl 和 v0.94/project/redpitaya.xpr 判断当前代码。
禁止读取或引用 v-weifang、version-weifang、version/v1、version/v2、old、before 作为当前结论依据。
请输出：已读文件、当前主线、RTL直接确认、文档确认但未实验验证、风险、下一步安全动作。
```
