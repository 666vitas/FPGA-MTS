# PyRPL / `pyprl` 本地包阅读与适用性

## 1. 本地目录身份判定

本地目录只有一个文件：

```text
pyprl/
└─ pyrpl-windows-2025-12-3.00-bc739ea5.exe
```

结论：

- `[CONFIRMED]` 文件不是源码仓库，没有 README、LICENSE、build instructions
  或 `.git`。
- `[CONFIRMED]` 它是 PE64、PyInstaller archive，cookie magic 为
  `MEI 0C 0B 0A 0B 0E`，嵌入 `python39.dll` 与 `PYZ.pyz`。
- `[CONFIRMED]` SHA-256：
  `7B77A76046DCD2C11970CAE4519CE56BD8E9C70AEB553CBB45B4C04B3C89FFB7`。
- `[CONFIRMED]` Windows Authenticode 状态：`NotSigned`。
- `[CONFIRMED]` PyInstaller TOC 含 3,084 项；PYZ 含 2,494 Python modules，
  其中 73 个 `pyrpl` modules。
- `[INFERENCE]` 文件名的 `3.00-bc739ea5` 是 build/version label，可能含
  commit-like token；因无 Git metadata 且 token 未嵌入可搜索字符串，不能
  把它写成已验证 commit。
- `[NOT VERIFIED]` license：本地包没有可归属于 PyRPL 根项目的 LICENSE。
  本审计不以外部记忆代替本地证据。

因此，“pyprl”只是拼写错误的本地目录名；嵌入包名与模块路径明确证明
内容是 PyRPL，但本轮只能做 binary inventory 与 bytecode metadata 审计，
不能给源码行号。

## 2. 可确认模块拓扑

PyInstaller PYZ 清单确认：

```text
pyrpl/
├─ pyrpl.py / redpitaya.py / redpitaya_client.py
├─ hardware_modules/
│  ├─ pid.py
│  ├─ iq.py
│  ├─ scope.py
│  ├─ asg.py / trig.py / sampler.py
│  └─ iir/
├─ software_modules/
│  ├─ lockbox/
│  │  ├─ lockbox.py
│  │  ├─ input.py
│  │  ├─ output.py
│  │  ├─ stage.py
│  │  ├─ gainoptimizer.py
│  │  └─ models/{linear,interferometer,fabryperot,pll,...}.py
│  ├─ software_pid.py
│  ├─ spectrum_analyzer.py
│  └─ network_analyzer.py
└─ widgets/module_widgets/
   ├─ lockbox_widget.py
   ├─ pid_widget.py
   ├─ iq_widget.py
   └─ scope_widget.py
```

还确认包含 `pyrpl/fpga/red_pitaya.bin` 与 monitor server binaries，说明它
依赖自己的完整 FPGA image 与寄存器架构，而不是可直接嵌入
FPGA-MTS 的纯 Python 控制算法。

## 3. lockbox 行为（bytecode metadata）

下面结论来自解压后的 Python 3.9 bytecode 中保留的类名、方法名和 docstring；
属于 `[CONFIRMED: embedded bytecode metadata]`，但没有源码行号。

### 3.1 数据模型

`pyrpl.software_modules.lockbox.output.OutputSignal` 的 docstring 定义：

- 每个 output 有 `dc_gain`、unit；
- sweep amplitude/offset/frequency/waveform；
- physical `output_channel`；
- loop `p/i`；
- additional filter / extra module；
- min/max voltage；
- measured/model transfer function；
- desired unity gain frequency。

`OutputSignal._setup_pid_lock()` 依据 input gain、PID gain 与 output dc_gain
组合外环增益。`OutputSignal.is_saturated()` 用于 lock status。

这是一种比 FPGA-MTS 当前 `LockTarget + BasicLockRequest` 更完整的
model-based actuator 描述。

### 3.2 acquisition sequence

确认的 symbols：

- `Lockbox.lock_async()`：“stage by stage”执行完整 sequence；
- `Stage.execute_async()` / `Stage._setup()`；
- stage attributes：`input`、`setpoint`、`duration`、`gain_factor`、
  `function_call`、per-output settings；
- `Lockbox.is_locked()` 会检查 state 与每个 output 是否 saturated；
- `Lockbox._monitor_lock_status_async()`；
- `Lockbox.unlock()`、`sweep()`、`sleep_while_locked()`。

因此 PyRPL lockbox 是“物理模型 + 多 stage + 多 output”的通用锁定框架，
不是专门的“点击一条 MTS 谱线，自动寻找 ERROR crossing，再原子切 P-only”
工作流。

### 3.3 PID / IQ / scope

