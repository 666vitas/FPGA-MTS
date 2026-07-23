# v3 开发日志

## 2026-07-12 - v3LOCK-P0 上位机准实时观察与人工锁点工作台

- 本次目标：只修改上位机 Python 和既有记录，完成用于 10 Hz PZT 扫描的“实验工作台”，不是高速示波器，也不声称已经真实激光锁定。
- 修改文件：`software/redpitaya_lock_host/redpitaya_lock_host/main_window.py`、`software/redpitaya_lock_host/tests/test_custom_fpga_backend.py`、`version/STATUS.md`、`version/v3/DEVELOPMENT_LOG.md`、`software/redpitaya_lock_host/docs/DEVELOPMENT_LOG.md`。
- 未修改：RTL、Vivado project、bitstream、寄存器地址、寄存器语义均未修改；未新增 AI、自动重锁 FSM、自动 PID 调参或自动 polarity 判断。
- 准实时采集：新增 `Start Live`、`Stop Live`、`Capture Once` 与 `refresh interval 500/1000/2000 ms`，默认 `1000 ms`。Live 使用 `capture_in_flight` 防重入，流程为 capture 完成 -> GUI 更新/安全检查 -> single-shot 延时 -> 下一次 capture；capture/SSH/MAGIC/VERSION/saturation/OUT2 safe range/连续 LOCK_ERROR 异常或窗口关闭会停止 Live。
- 四通道显示：右侧改为四个独立 `WaveformPlot`：CH1 IN1/PD、CH3 OUT1/laser_error、CH4 OUT2/selected_out2、CH2 IN2/REF。每通道有 `Visible`、`Auto Y`、`Scale counts/div`、`Center counts`、`Reset`；这些控件只改变显示范围和可见性，不改 capture 原始数据，不写 FPGA。
- 视图模式：`Lock View` 默认显示 CH1/CH3/CH4、隐藏 CH2，capture length 默认 2048，并按 scan freq 估算 decimation 以覆盖约一个扫描周期，同时显示当前 capture 时间窗；`REF Debug` 默认只显示 CH2，decimation 仅 1/2/4/8，并提示不能同时完整显示 10 Hz 慢速扫描周期。
- 人工锁点：新增 `Select Target Transition` 与 `Confirm Lock Point`。用户在 CH1/PD 图点击目标峰附近后，GUI 记录 clicked index/time/OUT2，并在附近窗口搜索 CH3/error 有效零交叉；有效性检查包括局部 Vpp、斜率、capture 边缘、OUT2 安全范围和 saturation。找到后只生成 pending lock point，并在四通道画 target marker 与 resolved zero-crossing marker；只有 `Confirm Lock Point` 更新 `selected_lock_point`。
- 最小 P-only：`LOCK HERE` 必须已有 confirmed lock point；随后等待 OUT2 到 target window，触发 FPGA `CAPTURE_LOCK_POINT`，由 FPGA 捕获 `ERROR_SETPOINT` 和 `LOCK_BIAS` 并进入 `MODE=3 P_LOCK`，Kp 从 0 开始。`APPLY P` 不覆盖锁点，只允许用户手动 Kp `0/4/8/16/32` 与 polarity；Ki/Kd 禁用，不自动加 Kp，不自动判断 polarity，不自动重锁。
- GUI 说明：补充 offset-v、amp-v、freq-hz、step-counts、limit-counts、hold-v、Kp manual step、polarity、correction-limit-counts、target-window-counts、capture-length、capture-decimation、LOCK_BIAS、ERROR_SETPOINT、LOCK_ERROR 等简短 tooltip/状态说明。
- 测试结果：在 `software/redpitaya_lock_host` 下运行 `.venv\Scripts\python.exe -m pytest tests`，结果 `42 passed`；运行 `.venv\Scripts\python.exe -m py_compile scripts\custom_fpga_scan_control.py redpitaya_lock_host\custom_fpga_backend.py redpitaya_lock_host\connection_workers.py redpitaya_lock_host\main_window.py redpitaya_lock_host\waveform_plot.py` 通过。
- 上板预期现象：SCAN 后 Lock View Live 能看到 CH1/CH3/CH4，CH2 默认隐藏；点击 CH1 目标峰附近后，CH3 附近解析出过零并显示 marker；Confirm 后 `LOCK HERE` 进入 P_LOCK Kp=0；之后仅用户手动 `APPLY P` 小步增益。
- PASS 判据：Live 不重入，Stop 后不继续 capture；capture 完成后才排下一轮；四通道显示控制不改原始数据；无过零拒绝 Confirm；未 Confirm 阻止 LOCK HERE；APPLY P 不覆盖 `LOCK_BIAS` / `ERROR_SETPOINT`。FAIL 判据：收到 capture 但不显示、Live 重入、未 Confirm 可 LOCK HERE、APPLY P 重新捕获或覆盖锁点、任何 RTL/Vivado/bitstream 被改动。
- 下一步唯一任务：用户上板执行 `SCAN -> Lock View Live/Capture Once -> CH1 点击目标峰附近 -> Confirm Lock Point -> LOCK HERE -> 手动 APPLY P 0/4/8/16/32 -> 判断 polarity -> 异常 SAFE`，记录真实 capture 和 LOCK HERE 现象。

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
- RTL 审查结论：`MODE=1 SCAN` 进入 `selected_out2 -> DAC B / OUT2`；`CAPTURE_LOCK_POINT` 同拍捕获 `ERROR_SETPOINT` 和 `LOCK_BIAS`；`P_LOCK` 使用 `laser_error - ERROR_SETPOINT` 后的 `LOCK_ERROR`；Kp=0 时保持捕获的 `LOCK_BIAS`；P correction 受 `LOCK_CORRECTION_LIMIT` 限制；最终 OUT2 受绝对 limit / DAC limit 限制；SAFE 退出扫描和反馈。
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
- 测试：`py_compile` 通过；`python -m pytest tests` 通过，`21 passed`。
- 未运行 Vivado，未生成 bitstream，未烧录，未声明已经真实激光稳频。
- 用户下一步：`SCAN -> 选择过零点 -> LOCK HERE -> Kp=0 -> APPLY P 4/8/16/32 -> 判断 polarity -> 异常 SAFE`。

