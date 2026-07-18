# Hardware Calibration SOP

## 当前范围：Gate L0 HOLD / LOCK HERE 对比

```text
Current Stage: v3LOCK-P0 / Linien-style Manual Lock Foundation
Current Gate: Gate L0 / Diagnose scan-to-lock offset
Allowed action: one A/B comparison, HOLD SELECTED COUNT vs LOCK HERE at Kp=0
Hardware result: [NOT VERIFIED]
```

本次只诊断用户已观察到的谱峰/cursor 偏移。它不是 P-only 实验，不授权 `APPLY P`、非零 Kp/Ki、polarity 切换、PI 或自动进入下一 Gate。

### 接线与开始条件

1. 从 `SAFE` 开始。OUT2 只连接激光器专用 PZT/Scan input，并通过被动 BNC T 接示波器；scope 使用 `1 MΩ/Hi-Z`、`DC coupling` 和正确 probe ratio。
2. 必须由用户确认该 PZT/Scan input 允许 `0.600~0.900 V`。断开激光器电流调制、D2-125 Servo/Aux Output 和其他有源输出，禁止输出并联。
3. `Probe Registers` 必须显示当前 `MAGIC/VERSION` 与 host 匹配。`SAFE -> Status` 必须为 `MODE=0`、`ENABLE=0`、无 saturation。
4. 使用已建立的低速条件：safe min/max `0.600/0.900 V`、center `0.770 V`、amplitude `0.080 V`、frequency `2 Hz`、`Kp=0`、`Ki=0`；polarity 保持原值。
5. Lock View capture window 必须覆盖至少一个完整 `2 Hz` 周期；当前 2048 points 对应 decimation 约 `30518`、window 约 `0.5 s`。窗口不正确时停止，不用短 capture 选点。

### 唯一实验：同一目标 A/B 对比

1. `START SCAN`，确认 loaded-node 电压约在 `0.690~0.850 V`、无 saturation/削顶/跳变，CH1/CH3/CH4 可重复。选择同一目标谱线和同一 MTS error 零交叉，记录 rising/falling、capture 标识、selected OUT2 counts 和 cursor 位置。
2. 执行 `HOLD SELECTED COUNT`。记录转换前 count、HOLD readback count、示波器实际 OUT2 电压、转换后立即及稳定后的谱峰/cursor 偏移、MODE/ENABLE 和 saturation，然后 `SAFE -> Status`。
3. 重新使用相同扫描参数、同一目标谱线、同一零交叉和同一扫描方向。记录新的 capture 标识及 selected OUT2 counts。
4. 执行一次 `LOCK HERE`，保持 `Kp=0`、`Ki=0`，不得点击 `APPLY P`。记录执行前 count、LOCK readback count、示波器实际 OUT2 电压、执行后立即及稳定后的谱峰/cursor 偏移、MODE/ENABLE 和 saturation，然后立即 `SAFE -> Status`。
5. 保存两组 CH1/CH3/CH4 截图或 CSV、scope 截图、操作时间和最终 SAFE 状态。用户确认数据完整后，Gate L0 才可作诊断判定。

### 判定

- HOLD 与 LOCK HERE 都偏：优先调查 PZT/激光器动态迟滞、扫描频率、rising/falling 和动态/静态电压差。
- HOLD 不偏、LOCK HERE 偏：优先调查目标方向约束、执行时重新捕获和 FPGA 原子触发机制。
- 两者真实电压均正确但谱峰都偏：优先调查 MTS 零交叉、解调相位和目标饱和吸收峰的对应关系。
- rising/falling 结果不同：先量化扫描方向对应的频率/迟滞差异，不进入 Kp。

Gate L0 的 PASS 只表示获得可比较数据并缩小根因类别，不表示 Kp=0 无扰、P-only 或激光锁定已经通过。数据不完整或两次目标/方向不可比时为 `[NOT VERIFIED]`，不是 PASS。

### 立即 SAFE / FAIL

身份或通信异常、SAFE 不可确认、端口/允许范围/接线/scope 条件不清、loaded-node 越界、readback 不一致、saturation、削顶、异常跳变、光谱消失、错误 capture、方向不明或任何有源输出并联时，立即 SAFE 并结束实验。失败后保留数据，不提高 Kp，不切换 polarity，不再次 LOCK。

