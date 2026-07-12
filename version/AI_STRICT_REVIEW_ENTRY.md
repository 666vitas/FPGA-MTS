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
v0.94/rtl/error_setpoint_corrector.sv
v0.94/rtl/custom_debug_capture.sv
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
10. v0.94/rtl/error_setpoint_corrector.sv
11. v0.94/rtl/custom_debug_capture.sv
12. 其他 manifest 中列出的当前 RTL、上位机文档和实验日志
```

如果工具支持精确读取文件，必须使用精确读取。不要先用全仓库搜索来猜当前主线。

## 3. 当前主线判定

<<<<<<< HEAD
截至 2026-07-11，当前主线为：

```text
v3REG-0 register-controlled OUT2 SAFE/SCAN 已由用户上板验证；
GitHub main 已进入 v3LOCK-P0 人工 LOCK HERE 候选；
HOLD / P_LOCK / PI_LOCK / LOCK HERE 尚未完成最新 Vivado synthesis / implementation / timing / bitstream / 烧录 / 上板示波器验证。
=======
截至 2026-07-12，当前主线为：

```text
项目最终目标固定为：基于 Red Pitaya 的全自动深度学习参数优化 MTS 激光稳频系统。
当前只做 PZT 基础稳频最小闭环：SCAN -> 观察 MTS error -> 人工选择色散过零点 -> LOCK HERE -> 同拍捕获 ERROR_SETPOINT 和 LOCK_BIAS -> P-only 小增益反馈 -> SAFE。
OUT2 的目标执行器是激光器专用 PZT / Scan 输入，SCAN 和 P_LOCK 使用同一个 PZT 接口。
>>>>>>> 0a6928a (Update v94 project code documents and records)
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
已验证 bitstream 的 VERSION = 0x00030000
GUI / monitor 已可控制 OUT2 三角波并 SAFE 关闭
```

2026-07-11 v3LOCK-P0 候选必须这样表述：

```text
当前候选协议 VERSION = 0x00030001，但尚未生成并上板验证对应 bitstream。
ERROR_SETPOINT / LOCK_ERROR_MONITOR / CAPTURE_LOCK_POINT 已在当前 RTL 中实现。
LOCK HERE = 人工从当前波形选择目标后的候选流程，不是自动识峰、AI 自动锁定或已完成稳频。
禁止把 board(1).csv 或历史实验中的 counts、电压、频率、峰值、基线、扫描位置写成生产默认值或固定锁点。
真实锁点必须来自当前扫描；CAPTURE_LOCK_POINT 在同一 clk_i 域捕获 ERROR_SETPOINT 与 LOCK_BIAS。
MODE=3 P_LOCK 是 P-only；MODE=4 PI_LOCK 暂时退化为 P_LOCK；KI / integral 当前不要恢复。
custom_debug_capture 已加入 block RAM 推断候选修复，但尚未由最新 Vivado implementation 验证。
没有新 bitstream 或 capture 数据时，GUI 必须显示 custom_debug_capture not available，不得画 0 冒充真实波形。
没有通过最新 synthesis / implementation / timing / bitstream / 烧录 / 上板示波器验证前，不得声称 LOCK HERE、P_LOCK 或 debug_capture 已通过硬件验证。
```

如果某个旧文档写着“还没有 register_bank”或“OUT2 仍是 PI shadow control”，只能判定为历史阶段描述，不能覆盖当前主线。

## 4. 当前安全边界

任何审查都必须保留下面结论：

```text
OUT2 的目标执行器是激光器专用 PZT / Scan 输入。
SCAN 和 P_LOCK 使用同一个 PZT 接口。
必须限制 OUT2 幅度、偏置、LOCK_CORRECTION_LIMIT 和 LOCK_LIMIT。
异常、反馈方向错误、持续 saturation 或输出接近 limit 时立即 SAFE。
禁止 OUT2 接激光器电流调制输入。
禁止 OUT2 接 D2-125 Servo Output。
禁止 OUT2 接 D2-125 Aux Output。
禁止 OUT2 与任何 D2-125 输出并联。
禁止两个设备输出端并联。
禁止声称已经完成全自动锁定、自动重锁或深度学习参数优化。
禁止把 Auto Lock candidate 说成已经完成激光稳频。
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

### 错误 4：把 PZT 基础稳频主线误写成永久示波器-only

纠正：当前 PZT 基础稳频主线的目标执行器就是激光器专用 PZT / Scan 输入。正确边界不是“永久禁止 PZT”，而是“只能接专用 PZT/Scan 输入，必须限幅、限偏置、小 Kp、异常 SAFE；禁止接电流调制输入和任何 D2-125 输出端”。

### 错误 5：看到 LOCK HERE / CAPTURE_LOCK_POINT 就说已经实现自动锁定

纠正：当前 v3LOCK-P0 是人工从当前扫描波形选点后的候选流程，不是自动识峰。没有最新 Vivado 和示波器证据，不能声称已经锁定。

### 错误 6：用历史 CSV 参数作为当前锁点

纠正：历史数据只用于分析问题。ERROR_SETPOINT 和 LOCK_BIAS 必须来自当前扫描与当前 FPGA 同拍捕获，不能硬编码历史 counts、电压或扫描位置。

## 7. 给 AI 的最短调用指令

用户可以直接复制下面这段给任何审查窗口：

```text
请按强约束审查系统审查 666vitas/FPGA-MTS main。
先读 AI_REVIEW_README.md、version/AI_STRICT_REVIEW_ENTRY.md、version/CURRENT_REVIEW_MANIFEST.md、version/STATUS.md。
只以 v0.94/rtl 和 v0.94/project/redpitaya.xpr 判断当前代码。
禁止读取或引用 v-weifang、version-weifang、version/v1、version/v2、old、before 作为当前结论依据。
请输出：已读文件、当前主线、RTL直接确认、文档确认但未实验验证、风险、下一步安全动作。
```
