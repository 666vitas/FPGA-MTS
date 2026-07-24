Status: ACTIVE
Effective-Gate: ALL
Authority: SPEC
Last-Updated: 2026-07-24
Supersedes: FPGA_MTS_Linien_Basic_Lock_Project_Spec.md
Superseded-By: NONE

# FPGA-MTS 最基础锁定项目说明书

**项目名称：** MTS P-only Lock MVP（Linien-inspired）  
**目标硬件：** Red Pitaya STEMlab 125-14  
**当前信号约定：** IN1=PD，IN2=REF，OUT1=MTS error，OUT2=PZT/Scan  
**文档版本：** 1.0  
**核心目标：** 在不重写整个项目的前提下，实现一次真实、可重复、无明显谱峰偏移的 P-only 激光锁定，并建立可逐步演进为 Linien 式系统的软件边界。

---

## 1. 项目结论

当前项目并不缺少“功能模块”。现有工程已经具备：

- FPGA 三角波扫描；
- MTS mixer/LPF error signal；
- SAFE、SCAN、HOLD、P_LOCK 模式；
- P-only 控制器；
- 自定义波形 capture RAM；
- FPGA 寄存器读写；
- GUI 中的扫描、选点和 Kp 操作；
- deterministic acquisition/ARM 原型。

当前真正缺少的是一条经过真实硬件验证的最小闭环：

```text
SCAN
→ 获取真实且对齐的 PD / ERROR / OUT2
→ 选择零交叉
→ 精确 HOLD
→ 补偿扫描转静态后的迟滞与漂移
→ P_LOCK Kp=0 无扰切换
→ 最小非零 Kp 验证负反馈方向
→ 连续保持锁定
→ 异常 SAFE
```

因此，本项目不采用“完整复制 Linien”或“推倒重写”的路线，而采用：

```text
保留现有 FPGA 实时数据通路
+ 冻结复杂 ARM 获取逻辑
+ 建立最小统一控制服务
+ 完成真实 P-only 硬件闭环
+ 再把控制服务迁移到 Red Pitaya 常驻进程
```

---

## 2. 当前项目的主要问题

### 2.1 P0：当前新 RTL 尚未 timing closure

当前 deterministic acquisition 版本仍存在 setup timing failure。行为仿真通过不代表该 bitstream 可以可靠运行在 125 MHz 实际硬件上。

**处理原则：**

- 创建 `LOCK_MVP_BUILD`；
- deterministic ARM 不参与该构建；
- 只保留 mixer/LPF、SCAN、HOLD、P_LOCK、capture、limits、SAFE；
- 必须先达到 WNS≥0、TNS=0、WHS≥0、无 unconstrained path，才烧录上板。

ARM 源码和测试保留在 `D1_ARM_BUILD`，但不再阻塞第一次真实锁定。

### 2.2 P0：没有真实闭环证据

目前已证明可以扫描、观察 error 并选择零点，但尚未证明：

- Kp=0 切换在带 PZT 负载时无明显跳变；
- Kp=4 等最小非零增益构成负反馈；
- error RMS 在闭环后降低；
- 谱峰不再相对 cursor 偏移；
- 锁定可持续至少 60 秒。

项目完成度必须以真实硬件测量为准，而不是代码行数、GUI 页面或仿真数量。

### 2.3 P0：扫描点到静态工作点之间存在真实物理偏差

扫描状态下选中的 OUT2 位置，停止扫描后可能因以下因素改变：

- PZT 和激光器迟滞；
- rising/falling 扫描方向差异；
- 扫描速度与静态保持状态不同；
- PZT 实际节点电压与命令侧校准不同；
- 激光器热漂移或模式跳变；
- error signal 偏置、噪声或线形变化。

因此，不能把“扫描时选中的 OUT2 count”直接等同于“静态锁定时的正确 bias”。必须加入 HOLD 后的软件慢速 approach。

