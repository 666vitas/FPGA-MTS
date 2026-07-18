# AI_STRICT_REVIEW_ENTRY

本文件是 `666vitas/FPGA-MTS` 的 GitHub `Review Mode` 强约束入口，用于防止 AI 把历史版本、旧注释、备份文件、过期状态和当前主线混在一起。

本文件只用于只读审计，不授权修复、开发、Vivado、bitstream、烧录或实验。

## 0. 审查原则

```text
只审当前 GitHub main，不拼接历史版本。
先读入口与 manifest，再读 STATUS 顶部，再读当前代码和证据。
当前实现由实际代码和最终路由决定。
当前 Stage/Gate 由 STATUS 顶部和对应实验文档决定。
没有读取当前文件，就不能下结论。
没有对应证据，就不能抬高验证等级。
```

如果仓库文件中存在 conflict markers、相互矛盾的接线规则、过期硬编码阶段或无法确认的状态，必须列为问题，不能选择对推进更有利的一侧继续。

## 1. Review Mode 触发条件

只有用户明确输入以下任一指令时启用：

```text
@GitHub 审计
审查最新main
```

普通 `@GitHub` 开发、修复或修改请求不属于本模式。

## 2. 数据源优先级

### 2.1 当前代码事实

判断模块、信号、寄存器、模式和最终 OUT1/OUT2 路由时，优先级为：

```text
GitHub main 当前代码
> GitHub main 当前测试
> version/STATUS.md 顶部记录
> 其他说明文档和注释
```

当前 RTL 主线至少包括：

```text
v0.94/project/redpitaya.xpr
v0.94/rtl/red_pitaya_top.sv
v0.94/rtl/laser_lock_core.sv
v0.94/rtl/custom_register_bank.sv
v0.94/rtl/ramp_generator.sv
v0.94/rtl/mixer_core.sv
v0.94/rtl/lpf_core.sv
v0.94/rtl/output_protect.sv
v0.94/rtl/pi_controller_seq.sv
v0.94/rtl/pi_controller.sv
v0.94/rtl/error_setpoint_corrector.sv
v0.94/rtl/custom_debug_capture.sv
```

判断 OUT2 时必须追踪到 `red_pitaya_top.sv` 的最终 DAC B 数据源。看到 `pi_controller`、`laser_control`、候选模块或旧注释，不足以证明它们正在驱动 OUT2。

### 2.2 当前 Stage、Gate 和下一步动作

优先级为：

```text
version/STATUS.md 顶部最新条目
> 当前 Gate 对应的最新 SOP/实验记录
> version/HARDWARE_VALIDATION.md 中同一 Gate 的有效记录
> README、代码注释和历史日志
```

Review 必须指出这些来源是否一致。存在影响接线、PZT、OUT2、Kp、polarity、limits 或推进顺序的冲突时，结论至少为 `CONDITIONAL PASS` 或 `FAIL`，并要求先对齐文档。

### 2.3 当前审查范围

以 `version/CURRENT_REVIEW_MANIFEST.md` 为准。Manifest 只定义本次应读取的当前文件，不得覆盖实际代码或 `STATUS.md` 顶部。

### 2.4 历史资料

以下路径默认属于历史层：

```text
v-weifang/**
version-weifang/**
version/v1/**
version/v2/**
**/old/**
**/*.before_*
**/*before*
```

历史资料只能用于回答“过去做过什么”，不能回答“当前 main 做了什么”或“当前可以执行什么实验”。

## 3. 强制读取顺序

```text
1. AI_REVIEW_README.md
2. AGENTS.md
3. version/AI_STRICT_REVIEW_ENTRY.md
4. version/CURRENT_REVIEW_MANIFEST.md
5. version/STATUS.md 顶部最新条目
6. version/rules/20_MULTI_AGENT_MTS_DEVELOPMENT.md
7. Manifest 指定的当前 RTL、上位机、测试、SOP 和实验记录
8. 本次最新 commit/diff
```

如果工具支持精确读取文件，必须使用精确读取，不要先用全仓库搜索猜测主线。

## 4. 固定架构与安全检查

除非当前 main 的最终代码和最新状态明确显示经过授权的架构变化，审查基线为：

```text
IN1 = PD
IN2 = REF
OUT1 = laser_error
OUT2 = selected_out2
MODE=0 SAFE
MODE=1 SCAN
MODE=2 HOLD
MODE=3 P_LOCK
MODE=4 PI_LOCK candidate
MAGIC = 0x4D545330
```

`VERSION` 必须从当前 `custom_register_bank.sv` 和实际实验记录读取，禁止沿用本文件中的旧值。