## 2026-07-12 - BASIC LOCK 小白版界面与 Scope 黑屏修复

- 当前问题：板端 `custom_debug_capture` 已能返回真实四路数据且统计正常，但 GUI `Custom FPGA Scope` 依赖默认 pyqtgraph/Qt 主题，黑色背景下坐标轴文字、标题或曲线可能不可见；旧界面还要求用户手填 offset、amp、freq、step 和 decimation，不适合第一版“小白版 BASIC LOCK”。
- Scope 修复：显式设置黑色背景、亮色坐标轴/文字/标题和非黑色曲线；placeholder 保存引用，真实数据到来后隐藏；四条曲线收到数据后强制可见；显示范围优先覆盖 CH3 `laser_error` 和 CH4 `selected_out2`，避免 IN2/REF alias 把 error 压扁。
- BASIC LOCK 范围：顶层只保留 PZT safe min/max、`BASIC LOCK`、`SAFE`、当前状态和候选锁点；工程参数默认折叠在 `Advanced`。
- 自动参数：`offset_v=(min+max)/2`、`amp_v=abs(max-min)/2`、`freq_hz=10`、`step_counts=1`、`capture_length=2048`、`capture_decimation=round(125000000/(freq_hz*capture_length))`。
- zero crossing：只使用当前 capture 的 CH3/CH4，使用当前数据噪声估计、局部斜率和局部 Vpp 评分；不使用历史 CSV、固定峰位或固定 `LOCK_BIAS`。
- SAFE 条件：PZT 范围非法、全零/平坦 capture、OUT2 越过用户 PZT 范围、saturation、无有效候选、通信失败或用户拒绝候选。
- 测试：`py_compile` 通过；`python -m pytest tests` 通过，`28 passed`。
- 未运行 Vivado，未生成 bitstream，未烧录，尚未证明真实基础稳频完成。
## 2026-07-12 - BASIC LOCK 联调阻塞修复

- 本次只修上位机联调阻塞：启动 status 探测、BASIC LOCK 内部 SAFE 不再中断队列、capture 缺失时明确报真实 FPGA 接口不可用。
- 当前 BASIC LOCK 状态机收敛为 `IDLE -> SAFE -> SCAN -> CANDIDATE_FOUND -> CAPTURE_LOCK_POINT -> P_LOCK`，异常转 SAFE。
- LOCK HERE 成功后保持 `MODE=3 P_LOCK` 且 `Kp=0`；小步 Kp 由用户手动 `APPLY P`，不自动启用 Ki/PI。
- 未修改 RTL / Vivado project，未运行 Vivado，未生成 bitstream，未烧录，未声明真实激光稳频已经完成。
## 2026-07-13 Codex / Claude Code 统一接管与交接规则

