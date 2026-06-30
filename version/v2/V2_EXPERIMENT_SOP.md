# V2_EXPERIMENT_SOP

## 2026-06-30 v2B3 Timing Clean And First Scan/Lock SOP Boundary

Timing record from user manual Vivado Implementation:

```text
WNS = +0.107 ns
TNS = 0.000 ns
Failing Endpoints = 0
WHS = 0.054 ns
THS = 0
Conclusion: mode=1 sequential PI candidate is timing clean.
```

This result means the current mode=1 sequential PI candidate passed timing. It
does not mean the laser is locked, and it does not authorize connecting OUT2 to
the laser, D2-125 Servo Output, D2-125 Aux/Scan, or any real actuator.

Current valid check:

```text
OUT1 -> oscilloscope: FPGA laser_error / error observation.
OUT2 -> oscilloscope: FPGA laser_control / sequential PI candidate.
```

Future first scan/lock experiment SOP, after register/mode RTL exists and after
separate approval:

```text
1. IN1 <- PD BPF/amp signal, verified within +/-1 V.
2. IN2 <- REF signal, verified within +/-1 V.
3. OUT1 -> oscilloscope CH2: FPGA error.
4. OUT2 -> oscilloscope CH4: do not connect to laser yet.
5. SAFE: confirm OUT2 = 0.
6. SCAN: confirm small triangle on OUT2.
7. Disconnect D2-125 Aux Servo Output from laser Scan.
8. Only after step 7, connect RP OUT2 to laser power Scan/PZT.
9. Confirm spectrum sweep.
10. Near a zero crossing, Capture Vlock.
11. HOLD.
12. Later, after review, P_LOCK then PI_LOCK.
```

Stop immediately if:

```text
IN1/IN2 exceeds +/-1 V.
OUT1 disappears or saturates unexpectedly.
OUT2 exceeds output_limit or approaches +/-1 V.
OUT2 jumps randomly, ramps unexpectedly, or direction is unknown.
D2-125 Aux/Scan is still connected while RP OUT2 is being considered.
```

## 2026-06-23 v2B3 sequential PI mode=1 上板示波器预期现象

### 接线和绝对边界

```text
IN1 <- PD 经 v1 既有带通/放大链路后的信号，确认在 +/-1 V 内。
IN2 <- 同路解调 REF，确认在 +/-1 V 内。
OUT1 -> 示波器 CH2。
OUT2 -> 示波器 CH4。

禁止：OUT2 -> 激光器；OUT2 -> D2-125 Servo Output；
OUT2 -> D2-125 Scan/Aux/Current/PZT；D2-125 DC Error -> IN1；
以及任何超过 +/-1 V 的 IN1/IN2 输入。
```

### mode=1 正常现象

```text
OUT1/CH2：仍应看到板内 mixer + LPF 后的 FPGA 解调 error。
若 OUT1 消失，立即停止；说明主 error 链路可能被破坏。

OUT2/CH4：是 sequential PI 输出，不再要求严格等于 OUT1 的一半。
短时间内它可能仍很像 P-only；若同号 error 长时间存在，小 Ki 可造成缓慢基线移动。
OUT2 仍应受 output_limit 限制，不应接近 +/-1 V、随机跳变、快速爬升或快速饱和。
```

### mode=1 异常和停止条件

```text
OUT1 消失：停止，检查 OUTPUT_MODE、mixer_core、lpf_core、output_protect。
OUT2 一直为 0：停止，检查 LASER_LOCK_CONTROL_PATH_MODE=1 和 pi_controller_seq.sv 是否在 Design Sources。
OUT2 严格等于 OUT1 的一半：可能仍在 mode=0 P-only fallback，停止并检查顶层参数。
OUT2 快速爬升：停止，Ki、极性或积分器逻辑可能异常。
OUT2 接近 +/-1 V：立即停止，不进入任何闭环测试。
Vivado timing failed：不得生成可上板 bitstream，也不得烧录。
```

## 2026-06-22 v2B2/v2B3 sequential PI 上板前 SOP（当前有效）

新的 `pi_controller_seq.sv` 已通过独立 XSim，`laser_lock_core.sv` 的 `CONTROL_PATH_MODE=1` 也已通过集成 XSim；这只证明 RTL/SIM 行为，尚不代表板级 timing 或硬件输出已通过。

