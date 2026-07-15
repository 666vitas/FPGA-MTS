# 开发日志

## 2026-07-14 - v3LOCK-P0 Host Lock Point Selector 最小审查与修复

- 执行 Agent：Claude Code。本轮只改上位机，不改 RTL、不运行 Vivado、不生成 bitstream、不烧录。
- 修改文件：`main_window.py`（修复重复 setVisible）、`tests/test_custom_fpga_backend.py`（修复断言+新增 11 项测试）、`../../version/STATUS.md`、本日志。

**问题背景：**
- `resolve_lock_point_selection()` 已在 `main_window.py` 中完成实现（CH1 峰搜索 + CH3 过零解析 + CH4 ramp 方向判断），但：
  1. 缺少直接单元测试（旧测试只覆盖 `resolve_target_transition`，不含 CH1 峰搜索和 ramp direction）
  2. `_render_custom_capture_payload` 在新 capture 时清除 `pending_lock_point`（正确行为），但旧测试错误期望它在 render 后仍存在
  3. 旧测试在 X 轴为 "OUT2 counts" 默认值时使用 time 坐标模拟点击，坐标转换错误
  4. `_update_lock_point_markers` 中存在一行重复的 `setVisible(False)`

**修复方式：**
- `main_window.py` line 1719-1720：删除重复的 `custom_target_window_region.setVisible(False)`
- 修正三处 GUI 测试的 click 坐标（改用 OUT2 counts 而非 time）
- 添加 11 项 `resolve_lock_point_selection` 单元测试：
  - `test_resolve_lock_point_from_ch1_peak_to_ch3_zero_crossing`：基本 CH1 峰→CH3 过零，ramp rising
  - `test_resolve_lock_point_prefers_max_slope_zero_crossing`：多过零选 |dError/dOut2| 最大
  - `test_resolve_lock_point_prefers_closer_when_slopes_similar`：斜率接近选离峰更近
  - `test_resolve_lock_point_detects_ramp_rising` / `_falling`：ramp 方向检测
  - `test_resolve_lock_point_rejects_when_ramp_direction_unavailable`：CH4 平坦拒绝
  - `test_resolve_lock_point_rejects_no_zero_crossing`：无过零拒绝
  - `test_resolve_lock_point_rejects_outside_pzt_safe_range`：OUT2 越界拒绝
  - `test_resolve_lock_point_rejects_click_near_edge`：边缘点击拒绝
  - `test_resolve_lock_point_rejects_on_saturated_flag`：saturated 拒绝
  - `test_resolve_lock_point_result_contains_all_required_fields`：字段完整性
- `test_pending_lock_point_cleared_on_new_capture`：验证新 capture 清除旧 pending
- `test_lock_here_requires_confirmed_lock_point_not_pending_candidate`：修正断言顺序
- `test_confirm_lock_point_promotes_pending_zero_crossing_only`：修正断言+字段检查

**测试命令：**
```bash
cd E:\new\fpga_lock\v94\software\redpitaya_lock_host
python -m pytest tests
python -m py_compile redpitaya_lock_host\main_window.py
python -m py_compile redpitaya_lock_host\waveform_plot.py
python -m py_compile redpitaya_lock_host\custom_fpga_backend.py
python -m py_compile scripts\custom_fpga_scan_control.py
```

**测试结果：** 待用户手动运行（VM workspace 不可用）

**用户上板操作顺序：**
1. 重启上位机
2. Probe Registers -> Status -> SAFE -> SCAN
3. Capture Waveform
4. Lock View X axis 选择 OUT2 counts
5. 勾选 Select Target Transition
6. 点击 CH1 / PD 目标峰附近
7. 检查 target marker 和 zero marker
8. Confirm Lock Point
9. **暂时不要急着 LOCK HERE**，先把截图和 selected lock point 参数发给 GPT 审查

**安全边界：**
- OUT2 只允许接激光器专用 PZT / Scan 输入
- 禁止接激光器电流调制、D2-125 Servo Output、D2-125 Aux Output、任何并联输出
- PZT safe range 在 Red Pitaya DAC ±1 V 内
- saturation、通信失败、MAGIC/VERSION 异常、OUT2 越界、反馈方向疑似错误时必须 SAFE