- `hardware_modules.pid`：3 个 PID modules；P/I、input filter、integrator
  value `ival`；docstring 明确 14-bit output 在约 ±1 V 饱和，而内部 32-bit
  integral 可远超输出范围。这是 windup 风险提示，不是自动 anti-windup
  证明。
- `hardware_modules.iq`：FPGA demodulation/lock-in/PDH、network analysis，
  依赖 PyRPL signal routing 与 FPGA modules。
- `hardware_modules.scope`：双通道 `2^14` samples、decimation/average、
  threshold+hysteresis edge trigger、current/trigger timestamp。

## 4. 对重点问题的回答

1. **是否有“选谱线后自动锁定”的完整流程？**
   `[CONFIRMED/INFERENCE]` 有通用 lockbox sequence、model、sweep、stage、
   saturation monitoring；本地 binary metadata 没有证明一个 Linien 式
   feature correlation/line identity 流程。不能把 lockbox 等同于 MTS
   自动选谱线。

2. **如何描述 input、actuator、setpoint？**
   `[CONFIRMED]` `Lockbox` 有 logical inputs/outputs；`Stage` 绑定 input、
   setpoint、duration/gain factor；`OutputSignal` 描述 dc gain、channel、
   voltage limits、P/I 与 transfer function。

3. **是否支持快慢执行器？**
   `[CONFIRMED]` `OutputSignal` 可添加多个 output，sequence 对各 output
   分别配置；`PiezoOutput` symbol 存在。它在数据模型层支持多执行器。

4. **是否适合不可软件控制的 D2-125？**
   `[INFERENCE]` 不适合直接纳入闭环 ownership。PyRPL 的 output model
   假定能配置 PID/channel、读取 saturation、执行 unlock/sweep；外部
   D2-125 不满足这些接口。

5. **适合上位机的数据模型？**
   `OutputSignal` 的 dc gain/unit/limits/transfer-function 与 `Stage`
   的 explicit setpoint/gain factor 值得概念借鉴；完整 dynamic module tree、
   model inheritance、gain optimizer 对当前最小 P-only 过重。

6. **PID/IQ 能否局部移植？**
   `[CONFIRMED]` installer 同时携带 PyRPL FPGA bitstream、hardware module
   mapping 与 GUI。`[INFERENCE]` PID/IQ Python API 强依赖其 gateware CSR
   和 signal routing，不能把 Python module 单独复制到 SystemVerilog
   FPGA-MTS。

## 5. 适用性清单

| 功能 | embedded module / symbol | 分类 | 风险与推荐 | 阶段 |
|---|---|---|---|---|
| Input/Output/Stage 数据模型 | `lockbox/{input,output,stage}.py` | CONCEPTUALLY REUSABLE | 可用于未来 actuator metadata 与人工 D2 state fields；不要引入 dynamic framework | P2 |
| output voltage limits + saturation status | `OutputSignal.is_saturated` | CONCEPTUALLY REUSABLE | 当前 FPGA 已有限幅/saturation；可借鉴 host 统一呈现 | P1/P2 |
| multi-stage sequence | `Lockbox.lock_async`, `Stage.execute_async` | CONCEPTUALLY REUSABLE | 当前 L1 已有更小状态机；只借鉴显式 stage/readback | FUTURE ONLY |
| multi-output / PiezoOutput | `OutputSignal`, `PiezoOutput` | DANGEROUS UNDER CURRENT HYBRID LOOP | 外部 D2 不可控/不可读，不能假装统一 ownership | 禁止当前 |
| PID `ival` / integrator | `hardware_modules.pid` | NOT APPLICABLE NOW | 当前 P-only 禁止 Ki；docstring 反而显示 windup 风险 | H4 后评估 |
| IQ / demodulation | `hardware_modules.iq` | REQUIRES ARCHITECTURE CHANGE | FPGA-MTS 已有 mixer/LPF；局部移植会重构 gateware | 不引入 |
| scope trigger/timestamp | `hardware_modules.scope` | CONCEPTUALLY REUSABLE | 当前已有 4-channel aligned capture 与 L1 event timestamp；无需复制 | 已覆盖 |
| full PyRPL binary | installer | NOT APPLICABLE NOW | 未签名、非源码、license/commit 不可验证；不可作为产品依赖 | 不引入 |

## 6. 最终结论

本地 `pyprl` 是 PyRPL Windows binary distribution，不是可审计源码。
它最有价值的是 lockbox 的 input/output/stage 数据模型与“每个 actuator
明确 dc gain、limits、transfer function、saturation”的思想。当前不运行、
不安装、不反编译为产品代码，也不移植 PID/IQ；若未来需要逐行学习，应由
用户另行提供带 README/LICENSE/Git metadata 的 PyRPL source snapshot。
