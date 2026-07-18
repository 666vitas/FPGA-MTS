# CURRENT_REVIEW_MANIFEST

本文件只用于 GitHub `Review Mode`，不是 Development Mode 的启动入口，也不授权修改项目文件。

## 1. Review Mode 触发与边界

只有用户明确输入以下任一指令时读取本 Manifest：

```text
@GitHub 审计
审查最新main
```

```text
Repository: 666vitas/FPGA-MTS
Primary branch: main
Data source: GitHub main
Goal: inspect current commit, code, tests, evidence, Stage and Gate
Mutation: audit only
```

允许：

- 读取 GitHub online
- 检查当前 commit、diff、代码、测试和文档
- 比较状态记录与实际实现
- 输出问题和下一步安全动作

禁止：

- 修改代码、测试、RTL、Vivado 工程、寄存器、bitstream 或项目逻辑
- 自动切换到 Development Mode
- 用远端失败阻塞默认的本地 Development Mode

## 2. 强制入口顺序

```text
1. AI_REVIEW_README.md
2. AGENTS.md
3. version/AI_STRICT_REVIEW_ENTRY.md
4. version/CURRENT_REVIEW_MANIFEST.md
5. version/STATUS.md 顶部最新条目
6. version/rules/20_MULTI_AGENT_MTS_DEVELOPMENT.md
7. 本 Manifest 指定的当前代码、测试、SOP 和实验记录
8. 本次最新 commit/diff
```

## 3. 当前主线文件

### RTL / Vivado

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

### 上位机

按审查问题读取当前 `software/redpitaya_lock_host/` 下直接相关代码和测试，至少核对：

```text
software/redpitaya_lock_host/redpitaya_lock_host/main_window.py
software/redpitaya_lock_host/redpitaya_lock_host/custom_fpga_backend.py
software/redpitaya_lock_host/redpitaya_lock_host/connection_workers.py
software/redpitaya_lock_host/scripts/custom_fpga_scan_control.py
software/redpitaya_lock_host/tests/
```

### 当前状态与实验记录

```text
version/STATUS.md
version/HARDWARE_VALIDATION.md
software/redpitaya_lock_host/docs/HARDWARE_CALIBRATION_SOP.md
software/redpitaya_lock_host/docs/DEVELOPMENT_LOG.md
```

需要时读取用户在当前任务中提供的截图、CSV、寄存器读回和实验记录。

## 4. 当前事实判定

### 4.1 代码实现

```text
GitHub main 实际代码和最终路由
> 当前测试
> STATUS 顶部
> 其他文档和注释
```

判断 OUT1/OUT2 时必须追踪 `red_pitaya_top.sv` 的最终 DAC 数据源，不能用候选模块、模块名或旧注释代替。

### 4.2 当前 Stage、Gate 和下一步动作

```text
version/STATUS.md 顶部最新条目
> 当前 Gate 对应的最新 SOP/实验记录
> version/HARDWARE_VALIDATION.md 中同一 Gate 的有效记录
> README、代码注释和历史日志
```

本 Manifest 不再硬编码某一天的当前阶段。Review 必须从 `STATUS.md` 顶部读取当前 Stage/Gate，并检查与 SOP、硬件记录和代码是否一致。

如果状态来源之间存在影响接线、输出、Kp、polarity、limits 或推进顺序的冲突：

- 列为 `Blocker`
- 禁止推进有源输出和闭环动作
- 要求先修正文档或由用户确认当前 Gate

## 5. 固定架构与安全基线

除非当前 main 明确包含经授权的架构变化，审查基线为：

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

`VERSION` 必须从当前 RTL 和实际实验记录读取。

固定安全结论：

- OUT2 只能连接当前 Gate 明确授权的激光器专用 PZT/Scan 输入和测量设备。
- 禁止 OUT2 接激光器电流调制、D2-125 `Servo Output`、D2-125 `Aux Output`。
- 禁止任何两个有源输出并联。
- 通信失败、身份不匹配、saturation、越界、异常跳变、极性无法解释或反馈方向疑似错误时必须 SAFE。
- 不得自动提高 Kp、切换 polarity、恢复 Ki、扩大 safe range 或自动重锁。
- CH4 command/capture 不自动等于 loaded PZT 电压。
- 软件、GUI、硬件、闭环和长期稳定性必须分开表述。

## 6. 禁止作为当前 main 依据的路径

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

历史路径可以用于解释演进，但不得覆盖当前代码、当前测试、`STATUS.md` 顶部或当前 Gate。

## 7. Review 必查差异

审查必须主动查找：

- conflict markers
- README、STATUS、HARDWARE_VALIDATION、SOP 和代码注释之间的冲突
- host/RTL 寄存器地址、模式、`MAGIC/VERSION` 不一致
- 实现存在但测试未覆盖
- 自动化通过但 GUI/硬件/闭环证据缺失
- selected/captured/readback/current 或 counts/volts/physical voltage 被混写
- 旧默认值、历史 CSV、硬编码锁点或过期 Stage 污染当前结论

## 8. Review 输出

```text
A. 实际读取文件
B. GitHub main commit 与 diff 范围
C. 当前 Stage/Gate 和来源一致性
D. 当前代码直接证据
E. 自动化测试证据
F. 用户 GUI/硬件/实验记录证据
G. 未验证事项
H. Blocker/High/Medium/Low 问题
I. 旧版本、旧注释、冲突标记和文档污染
J. 禁止推进的动作
K. 下一步唯一安全动作
L. PASS / CONDITIONAL PASS / FAIL / LAB VERIFICATION REQUIRED
```

Review Mode 只交付报告，不实施修复。