### 2.4 P0：带负载 OUT2 校准不完整

当前校准主要是命令侧估计。基础锁定前必须记录：

- OUT2 command counts；
- PZT 与示波器实际连接时的节点电压；
- 中心值和相对幅度；
- rising/falling 时同一谱峰对应的 OUT2；
- HOLD 后的静态偏移。

### 2.5 P1：GUI 同时承担界面、状态机、安全和硬件访问

当前 GUI 会读取输入框、检查安全范围、构造参数、创建 SSH Worker、调用 backend、维护多个状态标志并更新按钮。这会造成：

- 状态存在多份副本；
- GUI 标签与 FPGA readback 可能不一致；
- 自动流程难以测试；
- 通信失败后的 SAFE 行为分散；
- 后续迁移到板端 server 困难。

### 2.6 P1：寄存器协议和文档存在漂移

寄存器地址、版本号和换算逻辑分散在 RTL、Python backend、远程 helper 和文档中。当前文档中仍存在旧版本号或旧 capture 描述，与当前 RTL/STATUS 不完全一致。

**处理原则：** 建立一个唯一的寄存器描述和一个自动生成/校验机制，至少确保：

- `MAGIC`；
- `VERSION`；
- 地址；
- signed14 编解码；
- 读写属性；
- W1P 命令；
- 单位换算；

不再由 GUI 或多个脚本分别硬编码。

### 2.7 P1：项目范围持续扩张

deterministic ARM、自动锁定、GUI 诊断、PI、AI、规则和审查同时推进，使最关键的 P-only 硬件闭环没有成为唯一 Gate。

本说明书明确冻结：

- PI/Ki；
- 自动重锁；
- IQ 重构；
- 机器学习；
- PSD；
- 快慢双通道；
- 大规模 GUI 改版；
- 复杂 ARM 时序优化。

---

## 3. “Linien 式最基础锁定”的定义

这里不复制 Linien 全部功能，只采用四个最重要的设计原则。

### 3.1 GUI 是客户端，不是硬件控制器

GUI 只负责：

- 显示参数和真实波形；
- 接收用户命令；
- 展示当前状态、失败原因和安全警告。

GUI 不负责：

- 寄存器地址；
- SSH 命令；
- `/dev/mem`；
- approach 循环；
- 状态迁移；
- SAFE 决策。

### 3.2 一个控制服务拥有系统状态

所有命令必须进入统一 `LockService`。它是唯一状态机，负责：

- SCAN；
- 目标选择确认；
- HOLD；
- approach；
- P_LOCK Kp=0；
- Kp 阶梯；
- 失败回 SAFE。

### 3.3 FPGA 负责实时控制

FPGA 负责：

- 三角波扫描；
- mixer/LPF；
- aligned capture；
- P-only 乘法和限幅；
- 模式选择；
- 实时 SAFE/饱和保护。

Windows、Linux 或网络不得参与每个 servo sample 的计算。

### 3.4 板端服务最终应常驻

第一阶段为了尽快完成真实锁定，可让 `LockService` 暂时运行在 Windows，并继续复用 SSH+/dev/mem transport。

真实锁定通过后，将同一个 `LockService`、`RegisterMapper` 和 `AcquisitionService` 移到 Red Pitaya 常驻进程：

```text
Windows GUI / Python Client
            ↓ RPC
Red Pitaya Lock Server
            ↓
RegisterMapper + AcquisitionService
            ↓ mmap /dev/mem
FPGA realtime scan / capture / P servo
```

迁移前后 API 不变，避免再次重写 GUI。

---

## 4. 系统目标架构

