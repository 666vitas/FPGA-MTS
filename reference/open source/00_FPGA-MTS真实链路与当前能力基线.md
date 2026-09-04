# FPGA-MTS 真实链路与当前能力基线

> 审计日期：2026-07-27
> 任务模式：ANALYZE（产品代码只读；本文是允许的分析产物）
> 当前 Gate：`LOCK-MVP-L1`
> 证据标签：`[CONFIRMED]`、`[INFERENCE]`、`[NOT VERIFIED]`、`[NOT APPLICABLE]`

## 1. 审计边界与权威来源

当前 active 事实由以下文件约束：

- `../AGENTS.md`
- `../version/CURRENT_GATE.md`
- `../version/STATUS.md`
- `../version/CURRENT_REVIEW_MANIFEST.md`
- `../version/rules/20_FPGA_MTS_ENGINEERING_WORKFLOW.md`
- `../docs/architecture/FPGA_MTS_LINIEN_BASIC_LOCK_PROJECT_SPEC.md`

`CURRENT_REVIEW_MANIFEST.md` 的元数据仍写 `LOCK-MVP-T0`，而
`CURRENT_GATE.md` 与 `STATUS.md` 已进入 `LOCK-MVP-L1`。按照文档优先级，
本审计以 L1 为当前 Gate，并把 manifest 的代码范围作为最低读取集合。

## 2. 真实混合物理链路

```text
PD  ───────────────> Red Pitaya IN1
REF ───────────────> Red Pitaya IN2
                         |
                         +-- FPGA mixer/LPF --> OUT1 = laser_error
                         |
                         +-- SCAN / P-only --> OUT2 = selected_out2
                                                  |
                                                  +--> laser dedicated PZT/Scan input

MTS ERROR ──> D2-125 Error Input [NOT VERIFIED: actual source]
                  |
                  +--> D2-125 Servo Output --> laser current input [user-stated physical chain]
```

- `[CONFIRMED]` FPGA 固定语义是 `IN1=PD`、`IN2=REF`、`OUT1=laser_error`、
  `OUT2=selected_out2`。证据：`../AGENTS.md:20-33`；
  `../v0.94/rtl/red_pitaya_top.sv:490-513,551-576,591-616`。
- `[CONFIRMED]` FPGA-MTS 代码只建模 Red Pitaya 的 PZT/Scan 执行器，
  没有 D2-125 状态对象、寄存器、遥测或互锁。产品代码对 `D2-125`
  的命中仅是 GUI 文案与安全警告，而非控制模型。
- `[CONFIRMED]` GUI 当前甚至显示
  `D2-125 Error Input -> FPGA mixer + LPF -> laser_error`：
  `../software/redpitaya_lock_host/redpitaya_lock_host/main_window.py:2192-2194`。
  这是一段“替代路径”说明，不能证明真实 D2-125 Error Input 已接 OUT1。
- `[NOT VERIFIED]` D2-125 Error Input 的实际信号、servo enable/hold/manual
  状态、polarity、积分器状态、带宽、DC gain、current tuning coefficient。
- `[NOT VERIFIED]` D2-125 Servo Output 仍连接 current input 的事实来自本次
  用户任务说明，尚无本地接线照片、示波器记录或电子 readback。

永久安全边界：OUT2 只能接激光器专用 PZT/Scan input 与测量设备，禁止接
current modulation、D2-125 `Servo Output`、`Aux Output` 或任何其他有源输出，
禁止输出并联。

## 3. 当前代码模块图

```text
GUI MainWindow
  |  click CH1/CH3, resolve ERROR crossing, show diagnostics
  v
LockService ----------------------+
  | host state / valid commands   |
  v                               v
AcquisitionService          custom_fpga_backend
  | capture_id              CSR mapping / SSH+/dev/mem
  +---------------+---------------+
                  v
custom_register_bank
  | shadow -> active snapshot, VERSION/capability, event readback
  v
simple_lock_acquisition
  | direction + guard + realtime H/N ERROR crossing
  | ARM_VALIDATE / ARM_ACTIVE
  | actual OUT2 capture, Kp ramp, supervisor, event recorder
  v
out2_lock_controller
  | bias + polarity * ((Kp * lock_error) >>> 8)
  | correction limit -> absolute limit -> servo divider -> slew limit
  v
selected_out2 -> official DAC saturation/ODDR shell -> OUT2
```

关键调用证据：

- `LockService.request_lock()` 构造 target 配置并选择
  `validate_lock_target()` 或 `arm_lock_target()`：
  `../software/redpitaya_lock_host/redpitaya_lock_host/core/lock_service.py:62-132`。
- `simple_lock_acquisition` 同拍对齐 ERROR/OUT2/setpoint/方向上下文：
  `../v0.94/rtl/simple_lock_acquisition.sv:185-220,467-518`。
- crossing detector 与 guard/direction 条件：
  `../v0.94/rtl/simple_lock_acquisition.sv:520-560`。