## 2026-07-14 Claude Code Takeover — Codex 遗留问题修复

- 执行 Agent：Claude Code（接管 Codex 的未完成修复）。本轮只改上位机，不改 RTL/Vivado/bitstream/寄存器。
- 修改文件：`main_window.py`、`tests/test_custom_fpga_backend.py`。另修改 `../../AGENTS.md`、`../../version/STATUS.md`、本日志。删除 `../../before_claude_takeover.patch`。

**接管修复四项：**

1. **`_find_and_render_basic_candidates()` 语义修复**：删除自动选择 `pending_lock_point` 的代码块（约 30 行）。自动候选检测只负责显示 candidates，不再写入 `pending_lock_point`。`pending_lock_point` 仅由用户点击 `_on_custom_scope_clicked` 设置。这解决了自动检测与用户手动选点之间的语义冲突。

2. **候选 marker 坐标修复**：`_find_and_render_basic_candidates` 中 marker 位置从硬编码 `data["time_s"][candidate.index]` 改为 `self._scope_x_value(candidate.index)`，标记跟随 X 轴（OUT2 counts / time(ms)）。`_refresh_scope_display` 已有 `_update_lock_point_markers` 调用，X 轴切换时自动刷新。

3. **ramp / delta_out2 阈值修复**：Codex 将三处阈值从 `abs(…) < 0.5`（整数 count 语义）改为 `abs(…) <= 1e-9`（浮点 epsilon）。OUT2 是整数 DAC counts，0.5 counts/sample 是合理的最小 ramp 检测阈值，`1e-9` 会使平坦/噪声 ramp 被错误判为有效。三处已统一回退。

4. **AGENTS.md 清理**：移除"Project Skill"段（引用已被用户删除的 `.agents/skills/mts-redpitaya-project/`），替换为简短说明。

5. **`before_claude_takeover.patch` 已删除**。

6. **测试修正**：`test_custom_scope_render_payload_shows_curves_range_and_candidate` 断言从 `pending_lock_point is not None` 改为 `is None`，与修复后语义一致。

**修改的具体行（main_window.py）：**
- `_find_and_render_basic_candidates` (~line 2106-2137)：删除 `try: selected = resolve_lock_point_selection(...)` 至 `except Exception: self.pending_lock_point = None` 代码块
- `_find_and_render_basic_candidates` marker 位置 (~5 行)：`float(data["time_s"][candidate.index])` → `self._scope_x_value(candidate.index)`
- `_select_manual_lock_target` (~3 处)：`abs(median_ramp) <= 1e-9` → `abs(median_ramp) < 0.5`、`abs(delta_out2) <= 1e-9` → `abs(delta_out2) < 0.5`

**未修改：** RTL、testbench、Vivado 工程、寄存器语义、bitstream、LOCK HERE/APPLY P 语义、`_on_custom_scope_clicked`、`_confirm_pending_lock_point`、`_render_custom_capture_payload`。

**测试命令：**
```bash
cd E:\new\fpga_lock\v94\software\redpitaya_lock_host
.\.venv\Scripts\python.exe -m pytest -q tests/test_custom_fpga_backend.py
.\.venv\Scripts\python.exe -m pytest -q tests
.\.venv\Scripts\python.exe -m py_compile redpitaya_lock_host\main_window.py redpitaya_lock_host\waveform_plot.py redpitaya_lock_host\custom_fpga_backend.py redpitaya_lock_host\connection_workers.py scripts\custom_fpga_scan_control.py
```

**测试结果：** 待用户手动运行。