上板前由用户手动确认：

```text
1. pi_controller_seq.sv 已加入 Vivado Design Sources。
2. CONTROL_PATH_MODE 默认仍为 0；不要仅为上板而提前改成 1。
3. Synthesis/Implementation 完成后，WNS >= 0、TNS = 0。
4. 确认最差路径不在 pi_controller_seq 内部。
5. timing 通过后才允许为 mode 1 生成 bitstream。
```

首次 mode 1 示波器验证只允许：

```text
OUT1 -> CH2，继续观察 FPGA mixer+LPF error。
OUT2 -> CH4，观察 sequential PI 的 P-only 和小 Ki 行为。
OUT2 禁止接激光器、D2-125 Servo Output、Scan、PZT 或 current 执行器。
D2-125 DC Error 禁止接 Red Pitaya IN1。
```

通过条件是 OUT1 不被破坏、OUT2 对 error 的方向和限幅可解释、无异常跳变或不可解释积分爬升。即使通过，也仍是 OUT2 开环示波器验证，不是激光锁定或 D2-125 替代。

## 2026-06-22 v2B1 timing-safe P-only Shadow Control 上板示波器记录（当前有效）

本次用户已完成 Vivado 重新综合、实现、bitstream 生成和 Red Pitaya 烧录。记录的 implementation timing 为 `WNS=+0.361 ns`、`TNS=0.000 ns`、`Failing Endpoints=0`，因此本次烧录对应 timing 通过的设计。

### 实验边界

```text
OUT1：接示波器，观察 FPGA mixer+LPF error。
OUT2：接示波器，观察 timing-safe P-only shadow control。
OUT2 没有接激光器、D2-125 Servo Output、Scan 或其他执行器。
```

### 示波器数据

| 数据文件 | OUT2 Vpp / RMS | OUT1 Vpp / RMS | OUT2 / OUT1 |
|---|---:|---:|---:|
| `mixer.csv` | `0.01771 V` / `0.007694 V` | `0.03439 V` / `0.003643 V` | `0.515` |
| `no-mixer.csv` | `0.02644 V` / `0.006752 V` | `0.04768 V` / `0.004388 V` | `0.555` |

同步记录：

```text
mixer.csv
  Saturated absorption peak: Vpp=0.1893 V, RMS=0.8157 V
  D2-125 error signal:      Vpp=1.829 V, RMS=0.3469 V

no-mixer.csv
  Saturated absorption peak: Vpp=0.1793 V, RMS=0.8147 V
  D2-125 error signal:      Vpp=0.0402 V, RMS=0.2935 V
```

### 实验结论

```text
2026-06-22 v2B1 timing-safe P-only Shadow Control 上板示波器测试完成。

1. OUT1 能输出 FPGA mixer+LPF 后的 error signal，幅度为几十 mVpp。
2. OUT2 能输出由 OUT1 派生的 P-only shadow control。
3. OUT2 / OUT1 比例约为 0.5。
4. OUT2 没有打到 +/-1 V。
5. OUT2 没有出现明显失控、饱和或积分爬升。
6. 该现象与 RTL 中 protected_error >>> 1 的 timing-safe P-only 设计一致。

阶段结论：v2B1 的 OUT2 控制输出通道已经打通。
当前版本可作为“OUT2 安全输出验证通过”的实验记录。
```

### 小白解释：小幅度是安全现象

OUT2 目前只承担“影子控制量”观察任务。`laser_lock_core.sv` 默认使用 `USE_FULL_PI_CONTROLLER=0`，把 `protected_error` 经过 `>>> 1` 变成半幅 P-only 输出；没有数字增益放大，也没有完整 PI 的积分累积。因此 OUT1/OUT2 只有几十 mVpp 是当前安全验证的预期，而不是输出失败。

### 严格限制

```text
当前版本不是完整 PI，也不是 PID。
当前版本不能锁定激光，不能声称替代 D2-125。
OUT2 仍然只能接示波器；禁止接激光器、D2-125 Servo Output 或 Scan。
D2-125 DC Error 禁止接 Red Pitaya IN1。
```

## 2026-06-16 v2B1 timing-safe P-only Shadow Control 上板前 SOP（当前有效）

