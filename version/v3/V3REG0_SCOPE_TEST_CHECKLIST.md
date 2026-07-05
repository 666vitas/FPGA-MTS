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

Timing clean 后必须先：

```text
Generate Bitstream
-> 将 timing-clean bitstream 加载/烧录到 Red Pitaya FPGA
-> 烧录完成后再运行上位机脚本
```

`Generate Bitstream` 只是生成 bit 文件；`Program Device` / 加载 bitstream 才是把 FPGA 程序放进 Red Pitaya。`custom_fpga_scan_control.py` 只读写已经加载进 FPGA 的 `custom_register_bank`，不能替代 bitstream 烧录。`Program Device` 后如果板子重启，需要重新加载当前 timing-pass 的 bitstream。Red Pitaya 网页界面不是本阶段必需条件；VPN 可能影响网页、`.local` 或 SSH。实验时建议关闭 VPN，或直接使用板子的实际 IP。

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

如果 `status` 读到 `magic = 0x00000000` / `version = 0x00000000`，说明 SSH 和 `/dev/mem` 读取已经执行，但没有读到 `custom_register_bank`。这不能 safe/scan；先运行：

```powershell
python .\scripts\custom_fpga_scan_control.py --host rp-f0cb13.local probe
```

如果 `probe` 全部为 0，重新 Program Device / 重新加载当前 timing-pass 的 `red_pitaya_top.bit`。不要把“没打开 Red Pitaya 网页 App”误判为已经排除了 bitstream 加载问题。

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

GUI path for the same v3REG-0 register check:

```text
software/redpitaya_lock_host/run.bat
-> Custom FPGA Mode / Custom FPGA Observe
-> Probe Registers
-> Status
-> SAFE
-> SCAN
```

GUI `Probe Registers` and `Status` are read-only. GUI `SAFE` and `SCAN` use SSH + `/dev/mem` and must read `MAGIC = 0x4D545330` before any register write. If GUI shows `MAGIC = 0x00000000`, stop: no `custom_register_bank` was read. Re-run Probe Registers, check Program Device / timing-pass bitstream reload, and check the base address before trying SAFE or SCAN again.

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

## 2026-07-05 Board Verification Record

Result: PASS for v3REG-0 host/register controlled OUT2 safe triangle hardware path.

Observed on board:

```text
Red Pitaya loaded: /root/red_pitaya_top.bit.bin

/opt/redpitaya/bin/monitor 0x40600000 -> 0x4D545330
/opt/redpitaya/bin/monitor 0x40600004 -> 0x00030000
```

The monitor reads confirm:

- `custom_register_bank` MAGIC is present at base address `0x40600000`.
- VERSION is `0x00030000`.
- PS -> PL `sys_bus` register access works on the board.

The following monitor-written register state produced an approximately 10 Hz safe triangle on physical OUT2:

```text
MODE            = 1
ENABLE          = 1
SCAN_OFFSET     = 0
SCAN_AMP        = 0x19A
SCAN_STEP       = 0x1
SCAN_UPDATE_DIV = 0x1DC6
OUT2_LIMIT      = 0x1FFF
```

SAFE / shutdown was verified with:

```text
/opt/redpitaya/bin/monitor 0x4060000C 0x0
/opt/redpitaya/bin/monitor 0x40600008 0x0
```

After SAFE, the oscilloscope OUT2 triangle disappeared and OUT2 returned to the no-triangle state.

Verified conclusions:

- PS -> PL `sys_bus` custom register access works.
- `0x40600000` is the correct base address for this loaded bitstream.
- `custom_register_bank` is active in the real board bitstream.
- `ramp_generator` output is effective.
- `MODE` and `ENABLE` have real control over OUT2.
- `selected_out2` -> DAC B / physical OUT2 is connected.
- SAFE shutdown is effective.

Safety boundary after this PASS remains unchanged: OUT2 is oscilloscope-only. Do not connect OUT2 to laser PZT, laser current, D2-125 Servo Output, or Scan input.

Next GUI validation path:

```text
Custom FPGA Mode
-> Custom FPGA Observe
-> Probe Registers
-> Status
-> SAFE
-> SCAN
```
