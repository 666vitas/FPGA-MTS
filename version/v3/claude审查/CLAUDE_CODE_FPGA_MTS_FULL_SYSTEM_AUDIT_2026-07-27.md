
● 所有模块已读取完毕。现在撰写完整审查报告。

● 现在我已完成全部审查任务的信息收集，直接给出完整审查报告。

  ---
  FPGA-MTS 全系统独立审查报告

  审查模式：ANALYZE + VERIFY（只读，未修改任何文件）
  审查对象：E:\new\fpga_lock\v94，main@76cf453
  当前 Gate：LOCK-MVP-L1 — FPGA Real-Time ERROR-Crossing P-Only Lock
  报告日期：2026-07-27

  ---
  1. 执行摘要

  结论一：项目已经在 RTL 与 Host 分层上形成了合理的 P-only 闭环结构，但结构上还没有得到 timing 与硬件证据支持。

  结构成立的部分（[CODE INSPECTED]）：
  - 从 IN1/IN2 到 OUT2 的实时数据路径：mixer_core → lpf_core → laser_error → error_setpoint_corrector →
  simple_lock_acquisition → out2_lock_controller → selected_out2 → DAC B；
  - 实时 ERROR 零交叉检测、H/N 方向解耦、guard 窗口、Kp ramp、supervisor、event recorder；
  - Host 侧 LocalClient → LockService → CustomFpgaBackend → SSH → /dev/mem；
  - L1 capability CSR (0xE4 = 0x4C31_0001)、VERSION = 0x00030200、MAGIC = 0x4D545330。

  结论二：当前尚不能宣称"已实现锁频"。

  - Timing：官方 documented [AUTOMATED VERIFIED] 结果（STATUS.md 2026-07-26）称 WNS=+0.142 ns、TNS=0、setup failing =
  0；但仓库中最新可读的两份 timing summary（timing_for_codex/01_timing_summary.rpt, l1_impl_fail_2026-07-26/）分别为
  WNS=−0.387 ns（19 endpoints）与 iter1 WNS=−0.119 ns（4 endpoints），且 README 顶部仍显示 −0.387 ns / −5.015 ns / 19
  endpoints。文档、STATUS 和实际报告存在冲突。
  - 硬件：无任何 [USER HARDWARE VERIFIED]；bitstream 未烧录；未连接板卡。
  - 完整 Timing Gate 未过：check_timing 报告 19 unconstrained internal endpoints、17 no-input-delay、42 no-output-delay、52
  no-clock 项、TIMING-6/7 关于 par_clk↔pll_adc_clk 的两个 critical warning、TIMING-17 关于 i_hk/i_DNA/CLK non-clocked
  sequential cell。

  三大 P0 blocker

  1. Timing Gate 事实冲突且未完整通过：STATUS 声明 WNS=+0.142 ns，但 timing_for_codex/01_timing_summary.rpt 和 README 仍是
  setup fail。文档与仓库不一致，必须先由用户重新出报告并统一。
  2. 物理反馈方向未从硬件确认：polarity_suggestion 只由 ERROR-vs-OUT2 slope 推断，忽略 PZT/激光频率方向。RTL 与 Host
  都不知道"OUT2 变大 → 激光频率是升还是降"，任何一次首次 Kp≠0 都可能是正反馈发散。
  3. loaded PZT 电压校准缺失、CH4 语义未验证：CH4 是 selected_out2 数字信号（red_pitaya_top.sv:569），空载/带载/示波器
  load/probe 都不确定；out2_calibration 系数尚未在 loaded PZT 下核对。

  三大安全风险

  1. legacy CAPTURE_LOCK_POINT 与 APPLY P 手动路径仍活着（custom_register_bank.sv:534–544；main_window.py 多处仍连 APPLY P /
  LOCK HERE 按钮）。GUI 声称 hidden，但 code 层可达；触发它会绕过 supervisor、Kp ramp 与 config generation。
  2. _fail_safe 只 raise，不阻止后续调用（lock_service.py:144）。SAFE 写入失败时会被 finally 忽略，raise
  CustomFpgaBackendError(...) 由 Worker except Exception 吞掉；GUI 会看到 SAFE 状态但硬件不一定 SAFE。
  3. AcquisitionService.adopt_capture_id（acquisition_service.py:22–27）允许 Worker 直接把任意 capture_id 塞进短生命周期的
  service，而 connection_workers.py:139 每个 op 都新建 LockService/AcquisitionService。target capture_id
  校验是在新实例里进行的——它对旧 GUI capture 无任何真实关联，stale 检查形同虚设。

  ---
  2. 已确认事实（[CODE INSPECTED] / [RTL SIMULATED] / [UNIT TESTED]）

  - 信号语义：red_pitaya_top.sv:151–153, 229–240, 493–503, 630：USE_LASER_LOCK_CORE=1、LASER_LOCK_OUTPUT_MODE=3、OUT1=laser_er
  ror（mixer+LPF），OUT2=selected_out2；LASER_LOCK_CONTROL_PATH_MODE=1 只影响 laser_control 的候选 seq PI，当前不驱动
  OUT2；OUT2 由 out2_lock_controller.control_o 直接驱动。
  - mixer：mixer_core.sv:39–40：product = pd × ref（14×14=28 位），>>>13 后 saturate 到 14 位。REF 相位/幅度未在 FPGA
  中做任何调节。
  - LPF：lpf_core.sv:34–83：一阶 IIR，acc += (x<<LPF_SHIFT − acc)>>>LPF_SHIFT，LPF_SHIFT=12；DC 增益单位，等效 τ ≈ 2^12 /
  f_clk ≈ 33 μs（−3 dB ≈ 4.9 kHz）。这远慢于 4.6 MHz REF 的 2f 分量——理论上可以正确抑制。
  - ERROR pipeline：laser_lock_core.sv:196 输出 protected_error → error_o；顶层引出为
  laser_error。error_setpoint_corrector.sv:17–27 计算 lock_error = clip(error − setpoint)。
  - 控制方程（从 RTL 精确推导）：
  s1 = polarity ? -lock_error : +lock_error      // 15 bit
  s2 = s1 * kp_effective                          // 29 bit
  s3 = s2 >>> 8                                   // 32 bit
  s4 = clip(s3, ±min(|correction_limit|, 8191))   // correction
  s5 = clip(s4 + lock_bias, ±min(|lock_limit|, 8191))
  s6 = slew_limit(s5, control_o, out2_slew_limit) // per servo tick
  control_o = s6   （在 MODE=P_LOCK 且 s6_valid 时）
  - 详见 custom_register_bank.sv:1739–2049 的 out2_lock_controller（该模块虽名在 register bank 中但是独立模块）。
  - 6 级 pipeline latency = 8 clocks（STATUS.md），进入 P_LOCK 后 flush pipeline valid（out2_lock_controller.sv:1984–1995）。
  - SAFE / abort / fault 处理（out2_lock_controller L1997–2000）：control_o ← 0，servo_count 归零，pipeline enable 清零。
  - 状态机：simple_lock_acquisition.sv:77–84：SAFE(0) → SCAN(1) → VALIDATING(2) / ARMED(3) → ACQUIRING(4) → P_LOCKED(5) /
  FAILED(6) / FAULT(7)。转移条件严格：
    - ARM 请求经三级流水（capture → decide → accept/reject），配置只在 state==SCAN && enable && mode==SCAN 时进入
  pending，配置在 ARM 期间冻结（active_* 只在 arm_accepted_w 时更新，见 L423–465）。
    - runtime_fault_q（L637–645）：VALIDATING/ARMED 期间 saturated_i || !enable_i || mode≠SCAN 立即 FAULT；ACQUIRING/P_LOCKED
  期间 saturated_i || !enable_i || (mode≠P_LOCK && counter>2) FAULT。
    - crossing_event_q 是同一 crossing 拍捕获的 out2/error 的两拍延迟版本（L549–562），trigger 使用 crossing_out2_q /
  crossing_error_q；trigger 与 kp/supervisor start 同一拍。
  - crossing detector（realtime_error_crossing_detector.sv）：N 连续 source-side → N 连续 destination-side，pass_consumed
  防止同一 guard pass 内重复触发；clear_i 在离开 VALIDATING/ARMED 或 abort 时重置。
  - register bank atomicity（custom_register_bank.sv:483–500）：acq_trigger_o 触发时原子更新 lock_bias =
  trigger_out2_sample_w、error_setpoint =
  active_error_setpoint_w、correction_limit、lock_limit、ki=0、integral_reset=1、mode=P_LOCK、enable=1；D1 分支额外把
  kp=0；SIMPLE/L1 分支保留 kp_o 原值（因为 kp_effective_o 由 FPGA l1_kp_ramp 从 0 起爬，不需要 kp_o 归零）。
  - L1 servo 参数原子性（L557–565）：servo_update_div_o 与 out2_slew_limit_o 只在 arm_accepted_w 时从 servo_config_q
  快照，保证 acquisition 期间不被后续 bus 写扰动。
  - supervisor 判据（l1_lock_supervisor.sv）：256 样本窗口累加 lock_error（signed 24 bit）与 abs_error；observation_good 需要
  |sum| < mean_sum_limit && abs_sum < abs_sum_limit && kp_target_reached && !overflow；连续 confirm_windows 次 good →
  supervisor_lock；连续 divergence_windows 次 bad → supervisor_fail。
  - CSR：MAGIC=0x00, VERSION=0x01（值 0x00030200），L1_CAPABILITY=0x39（值 0x4C31_0001），CROSSING_CONFIG=0x3A ...
  SUPERVISOR_METRICS=0x44；ACQ_COMMAND W1P: ARM=1, ABORT=2, CLEAR_EVENT=4, VALIDATE=8；registered 命令 mailbox 保证 wen
  挂起时不会重发（L235–266）。
  - RTL simulation：[RTL SIMULATED] STATUS.md 声称 20 个 testbench 全部通过，其中 crossing 13/13, supervisor 5/5, kp_ramp 6/6,
  plant 8/8, out2 controller 54/54, SIMPLE 32/32, deterministic 50/50, D1 register bank 166/166, ramp
  25/25。注意仓库中我未运行仿真核对——这条只是"文档声明"。
  - Python unit tests：[UNIT TESTED] STATUS 声称 148 passed；tests/test_lock_services.py 覆盖 stale capture、L1
  preload、VALIDATE 独立、l1_capability 缺失→SAFE、ARM readback mismatch→FAILED（5 个测试全部对准 L1 路径）。

  ---
  3. 暂时无法确认的信息（[NEEDS USER CONFIRMATION]）

  - D2-125 当前实际连接（Servo Output / Aux Output / Ramp Output 各接到激光器何处）。
  - 激光器 PZT/scan 输入的电压范围、极性、带宽、迟滞、加载阻抗。
  - Red Pitaya OUT2 到底替代 D2-125 的哪一个输出。
  - 示波器 CH1/CH2/CH3/CH4 探头倍率、AC/DC coupling、50 Ω/Hi-Z。
  - PD 信号进入 IN1 之前的 BPF/放大器增益，REF 的实际幅度和相位。
  - loaded PZT 电压对 OUT2 counts 的实际系数。
  - 是否有过任何真实带激光的实验记录（docs/experiment_logs/ 存在但未审查）。

  ---
  4. 物理闭环图

  4A. 当前实验实际链路（推断）

  [Laser + Rb Cell + PBS + Photodetector]
          │ PD (baseband + 4.6 MHz DSB-SC MTS)
          ▼
  [Analog BPF? Preamp?]      ← 未在仓库中定义
          │
          ▼  IN1 (±1 V, signed14)
  ┌────────────────────────────────────────────┐
  │ Red Pitaya STEMlab 125-14                  │
  │                                            │
  │  IN1 ─┐                                    │
  │       ▼                                    │
  │    [mixer_core] ← IN2 (REF 4.6 MHz)        │
  │       │                                    │
  │    [lpf_core, τ≈33 μs]                     │
  │       │                                    │
  │       ├───► DAC A / OUT1  (laser_error)    │
  │       │                                    │
  │    [error_setpoint_corrector]              │
  │       │  lock_error                        │
  │    [simple_lock_acquisition]               │
  │       │                                    │
  │    [out2_lock_controller]                  │
  │       │  selected_out2                     │
  │       └───► DAC B / OUT2                   │
  └────────────────────────────────────────────┘
          │
          ▼  ??? (unknown)
  [D2-125 Servo Output → 激光器 PZT / 激光器电流]
          │
          └───► Laser frequency

  未确认：OUT2 现在到底进 PZT 还是电流 mod；D2-125 的三个输出目前担任什么。

  4B. 目标 P-only 闭环

  [激光] ← PZT ← OUT2 = clip(lock_bias + polarity·Kp·(error−setpoint)/2⁸, ±limit)
     │                     ▲
     ▼                     │
  [原子 Rb → PD → BPF → IN1]
                           │
                       [mixer × IN2(REF)]
                           │
                       [LPF]
                           │
                       [error]
                           │
                       [error − setpoint = lock_error]
                           │
                       [supervisor / crossing detector]
                           │
                      trigger → 更新 lock_bias & setpoint & Kp ramp

  安全边界（永久）：
  - OUT1 只到示波器；
  - OUT2 只到激光器专用 PZT/Scan 输入 + 示波器；
  - 禁止 OUT2 到电流调制或与其他有源输出并联；
  - IN1/IN2 幅度必须 ≤ ±1 V。

  4C. Host/FPGA 控制链

  GUI (main_window.py, 5335 行)
     │
     ▼ button.clicked → _start_custom_fpga_operation(op)
  CustomFpgaRegisterWorker(QThread)          ← 每次操作新建
     │  __init__ 内 new CustomFpgaBackend
     │  __init__ 内 new AcquisitionService
     │  __init__ 内 new LockService
     ▼
  LocalClient (thin wrapper)
     ▼
  LockService.request_lock(BasicLockRequest)
     ▼  build_acquisition_target_config
  CustomFpgaBackend.arm_lock_target / validate_lock_target
     ▼  ssh python3 -c "base64_helper_exec ..."
  Red Pitaya /dev/mem
     ▼
  FPGA custom_register_bank shadow regs → arm_command_q → simple_lock_acquisition

  ---
  5. 控制方程与反馈符号（从 RTL 精确推导）

  lock_error = clip( error - setpoint,  ±8191 )              // signed 14
               （error_setpoint_corrector.sv:17-27）

  s0..s6 (out2_lock_controller):
    polarity_signed = polarity ? -lock_error : +lock_error
    product = polarity_signed * kp_effective                  // 29 bit
    p_term  = product >>> 8                                   // 32 bit
    correction = clip(p_term, ±min(|lock_correction_limit|, 8191))
    raw = correction + lock_bias                              // 32 bit
    abs_limit_13 = clip(|lock_limit|, 8191)                   // (lock_limit==-8192 → 8191)
    target = clip(raw, ±abs_limit_13)                         // 14 bit
    saturated = correction_saturated OR |raw|>abs_limit

  Per servo tick (servo_update_div_i):
    delta = target - control_o
    slew  = max(out2_slew_limit_i, 1)
    next_control =
        target                         if |delta| ≤ slew
        control_o + slew               if delta > slew
        control_o − slew               if delta < −slew

  SAFE / abort / fault / mode≠P_LOCK → control_o ← 0, pipeline flush
  SCAN                                → control_o ← scan_i
  HOLD                                → control_o ← hold_value_i

  负反馈符号判据

  回路开环增益（在锁点附近的小信号）：
  G_loop = polarity_sign · Kp · slope_error_per_out2_at_target · slope_freq_per_out2 · slope_error_per_freq
  其中：
  - slope_error_per_out2_at_target：ERROR 曲线对 OUT2 的局部斜率（由 target selection 得到，符号可正可负）；
  - slope_freq_per_out2：激光器 PZT/电流方向决定的物理常数（未知）；
  - slope_error_per_freq：MTS discriminator 对激光频率变化的响应，符号由光路和 REF 相位共同决定。

  Host 的 polarity_suggestion 只根据 slope 符号（acquisition_service.py:75）：
  polarity_suggestion=1 if slope > 0 else 0
  这条推断只对 slope_freq_per_out2 · slope_error_per_freq > 0 的情况成立。如果 PZT
  极性、电流极性或光路方向使得该乘积为负，polarity 建议会给出正反馈的方向。

  ▎ 关键判断：本项目目前没有任何代码或 RTL 环节在做真实反馈方向的独立确认。首次上板 Kp≠0
  ▎ 之前，必须由用户在硬件上先做一次"±小电压扫描 → 观察 error 方向" 的极性核对。

  ---
  6. FPGA 功能审查

  模块: mixer_core
  关键行: 62 行
  结论: product = pd*ref, >>>13, saturate. REF 相位不可调——若光路造成 REF 相位偏差，只能通过 IN2 前的模拟移相器补偿。[CODE
  INSPECTED] OK。
  ────────────────────────────────────────
  模块: lpf_core
  关键行: 85 行
  结论: 单极 IIR，DC 增益 1，−3 dB 约 5 kHz。适合抑制 4.6 MHz × 2 = 9.2 MHz 分量。
  ────────────────────────────────────────
  模块: laser_lock_core
  关键行: 349 行
  结论: OUTPUT_MODE=3 时把 lpf_signal 送到 output_protect → error_o。CONTROL_PATH_MODE=1 生成 pi_controller_seq 到
  control_o（laser_control），但顶层 OUT2 不使用 laser_control（dac_b_sum_laser = selected_out2, top L630）。laser_control 是
   dead code 对 OUT2 而言，只是 latency 与资源被占用。
  ────────────────────────────────────────
  模块: error_setpoint_corrector
  关键行: 37 行
  结论: lock_error = clip(error−setpoint, ±8191)。语义 OK。
  ────────────────────────────────────────
  模块: ramp_generator
  关键行: 165 行
  结论: 双向三角波，amp/step/update_div 都有 sanitize（step≥1, amp≤8191, div≥1）。默认 offset=6962≈0.85 V，amp=410≈0.05
  V，div=1524。等效扫描周期 ≈ 2·2·amp·div/f_clk ≈ 2·2·410·1524/125e6 ≈ 20 ms → 50 Hz。enable=0 时 pos_q 复位到
  -amp，恢复扫描会从最低点开始，不是 bumpless。
  ────────────────────────────────────────
  模块: realtime_error_crossing_detector
  关键行: 117 行
  结论: H/N 独立、guard 内 pass_consumed、离开 guard 后重置。逻辑清晰。
  ────────────────────────────────────────
  模块: l1_kp_ramp
  关键行: 51 行
  结论: 每 servo_tick 每 ramp_div 步 +kp_step；到达 target 后 kp_target_reached。start 时 kp_effective 归零，stop
  时归零。只支持单调正 Kp（kp_next_w = kp + step 只加不减）。这也意味着 kp_target 必须 ≥ 0，Host 的
  build_acquisition_target_config L340 要求 kp∈{0,4} 匹配。
  ────────────────────────────────────────
  模块: l1_lock_supervisor
  关键行: 209 行
  结论: 256-sample windows；mean_sum_limit = error_mean_limit<<8，abs_sum_limit = error_abs_limit<<8，divergence_sum_limit =
  error_abs_limit<<10。observation_good 要求 kp_target_reached——即 Kp 未到 target 之前不能判 P_LOCKED（good
  计数被强制清零）。
  ────────────────────────────────────────
  模块: l1_event_recorder
  关键行: 82 行
  结论: 单事件寄存器，request_i 时快照；clear_i 清 valid。sequence 自增作为幂等标记。
  ────────────────────────────────────────
  模块: simple_lock_acquisition
  关键行: 889 行
  结论: 顶层集成。ARM 三级流水；pending → active 只经过 arm_accepted_w 一拍；hold_o 在 ARMED 阶段 crossing
  candidate/event/trigger 时置位（用于告诉 controller 别再输出 scan），在 ACQUIRING 时 mode==SCAN 也置位；trigger 拍捕获
  crossing_out2_q 作为真实实时 OUT2；trigger 同时启动 kp_ramp 和 supervisor。
  ────────────────────────────────────────
  模块: out2_lock_controller
  关键行: 311 行
  结论: 见第 5 节。SAFE bumpless（jump to 0）并不是模拟 bumpless——control_o=0 是 0 counts，即 DAC 中值电压 (≈0 V)。SAFE 会造成

  OUT2 从 lock_bias 突降到 0，产生激光 PZT 的电压跳变。此为危险行为：任何 fault 触发 SAFE，都会直接把 PZT 拉到 0 V。

  F0 P0 发现：out2_lock_controller SAFE 时 control_o ← 0 而非"maintain last value" 或 "ramp to
  lock_bias"（L1998）。这对激光器专用 PZT 是硬跳变。可能引起 mode hop 或机械冲击。

  ---
  7. Host / FPGA 交互审查

  调用链

  main_window → _start_custom_fpga_operation(op) → CustomFpgaRegisterWorker → 每次 run() 内 backend = CustomFpgaBackend(...),
  acquisition_service = AcquisitionService(backend), local_client = LocalClient(LockService(backend, acquisition_service)) →
  backend._run(op, config) → RedPitayaSshClient.run("python3 -c ...") → remote helper → mmap /dev/mem。

  关键问题

  H1 (P0)：LockService 无持久性。每个 GUI 按钮点击都新建一个 LockService，其 self.state 初始为
  SAFE，self.target=None。这意味着：
  - 在同一次 P_LOCK 过程中，用户点 "STATUS"、"CAPTURE"、"APPLY P" 各来自新的 LockService，Host
  侧状态机形同虚设，实际状态完全依赖 FPGA readback。
  - service.state = LockState.ARMED 之类的赋值只影响一次 Worker 生命周期，不留在下一 Worker 里。
  - LockTarget 唯一持久性载体是 GUI 的 params dict + AcquisitionService.adopt_capture_id。这条链是唯一 anti-stale 屏障。

  H2 (P0)：AcquisitionService.adopt_capture_id(int) 接受任何正数（acquisition_service.py:22-27）。GUI 侧 params["capture_id"]
  只是 GUI 计数器（main_window 里的一个内部 int），FPGA 并不返回 capture_id——"stale capture" 检查检的是 GUI
  自己的计数器，而不是 FPGA 曾经完成的哪一次 capture。等价于：assert my_number == my_number。测试
  test_stale_capture_is_rejected_before_arm 只是验证 GUI 传错自己的 capture_id 会被拒，不是验证 FPGA capture ID 一致。

  H3 (P0)：`legacy CAPTURE_LOCK_POINT / APPLY P / LOCK HERE 仍活着**。
  - custom_register_bank.sv:534-544：写 REG_CAPTURE_LOCK_POINT 会直接把 error_setpoint←error_monitor_i,
  lock_bias←out2_monitor_i, kp=0, mode=P_LOCK, enable=1。这条路径完全绕过 supervisor/kp_ramp/arm 三级流水。
  - custom_register_bank.sv:527-533, 519：直接写 REG_KP、REG_LOCK_BIAS、REG_LOCK_LIMIT、REG_ERROR_SETPOINT、REG_KI 也不受
  acquisition 保护。
  - Host 侧 custom_fpga_backend.update_p_lock (L1050) 是显式为 legacy APPLY P 保留的入口，LockService.apply_p (L134) 直接调用
  backend，不检查 acquisition_state。
  - GUI main_window.py 上的 APPLY P 按钮虽然默认隐藏 (setVisible(False) at L2112)，但事件绑定和后端支持完好；只需 patch
  一行即可暴露。

  H4 (P1)：_fail_safe 在 LockService 里（L144–149）执行 self._backend.set_mode_safe()；如果 SSH 抛异常，会跳到 finally:
  self.state = LockState.FAILED，然后 raise CustomFpgaBackendError。Worker 的 except Exception 只报 str(exc) 到 GUI
  状态栏，不再区分 "SAFE 已完成" vs "SAFE 请求失败"。硬件可能仍在 P_LOCK。

  H5 (P1)：arm_lock_target 的 readback 检查（lock_service.py:117-123）要求 acquisition_state ∈ {3,4,5} 和 mode==3 &&
  enable==1。RTL 的 state_readback_o[2:0] 用 3-bit 编码 SAFE=0..FAULT=7 与 Host 期望的十进制值一致。但 Host 未验
  active_config_valid, active_generation, event_config_generation 等其他 payload 字段——一致性不完整。

  H6 (P2)：Register bank 允许在任何时候写 shadow regs（L579–612），只有 SIMPLE 分支在 arm_capture_pending_q 时快照到
  pending_*。因此在 SCAN 状态下多次快速 ARM，只要 window 命中，可以持续替换 pending config——config_generation_shadow_q 是 Host
  侧责任，FPGA 不做单调检查。

  ---
  8. 文档 — 代码 — 测试 — 硬件不一致矩阵

  #: 1
  声明位置: README.md L24–29
  声明内容: WNS=−0.387, TNS=−5.015, setup fail=19
  实际证据: timing_for_codex/01_timing_summary.rpt L273 相符
  结论: README 与旧 timing 一致
  ────────────────────────────────────────
  #: 2
  声明位置: STATUS.md L52–56
  声明内容: WNS=+0.142, TNS=0, setup fail=0
  实际证据: 仓库中无 WNS=+0.142 的报告文件；grep 只在 STATUS 本身出现
  结论: 文档 vs 报告冲突（P0）
  ────────────────────────────────────────
  #: 3
  声明位置: CURRENT_REVIEW_MANIFEST.md L2
  声明内容: Effective-Gate: LOCK-MVP-T0
  实际证据: CURRENT_GATE.md L2 = LOCK-MVP-L1；AGENTS L4 = 2026-07-24
  结论: Manifest 落后于 CURRENT_GATE（P1）
  ────────────────────────────────────────
  #: 4
  声明位置: Manifest L27–37
  声明内容: 当前范围只含 3 个 tb 和 red_pitaya_top/custom_register_bank/ramp_generator
  实际证据: 实际 RTL 已增加
  simple_lock_acquisition/realtime_error_crossing_detector/l1_kp_ramp/l1_lock_supervisor/l1_event_recorder，10 个 L1 相关 tb
  结论: Manifest 未跟上 L1 增量
  ────────────────────────────────────────
  #: 5
  声明位置: SPEC L960–997 (L1 note)
  声明内容: ARM_VALIDATE / ACTIVE / kp_effective 是 L1 正规路径
  实际证据: RTL 与 Host 已实现
  结论: 一致
  ────────────────────────────────────────
  #: 6
  声明位置: SPEC L534–544 (CAPTURE_LOCK_POINT 描述)
  声明内容: 已列为 diagnostic-only
  实际证据: RTL L534–544 仍是权限最高的一条路径（直接 mode=P_LOCK, enable=1, bypass 一切）
  结论: SPEC 声称已废弃，RTL 未废弃（P0）
  ────────────────────────────────────────
  #: 7
  声明位置: AGENTS L15
  声明内容: VERSION 需从当前 RTL/host/bitstream 核对，不写死
  实际证据: RTL L59–61 用 localparam 硬编码；Host common/lock_models.py:84 也硬编码 0x00030200；文档 AGENTS 也提到这个值
  结论: 三处一致（OK），但不是文档所说的"不写死"
  ────────────────────────────────────────
  #: 8
  声明位置: AGENTS L142
  声明内容: [USER HARDWARE VERIFIED] 需要用户真实接线通过
  实际证据: 任何硬件证据都没有
  结论: 未违规，但当前项目没有此类证据
  ────────────────────────────────────────
  #: 9
  声明位置: CURRENT_GATE L26
  声明内容: [NOT VERIFIED] timing、bitstream、板卡、真实锁定
  实际证据: 与 README/timing_for_codex 一致
  结论: OK
  ────────────────────────────────────────
  #: 10
  声明位置: main_window docstring L5182
  声明内容: 用户路径是 "Capture Waveform → click target → LOCK HERE → APPLY P"
  实际证据: L1 spec 说 legacy
  结论: GUI 文案仍然是 legacy L0 流程（P1）

  ---
  9. 风险清单

  P0

  P0-1 · Timing Gate 数据自相矛盾
  - 证据：README L24-29 = fail；timing_for_codex/01_timing_summary.rpt L273 = fail；STATUS.md L52-56 = pass；未找到 pass
  报告的实际文件。
  - 影响：无法判断当前 bitstream 是否 timing-clean，进而无法评估上板风险。
  - 触发：一旦按 STATUS 相信 timing 已 pass 就烧板。
  - 当前发生：是（文档层面）。
  - 最小修复：用户重新运行一次 clean synth+impl，把新的 01_timing_summary.rpt 覆盖到 timing_for_codex/，同步 README 和
  STATUS。
  - 验证：grep -R "0.142" v0.94/timing_for_codex/ 或运行 report_timing_summary。

  P0-2 · 反馈符号未在硬件确认
  - 证据：acquisition_service.py:75 只从 ERROR/OUT2 slope 推 polarity；RTL polarity_i 直接 XOR 到 -lock_error。
  - 影响：首次 Kp≠0 可能是正反馈发散，PZT 撞限、mode hop、镜面损伤或原子锁失锁。
  - 触发：任何 kp=4 首次 ARM ACTIVE。
  - 当前发生：结构上确定，硬件上尚未发生（未上板）。
  - 最小修复：Kp=4 之前必须先在 HOLD 下人工小步移 OUT2 观察 error 方向，或先运行 Kp=0（不产生反馈）确认 error 极性对齐；再决定
  polarity bit。
  - 验证：一次 Kp=0 + PZT ±20 counts 手动激励 + 示波器观察 error mean 变化。

  P0-3 · SAFE 硬跳变
  - 证据：out2_lock_controller L1997-2000：SAFE / abort / fault → control_o<=0。
  - 影响：任何 fault（saturation、timeout、divergence、SSH 中断、mode 变化）都会把 OUT2 从 lock_bias 瞬间拉到 0 V (数字 0
  counts = DAC 中值)。这不是"maintain last output"，是一次数字跳变可到 ±全量程/2。
  - 触发：saturated=1、user 手工写 mode=SAFE、fault_immediate=1、通信中断（remote helper 早退让 mode 变）。
  - 当前发生：一旦上板任何 fault 都会重现。
  - 最小修复方向：把 SAFE/abort/fault 出口改为"进入 SAFE ramp"（例如按 slew_limit 缓慢拉回 0 或 hold_value_i）；至少允许
  config 一个 SAFE_TARGET 值。
  - 本轮 ANALYZE：不动 RTL；用户需在 SOP 中要求 SAFE 前先 UNLOCK 到 HOLD，再 SAFE。

  P0-4 · legacy CAPTURE_LOCK_POINT / 直写 CSR 仍是权限最高路径
  - 证据：custom_register_bank.sv:534-544、L519-533、update_p_lock。
  - 影响：任何一次写 REG_KP (=0x0C) 或 REG_CAPTURE_LOCK_POINT (=0x17) 都可以在 P_LOCK 中改变 Kp、bias 或直接强制 lock，不经过
  supervisor、Kp ramp、config generation。
  - 触发：GUI 意外触发（旧按钮）、用户手工 monitor 工具 mmap、脚本调用。
  - 当前发生：功能存在，未观察到误用。
  - 最小修复方向：在 L1 build 中禁用这几个 write 分支，或让它们在 mode≠SAFE 时被 acquisition mailbox 拒绝。
  - 本轮 ANALYZE：确认 SPEC 已宣称 diagnostic-only 但 RTL 未清理。

  P0-5 · LockService 无状态持久性 / capture_id 校验形同虚设
  - 证据：connection_workers.py:132-139 每 op 新建 LockService；AcquisitionService.adopt_capture_id 接受任意正数。
  - 影响：Host 侧状态机不是唯一真理来源；stale capture 只能识别 Python 计数器一致性，不能识别"这次 target 是从哪次 FPGA
  capture 得出"。
  - 触发：GUI 快速点击、多个 Worker 并发、旧 waveform 上点选后 SCAN 参数改变。
  - 当前发生：结构问题存在，日常操作会造成。
  - 最小修复方向：把 LockService 提升为 main_window 单例，Worker 共享；capture_id 由 FPGA 提供（例如把 capture_start_o 的
  pulse 计数放进一个 CSR），Host 验 FPGA capture_id。
  - 本轮 ANALYZE：仅记录。

  P1

  P1-1 · Manifest 与 CURRENT_GATE 不同步：Effective-Gate: LOCK-MVP-T0 vs LOCK-MVP-L1。冲突优先级下 CURRENT_GATE
  胜出，但强制读取集合可能漏掉 L1 相关模块。

  P1-2 · 完整 Timing Gate 未过：check_timing 19 unconstrained internal endpoints (i_daisy/txp_dat_reg[*],
  i_hk/i_DNA/READ/SHIFT)、17 no-input-delay ports、42 no-output-delay ports、52 no-clock 项、TIMING-6/7 关于
  par_clk↔pll_adc_clk（unsafe timed）、TIMING-17 non-clocked sequential (i_hk/i_DNA/CLK)。这些都来自官方 Red Pitaya 基座
  (daisy, hk)，不是本项目实时锁定路径，但 Gate 声称需要 unconstrained=0，冲突。

  P1-3 · GUI 文案仍是 legacy 流程：main_window.py:5182"Capture Waveform → click target → LOCK HERE → APPLY P". 与 L1 spec
  冲突。

  P1-4 · laser_control dead path 占用资源：red_pitaya_top 实例化 laser_lock_core 且 CONTROL_PATH_MODE=1, 生成
  pi_controller_seq，但顶层 dac_b_sum_laser 使用 selected_out2 而非 laser_control。占用 1 个 DSP、少量 LUT/FF，同时给 timing
  报告增加干扰路径。

  P1-5 · polarity 与 lock_kp_effective 不进 pipeline flush 集合：polarity_o 由 custom_register_bank 顶层 bus.wen
  直写（L640），不经过 acquisition mailbox。P_LOCK 期间 host 若写 POLARITY 会立即翻转 polarity_i，然后 6 拍后到
  s1，控制方向瞬间反相。

  P1-6 · save.state 与实际 readback 可能分叉：LockService.state 在 request_lock 后按 acq_state 赋值，但下次 Worker 又初始化为
  SAFE。GUI 显示状态和实际不一致。

  P1-7 · crossing_hysteresis / crossing_samples 默认值极小：Host 默认 hysteresis=4 counts、samples=3。若 lock_error
  噪声大，H/N 判据可能被单个 spike 误触。

  P1-8 · Kp ramp 单调递增，不能应对越锁越大：l1_kp_ramp 只加不减；supervisor 观测的 divergence 只能触发 fail，不能回退。

  P1-9 · SAFE mode 与 enable=0 都会 flush pipeline valid：out2_lock_controller L1984。若 acquisition 期间 GUI 意外把 enable 写
  0，pipeline valid 立即清，控制器进入 servo_count=0 分支 → 使用 lock_bias_i 作 control_o（L2035）。跳变量 = correction
  部分被扔掉。

  P2

  P2-1 deterministic (D1) 源码 & tb 保留但不构建，代码维护成本。
  P2-2 README 中 timing 数值需要人工维护，容易漂移。
  P2-3 history/v1-v5 目录仍然存在，若 grep 无过滤会污染搜索。

  ---
  10. 当前系统真实能力边界

  ┌────────────────┬──────────────────────────────────────────────────────────────────────────────────────────────────────┐
  │      类别      │                                                 状态                                                 │
  ├────────────────┼──────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ 代码已实现     │ ✅ RTL SIMPLE/L1 完整，Host L1 workflow 完整                                                         │
  ├────────────────┼──────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ RTL 已仿真     │ ✅ (依 STATUS 声明；本轮未运行)                                                                      │
  ├────────────────┼──────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ 软件已单元测试 │ ✅ (依 STATUS 声明；本轮未运行)                                                                      │
  ├────────────────┼──────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ Timing 已通过  │ ⚠️ 声明冲突：STATUS 说通过、README/仓库 timing 报告说未通过；unconstrained/no-input/no-output 都未清 │
  ├────────────────┼──────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ 硬件已观察     │ ❌ 无                                                                                                │
  ├────────────────┼──────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ 闭环已验证     │ ❌ 无                                                                                                │
  ├────────────────┼──────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ 长期稳频已验证 │ ❌ 无                                                                                                │
  └────────────────┴──────────────────────────────────────────────────────────────────────────────────────────────────────┘

  结论：当前能力等价于"已完成一次完整 P-only 系统设计并通过 RTL 行为仿真与 Host
  单元测试"，尚未证明能上板、不能证明能锁频、不能证明反馈方向正确。

  ---
  11. 最小修复路线（不动 RTL 的部分）

  必须先修（在任何硬件动作之前）：
  1. 统一 timing 事实：让 STATUS/README/timing_for_codex/ 三处一致。要求用户重新出一份 clean routed 报告并把它作为
  authoritative。
  2. 决定当前 check_timing 的 unconstrained/no-input/no-output 项如何处理：给每一项写出分类（官方 IP / 未使用 / 需要
  exception）。不允许 blanket false path。
  3. Manifest 更新到 Effective-Gate: LOCK-MVP-L1 并列出 L1 tb/RTL。
  4. 在 SOP 中明确禁止在正常 GUI 流程中触发 CAPTURE_LOCK_POINT/APPLY P/直写 REG_KP。（RTL 清理放在下一 Gate）
  5. 更新 GUI 文案与 tooltip，与 L1 spec 一致。

  上板前修：
  6. Host 侧提升 LockService 为 main_window 单例；capture_id 使用 FPGA 侧序列号（可以先复用 event_sequence_o）。
  7. 决定 SAFE 出口的物理策略：至少在 SOP 中要求"先 abort → 观察 event_recorder → 再 SAFE"，最好把 controller SAFE 出口从 <=0
  改为 slew to hold_value_i（下一次授权修改 RTL 时）。
  8. 极性核对 SOP：Kp=4 前必须先 Kp=0 静态注入 ±小 OUT2 counts，示波器观察 error 方向，确认 polarity。

  第一次 P-only 之后再修：
  9. RTL 清理 CAPTURE_LOCK_POINT 与直写路径（REG_KP/REG_LOCK_BIAS/REG_ERROR_SETPOINT 只在 SCAN/SAFE 生效）。
  10. polarity_o 走 acquisition mailbox，P_LOCK 期间禁写。
  11. laser_control dead branch 从 top 删除（下一 build）。
  12. Kp ramp 支持下调（应对 divergence 缓解）。

  暂时冻结：PI/Ki、自动重锁、AI、双执行器、Linien robust acquisition。

  ---
  12. 唯一下一动作

  在不修改 RTL、不生成 bitstream、不连接板卡的前提下：

  ▎ 让用户在 Vivado 中执行一次 clean synth_1 → impl_1 → route_design → report_timing_summary -report_unconstrained
  ▎ -check_timing_verbose，把新的 01_timing_summary.rpt 和 06_check_timing.rpt 覆盖到
  ▎ E:\new\fpga_lock\v94\v0.94\timing_for_codex\，同时贴出：
  ▎
  ▎ 1. WNS / TNS / setup failing endpoints
  ▎ 2. WHS / THS / hold failing endpoints
  ▎ 3. no_clock / unconstrained_internal_endpoints / no_input_delay / no_output_delay 各自数量
  ▎ 4. report_methodology 中的 TIMING-6/7/17 是否仍存在
  ▎
  ▎ 在这一步得到之前，任何"锁频推进"都是危险的，因为 STATUS 声明与仓库报告不一致意味着我们此刻甚至不确定当前 RTL
  ▎ 是否真的能收敛。

  得到新的 timing 报告后，我可以：
  - 帮你把每一个 check_timing 项按 A/B/C/D/E/F 分类；
  - 帮你把 STATUS/README/Manifest/CURRENT_GATE 四份文档统一到同一份 timing fact；
  - 再决定是否进入硬件 Gate H0（身份 + SAFE readback 检验）。