- 本次目标：只统一 Codex 与 Claude Code 的项目接管、修改、记录和实验交接规则；Codex 为默认执行 Agent，Claude Code 仅在 Codex 额度不足或用户明确指定时接管。
- 修改文件：新增根目录 `AGENTS.md`；更新 `version/CURRENT_REVIEW_MANIFEST.md`、`version/STATUS.md`、本日志与 `software/redpitaya_lock_host/docs/DEVELOPMENT_LOG.md`。未修改 Python、RTL、Vivado 工程、约束、测试、寄存器、bitstream 或历史版本路径。
- 规则实现：两种 Agent 每次读取相同的入口、STATUS、MANIFEST、git 状态、任务关联文件和现有日志；每次只完成一个任务，不重新规划主线或扩大范围。`STATUS.md` 顶部维护当前快照，`DEVELOPMENT_LOG.md` 只在末尾追加历史；涉及上位机时同步追加上位机日志。
- 状态纠正：用户截图已证明 `custom_debug_capture` 返回四通道非零数据，当前 GUI 已能显示真实 capture 曲线；剩余问题是示波器式显示布局，不能再写成 FPGA capture 失效，也不能把纯 GUI 修改与 Vivado、bitstream、烧录混为一谈。
- 验证：仅完成文档一致性审查和 git 状态记录；未运行 Vivado、未生成 bitstream、未烧录、未进行新的硬件实验。未得到用户实验反馈的项目结论均保持“等待验证”。
- 用户实验操作：重新启动上位机后执行 `Probe Registers -> Status -> SCAN -> Capture Waveform`，观察四通道真实曲线及量程/布局。
- PASS：capture 数据非零且曲线可见。FAIL：capture 返回数据但图空白、曲线不可辨识、通信/寄存器身份异常或 OUT2 异常。
- 必须 SAFE：OUT2 越界或接近 limit、saturation、通信失败、MAGIC/VERSION 异常、异常跳变、反馈方向疑似错误，或准备连接禁止端口/并联输出时。
- 下一步唯一任务：设计并实现示波器式三/四通道显示层。

## 2026-07-13 Codex 当前状态文档清理

- 执行 Agent：Codex。本次只修规则和状态文档：更新 `AGENTS.md`、`version/STATUS.md`、`version/CURRENT_REVIEW_MANIFEST.md`，并向两份已有开发日志追加记录。
- 清理旧结论：将“`custom_debug_capture` 等待 bitstream/烧录/上板验证”、“`VERSION=0x00030001` 候选仍等待 synthesis/implementation/timing/bitstream/烧录”以及“BRAM 修复仍等待 Vivado 验证”标记为已被后续 timing PASS、bitstream、烧录、`VERSION` 读回和四通道 capture 覆盖的历史阶段记录，不再作为当前待办。
- 当前真实验证等级：synthesis / implementation / timing 已完成；bitstream 已生成并烧录；`MAGIC=0x4D545330`、`VERSION=0x00030001`；四通道 capture 非零且 GUI 可显示真实曲线。
- 仍等待验证：HOLD、LOCK HERE 真实切换、P_LOCK 真实 PZT 闭环、polarity/小 Kp、长时间稳频、FSM 自动重锁和 AI 参数优化。当前不启用 `KI`、integral、PI_LOCK 实验主线、自动 polarity、自动增加 Kp、自动重锁或 AI 自动识峰。
- 未修改代码、测试、RTL、Vivado 工程、寄存器、bitstream 或历史版本目录；未运行测试、未运行 Vivado、未生成 bitstream、未烧录。
- 下一步唯一任务：实现示波器式三/四通道显示层。

## 2026-07-13 Custom FPGA Scope 简易台式示波器式分层显示

