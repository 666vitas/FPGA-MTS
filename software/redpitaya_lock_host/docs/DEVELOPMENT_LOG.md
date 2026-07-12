# 开发日志

## 2026-07-12 - 修复 Custom FPGA Scope 曲线不显示：四通道合并为单窗口

- 本次问题：新 bitstream (`VERSION=0x00030001`) 烧录后，`Capture Waveform` 返回真实 points，统计量非零（IN1/PD, IN2/REF, OUT1/laser_error, OUT2/selected_out2 的 Vpp > 0），但右侧四个独立 `ChannelPanel` plot 黑框里没有显示曲线。
- 根因定位：四个独立 `WaveformPlot`（GraphicsLayoutWidget）通过 2×2 QGridLayout 排布，每个 plot 内嵌 placeholder、curve、marker、axis 多条 item，`ChannelPanel.apply_display_range()` 与 `_update_custom_scope_visibility()` 的交互可能导致 curve setVisible 状态与 plot 渲染不同步；同时四个大窗口占用空间太大、界面显示不完整。
- 修复方式：把四个独立大窗口收敛为一个紧凑的 `Custom FPGA Scope` 单窗口，使用单个 `pg.PlotWidget`，四条曲线（CH1/CH2/CH3/CH4）在同一 plot 叠加显示。
- 修改文件：`main_window.py`（`_build_plots`, `_render_custom_capture_payload`, `_on_custom_scope_clicked`, `_update_custom_scope_visibility`, `_fit_custom_scope_ranges`, `_clear_candidate_markers`, `_find_and_render_basic_candidates`, `_capture_payload_hazard`, `_show_custom_waveform_capture_plan`, `_apply_capture_view_mode`，新增 `_reset_custom_scope_view`）、`tests/test_custom_fpga_backend.py`（更新 5 个旧测试，新增 7 个测试）、`docs/DEVELOPMENT_LOG.md`、`../../version/STATUS.md`。
- 本轮只改上位机，不改 RTL / testbench / Vivado project / bitstream；不运行 Vivado，不需重新 bitstream，不需重新烧录。
- 单窗口布局：
  - 顶部：紧凑统计摘要（四通道 Vpp/min/max/mean + MODE + OUT2 + LOCK_BIAS + correction_limit）
  - 中间：一个 `pg.PlotWidget`，四条 pyqtgraph PlotDataItem 曲线叠加
  - 下方：紧凑 checkbox 行（`Show CH1/PD`、`Show CH3/laser_error`、`Show CH4/selected_out2`、`Show CH2/REF`）+ `Auto Range` + `Reset View`
  - 默认显示 CH1/CH3/CH4；CH2（4.6 MHz REF）默认隐藏
- curve 显示确保：
  - capture points 非空时 `custom_scope_data` 包含 ch1/ch2/ch3/ch4/time_s
  - 每条曲线 `setData(t, data[key])` 后调用 `setVisible(True)`，placeholder hide
  - 渲染后校验 xData 长度 > 0，否则在 warning_text 提示 "capture data exists but plot render failed"
  - auto-range 根据可见曲线 Y 数据拟合
  - plot.repaint() 确保刷新
- marker 功能保留：
  - target marker (purple dotted) 和 zero-crossing marker (yellow dashed) 在单 plot 上显示
  - 点击仍使用 CH1/PD only；`Select Target Transition` 后点击 plot 内任意位置，GUI 解析 CH3/error 附近零交叉
  - candidate markers 在单 plot 上叠加
  - `Confirm Lock Point` / `LOCK HERE` / `APPLY P` 逻辑保持不变
- safe range 提示增强：
  - `_capture_payload_hazard()` 在 OUT2 超 safe range 时显示：当前 OUT2 counts / V ideal、configured safe_min counts / V、configured safe_max counts / V、以及建议（调整 SCAN offset/amp 或扩大 PZT safe range）
  - 不自动扩大 safe range，不自动继续 Live，不自动 LOCK HERE
- 测试结果：`.venv\Scripts\python.exe -m pytest tests` 通过，`49 passed`；`.venv\Scripts\python.exe -m py_compile scripts\custom_fpga_scan_control.py redpitaya_lock_host\custom_fpga_backend.py redpitaya_lock_host\connection_workers.py redpitaya_lock_host\main_window.py redpitaya_lock_host\waveform_plot.py` 通过。
- 上板预期：`Capture Waveform` 后 Custom FPGA Scope 单窗口中应叠加显示 CH1/CH3/CH4 三条曲线，CH2 默认隐藏；stats 显示四通道非零 Vpp；点击 CH1 目标峰附近后 target/zero marker 正确显示；safe range 越限时提示当前值和范围。
- PASS 判据：capture points 非空 → 曲线在单 plot 中显示 → stats 非零 Vpp → placeholder hidden → 点击 marker 逻辑正常 → safe range 越限详细提示。FAIL 判据：capture 返回数据但 GUI 不显示曲线、placeholder 仍可见、stats 为 0、marker 异常、safe range 提示不清、任何 RTL/Vivado/bitstream 被修改。

## 2026-07-12 - v3LOCK-P0 上位机准实时观察与人工锁点工作台

- 本次目标：只修改上位机 Python 和既有记录，完成用于 10 Hz PZT 扫描的“实验工作台”，不是高速示波器，也不声称已经真实激光锁定。
- 修改文件：`redpitaya_lock_host/main_window.py`、`tests/test_custom_fpga_backend.py`、`../../version/STATUS.md`、`../../version/v3/DEVELOPMENT_LOG.md`、`docs/DEVELOPMENT_LOG.md`。
- 未修改：RTL、Vivado project、bitstream、寄存器地址、寄存器语义均未修改；未新增 AI、自动重锁 FSM、自动 PID 调参或自动 polarity 判断。
- 准实时采集：新增 `Start Live`、`Stop Live`、`Capture Once` 与 `refresh interval 500/1000/2000 ms`，默认 `1000 ms`。Live 使用 `capture_in_flight` 防重入，流程为 capture 完成 -> GUI 更新/安全检查 -> single-shot 延时 -> 下一次 capture；capture/SSH/MAGIC/VERSION/saturation/OUT2 safe range/连续 LOCK_ERROR 异常或窗口关闭会停止 Live。
- 四通道显示：右侧改为四个独立 `WaveformPlot`：CH1 IN1/PD、CH3 OUT1/laser_error、CH4 OUT2/selected_out2、CH2 IN2/REF。每通道有 `Visible`、`Auto Y`、`Scale counts/div`、`Center counts`、`Reset`；这些控件只改变显示范围和可见性，不改 capture 原始数据，不写 FPGA。
- 视图模式：`Lock View` 默认显示 CH1/CH3/CH4、隐藏 CH2，capture length 默认 2048，并按 scan freq 估算 decimation 以覆盖约一个扫描周期，同时显示当前 capture 时间窗；`REF Debug` 默认只显示 CH2，decimation 仅 1/2/4/8，并提示不能同时完整显示 10 Hz 慢速扫描周期。
- 人工锁点：新增 `Select Target Transition` 与 `Confirm Lock Point`。用户在 CH1/PD 图点击目标峰附近后，GUI 记录 clicked index/time/OUT2，并在附近窗口搜索 CH3/error 有效零交叉；有效性检查包括局部 Vpp、斜率、capture 边缘、OUT2 安全范围和 saturation。找到后只生成 pending lock point，并在四通道画 target marker 与 resolved zero-crossing marker；只有 `Confirm Lock Point` 更新 `selected_lock_point`。
- 最小 P-only：`LOCK HERE` 必须已有 confirmed lock point；随后等待 OUT2 到 target window，触发 FPGA `CAPTURE_LOCK_POINT`，由 FPGA 捕获 `ERROR_SETPOINT` 和 `LOCK_BIAS` 并进入 `MODE=3 P_LOCK`，Kp 从 0 开始。`APPLY P` 不覆盖锁点，只允许用户手动 Kp `0/4/8/16/32` 与 polarity；Ki/Kd 禁用，不自动加 Kp，不自动判断 polarity，不自动重锁。
- GUI 说明：补充 offset-v、amp-v、freq-hz、step-counts、limit-counts、hold-v、Kp manual step、polarity、correction-limit-counts、target-window-counts、capture-length、capture-decimation、LOCK_BIAS、ERROR_SETPOINT、LOCK_ERROR 等简短 tooltip/状态说明。
- 测试结果：`.venv\Scripts\python.exe -m pytest tests` 通过，`42 passed`；`.venv\Scripts\python.exe -m py_compile scripts\custom_fpga_scan_control.py redpitaya_lock_host\custom_fpga_backend.py redpitaya_lock_host\connection_workers.py redpitaya_lock_host\main_window.py redpitaya_lock_host\waveform_plot.py` 通过。
- 上板预期现象：SCAN 后 Lock View Live 能看到 CH1/CH3/CH4，CH2 默认隐藏；点击 CH1 目标峰附近后，CH3 附近解析出过零并显示 marker；Confirm 后 `LOCK HERE` 进入 P_LOCK Kp=0；之后仅用户手动 `APPLY P` 小步增益。
- PASS 判据：Live 不重入，Stop 后不继续 capture；capture 完成后才排下一轮；四通道显示控制不改原始数据；无过零拒绝 Confirm；未 Confirm 阻止 LOCK HERE；APPLY P 不覆盖 `LOCK_BIAS` / `ERROR_SETPOINT`。FAIL 判据：收到 capture 但不显示、Live 重入、未 Confirm 可 LOCK HERE、APPLY P 重新捕获或覆盖锁点、任何 RTL/Vivado/bitstream 被改动。
- 下一步唯一任务：用户上板执行 `SCAN -> Lock View Live/Capture Once -> CH1 点击目标峰附近 -> Confirm Lock Point -> LOCK HERE -> 手动 APPLY P 0/4/8/16/32 -> 判断 polarity -> 异常 SAFE`，记录真实 capture 和 LOCK HERE 现象。