本节覆盖后续所有“完整 PI 直接接 OUT2”或“D2-125 DC Error 旁路进 Red Pitaya”的旧描述。当前有效实验目标只有一个：在 Vivado timing 重新通过后，让 OUT2 输出一个很小的 P-only shadow control，并且 OUT2 第一阶段只接示波器。

当前允许看到的信号：

```text
OUT1 / CH2：FPGA mixer+LPF error，预计仍约 0.12~0.15 V
OUT2 / CH4：timing-safe P-only shadow control，预计约为 OUT1 的 1/2
OUT2 limit：PID_OUTPUT_LIMIT_DEFAULT=1500，约 +/-0.18 V，不是 +/-1 V
```

当前 RTL 含义：

```text
pi_controller.sv：保留完整 PI，不修改，不作为 v2B1 默认板级路径。
laser_lock_core.sv：默认 USE_FULL_PI_CONTROLLER=0，使用 protected_error >>> 1 的 timing-safe P-only 路径。
```

烧录前硬性条件：

```text
必须手动重新 Run Synthesis。
必须手动重新 Run Implementation。
必须确认 timing 通过，WNS/TNS 不再是负值阻塞。
只有 timing 通过后才允许 Generate Bitstream。
timing fail 的 bitstream 不允许烧录。
```

示波器接线：

```text
OUT1 -> 示波器 CH2
OUT2 -> 示波器 CH4
OUT2 不接激光器
OUT2 不接 D2-125 Servo Output
OUT2 不接 D2-125 Scan / Aux / Current / PZT 控制端
```

如果 OUT2 接近 `+/-1 V`、随机跳变、慢慢爬升、或 OUT1 原有 error 消失，立即停止，不进入激光闭环。

## 2026-06-14 v2B1 FPGA MTS Error Shadow PI 上板前 SOP（当前有效）

本节覆盖本文档中旧的“D2-125 DC Error -> Red Pitaya IN1”旁路线描述。当前安全主线不是把 D2-125 的 DC Error 或 Servo Output 接进 Red Pitaya，而是使用 Red Pitaya 自己的 IN1/IN2 生成 FPGA 内部 error。

### 当前允许接线

```text
Red Pitaya IN1 -> 混频前 PD/MTS 信号，必须在 +/-1 V 内
Red Pitaya IN2 -> 外部 REF，必须在 +/-1 V 内
Red Pitaya OUT1 -> 示波器 CH2：FPGA mixer+LPF error，当前约 0.12~0.15 V
Red Pitaya OUT2 -> 示波器 CH4：FPGA P-only control
```

### 当前 FPGA 数据链路

```text
IN1 + IN2
-> mixer_core
-> lpf_core
-> output_protect
-> error_o
-> OUT1

同时：

error_o
-> pi_controller
-> control_o
-> OUT2
```

### 禁止接线

```text
D2-125 DC Error -> Red Pitaya IN1
D2-125 Servo Output -> Red Pitaya IN1
Red Pitaya OUT2 -> 激光器
Red Pitaya OUT2 -> D2-125 Servo Output 三通
Red Pitaya OUT2 -> 激光器电源 Scan
任何超过 +/-1 V 的信号进入 IN1/IN2
```

### 用户手动 Vivado 操作

Codex 本次只修改 RTL/SIM/MD，并运行独立 XSim，不运行 Vivado，不生成 bit/bin，不烧录。

```text
1. 用户打开 v0.94/project/redpitaya.xpr
2. 用户在 Sources 中确认 pi_controller.sv 是否已经加入
3. 如果没有，用户手动 Add Sources：
   v0.94/rtl/pi_controller.sv
4. 用户确认 laser_lock_core.sv、red_pitaya_top.sv 使用的是 v0.94/rtl 下的文件
5. 用户手动 Run Synthesis
6. 用户手动 Run Implementation
7. 用户手动 Generate Bitstream
8. 用户自行烧录 Red Pitaya
```

### 正确实验现象