```text
┌───────────────────────────────────────────────┐
│ Windows GUI                                   │
│ - 参数输入                                    │
│ - 波形显示                                    │
│ - 用户命令                                    │
│ - 不包含寄存器和控制状态机                    │
└──────────────────────┬────────────────────────┘
                       │ LocalClient / RPC Client
┌──────────────────────▼────────────────────────┐
│ LockService                                   │
│ - 唯一状态机                                  │
│ - SCAN/HOLD/APPROACH/P_LOCK/SAFE              │
│ - 参数验证                                    │
│ - 故障处理                                    │
└───────────────┬─────────────────┬─────────────┘
                │                 │
┌───────────────▼────────┐ ┌──────▼──────────────┐
│ RegisterMapper          │ │ AcquisitionService  │
│ - 参数→CSR              │ │ - capture_once      │
│ - signed14              │ │ - monitor sampling  │
│ - 写顺序/readback       │ │ - frame generation  │
│ - 版本兼容              │ │ - statistics        │
└───────────────┬────────┘ └──────┬──────────────┘
                │                 │
┌───────────────▼─────────────────▼──────────────┐
│ Transport                                     │
│ Phase A: SSH + /dev/mem adapter               │
│ Phase B: board-local mmap                     │
└──────────────────────┬────────────────────────┘
                       │
┌──────────────────────▼────────────────────────┐
│ FPGA                                          │
│ mixer/LPF → error                             │
│ ramp_generator → SCAN                         │
│ custom_debug_capture → aligned frame          │
│ out2_lock_controller → P-only                 │
│ custom_register_bank → CSR                    │
└───────────────────────────────────────────────┘
```

---

## 5. 推荐目录结构

第一阶段只增加最少文件，不立即拆毁现有 GUI 和 backend。

```text
software/redpitaya_lock_host/redpitaya_lock_host/
├── main_window.py                    # 现有 GUI，逐步变为 adapter
├── custom_fpga_backend.py            # 现有底层，暂作 transport adapter
├── connection_workers.py             # 暂时保留
├── common/
│   ├── models.py                     # 请求、结果、Frame、枚举
│   └── parameters.py                 # 唯一公开参数定义
├── core/
│   ├── lock_service.py               # 唯一状态机
│   ├── register_mapper.py            # 唯一寄存器知识
│   ├── acquisition_service.py        # 真实 capture 和统计
│   └── safety_service.py             # 安全条件和 SAFE
└── client/
    └── local_client.py               # GUI 调用接口
```

真实 P-only 通过后再增加：

```text
├── server/
│   ├── board_server.py
│   └── rpc_protocol.py
└── client/
    └── rpc_client.py
```

---

## 6. 参数模型

### 6.1 用户可设置参数

```text
scan_center_v
scan_amplitude_v
scan_frequency_hz
pzt_safe_min_v
pzt_safe_max_v
polarity
kp_requested
correction_limit_v
```

### 6.2 派生只读参数

```text
scan_offset_counts
scan_amplitude_counts
scan_step_counts
scan_update_div
scan_actual_frequency_hz
safe_min_counts
safe_max_counts
correction_limit_counts
absolute_limit_counts
```

### 6.3 运行状态

```text
connected
fpga_magic
fpga_version
lock_state
mode_readback
enable_readback
saturated
capture_id
scan_generation
target_generation
selected_out2_counts
selected_error_setpoint_counts
selected_slope
selected_scan_direction
hold_out2_counts
lock_bias_counts
kp_applied
error_mean
error_std
error_rms
control_mean
control_std
last_failure_reason
```

### 6.4 参数原则

- GUI 不维护另一份硬件状态；
- FPGA readback 是硬件状态的唯一事实来源；
- 所有目标选择必须绑定 `capture_id` 和 `scan_generation`；
- 扫描参数改变后，旧 target 自动失效；
- 所有单位必须明确是 V、counts、Hz、秒或 raw fixed-point。

---

## 7. 状态机

```text
DISCONNECTED
    ↓ connect
SAFE
    ↓ start_scan
SCANNING
    ↓ select_target
TARGET_SELECTED
    ↓ enter_hold
HOLDING
    ↓ approach_target
APPROACHING
    ↓ target stable
READY_TO_LOCK
    ↓ enter_p_lock_kp0
P_LOCK_KP0
    ↓ apply_kp(4)
P_LOCK_ACTIVE

任何状态 ──通信异常/饱和/越界/超时──> FAILED ──> SAFE
```

