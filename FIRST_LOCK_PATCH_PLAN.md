# FPGA-MTS v0.94 FIRST_LOCK 最小补丁与实验计划

Gate：`LOCK-MVP-L1`
原则：单板、PZT P-only、D2-125 电流快环保留；不扩展 AI、自动识峰/重锁、PI/Ki、多板、GUI 重构。

## 1. 最小修改清单

| 优先级 | 修改 | 状态 | 理由 / 验证 |
|---:|---|---|---|
| 0 | `red_pitaya_top` 增加默认 `ENABLE_DAISY=0`，静态隔离 legacy Daisy | `[IMPLEMENTED]` | 当前 Timing blocker；需 fresh elaborate/sim/synth/impl/CDC/timing |
| 0 | 更新 Gate STATUS，明确旧 timing 不适用于修改后 candidate | `[IMPLEMENTED]` | 防止把正 WNS 误写成新 build 已通过 |
| 1 | CH4 改名为 DAC-pre command counts，estimate/measured 分栏 | `[PLANNED]` | 降低 GUI 与 scope 量义误判；Timing Gate 后实施 |
| 1 | Lock View 改为两周期并显示 frame age/id/generation/direction | `[PLANNED]` | 提升 crossing 重复性判断；Timing Gate 后实施 |
| 1 | FIRST_LOCK 主路径显式展示 VALIDATE、ACTIVE Kp=0、用户批准 Kp=4 | `[PLANNED]` | 不让一键 Basic 操作隐藏硬件 Gate |
| 条件项 | Daisy 隔离后仍存在的 DNA/接口 timing finding 逐项约束或证明 | `[NOT VERIFIED]` | 只针对真实同步关系处理；禁止 blanket false path |

本轮不修改 mixer、LPF、acquisition、P controller、CSR、`MAGIC`、`VERSION`、capability、XDC、Vivado Tcl 或 Host 产品代码。

## 2. 修改后验证顺序

必须产生同一个 clean candidate 的连续证据：

1. 确认 top 默认 `ENABLE_DAISY=0`，compile order 使用当前 `v0.94/rtl`。
2. SystemVerilog compile/elaboration；运行现有全部 RTL behavioral testbench。任何 compile/sim failure 都停止。
3. clean synthesis，检查 Daisy recovered-clock 实例未 elaboration，并检查 latch、multiple-driver、width、black-box warning。
4. clean implementation；记录 part、Vivado 版本、source hash、WNS/TNS/WHS/THS 和 failing endpoints。
5. `report_cdc -details`：Daisy `pll_adc_clk <-> par_clk` critical CDC 必须消失；其余 CDC 逐项解释或修复。
6. `check_timing`：no-clock、unconstrained internal endpoints、no-input/output-delay 逐类审核；不使用 blanket exception。
7. `report_drc`、`report_methodology` 和 routed timing 满足 active Gate 后，才允许生成 bitstream。
8. bitstream 生成不等于烧录；烧录和接板仍需用户单独执行并记录实际文件/hash、`MAGIC/VERSION/capability` readback。

## 3. 烧录前检查清单

- [ ] 修改后 RTL simulation 全通过，且不是沿用旧日志。
- [ ] clean synthesis/implementation 使用 `xc7z010clg400-1` 和当前 source set。
- [ ] setup/hold 均通过；报告无 failing endpoint。
- [ ] Daisy critical CDC 已消失；剩余 CDC 有明确同步结构与解释。
- [ ] `check_timing` 各项满足 active rule；未用虚假 false path 掩盖问题。
- [ ] DRC/methodology 无未处置 critical warning。
- [ ] build 记录 bitstream、source、Vivado 版本和报告的一致身份。
- [ ] 预期 `MAGIC=0x4D545330`、`VERSION=0x00030200`、L1 capability `0x4C310001` 已与当前 RTL/Host/bitstream 记录核对。
- [ ] PZT datasheet/驱动器允许输入范围、极性、阻抗和共地方案已确认；FPGA safe min/max 不超过它。
- [ ] IN1/IN2 电压在 Red Pitaya 输入允许范围内，无削顶。
- [ ] OUT2 当前只接示波器或已授权的 PZT/Scan input；绝不接 D2-125 Servo/Aux 输出或电流调制口。
- [ ] D2-125 Main Servo 继续连接激光电流快反馈；D2-125 AUX 与 PZT 物理断开，两个输出不并联。