- VALIDATE 只记录事件；ACTIVE 捕获实际 OUT2 并启动 Kp ramp/supervisor：
  `../v0.94/rtl/simple_lock_acquisition.sv:772-821`。
- register bank 在 trigger 时把实际 OUT2 写入 `lock_bias_o`：
  `../v0.94/rtl/custom_register_bank.sv:489-495`。
- P-only 算术与限幅/更新：
  `../v0.94/rtl/custom_register_bank.sv:1926-2045`。

## 4. 当前能力分类表

| 能力 | 分类 | 结论与证据 |
|---|---|---|
| aligned PD/REF/ERROR/OUT2 capture | A/C | `[CONFIRMED]` 四通道在同一 `always_ff`、同一 write index 写 RAM：`custom_debug_capture.sv:45-93`；接线为 CH1=PD、CH2=REF、CH3=ERROR、CH4=OUT2：`red_pitaya_top.sv:559-576`。`tb_custom_debug_capture.sv` 存在，STATUS 报告完整 RTL 回归通过。 |
| `capture_id` | A/B | `[CONFIRMED]` `AcquisitionService` 自增并拒绝 stale target：`acquisition_service.py:13-35,80-85`；`LockTarget.capture_id`：`lock_models.py:29-42`。 |
| `scan_generation` | F | `[CONFIRMED]` 没有此字段。GUI 有进程内 `custom_capture_generation` 和独立 `config_generation`：`main_window.py:963-964,3702,3807-3808`，但扫描参数改变时统一递增、持久化并失效 target 的 `scan_generation` 语义未实现。 |
| 用户点击 PD feature，再解析 ERROR crossing | A/B/E | `[CONFIRMED]` UI 提示可点 CH1/CH3：`main_window.py:2105-2106,3619-3702`；`resolve_direct_error_zero_crossing()` 做插值、方向、slope、noise/range 检查：`main_window.py:518-642`。GUI 真实硬件选择行为仍 `[NOT VERIFIED]`。 |
| 零交叉插值 | A/B | `[CONFIRMED]` `interpolate_zero_crossing()`：`custom_fpga_backend.py:447-483`，并由 GUI selection 调用。相关 host tests 位于 `tests/test_custom_fpga_backend.py`、`test_custom_fpga_workflow.py`。 |
| rising/falling 与 ERROR NEG_TO_POS/POS_TO_NEG | A/B/C | `[CONFIRMED]` 两个方向是独立 enum/config：`custom_fpga_backend.py:43-52,105-118,305-329`；RTL 分开校验：`simple_lock_acquisition.sv:260-268,524-541`。 |
| target window / guard | A/B/C | `[CONFIRMED]` L1 把历史 target/window 解释为 guard；Host 验证 safe/absolute range：`custom_fpga_backend.py:285-350`；RTL guard：`simple_lock_acquisition.sv:435-456,482-489`。 |
| target shadow/active snapshot | A/C | `[CONFIRMED]` shadow fields：`custom_register_bank.sv:147-151,573-599`；ARM mailbox 原子提交 active：`simple_lock_acquisition.sv:356-465`。 |
| ARM VALIDATE | A/B/C/E | `[CONFIRMED]` `validate_only` 路由和 readback 约束：`lock_service.py:108-131`；RTL `STATE_VALIDATING` 只记 event：`simple_lock_acquisition.sv:772-790`。硬件 `[NOT VERIFIED]`。 |
| ARM ACTIVE / FPGA realtime crossing | A/B/C/E | `[CONFIRMED]` RTL 在 `adc_clk` 域触发，不依赖 host polling：`simple_lock_acquisition.sv:524-560,792-816`。硬件 `[NOT VERIFIED]`。 |
| actual OUT2 原子作为 bias | A/C/E | `[CONFIRMED]` trigger sample：`simple_lock_acquisition.sv:793-815`；commit bias：`custom_register_bank.sv:489-495`。数字与模拟 bumpless 硬件效果 `[NOT VERIFIED]`。 |
| P_LOCK_KP0 | A/B/C/E | `[CONFIRMED]` 允许用户明确请求 Kp 0/4：`lock_service.py:62-65`；FPGA Kp ramp 可从 0 开始。当前 L1 正常 ACTIVE 也允许预批准非零 target，不应把“状态已进入 P_LOCK”写成真实锁定。 |
| Kp ramp / effective Kp | A/B/C | `[CONFIRMED]` `l1_kp_ramp` 实例：`simple_lock_acquisition.sv:586-601`；readback 字段：`lock_models.py:63-67`、L1 CSR 文档。 |
| servo divider / slew limit | A/B/C | `[CONFIRMED]` `out2_lock_controller` 的 divider 与 slew commit：`custom_register_bank.sv:1863-1865,2016-2036`。 |
| correction limit / absolute limit / saturation | A/B/C | `[CONFIRMED]` 两级限幅和 saturation：`custom_register_bank.sv:1830-1857,1951-1979`。 |
| lock supervisor | A/B/C/E | `[CONFIRMED]` `l1_lock_supervisor` 以 mean/abs/divergence windows 决策：`simple_lock_acquisition.sv:603-628,818-821`。它证明 FPGA 判据通过，不证明 sustained frequency lock。 |
| event timestamp/readback | A/B/C | `[CONFIRMED]` event payload 含 sequence、OUT2、ERROR、lock_error、generation、64-bit cycle timestamp：`simple_lock_acquisition.sv:833-856`。 |
| GUI acquisition/event/bias/delta/fault diagnostics | A/B/E | `[CONFIRMED]` 诊断建模：`main_window.py:310-355,1414-1745,4166-4351`。真实 GUI/板卡仍 `[NOT VERIFIED]`。 |
| D2-125 external-controller state | F/G | `[CONFIRMED]` 无状态模型，仅有文案。真实混合环路 Gate 不匹配。 |
| PI/Ki、自动重锁、AI | H / NOT APPLICABLE | 源码候选或历史路径不属于当前 Gate；不能列为本轮建议实现。 |

