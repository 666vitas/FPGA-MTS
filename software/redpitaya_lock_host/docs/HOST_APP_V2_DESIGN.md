# Host App V2 设计说明

## 当前定位

Host App V2 是 Red Pitaya 激光频率锁定项目的上位机。它的职责是：

- 管理 Official SCPI Mode 与 Custom FPGA Mode 的边界。
- 通过 GUI 引导用户做安全的示波器验证。
- 通过 SSH + `/dev/mem` 访问 custom FPGA register bank。
- 记录实验过程、参数和安全判断。

它不是通用 signal generator GUI，也不是已经完成的自动锁定控制器。

## 当前主线状态

v3REG-0 SAFE/SCAN 已由用户上板验证：

```text
base address = 0x40600000
MAGIC = 0x4D545330
VERSION = 0x00030000
GUI / monitor 可控制 OUT2 三角波
GUI / monitor SAFE 可关闭 OUT2
```

当前 RTL / software 已包含 v3REG-1 / v3REG-2 候选：

```text
SAFE -> SCAN -> HOLD -> P_LOCK -> PI_LOCK
```

HOLD/P_LOCK/PI_LOCK 尚未完成 Vivado timing、bitstream、烧录和上板验证。因此这些模式当前只能 scope-only。

## Custom FPGA Control 链路

GUI 到 FPGA 的链路：

```text
main_window.py
-> CustomFpgaRegisterWorker
-> CustomFpgaBackend
-> SSH
-> remote Python /dev/mem helper
-> custom_register_bank
-> out2_lock_controller / ramp_generator
-> selected_out2
```

该路径不启动 `redpitaya_scpi`，也不使用 Official SCPI ASG 控制 Custom FPGA OUT2。

`Probe Registers` 和 `Status` 只读。SAFE/SCAN/HOLD/P_LOCK/PI_LOCK 写寄存器前必须通过 `MAGIC=0x4D545330` 检查。

## GUI 控件

Custom FPGA Control 当前包含：

```text
Probe Registers
Status
SAFE
SCAN
HOLD
P_LOCK
PI_LOCK
base address
offset-v
amp-v
freq-hz
step-counts
limit-counts
hold-v
Kp raw
Ki raw
polarity
lock-bias-v
lock-limit-counts
```

状态显示包含：

```text
MAGIC
VERSION
MODE
ENABLE
STATUS
OUT2_MONITOR
ERROR_MONITOR
CONTROL_MONITOR
错误/警告信息
```

## 寄存器和 MODE

新增/当前关键寄存器：

```text
0x00 MAGIC
0x04 VERSION
0x08 MODE
0x0C ENABLE
0x10 SCAN_OFFSET
0x14 SCAN_AMP
0x18 SCAN_STEP
0x1C SCAN_UPDATE_DIV
0x20 OUT2_LIMIT
0x24 STATUS
0x28 OUT2_MONITOR
0x2C HOLD_VALUE
0x30 KP
0x34 POLARITY
0x38 LOCK_BIAS
0x3C LOCK_LIMIT
0x40 ERROR_MONITOR
0x44 CONTROL_MONITOR
0x48 KI
0x4C INTEGRAL_RESET
```

MODE 定义：

```text
0 SAFE
1 SCAN
2 HOLD
3 P_LOCK
4 PI_LOCK
```

`SAFE` 是最高优先级：`ENABLE=0` 或 `MODE=0` 时 OUT2 必须为 0。

P_LOCK/PI_LOCK 默认 `Kp=0`、`Ki=0`，GUI 只提供人工逐步增加入口，不做自动闭环调参。

## 模块职责

