# Hardware Validation Record

## 当前 Gate

```text
Current Stage: v3LOCK-P0 / Stage 3 Hardware Verification
Current Gate: HV-1 OUT2 fixed-count physical voltage calibration
Git baseline: main clean, HEAD == origin/main
Latest main commit: 0e13f2806d7a716d3e66d365babbe2b247e59d8b
Bitstream MAGIC: 0x4D545330
Bitstream VERSION: 0x00030001
Board model: NOT RECORDED
Board identity: NOT RECORDED
Experiment date: NOT RECORDED
Operator: NOT RECORDED
```

当前只准备 HV-1，尚未执行硬件校准。当前唯一允许的实验点是 count=0；非零点、SCAN、LOCK HERE 和 P-only 均不在本次 Gate 操作范围内。

## 证据等级

- `[IMPLEMENTED]`：代码、文档或操作入口存在，尚未完成自动化验证。
- `[AUTOMATED VERIFIED]`：本轮软件检查或自动化测试实际通过。
- `[USER GUI VERIFIED]`：用户已在真实 GUI 中完成操作；不代表物理量已验证。
- `[USER HARDWARE VERIFIED]`：用户已完成真实接线和物理测量并提供结果。
- `[FAILED]`：Gate 已有明确失败证据，停止推进。
- `[NOT VERIFIED]`：尚未执行或证据不足。

## 当前证据基线

```text
CODE/REGISTER TRACE PASS
GUI ABSOLUTE VOLTAGE FAIL
PHYSICAL ADC/DAC CALIBRATION NOT VERIFIED
OUT1 LOCK MEANING NOT VERIFIED
P-ONLY CLOSED LOOP NOT VERIFIED
```

这里的 `GUI ABSOLUTE VOLTAGE FAIL` 表示 GUI nominal/ideal 换算不能作为真实物理电压证据，不表示 raw signed14 count 链失败。

## Hardware Verification Gates

| Gate | 目标 | 准备状态 | 实验状态 |
|---|---|---|---|
| HV-1 | OUT2 fixed count -> scope voltage | `[IMPLEMENTED]` | `[NOT VERIFIED]` |
| HV-2 | OUT2 SCAN CH4 -> scope OUT2 | `[NOT VERIFIED]` | `[NOT VERIFIED]` |
| HV-3 | CH3 -> physical OUT1 | `[NOT VERIFIED]` | `[NOT VERIFIED]` |
| HV-4 | IN1/IN2 physical voltage -> ADC counts | `[NOT VERIFIED]` | `[NOT VERIFIED]` |
| HV-5 | error zero crossing physical meaning | `[NOT VERIFIED]` | `[NOT VERIFIED]` |
| HV-6 | LOCK HERE Kp=0 bumpless transfer | `[NOT VERIFIED]` | `[NOT VERIFIED]` |
| HV-7 | minimal nonzero Kp P-only | `[NOT VERIFIED]` | `[NOT VERIFIED]` |

只有 HV-1 的文档和既有操作入口可以使用。HV-1 未获 `[USER HARDWARE VERIFIED]` 前，不得进入 HV-2 至 HV-7。

## 上位机能力审计

- `[IMPLEMENTED]` `Probe Registers` 和 `Status` 可读 `MAGIC`、`VERSION`、`MODE`、`ENABLE`、`STATUS`、`OUT2_MONITOR` 和 saturation。
- `[IMPLEMENTED]` 现有 `hold-v` 经 `round(volts * 8191)` 转成 signed14 count；`0.0000` 精确转换为 count=0。
- `[IMPLEMENTED]` HOLD 写入顺序为 `ENABLE=0 -> HOLD_VALUE -> MODE=2 -> ENABLE=1`，随后返回状态 readback。
- `[IMPLEMENTED]` `Capture Waveform` 可记录 CH4=`selected_out2` raw count。
- 风险：HOLD 不受 SCAN `OUT2_LIMIT` 保护；使用者必须先 SAFE，且当前只允许 count=0。
- 风险：上位机输入和显示的 V 是 nominal/ideal，不是实测或校准电压。

结论：现有上位机足够安全执行本次唯一授权的 count=0 点，无需修改 Python。该结论不授权用 `hold-v` 执行任意非零 count 校准；后续扩展 HV-1 点位前必须重新审查 exact-count 操作和安全边界。

