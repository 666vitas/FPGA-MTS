# FPGA Deterministic Lock Acquisition

> **D1-A DESIGN BASELINE / `[NOT VERIFIED]`**  
> 本文件定义 `v3LOCK-D1 / Deterministic FPGA Lock Acquisition Design` 的最小接口基线。它描述待实现的 RTL、寄存器和 host 契约，不表示 RTL、bitstream、GUI 或真实锁定已经通过。

## 1. 当前真实路径

当前 `LOCK HERE` 不是“host 选择一个历史点后，FPGA 在相同方向的下一次 ERROR crossing 自主切换”。真实数据路径为：

```text
FPGA custom_debug_capture 生成历史 CH1/CH2/CH3/CH4 capture
-> Windows GUI 在历史 capture 中选取 ERROR 零交叉
-> GUI 保存 target_out2_counts、error_setpoint_counts、ramp_direction
-> GUI 经 SSH 调用 Red Pitaya Linux custom_fpga_scan_control.py
-> Linux 轮询 OUT2_MONITOR，等待进入 target_out2_counts +/- target_window_counts
-> Linux 写 CAPTURE_LOCK_POINT=1
-> custom_register_bank 在该写命令到达的 clk_i 拍捕获：
   ERROR_SETPOINT <- 当前 ERROR_MONITOR
   LOCK_BIAS      <- 当前 OUT2_MONITOR
   Kp/Ki          <- 0
   MODE           <- P_LOCK
   ENABLE         <- 1
-> out2_lock_controller 以捕获的 LOCK_BIAS 输出 Kp=0
```

对应当前代码事实：

- [IMPLEMENTED] GUI 通过 capture 中相邻 CH4 样本的变化方向生成 `ramp_direction=rising/falling`。
- [IMPLEMENTED] `target_out2_counts` 和 `target_window_counts` 被传到 Linux。
- [IMPLEMENTED] Linux 的 `target wait` 只比较 `OUT2_MONITOR` 与目标窗口，不检查 GUI 保存的 `ramp_direction`，也不检查 ERROR crossing。
- [IMPLEMENTED] `CAPTURE_LOCK_POINT` 的最终寄存器更新位于 FPGA `clk_i` 域，同拍捕获 ERROR/OUT2 并进入 Kp=0 P_LOCK。
- [NOT VERIFIED] 触发时刻仍由 Linux 轮询周期、SSH/进程调度、`/dev/mem` 访问和寄存器写入延迟共同决定。

审计路径中没有独立的 `v0.94/rtl/out2_lock_controller.sv`。`out2_lock_controller` module 当前附在 `v0.94/rtl/custom_register_bank.sv` 末尾；后续 RTL Gate 可在不改变行为的前提下决定是否拆文件，但拆分不是 D1 的功能目标。

## 2. 为什么当前路径不是确定性数字切换

`CAPTURE_LOCK_POINT` 到达 FPGA 后的捕获是原子的，但“何时发出该命令”不是 FPGA 实时事件。Linux 看到目标窗口后到寄存器写入真正到达之间，扫描仍在继续；不同轮询相位和系统调度会产生不同的捕获点。

当前路径还缺少两个互相独立的实时条件：

1. GUI 从历史 capture 得到的 `ramp_direction` 没有进入 FPGA。
2. 没有 `required_error_crossing_direction`，FPGA 不知道应接受 ERROR 的 negative-to-positive 还是 positive-to-negative crossing。

因此，`target_wait_matched=True` 只能表示 host 曾经读到 OUT2 落在窗口中；它不是 FPGA `ARMED/TRIGGERED` 状态。GUI 的 selected-to-captured delta 也只是两次 host 可见数值之差，不是 FPGA 时钟级 scan-to-lock jump。

## 3. 新架构职责

### Windows host

- 显示实时/历史扫描波形并让用户选择、确认目标。
- 从同一 capture 生成完整目标描述。
- 预装 shadow registers，发送一次 `ARM`。
- 只读取 `state`、sticky event、fault 和 monitor；不参与精确触发时刻。

