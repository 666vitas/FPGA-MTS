Status: SUPPORTING
Effective-Gate: ALL
Authority: SUPPORTING
Last-Updated: 2026-07-24
Supersedes: version/HARDWARE_VALIDATION.md
Superseded-By: NONE

# Hardware Validation Record

> 本文件保存真实硬件校准、接线和旧 Gate 证据。正文中的“当前 Gate/下一步”是历史记录，不能覆盖 `version/CURRENT_GATE.md` 与 `version/STATUS.md`。

## 当前 Gate

```text
Current Stage: v3LOCK-P0 / Linien-style Manual Lock Foundation
Current Gate: Gate L0 / Diagnose scan-to-lock offset
Git baseline: local main with pre-existing uncommitted host/test/HV-2 documentation changes; no remote refresh
Latest local commit: 14dba075fe3a533956f3857d00a1bb8a5214e45a
Bitstream MAGIC: 0x4D545330
Bitstream VERSION: 0x00030001
Board model: Red Pitaya STEM125-14
Board identity: NOT RECORDED
Experiment date: NOT RECORDED
Operator: user-reported measurement
```

用户已提供修复前 SCAN center/amplitude 的示波器测量，并在 2026-07-18 明确确认：使用当前软件预补偿、PZT 断开时，上位机设定电压与板上真实 OUT2 输出一致。HV-1B 据此标记为 `[USER HARDWARE VERIFIED]`；用户未在本轮重新提供精确 center/Vpp/frequency 和 scope 配置数值，本记录不虚构这些数据。

用户在本次任务中明确报告：loaded PZT 实验已能观察 PZT 扫描、PD、MTS error 和 OUT2，也能选择目标 error zero crossing，但执行 `LOCK HERE` 后目标饱和吸收峰与示波器 cursor 明显偏离。Current Gate 因此收敛为 Gate L0：在同一目标和方向下对比 `HOLD SELECTED COUNT` 与 `LOCK HERE, Kp=0`，只定位偏移来源；不授权 `APPLY P`、非零 Kp/Ki、polarity 变更或下一 Gate。

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
POST-CORRECTION OUT2 HARDWARE RE-VALIDATION USER HARDWARE VERIFIED
LOADED PZT SCAN NODE VOLTAGE NOT VERIFIED
LOCK HERE PEAK/CURSOR OFFSET USER HARDWARE VERIFIED
HOLD VS LOCK HERE ROOT CAUSE NOT VERIFIED
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

## Hardware Evidence Track And Current Gate

| Gate | 目标 | 准备状态 | 实验状态 |
|---|---|---|---|
| HV-1A | 修复前 GUI SCAN -> scope voltage mapping | `[IMPLEMENTED]` | `[USER HARDWARE VERIFIED]` |
| HV-1B | 修复后 center=0.8 V / amplitude=0.1 V 复测 | `[AUTOMATED VERIFIED]` | `[USER HARDWARE VERIFIED]` |
| HV-2 | loaded PZT SCAN 节点电压 + CH1/CH3 光谱响应 | `[AUTOMATED VERIFIED]` | `[NOT VERIFIED]` |
| HV-3 | CH3 -> physical OUT1 | `[NOT VERIFIED]` | `[NOT VERIFIED]` |
| HV-4 | IN1/IN2 physical voltage -> ADC counts | `[NOT VERIFIED]` | `[NOT VERIFIED]` |
| HV-5 | error zero crossing physical meaning | `[NOT VERIFIED]` | `[NOT VERIFIED]` |
| HV-6 | LOCK HERE Kp=0 bumpless transfer | `[NOT VERIFIED]` | `[NOT VERIFIED]` |
| HV-7 | minimal nonzero Kp P-only | `[NOT VERIFIED]` | `[NOT VERIFIED]` |
| Gate L0 | 同一目标/方向的 HOLD 与 LOCK HERE Kp=0 对比 | `[AUTOMATED VERIFIED]` | `[NOT VERIFIED]` |

HV-* 行保留校准和硬件证据历史，不再作为当前开发流程控制器。当前只允许执行 Gate L0 的单次 A/B 对比；用户未确认 Gate L0 前不得进入原子 scan-to-lock 实现、非零 Kp 或 P-only。

## 上位机能力审计

- `[IMPLEMENTED]` `Probe Registers` 和 `Status` 可读 `MAGIC`、`VERSION`、`MODE`、`ENABLE`、`STATUS`、`OUT2_MONITOR` 和 saturation。
- `[AUTOMATED VERIFIED]` SCAN center、HOLD 和 manual LOCK_BIAS 经 `round(((V_target - 0.009) / 1.13) * 8191)` 转成 signed14 count。
- `[AUTOMATED VERIFIED]` SCAN single-sided amplitude 经 `round((V_delta / 1.18) * 8191)` 转换；`0.100 V` 为 `694 counts`。
- `[IMPLEMENTED]` HOLD 写入顺序为 `ENABLE=0 -> HOLD_VALUE -> MODE=2 -> ENABLE=1`，随后返回状态 readback。
- `[IMPLEMENTED]` `Capture Waveform` 可记录 CH4=`selected_out2` raw count。
- `[AUTOMATED VERIFIED]` Lock View 在 scan frequency 或 capture length 变化时自动重算 capture decimation；`2 Hz / 2048 points` 为约 `30518`，capture window 约 `0.5 s`，覆盖一个完整扫描周期。
- 风险：校准后 `hold-v=0.0000 V` 预补偿为 `-65 counts`，不再是 exact count=0；旧 count=0 SOP 已暂停。
- 风险：软件电压是基于本次实测系数的估算；示波器仍是硬件 Gate 的物理真值。

结论：现有上位机已实现 Gate L0 所需的 identity、SAFE、SCAN safe-range、MODE/ENABLE、selected-count HOLD、Kp=0 LOCK HERE、OUT2 readback、saturation 和 capture 观测。只授权按 `HARDWARE_CALIBRATION_SOP.md` 执行一次 HOLD/LOCK HERE A/B 对比；不授权 Apply Kp、polarity 变更、PI 或 P-only 完成声明。

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

## 当前 Gate L0 立即停止条件

出现以下任一情况，立即请求 SAFE 并停止 Gate L0：

- `MAGIC` / `VERSION` 身份不匹配。
- 通信失败，或不能确认 SAFE 已执行。
- requested count、`OUT2_MONITOR` 或 CH4 不一致。
- OUT2 异常跳变、过压、削顶或 saturation。
- 极性现象无法解释。
- 接线、scope load、coupling 或 probe ratio 不明确。
- 无法确认当前端口是激光器专用 PZT/Scan 输入，或无法确认该输入允许 `0.600~0.900 V`。
- OUT2 与任何其他有源输出并联。

## 下一步唯一动作

按 `software/redpitaya_lock_host/docs/HARDWARE_CALIBRATION_SOP.md` 执行一次 Gate L0 A/B 对比：保持 `center=0.770 V / amplitude=0.080 V / 2 Hz / Kp=0 / Ki=0`，对同一谱线、zero crossing 和 rising/falling 方向分别记录 `HOLD SELECTED COUNT` 与 `LOCK HERE` 的 selected/readback counts、真实 loaded-node 电压和谱峰/cursor 偏移；两次动作之间及结束后均 SAFE。