必须保留的安全结论：

- OUT2 只能连接当前 Gate 明确授权的激光器专用 PZT/Scan 输入和测量设备。
- 禁止 OUT2 接激光器电流调制输入。
- 禁止 OUT2 接 D2-125 `Servo Output` 或 `Aux Output`。
- 禁止任何两个有源输出并联。
- 必须限制 OUT2 幅度、偏置、PZT safe range、`LOCK_CORRECTION_LIMIT` 和 `LOCK_LIMIT`。
- 通信失败、身份不匹配、saturation、越界、异常跳变、极性无法解释或反馈方向疑似错误时立即 SAFE。
- 不得自动提高 Kp、切换 polarity、恢复 Ki、自动重锁或扩大安全范围。

## 5. 证据等级审查

允许的证据等级：

```text
[IMPLEMENTED]
[AUTOMATED VERIFIED]
[USER GUI VERIFIED]
[USER HARDWARE VERIFIED]
[FAILED]
[NOT VERIFIED]
```

必须逐层检查，禁止以下替代：

```text
代码存在 -> 自动化通过
自动化通过 -> GUI 通过
GUI 通过 -> bitstream/上板通过
CH4 command -> loaded PZT 电压
示波器波形 -> 闭环锁定
短时锁定 -> 激光稳频或长期稳定性
```

bitstream 生成、烧录、`MAGIC/VERSION` 读回、真实 OUT1/OUT2、PZT loaded node、谱线位置、P-only、PI 和长期稳定性必须分别有证据。

## 6. 必查内容

### 6.1 RTL 与寄存器

- 最终 OUT1/OUT2 路由
- reset 后 SAFE
- mode/enable 状态
- signed/unsigned、位宽、乘法、移位、截位和饱和
- correction limit 与 absolute limit
- `CAPTURE_LOCK_POINT` 的实际语义
- host/RTL 寄存器地址、模式编码和 `VERSION` 一致性
- testbench 是否覆盖零值、极值、正负 error/Kp、polarity、模式切换和饱和

### 6.2 上位机

- Live/capture 防重入
- 通信失败、身份错误、窗口关闭和异常时 SAFE
- selected、captured、readback 和 current 是否分开
- unavailable 是否被 0、默认值或期望值冒充
- counts、ideal equivalent、calibrated estimate 和物理测量是否分开
- GUI、CSV 和实验日志语义是否一致

### 6.3 实验与 Gate

- 当前只允许哪个最小实验动作
- 接线、负载、耦合和探头倍率是否明确
- PZT safe range 是否有证据
- `Kp=0 HOLD`、`Kp=0 LOCK HERE` 和非零 Kp P-only 是否被分开
- 是否记录 commit、bitstream、`MAGIC/VERSION`、截图、CSV 和 readback
- 是否存在继续动作前必须解决的 FAIL 或 Blocker

## 7. Review 输出模板

```text
A. 本次实际读取的文件
B. GitHub main commit 与审查范围
C. 当前 Stage/Gate 和来源一致性
D. 当前代码直接确认的事实
E. 自动化测试直接确认的事实
F. 用户 GUI/硬件/实验记录确认的事实
G. 未验证事项
H. Blocker/High/Medium/Low 问题
I. 旧版本、旧注释、冲突标记和文档污染
J. 禁止推进的动作
K. 下一步唯一安全动作
L. PASS / CONDITIONAL PASS / FAIL / LAB VERIFICATION REQUIRED
```

## 8. 禁止结论

没有对应证据时，禁止声称：

- 已完成 HOLD/P_LOCK/PI_LOCK 硬件验证
- 已完成 `LOCK HERE` 无跳变
- 已找到真实 MTS 锁点
- 已完成 P-only 或 PI 闭环
- 已替代 D2-125
- 已实现自动锁定、自动重锁或 AI 参数优化
- 已完成激光稳频或长期稳定性验证

## 9. 最短调用指令

```text
请按强约束 Review Mode 审查 666vitas/FPGA-MTS 最新 main。
先读 AI_REVIEW_README.md、AGENTS.md、version/AI_STRICT_REVIEW_ENTRY.md、version/CURRENT_REVIEW_MANIFEST.md、version/STATUS.md 顶部和 version/rules/20_MULTI_AGENT_MTS_DEVELOPMENT.md。
只以当前代码、当前测试和当前实验记录判断；历史目录不得作为当前结论。
输出已读文件、当前 Stage/Gate、代码事实、测试事实、实验事实、问题分级、禁止动作、下一步唯一安全动作和最终结论。
```