## 2026-07-11 - v3LOCK-P0 人工 LOCK HERE 与同拍锁点捕获候选

- 本次重要纠正：历史 `board(1).csv` 中的 `54 counts`、`0.704 V`、`0.784 V`、`49.75 Hz` 以及任何峰值、基线、扫描位置，只允许作为问题分析证据，禁止硬编码进 RTL、Python、GUI、测试默认值或锁点配置。
- RTL 修改：`custom_register_bank.sv` 新增 `ERROR_SETPOINT`、`LOCK_ERROR_MONITOR`、`CAPTURE_LOCK_POINT`，协议版本升为 `0x00030001`。写 `CAPTURE_LOCK_POINT=1` 时，FPGA 在 `clk_i` 域锁存当前 `ERROR_MONITOR` 为 `ERROR_SETPOINT`、当前 `OUT2_MONITOR` 为 `LOCK_BIAS`，并进入 `MODE=3 P_LOCK`。
- RTL 新增：`error_setpoint_corrector.sv`，输出寄存化 `lock_error = saturate_14bit(laser_error - error_setpoint)`；`red_pitaya_top.sv` 改为让 P_LOCK 使用 `lock_error`，OUT1 仍保持原始 `laser_error` 观察。
- 无扰切换修复：`out2_lock_controller` 在 P_LOCK 管线填充期间输出 `LOCK_BIAS`，避免 `SCAN -> P_LOCK` 时因 Kp=0 先跳到 0。
- 上位机修改：主流程改为 `Capture Waveform -> 点击当前波形目标 -> LOCK HERE`。`LOCK HERE` 等待当前 OUT2 重新进入用户所选目标窗口后，调用 FPGA `CAPTURE_LOCK_POINT`；不使用历史 CSV 锁点，不要求用户手工填写 `ERROR_SETPOINT` 或 `LOCK_BIAS`。
- 删除/隐藏当前 GUI 的自动识峰入口；第一版不做 AI、不做自动区分 Rb 谱峰、不恢复 Ki/integral、不做复杂 PID。
- 验证：`py_compile` 通过；`python -m pytest tests` 结果 `18 passed`；`tb_error_setpoint_corrector` 结果 `tests=6 pass=6 fail=0`；`tb_custom_register_bank_basic` 结果 `tests=83 pass=83 fail=0`；`tb_out2_lock_controller` 结果 `tests=29 pass=29 fail=0`。
- 未执行：未运行 Vivado synthesis / implementation / timing，未生成 bitstream，未烧录，未接板子，未运行真实 LOCK HERE。
- 安全边界：当前仍禁止声称 FPGA 已闭环锁定或替代 D2-125；LOCK HERE 必须先 OUT2 示波器验证，异常立即 SAFE。

## 2026-07-11 - 修复 custom_debug_capture LUTRAM 资源爆炸

- 问题：用户手动 Vivado synthesis 完成后，implementation `place_design` 报 `[Place 30-484]`；`custom_debug_capture` 的 `mem_ch*` 被推断成 LUTRAM / RAM64M / RAM64X1D，`Number of LUTRAMs/SRLs=6520`，`required capable slices=1630 out of 1500`，利用率 `108.667%`。
- 修复：`v0.94/rtl/custom_debug_capture.sv` 中为 `mem_ch1..mem_ch4` 添加 `(* ram_style = "block" *)`，并删除组合读，改为同步读；`data_ch*_o` 允许 1 个 `clk_i` 周期读取延迟，目标是让 Vivado 推断 Block RAM 而不是 distributed RAM。
- 四通道保持完整：CH1=IN1/PD，CH2=IN2/REF，CH3=laser_error，CH4=selected_out2；默认 `DEPTH=4096` 保持不变，未降级为 CH3/CH4-only。
- testbench：`v0.94/sim/tb_custom_debug_capture.sv` 已适配同步读 1-cycle latency，继续覆盖 start capture、busy/done、read_index 读取 CH1-CH4、decimation 和 length 限制。
- 验证：`xvlog -sv rtl/custom_debug_capture.sv sim/tb_custom_debug_capture.sv` 通过；`tb_custom_debug_capture` 仿真结果 `tests=12 pass=12 fail=0`。
- 未执行：未运行 Vivado synthesis / implementation，未生成 bitstream，未烧录，未接板子，未运行 Auto Lock。
- 安全边界：未修改 Auto Lock / P_LOCK / KI / correction limit；不恢复积分，不新增 FSM / relock / AI。下一步必须由用户手动 Vivado implementation 确认不再出现 `[Place 30-484]`，并检查 timing `WNS >= 0, TNS = 0, Failing Endpoints = 0`。

## 2026-07-10 - Auto Lock candidate 与单窗口波形显示第一版

- 本轮目标：实现 Auto Lock candidate 和单窗口 `Custom FPGA Scope`，不是完整 AI 自动锁定，也不是已完成激光稳频。
- RTL 修改：`custom_register_bank.sv` 中新增 `LOCK_CORRECTION_LIMIT`，默认 `128 counts`；`out2_lock_controller` 的 P-only correction 先按该 limit 限幅，再叠加 `LOCK_BIAS`，最终仍按绝对 DAC limit 限幅。`MODE=4 PI_LOCK` 继续退化为 P_LOCK，`KI / integral` 不恢复。
- RTL 新增：`custom_debug_capture.sv`，手动 capture 四路信号：CH1=IN1/PD，CH2=IN2/REF，CH3=OUT1/laser_error，CH4=OUT2/selected_out2；支持 decimation、length、read index 和四路数据寄存器。4.6 MHz REF 在高 decimation 下可能 alias。
- 上位机修改：新增 `ARM AUTO LOCK` / `ABORT AUTO LOCK` 候选流程。Auto Lock 必须先处于 SCAN，寻找 error 过零点，写 `LOCK_BIAS` 和 `LOCK_CORRECTION_LIMIT`，强制 `Kp=0`、`Ki=0` 后进入 `MODE=3 P_LOCK`，再只允许自动小步 `Kp=4/8/16/32`；error 变大、OUT2 接近 limit 或 saturated 时立即 SAFE。
- GUI 修改：右侧四个空 preview 窗口收敛为单窗口 `Custom FPGA Scope`，叠加 IN1 / IN2 / OUT1 / OUT2，支持通道勾选、统计和 CSV 保存；没有新 bitstream 或 capture 数据时显示 `custom_debug_capture not available`，不画 0。
- 验证：`python -m pytest tests` 通过，`16 passed`；`py_compile` 通过；`xvlog` 通过；`tb_out2_lock_controller` 结果 `tests=28 pass=28 fail=0`；`tb_custom_debug_capture` 结果 `tests=11 pass=11 fail=0`；`tb_custom_register_bank_basic` 结果 `tests=71 pass=71 fail=0`。
- 尚未执行：未运行 Vivado synthesis / implementation / timing，未生成 bitstream，未烧录，未上板验证。下一步必须由用户手动 Vivado timing；通过前不得声称 Auto Lock 或 debug_capture 已通过硬件验证。
- 安全边界：OUT2 当前已接 PZT / Scan，所以 P_LOCK / Auto Lock 必须默认小 Kp、小 correction limit；禁止恢复积分，禁止 relock，禁止 AI 自动锁定，禁止失败后继续输出未知电压，禁止声称 FPGA 已闭环稳频或替代 D2-125。

