# v3REG-0 上位机实时控制 OUT2 三角波计划

## 目标

本阶段实现最小 Custom FPGA 参数控制链路：

```text
上位机
-> Red Pitaya Linux
-> /dev/mem 写 PS M_AXI_GP0 映射寄存器
-> FPGA sys_bus_if / custom_register_bank
-> ramp_generator
-> OUT2 输出可实时调节的三角波
```

第一版只用于示波器验证 OUT2，不接 Scan/PZT，不接激光器，不接 D2-125 Servo Output，不和 D2-125 Aux Output 并联。

## 为什么硬编码 RTL 不满足需求

硬编码 `OUT2_TEST_MODE` 或编译时参数只能在 Vivado 综合前固定 offset、amplitude、frequency。用户希望上位机实时扫频和调幅时，每次改参数都重新综合、实现、生成 bitstream、烧录 Red Pitaya 是不可接受的。

真正的 Custom FPGA 控制方式必须让参数在 bitstream 已加载后可写。也就是上位机写寄存器，FPGA 逻辑在运行时读取寄存器并更新 OUT2。

## 为什么需要 register_bank

当前 Custom FPGA Mode 下，OUT1/OUT2 由自定义 RTL 驱动，不再由 official SCPI ASG 控制。没有 `register_bank` 时，上位机只能观察，不能写 FPGA 内部参数。

`register_bank` 的作用是把 PS->PL 的软件写入变成 FPGA 内部稳定寄存器，让上位机可以在不重新生成 bitstream 的情况下切换 SAFE/SCAN，修改三角波 offset、幅度和频率。

## 上位机和 FPGA 分工

上位机负责：

- 通过 SSH 在 Red Pitaya Linux 端运行 `/dev/mem` 小脚本；
- 写 SAFE/SCAN 模式和三角波参数；
- 把 volt / Hz 转换成 FPGA counts / divider；
- 读取 `MAGIC`、`VERSION`、`STATUS`、`OUT2_MONITOR`；
- 记录用户设置和示波器观察结果。

FPGA 负责：

- 通过 GP0 AXI slave -> `sys_bus_if` 接收寄存器读写；
- 保存运行时参数；
- 生成三角波；
- 在 reset、disable、SAFE 时输出 0；
- 对 OUT2 做不超过 `+/-1 V` 的限幅；
- 报告 enable/saturation/out2 monitor 状态。

上位机不做高速实时 PID，不参与 125 MHz 控制环。

## 第一版功能边界

第一版只做：

```text
SAFE: OUT2 = 0
SCAN: OUT2 = scan_offset + triangle
```

第一版不做：

```text
HOLD
P_LOCK
PI_LOCK
AI
自动锁定
debug_buffer
```

## 第一版实验边界

允许：

```text
OUT2 -> 示波器
```

禁止：

```text
OUT2 -> Scan/PZT
OUT2 -> 激光器
OUT2 -> D2-125 Servo Output
OUT2 -> D2-125 Aux Output
OUT2 和 D2-125 Aux Output 并联
OUT2 和任何真实执行器并联
```

原因是 v3REG-0 只验证“上位机实时写参数 -> FPGA 输出变化”这条控制链路，不验证 PZT 响应、不验证锁定、不替代 D2-125。

## Official SCPI Mode 与 Custom FPGA Mode 区别

Official SCPI Mode：

- 通过 `redpitaya_scpi` 控制官方 ASG；
- 可用 SCPI 设置 OUT1/OUT2 波形；
- 启动 SCPI 服务可能加载官方 overlay；
- 可能覆盖当前 custom FPGA bitstream；
- 适合官方功能 bring-up，不是最终 Custom FPGA 锁定控制方式。

Custom FPGA Mode：

- OUT1/OUT2 由自定义 RTL 驱动；
- Official SCPI ASG 不再控制 OUT2；
- 参数必须通过 FPGA `register_bank` 或后续 debug/control 接口写入；
- 本阶段通过 `sys[6]` custom register bank 写 SAFE/SCAN 参数。

## 默认参数

采用 `1 V ~= 8191 counts`：

```text
offset = 0.85 V ~= 6962 counts
amp    = 0.05 V ~= 410 counts
freq   ~= 50 Hz
step   = 1 count/update
update_div ~= 1524 at 125 MHz
limit  = 8191 counts
```

## Linux 写寄存器路径

当前最小路径：

```text
PS M_AXI_GP0
-> axi4_slave
-> ps_sys
-> sys_bus_interconnect(SN=8, SW=20)
-> sys[6]
-> custom_register_bank
```

Red Pitaya Linux 端预计通过 `/dev/mem` mmap 写 GP0 地址空间。按现有 `sys_bus_interconnect` 的 1 MiB 区域划分，`sys[6]` 对应 GP0 base + `0x0060_0000`。当前脚本默认物理地址：

```text
0x40600000
```

该地址必须在用户手动生成 bitstream、烧录并上板后用 `REG_MAGIC = 0x4D545330` 实测确认。

## 后续阶段

v3REG-0 通过后，后续才讨论：

```text
HOLD
P_LOCK
PI_LOCK
debug_buffer
Custom FPGA GUI panel
PZT 开环响应
低增益闭环
AI / 自动重锁
```