**结论：** Lock Point Selector 上位机代码与测试完成。即使全部软件测试通过，结论也只能是"等待用户真实 GUI、capture 和人工选点验证"。下一步是上板人工操作 Lock Point Selector 完整工作流（Capture → 选点 → Confirm → 截图审查），确认 marker 坐标、pending/selected lock point 参数正确后再考虑 LOCK HERE。
- 不允许声称已经完成锁定
- 不允许声称已经替代 D2-125
- 本轮未修改 RTL、未运行 Vivado、未生成 bitstream、未烧录

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
## 2026-07-13 Codex / Claude Code 统一接管与上位机交接规则

- 本次目标：只统一 Codex 与 Claude Code 的项目接管、修改、记录和实验交接规则；Codex 为默认执行 Agent，Claude Code 仅在 Codex 额度不足或用户明确指定时接管。
- 修改文件：新增根目录 `AGENTS.md`；更新 `version/CURRENT_REVIEW_MANIFEST.md`、`version/STATUS.md`、`version/v3/DEVELOPMENT_LOG.md` 与本日志。未修改任何上位机 Python、RTL、Vivado 工程、测试、寄存器、bitstream 或历史版本路径。
- 上位机状态：用户截图已证明 `custom_debug_capture` 返回四通道非零数据，Custom FPGA Scope 已从空白 plot 修复为可显示真实 capture 曲线；当前问题是四路共用原始 Y 轴时 OUT2 大偏置压缩其他通道，界面尚未达到台式示波器式简易分层。
- 规则：纯 GUI 修改不触发 Vivado、bitstream 或烧录要求；没有用户实验反馈时只记录“等待验证”。每次上位机相关修改完成后，更新 `STATUS.md` 快照并向本日志末尾追加。
- 验证：本次仅审查文档和 git 状态；未运行 Vivado、未生成 bitstream、未烧录、未做新的板上实验。
- 用户实验操作：重新启动上位机，执行 `Probe Registers -> Status -> SCAN -> Capture Waveform`，确认真实曲线可见并记录布局现象。
- PASS：四通道 capture 数据非零且 GUI 曲线可见。FAIL：capture 已返回但 plot 空白、曲线不可辨识、通信/寄存器身份异常或 OUT2 异常。
- 必须 SAFE：OUT2 越界/接近 limit、saturation、通信失败、MAGIC/VERSION 异常、异常跳变、反馈方向疑似错误或准备连接禁止端口/并联输出时。
- 下一步唯一任务：设计并实现示波器式三/四通道显示层。

## 2026-07-13 Codex 当前状态文档清理

- 执行 Agent：Codex。本次只修规则和状态文档；未修改任何上位机 Python、测试、RTL、Vivado 工程、寄存器、bitstream 或历史版本目录。
- 清理旧结论：将 `custom_debug_capture`、`VERSION=0x00030001` 和 BRAM 修复的“仍等待 Vivado/bitstream/烧录”文字降为已被后续验证覆盖的历史阶段记录，不再作为当前 GUI 任务待办。
- 当前真实验证等级：synthesis / implementation / timing 已完成；bitstream 已生成并烧录；`MAGIC=0x4D545330`、`VERSION=0x00030001`；四通道 capture 非零，GUI 已可显示真实曲线。
- 未验证：HOLD、LOCK HERE 真实切换、P_LOCK 真实 PZT 闭环、polarity/小 Kp、长时间稳频、FSM 自动重锁与 AI 参数优化。当前不启用 `KI`、integral、PI_LOCK 实验主线、自动 polarity、自动增加 Kp、自动重锁或 AI 自动识峰。
- 本次未运行测试、未运行 Vivado、未生成 bitstream、未烧录。
- 下一步唯一任务：实现示波器式三/四通道显示层。

## 2026-07-13 Custom FPGA Scope 简易台式示波器式分层显示

