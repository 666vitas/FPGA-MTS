# Linien 代码阅读与适用性

## 1. 项目身份

- `[CONFIRMED]` 定位：Red Pitaya STEMlab 125-14 上的 spectroscopy/laser
  lock 应用，Python + Migen，源自 redpid。
  证据：`linien/linien-master/README.md:5-13`。
- `[CONFIRMED]` 本地 package 版本：`linien-server 2.1.0`。
  证据：`linien/linien-master/linien-server/pyproject.toml:5-32`。
- `[NOT VERIFIED]` commit：本地是解压快照，没有 `.git`，无法证明 commit。
- `[CONFIRMED]` license：GPL-3.0-or-later。
  证据：`linien/linien-master/README.md:492-507` 与根 `LICENSE`。

主要目录：

```text
linien-master/
├─ gateware/logic/               FPGA/Migen autolock, PID, sweep
├─ linien-server/linien_server/  server, acquisition, registers, autolock
├─ linien-client/                RPC client
├─ linien-gui/                   Qt GUI
├─ linien-common/                parameters/common algorithms
└─ tests/                        PID, sweep, simple/robust autolock tests
```

## 2. GUI / server / FPGA 职责

| 层 | 实际职责 | 证据 |
|---|---|---|
| GUI/client | 选择一段 line、显示 sweep/lock、发参数和命令 | `README.md:183-208,322-403` |
| server | 记录 reference spectrum、计算 line point/correlation、选择 simple/robust、写参数和 CSR | `linien_server/autolock/autolock.py:36-133,144-247` |
| FPGA | sweep、PID、simple sweep-position trigger、robust peak-instruction matching、hold sweep、fast/slow outputs | `gateware/logic/autolock.py:27-68,71-112,115-223`; `gateware/linien_module.py:94-106,292-341` |
| acquisition service | 在板端持续取 scope、等待 gateware `lock_running`、切换 unlocked/locked signal naming | `linien_server/acquisition.py:40-104,143-186` |

这与 FPGA-MTS 的目标分层在原则上相似：GUI 不参与逐样本控制，server
拥有工作流，FPGA 决定实时切换。

## 3. autolock 实际流程

### 3.1 目标选择

用户不是只点一个零交叉，而是拖选包含目标 line 两个 extrema 的区间。
`Autolock.record_first_error_signal()` 调用 `get_lock_point()` 得到 mean、
目标 slope、line width、peak indices，并可把 line 中心移到 zero：
`linien_server/autolock/autolock.py:221-247`。

因此答案是：

- `[CONFIRMED]` Linien 的 target identity 首先来自谱线形状/峰对，不是单独
  ERROR 零交叉。
- `[CONFIRMED]` simple 模式随后用整段 reference 与新 spectrum 的
  correlation 求 shift：`linien_server/autolock/simple.py:29-78`。
- `[CONFIRMED]` robust 模式用多帧生成一组带 sign、threshold、minimum
  separation 的 peak instructions：`robust.py:175-253`。

### 3.2 simple autolock

调用关系：

```text
Autolock.handle_new_spectrum
-> SimpleAutolock.handle_new_spectrum
-> determine_shift_by_correlation
-> autolock_target_position CSR
-> exposed_start_lock
-> FPGA SimpleAutolock waits sweep_value in target window and sweep_up
-> lock_running=1
```

精确证据：

- CPU correlation 与 target count：`simple.py:50-76`。
- FPGA target window 约为 `target +/- sweep_step/2`，且只接受 sweep up：
  `gateware/logic/autolock.py:71-112`。

它不是 host/Linux 在目标点轮询写锁，而是 CPU 先估计 target、FPGA 再在
实时 sweep position 命中时打开 lock。不过它的 target 仍是 sweep position，
没有 FPGA-MTS L1 的独立 raw ERROR H/N crossing 条件。

### 3.3 robust autolock

服务器收集通常 5 条 correlated spectra，计算 jitter-tolerant description，
写入 FPGA，并以 `request_lock` 启动：
`robust.py:50-133`。FPGA 对实时 scope samples 做 delayed sum difference，
依次匹配 sign/height/time separation，全部指令满足并等待 final delay 后
`turn_on_lock`：`gateware/logic/autolock.py:115-223`。

`README.md:196-203` 对 simple/robust 的描述与实现一致：

- simple：CPU correlation + FPGA position trigger；
- robust：FPGA peak-shape instruction matching，抗通信抖动。

## 4. scan-to-lock 与 bumpless

`linien_module.py:94-106` 同时把 `autolock.lock_running` 接到：

```text
pid.running = lock_running
sweep.hold  = lock_running
```

fast output 是 PID、modulation、sweep、offset、slow output 的和：
`linien_module.py:313-342`。因此：

- `[CONFIRMED]` trigger 时 sweep 被 hold，基线 sweep value 保留；
- `[CONFIRMED]` PID 与 sweep 是相加，不是捕获实际 DAC 为一个独立
  `lock_bias` 寄存器；
- `[INFERENCE]` 当 P=I=D=0 时有等价的基线连续性；
- `[INFERENCE]` 非零 P 在 enable 首拍即可产生 correction，代码没有
  FPGA-MTS 那种“actual OUT2 同拍 capture + Kp soft-start + slew limit”
  的同构机制；