## HV-1 OUT2 calibration record

当前仅第一行可由用户执行。其余行只是后续 HV-1 记录占位，不是本轮操作授权。

| requested_count | OUT2_MONITOR_count | CH4_count | mode | enable | saturation | scope_load | scope_coupling | probe_ratio | measured_voltage_mean_V | measured_voltage_min_V | measured_voltage_max_V | repeat_index | result | notes |
|---:|---:|---:|---:|---:|---|---|---|---|---:|---:|---:|---:|---|---|
| 0 | NOT RECORDED | NOT RECORDED | NOT RECORDED | NOT RECORDED | NOT RECORDED | NOT RECORDED | NOT RECORDED | NOT RECORDED | NOT RECORDED | NOT RECORDED | NOT RECORDED | 1 | `[NOT VERIFIED]` | 当前唯一允许点 |
| +1024 | NOT RECORDED | NOT RECORDED | NOT RECORDED | NOT RECORDED | NOT RECORDED | NOT RECORDED | NOT RECORDED | NOT RECORDED | NOT RECORDED | NOT RECORDED | NOT RECORDED | NOT RECORDED | `[NOT VERIFIED]` | 本轮禁止执行 |
| -1024 | NOT RECORDED | NOT RECORDED | NOT RECORDED | NOT RECORDED | NOT RECORDED | NOT RECORDED | NOT RECORDED | NOT RECORDED | NOT RECORDED | NOT RECORDED | NOT RECORDED | NOT RECORDED | `[NOT VERIFIED]` | 本轮禁止执行 |
| +2048 | NOT RECORDED | NOT RECORDED | NOT RECORDED | NOT RECORDED | NOT RECORDED | NOT RECORDED | NOT RECORDED | NOT RECORDED | NOT RECORDED | NOT RECORDED | NOT RECORDED | NOT RECORDED | `[NOT VERIFIED]` | 本轮禁止执行 |
| -2048 | NOT RECORDED | NOT RECORDED | NOT RECORDED | NOT RECORDED | NOT RECORDED | NOT RECORDED | NOT RECORDED | NOT RECORDED | NOT RECORDED | NOT RECORDED | NOT RECORDED | NOT RECORDED | `[NOT VERIFIED]` | 本轮禁止执行 |
| +4096 | NOT RECORDED | NOT RECORDED | NOT RECORDED | NOT RECORDED | NOT RECORDED | NOT RECORDED | NOT RECORDED | NOT RECORDED | NOT RECORDED | NOT RECORDED | NOT RECORDED | NOT RECORDED | `[NOT VERIFIED]` | 本轮禁止执行 |
| -4096 | NOT RECORDED | NOT RECORDED | NOT RECORDED | NOT RECORDED | NOT RECORDED | NOT RECORDED | NOT RECORDED | NOT RECORDED | NOT RECORDED | NOT RECORDED | NOT RECORDED | NOT RECORDED | `[NOT VERIFIED]` | 本轮禁止执行 |

## OUT2 fit record

```text
V_OUT2 = a2 * count + b2
a2: NOT RECORDED
b2: NOT RECORDED
counts_per_volt: NOT RECORDED
R2: NOT RECORDED
max_residual_V: NOT RECORDED
scope_load: NOT RECORDED
fit_result: NOT VERIFIED
```

一个 count=0 点不能拟合 gain；它只建立零点读回和测量流程。任何 50 ohm 下得到的系数都不能自动用于 Hi-Z 或 PZT 负载，反之亦然。

## 立即停止条件

出现以下任一情况，立即请求 SAFE 并停止 HV-1：

- `MAGIC` / `VERSION` 身份不匹配。
- 通信失败，或不能确认 SAFE 已执行。
- requested count、`OUT2_MONITOR` 或 CH4 不一致。
- OUT2 异常跳变、过压、削顶或 saturation。
- 极性现象无法解释。
- 接线、scope load、coupling 或 probe ratio 不明确。
- PZT 仍连接。
- OUT2 与任何其他有源输出并联。

## 下一步唯一动作

断开 PZT，使 OUT2 只连接示波器，按照 `software/redpitaya_lock_host/docs/HARDWARE_CALIBRATION_SOP.md` 只执行 count=0 的 HV-1 测量，记录 readback 和示波器真实电压，然后立即 SAFE。