### Red Pitaya Linux

- 执行低速寄存器传输、身份检查、ARM/ABORT 命令和状态读取。
- 不轮询目标窗口来决定切换，不在触发路径写 `CAPTURE_LOCK_POINT`。
- 通信延迟只影响“何时开始 ARMED”，不影响 ARMED 后“在哪个 FPGA 时钟拍触发”。

### FPGA

- 继续产生实时扫描。
- 提供与 `scan_o` 对齐的实时扫描方向。
- 在 FPGA 时钟域判断目标窗口和独立 ERROR crossing direction。
- 在唯一触发拍原子捕获实际 bias、冻结 acquisition 事件并进入 Kp=0。
- 执行 P-only、correction/absolute limit、saturation、ABORT 和 FAULT。

### 用户

- 后续只按新 SOP 完成接线、截图、示波器观察和结果报告。
- 用户仍是唯一能批准 Kp=0、最小非零 Kp 和真实硬件锁定 Gate 的操作者。

## 4. 目标描述与有效性

ARM 前由 host 写入以下 shadow fields；ARM 被接受时 FPGA 一次性复制到 active fields。ARM 后继续写 shadow fields 不得改变当前 active transaction。

| Field | 最小语义 |
|---|---|
| `target_out2_counts` | 历史 capture 中目标 ERROR crossing 对应的 nominal OUT2 count，signed 14-bit |
| `target_error_setpoint_counts` | 期望 ERROR crossing level，signed 14-bit；第一版通常为 0 或确认点的明确 setpoint |
| `target_window_counts` | `abs(scan-target) <= window` 的非负窗口 |
| `required_scan_direction` | `RISING` 或 `FALLING`；必须来自 confirmed capture |
| `required_error_crossing_direction` | `NEG_TO_POS` 或 `POS_TO_NEG`，独立于 scan direction |
| `initial_polarity_suggestion` | host 根据已确认斜率生成的提示；Kp=0 时不生效，未经用户批准不得自动应用 |
| `correction_limit` | P correction 相对 lock bias 的最大绝对 counts |
| `absolute_limit` | 最终 OUT2 的最大绝对 counts |
| `config_generation` | host 目标代次；事件回读用于排除 stale target/event |

ARM 最低校验：

- 所有 signed/unsigned 字段在 14-bit 和 DAC 合法范围内。
- `target_window_counts > 0`。
- `correction_limit <= absolute_limit <= 8191`。
- `target_out2_counts` 及其目标窗口位于 host 已批准的 PZT safe range 与 `absolute_limit` 内。
- 两个 direction enum 均有效。
- 当前状态为 `SCAN`、`ENABLE=1`，无 saturation、无未清除的 runtime FAULT。

无效配置的 ARM 必须被拒绝，保持 `SCAN`，设置 sticky `CONFIG_REJECTED` readback；不得使用部分 shadow 值，也不得伪造 `ARMED`。运行期 saturation、非法状态或限幅不变量破坏进入 `FAULT`。

## 5. FPGA acquisition 状态机

```text
SAFE
  | explicit SCAN with valid limits
  v
SCAN
  | valid ARM: shadow -> active atomically
  v
ARMED
  | direction AND window AND ERROR crossing
  v
TRIGGER_CAPTURE  (one FPGA clock commit state)
  |
  v
P_LOCK_KP0
  | later explicit, user-approved nonzero Kp
  v
P_LOCK_ACTIVE

ABORT from any non-SAFE state -> SAFE
runtime safety violation -> FAULT -> safe output
FAULT requires explicit SAFE/clear sequence before a new SCAN
```

### `SAFE`

`ENABLE=0`，Kp=Ki=0，输出使用既有 SAFE 语义。清除 armed transaction；sticky event 只在显式 `CLEAR_EVENT` 时清除。

### `SCAN`

输出来自 `ramp_generator`。允许 host 更新下一次 shadow target。只有合法 ARM 能进入 `ARMED`。

### `ARMED`