```text
1. OUT1 / CH2 仍能看到 FPGA mixer+LPF error，约 0.12~0.15 V
2. OUT2 / CH4 能看到跟 OUT1 同步的小控制信号
3. OUT1 为正时，OUT2 同向变化，除非 polarity 设为反向
4. OUT1 过零时，OUT2 也应过零
5. OUT2 不应超过约 +/-0.18 V
6. OUT2 不应打到 +/-1 V
7. Ki=0 时，OUT2 不应慢慢爬升
8. OUT2 不应随机跳变
9. OUT2 第一轮只接示波器
```

### 异常现象和下一步

```text
OUT2 一直为 0：
检查 laser_lock_core 是否真正接入 pi_controller，red_pitaya_top 是否将 DAC B 接到 laser_control。

OUT2 方向反了：
下一版只改 PID_POLARITY_DEFAULT。

OUT2 太小：
下一版可把 PID_KP_DEFAULT 从 2048 提高到 4096。

OUT2 太大或接近 +/-1 V：
立即停止，降低 PID_KP_DEFAULT 和 PID_OUTPUT_LIMIT_DEFAULT，检查 DAC B 路由和 saturation。

OUT2 慢慢爬升：
确认 PID_KI_DEFAULT = 0，检查 reset_integrator 和 enable。

OUT1 被破坏：
回退，检查 OUTPUT_MODE=3、mixer_core、lpf_core、output_protect 是否被误改。
```

## 2026-06-14 旧方案记录：v2B1 Shadow PI DC Error 实验 SOP（已废弃 / 禁止执行）

> 注意：本节保留为历史记录，不再作为当前实验 SOP。禁止执行“D2-125 DC Error -> Red Pitaya IN1”。当前有效 SOP 是本文档最前面的“v2B1 FPGA MTS Error Shadow PI 上板前 SOP”。

当前真实接线：

```text
D2-125 Ramp -> 示波器 CH1
D2-125 DC Error -> 示波器 CH3
模拟 mixer 后 error -> D2-125 Error Input
D2-125 Servo Output -> 三通 -> 激光器电源 / 激光器锁定控制端
D2-125 Aux Servo Output -> 激光器电源 Scan
Red Pitaya OUT2 -> 后续示波器 CH4
```

v2B1 目标：

```text
D2-125 DC Error Monitor
-> Red Pitaya IN1
-> pi_controller.sv
-> Red Pitaya OUT2
-> 示波器 CH4
```

实验前：

```text
1. 保持 D2-125 原锁定链路不变；
2. 确认 D2-125 可以正常扫到谱线并锁定；
3. 确认 CH1 = D2-125 Ramp；
4. 确认 CH3 = D2-125 DC Error；
5. Red Pitaya OUT2 不接任何激光器输入。
```

上板第一轮：

```text
1. 烧录 v2B1 bitstream；
2. Red Pitaya IN1 接 D2-125 DC Error Monitor；
3. Red Pitaya OUT2 接示波器 CH4；
4. D2-125 继续锁定激光；
5. 观察 CH3 和 CH4 的关系。
```

判断标准：

```text
CH3 接近 0 时，CH4 应接近 0 或小范围变化；
CH3 正负变化时，CH4 应有对应方向变化；
CH4 不能随机跳变；
CH4 不能长时间饱和；
CH4 不能超过 output_limit；
Ki=0 时，CH4 不应出现积分式慢慢爬升。
```

禁止事项：

```text
OUT2 不接激光；
OUT2 不与 D2-125 Servo Output 并联；
不替代 D2-125 Ramp；
不替代 D2-125 Aux Servo Output；
不做 scan/lock 状态机；
不声称 FPGA 已锁定激光。
```

本文档服务于 v2 FPGA PI/PID 替代 D2-125 阶段。

## 1. 上板前检查

上板前必须确认：

- `pi_controller.sv` testbench PASS；
- P-only 测试 PASS；
- I 项测试 PASS；
- anti-windup 测试 PASS；
- output limiter 测试 PASS；
- reset / enable / hold / reset_integrator 测试 PASS；
- v1 OUT1 error 输出路径仍可回退；
- GPT 已审查设计；
- Claude Code 已审查 RTL；
- 当前 bit/bin 对应的参数已记录。

## 2. bit/bin 烧录前检查

烧录前记录：

- 日期；
- git / 文件版本，如果可用；
- bit/bin 文件名；
- top 参数；
- `pid_ce` 更新频率；
- `kp_i`；
- `ki_i`；
- `output_limit_i`；
- `offset_i`；
- `enable_i` 默认值；
- `polarity_i` 默认值；
- OUT2 接线。