### 7.1 合法命令

| 当前状态 | 合法命令 |
|---|---|
| SAFE | `start_scan()` |
| SCANNING | `capture_once()`、`select_target()`、`safe()` |
| TARGET_SELECTED | `enter_hold()`、`start_scan()`、`safe()` |
| HOLDING | `approach_target()`、`start_scan()`、`safe()` |
| APPROACHING | 内部 step、`abort()` |
| READY_TO_LOCK | `enter_p_lock_kp0()`、`safe()` |
| P_LOCK_KP0 | `apply_kp(4)`、`safe()` |
| P_LOCK_ACTIVE | `apply_next_kp()`、`safe()` |

任何非法状态调用必须返回结构化错误，不得偷偷写寄存器。

---

## 8. 核心数据结构

### 8.1 AcquisitionFrame

```python
@dataclass(frozen=True)
class AcquisitionFrame:
    capture_id: int
    scan_generation: int
    timestamp_monotonic: float
    sample_rate_hz: float
    sample_index: ndarray
    time_s: ndarray
    pd_counts: ndarray
    ref_counts: ndarray | None
    error_counts: ndarray
    out2_counts: ndarray
    mode: int
    enabled: bool
    saturated: bool
    valid: bool
    invalid_reason: str
```

### 8.2 TargetSelection

```python
@dataclass(frozen=True)
class TargetSelection:
    capture_id: int
    scan_generation: int
    clicked_index: int
    resolved_index: float
    out2_counts: int
    error_setpoint_counts: int
    slope_error_per_out2: float
    scan_direction: str
    error_crossing_direction: str
    local_noise_counts: float
    local_vpp_counts: float
```

### 8.3 CommandResult

```python
@dataclass(frozen=True)
class CommandResult:
    ok: bool
    state: LockState
    message: str
    readback: dict
    failure_code: str | None
```

---

## 9. 最基础锁定完整流程

### 9.1 CONNECT 与身份确认

1. 连接 `rp-f0cb13.local`；
2. 读取 `MAGIC`、`VERSION`、MODE、ENABLE、STATUS；
3. 版本不匹配时只允许读取和 SAFE，不允许 SCAN/LOCK；
4. 记录 host commit 与 FPGA version，但两者不得混为同一个版本。

### 9.2 SAFE

SAFE 必须执行：

```text
KP=0
KI=0
ENABLE=0
MODE=SAFE
integrator reset
```

然后 readback：

```text
MODE==SAFE
ENABLE==0
KP==0
KI==0
```

通信异常时执行 best-effort SAFE，并明确提示“SAFE 写入是否得到 readback”。

### 9.3 SCAN

用户输入中心、幅度、频率和安全范围。`LockService` 检查：

```text
safe_min < scan_center - scan_amplitude
scan_center + scan_amplitude < safe_max
范围在 Red Pitaya DAC 能力内
```

由 `RegisterMapper` 完成 counts 和 divider 换算。写入顺序：

```text
ENABLE=0
SCAN_OFFSET
SCAN_AMP
SCAN_STEP
SCAN_UPDATE_DIV
OUT2_LIMIT
MODE=SCAN
ENABLE=1
```

readback 必须确认：

```text
MODE=SCAN
ENABLE=1
SATURATED=0
```

扫描期间禁止热更新 center/amplitude/frequency。修改参数时必须 SAFE 后重新 SCAN，并递增 `scan_generation`。

### 9.4 CAPTURE

capture 至少覆盖 1.2 个扫描周期，推荐 1.5～2 个周期。必须获得同一采样时基的：

- CH1 PD；
- CH3 ERROR；
- CH4 OUT2。

