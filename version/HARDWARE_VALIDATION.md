# Hardware Validation Record

## 当前 Gate

```text
Current Stage: v3LOCK-P0 / Stage 3 Hardware Verification
Current Gate: corrected OUT2 voltage mapping hardware re-validation
Git baseline: local main clean at task start; no remote refresh by user request
Latest local commit: 016f8d51b4500ec90f9d8006d138a8504c58b12a
Bitstream MAGIC: 0x4D545330
Bitstream VERSION: 0x00030001
Board model: Red Pitaya STEM125-14
Board identity: NOT RECORDED
Experiment date: NOT RECORDED
Operator: user-reported measurement
```

用户已提供修复前 SCAN center/amplitude 的示波器测量。本轮已根据这些数据实现软件预补偿；修复后的模拟输出尚未复测，当前 Gate 仍为 `[NOT VERIFIED]`。

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
PRE-CORRECTION GUI ABSOLUTE VOLTAGE FAIL
OUT2 VOLTAGE MAPPING SOFTWARE CORRECTION AUTOMATED VERIFIED
POST-CORRECTION OUT2 HARDWARE RE-VALIDATION NOT VERIFIED
OUT1 LOCK MEANING NOT VERIFIED
P-ONLY CLOSED LOOP NOT VERIFIED
```

这里的修复前 `GUI ABSOLUTE VOLTAGE FAIL` 不表示 raw signed14 count 链失败。RTL 审计确认 count 链无额外缩放；软件修正通过自动化测试仍不等于真实 OUT2 已校准。

## 2026-07-16 修复前 OUT2 mapping evidence

实验条件：Red Pitaya STEM125-14，OUT2 直接连接示波器，SCAN frequency `50 Hz`，三角波形和频率正常。scope load、coupling、probe ratio 和实验日期未记录。

| GUI Scan center (V) | scope actual center (V) |
|---:|---:|
| 0.500 | 0.5740 |
| 0.600 | 0.6875 |
| 0.700 | 0.8015 |
| 0.800 | 0.9130 |
| 0.900 | 1.0255 |

中心拟合：

```text
V_actual ~= 1.13 * V_GUI + 0.009 V
```

| GUI single-sided amplitude (V) | scope Vpp (V) |
|---:|---:|
| 0.050 | 0.125 |
| 0.100 | 0.237 |
| 0.200 | 0.462 |

幅度增益约 `1.18`。软件逆补偿为：

```text
absolute count = round(((V_target - 0.009) / 1.13) * 8191)
delta count    = round((V_delta / 1.18) * 8191)
```

- [AUTOMATED VERIFIED] SCAN center/amplitude、HOLD、manual LOCK_BIAS 和 PZT safe count 边界已使用统一软件校准层。
- `LOCK HERE` 捕获已在 count 域中的 `OUT2_MONITOR`，不重复转换。
- P correction 仍由 RTL 以 raw count 计算；未修改 Kp、correction limit 或锁定逻辑。修复后 P-only 物理增量为 `[NOT VERIFIED]`。
- 未修改 RTL、Vivado、register address/semantics 或 bitstream。

## Hardware Verification Gates

| Gate | 目标 | 准备状态 | 实验状态 |
|---|---|---|---|
| HV-1A | 修复前 GUI SCAN -> scope voltage mapping | `[IMPLEMENTED]` | `[USER HARDWARE VERIFIED]` |
| HV-1B | 修复后 center=0.8 V / amplitude=0.1 V 复测 | `[AUTOMATED VERIFIED]` | `[NOT VERIFIED]` |
| HV-2 | OUT2 SCAN CH4 -> scope OUT2 扩展验证 | `[NOT VERIFIED]` | `[NOT VERIFIED]` |
| HV-3 | CH3 -> physical OUT1 | `[NOT VERIFIED]` | `[NOT VERIFIED]` |
| HV-4 | IN1/IN2 physical voltage -> ADC counts | `[NOT VERIFIED]` | `[NOT VERIFIED]` |
| HV-5 | error zero crossing physical meaning | `[NOT VERIFIED]` | `[NOT VERIFIED]` |
| HV-6 | LOCK HERE Kp=0 bumpless transfer | `[NOT VERIFIED]` | `[NOT VERIFIED]` |
| HV-7 | minimal nonzero Kp P-only | `[NOT VERIFIED]` | `[NOT VERIFIED]` |

当前只允许执行 HV-1B 的单组修复后复测；HV-1B 未通过前不得进入 HV-2 至 HV-7。

## 上位机能力审计

- `[IMPLEMENTED]` `Probe Registers` 和 `Status` 可读 `MAGIC`、`VERSION`、`MODE`、`ENABLE`、`STATUS`、`OUT2_MONITOR` 和 saturation。
- `[AUTOMATED VERIFIED]` SCAN center、HOLD 和 manual LOCK_BIAS 经 `round(((V_target - 0.009) / 1.13) * 8191)` 转成 signed14 count。
- `[AUTOMATED VERIFIED]` SCAN single-sided amplitude 经 `round((V_delta / 1.18) * 8191)` 转换；`0.100 V` 为 `694 counts`。
- `[IMPLEMENTED]` HOLD 写入顺序为 `ENABLE=0 -> HOLD_VALUE -> MODE=2 -> ENABLE=1`，随后返回状态 readback。
- `[IMPLEMENTED]` `Capture Waveform` 可记录 CH4=`selected_out2` raw count。
- 风险：校准后 `hold-v=0.0000 V` 预补偿为 `-65 counts`，不再是 exact count=0；旧 count=0 SOP 已暂停。
- 风险：软件电压是基于本次实测系数的估算；示波器仍是硬件 Gate 的物理真值。

结论：现有上位机已实现 HV-1B 所需的软件预补偿。只授权 PZT 断开时执行 center `0.800 V`、amplitude `0.100 V`、50 Hz 的示波器复测；不授权 LOCK HERE 或 P-only。

## Earlier exact-count calibration record

该表保留为早期 exact-count 计划记录，不是当前操作入口。校准后的 `hold-v` 是物理电压请求，不能再用于指定 raw count；在增加独立 exact-count 安全入口前，禁止执行本表点位。

| requested_count | OUT2_MONITOR_count | CH4_count | mode | enable | saturation | scope_load | scope_coupling | probe_ratio | measured_voltage_mean_V | measured_voltage_min_V | measured_voltage_max_V | repeat_index | result | notes |
|---:|---:|---:|---:|---:|---|---|---|---|---:|---:|---:|---:|---|---|
| 0 | NOT RECORDED | NOT RECORDED | NOT RECORDED | NOT RECORDED | NOT RECORDED | NOT RECORDED | NOT RECORDED | NOT RECORDED | NOT RECORDED | NOT RECORDED | NOT RECORDED | 1 | `[NOT VERIFIED]` | 历史占位；当前禁止执行 |
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

保持 PZT 断开且 OUT2 只接示波器，按 `software/redpitaya_lock_host/docs/HARDWARE_CALIBRATION_SOP.md` 复测 `Scan center=0.800 V`、`Scan amplitude=0.100 V`、`50 Hz`；中心约 `0.800 V`、Vpp 约 `0.200 V` 且误差均小于 5% 才 PASS，记录后立即 SAFE。