## 2026-07-10 - 当前 main 主线文档同步

- 本次只同步文档，不修改 RTL、不修改 testbench、不修改 Vivado project、不运行 Vivado、不生成 bitstream、不烧录、不连接 Red Pitaya。
- 当前主线：v3REG-0 SAFE/SCAN 已由用户上板验证；base address `0x40600000`，`MAGIC=0x4D545330`，`VERSION=0x00030000`；GUI / monitor 已可控制 OUT2 三角波并可 SAFE 关闭。
- GitHub main 已包含 HOLD / P_LOCK / PI_LOCK 候选，但尚未完成最新 Vivado synthesis / implementation / timing / bitstream / 烧录 / 上板示波器验证。
- 当前 LOCK 目标缩小为 P-only：`MODE=3 P_LOCK` 是下一步验证重点；`MODE=4 PI_LOCK` 暂时退化为 P_LOCK，`KI / integral` 当前不要恢复。
- OUT2 仍只允许接示波器；禁止接 PZT / Scan input / 激光器 / D2-125 Servo Output / D2-125 Aux Output；禁止声称 FPGA 已经闭环锁定或替代 D2-125。

## 2026-07-09 - 修复 Custom FPGA Lock Host GUI 启动失败

- 本次实现目标：修复 `.\run_mock.bat` 启动时报 `AttributeError: 'MainWindow' object has no attribute 'out1'` 的问题。根因是主界面已收敛为 `Custom FPGA Lock Host`，不再创建 Official SCPI OUT1/OUT2 控件，但 `main_window.py` 中仍有旧的 `self.out1` / `self.out2` 信号绑定、预览、按钮状态和 CSV metadata 引用。
- 修改 Python 文件：`software/redpitaya_lock_host/redpitaya_lock_host/main_window.py`、`software/redpitaya_lock_host/tests/test_custom_fpga_backend.py`。
- 修复方式：新增 legacy SCPI 控件存在性保护；`_connect_signals()`、`_load_defaults()`、`_redraw_from_last_waveforms()`、`_apply_button_state()`、`_csv_metadata()` 在未创建 `self.out1/self.out2` 时不再访问它们。CH3/CH4 在 Custom FPGA 主界面下使用零线占位，不依赖 Official SCPI preview 控件。
- 当前方向：主界面继续收敛为 `Custom FPGA Lock Host`，保留 `Probe Registers`、`Status`、`SAFE`、`SCAN`、`HOLD`、`Capture Bias`、`LOCK`、`UNLOCK / SAFE`，不恢复 Official SCPI 主界面。
- 如何运行/验证：`py_compile` 通过；系统 Python `python -m pytest tests` 通过；`run_mock.bat` 启动后 5 秒仍运行；直接运行 `python -m redpitaya_lock_host.main` 5 秒仍运行且无 stderr。
- 是否修改 RTL：否。
- 是否运行 Vivado：否。
- 是否生成 bitstream：否。

## 2026-07-09 - 上位机收敛为 Custom FPGA Lock Host，并加入一键 P_LOCK 工作流

- 本次实现目标：上位机主界面不再暴露 `Official SCPI Mode`、`Start SCPI Server`、`Connect SCPI` 和 Official ASG OUT1/OUT2 主入口，默认收敛为项目专用 `Custom FPGA Lock Host`。
- 修改 Python 文件：`software/redpitaya_lock_host/redpitaya_lock_host/custom_fpga_backend.py`、`software/redpitaya_lock_host/redpitaya_lock_host/connection_workers.py`、`software/redpitaya_lock_host/redpitaya_lock_host/main_window.py`、`software/redpitaya_lock_host/tests/test_custom_fpga_backend.py`。
- GUI 新增主流程按钮：`Capture Bias`、`LOCK`、`UNLOCK / SAFE`、`Capture Waveform`。其中 `LOCK` 为 P-only 工作流：先 `Status` 读取并检查 `MAGIC=0x4D545330`，再用当前 `OUT2_MONITOR` counts 作为 `LOCK_BIAS`，随后写入 `MODE=3 P_LOCK`、`ENABLE=1`、`KP`、`POLARITY`、`LOCK_LIMIT`。
- 重要约束：`LOCK_BIAS` 捕获不使用 `lock-bias-v` 电压估算，而使用板端 `OUT2_MONITOR` counts；GUI 同时显示理想 volts 仅作寄存器尺度参考，真实 DAC 输出以示波器为准。
- 当前 `IN1/IN2` 自定义波形采集未实现。GUI 只显示 `debug_capture` 的最小寄存器方案提示：`DEBUG_CTRL`、`DEBUG_STATUS`、`DEBUG_DECIM`、`DEBUG_LENGTH`、`DEBUG_INDEX`、`DEBUG_IN1_DATA`、`DEBUG_IN2_DATA`，后续再扩展 `DEBUG_ERROR_DATA` / `DEBUG_OUT2_DATA`；本次不修改 RTL。
- 记录当前 OUT2 DAC 实测偏差数据：

| offset-v | amp-v | 理论范围 | 实测 min | 实测 max | 实测 Vpp |
|---:|---:|---:|---:|---:|---:|
| 0.50 | 0.05 | 0.45-0.55 V | 513 mV | 636 mV | 123 mV |
| 0.60 | 0.05 | 0.55-0.65 V | 624 mV | 752 mV | 123 mV |
| 0.70 | 0.05 | 0.65-0.75 V | 736 mV | 863 mV | 123 mV |
| 0.60 | 0.10 | 0.50-0.70 V | 569 mV | 803 mV | 235 mV |
| 0.60 | 0.15 | 0.45-0.75 V | 513 mV | 863 mV | 350 mV |

- 判断：当前偏差更像 DAC 模拟输出链路的 gain/offset 标定问题，而不是寄存器或 ramp 逻辑完全错误。后续需要做 OUT2 校准或继续在 GUI 中保留“理想 volts 与示波器实测不同”的提示。
- 如何运行/验证：进入 `software/redpitaya_lock_host` 后运行 `.\run.bat`；GUI 路径为 `Probe Registers -> Status -> SAFE -> SCAN -> Capture Bias -> LOCK -> UNLOCK / SAFE`，全程先只接示波器。
- 是否修改 RTL：否。
- 是否生成 bitstream：否。

## 2026-07-09 - v3REG P_LOCK timing 修复：OUT2 锁定控制缩小为 P-only 流水线

