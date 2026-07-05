# v3REG-0 OUT2 示波器上板验证 checklist

## 0. 阶段边界

本 checklist 只验证：

```text
上位机
-> Red Pitaya Linux /dev/mem
-> custom_register_bank
-> ramp_generator
-> OUT2 示波器三角波
```

本阶段不验证锁定，不验证 PZT 响应，不接真实执行器，不开发 GUI，不做 HOLD / P_LOCK / PI_LOCK / AI。

## 1. Vivado 前检查

打开 `v0.94/project/redpitaya.xpr` 后先确认：

- `red_pitaya_top` 是 Design Top。
- `custom_register_bank.sv` 在 Design Sources。
- `ramp_generator.sv` 在 Design Sources。
- `tb_*.sv` 不在 Design Sources，只能作为 Simulation Sources 或 disabled source。
- `red_pitaya_top.sv` 中 `custom_register_bank` 挂在 `sys[6]`。
- `sys[6]` 没有被 `sys_bus_stub` stub 掉。
- `sys[7]` 可以继续 stub。

## 2. Vivado 通过标准

只有同时满足以下条件，才允许继续生成 bitstream：

```text
WNS >= 0
TNS = 0
Failing Endpoints = 0
```

如果 timing 不通过，停止，不生成可上板 bitstream。

## 3. 烧录后第一步

烧录后不要先开 SCAN，先只读 status：

```powershell
python .\scripts\custom_fpga_scan_control.py --host rp-f0cb13.local status
```

必须读到：

```text
MAGIC = 0x4D545330
```

如果 MAGIC 读不到，停止。不要继续写 scan 参数，不要判断 OUT2 波形。

脚本安全要求：

- `status` 只允许读寄存器，不写寄存器。
- `safe` 和 `scan` 在写任何寄存器前，必须先读取 `MAGIC`。
- 只有 `MAGIC = 0x4D545330` 时，`safe` / `scan` 才允许继续写寄存器。
- 如果 MAGIC 不匹配，脚本必须非零退出，且不得写 `MODE`、`ENABLE`、`SCAN_OFFSET`、`SCAN_AMP`、`SCAN_STEP`、`SCAN_UPDATE_DIV`、`OUT2_LIMIT`。
- MAGIC 不匹配通常说明旧 bitstream、base address 错误，或 `sys[6]` 没有连接 `custom_register_bank`。

## 4. 示波器接线

只允许：

```text
OUT2 -> 示波器 CH4
```

禁止：

```text
OUT2 -> Scan/PZT
OUT2 -> 激光器
OUT2 -> D2-125 Servo Output
OUT2 -> D2-125 Aux Output
OUT2 与任何真实执行器并联
```

本阶段 OUT2 只接示波器。只要有人准备接 Scan/PZT，立即停止。

## 5. 验证命令

在 `software/redpitaya_lock_host` 目录执行。

先确认寄存器存在：

```powershell
python .\scripts\custom_fpga_scan_control.py --host rp-f0cb13.local status
```

进入 SAFE：

```powershell
python .\scripts\custom_fpga_scan_control.py --host rp-f0cb13.local safe
```

默认 SCAN：

```powershell
python .\scripts\custom_fpga_scan_control.py --host rp-f0cb13.local scan --offset-v 0.85 --amp-v 0.05 --freq-hz 50
```

改 offset 到 0.82 V：

```powershell
python .\scripts\custom_fpga_scan_control.py --host rp-f0cb13.local scan --offset-v 0.82 --amp-v 0.05 --freq-hz 50
```

改 offset 到 0.88 V：

```powershell
python .\scripts\custom_fpga_scan_control.py --host rp-f0cb13.local scan --offset-v 0.88 --amp-v 0.05 --freq-hz 50
```

改 amp 到 0.02 V：

```powershell
python .\scripts\custom_fpga_scan_control.py --host rp-f0cb13.local scan --offset-v 0.85 --amp-v 0.02 --freq-hz 50
```

最后回 SAFE：

```powershell
python .\scripts\custom_fpga_scan_control.py --host rp-f0cb13.local safe
```

## 6. 正常现象

- `safe` 后 OUT2 约等于 0 V。
- 默认 `scan` 后 OUT2 约在 0.80 V 到 0.90 V 之间往返。
- 改 `offset-v` 后，中心电压变化。
- 改 `amp-v` 后，三角波幅度变化。
- 改 `freq-hz` 后，三角波频率变化。
- `status` 能读到 magic/version/status/out2_monitor。

## 7. 停止条件

出现以下任一情况，立即停止：

- MAGIC 读不到。
- OUT2 接近 `+/-1 V`。
- OUT2 不受 `safe` 控制。
- OUT2 随机跳变。
- OUT1 原有 error observation 异常消失。
- 有人准备接 Scan/PZT。
- 有人准备接激光器、D2-125 Servo Output 或 D2-125 Aux Output。

停止后回到代码和接线审查，不继续上板验证。

## 8. 需要保存的证据

- Vivado timing 截图或 summary。
- `status` 命令输出。
- `safe` 后 OUT2 示波器截图。
- 默认 `0.85 V / 0.05 V / 50 Hz` 波形截图。
- 改 offset 后的截图。
- 改 amp 后的截图。
- 最后回到 `safe` 的截图。