- 执行 Agent：Codex。本次只修改上位机 GUI、已有 Python 测试和既有状态/日志记录；未修改 RTL、仿真、Vivado 工程、约束、寄存器、custom capture 协议、bitstream 或历史版本目录。
- 本次问题：四路原始 counts 共用一个 Y 轴直接叠加时，CH4/OUT2 的大直流偏置与幅度压缩 CH1/PD 和 CH3/laser_error，曲线虽可显示但不适合实验观察。
- 显示层修复：单个紧凑 `Custom FPGA Scope` 保持共享 X 时间轴，采用 `display_y = (raw_y - display_center) * display_gain + vertical_offset`。默认 CH4 上层、CH3 中层、CH1 下层，CH2 默认隐藏；`Scope Default` 可恢复该布局。每通道保留 Visible、Auto scale、Scale、Vertical position、Reset display，center/gain 按当前 capture 的中位数和稳健 2%~98% 范围自动估算。
- 数据边界：`custom_scope_data`、CSV 保存、stats、LOCK HERE 选点与 marker 均继续使用原始 capture；仅 PlotDataItem 使用显示副本。OUT2 的大直流中心仅在显示层移除，完整原始 min/max/mean/Vpp counts 与 V ideal 仍在 stats tooltip 中。
- 修改文件：`software/redpitaya_lock_host/redpitaya_lock_host/main_window.py`、`software/redpitaya_lock_host/tests/test_custom_fpga_backend.py`、`version/STATUS.md`、本日志、`software/redpitaya_lock_host/docs/DEVELOPMENT_LOG.md`。
- 测试：在上位机 `.venv` 运行 `python -m pytest tests`，`55 passed`；`python -m py_compile redpitaya_lock_host/main_window.py redpitaya_lock_host/waveform_plot.py` 通过。未运行 Vivado、未生成 bitstream、未烧录。
- 用户验证：`Probe Registers -> Status -> SCAN -> Capture Waveform`；确认 CH4/CH3/CH1 三层、CH2 默认隐藏；点击 CH1 后确认 target/zero marker 时间不偏移；必要时点击 `Scope Default` 恢复布局。
- PASS：CH1/CH3 不再被 OUT2 压缩，原始 stats/保存/选点不变，`Scope Default` 正常。FAIL：显示控件改写原始数据或参数、marker 偏移、capture 返回数据但图空白，或 OUT2 异常。
- 必须 SAFE：OUT2 越界或接近 limit、saturation、通信失败、MAGIC/VERSION 异常、异常跳变、反馈方向疑似错误或准备连接禁止端口/并联输出时。
- 下一步唯一任务：用户上板验证 Custom FPGA Scope 分层显示与人工选点 marker 映射。

## 2026-07-15 v3LOCK-P0 RTL/上位机电压映射只读审查与硬件校准方案

