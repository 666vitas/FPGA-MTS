# Loaded PZT Scan SOP

> **HISTORICAL / NOT ACTIVE**：本文件保留 Gate L0 前的 HV-2 SCAN-only 准备流程，不再定义当前唯一动作。当前 Gate 和 A/B 对比步骤见 `version/STATUS.md` 顶部与 `HARDWARE_CALIBRATION_SOP.md`。

## 当前范围

```text
Current Stage: v3LOCK-P0 / Stage 3 Hardware Verification
Current Gate: Gate 2 / HV-2 loaded PZT SCAN voltage and spectral-response verification
Allowed action: one slow SCAN-only measurement
Hardware result: [NOT VERIFIED]
```

本 Gate 只确认真实 loaded PZT 节点的扫描电压、频率和对应光谱/MTS error 响应。不执行 `HOLD SELECTED COUNT`、`LOCK HERE`、`APPLY P`、非零 Kp/Ki、polarity 切换、P-only 或 PI。

## 目的

在不进入反馈的前提下，证明 OUT2 连接真实激光器 PZT/Scan 输入后：

1. loaded-node 电压仍在已确认的 PZT 安全范围内。
2. 扫描会产生可重复的光谱和色散型 CH3 MTS error 结构。
3. identity、MODE、ENABLE、OUT2 readback、saturation 和 SAFE 行为正常。

## 接线与开始前条件

1. 先保持 `SAFE`。
2. 确认激光器端口是专用 `PZT/Scan input`，且制造商规格或用户已确认它允许 `0.600~0.900 V`。无法确认时不开始。
3. 在 PZT 节点使用被动 BNC T：`OUT2 -> PZT/Scan input + 示波器`。示波器必须为 `1 MΩ/Hi-Z`、`DC coupling`，probe ratio 与实际探头一致。
4. 断开 D2-125 Servo Output、D2-125 Aux Output、激光器电流调制输入和其他有源输出；禁止任何输出端并联。
5. 示波器量程覆盖至少 `0.600~0.900 V`；确认连线和探头不会短路 PZT 节点。

## 唯一操作

1. 点击 `Probe Registers`；只在 `MAGIC=0x4D545330`、`VERSION=0x00030001`、Identity=`Matched` 时继续。
2. 点击 `SAFE -> Status`；确认 `MODE=0`、`ENABLE=0`、无 saturation。
3. 设置：
   - `PZT safe min=0.600 V`
   - `PZT safe max=0.900 V`
   - `Scan center=0.770 V`
   - `Scan amplitude=0.080 V`
   - `Scan frequency=2 Hz`
   - `Capture view=Lock View`
   - `capture-length=2048`
   - `capture-decimation`应自动跟随为约 `30518`，界面必须显示 capture window 约 `0.5 s`
   - `Kp=0`
   - `Ki=0`
   - polarity 保持当前值，不在本 Gate 中切换
4. 点击 `START SCAN`。只观测 SCAN；不点击 HOLD、LOCK HERE 或 APPLY P。
5. 在示波器记录 loaded PZT 节点的 min、max、center、Vpp、frequency、波形和 probe/load/coupling。目标电压约为 `0.690~0.850 V`、center `0.770 V`、Vpp `0.160 V`。
6. Capture 前再确认界面显示约 `0.5 s` 的完整扫描窗口。若仍约为 `0.02 s`，不得用该 capture 判定 PASS/FAIL；重新选择 `Lock View` 并核对 `2048 / 30518`。然后执行一次 `Capture Waveform`，保存 CH1、CH3、CH4 截图和 CSV；记录 SCAN 时 `MODE=1`、`ENABLE=1`、`OUT2_MONITOR`、saturation。
7. 观测完成后立即点击 `STOP / SAFE -> Status`；确认 `MODE=0`、`ENABLE=0`、无 saturation。

## PASS / FAIL

PASS 必须同时满足：

- loaded-node 三角波正常，frequency 接近 `2 Hz`。
- center 和 Vpp 分别在 `0.770 V` 和 `0.160 V` 的 +/-5% 内，且 min/max 不越过 `0.600~0.900 V`。
- CH1 光谱和 CH3 MTS error 随扫描重复出现，CH3 具有可用的目标色散过零结构。
- Lock View capture window 至少覆盖一个完整 `2 Hz` 扫描周期（约 `0.5 s`），不用短窗口推断完整扫描。
- `MODE=1`、`ENABLE=1`、OUT2 readback 与 SCAN 范围一致，无 saturation、削顶、异常跳变或通信错误。
- 实验后已确认最终 SAFE。

FAIL：任一 PASS 条件不满足，或无法确认 PZT 端口/额定范围、接线、示波器条件、identity、readback 或最终 SAFE。FAIL 后保留数据，不进入人工锁点或非零 Kp。

## 立即 SAFE

以下任一情况立即 `STOP / SAFE` 并结束本 Gate：

- `MAGIC/VERSION` 不匹配、通信失败或 SAFE 不可确认。
- 端口不是专用 PZT/Scan input，或 OUT2 与任何有源输出并联。
- loaded-node 超过 `0.600~0.900 V`、saturation、削顶、异常跳变或无法解释的极性反转。
- CH1/CH3 波形消失、异常或与扫描无可重复关系。

## 用户需返回的数据

- 激光器 PZT/Scan 端口名称及已确认的允许电压范围。
- 示波器 loaded-node 截图，以及 min/max/center/Vpp/frequency、load、DC coupling、probe ratio。
- CH1/CH3/CH4 截图和本次 capture CSV。
- SCAN 时和最终 SAFE 时的 `MAGIC`、`VERSION`、`MODE`、`ENABLE`、`OUT2_MONITOR`、saturation。
- PASS 或 FAIL，以及任何异常跳变、削顶、光谱消失或通信错误。
