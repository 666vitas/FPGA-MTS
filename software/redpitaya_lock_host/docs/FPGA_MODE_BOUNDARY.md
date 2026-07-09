# FPGA 模式边界

## OUT2 路径边界

当前 custom RTL 将物理 OUT2 路由到 `selected_out2`，不是 `laser_control`。

GUI 中必须区分两条路径：

```text
A. Official SCPI Mode -> redpitaya_scpi -> official ASG -> OUT1/OUT2
   只用于官方 overlay / ASG 测试路径。

B. Custom FPGA Mode -> SSH + /dev/mem -> custom_register_bank
   -> ramp_generator / out2_lock_controller -> selected_out2 -> physical OUT2
   用于 Custom FPGA Observe -> Probe Registers -> Status -> SAFE/SCAN/HOLD/P_LOCK/PI_LOCK。
```

当加载 `USE_LASER_LOCK_CORE=1` 的 custom RTL 时，Official SCPI ASG OUT2 命令可能在协议层成功，但不会驱动物理 OUT2，因为物理 OUT2 已路由到 `selected_out2`。

## 当前 Custom FPGA Routing

`red_pitaya_top.sv` 设置：

```systemverilog
localparam logic USE_LASER_LOCK_CORE = 1'b1;
localparam int   LASER_LOCK_OUTPUT_MODE = 3;
localparam int   LASER_LOCK_CONTROL_PATH_MODE = 1;
```

当前 routing：

- OUT1 / DAC A = `laser_error`
- OUT2 / DAC B = `selected_out2`
- official `asg_dat[0]` 和 `asg_dat[1]` 不再直接驱动物理 OUT1/OUT2

Custom FPGA 信号链：

```text
IN1 + IN2 -> mixer_core -> lpf_core -> output_protect -> OUT1 laser_error
SSH /dev/mem -> custom_register_bank -> ramp_generator / out2_lock_controller -> selected_out2 -> OUT2
```

## v3REG-0 与 v3REG-1 / v3REG-2 状态

v3REG-0 SAFE/SCAN 已由用户上板验证：

```text
base address = 0x40600000
MAGIC = 0x4D545330
VERSION = 0x00030000
GUI / monitor 可控制 OUT2 三角波
SAFE 可关闭 OUT2
```

当前 RTL / software 已包含 v3REG-1 / v3REG-2 候选：

```text
MODE=0 SAFE
MODE=1 SCAN
MODE=2 HOLD
MODE=3 P_LOCK
MODE=4 PI_LOCK
```

HOLD/P_LOCK/PI_LOCK 尚未完成 Vivado timing、bitstream、烧录和上板验证。

## 硬件安全边界

当前 custom FPGA mode 中，OUT2 仍然只允许接示波器。

禁止把 OUT2 接到：

- laser scan/PZT
- Scan input
- laser current modulation
- D2-125 Servo Output
- D2-125 Aux Output
- 任何真实执行器路径

只有完成物理电压范围、polarity、bandwidth、timing、SAFE 行为和 lock/scan switching 审查后，才允许单独讨论真实执行器连接 SOP。

## Official SCPI Mode

Official SCPI Mode 会启动或连接 `redpitaya_scpi`，然后通过 SCPI 控制官方 ASG 输出。该模式适合示波器和 signal-generator bring-up，但可能不会保留 custom FPGA bitstream。

启动 `redpitaya_scpi` 可能执行官方 v0.94 overlay 路径，并可能覆盖当前已经加载的 custom FPGA bitstream。

如果 custom FPGA bitstream 中 `USE_LASER_LOCK_CORE=1`，SCPI OUT2 命令仍可能返回成功，但不会驱动物理 OUT2，因为物理 OUT2 已经路由到 `selected_out2`。

## Custom FPGA Mode

Custom FPGA Mode 表示当前 custom bitstream 已加载，不应该通过启动 official SCPI overlay 服务来打扰它。

在该模式下：

- OUT1 是 FPGA `laser_error`，不是 SCPI ASG OUT1。
- OUT2 是 `selected_out2`，不是 SCPI ASG OUT2。
- V2 host app 通过 SSH `/dev/mem` 访问 `custom_register_bank`。
- `Probe Registers` 和 `Status` 只读。
- SAFE/SCAN/HOLD/P_LOCK/PI_LOCK 写寄存器前必须确认 `MAGIC = 0x4D545330`。
- Custom FPGA Observe Mode 记录手动示波器读数和安全判断。
- Lock Workflow Mode 是 D2-125 替代路径 checklist，不是已经完成的自动锁定控制器。

## 后续集成

如果项目需要同时保留官方 SCPI output control 和 custom FPGA error path，必须重新设计 RTL/top-level 集成。可能方向是保留必要的官方 scope/acquisition plumbing，同时通过明确的 register/debug interface 暴露 custom FPGA control/status。