- 本轮目标：不开发新锁定功能，只审查 ADC -> mixer -> LPF -> `laser_error` -> OUT1、`selected_out2` -> OUT2，以及 FPGA register -> backend -> GUI -> physical voltage 的完整数据链；为第一次 P-only 前的硬件校准建立最小 SOP。
- Git 基线：detached HEAD；`HEAD=origin/main=9417832e147f4d87b142ba608c192a77f304a554`。初始工作区已有用户未跟踪 `.claude/`，已保留且未纳入任务。
- RTL 结论：ADC 从 `adc_dat_i[15:2]` 取得 14 bit 并转换为 signed；mixer 为 `14x14 -> 28 bit -> >>>13 -> signed14`；LPF 为 32-bit accumulator、12 个 fractional-count bits、DC 增益约 1；`laser_error` 为 signed14 internal counts；OUT1 直接取 `laser_error`，OUT2 直接取 `selected_out2`，`laser_control` 不进入当前 OUT2。
- 理论式：`laser_error_count ~= LPF(pd_count * ref_count / 8192)`；同频正弦的 DC 还包含 `cos(phi)/2`。REF 幅值/相位、LPF 频响、截断和饱和都会改变幅值，不能把 `laser_error` 当作 IN1 电压原样换算。
- 映射结论：CH1/2/3/4 capture 都是 14-bit pre-analog counts；寄存器 sign-extend 到 32 bit，remote helper 用 `to_signed14()` 恢复，backend 不缩放，GUI 原始数组仍是 counts。plot Y 轴为 display-only `div`；CSV 保留 raw counts 和 nominal `time_s`。
- 电压风险：active backend/helper 统一使用 `COUNTS_PER_VOLT=8191.0`；Red Pitaya 官方 14-bit LV raw ADC 理想 divisor 为 8192。更关键的是当前 custom ADC/DAC 路径没有 per-channel gain/offset/LV-HV/load 校准；50 ohm 与 Hi-Z/PZT 负载可能产生显著不同的物理电压。GUI 电压只能视为 ideal estimate，不能视为真实电压。
- 时间风险：`time_s=index*decimation/125e6` 是 nominal relative time；RTL 的 ramp position update 在 divider tick 后还有 `update_pending` 周期，实际 step interval 约为 `(update_div+1)/clk`。真实 scan period 必须由 capture/scope 测量。
- 硬件校准设计：复用现有 `MODE=2 HOLD`，不新增 mode。只接 OUT2 到 scope，记录 50 ohm/Hi-Z、探头和线缆；对 `0, +/-1024, +/-2048, +/-4096 counts` 逐点执行 `SAFE -> exact HOLD -> readback/CH4/scope -> SAFE`，再覆盖计划 scan min/center/max。拟合 `V=a*C+b`，得到 `DAC_count_per_volt_OUT2=1/a` 与 `zero_offset_OUT2=b`。
- PASS：readback 与命令 count 一致、正确极性/单调、无 saturation/削顶、重复性满足 scope 规格、`R^2>=0.999`、最大残差不超过实测 span 1%、计划区间保留 PZT 安全余量。任何通信/身份异常、越界、跳变、readback 不符或未解释的负载倍数差都 FAIL 并立即 SAFE。
- 第一次 P-only 前仍必须取得三项板上数据：OUT2 `count/V + zero offset + load`；CH3 counts 对 scope OUT1 的 gain/offset/极性；实际 PZT 节点 scan 的 `Vmin/Vmax/Vpp/period/polarity` 与 CH4 counts 对应关系。三项当前均为 `[NOT VERIFIED]`。
- 自动化：`tabnanny`、`py_compile` 通过；收集 `75 tests`；targeted `31 passed, 44 deselected`；当前文件 `75 passed`；完整 software tests `81 passed, 4 subtests passed`。pytest 仅有 sandbox 无权创建 `.pytest_cache` 的 warning，不影响测试结果。
- `git diff --check` 通过；`version/AI_STRICT_REVIEW_ENTRY.md` 的既有 merge conflict markers/旧状态仅作为已知文档污染报告，本轮未修改且未用于覆盖当前 RTL/STATUS。
- 未修改 RTL、Vivado 工程、寄存器地址/语义、`MAGIC`、`VERSION`、bitstream 或 Python；未运行 Vivado、未生成/烧录 bitstream、未连接板卡、未执行 LOCK HERE/P-only。
- 阶段结论：`CODE/TRACE PASS / PHYSICAL VOLTAGE NOT CALIBRATED / WAITING BOARD EXPERIMENT`。
- 下一步唯一动作：只接 OUT2 到示波器，用 MODE=2 HOLD 完成 exact-count 多点测量，先得到 `DAC_count_per_volt_OUT2` 和 `zero_offset_OUT2`。

## 2026-07-16 v3LOCK-P0 Hardware Verification Infrastructure / HV-1 准备

- Git Gate PASS：历史遗留 interactive rebase 已由用户结束，`main` 已恢复；本轮开始和 fetch 后均确认 working tree clean、无进行中的 Git 操作、`HEAD=origin/main=0e13f2806d7a716d3e66d365babbe2b247e59d8b`。保险分支只作恢复点，本轮未再次执行 rebase。
- 固化 Stage 0 Audit -> Stage 1 Code -> Stage 2 Software Verification -> Stage 3 Hardware Verification -> Stage 4 Review，并建立 Git Baseline Gate、单一 Current Stage/Gate/下一步和统一证据等级规则。
- 新增 `version/HARDWARE_VALIDATION.md` 和上位机 `docs/HARDWARE_CALIBRATION_SOP.md`；当前 Gate 只准备 HV-1 OUT2 count=0，PZT 必须断开，OUT2 只接示波器。
- 上位机现有 `hold-v=0.0000` 可精确生成 count=0，Probe/Status/Capture 可记录身份、MODE、ENABLE、STATUS、OUT2_MONITOR、saturation 和 CH4，因此本轮未修改 Python。非零 exact-count 不在本轮授权范围。
- `tabnanny`、五个指定 `py_compile` 通过；收集 `81 tests`，完整测试 `81 passed`。硬件校准尚未执行，证据仍为 `[NOT VERIFIED]`。
- 未修改 RTL、Vivado、寄存器地址/语义、MAGIC、VERSION、bitstream 或测试；未运行 Vivado、未生成/烧录 bitstream、未执行 SCAN、LOCK HERE 或 P-only。
- 阶段结论：`CALIBRATION INFRASTRUCTURE CODE PASS / WAITING USER HARDWARE HV-1`。
- 下一步唯一动作：断开 PZT，使 OUT2 只连接示波器，按 SOP 只执行 count=0 的 HV-1 测量，记录 readback 和示波器真实电压，然后立即 SAFE。
## 2026-07-16 v3LOCK-P0 System Identity 只读上位机准备