不得把 preview 当成真实数据。frame 中任一关键通道为空、全零、饱和或 OUT2 超界时，目标选择被禁止。

### 9.5 SELECT TARGET

用户点击 ERROR 附近，服务端在有限搜索窗口内解析真实零交叉，而不是直接采用鼠标像素位置。

验证：

- capture_id 是最新 capture；
- scan_generation 未变化；
- 零交叉不在 buffer 边缘；
- 局部 Vpp 明显高于噪声；
- slope 非零；
- OUT2 在安全范围；
- 记录 rising/falling 方向。

### 9.6 HOLD

写入精确选中 OUT2 count：

```text
ENABLE=0
HOLD_VALUE=selected_out2_counts
MODE=HOLD
ENABLE=1
```

等待 PZT/激光器稳定，再读取：

- OUT2；
- ERROR mean/std/RMS；
- saturation。

HOLD readback 与目标 count 不一致时立即 SAFE。

### 9.7 软件慢速 APPROACH

这是解决“扫描 cursor 与静态谱峰偏移”的关键步骤。

算法：

1. 以 HOLD 后实际 OUT2 为起点；
2. 使用选点时测得的 slope 决定初始移动方向；
3. 每次只移动 1～4 counts；
4. 每步等待 5～20 ms，再采样 ERROR；
5. 目标是 `ERROR mean` 接近 `selected_error_setpoint`；
6. error 绝对值连续 N 次减小则继续；
7. error 变大、符号异常、越过局部范围或超时则停止并 SAFE；
8. 最大移动范围限制为用户安全范围与 correction limit 的交集。

软件 approach 只负责慢速找到静态工作点，不承担实时 servo。

建议停止条件：

```text
abs(error_mean - setpoint)
<= max(3 * error_noise_std, configured_error_tolerance_counts)
```

并连续保持 200～500 ms。

### 9.8 P_LOCK Kp=0 无扰切换

使用 approach 最终实际 OUT2 作为 `LOCK_BIAS`，使用目标 error 作为 `ERROR_SETPOINT`：

```text
KP=0
KI=0
POLARITY=用户选择
LOCK_BIAS=当前实际OUT2
CORRECTION_LIMIT=局部安全范围
LOCK_LIMIT=绝对范围
integrator reset
MODE=P_LOCK
ENABLE=1
```

readback 检查：

- MODE=P_LOCK；
- ENABLE=1；
- KP=0；
- KI=0；
- saturation=0；
- OUT2 数字命令跳变在允许范围内。

### 9.9 最小非零 Kp 和符号验证

第一步只允许 Kp=4。

在应用前记录 0.5～1 秒基线：

```text
error_mean_before
error_rms_before
out2_mean_before
```

应用 Kp=4 后观察 0.5～2 秒：

- error RMS 是否下降；
- error mean 是否更接近 setpoint；
- OUT2 是否朝恢复方向变化；
- 是否出现 saturation；
- 是否接近 correction limit。

若 error 快速增大、控制量撞限或谱峰远离目标：

```text
KP=0
ENABLE=0
MODE=SAFE
```

并提示 polarity 可能错误。第一版不自动反转 polarity。

只有 Kp=4 通过后，才允许：

```text
4 → 8 → 16 → 32
```

每一级都必须重新计算稳定性指标。

---

## 10. 安全规则

### 10.1 物理连接

- OUT2 只接激光器专用 PZT/Scan 输入；
- 禁止接激光器电流调制输入；
- 禁止与 D2-125 输出端并联；
- IN1/IN2 必须在 ±1 V ADC 范围内；
- 示波器地与系统地连接必须明确。

### 10.2 软件安全

以下任一情况立即 SAFE：

- SSH/RPC/mmap 异常；
- FPGA MAGIC/VERSION 不匹配；
- readback 与请求模式不一致；
- saturation；
- OUT2 越界；
- approach 超时；
- error 发散；
- control 撞 correction limit；
- capture 失效；
- target generation 过期。