- 执行 Agent：Codex。本次只改上位机显示层、已有测试和状态/日志；未修改 RTL、仿真、Vivado 工程、寄存器、custom capture 协议、bitstream 或历史版本目录。
- 本次问题：四路原始 counts 直接共用一个 Y 轴时，CH4/OUT2 的大直流偏置压缩 CH1/PD 和 CH3/laser_error，GUI 虽有曲线但不便实验观察。
- 修复：单一紧凑 Scope 采用显示副本 `display_y = (raw_y - display_center) * display_gain + vertical_offset`。默认 CH4 上、CH3 中、CH1 下、CH2 隐藏；新增 `Scope Default`；每通道有 Visible、Auto scale、Scale、Vertical position、Reset display。center/gain 从当前 capture 的中位数与稳健范围计算，不写死实验 counts。
- 原始数据边界：capture、stats、保存、marker、点击 index/time 均保持原始数据；只有曲线显示数据变换。完整 raw min/max/mean/Vpp counts 与 V ideal 放在 stats tooltip，主区域只保留 MODE、OUT2、correction_limit、CH1/CH3/CH4 Vpp 与现有安全告警。
- 测试：`.venv\Scripts\python.exe -m pytest tests` 通过，`55 passed`；`py_compile` 通过。未运行 Vivado、未生成 bitstream、未烧录。
- 用户验证：`Probe Registers -> Status -> SCAN -> Capture Waveform`，确认三路分层、CH2 默认隐藏，点击 CH1 后 target/zero marker 时间正确；`Scope Default` 可恢复默认布局。
- PASS：CH1/CH3 不再被 OUT2 压缩，显示控制不改 raw capture/stats/marker，`Scope Default` 正常。FAIL：显示控件影响原始数据或 FPGA 参数、marker 偏移、图空白或 OUT2 异常。
- 必须 SAFE：OUT2 越界/接近 limit、saturation、通信或 MAGIC/VERSION 异常、异常跳变、反馈方向疑似错误或准备连接禁止端口/并联输出时。
- 下一步唯一任务：用户上板验证 Custom FPGA Scope 分层显示与人工选点 marker 映射。

## 2026-07-15 上位机测试尾部污染与 time(ms) target window 修复

- 初始 Git 状态：`HEAD=b061a3b22f8fd1888c6a8456dfbd5fd7b497ee7a`；工作区处于既有的 `main` interactive rebase 编辑状态，开始修改前无未提交改动。本轮未执行 `rebase --continue`、`rebase --abort`、commit 或 push。
- 缩进错误根因：`tests/test_custom_fpga_backend.py` 尾部错误合并后留下 5 空格缩进的 `return`、`finally` 后非法缩进的 `return`、一段脱离函数头的旧 `test_custom_scope_reset_view_restores_auto_range` 函数体，以及两个重复测试定义。
- 删除的重复定义：第二份 `test_single_plot_curves_rendered_with_data_after_capture`；第二份 `test_default_ch2_hidden_ch1_ch3_ch4_visible`。三个目标测试各保留一份完整定义。
- `main_window.py` 修复：OUT2 counts 轴下 region 半宽保持为 `target_window_counts`；time(ms) 轴下根据目标索引相邻样本计算局部 `counts/ms`，再换算 `window_ms = abs(target_window_counts / local_counts_per_ms)`。局部速度无效或样本不足时隐藏 region，marker 仍由 `_scope_x_value(index)` 定位。
- 新增最小测试：同时检查默认 OUT2 counts 轴和 time(ms) 轴的 region 单位、region 中心与 target marker 一致，以及时间轴宽度不会出现数量级膨胀。
- AST 重复检查：`test functions: 64`，`duplicates: []`。
- `python -m tabnanny tests/test_custom_fpga_backend.py`：通过，无输出。
- `python -m py_compile tests/test_custom_fpga_backend.py redpitaya_lock_host/main_window.py`：通过。
- `python -m pytest --collect-only -q tests/test_custom_fpga_backend.py`：通过，`64 tests collected`。
- targeted pytest：`7 passed, 57 deselected`。
- `python -m pytest -q tests/test_custom_fpga_backend.py`：`64 passed`。
- `python -m pytest -q tests`：`70 passed, 4 subtests passed`。
- 附件指定的完整 `py_compile` 文件集合：通过；`git diff --check`：无输出。
- 本轮只完成上位机软件验证；真实 GUI 和上板实验尚未执行，等待验证。未修改 RTL、Vivado、寄存器或 bitstream，未运行 Vivado，未生成 bitstream，未烧录。
- 用户验证：启动上位机后执行安全的 capture 显示检查，在 OUT2 counts 与 time(ms) 间切换，确认 target/zero marker 不偏移，target window 中心与 target marker 一致，时间轴窗口宽度合理。
- PASS：两种 X 轴下 marker/region 正确且 BASIC LOCK capture 后仍停在 `CANDIDATE_FOUND` 等待人工点击和 Confirm。FAIL：region 数量级异常、marker 偏移、自动 Confirm/LOCK HERE，或任何 OUT2 越界、saturation、通信/MAGIC/VERSION 异常。必须 SAFE：出现上述硬件异常、异常跳变、反馈方向疑似错误，或准备连接禁止端口/并联输出时，立即停止并执行 SAFE。