- Git Gate PASS：`main` clean、无进行中的 Git 操作，fetch 后 `HEAD=origin/main=4a0b7b0ecf30a215191f930f491447f7cc17a417`；未 commit/push。
- Current Stage/Gate 不变：`Stage 3 Hardware Verification / HV-1 OUT2 fixed-count physical voltage calibration`。本轮只增加左侧紧凑 `System Identity`，不改变扫描、人工锁点、LOCK HERE 或 APPLY P。
- `REFRESH IDENTITY` 复用只读 `status`，显示连接、host、Matched/Mismatch/Unknown、`v3.0.1`、SAFE/SCAN/HOLD/P_LOCK/PI_LOCK、Disabled/Enabled/Saturated 和本机 probe 时间。
- 当前协议不含 bitstream build date/time、Git SHA、Vivado build ID 或 filename；界面固定显示 build date unavailable，本地 Host code 明确不代表 bitstream。
- 通信/认证/身份/寄存器读取错误分类显示；失败后清除旧身份缓存。Identity 非 Matched 或 Saturated 时危险操作入口禁用，SAFE 与原有安全守卫保留。
- 自动化：tabnanny、py_compile 通过；collect `84`；targeted `13 passed, 71 deselected`；当前文件 `84 passed`；完整 software tests `90 passed, 4 subtests passed`。
- 未修改 backend/worker、RTL、Vivado、寄存器、MAGIC、VERSION、bitstream、Hardware Validation 结果或 SOP；未执行真实 GUI/硬件实验。
- 结论：`SYSTEM IDENTITY SOFTWARE PASS / WAITING USER HARDWARE HV-1`；下一步仍为 PZT 断开、OUT2 只接示波器，按 SOP 只执行 count=0 HV-1，记录后立即 SAFE。

## 2026-07-16 OUT2 voltage mapping software correction

- 本地工程 `main` initial HEAD `016f8d51b4500ec90f9d8006d138a8504c58b12a`；用户禁止联网和 Git 历史改写，本轮未执行 fetch/pull/reset/rebase。
- 修复前硬件证据：STEM125-14 OUT2 50 Hz 三角波频率/波形正常；center 为 `0.5/0.6/0.7/0.8/0.9 V -> 0.574/0.6875/0.8015/0.913/1.0255 V`；拟合 `V_actual ~= 1.13 * V_GUI + 0.009 V`；amplitude gain 约 `1.18`。
- RTL 审计确认 register、ramp、mode selector 和 DAC 入口均保持 signed14 count，无二次缩放。新增 Python 单一校准层，修正 SCAN center/amplitude、HOLD、manual LOCK_BIAS 和 PZT safe count；自动捕获 LOCK_BIAS 保持原始 `OUT2_MONITOR` count。
- P correction 仍在 RTL raw-count 域计算，本轮未修改 mixer、LPF、PID/P-only、锁定逻辑、RTL、Vivado、register 或 bitstream。
- 校准后 HOLD `0 V` 不再等于 raw count 0；旧 exact-count=0 步骤已暂停，当前 SOP 只授权 PZT 断开时执行 center `0.800 V`、amplitude `0.100 V`、50 Hz 单组复测。
- 自动化验证：tabnanny PASS；PowerShell 展开实际 Python 文件后的 py_compile PASS（原样 `*.py` 参数因 Windows 不展开通配符返回 Invalid argument）；collect-only `94 tests collected`；targeted `6 passed`；当前测试文件 `88 passed`；完整 software tests `94 passed`。
- 阶段结论：OUT2 voltage mapping software correction implemented；Waiting hardware re-validation。下一步唯一动作是在原示波器条件下复测 `center=0.800 V`、`amplitude=0.100 V`、`50 Hz`，确认中心和 Vpp 均小于 5% 误差后 SAFE。

## 2026-07-16 v3LOCK-P0 MTS zero crossing 插值与人工锁点校准