### 自动验证证据等级

- `[UNIT TESTED]` `STATUS.md:39-48` 报告 host tests `148 passed`。
- `[RTL SIMULATED]` `STATUS.md:39-48` 报告 20 个 testbench 全通过，其中
  OUT2 controller 54/54、SIMPLE 32/32、crossing 13/13、Kp ramp 6/6、
  supervisor 5/5。
- `[TIMING PASSED]` routed setup/hold 数值满足：
  `WNS=0.142 ns`、`TNS=0`、`WHS=0.053 ns`、`THS=0`：
  `STATUS.md:49-61`。
- `[NOT VERIFIED]` 完整 Timing Gate：仍有 unconstrained/no-delay/no-clock
  项：`STATUS.md:62-65`。
- `[NOT VERIFIED]` bitstream、板卡加载、ARM VALIDATE/ACTIVE、PZT bumpless、
  P-only convergence、60 秒 sustained lock：`STATUS.md:66-68`。

## 5. 与真实混合链路的关键缺口

1. `[CONFIRMED]` Host/FPGA 没有建模 D2-125；它不知道 external current loop
   是 OFF/ON/HOLD/UNKNOWN。
2. `[CONFIRMED]` GUI 文案把“未来替代关系”写得像真实接线，容易把
   D2-125 Error Input source 误认为已确认。
3. `[INFERENCE]` 若 D2-125 current loop 同时含 DC/I 增益，它会改变
   `OUT2(PZT) -> ERROR` 的有效 plant；当前单执行器仿真
   `error = slope*(out2-target)+noise` 不能代表此闭环 plant。
4. `[INFERENCE]` 两环若同时校正同一 ERROR DC，会争夺零点；D2-125
   若更快，可能把 FPGA 可观察误差压低；若两者积分或 DC 增益重叠，
   可能出现慢漂、windup、执行器撞限。
5. `[CONFIRMED]` `scan_generation` 缺失，capture freshness 主要依赖 GUI
   进程内 counter；“扫描参数改变即 target 失效”的契约没有统一归属。

## 6. 必须增加到硬件流程的人工确认（不是自动检测）

在任何 ACTIVE 硬件实验之前，Host 应要求操作者明确确认并记录：

| 项目 | 允许值 | 当前值 |
|---|---|---|
| D2-125 current loop | OFF / ON / HOLD / UNKNOWN | `[NOT VERIFIED]` |
| D2-125 polarity | POS / NEG / UNKNOWN | `[NOT VERIFIED]` |
| D2-125 integrator | RESET / ACTIVE / DISABLED / UNKNOWN | `[NOT VERIFIED]` |
| D2-125 Error Input source | OUT1 / other / disconnected / UNKNOWN | `[NOT VERIFIED]` |
| D2-125 Servo Output connection | current input / disconnected / other / UNKNOWN | `[NOT VERIFIED]` |
| D2-125 bandwidth / DC gain | measured values / UNKNOWN | `[NOT VERIFIED]` |
| PZT/current tuning direction | measured signs / UNKNOWN | `[NOT VERIFIED]` |

这些字段只能标为“用户确认”，不能显示为“软件检测”。

## 7. 基线结论

- 当前项目不缺 ARM、crossing、actual-bias capture、Kp ramp、limits、
  supervisor 或 GUI diagnostics；不要重复开发。
- 当前真正的 P0 风险不是按钮数量，而是完整 Timing Gate 未闭合，以及
  D2-125 current loop 对真实 plant、scan-to-lock 和锁定判断的影响未建模。
- 当前唯一安全推进方向仍是：先完成现行 timing/XDC 审计，然后由用户
  在明确 D2-125 状态的前提下执行单一硬件 Gate。