## 2026-07-15 - 专用数字示波器与 Direct ERROR 人工锁点

### 执行信息

- Agent：Codex。
- branch：detached HEAD；当前提交与 GitHub `main` 一致。
- initial HEAD：`d63a2b7610865d1ee8274e640ec485211a891a74`。
- origin/main：`d63a2b7610865d1ee8274e640ec485211a891a74`；首次 fetch TLS EOF，随后 `git ls-remote` 实时确认。
- initial working tree：clean，无 rebase/merge；未自动 commit 或 push。

### 本轮目标

统一 Codex / Claude Code 的长期开发、验证、状态记录和交接流程；将上位机主实验界面收敛为 FPGA-MTS 专用数字示波器，同时保留并强化人工选点、Confirm 和最小 P-only 安全路径。

### 修改前问题

主界面仍是左侧多页开发调试面板加右侧 plot；正常实验视图显示 raw counts、原始浮点 gain 和无量纲 position；默认 X 轴为 OUT2 counts；人工选点仅有 CH1 assisted 入口，操作按钮分散在 Advanced 中；长期流程文件未完整固化证据等级、分层验证和标准交接格式。

### 根本原因

现有 UI 是多轮 bring-up 功能逐步叠加形成，工程参数、寄存器诊断和实验操作没有明确分层；显示副本已有基础，但缺少物理 volts/div 模型和主界面电压摘要；选点 resolver 只有“CH1 peak -> nearby CH3 zero”路径，缺少实验用户直接点击 CH3 过零的入口。

### 修改文件

- `AGENTS.md`
- `AI_REVIEW_README.md`
- `software/redpitaya_lock_host/redpitaya_lock_host/main_window.py`
- `software/redpitaya_lock_host/tests/test_custom_fpga_backend.py`
- `version/STATUS.md`
- `software/redpitaya_lock_host/docs/DEVELOPMENT_LOG.md`

### 关键实现

- `AGENTS.md`：固化读取顺序、Git 安全、证据等级、最小开发、七层验证、文档职责和标准交接；继续明确不使用自定义 skill。
- `AI_REVIEW_README.md`：收敛为新 Agent 简明入口；动态状态只指向 STATUS 顶部，历史只指向开发日志，严格模板不覆盖当前代码事实。
- `format_scope_voltage()` / `format_volts_per_div()` / `choose_scope_volts_per_div()`：提供 ideal counts-to-voltage 显示和 1/2/5 volts/div 档位。
- `_build_ui()`：主界面改为顶部四通道卡、中间 Time Scope、底部 capture/scan/lock 操作栏；原连接、寄存器、counts 和诊断面板整体移入默认折叠的 `Advanced / Engineer Details`。
- `_build_plots()`：默认 `time (ms)`，CH4 黄色、CH3 蓝色、CH1 绿色、CH2 橙色；每通道独立 Visible、Volts/Div、Position、Channel Auto 和 ground line；raw gain 控件只留在 Engineer Details。
- `_update_channel_cards()` / `_update_scope_timebase_summary()`：主界面只显示 Vpp/min/max/mean/DC offset、mV/div/V/div、time/div、window、sample rate、scan period 和 cycles；硬件校准限制写入 tooltip。
- `_auto_set_scope_channel()` / `_apply_scope_default_layout()`：按当前 Vpp 选 volts/div 并恢复 CH4/CH3/CH1 分层，保持 CH2 隐藏；不改 raw capture、FPGA、scan 或 lock 参数。
- `resolve_direct_error_zero_crossing()`：在点击附近选择最近有效 CH3 过零，检查 capture edge、局部 slope、CH4 ramp direction、PZT safe range 和 saturation，只返回 pending 所需字段。
- `_on_custom_scope_clicked()`：默认 Direct ERROR；Advanced 可切换 CH1 Peak Assisted。点击只创建 pending，Confirm 才创建 selected。
- `_start_custom_fpga_operation()` / `_on_polarity_selection_changed()`：首次 `LOCK HERE` 强制 Kp=0；非零已应用 Kp 时阻止直接改变 polarity；非零 APPLY P 需已有成功 Kp=0 LOCK HERE。