### 用户需返回

- PZT/Scan 端口名称与允许范围；scope load、coupling、probe ratio 和接线图。
- 两次使用的 capture 标识、目标谱线/零交叉、rising/falling 和 selected counts。
- HOLD 与 LOCK HERE 各自的转换前 count、readback count、真实 OUT2 电压、立即/稳定后谱峰偏移、MODE/ENABLE/saturation。
- CH1/CH3/CH4 与 scope 截图或 CSV、异常现象以及最终 SAFE 状态。

## 历史 HV-1B 已完成范围

```text
Current Stage: v3LOCK-P0 / Stage 3 Hardware Verification
Historical Gate: HV-1B corrected OUT2 voltage mapping hardware re-validation
Allowed point: Scan center=0.800 V, amplitude=0.100 V, frequency=50 Hz
Hardware result: [USER HARDWARE VERIFIED] (user confirmation; exact measurement metadata not re-recorded)
```

本历史小节只记录修复后的单组 OUT2 SCAN 电压映射；当时的 HV-1B 不授权 LOCK HERE、APPLY P、P-only 或其他点位。2026-07-18 用户已确认当前软件预补偿后、PZT 断开时，上位机设定与板上 OUT2 输出一致；HV-1B 据此完成。精确测量数值和 scope 配置未在本轮重新提供，不在此虚构。

校准后 `hold-v=0.0000 V` 会发送约 `-65 counts` 以抵消实测零偏，不再等于 raw count=0。旧的 HOLD exact-count=0 流程已暂停；没有独立 exact-count 安全入口时不得继续该旧流程。

## 接线

1. 断开 PZT；OUT2 本次只允许连接示波器。
2. 禁止 OUT2 与 D2-125 Servo Output、D2-125 Aux Output 或任何其他有源输出并联。
3. 使用与修复前测量相同的 scope load、DC coupling、probe ratio 和线缆；若原条件无法确认，记录实际条件并把结果标为不可直接比较。
4. 若不是 DC coupling，停止实验。

## 开始前检查

1. 点击 `Probe Registers`，只在 `MAGIC=0x4D545330`、`VERSION=0x00030001`、Identity=`Matched` 时继续。
2. 点击 `SAFE` 后再点 `Status`；必须看到 `MODE=0`、`ENABLE=0`、无 saturation。
3. 确认 PZT 已断开、OUT2 只接示波器、示波器量程足以覆盖 `0.7 V` 至 `0.9 V`。

## HV-1B 单组步骤

1. 设置 `PZT safe min=0.700 V`、`PZT safe max=0.900 V`。
2. 设置 `Scan center=0.800 V`、`Scan amplitude=0.100 V`、`Scan frequency=50 Hz`。
3. 点击 `START SCAN`。软件预期写入 center `5734 counts`、amplitude `694 counts`；`OUT2_MONITOR` 应在约 `5040..6428 counts` 内变化且无 saturation。
4. 示波器记录三角波 center、Vpp、frequency，以及 scope load、coupling、probe ratio。
5. 测量完成后立即点击 `STOP / SAFE`，再点 `Status` 确认 `MODE=0`、`ENABLE=0` 且无 saturation。
6. 将结果写入 `version/HARDWARE_VALIDATION.md`；未提供复测结果前保持 `[NOT VERIFIED]`。

## PASS / FAIL

PASS 必须同时满足：

- 三角波形正常，frequency 接近 `50 Hz`。
- center 在 `0.800 V` 的 +/-5% 内。
- Vpp 在 `0.200 V` 的 +/-5% 内。
- 无 saturation、削顶、异常跳变或通信错误。
- 实验后已确认 SAFE。

以下任一情况立即 SAFE 并停止：身份不匹配、通信失败、OUT2 越界、saturation、削顶、异常跳变、接线/负载不清楚、PZT 未断开、OUT2 与其他输出并联，或无法确认最终 SAFE。失败后先记录证据，不修改 RTL，不提高 Kp，不切换 polarity，不执行 LOCK HERE。

## 历史 HV-1B 后续说明

HV-1B 已完成。除非校准、板卡、负载或模拟链发生变化，不重复本空载复测。当前唯一动作只看本文件顶部 Gate L0。