默认要求：

```text
enable_i = 0
kp_i = 0 或极小
ki_i = 0
output_limit_i = 很小
control_o = 0
```

## 3. OUT2 接示波器测试步骤

第一轮只允许：

```text
Red Pitaya OUT2 -> 示波器
```

不允许：

- OUT2 接激光器；
- OUT2 接 D2-125 输出端；
- OUT2 接任何未知输入；
- 闭环。

测试：

1. reset 后 OUT2 是否为 0；
2. `enable=0` 时 OUT2 是否为 0；
3. `enable=1, kp=0, ki=0` 时 OUT2 是否为 0；
4. 小 `kp` 时 OUT2 是否随 error 变化；
5. `polarity_i` 翻转后 OUT2 方向是否翻转；
6. `output_limit_i` 改小时 OUT2 是否被限制；
7. `hold_i` 时 OUT2 是否冻结或保持定义行为；
8. `reset_integrator_i` 后 I 项是否清零。

## 4. 不接激光时的测试步骤

使用函数发生器或仿真风格输入模拟 error：

- 低频正弦；
- 低频三角波；
- 阶跃；
- 固定正偏差；
- 固定负偏差。

观察：

- 输出方向；
- 输出限幅；
- 积分累加；
- windup；
- reset；
- enable；
- 随机跳变。

## 5. 接入实验链路前必须满足的条件

必须全部满足：

- OUT2 示波器测试通过；
- 无随机跳变；
- 无 reset 后异常输出；
- `enable=0` 安全；
- `output_limit_i` 有效；
- 初始 `kp/ki` 很小；
- `ki_i` 可先设为 0；
- `reset_integrator_i` 操作明确；
- 用户知道如何立即断开反馈；
- GPT 判断可以进入低增益测试。

## 6. 初始 Kp/Ki 要求

初始参数：

- 先 `P-only`；
- `ki_i=0`；
- `kp_i` 从极小值开始；
- P-only 输出方向确认后，再加入很小 `ki_i`；
- 每次只改一个参数；
- 每次记录示波器截图和参数。

## 7. enable 默认关闭

所有上板版本默认：

```text
enable_i = 0
```

操作顺序：

1. 烧录 bit/bin；
2. 确认 OUT2 为 0；
3. 确认示波器接线；
4. 确认 output limit；
5. reset integrator；
6. 设置极小 Kp/Ki；
7. 手动 enable；
8. 随时准备 disable。

## 8. reset_integrator 操作流程

使用场景：

- 每次 enable 前；
- 每次改变 `ki_i` 前；
- 输出饱和后；
- 误接极性导致发散后；
- 从 hold 恢复前。

流程：

```text
disable -> reset_integrator -> 检查 OUT2 -> 设置参数 -> enable
```

## 9. 异常处理

### 出现振荡

立即：

- disable；
- reset_integrator；
- 降低 `kp_i`；
- `ki_i` 设为 0；
- 检查 polarity；
- 回到 OUT2 示波器测试。

### 出现削顶

立即：

- disable；
- 降低 `output_limit_i`；
- 检查 offset；
- 检查 P/I sum；
- 检查是否 windup。

### 输出饱和

立即：

- disable；
- reset_integrator；
- 检查 anti-windup；
- 降低 `ki_i`；
- 降低 `kp_i`；
- 检查是否 error 输入 offset 过大。

### 疑似正反馈

立即：

- disable；
- 切换 `polarity_i`；
- 从 P-only 小增益重测；
- 不允许带 I 项直接重试。

## 10. 与 D2-125 对比

对比时记录：

- D2-125 是否能锁；
- FPGA PI 是否能锁；
- 锁定时间；
- 锁定持续时间；
- error RMS；
- control 输出是否饱和；
- 是否发散；
- 是否需要手动重置；
- 极性是否一致；
- 相同 error signal 下噪声是否变化。

对比原则：

- D2-125 是 v2 的基准；
- FPGA PI 第一版只要求安全可控，不要求立刻优于 D2-125；
- 若 FPGA PI 不稳定，回退 D2-125，不继续硬推。