### 保留行为

保留 raw capture、CSV/PNG、time/index、MAGIC/VERSION、saturation、OUT2 safe range、pending/selected、Confirm、LOCK HERE 守卫、Kp 0/4/8/16/32、BASIC LOCK `CANDIDATE_FOUND` 停点、新 capture 清除选择、Capture Once、Live 防重入、失败停 Live 和窗口关闭 SAFE。未增加自动 Confirm、自动 LOCK HERE、自动 APPLY P、自动 Kp/polarity 或自动重锁。

### 安全边界

未修改 RTL、Vivado 工程、寄存器地址/语义、`MAGIC`、`VERSION` 或 bitstream；未运行 Vivado、未生成或烧录 bitstream。OUT2 只允许连接激光器专用 PZT / Scan 输入；禁止电流调制、D2-125 Servo/Aux Output 和任何输出端并联。通信、身份、saturation、OUT2 越界、异常跳变或方向疑似错误时立即 SAFE。

### 测试命令

```powershell
.\.venv\Scripts\python.exe -m tabnanny redpitaya_lock_host\main_window.py tests\test_custom_fpga_backend.py
.\.venv\Scripts\python.exe -m py_compile redpitaya_lock_host\main_window.py tests\test_custom_fpga_backend.py
.\.venv\Scripts\python.exe -m pytest --collect-only -q tests/test_custom_fpga_backend.py
.\.venv\Scripts\python.exe -m pytest -q tests/test_custom_fpga_backend.py -k "scope or voltage or channel or lock_point or confirm or lock_here or safety"
.\.venv\Scripts\python.exe -m pytest -q tests/test_custom_fpga_backend.py
.\.venv\Scripts\python.exe -m pytest -q tests
.\.venv\Scripts\python.exe -m py_compile redpitaya_lock_host\main_window.py redpitaya_lock_host\waveform_plot.py redpitaya_lock_host\custom_fpga_backend.py redpitaya_lock_host\connection_workers.py scripts\custom_fpga_scan_control.py
git diff --check
```

### 测试结果

- tabnanny：通过，无输出。
- target py_compile：通过。
- collect：`72 tests collected`。
- targeted：最终 `39 passed, 33 deselected`。
- current file：`72 passed`。
- full tests：`78 passed, 4 subtests passed`。
- full py_compile：通过。
- `git diff --check`：无输出。
- 1600x950 离屏布局截图：三段式布局无明显重叠；离屏字体缺失显示方框，不作为真实 Windows GUI 验证。

### 用户已验证

[USER GUI VERIFIED] 既有真实 GUI 已显示 Red Pitaya time(ms) capture、CH4 重复三角扫描、CH3 非零 laser_error、CH1 非零 PD/IN1，并可在约 100 ms 内观察多个周期。本轮新布局尚未由用户验证。

### 尚未验证

新 GUI 的真实 Windows 字体/DPI/交互、ideal 电压与 Keysight 一致性、Direct ERROR 真实点击、pending/Confirm、LOCK HERE、Kp=0 无跳变、polarity、非零 Kp P-only、真实激光闭环和长期稳频均未验证。

### 当前证据等级