- 本次实现目标：针对用户手动 Vivado implementation timing fail（`WNS=-10.361 ns`、`TNS=-16400.330 ns`、`Failing Endpoints=6099`），将 `out2_lock_controller` 从组合式 P/PI 路径改为 timing-friendly 的 P-only 流水线控制器。
- 修改 RTL 文件：`v0.94/rtl/custom_register_bank.sv`。保持 module 端口和 register map 不变；`MODE=3 P_LOCK` 执行 `OUT2 = clamp(LOCK_BIAS + POLARITY * KP * error, LOCK_LIMIT)`；`MODE=4 PI_LOCK` 暂时退化为同样的 P_LOCK。
- 修改仿真文件：`v0.94/sim/tb_out2_lock_controller.sv`。测试更新为等待 P_LOCK 流水线 latency，并确认 `PI_LOCK` 在 `Ki` 非零时仍输出 P-only 结果，证明 `Ki/integrator` 当前被禁用。
- 当前处理：删除 `out2_lock_controller` 内部 `integral_acc`、`Ki` 乘法、I term 和 error->Ki->integral->clamp 长组合路径；`ki_i` 和 `integral_reset_i` 端口保留但当前 RTL 不使用。
- 修改 Python 文件：无。上位机 `p-lock` / `pi-lock` 操作和寄存器地址保持不变；上位机仍可写 `KI`，但当前 RTL 不使用 `KI`。
- 验证方式：未运行 Vivado、未运行 synthesis / implementation、未生成 bitstream、未上板；本次只做非 Vivado 静态检查与 host 侧 Python 检查。
- 是否修改 RTL：是，仅修改 `v0.94/rtl/custom_register_bank.sv` 中 `out2_lock_controller`。
- 是否生成 bitstream：否。
- 安全边界：当前 LOCK 目标缩小为 P_LOCK；OUT2 仍必须先只接示波器验证 SAFE/SCAN/HOLD/P_LOCK 行为，不能直接接 PZT、Scan input、激光器电流调制或 D2-125 输出。

## 2026-07-09 - 项目文档中文化与永久语言规则记录

- 本次任务：将当前入口文档、version 规则文档和上位机 docs 中明显英文说明改为中文，并在根目录 `README.md` 与 `version/rules/00_DOCUMENT_LANGUAGE_AND_STYLE_RULES.md` 中记录后续项目文档默认使用中文。
- 修改 Python 文件：无。
- 修改 RTL 文件：无。
- 修改文档文件：`README.md`、`AI_REVIEW_README.md`、`CURRENT_MAINLINE_REVIEW.md`、`version/CURRENT_REVIEW_MANIFEST.md`、`version/PROJECT_DIRECTORY_AND_WORKFLOW_RULES.md`、`version/rules/00_DOCUMENT_LANGUAGE_AND_STYLE_RULES.md`、`version/rules/00_PROJECT_ROOT_AND_AGENT_ROLES.md`、`software/redpitaya_lock_host/README.md` 以及 `software/redpitaya_lock_host/docs/` 下多份说明文档。
- 验证方式：运行 Markdown 英文关键词自查；保留命令、路径、寄存器名、模块名、模式名、英文缩写和历史 review 中的英文引用。
- 是否修改 RTL：否。
- 是否生成 bitstream：否。

## 2026-07-08 - v3REG-1 / v3REG-2 状态文档同步与独立仿真确认

- 本次实现/同步内容：只做文档同步和仿真确认，不接真实执行器，不运行 Vivado synthesis / implementation，不生成 bitstream。明确 v3REG-0 SAFE/SCAN 已由用户上板验证；当前 GitHub main RTL/software 已包含 v3REG-1/v3REG-2 候选 `HOLD/P_LOCK/PI_LOCK`，但尚未完成 Vivado/timing/bitstream/上板验证。
- 修改 Python 文件：无。
- 修改文档文件：`version/STATUS.md`、`version/CURRENT_REVIEW_MANIFEST.md`、`software/redpitaya_lock_host/docs/CONNECTION_DIAGNOSIS.md`、`software/redpitaya_lock_host/docs/HARDWARE_TEST_SOP.md`、`software/redpitaya_lock_host/docs/CUSTOM_FPGA_LOCK_WORKFLOW.md`、`software/redpitaya_lock_host/docs/DEVELOPMENT_LOG.md`。
- 修改仿真文件：`v0.94/sim/tb_out2_lock_controller.sv`，补充 `P_LOCK Kp=0 -> lock_bias` 以及 PI 在 `ENABLE=0`、`MODE=SAFE` 下清积分的断言。
- 验证方式：独立运行 `xvlog / xelab / xsim`，未打开 Vivado 工程。`tb_out2_lock_controller` 结果 `tests=20 pass=20 fail=0`；`tb_custom_register_bank_basic` 结果 `tests=53 pass=53 fail=0`。
- 是否修改 RTL：否，未修改功能 RTL；只修改 testbench。
- 是否生成 bitstream：否。
- 安全边界：OUT2 仍只允许接示波器；禁止接 PZT、Scan input、激光器、D2-125 Servo Output 或 D2-125 Aux Output。

## 2026-07-08 - v3REG-1 / v3REG-2 最短锁定路径：HOLD、P_LOCK、PI_LOCK 第一版

- 本次实现目标：在 v3REG-0 已验证 `GUI -> SSH -> /dev/mem -> custom_register_bank -> ramp_generator -> selected_out2 -> DAC B / OUT2` 的基础上，继续实现最短手动/半自动锁定路径。新增 `HOLD` 固定输出、`P_LOCK` 比例锁定、`PI_LOCK` 比例积分锁定的第一版硬件寄存器、RTL 输出选择、CLI、GUI 和测试。当前仍保留外部 EOM RF、模拟 BPF 和放大器，不替代模拟前端。
- 修改 Python 文件：`software/redpitaya_lock_host/scripts/custom_fpga_scan_control.py`、`software/redpitaya_lock_host/redpitaya_lock_host/custom_fpga_backend.py`、`software/redpitaya_lock_host/redpitaya_lock_host/connection_workers.py`、`software/redpitaya_lock_host/redpitaya_lock_host/main_window.py`、`software/redpitaya_lock_host/tests/test_custom_fpga_backend.py`。
- 修改 RTL / 仿真文件：`v0.94/rtl/custom_register_bank.sv`、`v0.94/rtl/red_pitaya_top.sv`、`v0.94/sim/tb_custom_register_bank_basic.sv`、新增 `v0.94/sim/tb_out2_lock_controller.sv`。
- 新寄存器：`HOLD_VALUE(0x2C)`、`KP(0x30)`、`POLARITY(0x34)`、`LOCK_BIAS(0x38)`、`LOCK_LIMIT(0x3C)`、`ERROR_MONITOR(0x40, RO)`、`CONTROL_MONITOR(0x44, RO)`、`KI(0x48)`、`INTEGRAL_RESET(0x4C)`。`KP/KI` 为 raw gain，约定 `256 = 1.0x`；`POLARITY=0` 为 normal，`POLARITY=1` 为 invert。
- MODE 定义：`0=SAFE`，`1=SCAN`，`2=HOLD`，`3=P_LOCK`，`4=PI_LOCK`。`ENABLE=0` 或 `MODE=0` 时 OUT2 强制为 0；SAFE 仍为最高优先级。P_LOCK/PI_LOCK 默认 `Kp=0`、`Ki=0`，必须人工逐步增加，且先 scope-only 验证。
- GUI 功能变化：Custom FPGA Control 增加 `HOLD`、`P_LOCK`、`PI_LOCK` 按钮，以及 `hold-v`、`Kp raw`、`Ki raw`、`polarity`、`lock-bias-v`、`lock-limit-counts` 输入；Status 显示增加 `ERROR_MONITOR` 和 `CONTROL_MONITOR`。所有写操作继续要求先通过 MAGIC 检查。
- 验证方式：host 侧 `py_compile` 通过；`python -m pytest tests` 通过，结果 `13 passed`。Vivado xsim 仿真通过：`tb_out2_lock_controller` 结果 `tests=14 pass=14 fail=0`；`tb_custom_register_bank_basic` 结果 `tests=53 pass=53 fail=0`；`tb_ramp_generator` 结果 `tests=249 pass=249 fail=0`。`red_pitaya_top.sv` 已完成 xvlog 语法分析。
- 是否修改 RTL：是，修改寄存器银行和 OUT2 模式选择逻辑；未修改 Vivado 工程文件。
- 是否生成 bitstream：否。
- 安全边界：本阶段只允许 OUT2 接示波器观察。HOLD/P_LOCK/PI_LOCK 不得默认接 PZT、激光电流、D2-125 Servo Output 或 Scan input。P_LOCK/PI_LOCK 上板时必须从 `Kp=0`、`Ki=0`、`LOCK_LIMIT` 小范围开始，确认 OUT2 幅度、极性、限幅和 SAFE 行为后，才能制定执行器连接 SOP。