- `connection_probe.py`：解析 hostname，探测 ping、端口 22/80/5000。
- `ssh_client.py`：通过 Paramiko 执行 Red Pitaya service-management 命令。
- `scpi_client.py`：底层 TCP SCPI transport，使用 CRLF 命令结尾。
- `rp_scpi_client.py`：Red Pitaya SCPI 业务封装，用于官方输出和 acquisition。
- `acquisition_worker.py`：后台 `QThread` acquisition loop。
- `waveform_preview.py`：生成 OUT1/OUT2 preview time axis 和 waveform。
- `custom_fpga_workflow.py`：Custom FPGA Observe 页面中的手动示波器读数分析和安全判断。
- `custom_fpga_backend.py`：通过 SSH + `/dev/mem` 执行 Probe Registers、Status、SAFE、SCAN、HOLD、P_LOCK、PI_LOCK。
- `main_window.py`：V2 GUI，包含连接管理、输出控制、acquisition 和四通道显示。
- `data_logger.py`：CSV metadata 和 PNG export。
- `safety.py`：输出安全检查和退出时 best-effort shutdown。

## 两层连接模型

第一层：SSH / 网络管理。

- 解析 host 到 IP。
- Probe ping。
- Probe SSH port 22。
- Probe Web port 80。
- Probe SCPI port 5000。
- 必要时通过 SSH 启动 SCPI server。

第二层：SCPI control。

- 连接选定 host/IP 的 5000 端口。
- 运行 `*IDN?`。
- 配置 OUT1 / OUT2。
- 通过 `ACQ:*` 命令采集 IN1 / IN2。

该两层模型只适用于 Official SCPI Mode。Custom FPGA Mode 中仍可以做网络 probe，但应避免启动 `redpitaya_scpi`，因为它可能加载官方 overlay。

## GUI 模式边界

GUI 分为四个页面：

- Hardware Bring-up：Official SCPI 硬件检查和安全 OUT2 scan。
- Custom FPGA Observe：真实接线的 IN1/IN2/OUT1/OUT2 手动示波器读数，以及 Custom FPGA Control。
- Lock Workflow：D2-125 替代路径 checklist 和未来 lock/relock 计划。
- Data Log：导出 Markdown 实验日志。

Official SCPI Mode：

- 可以启动 `redpitaya_scpi`。
- 可以连接 5000 端口并运行 `*IDN?`。
- 控制官方 ASG OUT1/OUT2。
- 通过官方 SCPI ACQ 采集 IN1/IN2。
- 可能覆盖当前加载的 custom FPGA bitstream。

Custom FPGA Mode：

- 不启动 SCPI overlay。
- 把当前 custom bitstream 视为有效硬件路径。
- 当前 RTL 中 `USE_LASER_LOCK_CORE = 1`。
- OUT1 / DAC A = `laser_error`。
- OUT2 / DAC B = `selected_out2`。
- official `asg_dat[0]` / `asg_dat[1]` 不直接驱动物理 OUT1/OUT2。
- 上位机可通过 SSH `/dev/mem` 读写 SAFE/SCAN/HOLD/P_LOCK/PI_LOCK 候选寄存器。
- debug-buffer read、automatic lock/relock 和 actuator connection SOP 仍是后续工作。

## 输出控制安全规则

Official SCPI Mode 中，每个输出支持：

- enable
- waveform type: sine, square, triangle, sawtooth
- frequency_hz
- amplitude_v
- offset_v
- phase_deg

安全规则：

- `amplitude_v >= 0`
- `abs(offset_v) + amplitude_v <= output_range_v`
- 默认 `output_range_v = 1.0 V`
- 默认 `amplitude_v = 0.05 V`

关闭顺序：

```text
SOUR1:VOLT 0
SOUR2:VOLT 0
OUTPUT1:STATE OFF
OUTPUT2:STATE OFF
GEN:STOP
```

## 安全边界

当前阶段必须遵守：

```text
OUT2 只允许接示波器。
禁止接 PZT。
禁止接 Scan input。
禁止接 laser current modulation。
禁止接 D2-125 Servo Output。
禁止接 D2-125 Aux Output。
不能声称已经闭环锁定。
不能声称已经替代 D2-125。
```

任何真实执行器连接都必须另写 SOP，记录接线方式、幅度范围、偏置范围、停止条件和通过标准。