工作流、专用示波器代码、Direct ERROR、Confirm/Kp/polarity 守卫为 `[AUTOMATED VERIFIED]`；既有真实 capture 显示为 `[USER GUI VERIFIED]`；真实锁点与闭环为 `[NOT VERIFIED]`。

### 当前阶段结论

`CODE PASS / WAITING GUI`

### 下一步唯一动作

用户在真实 Windows GUI 和当前 Red Pitaya capture 下使用默认 `Direct ERROR Zero Crossing` 选择一个 CH3 过零点并点击 `CONFIRM`，只检查 marker、候选电压和 selected 参数，不执行 `LOCK HERE`。

## 2026-07-15 v3LOCK-P0 上位机 count/电压映射审查与校准前置

- 本轮只读追踪 `custom_debug_capture -> CAPTURE_DATA_CH1..CH4 -> /dev/mem -> to_signed14 -> backend payload -> main_window`。14-bit signed counts 经 FPGA sign-extend 读回，helper 恢复 signed14，backend 不改变 capture 数值，GUI `custom_scope_data` 保留 raw counts；CSV 保存 nominal `time_s` 和四路 counts。
- `COUNTS_PER_VOLT` 在 active backend 与 helper 中均为 `8191.0`；状态 JSON、channel card、volts/div 和锁点 PZT 值都由 `count/8191` 产生。Red Pitaya 官方对 STEMlab 125-14 LV raw ADC 的理想 divisor 为 8192；当前 8191 是 host 安全限幅约定，不是板卡实测校准。
- GUI 波形 Y 轴是 `Channel position (div)`；每通道执行 display-only center/gain/position，不修改 raw count。主界面默认隐藏 counts，只显示 nominal mV/V；tooltip 虽注明 hardware calibration not verified，但部分状态/锁点文本直接写 `V`，仍有被误读为真实电压的风险。
- 当前 custom ADC/DAC 路径没有 per-channel gain、offset、LV/HV jumper、frequency equalization 或 load correction。CH1/CH2 是 raw ADC counts；CH3/CH4 是 pre-DAC internal counts。真实 OUT1/OUT2 电压必须由 scope 在当前负载下实测；50 ohm 与 Hi-Z/PZT 结果不可混用。
- `time_s=index*decimation/125e6` 的秒/ms/sample-index 换算一致，但属于 125 MHz nominal relative time；GUI scan label 是命令值，不替代 scope period。
- 当前可信边界：raw counts、通道身份、寄存器/JSON/GUI 数值传递和相对波形形状可作为代码链证据；GUI 绝对 mV/V、ADC 输入物理 V、OUT1/OUT2 物理 V 均为 `[NOT VERIFIED]`。
- 最小硬件校准不新增功能：复用 `MODE=2 HOLD`，只接 OUT2 到 scope，对 `0, +/-1024, +/-2048, +/-4096 counts` 和计划 scan min/center/max 做 exact-count/readback/scope 多点测量，拟合 `V=a*C+b`，得到 `DAC_count_per_volt_OUT2=1/a` 与 `zero_offset_OUT2=b`。
- 必须记录 scope 50 ohm/Hi-Z、探头、线缆、每点 `HOLD_VALUE`、`OUT2_MONITOR`、CH4 count、scope mean V、重复性、saturation。异常、越界、身份/通信失败、随机跳变或 readback 不符立即 SAFE。
- 软件回归：`tabnanny`、`py_compile` 通过；`75 tests collected`；targeted `31 passed, 44 deselected`；当前文件 `75 passed`；完整 `81 passed, 4 subtests passed`。pytest 仅有无法创建 `.pytest_cache` 的 sandbox warning。
- `git diff --check` 通过，无输出。
- 未修改 Python、RTL、Vivado、寄存器或 bitstream；未运行 Vivado；未进行新的 GUI/板卡/闭环实验。
- 下一步唯一动作：完成 OUT2 MODE=2 HOLD 的 scope exact-count 校准；在 count/V 和 zero offset 得到前，不执行 LOCK HERE 或非零 Kp。