## 2026-07-05 - v3REG-0 GUI 控制 OUT2 扫描并观察到实验波形

- 记录当前阶段推进：v3REG-0 已经从“板子是否能被上位机控制”推进到“上位机可以控制扫描参数，并且能观察到实验波形”的阶段。
- 已验证完整链路：GUI -> SSH -> `/dev/mem` -> `custom_register_bank` -> `ramp_generator` -> `selected_out2` -> DAC B / OUT2。Red Pitaya 自定义 bitstream 已在板上运行，base address 为 `0x40600000`；GUI Probe Registers 能找到 `MAGIC=0x4D545330`、`VERSION=0x00030000`、`found_base_addr=0x40600000`。
- 已确认手动 monitor 和 GUI 两条路径均通过：monitor 写寄存器可以产生 10 Hz OUT2 三角波，monitor SAFE 后三角波消失；修复 `/dev/mem mmap.flush()` EINVAL 的 host helper 问题后，GUI SCAN 可以产生 OUT2 三角波，GUI SAFE 可以关闭 OUT2 输出。
- 当前 GUI Custom FPGA Control 参数：base address `0x40600000`，`offset-v=0.7500 V`，`amp-v=0.2000 V`，`freq-hz=50.170 Hz`，`step-counts=1`，`limit-counts=8191`。
- GUI SCAN 读回：`MAGIC=0x4D545330`，`VERSION=0x00030000`，`MODE=1`，`ENABLE=1`，`STATUS=0x00000001`，`OUT2=4522 counts / 0.552069 V`。设定扫描范围约为 `0.55 V` 到 `0.95 V`（约 `0.40 Vpp`），因此当前读回值接近理论下限。
- 观察到波形时的激光器控制器状态：TEC 设置/工作 `22.66 C / 22.46 C`；电流设置/工作 `40.07 mA / 57.42 mA`；PZT 设置/工作 `34.99 V / 42.52 V`。后续波形变化需要与这些 TEC / current / PZT 条件对照。
- 本次波形指标：板端扫描/输出信号 `Vpp=0.4583 V`，`min=0.6236 V`，`max=1.082 V`，`RMS=0.8492 V`；CH2 信号 `Vpp=0.2701 V`，`min=0.3303 V`，`max=0.6004 V`，`RMS=0.4828 V`；CH3 信号 `Vpp=1.784 V`，`min=-1.16 V`，`max=0.6239 V`，`RMS=0.2433 V`；板端输出信号 `Vpp=0.08848 V`，`min=0.6243 V`，`max=0.7128 V`，`RMS=0.6696 V`。
- 结论：GUI 已经可以设置 OUT2 的 offset、amplitude、frequency、enable/safe 和 scan mode；在 `offset=0.75 V`、`amp=0.20 V`、`freq=50.17 Hz` 条件下，系统可以扫描并显示周期性通道响应，已经可以进入下一步谱线扫描观察。
- 边界：当前完成的是 GUI 可控扫描输出 + 实验波形观察，不是闭环锁定，也不是 D2-125 替代。继续以示波器优先观察；任何连接到激光器 PZT、scan、current modulation 或 D2-125 输入的操作，都必须记录接线、幅度、偏置和安全限制。
- 下一步计划：执行参数矩阵 A `offset=0.50 V, amp=0.20 V, freq=50 Hz`；B `offset=0.75 V, amp=0.20 V, freq=50 Hz`；C `offset=0.75 V, amp=0.10 V, freq=20 Hz`；D `offset=0.75 V, amp=0.05 V, freq=10 Hz`。每组记录 GUI 参数、OUT2 读回、示波器 OUT2 Vpp/min/max、CH2/CH3 稳定性，以及是否出现削顶、跳变、饱和或断裂。
- 修改 Python 文件：无。
- 验证方式：仅文档记录更新，本次未运行命令。
- 是否修改 RTL：否。
- 是否生成 bitstream：否。

## 2026-07-05 - 修复 GUI SAFE/SCAN 的 /dev/mem flush EINVAL 问题

- 修复 GUI Custom FPGA SAFE/SCAN 写寄存器失败问题：Probe Registers 和 Status 已经成功（`MAGIC=0x4D545330`，`VERSION=0x00030000`），但远端 helper 写寄存器时报 `OSError: [Errno 22] Invalid argument`。
- 根因：板端 Python helper 的 `RegisterWindow.write()` 在 `/dev/mem` MMIO 写入后调用了 `mmap.flush()`；当前 Red Pitaya Linux 路径下该调用可能返回 EINVAL，即使 monitor 写寄存器本身是有效的。
- 修复方式：从 REMOTE_HELPER 写寄存器路径中删除 `self.mem.flush()`；SAFE/SCAN 仍保留 MAGIC precheck，并在写入后继续读回 status。
- 修改 Python 文件：`scripts/custom_fpga_scan_control.py`，`tests/test_custom_fpga_backend.py`。
- 验证：`.\.venv\Scripts\python.exe -m py_compile scripts\custom_fpga_scan_control.py redpitaya_lock_host\custom_fpga_backend.py redpitaya_lock_host\main_window.py` 通过；`python -m pytest tests` 通过。`.\.venv\Scripts\python.exe -m pytest tests` 未能运行，因为 `.venv` 中未安装 pytest。
- 是否修改 RTL：否。
- 是否生成 bitstream：否。

## 2026-07-05 - v3REG-0 板端 monitor 验证 OUT2 SAFE/SCAN 通过

- 记录板端 bring-up 证据：Red Pitaya 已加载 `/root/red_pitaya_top.bit.bin`；`/opt/redpitaya/bin/monitor 0x40600000` 返回 `0x4D545330`；`/opt/redpitaya/bin/monitor 0x40600004` 返回 `0x00030000`。
- 验证硬件行为：monitor 写入 `MODE=1`、`ENABLE=1`、`SCAN_OFFSET=0`、`SCAN_AMP=0x19A`、`SCAN_STEP=0x1`、`SCAN_UPDATE_DIV=0x1DC6`、`OUT2_LIMIT=0x1FFF` 后，OUT2 产生约 10 Hz 安全三角波。
- 验证 SAFE 关闭：向 `0x4060000C` 写 `0x0`，再向 `0x40600008` 写 `0x0` 后，OUT2 三角波消失，OUT2 回到无三角波状态。
- 结论：PS -> PL sys_bus 访问、base address `0x40600000`、`custom_register_bank`、`ramp_generator`、MODE/ENABLE 控制、`selected_out2` -> DAC B / OUT2、SAFE 关闭链路都已在硬件上验证通过。
- 修改 Python 文件：无。
- 如何运行/验证：使用上述 board monitor 命令；下一步 GUI 验证路径是 Custom FPGA Mode -> Probe Registers -> Status -> SAFE -> SCAN。
- 是否修改 RTL：否。
- 是否生成 bitstream：否。
- 安全边界不变：OUT2 仅接示波器观察；不要将 OUT2 接到 laser PZT、laser current、D2-125 Servo Output 或 Scan input。

## 2026-07-05 - GUI OUT2 路径边界文案修复

- 完成最小 GUI 文案和默认参数修复，让用户明确区分 Official SCPI OUT2 和 Custom FPGA `selected_out2` SAFE/SCAN。
- 修改 Python 文件：`redpitaya_lock_host/main_window.py`、`tests/test_custom_fpga_backend.py`、`tests/test_custom_fpga_workflow.py`。
- 验证：`python -m py_compile redpitaya_lock_host\main_window.py redpitaya_lock_host\custom_fpga_backend.py`；`python -m pytest tests`。
- 是否修改 RTL：否。
- 是否生成 bitstream：否。

## 2026-07-05 - Custom FPGA 缺失寄存器 GUI 状态保护

- 新增 GUI/status 保护：当 `MAGIC != 0x4D545330` 时显示 `custom_register_bank not found`，不再显示假的全零寄存器状态。
- 修改 Python 文件：`redpitaya_lock_host/custom_fpga_backend.py`、`redpitaya_lock_host/main_window.py`、`tests/test_custom_fpga_backend.py`。
- 验证：`python -m pytest tests\test_custom_fpga_backend.py`；`python -m py_compile redpitaya_lock_host\custom_fpga_backend.py redpitaya_lock_host\main_window.py`。
- 是否修改 RTL：否。
- 是否生成 bitstream：否。