- `[NOT VERIFIED]` Linien 自身真实模拟 OUT2 是否无突跳，不能从这些
  Migen 连接单独证明。

## 5. PID enable、lock confirmation 与 loss-of-lock

- PID 参数在 `lock` 变化时写入，slope 决定 fast PID sign：
  `linien_server/registers.py:353-384`。
- acquisition service 区分“lock requested”与 FPGA `lock_running`：
  `linien_server/acquisition.py:56-63,98-104`。
- 本地 2.1.0 `Autolock.after_lock()` 只把 `autolock_locked=True` 并停止监听：
  `linien_server/autolock/autolock.py:249-256`。
- README 明确 lock detection 与 automatic relocking 在当前版本 temporarily
  disabled：`README.md:26-27`。

所以不能把 Linien 2.1.0 写成当前具有完整持续 lock supervisor/relock。

## 6. 双执行器

Linien 的 fast output 与 slow integrator 都由同一个 FPGA 控制：

- slow PID `running` 同样由 `lock_running` 驱动：
  `gateware/linien_module.py:304-311`；
- fast output 可叠加 slow chain：`linien_module.py:313-341`；
- README 称 slow integrator 用于 ECDL piezo：`README.md:34-35`。

`[CONFIRMED]` 这是“同一 FPGA 知道两执行器状态”的架构。它不适用于一个
不可读、不可 reset、不可 hold 的外部 D2-125 current controller。

`[DANGEROUS UNDER CURRENT HYBRID LOOP]` 若直接把 Linien slow/fast
双执行器概念套到 “D2-125 current + FPGA PZT”，控制器 ownership、
积分器 reset、setpoint 与 saturation 协调全部缺失，可能形成两个 DC
控制器争夺零点。

## 7. 适用性清单

| 功能 | 源文件 / symbol | 分类 | 对 FPGA-MTS 的结论 | 阶段 |
|---|---|---|---|---|
| GUI client / board server / FPGA 分层 | `README.md:18-23,155`; `AcquisitionService` | CONCEPTUALLY REUSABLE | 与目标 `LockService/RegisterMapper/AcquisitionService` 边界一致，不复制 RPyC/pyrp3 | 当前设计原则 |
| line extrema selection + `get_lock_point` | `autolock.py:221-247` | CONCEPTUALLY REUSABLE | 可作为未来谱线身份，不替代当前 PD feature + ERROR crossing | FUTURE ONLY |
| simple correlation | `simple.py:29-78` | CONCEPTUALLY REUSABLE | 可用于跨周期验证同一谱线；当前 L1 已有更确定的 ERROR crossing trigger | H4 后 |
| FPGA target-position trigger | `gateware/logic/autolock.py:71-112` | NOT APPLICABLE NOW | 当前已有 direction+guard+ERROR crossing，功能更严格，不应倒退 | 不引入 |
| robust peak instructions | `robust.py:175-281`; FPGA `RobustAutolock` | REQUIRES ARCHITECTURE CHANGE | 需 Migen gateware、scope semantics 与 CSR 重构；对首个 P-only 过度复杂 | FUTURE ONLY |
| sweep hold + PID enable 同源 | `linien_module.py:94-106` | CONCEPTUALLY REUSABLE | 说明 trigger/hold/servo 必须同一 FPGA event；当前 L1 已实现 actual bias capture | 已吸收 |
| slow integrator | `linien_module.py:304-341` | DANGEROUS UNDER CURRENT HYBRID LOOP | 假定同一 FPGA 控制 fast/slow；外部 D2-125 不满足 | 禁止当前引入 |
| current 2.1.0 relock | README | NOT APPLICABLE NOW | 当前版本本身 temporarily disabled；FPGA-MTS H4 前也禁止 | 不引入 |

## 8. 对九个重点问题的直接回答

1. autolock 不是纯零交叉触发；simple 用 spectrum correlation 定位，
   robust 用多峰形状/顺序指令。
2. server 做目标抽取、correlation、算法选择与 robust 指令生成；FPGA 做
   sweep position/peak instruction 实时命中、hold 与 PID enable。
3. FPGA `lock_running` 同拍 hold sweep 并 enable PID。
4. 有“hold sweep baseline”这一等价连续性思想，但不是 FPGA-MTS 的
   actual OUT2 capture/Kp ramp/slew 完整 bumpless 合同。
5. robust autolock 不适合首个 P-only Gate。
6. Linien 双执行器不能直接用于外部 D2-125。
7. 可借鉴职责边界、reference validation、同一 FPGA event；不能直接移植
   Migen CSR、scope layout、完整 gateware 或 server。
8. 是，Linien 的 fast/slow 执行器状态由同一 FPGA/parameter system 拥有。
9. 当 D2-125 仍闭环且不可观测时，Linien 的 ownership 与 anti-windup
   假设失效。

## 9. 最终结论

Linien 最有价值的是架构和 acquisition 思想，而不是代码搬运。FPGA-MTS
当前 L1 已具备比 Linien simple target-position trigger 更明确的
direction+guard+ERROR crossing 和 actual-bias capture。当前不引入 robust、
relock、slow integrator 或完整 server；先解决真实 D2-125 状态与 P-only
硬件 Gate。