继续无扰扫描。active target 完全冻结。ARM 拍只初始化 crossing history，不允许使用 ARM 前的 stale ERROR sample 立即触发；至少取得一个 ARM 后样本再评估 crossing。

### `TRIGGER_CAPTURE`

这是单 FPGA 时钟的内部 commit 状态。该拍必须同时：

- 捕获实际 `selected_out2` 为 `lock_bias`，不是把 nominal `target_out2_counts` 强行作为 bias。
- 装载 active `target_error_setpoint_counts` 为控制 setpoint。
- 强制 Kp=0、Ki=0，清除积分候选状态。
- 冻结 event readback：实际 OUT2、实际 ERROR、两个实际方向、active config generation、触发 cycle counter。
- 置 sticky `TRIGGERED/EVENT_VALID`。

host 可能轮询不到这个单拍状态，因此 `EVENT_VALID`、`EVENT_SEQUENCE` 和 event payload 必须保持到显式清除。

### `P_LOCK_KP0`

输出保持触发拍捕获的 `lock_bias`。不得自动应用 `initial_polarity_suggestion`，不得自动增加 Kp。该状态是第一版 acquisition 的终点。

### `P_LOCK_ACTIVE`

只在后续 Gate 中由用户批准的显式命令进入。第一版只复用现有 P-only 路径；Ki 保持 0。

### `FAULT`

运行期 saturation、非法 state transition、active 配置损坏或安全不变量失败时进入。FAULT 置 sticky fault/event 并使用 SAFE 输出。不得自动返回 SCAN、重新 ARM 或重锁。

## 6. FPGA 触发条件

每个 FPGA 时钟拍只允许在 `state==ARMED` 时判断：

```text
trigger =
    armed
    AND scan_direction_matches
    AND scan_value_inside_target_window
    AND error_crosses_target_setpoint_in_required_direction
```

精确定义：

```text
inside_window =
    abs(widened_signed(scan_o) - widened_signed(target_out2_counts))
    <= widened_unsigned(target_window_counts)

NEG_TO_POS =
    previous_error < target_error_setpoint_counts
    AND current_error >= target_error_setpoint_counts

POS_TO_NEG =
    previous_error > target_error_setpoint_counts
    AND current_error <= target_error_setpoint_counts
```

实现必须使用扩展位宽计算差值和绝对值，避免 14-bit signed overflow。`ramp_generator` 需要输出与公开 `scan_o` 同拍对齐的 direction；不能直接暴露当前未对齐的内部 `direction_up_q`。ERROR crossing direction 与 scan direction 分开编码和回读。

第一版不做谱形相关、多点模板匹配或完整 Linien 自动识别。若噪声导致单样本 crossing 不可靠，应在后续单独 Gate 增加明确的 hysteresis/debounce 字段和仿真，不能在实现中加入未记录的隐式滤波。

## 7. 原子切换与 bumpless transfer

bumpless 的数字判据是：

```text
out2_before_trigger = selected_out2 on trigger edge
captured_lock_bias  = selected_out2 on the same trigger edge
first Kp=0 output   = captured_lock_bias
digital_jump_counts = first Kp=0 output - out2_before_trigger = 0
```

nominal `target_out2_counts` 只用于窗口判定；实际 bias 必须来自触发拍 `selected_out2`。模式、bias、setpoint、Kp/Ki、event 和 state 必须在一个同步 commit 中更新，不能由 host 多次写寄存器拼成切换。

RTL 仿真必须明确 controller pipeline 的首拍行为，证明进入 Kp=0 时不会短暂输出旧 bias、零值或 nominal target。真实 DAC、loaded PZT、模拟迟滞和谱峰是否无跳变仍需用户硬件验证，不能由数字零 jump 代替。

## 8. 建议寄存器契约

以下地址避开当前 `0x00..0x5C` 控制区和 `0x80..0xA0` capture 区，是 D1-A 的建议冻结基线。实现时须同步 RTL、Linux helper、Python backend、tests 与 `VERSION`；`MAGIC` 不变。