## 2026-07-05 - GUI Custom FPGA Control v1

- 在 Custom FPGA Mode 中实现第一版 GUI Custom FPGA Control 面板。
- 新增 SSH + `/dev/mem` 寄存器操作：Probe Registers、Status、SAFE、SCAN，不启动 `redpitaya_scpi`。
- 修改 Python 文件：`redpitaya_lock_host/custom_fpga_backend.py`、`redpitaya_lock_host/connection_workers.py`、`redpitaya_lock_host/main_window.py`。
- 验证：`python -m py_compile` 已通过 `custom_fpga_backend.py`、`connection_workers.py`、`main_window.py`、`scripts/custom_fpga_scan_control.py`。
- GUI 运行路径：`.\run.bat`，然后 Custom FPGA Mode -> Probe Registers -> Status -> SAFE -> SCAN。
- 是否修改 RTL：否。
- 是否生成 bitstream：否。

## 2026-06-30 - 四模式 GUI 工作流结构

- Reorganized the host GUI around four mode pages:
  Hardware Bring-up, Custom FPGA Observe, Lock Workflow, and Data Log.
- Kept Official SCPI Mode for Probe, Start SCPI Server, Connect SCPI, safe OUT2 scan, IN1/IN2 acquisition, and output disable.
- Added Custom FPGA Observe manual oscilloscope inputs for OUT1 laser_error, OUT2 laser_control, PD/absorption, REF, and notes.
- Added automatic OUT2/OUT1 Vpp ratio and safety judgment for manual scope readings.
- Added Lock Workflow Mode as a D2-125 replacement checklist without pretending automatic lock control is implemented.
- Added Markdown experiment log export to `docs/experiment_logs/`.
- Added `custom_fpga_backend.py` as a future interface stub; all hardware methods raise `NotImplementedError`.
- No FPGA internal data is faked.
- No FPGA RTL was modified.
- No Vivado project was modified.
- No bitstream was generated.

## 2026-06-30 - Canonical host-app development directory

- Confirmed all future Red Pitaya host-app development uses:
  `E:\new\fpga_lock\v94\software\redpitaya_lock_host`
- Confirmed the old standalone host-app directory is no longer used; the canonical directory is:
  `E:\new\fpga_lock\v94\software\redpitaya_lock_host`
- Documented the current directory rules:
  Python source in `redpitaya_lock_host/`, tests in `tests/`, Markdown docs/SOPs/stage notes in `docs/`, and stage records in `docs/DEVELOPMENT_LOG.md`.
- Confirmed usage instructions belong in `README.md` and `docs/USAGE.md`.
- Confirmed SCPI notes belong in `docs/SCPI_MODE_NOTES.md`.
- Confirmed `.venv/` is local only and must not be added to Git.
- Replaced remaining old standalone-directory references in active Markdown docs with the canonical host-app directory.
- Renamed the preview helper module to `waveform_preview.py` and the offline test to `tests/test_waveform_preview.py`.
- Confirmed root-level Word report cleanup was attempted, but the `.docx` file was locked by another process and was not moved.
- No FPGA RTL was modified.
- No Vivado project was modified.
- No bitstream was generated.

## 2026-06-29 - OUT1/OUT2 preview time-axis fix

- Fixed CH3/CH4 generated previews so they no longer reuse the IN1/IN2 acquisition time axis.
- Added `preview.cycles`, `preview.min_points`, and `preview.max_points` configuration.
- Documented that a 50 Hz triangle wave has a 20 ms period.
- Root cause: default `sample_count=2048` and `decimation=1024` gives about 16.78 ms of acquisition data, shorter than one 50 Hz period.
- CH3/CH4 now use an independent generated preview time axis and default to two cycles.
- CH4 remains a generated preview, not a measured OUT2 waveform.
- Real OUT2 must still be checked on an oscilloscope, or by safe OUT2 -> IN1 loopback with IN1 kept within ±1 V.
- Confirmed V2 SCPI apply uses `SOURn:TRig:INT`.
- Updated the legacy `rp_client.py` compatibility path to avoid the old `SOUR2:TRIG:IMM` command.
- Added offline preview waveform tests that do not require Red Pitaya.
- No FPGA RTL was modified.
- No Vivado project was modified.
- No bitstream was generated.

## 2026-06-29 - Windows environment and host-app documentation update

- Confirmed host app location:
  `E:\new\fpga_lock\v94\software\redpitaya_lock_host`
- Confirmed project-local `.venv` exists.
- Documented recommended environment:
  Official Python 3.11 + project-local `.venv`.
- Documented that Anaconda base is not recommended for this PySide6 GUI because of possible Qt/DLL conflicts.
- Added Windows setup instructions.
- Added usage instructions for `run.bat` and `run_mock.bat`.
- Added SCPI mode notes and hardware safety checklist.
- No FPGA RTL was modified.
- No Vivado project was modified.
- No bitstream was generated.

## 2026-06-26

### Python environment fix

Fixed repeated `ModuleNotFoundError: No module named 'yaml'` risk caused by mixed Anaconda/system Python and project `.venv` usage.

Changed:

- `requirements.txt` explicitly includes `PyYAML>=6.0`, `paramiko>=3.4`, `PySide6`, `pyqtgraph`, `numpy`, and `pandas`.
- `run.bat` now uses only `.venv\Scripts\python.exe` and no longer falls back to system Python.
- `run.bat` prints virtual-environment setup commands if `.venv` is missing.
- `main.py` prints a friendly PyYAML install hint if `import yaml` fails.
- README documents the recommended PowerShell `.venv` command path.

Confirmed scope:

- Host environment/startup files only.
- No FPGA RTL changes.
- No bitstream generation.

### V2 OUT1/OUT2 Apply SCPI fix

Fixed GUI Apply output command sequence after manual SCPI testing proved OUT2 hardware and wiring were healthy.

Manual verified sequence for OUT2:

```text
GEN:RST
SOUR2:FUNC TRIANGLE
SOUR2:FREQ:FIX 50
SOUR2:VOLT 0.05
SOUR2:VOLT:OFFS 0
OUTPUT2:STATE ON
SOUR2:TRig:INT
```

Changed:

- GUI Apply now uses `SOUR<n>:TRig:INT`, not `SOUR<n>:TRIG:IMM`.
- GUI Apply sends output state before the trigger.
- GUI Apply logs every sent SCPI command with `>>`.
- GUI Apply performs readback queries for function, frequency, amplitude, offset, and output state.
- Disable sends `SOUR<n>:VOLT 0`, `OUTPUT<n>:STATE OFF`, and `GEN:STOP`.
- Output amplitudes `>= 0.5 V` require a confirmation dialog.
- OUT2 defaults remain safe: triangle, `50 Hz`, `0.05 V`, `0 V`, enable unchecked.

Confirmed scope:

- Host SCPI output-control logic only.
- No FPGA RTL changes.
- No bitstream generation.

### V2 GUI freeze fix

Moved blocking network/SSH/SCPI actions out of the GUI thread.

Changed:

- Added background workers for Probe, Start SCPI Server, Connect SCPI, and Disconnect/safe shutdown.
- Added connection state handling for `DISCONNECTED`, `PROBING`, `SSH_AVAILABLE`, `SCPI_STARTING`, `SCPI_READY`, `SCPI_CONNECTED`, `ACQUIRING`, and `ERROR`.
- Start SCPI Server is only enabled when Probe shows SSH available and SCPI unavailable.
- If Probe shows `SCPI True`, Start SCPI Server no longer runs and the GUI instructs the user to click Connect SCPI.
- SSH startup command now uses short commands and timeout handling instead of `systemctl status`.
- Connection log and status bar report SSH/SCPI failures instead of freezing.

Confirmed scope:

- Host GUI/connection flow only.
- No FPGA RTL changes.
- No bitstream generation.

### V2 GUI layout fix

Fixed left-panel layout compression in the PySide6 GUI.

Changed:

- Main window default size is now `1600 x 950`.
- Left control panel is inside a `QScrollArea` with minimum width `430 px`.
- OUT1 and OUT2 controls are separated into tabs.
- Output controls use `QFormLayout` with minimum field widths and consistent button/input heights.
- Connection status uses a bounded read-only text area instead of a long compressed label.
- Plot panels and waveform widgets now use expanding size policies and minimum sizes.
- README documents PowerShell `.\run.bat` and notes the scrollable V2 layout.

Confirmed scope:

- GUI/layout-only code changes.
- No FPGA RTL changes.
- No bitstream generation.

### V2 mode-boundary correction

Reviewed the specified custom FPGA files and updated the host app/docs so Official SCPI Mode and Custom FPGA Mode are not mixed.

Confirmed from RTL:

- `USE_LASER_LOCK_CORE = 1`.
- OUT1 / DAC A is `laser_error`.
- OUT2 / DAC B is `laser_control`.
- official `asg_dat[0]` / `asg_dat[1]` no longer directly drive OUT1/OUT2 in custom FPGA mode.
- custom chain is IN1 + IN2 -> mixer_core -> lpf_core -> output_protect -> OUT1 error, and the same protected error feeds the shadow/sequential PI candidate -> OUT2 control.

Changed:

- Added GUI mode selector: Official SCPI Mode / Custom FPGA Mode.
- Disabled Start SCPI Server, SCPI connect, SCPI output apply, and SCPI acquisition in Custom FPGA Mode.
- Updated CH3/CH4 labels and warnings for custom FPGA output meaning.
- Hardened `run.bat` for PowerShell/CMD use, optional venv activation, argument forwarding, and missing Python message.
- Added `docs\FPGA_MODE_BOUNDARY.md`.
- Updated README and SOP documents with PowerShell `.\run.bat` instructions and mode boundary.

### V2 connection-stability refactor

Created a V2 host workflow focused on real lab connection stability.

Added:

- `connection_probe.py` for hostname resolution, ping, and port checks for 22/80/5000.
- `ssh_client.py` using Paramiko for Red Pitaya service-management commands.
- `rp_scpi_client.py` as the V2 Red Pitaya SCPI business layer.
- V2 GUI with Probe, Start SCPI Server, Connect SCPI, Disconnect, SSH credentials, resolved IP selection, OUT1/OUT2 controls, acquisition, and four-channel scope display.
- Documentation: `CONNECTION_DIAGNOSIS.md`, `SCPI_SERVER_STARTUP.md`, `HOST_APP_V2_DESIGN.md`, and `HARDWARE_TEST_SOP.md`.

Changed:

- Output defaults now use conservative `amplitude_v = 0.05 V`.
- Safe shutdown covers both OUT1 and OUT2.
- CH3 and CH4 are explicitly generated previews, not measured outputs.

Confirmed scope:

- No FPGA RTL changes.
- No bitstream generation.
- No use of any directory containing `weifang`.

### V1.1 hardware-test upgrade

Updated the host app based on `docs\CLAUDE_REVIEW_HOST_APP_V1.md`.

Added:

- `--mock` command-line support in `main.py`, with custom arguments filtered before creating `QApplication`.
- `acquisition_worker.py`, a `QThread` worker for non-blocking real SCPI acquisition.
- Real Red Pitaya acquisition methods in `rp_client.py`: `configure_acquisition`, `acquire_in1_in2`, `read_in1`, `read_in2`, and `parse_scpi_data`.
- Four-channel oscilloscope-style GUI layout.
- CH1 / CH2 measured ADC statistics and warnings.
- CH3 disabled placeholder for unavailable `error_internal`.
- CH4 generated OUT2 scan preview, explicitly not measured.
- Acquisition controls, decimation selection, sample rate display, and actual refresh-rate display.
- CSV metadata header lines.
- `atexit` best-effort safe shutdown registration.

Fixed:

- Mock mode no longer generates nonzero `error_internal`.
- `run.bat` now activates `.venv` and forwards arguments.
- `requirements.txt` now uses standard `PyYAML` package naming.

Confirmed scope:

- No FPGA RTL changes.
- No Vivado project changes.
- No bitstream generation.
- No use of any directory containing `weifang`.

### V1 initial implementation

Created Red Pitaya laser lock host V1; current development now lives in `E:\new\fpga_lock\v94\software\redpitaya_lock_host`.

Added:

- PySide6 GUI entry point and main window.
- SCPI socket client with query and write support.
- Red Pitaya client wrapper with `*IDN?` connection gate.
- OUT2 triangle scan apply, stop, and safe shutdown sequences.
- Safety validation for frequency, amplitude, and offset.
- Mock mode client with synthetic IN1, IN2, and placeholder `error_internal` waveforms.
- CSV export through pandas.
- PNG export of the plotting panel.
- Project config file, requirements file, and Windows run script.
- Documentation for project context, host design, test plan, and next FPGA debug-buffer phase.

Confirmed project boundary:

- No FPGA RTL changes.
- No Vivado project changes.
- No bitstream generation.
- No use of any directory containing `weifang`.

## 2026-07-11 - v3LOCK-P0 Vivado timing PASS 记录

- 本次目标：只同步用户手动 Vivado timing 结果到现有项目记录，不修改代码。
- 未修改代码：未修改 RTL、testbench、Python、Vivado 工程或配置；未运行 Vivado；未生成 bitstream；未烧录；未连接板卡。
- 当前验证等级：代码和 testbench 已通过；用户手动 synthesis / implementation / timing 已通过；尚未进入 bitstream / 烧录 / 上板验证。
- 用户手动 Vivado 证据：`red_pitaya_top` implementation 完成；Implemented Design 中存在 `i_custom_debug_capture`、`i_custom_register_bank`、`i_error_setpoint_corrector`。
- Timing 结果：Setup WNS `+0.031 ns`、TNS `0.000 ns`、Failing Endpoints `0`；Hold WHS `+0.048 ns`、THS `0.000 ns`、Failing Endpoints `0`；Pulse Width WPWS `+1.000 ns`、TPWS `0.000 ns`、Failing Endpoints `0`；Vivado 显示 `All user specified timing constraints are met.`。
- 尚未完成的验证：尚未证明 bitstream 已生成；尚未烧录；尚未读取新 `VERSION=0x00030001`；尚未完成 SAFE/SCAN 示波器回归；尚未验证 `custom_debug_capture` 上板工作；尚未验证 `LOCK HERE`；尚未真实闭环锁定激光。
- 上板预期现象：烧录后先读 `MAGIC=0x4D545330` 与 `VERSION=0x00030001`；SAFE 后 OUT2 回到约 0 V；SCAN 后 OUT2 输出可调三角波；Capture Waveform 能显示 IN1/IN2/laser_error/selected_out2；LOCK HERE 在 Kp=0 时应捕获当前 `ERROR_SETPOINT` 和 `LOCK_BIAS`，OUT2 不应突跳。
- PASS 判据：bitstream 生成成功；烧录后寄存器读回正确；SAFE/SCAN 示波器回归通过；`custom_debug_capture` 返回非假数据；LOCK HERE Kp=0 无扰切换；异常能 SAFE。
- FAIL / 停止判据：Generate Bitstream 失败；读不到 MAGIC/VERSION；OUT2 不受 SAFE 控制；OUT2 接近安全边界或随机跳变；capture 数据不可用或疑似假零；LOCK HERE 输出突跳；有人准备把 OUT2 接 PZT/Scan/激光器/D2-125 输出。
- 安全边界：OUT2 只允许接示波器；禁止接 PZT、Scan、激光器电流调制、D2-125 Servo Output、D2-125 Aux Output，也禁止与任何 D2-125 输出并联。
- 下一步唯一任务：用户手动 Generate Bitstream。

## 2026-07-12 - PZT 基础稳频主线纠正与 Apply Kp 最小闭环

