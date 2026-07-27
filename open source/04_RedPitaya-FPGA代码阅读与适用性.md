# RedPitaya-FPGA 代码阅读与适用性

## 1. 项目定位与版本

- `[CONFIRMED]` Red Pitaya 官方 FPGA/SoC 工程集合，包含 v0.94、classic、
  logic、stream、barebones 等 project。
- `[NOT VERIFIED]` commit/release：本地无 `.git`，不能从目录名
  `master` 推断 commit。
- `[CONFIRMED]` license：BSD 3-Clause。
  证据：`RedPitaya-FPGA-master/LICENSE:1-36`。
- `[CONFIRMED]` Makefile 支持 Vivado batch build、simulation、FSBL、
  DTS 与 bit-to-bin：`Makefile:5-69`。

关键目录：

```text
RedPitaya-FPGA-master/
├─ prj/v0.94/rtl/red_pitaya_top.sv
├─ prj/v0.94/sdc/red_pitaya.xdc
├─ rtl/classic/
│  ├─ red_pitaya_scope.v / rp_acq_bram.v
│  ├─ rp_adc_trig.v / rp_decim.v
│  ├─ red_pitaya_asg*.v
│  ├─ red_pitaya_pid*.v
│  └─ housekeeping / AXI modules
├─ rtl/{acq,asg,pid,...}.sv
└─ sdc/
```

## 2. FPGA-MTS 对官方外壳的复用审计

本地只读 `git diff --no-index`：

```text
official prj/v0.94/rtl/red_pitaya_top.sv
vs FPGA-MTS v0.94/rtl/red_pitaya_top.sv
= 243 insertions, 14 deletions
```

差异集中在：

- 新增 `LOCK_ACQ_IMPL` parameter；
- bus 6 接 `custom_register_bank`；
- 新增 laser lock core、capture、ramp、acquisition、OUT2 controller；
- DAC A/B data source 改为 custom signals；
- 关闭 housekeeping LED 的一条连接。

官方 ADC IO、PLL、PS、AXI/DDR、DAC saturation、signed-to-offset-binary 与
ODDR 外壳大体保留。当前源文件也明确说明这一边界：
`../v0.94/rtl/red_pitaya_top.sv:622-639`。

`[CONFIRMED]` 当前 `v0.94/sdc/red_pitaya.xdc` 与本地官方
`prj/v0.94/sdc/red_pitaya.xdc` 逐字相同（no-index diff 为空）。

结论：当前 FPGA-MTS 正确地以官方 v0.94 top 作为外壳基线，没有重写底层
ADC/DAC/PS；但“XDC 与官方相同”不等于完整 timing 已约束，因为新增内部
逻辑与现有 top-level I/O 的 timing semantics 仍要逐项审查。

## 3. official acquisition / trigger / decimation

### 3.1 trigger

`rtl/classic/rp_adc_trig.v:21-66`：

- signed threshold；
- threshold ± hysteresis；
- positive/negative Schmitt state；
- one-cycle edge pulses。

它解决通用 ADC edge trigger，不包含 scan direction、OUT2 guard、
generation、H/N consecutive samples 或 atomic mode switch。FPGA-MTS 的
`realtime_error_crossing_detector` 是更高层的锁定专用触发器，不应被
官方 trigger 直接替换。

### 3.2 decimation

`rtl/classic/rp_decim.v:21-166`：

- 支持 no-average 或 average；
- 1/2/4/8 shift average；
- ≥16 用 pipelined divide；
- 显式处理 signed sum。

FPGA-MTS `custom_debug_capture` 目前只“每 N 拍取一个 raw sample”，没有
average/filter：`../v0.94/rtl/custom_debug_capture.sv:63-93`。

`[INFERENCE]` official average decimator 可降低 alias/noise，但直接替换会
改变 target slope/noise、capture latency 和资源/timing；当前 P-only Gate
不应做这种重构。先以现有 aligned capture 完成真实硬件验证。

### 3.3 scope RAM