| Offset | Name | Access | 语义 |
|---:|---|---|---|
| `0x60` | `TARGET_OUT2_SHADOW` | RW | signed 14-bit |
| `0x64` | `TARGET_ERROR_SETPOINT_SHADOW` | RW | signed 14-bit |
| `0x68` | `TARGET_WINDOW_SHADOW` | RW | unsigned counts |
| `0x6C` | `TARGET_REQUIREMENTS_SHADOW` | RW | scan dir、ERROR crossing dir、polarity suggestion、valid bits |
| `0x70` | `CORRECTION_LIMIT_SHADOW` | RW | unsigned counts |
| `0x74` | `ABSOLUTE_LIMIT_SHADOW` | RW | unsigned counts |
| `0x78` | `CONFIG_GENERATION_SHADOW` | RW | host generation token |
| `0x7C` | `CONFIG_VALIDATION` | RO | field/range validation bits |
| `0xA4` | `ACQ_COMMAND` | WO/W1P | bit0 ARM、bit1 ABORT、bit2 CLEAR_EVENT；一次只允许一位 |
| `0xA8` | `ACQ_STATE` | RO | state enum 与 ARMED/TRIGGERED/LOCK_ACTIVE/FAULT flags |
| `0xAC` | `EVENT_SEQUENCE` | RO | 每次 accepted ARM/trigger/fault 单调增加 |
| `0xB0` | `EVENT_OUT2` | RO | 触发拍实际 signed OUT2 |
| `0xB4` | `EVENT_ERROR` | RO | 触发拍实际 signed ERROR |
| `0xB8` | `EVENT_CONFIG_GENERATION` | RO | 本次 active generation |
| `0xBC` | `EVENT_INFO` | RO | 实际 scan dir、ERROR crossing dir、原因、fault code |
| `0xC0` | `EVENT_TIMESTAMP_LO` | RO | FPGA cycle counter low |
| `0xC4` | `EVENT_TIMESTAMP_HI` | RO | FPGA cycle counter high |
| `0xC8` | `ACTIVE_TARGET_OUT2` | RO | ARM snapshot readback |
| `0xCC` | `ACTIVE_ERROR_SETPOINT` | RO | ARM snapshot readback |
| `0xD0` | `ACTIVE_WINDOW` | RO | ARM snapshot readback |
| `0xD4` | `ACTIVE_REQUIREMENTS` | RO | ARM snapshot readback |
| `0xD8` | `ACTIVE_CORRECTION_LIMIT` | RO | ARM snapshot readback |
| `0xDC` | `ACTIVE_ABSOLUTE_LIMIT` | RO | ARM snapshot readback |
| `0xE0` | `FAULT_DETAIL` | RO | sticky reject/runtime fault detail |

建议 state enum：

```text
0 SAFE
1 SCAN
2 ARMED
3 TRIGGER_CAPTURE
4 P_LOCK_KP0
5 P_LOCK_ACTIVE
6 FAULT
```

契约规则：

- 所有命令为 write-one-pulse；命令寄存器读回 0。
- `ARM` 只做一次 shadow-to-active snapshot，不直接触发。
- `ABORT` 优先级高于 trigger，并进入 SAFE。
- event payload 必须 coherent；读取顺序不能混合两个事件。软件应先读 `EVENT_SEQUENCE`，读 payload，再重读 sequence，不一致则重试。
- `CAPTURE_LOCK_POINT` 在兼容期可以保留为 legacy diagnostic command，但新的正常路径不得调用它。
- 实现该契约必须提升 `VERSION` 并拒绝旧 host/new bitstream 错配；本设计不指定最终 VERSION 数值。

## 9. 软件与 RTL 验收矩阵