- 本次目标：纠正当前主线文档中“OUT2 永久只接示波器 / 禁止 PZT”的旧阶段说法，并审查最小 PZT 基础稳频闭环。
- 当前最终目标：基于 Red Pitaya 的全自动深度学习参数优化 MTS 激光稳频系统；当前阶段只做人工 `SCAN -> LOCK HERE -> P-only -> SAFE`，不做 AI 自动识峰、自动重锁、复杂 PID 或深度学习。
- 当前真实执行器边界：OUT2 的目标执行器是激光器专用 PZT / Scan 输入；SCAN 和 P_LOCK 使用同一个 PZT 接口。禁止 OUT2 接激光器电流调制输入、D2-125 Servo Output、D2-125 Aux Output，禁止任何输出端并联。
- 上位机修复：新增 `Apply Kp` 最小路径。`LOCK HERE` 只捕获锁点并以 Kp=0 进入 `MODE=3 P_LOCK`；`Apply Kp` 只修改 Kp、polarity、`LOCK_CORRECTION_LIMIT` 和 `LOCK_LIMIT`，不重新捕获 `LOCK_BIAS` 或 `ERROR_SETPOINT`。
- 正常现象：SCAN 时 OUT2 驱动 PZT 扫描并看到 MTS error 色散曲线；LOCK HERE Kp=0 后扫描停止，OUT2 保持在 `LOCK_BIAS` 附近；小 Kp 且 polarity 正确时 `LOCK_ERROR` 应减小并靠近 0，OUT2 只在 `LOCK_BIAS` 附近有限校正。
- FAIL / SAFE 条件：polarity 错误导致误差增大、OUT2 接近 limit、持续 saturation、削顶、随机跳变、通信失败、有人准备接电流调制或 D2-125 输出时，立即 `UNLOCK / SAFE`。
- 测试：`python -m pytest tests\test_custom_fpga_backend.py` 在上位机目录通过，`13 passed`。未运行 Vivado，未生成 bitstream，未烧录。
- 用户下一步：`SCAN -> 选择锁点 -> LOCK HERE -> Kp 0/4/8/16/32 小步 Apply Kp -> 判断 polarity -> 基础稳频 -> SAFE`。

## 2026-07-12 - v3LOCK-P0 update-p-lock / APPLY P 修复

- 本次阻塞：`LOCK HERE` 已能同拍捕获 `ERROR_SETPOINT` 和 `LOCK_BIAS` 并进入 `MODE=3 P_LOCK`，但旧 `p-lock`/`Apply Kp` 路径会关闭 ENABLE、重写手工 bias 或 limits，存在覆盖真实捕获锁点的风险。
- 本次修复：新增独立 `update-p-lock` 操作和 GUI `APPLY P` 按钮；正常路径只写 `KP` 与 `POLARITY`，不写 `ERROR_SETPOINT`、`LOCK_BIAS`、`CAPTURE_LOCK_POINT`、`MODE`、`ENABLE`、`KI` 或 limits。
- 安全规则：操作前后确认 `MAGIC=0x4D545330`、`VERSION=0x00030001`、`MODE=3`、`ENABLE=1`、无 saturation；Kp 仅允许 `0/4/8/16/32`；非零 Kp 下拒绝直接翻转 polarity，需先 `APPLY P --kp 0`。
- 异常处理：若读回发现 mode/enable 错误、锁点或 bias 改变、Kp/polarity 不一致或 saturation，则执行 SAFE 顺序 `KP=0 -> ENABLE=0 -> MODE=0`。
- 修改文件：`custom_fpga_scan_control.py`、`custom_fpga_backend.py`、`connection_workers.py`、`main_window.py`、`tests/test_custom_fpga_backend.py`、本日志与 `version/STATUS.md`。
- 测试：`python -m py_compile scripts\custom_fpga_scan_control.py redpitaya_lock_host\custom_fpga_backend.py redpitaya_lock_host\connection_workers.py redpitaya_lock_host\main_window.py` 通过；`python -m pytest tests` 通过，`21 passed`。
- 未运行 Vivado，未生成 bitstream，未烧录，未声明已经真实激光稳频。
- 上板预期流程：`SCAN -> 选择过零点 -> LOCK HERE -> Kp=0 -> APPLY P 4/8/16/32 -> 判断 polarity -> 异常 SAFE`。

## 2026-07-12 - BASIC LOCK 小白版界面与 Scope 黑屏修复

- 当前问题：板端 `custom_debug_capture` 已能返回真实四路数据且统计正常，但 GUI `Custom FPGA Scope` 依赖默认 pyqtgraph/Qt 主题，黑色背景下坐标轴文字、标题或曲线可能不可见；旧界面还要求用户手填 offset、amp、freq、step 和 decimation，不适合第一版“小白版 BASIC LOCK”。
- Scope 修复：`WaveformPlot` 显式设置黑色背景、亮色坐标轴 pen、亮色坐标文字、亮色标题和非黑色曲线；placeholder 保存引用，真实数据到来后隐藏；四条曲线收到数据后强制 `setVisible(True)`；显示范围优先覆盖 CH3 `laser_error` 和 CH4 `selected_out2`，避免 IN2/REF alias 把 error 压扁。
- BASIC LOCK 范围：新增顶层 `BASIC LOCK` 区，只保留 `PZT safe min voltage`、`PZT safe max voltage`、`BASIC LOCK`、`SAFE`、当前状态和候选锁点；原工程参数移动到默认隐藏的 `Advanced` 区。
- 自动参数：根据用户 PZT 安全范围计算 `offset_v=(min+max)/2`、`amp_v=abs(max-min)/2`、`freq_hz=10`、`step_counts=1`、`capture_length=2048`、`capture_decimation=round(125000000/(freq_hz*capture_length))`，并限制在 Red Pitaya DAC 与用户 PZT 范围内。
- 候选规则：只使用当前 capture 的 CH3/CH4，做轻量平滑、基线去除、MAD/局部差分噪声估计、非边缘 sign crossing、局部斜率和局部 Vpp 评分；不使用历史 CSV、固定峰位、固定 `LOCK_BIAS` 或历史实验电压。
- SAFE 条件：PZT min>=max、超出 DAC +/-1 V、PD/error/OUT2 全零、OUT2 越过用户 PZT 范围、saturation、无有效候选、通信失败或用户拒绝候选时，进入或提示 SAFE。
- 测试：`py_compile` 通过；`python -m pytest tests` 通过，`28 passed`。
- 未运行 Vivado，未生成 bitstream，未烧录，尚未证明真实基础稳频完成。
- 用户下一步：只输入 PZT safe min/max，点击 `BASIC LOCK`，确认候选过零点后观察 `LOCK HERE -> APPLY P4 -> MONITOR`，异常立即 `SAFE`。
## 2026-07-12 - BASIC LOCK 联调阻塞修复

- 本次目标：把已有 BASIC LOCK 界面补到可联调的最小闭环路径，优先处理启动寄存器状态为空、`custom_debug_capture not available` 和 BASIC LOCK 队列被 SAFE 打断的问题。
- 修改代码：仅上位机 GUI 与 pytest；未修改 RTL、testbench、Vivado project；未运行 Vivado、未生成 bitstream、未烧录。
- 修复内容：启动后自动执行只读 `status` 探测，显示 MAGIC / VERSION / MODE / ENABLE / STATUS / OUT2；失败时写明通信、bitstream、base address 或 register bank 原因。
- 修复内容：BASIC LOCK 内部 `SAFE` 步骤不再清空自身队列，流程可继续 `SAFE -> SCAN -> CAPTURE -> CANDIDATE_FOUND -> CAPTURE_LOCK_POINT -> P_LOCK`；手动 `SAFE` 仍立即中止流程。
- 修复内容：`custom_debug_capture` 无点返回时明确显示需要 `CAPTURE_CTRL / CAPTURE_STATUS / CAPTURE_DATA_CH1..CH4`，不伪造波形，也不把单点 status 读数当作四通道波形替代。
- 安全收敛：LOCK HERE 成功后停在 `MODE=3 P_LOCK` 且 `Kp=0`，后续 Kp 需要用户手动 `APPLY P`；不启用 Ki/PI，不做自动识峰、自动重锁、FSM 或 AI。
- 尚未完成：尚未真实上板验证 BASIC LOCK 完成激光稳频；真实 PASS 仍需要用户在板上确认 capture 返回真实四通道数据、LOCK HERE 无跳变、小 Kp 方向正确、异常可 SAFE。