官方 classic scope 提供 trigger-relative BRAM、write pointer、pre/post
trigger 与 decimation；FPGA-MTS 自定义 capture 提供更简单的四通道同 index
aligned frame。对“PD/ERROR/OUT2 同帧选点”，当前四通道实现比官方双通道
scope 更直接；对通用 trigger/prehistory，官方实现更成熟。

## 4. official PID

`rtl/classic/red_pitaya_pid_block.v:49-218` 实现：

```text
error = setpoint - input
P = error*Kp >> PSR
I accumulator with numeric saturation and explicit reset
D = difference of scaled error
P+I+D -> 14-bit output saturation
```

关键限制：

- integrator 有 reset 与自身 32-bit numeric saturation：
  `red_pitaya_pid_block.v:118-145`；
- 但没有根据最终 output saturation 做 conditional integration/back
  calculation，因此不能把它称为完整 anti-windup；
- 没有 scan-to-lock bias capture、slew limit、supervisor 或 feature select。

FPGA-MTS 当前只用 P-only，自有 `product >>> 8`、correction limit、
absolute limit、servo divider、slew limit。为当前 Gate 替换成官方 PID
没有收益。

## 5. signed14 / DAC / CSR / clock domain

- `[CONFIRMED]` official PID 和 trigger 大量使用 `$signed`，说明 signed14
  需要在算术边界显式转换。
- `[CONFIRMED]` FPGA-MTS custom controller 对 error、Kp、bias 做显式
  sign extension：`custom_register_bank.sv:1926-1969`。
- `[CONFIRMED]` top 仍通过官方 DAC saturation 与 conversion：
  `red_pitaya_top.sv:622-639`。
- `[CONFIRMED]` custom data path、register bank、capture、acquisition 与
  OUT2 controller 全在 `adc_clk`，避免当前锁定路径 CDC。
- `[NOT VERIFIED]` 现有 `check_timing` 中 no-clock/unconstrained/no-delay
  项的真实接口语义；这是当前 STATUS 的 blocker，不能用“官方 XDC 相同”
  自动豁免。

## 6. 适用性清单

| 功能 | 源文件 / module | 分类 | 推荐 |
|---|---|---|---|
| v0.94 ADC/DAC/PS shell | `prj/v0.94/rtl/red_pitaya_top.sv` | DIRECTLY REUSABLE | 已复用；继续最小化差异 |
| v0.94 XDC | `prj/v0.94/sdc/red_pitaya.xdc` | DIRECTLY REUSABLE | 已逐字复用；逐项解释 timing warnings，不 blanket false-path |
| Schmitt edge trigger | `rp_adc_trig` | CONCEPTUALLY REUSABLE | 当前 H/N detector 已覆盖并增加 lock-specific context |
| average decimator | `rp_decim` | CONCEPTUALLY REUSABLE | 未来 capture noise/alias 有真实问题时再评估 |
| classic scope | `red_pitaya_scope`, `rp_acq_bram` | CONCEPTUALLY REUSABLE | 不替换当前四通道 capture；可参考 pretrigger/coherent pointer |
| official PID | `red_pitaya_pid_block` | NOT APPLICABLE NOW | 当前 P-only 已有更合适 limits/slew/acquisition |
| integrator saturation | `red_pitaya_pid_block:118-145` | FUTURE ONLY | 不是完整 anti-windup；H4 后 PI Gate 才评估 |
| official build flow | `Makefile`, project Tcl | CONCEPTUALLY REUSABLE | 当前构建已稳定，不能在本 Gate 迁移 |

## 7. 最终结论

官方工程能验证/支撑基础接口、signed arithmetic、scope/trigger/decimation
和构建/XDC基线，但完全不解决谱线 identity、ARM VALIDATE/ACTIVE、atomic
bias、P-only acquisition 策略或外部 D2-125。当前最重要的复用已经发生：
保留官方外壳与 XDC。下一步是完成现有 XDC/timing 语义审计，不是复制更多
官方 modules。