- 根因：原上位机以整数 index 表示 CH3 过零，并从最近单个样点读取 CH4/PZT，导致 candidate 与真实 `error=0` 存在采样量化偏差。
- 实现：相邻异号 CH3 样点按 `fraction=-e0/(e1-e0)` 插值得到 float index；同一 fraction 用于 error residual、CH4/PZT 和 nominal time。搜索要求持续异号、local Vpp/noise、CH4 单调和 PZT safe range，多候选选择最大 `|dError/dPZT|`。
- 人工校准：新增 `-5/-1/+1/+5 mV`，只更新 host-side `LOCK_BIAS` 目标，不改变插值 `ERROR_SETPOINT`、不立即进入反馈；Confirm 保存候选供既有 `LOCK HERE` 使用。
- 验证：`[-10,-5,5,10] -> zero_index=1.5`、residual `0`、PZT 线性插值通过；噪声拒绝、最大斜率、浮点 marker、Confirm 和无反馈微调均有回归测试。targeted `24 passed`；collect `98`；完整 tests `98 passed`；tabnanny、py_compile、git diff check 通过。
- 边界：未修改 RTL、Vivado、寄存器地址/语义、FPGA 接口、PID/P-only 或 bitstream，未运行 Vivado，未执行真实 `LOCK HERE`。
- 当前状态：[AUTOMATED VERIFIED] 人工锁点校准功能软件实现完成；下一步唯一动作是在 `Kp=0` 下完成一次真实选点/Confirm/LOCK HERE readback 与 CH4 无跳变验证，随后 SAFE；PASS 后再做小步 P-only。

## 2026-07-16 v3LOCK-P0 Lock Point Calibration 坐标与 bias 修复

- 实验状态：MTS error 已由用户确认正常；PICK LOCK POINT/Confirm 对真实 zero crossing 与 CH1 目标的映射失败；未进入 P-lock。
- 修复 `scene pixel -> ViewBox time(ms) -> capture buffer/raw index`，并显示 `display_x/time_ms/raw_index`；zero crossing 只接受 `y1*y2<0`，线性插值 float index、residual、time 与 CH4 raw。
- 候选优先级改为最小 residual，再取最大斜率与最近目标；Confirm 显式保存 `lock_index/error_setpoint/pzt_bias`。
- CH1/CH3/CH4 从一次遍历形成的同一二维 capture buffer 取对齐列；实验默认值改为 center `0.770 V`、amplitude `0.080 V`、frequency `50 Hz`、safe `0.600~0.900 V`、`Kp=0`、Normal。
- 自动验证：当前文件 `94 passed`，collect `100`，完整 tests `100 passed`，tabnanny/py_compile/git diff check 通过。
- 未修改 waveform_plot、RTL、Vivado、寄存器、FPGA 接口、PID/P-only 或 bitstream；Lock Point Calibration 仍等待真实 GUI/硬件复测，未进入 P-lock。

## 2026-07-18 v3LOCK-P0 Operator Voltage View and Loaded PZT Diagnostics

- 当前阶段保持 `v3LOCK-P0 / Stage 3 Hardware Verification`。CH4 明确为 pre-DAC `selected_out2` command counts，不是 PZT 节点回采；普通界面显示 command-side calibrated estimate，CH3 显示 ideal equivalent，raw counts 保留在算法、寄存器、CSV、事件日志和 Engineer Details。
- 新增 selected/captured 纯诊断：透明显示目标与 FPGA `captured_lock_bias_counts/captured_error_setpoint_counts`、delta、target wait、MODE/ENABLE/Kp/saturation；缺失字段为 unavailable。当前 FPGA 不提供事件级 pre/post/trigger direction，因此 selected→captured delta 不称为 scan→lock jump。
- 新增 `HOLD SELECTED COUNT`：confirmed `lock_bias_counts` 原样经过 backend/worker/既有 `--hold-counts` 写入 HOLD_VALUE；不做 counts→volts→counts，不触发 CAPTURE_LOCK_POINT，不写 Kp/Ki/polarity。执行前验证身份、Kp=0、当前 capture generation、safe range、空闲与无 saturation；回读异常请求 SAFE。
- 状态管理：HOLD 成功显示 `HOLD DIAGNOSTIC / Kp=0 / NOT LOCKED`；SAFE 保留 last/not live，新 capture/目标清除旧 captured 绑定，断线/身份错误标 stale。选点、HOLD、LOCK HERE 扩展进入实验导出。
- 自动验证：tabnanny/py_compile 通过；收集 `136`；targeted `4 passed, 90 deselected`；新增诊断文件 `36 passed`；主测试 `94 passed`；完整软件测试 `136 passed, 4 subtests passed`。
- [NOT VERIFIED] 真实 GUI、PZT + Scope loaded calibration、exact-count HOLD 谱线位置、Kp=0 LOCK HERE 无跳变、P-only、激光锁定和稳频。未修改 RTL、Vivado、寄存器、MAGIC、VERSION 或 bitstream，未运行 Vivado。
- 下一步唯一动作：最终 loaded PZT + scope Hi-Z 接线，Kp=0、优先 2~5 Hz，执行一次 `SAFE -> SCAN -> Capture -> Pick -> Confirm -> HOLD SELECTED COUNT -> 记录 -> SAFE`，只诊断 scan→hold 差异。

