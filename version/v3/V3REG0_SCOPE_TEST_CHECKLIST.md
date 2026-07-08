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

## 2026-07-05 板端验证记录

结果：通过。v3REG-0 上位机/寄存器控制 OUT2 安全三角波输出硬件链路已验证通过。

板端观察结果：

```text
Red Pitaya loaded: /root/red_pitaya_top.bit.bin

/opt/redpitaya/bin/monitor 0x40600000 -> 0x4D545330
/opt/redpitaya/bin/monitor 0x40600004 -> 0x00030000
```

monitor 读回确认：

- `custom_register_bank` 的 MAGIC 出现在 base address `0x40600000`。
- VERSION 为 `0x00030000`。
- PS -> PL `sys_bus` 寄存器访问在板端有效。

以下 monitor 写入寄存器状态后，物理 OUT2 输出约 10 Hz 安全三角波：

```text
MODE            = 1
ENABLE          = 1
SCAN_OFFSET     = 0
SCAN_AMP        = 0x19A
SCAN_STEP       = 0x1
SCAN_UPDATE_DIV = 0x1DC6
OUT2_LIMIT      = 0x1FFF
```

SAFE / 关闭操作通过以下命令验证：

```text
/opt/redpitaya/bin/monitor 0x4060000C 0x0
/opt/redpitaya/bin/monitor 0x40600008 0x0
```

执行 SAFE 后，示波器上的 OUT2 三角波消失，OUT2 回到无三角波状态。

已验证结论：

- PS -> PL `sys_bus` 自定义寄存器访问有效。
- `0x40600000` 是当前加载 bitstream 的正确 base address。
- `custom_register_bank` 已经在真实板端 bitstream 中工作。
- `ramp_generator` 输出有效。
- `MODE` 和 `ENABLE` 对 OUT2 具有真实控制作用。
- `selected_out2` -> DAC B / physical OUT2 链路已经打通。
- SAFE 关闭链路有效。

通过该项验证后，安全边界仍然不变：OUT2 仅允许接示波器观察；不要将 OUT2 接到 laser PZT、laser current、D2-125 Servo Output 或 Scan input。

下一步 GUI 验证路径：

```text
Custom FPGA Mode
-> Custom FPGA Observe
-> Probe Registers
-> Status
-> SAFE
-> SCAN
```

## 2026-07-05 GUI 控制扫描实验记录

结果：通过。v3REG-0 已经可以由 GUI 控制 OUT2 扫描输出，并首次在当前激光器工作状态下观察到实验波形。

已通过项目：

- MAGIC 读回通过：`MAGIC = 0x4D545330`。
- VERSION 读回通过：`VERSION = 0x00030000`。
- base address 确认通过：`found_base_addr = 0x40600000`。
- GUI SCAN 通过。
- GUI SAFE 通过。
- 已观察到 OUT2 三角波输出。
- GUI offset / amplitude / frequency 控制通过。
- 在当前激光器控制器状态下已观察到实验波形。

当前 GUI Custom FPGA Control 参数：

```text
base address = 0x40600000
offset-v     = 0.7500 V
amp-v        = 0.2000 V
freq-hz      = 50.170 Hz
step-counts  = 1
limit-counts = 8191
```

GUI SCAN 读回：

```text
MAGIC   = 0x4D545330
VERSION = 0x00030000
MODE    = 1
ENABLE  = 1
STATUS  = 0x00000001
OUT2    = 4522 counts / 0.552069 V
```

理论扫描范围：

```text
offset = 0.75 V
amp    = 0.20 V
range  ~= 0.55 V to 0.95 V
Vpp    ~= 0.40 Vpp
freq   ~= 50.17 Hz
```

GUI OUT2 读回值 `0.552069 V` 接近理论下限 `0.55 V`，说明 `OUT2_MONITOR` 与当前扫描参数匹配。

本次观察到波形时的激光器控制器状态：

```text
TEC set/work      = 22.66 C / 22.46 C
Current set/work  = 40.07 mA / 57.42 mA
PZT set/work      = 34.99 V / 42.52 V
```

这些数值属于本次实验条件。后续如果波形发生变化，需要与本次 TEC / current / PZT 状态对照。

本次观察到的波形指标：

```text
板端扫描/输出信号：
  Vpp = 0.4583 V
  min = 0.6236 V
  max = 1.082 V
  RMS = 0.8492 V

CH2 信号：
  Vpp = 0.2701 V
  min = 0.3303 V
  max = 0.6004 V
  RMS = 0.4828 V

CH3 信号：
  Vpp = 1.784 V
  min = -1.16 V
  max = 0.6239 V
  RMS = 0.2433 V

板端输出信号：
  Vpp = 0.08848 V
  min = 0.6243 V
  max = 0.7128 V
  RMS = 0.6696 V
```

