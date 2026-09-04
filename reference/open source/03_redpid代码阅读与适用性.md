# redpid 代码阅读与适用性

## 1. 项目定位

- `[CONFIRMED]` 定位：Red Pitaya 上的 “Digital Servo”，Migen/MiSoC
  gateware，只有基础 CSR-over-SSH CLI。
  证据：`redpid-master/README.rst:1-14`。
- `[NOT VERIFIED]` 版本/commit：本地无 `.git`，README 无 release version。
- `[CONFIRMED]` license：GPL-3.0-or-later。
  证据：`redpid-master/COPYING` 与 `gateware/chains.py:1-16`。

目录：

```text
redpid-master/
├─ gateware/
│  ├─ chains.py       fast/slow signal chains and crossbar
│  ├─ iir.py/filter.py/limit.py
│  ├─ sweep.py/relock.py/modulate.py
│  └─ analog.py/pitaya_ps.py/redpid.py
├─ verilog/           official Red Pitaya ASG/scope/AXI snippets
└─ test/              CSR CLI and filter transfer tests
```

它没有完整 GUI、server daemon、MTS line selection 或 autolock workflow。

## 2. 实际信号链

README 的完整 fast chain：

```text
ADC -> IIR -> demod -> IIR -> selectable x
    -> offset/limit -> IIR... -> selectable y
    -> offset + relock + sweep + modulation -> final limit -> DAC
```

证据：`README.rst:20-36`；实现：
`gateware/chains.py:28-155`。

`FastChain` 暴露：

- `x_hold/x_clear/y_hold/y_clear/y_relock` state inputs；
- saturation/railed/unlocked state outputs；
- signal crossbar；
- sweep/modulation/relock 与 filtered signal 的加法；
- final `LimitCSR` 后进入 DAC。

`SlowChain` 是低速 IIR + limits：
`gateware/chains.py:158-206`。它不是明确的“fast PID + slow PID”产品状态机。

## 3. PID / anti-windup / scan-to-PID

- `[CONFIRMED]` 本地 redpid 源码没有命名为 PID 的 Migen module；
  核心 servo 由 IIR filters 构成。
- `[CONFIRMED]` `LimitCSR` 暴露 saturation/railed，但没有看到
  “output saturation 时冻结 integrator”的专门 anti-windup state machine。
- `[CONFIRMED]` `Relock` 在 input 失锁/railed 时生成逐步扩大范围的 sweep：
  `gateware/relock.py:26-78`。
- `[CONFIRMED]` 它没有谱线 identity、ERROR crossing target、
  target generation、atomic actual-bias capture 或 lock confirmation。
- `[CONFIRMED]` sweep、relock、filtered output 在 fast output 端直接求和：
  `gateware/chains.py:143-155`。没有 FPGA-MTS L1 的显式
  `SCAN -> ARM -> ACQUIRING -> P_LOCKED`。

因此 redpid 主要是低层 digital servo/gateware substrate，不是完整锁频系统。

## 4. 可借鉴项

| 功能 | 源文件 / symbol | 分类 | 与 FPGA-MTS 差异 | 推荐 |
|---|---|---|---|---|
| final limiter + saturation/railed | `chains.py:70-85,128-155`; `limit.py` | CONCEPTUALLY REUSABLE | FPGA-MTS 已有 correction/absolute limits 与 saturation | 无需重复开发 |
| clear/hold state crossbar | `chains.py:37-59,209-268` | CONCEPTUALLY REUSABLE | 灵活但会扩大 CSR/ownership；当前显式 FSM 更安全 | 不引入 |
| sweep generator | `chains.py:80-85,134-148`; `sweep.py` | NOT APPLICABLE NOW | 当前已有 `ramp_generator` 和 tests | 不引入 |
| rail-driven relock sweep | `relock.py:26-78` | FUTURE ONLY | 当前 Gate 禁止自动重锁；混合 D2 loop 下危险 | H4 后 |
| fast/slow chains | `README.rst:20-49`; `chains.py` | REQUIRES ARCHITECTURE CHANGE | 不是外部 D2 ownership model | 不用于当前混合环 |
| CSR-over-SSH CLI | `README.rst:13`; `test/csr.py` | NOT APPLICABLE NOW | 当前 backend 已有 SSH+/dev/mem 与 readback | 不引入 |

## 5. 对重点问题的回答

1. 它是 digital servo/gateware framework，不是完整自动锁频系统。
2. 没有可直接移植的 P-only bumpless transfer；limit/railed/clear/hold
   只能借鉴概念。
3. 没有谱线识别和 lock-point acquisition。
4. 对 FPGA-MTS 的价值主要是历史架构背景（Linien 的底层来源）和
   filter/limit/crossbar 写法；当前 L1 已实现更贴合本项目的 acquisition、
   supervisor 与安全限幅。

## 6. 最终结论

`redpid` 不应因为名字含 PID 就被列为 autolock 方案。当前直接引入价值低；
其 `Relock` 在基础 P-only 前明确不适用，在 D2-125 current loop 状态未知时
还可能扩大扫描并激化双环冲突。