## 2026-07-18 v3LOCK-P0 HV-1B User Verification -> HV-2 Loaded PZT Scan

- [USER HARDWARE VERIFIED] 用户明确确认：当前软件预补偿下，PZT 断开时上位机设定的 OUT2 电压与板上真实输出一致。HV-1B 标记为通过，不再重复空载 SCAN 复测。
- 证据边界：本轮未收到独立的 center/Vpp/frequency、scope load/coupling/probe 数值，因此只记录用户硬件通过声明，不虚构缺失数据。
- 代码核对：现有 host 已具备 HV-2 所需 identity、SAFE、SCAN safe-range、MODE/ENABLE、OUT2 readback、saturation 和 CH1/CH3/CH4 capture。
- 本轮唯一独立工程复核发现 1 个 High：设为 2 Hz 后 capture decimation 仍可能保留 50 Hz 窗口，2048 点只覆盖约 20 ms，无法判定完整扫描。已在 `main_window.py` 将 Lock View capture window 与 scan frequency/capture length 同步；`2 Hz / 2048 points -> decimation 30518 -> 约 0.5 s`。复核无其他 Blocker/High。
- 验证：`tabnanny` 和修改文件 `py_compile` 通过；聚焦 `8 passed, 87 deselected`；`137 tests collected`；完整 software tests `137 passed`。
- 文档更新：当前 Gate 转为 `Gate 2 / HV-2 loaded PZT SCAN voltage and spectral-response verification`；新增 `software/redpitaya_lock_host/docs/LOADED_PZT_SCAN_SOP.md`，旧 `HARDWARE_CALIBRATION_SOP.md` 保留为已完成 HV-1B 记录。
- 只修改上位机 capture-window 同步与回归测试；未修改 RTL、Vivado、寄存器、`MAGIC`、`VERSION` 或 bitstream，未运行 Vivado，未执行硬件操作。
- 下一步唯一动作：只执行 loaded PZT 低速 SCAN-only：`SAFE -> OUT2 接专用 PZT/Scan + scope Hi-Z -> 0.770 V / 0.080 V / 2 Hz / Kp=Ki=0 -> Capture/record -> SAFE`。HV-2 PASS 前不执行 HOLD、LOCK HERE、APPLY P 或 polarity 变更。

## 2026-07-23 v3LOCK-D1 Deterministic FPGA Lock Acquisition Implementation

- D1-B/D1-C 已实现并自动验证：新 `VERSION=0x00030100`；FPGA shadow-to-active ARM、实际 OUT2 direction、原始 `laser_error` crossing、atomic P_LOCK_KP0、sticky event、ABORT/FAULT；host/GUI 正常路径改为完整 preload + 单次 ARM，legacy `CAPTURE_LOCK_POINT` 仅保留 diagnostic。
- XSim 结果：register bank `136/136`、OUT2 controller `35/35`、integrated acquisition `32/32`；bumpless 数字命令跳变 `0 counts`。正式 Python tests 合计 `142 passed`。
- 安全边界：未运行 Vivado synthesis/implementation/timing，未生成/烧录 bitstream，未执行硬件；真实 Kp=0、最小非零 Kp 与 P-only 均保持 `[NOT VERIFIED]`。
- 当前 Gate：`D1-D / Integrated software/RTL verification and hardware SOP`。下一步只由用户完成 Vivado source/timing 检查；通过后再进入新的单项硬件 SOP。