阶段结论：

- FPGA 寄存器控制链路已经验证通过：GUI -> SSH -> `/dev/mem` -> `custom_register_bank` -> `ramp_generator` -> `selected_out2` -> DAC B / OUT2。
- GUI 已经可以设置 OUT2 的 offset、amplitude、frequency、enable/safe 和 scan mode。
- 在 `offset=0.75 V`、`amp=0.20 V`、`freq=50.17 Hz` 条件下，系统能够产生可观察的周期性扫描波形和通道响应。
- 项目已经从“板子是否能被上位机控制”的阶段，推进到“上位机控制扫描参数并观察实验波形”的阶段。
- 当前不是闭环锁定，也不是 D2-125 替代；当前完成的是 GUI 可控扫描输出 + 实验波形观察。

安全边界：

- 继续以示波器优先观察。
- 任何连接到激光器 PZT、scan input、current modulation 或 D2-125 输入的操作，都必须记录接线方式、幅度范围、偏置范围和安全限制。
- OUT2 必须保持在 Red Pitaya DAC 安全范围内；提高 offset 或 amplitude 前，必须确认后级输入不会打满。
- 现在不允许进入闭环锁定测试，必须先完成扫描参数矩阵和波形稳定性记录。

下一步参数矩阵：

```text
A: offset=0.50 V, amp=0.20 V, freq=50 Hz
B: offset=0.75 V, amp=0.20 V, freq=50 Hz
C: offset=0.75 V, amp=0.10 V, freq=20 Hz
D: offset=0.75 V, amp=0.05 V, freq=10 Hz
```

每组都记录：

- GUI 参数。
- OUT2 读回。
- 示波器 OUT2 Vpp/min/max。
- CH2/CH3 波形稳定性。
- 是否出现削顶、跳变、饱和或波形断裂。

下一阶段目标：在保持安全幅度的前提下，找到最适合扫出稳定谱线的 offset / amplitude / frequency 组合。完成后再进入 FPGA mixer + LPF error signal 观察、error signal 与扫描信号关系检查，以及低风险闭环控制流程设计。

## 9. v3REG-1 / v3REG-2 HOLD 和 P/PI 锁定预验证扩展

本节只记录进入最短锁定路径后的 scope-only 上板顺序。当前目标是验证 Red Pitaya 能基于现有 MTS error signal 生成可控 OUT2，不替代外部 EOM RF、模拟 BPF 或放大器。

允许的 GUI 路径：

```text
Custom FPGA Mode
-> Probe Registers
-> Status
-> SAFE
-> SCAN
-> HOLD
-> P_LOCK, Kp=0 first
-> PI_LOCK, Kp=0 and Ki=0 first
```

允许的 CLI 路径：

```powershell
python .\scripts\custom_fpga_scan_control.py --host rp-f0cb13.local status
python .\scripts\custom_fpga_scan_control.py --host rp-f0cb13.local safe
python .\scripts\custom_fpga_scan_control.py --host rp-f0cb13.local hold --hold-v 0.0
python .\scripts\custom_fpga_scan_control.py --host rp-f0cb13.local p-lock --kp 0 --polarity normal --lock-bias-v 0.0 --lock-limit-counts 8191
python .\scripts\custom_fpga_scan_control.py --host rp-f0cb13.local pi-lock --kp 0 --ki 0 --polarity normal --lock-bias-v 0.0 --lock-limit-counts 8191
```

必须记录：

- `MAGIC = 0x4D545330` 和 `VERSION = 0x00030000`。
- `HOLD` 输出固定电压是否正确。
- `P_LOCK` 在 `Kp=0` 时是否保持 bias，不产生意外输出。
- 逐步增加 `Kp` 后，正/负 error 下 OUT2 方向是否符合 polarity。
- polarity 翻转后 OUT2 方向是否反转。
- `LOCK_LIMIT` 是否生效。
- `SAFE` 或 `ENABLE=0` 是否立即让 OUT2 回到 0。
- `ERROR_MONITOR` 和 `CONTROL_MONITOR` 读回是否与示波器趋势一致。

安全边界：

- HOLD/P_LOCK/PI_LOCK 第一轮只能 `OUT2 -> 示波器`。
- 禁止直接接 PZT、激光电流、D2-125 Servo Output 或 Scan input。
- P_LOCK/PI_LOCK 默认 `Kp=0`、`Ki=0`，必须人工逐步增加。
- 没有完成幅度、偏置、极性、限幅和 SAFE 验证前，不允许进入闭环锁定测试。