| 层级 | 场景 | 必须结果 |
|---|---|---|
| RTL | reset/SAFE | state SAFE、Kp=Ki=0、未 armed、输出 SAFE |
| RTL | shadow 部分写入 | active transaction 不变化 |
| RTL | valid ARM | 同拍复制全部 active fields，下一状态 ARMED，scan 连续 |
| RTL | invalid ARM | 保持 SCAN、无 trigger、`CONFIG_REJECTED` 可读 |
| RTL | 正确窗口但错误 scan direction | 不触发 |
| RTL | 正确 scan direction 但窗口外 | 不触发 |
| RTL | 方向和窗口正确但无指定 ERROR crossing | 不触发 |
| RTL | `NEG_TO_POS` / `POS_TO_NEG` | 只接受配置的 crossing direction |
| RTL | 全部条件同拍成立 | 单次进入 TRIGGER_CAPTURE，event 只生成一次 |
| RTL | bumpless | trigger 前 OUT2、captured bias、首个 Kp=0 OUT2 完全相等 |
| RTL | host 延迟/停止轮询 | ARMED 后触发拍不受 host 行为影响 |
| RTL | ABORT 与 trigger 同拍 | ABORT 优先，进入 SAFE，不生成成功 trigger |
| RTL | saturation/runtime fault | 进入 FAULT、SAFE 输出、sticky fault/event |
| RTL | event readback | actual OUT2/ERROR/directions/generation/timestamp coherent 且保持到 clear |
| RTL | arithmetic boundaries | signed target、窗口差值、limits 不 overflow/wrap |
| Host | target build | confirmed capture 生成两个独立 direction enum 和 generation |
| Host | preload + ARM | 完整写 shadow、检查 validation、单次 ARM；不调用 target polling |
| Host | state handling | 正确区分 SCAN/ARMED/TRIGGERED/P_LOCK_KP0/FAULT/stale event |
| Host | event coherent read | sequence 前后检查，generation 必须匹配当前 target |
| Host | timeout/disconnect | 不补发 `CAPTURE_LOCK_POINT`，不推断 FPGA 已触发；可由用户请求 ABORT/SAFE |
| Integration | 任意 Linux poll interval | 相同输入波形得到相同 FPGA trigger sample 和 event |

通过软件和 RTL 验收只允许标记 `[AUTOMATED VERIFIED]`。Kp=0 真实 OUT2、loaded PZT、谱峰位置、最小非零 Kp 和持续锁定在用户实验前全部保持 `[NOT VERIFIED]`。

## 10. 第一版边界

第一版只完成：

```text
capture -> user select -> confirm
-> preload target -> ARM
-> FPGA wait for direction + target window + ERROR crossing
-> atomic P_LOCK_KP0
-> host reads state/event
-> later user-approved minimal P-only
```

第一版不做完整 Linien 谱形匹配、谱线自动识别、PI/Ki、自动 polarity、自动增益、自动重锁、机器学习或长期稳频判断。

## 11. 当前 GUI 功能债务与处理策略

| 债务 | 当前事实 | 后续策略 |
|---|---|---|
| `custom_arm_auto_lock_button` | 已创建但隐藏，当前正常路径未使用 | D1-C 时复用或删除重复按钮，只保留一个语义明确的 ARM 入口 |
| `BASIC LOCK` | 点击后首先只自动排队 `SAFE -> SCAN -> CAPTURE`，随后仍需用户选点/确认；名称暗示已完成锁定 | D1-C 改名为 acquisition setup 或拆成显式步骤，不把 capture 成功写成 lock |
| `PI_LOCK` / Ki | UI/寄存器保留候选，Ki 控件禁用；当前 controller 对 P_LOCK/PI_LOCK 使用同一 P-only 路径，`ki_i` 不参与控制 | D3 前隐藏/标记 unsupported，不实现 PI |
| manual `lock-bias-v` | 用于直接 P/PI candidate 配置，不用于正常 `LOCK HERE` | deterministic 路径删除其歧义或标为 legacy/manual diagnostic |
| Target wait | Linux 轮询诊断，不是 FPGA 状态 | D1-C 从正常路径删除，改读 `ARMED/TRIGGERED` |
| selected-to-captured delta | host 诊断值，不是真实 FPGA 时钟级 jump | 保留为历史诊断；以 event OUT2 和 RTL bumpless assertion 作为数字切换证据 |

本 Gate 只记录这些债务，不删除或修改现有 Python/RTL 代码。