### 10.3 correction limit 计算

对于最终 bias：

```text
left_margin  = bias - safe_min
right_margin = safe_max - bias
correction_limit = min(left_margin, right_margin, user_limit)
```

这样即使 FPGA 使用对称 correction limit，也能保证局部输出不越过用户批准的非对称 PZT 安全范围。

---

## 11. FPGA 构建要求

### 11.1 LOCK_MVP_BUILD

必须包含：

- `laser_lock_core` mixer/LPF；
- `ramp_generator`；
- `out2_lock_controller`；
- `custom_debug_capture`；
- SAFE/SCAN/HOLD/P_LOCK；
- Kp、polarity、bias、setpoint；
- correction/absolute limit；
- monitor/readback；
- MAGIC/VERSION。

必须关闭：

- deterministic acquisition ARM；
- shadow target snapshot；
- sticky acquisition event；
- ARM 相关高 fanout 与复杂决策路径；
- PI/Ki 功能入口（寄存器可保留但必须固定为0）。

### 11.2 D1_ARM_BUILD

- 保留现有完整 ARM 源码和测试；
- 与 LOCK_MVP_BUILD 分开综合；
- 不作为第一次真实锁定依赖；
- 基础锁定通过后再恢复开发。

### 11.3 时序 Gate

LOCK_MVP_BUILD 上板前必须满足：

```text
WNS >= 0 ns
TNS = 0 ns
WHS >= 0 ns
THS = 0 ns
unconstrained paths = 0
```

并保存：

- timing summary；
- worst paths；
- utilization；
- bitstream SHA/日期；
- FPGA VERSION。

---

## 12. 测试计划

### 12.1 单元测试

- 参数范围和单位；
- signed14 编解码；
- volts/counts 换算；
- register write order；
- readback mismatch；
- capture frame 验证；
- zero-crossing 解析；
- rising/falling slope；
- state transition；
- approach 正负方向；
- approach timeout；
- Kp ladder；
- communication failure SAFE。

### 12.2 Mock 集成测试

使用模拟 plant：

```text
error = slope * (out2 - target) + noise
```

覆盖：

- 正 slope；
- 负 slope；
- wrong polarity；
- PZT hysteresis offset；
- noise；
- saturation；
- target drift；
- communication loss。

### 12.3 RTL 测试

LOCK_MVP_BUILD：

- SAFE 输出；
- triangle scan；
- HOLD exact count；
- P_LOCK Kp=0；
- P correction sign；
- correction limit；
- absolute limit；
- capture alignment；
- mode transition。

D1_ARM_BUILD：

- 原测试保持通过，但不要求本轮 timing closure。

---

## 13. 硬件验收 Gate

### Gate H0：身份与安全

- timing-clean LOCK_MVP bitstream 已加载；
- MAGIC/VERSION 正确；
- SAFE readback 正确；
- OUT2 接线和安全范围确认。

### Gate H1：扫描与采集

- 真实 OUT2 三角波稳定；
- CH1 PD、CH3 ERROR、CH4 OUT2 对齐；
- 连续 10 次 capture 无全零、无错位、无 saturation；
- rising/falling 峰位差已记录。

### Gate H2：HOLD 与 approach

- HOLD count readback 正确；
- 记录扫描转 HOLD 后的误差漂移；
- approach 能在安全范围内重新找到目标；
- 静态目标保持至少 0.5 秒。

### Gate H3：Kp=0 无扰切换

- 数字 OUT2 跳变满足限定；
- 示波器上无不可接受的模拟跳变；
- MODE、ENABLE、KP、KI、bias、setpoint readback 正确。

### Gate H4：最小 P-only 闭环

Kp=4 后：

- error RMS 相对 HOLD 基线下降；
- error mean 更接近 setpoint；
- 无 saturation；
- control 不撞限；
- 谱峰没有明显离开目标；
- 连续锁定至少 60 秒。