## 4. 真实实验步骤（逐 Gate 执行）

以下是顺序，不是一次性授权。当前唯一下一动作仍是完成上面的修改后 Timing Gate；在其通过前不得烧录或接 PZT。

### H0：身份与 SAFE（OUT2 仅接示波器）

1. 用户手动烧录已通过 Gate 的 candidate。
2. 读取并记录 `MAGIC/VERSION/capability`；任何不一致立即停止。
3. 请求 SAFE，核对 `MODE=SAFE`、`ENABLE=0`、acquisition state SAFE 和 output readback。
4. 示波器使用明确的 DC coupling、probe ratio、输入阻抗/termination 与共同参考地，测量 OUT2 静态电压和 SAFE 往返瞬态。
5. 超范围、削顶、跳变或 readback 异常立即 SAFE，不进入 H1。

### H1：SCAN 与物理标定

1. 先在 scope-only 条件以用户批准的最小 scan range 验证 OUT2 center、amplitude、frequency、slew 和 polarity。
2. D2-125 AUX 从 PZT 物理断开后，才把 FPGA OUT2 接到专用 PZT/Scan input；D2-125 Main Servo 保持电流快环。
3. 在 loaded PZT 节点重复测量 OUT2；分别记录 GUI command counts、软件 estimate 和 scope measured voltage。
4. 连续采集至少 10 个周期，分别比较 rising/falling 的 PD、ERROR、command 与 scope crossing，量化迟滞和重复性。
5. 只有 IN1/IN2/OUT2 无削顶、范围安全、目标 crossing 可重复，才进入 H2。

### H2：ARM VALIDATE，不开启 P_LOCK

1. 在冻结的同一 frame 选择目标，记录 capture id、generation、方向、frame age、ERROR slope 和 OUT2 guard。
2. CONFIRM 后只执行 ARM VALIDATE。
3. 等待未来同方向 crossing；核对 event direction、event ERROR、event OUT2、generation 和 validate count。
4. VALIDATE 不得引起 OUT2 模式切换或物理跳变；不一致立即 SAFE。

### H3：ACTIVE，`Kp=0`

1. 用户确认 H2 后，以相同 target 执行 ACTIVE、`Kp=0`。
2. 验证 crossing 拍捕获的 lock bias 与事件 OUT2 一致，SCAN 到 P_LOCK 的 OUT2 在 scope 上无不可接受跳变。
3. 观察 saturation、fault、state 和 ERROR；任何异常立即 SAFE。

### H4：首次非零 P-only，`Kp=4`

1. 只在用户明确批准后，从 SAFE 重新按完整流程进入，并使用 `Kp=4`；不自动增加 Kp 或切 polarity。
2. 先观察短时收敛方向：ERROR 应朝目标减小，OUT2 不触及 correction/absolute limit，无持续振荡或发散。
3. 若方向错误、ERROR 增大、OUT2 饱和、PD/REF 异常或 scope 出现跳变，立即 SAFE并记录 frame/readback，不重试自动锁定。
4. 短时通过后再进行用户定义的 sustained-lock 观察，保存 aligned capture、scope 截图、参数、环境与失败原因。

## 5. PASS 定义

第一次真实 P-only 只能在以下证据同时成立时报告 `[USER HARDWARE VERIFIED]`：身份正确、SAFE/readback 一致、loaded PZT 节点范围安全、D2 AUX 确认断开、H2/H3 无跳变、非零 Kp 下 ERROR 明确收敛且 OUT2 不饱和，并在约定观察时间内保持锁定。代码存在、RTL simulation、正 WNS、bitstream 生成或 GUI 显示 LOCK 都不能单独替代该证据。