首次达到 H4 即视为项目完成“最基础锁定”。不要在此之前增加 PI、自动重锁或 AI。

### Gate H5：Linien-basic 板端服务

在 H4 通过后：

- LockService 移到 Red Pitaya；
- GUI 通过 RPC 获取参数和 Frame；
- 关闭 GUI 后 FPGA 锁定不受影响；
- GUI 重连后恢复当前状态；
- GUI 中不再包含寄存器地址或 SSH 命令。

---

## 14. 分阶段实施计划

### 阶段 0：冻结与对齐

交付：

- 建立 `lock-mvp` 分支；
- 固定当前 main commit；
- 清理 README 中旧版本号和旧 capture 描述；
- 明确唯一寄存器版本；
- 暂停 ARM、PI、AI 和 GUI 扩展。

### 阶段 1：LOCK_MVP_BUILD

交付：

- ARM 可在构建时关闭；
- timing closure；
- XSim 与 host tests 通过；
- 新 bitstream/version 记录。

### 阶段 2：最小 LockService

交付：

- `models.py`；
- `register_mapper.py`；
- `acquisition_service.py`；
- `lock_service.py`；
- GUI 的 START SCAN、SAFE 先迁移到 LocalClient；
- 现有 backend 继续使用，不删除。

### 阶段 3：HOLD + APPROACH

交付：

- target 与 capture generation 绑定；
- exact-count HOLD；
- 慢速 approach；
- 超时和越界 SAFE；
- 硬件 Gate H1/H2。

### 阶段 4：P_LOCK

交付：

- Kp=0 无扰切换；
- Kp=4 符号验证；
- Kp 阶梯；
- 真实 60 秒 P-only 锁定；
- 硬件 Gate H3/H4。

### 阶段 5：板端 server

交付：

- board-local mmap transport；
- 常驻 LockService；
- RPC client；
- 重连状态恢复；
- Gate H5。

---

## 15. 明确不做的内容

在 H4 之前禁止：

- PI/Ki；
- 自动重锁；
- robust autolock；
- spectrum correlation；
- IQ demodulation重构；
- 双执行器快慢环；
- PSD；
- CMA-ES/深度学习；
- 大规模 GUI 重做；
- 多 Agent 无限审查；
- 将仿真结果描述为真实锁定。

---

## 16. 项目完成定义

“最基础锁定”完成必须同时满足：

1. LOCK_MVP_BUILD timing closed；
2. 真实 capture 可用并与 OUT2 对齐；
3. 目标选择绑定有效 capture；
4. HOLD 后通过 approach 消除扫描转静态偏差；
5. Kp=0 切换无不可接受跳变；
6. Kp=4 明确形成负反馈；
7. error RMS 下降且不饱和；
8. 谱峰无明显偏移；
9. 连续锁定至少 60 秒；
10. 任意异常能够返回 SAFE；
11. 所有结果有 bitstream、参数、示波器截图和实验日志。

完成上述条件后，项目才进入下一阶段：PI、自动重锁、Linien robust acquisition 和 AI 参数优化。

---

## 17. 参考依据

### 用户项目

- `version/STATUS.md`
- `software/redpitaya_lock_host/README.md`
- `software/redpitaya_lock_host/redpitaya_lock_host/main_window.py`
- `software/redpitaya_lock_host/redpitaya_lock_host/custom_fpga_backend.py`
- `software/redpitaya_lock_host/scripts/custom_fpga_scan_control.py`
- `v0.94/rtl/red_pitaya_top.sv`
- `v0.94/rtl/custom_register_bank.sv`
- `v0.94/rtl/ramp_generator.sv`

### Linien

- `linien-org/linien` 官方仓库及 Development Wiki
- Linien 官方论文：*Linien: A versatile, user-friendly, open-source FPGA-based tool for frequency stabilization and spectroscopy parameter optimization*
- Red Pitaya 官方 Linien 应用说明
