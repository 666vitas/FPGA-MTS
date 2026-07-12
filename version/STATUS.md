# STATUS

## 2026-07-12 v3LOCK-P0 上位机准实时观察与人工锁点工作台

本次目标：只修改上位机 Python 和既有文档记录，实现用于 10 Hz PZT 扫描的实验工作台：准实时 capture、四通道独立显示、人工点击 PD 后解析 CH3/error 过零、Confirm 后才允许 `LOCK HERE`，并保持最小 P-only `APPLY P` 链路。

修改文件：`software/redpitaya_lock_host/redpitaya_lock_host/main_window.py`、`software/redpitaya_lock_host/tests/test_custom_fpga_backend.py`、`version/STATUS.md`、`version/v3/DEVELOPMENT_LOG.md`、`software/redpitaya_lock_host/docs/DEVELOPMENT_LOG.md`。继续沿用既有 `custom_fpga_backend.py` / `custom_fpga_scan_control.py` 的 `lock-here` 与 `update-p-lock` 寄存器语义，未修改 RTL、Vivado 工程、bitstream、寄存器地址或寄存器语义。

实现功能：新增 `Start Live`、`Stop Live`、`Capture Once`、`refresh interval 500/1000/2000 ms`；Live 使用 `capture_in_flight` 防重入，并且只在 capture 完成、GUI 更新和安全检查后用 single-shot timer 安排下一次 capture。右侧改为四个独立 `WaveformPlot`：CH1 IN1/PD、CH3 OUT1/laser_error、CH4 OUT2/selected_out2、CH2 IN2/REF；每通道有 `Visible`、`Auto Y`、`Scale counts/div`、`Center counts`、`Reset`，这些只改变显示范围和可见性，不改原始 capture 数据、不写 FPGA。新增 `Lock View` / `REF Debug`：Lock View 默认 CH1/CH3/CH4、隐藏 CH2、capture length 2048 并按 scan freq 估算一个扫描周期；REF Debug 默认只显示 CH2，decimation 只选 1/2/4/8，并提示不能同时完整显示 10 Hz 慢扫描周期。

人工锁点：新增 `Select Target Transition` 与 `Confirm Lock Point`。用户必须先在 CH1/PD 图点击目标峰附近；GUI 记录 clicked index/time/OUT2，再在附近窗口搜索 CH3 laser_error 有效零交叉，检查局部 Vpp、斜率、capture 边缘、OUT2 安全范围和 saturation；找到后只生成 pending lock point，并在四通道画 target peak marker 与 resolved zero-crossing marker。只有 `Confirm Lock Point` 会更新 `selected_lock_point`；`LOCK HERE` 必须已有 confirmed lock point。

最小 P-only 行为：`LOCK HERE` 仍等待 OUT2 进入 confirmed target window 后触发 FPGA `CAPTURE_LOCK_POINT`，由 FPGA 同拍捕获 `ERROR_SETPOINT` 和 `LOCK_BIAS` 并进入 `MODE=3 P_LOCK`，Kp 从 0 开始。`APPLY P` 仍只允许 Kp `0/4/8/16/32` 和 polarity 手动更新；不覆盖 `LOCK_BIAS` / `ERROR_SETPOINT`，不触发重新捕获，不启用 Ki/Kd，不自动增加 Kp，不自动判断 polarity，不自动重锁。

安全行为：capture 失败、SSH 失败、MAGIC/VERSION 异常、capture timeout、saturation、OUT2 超出配置 PZT safe range、`LOCK_ERROR` 连续超阈值、用户 SAFE/ABORT/Stop Live 或窗口关闭都会停止 Live 并提示 SAFE；不会自动提高 Kp、切 polarity 或重新 LOCK HERE。

尚未实现/未声明：未做 AI 自动识峰、自动重锁 FSM、自动 PID 调参、自动 polarity 判断、Ki/Kd、真实激光闭环完成声明；未运行 Vivado，未生成 bitstream，未烧录，未上板验证本轮 GUI 工作台。

测试结果：`.venv\Scripts\python.exe -m pytest tests` 在上位机目录通过，`42 passed`；`py_compile` 通过，覆盖 `custom_fpga_scan_control.py`、`custom_fpga_backend.py`、`connection_workers.py`、`main_window.py`、`waveform_plot.py`。

上板预期现象：烧录当前 `VERSION=0x00030001` bitstream 后，先读 `MAGIC=0x4D545330` / `VERSION=0x00030001`；SCAN 时 Live 约 1 Hz 刷新四通道，CH1/CH3/CH4 在 Lock View 可见且 CH2 默认隐藏；点击 CH1 峰附近后，GUI 应在 CH3 附近解析出过零并显示两类 marker；Confirm 后 `LOCK HERE` 等待 OUT2 回到 target window，进入 P_LOCK Kp=0，随后用户手动 `APPLY P` 小步测试。

PASS 判据：Live 不重入且 Stop 后不再 capture；capture 完成后才安排下一次刷新；四通道曲线和显示控制正常且不改原始数据；无有效 CH3 过零时拒绝 Confirm；未 Confirm 时 `LOCK HERE` 被阻止；`APPLY P` 不改 `LOCK_BIAS` / `ERROR_SETPOINT`；异常能停止 Live 并提示 SAFE。FAIL 判据：GUI 明明收到 capture 却不显示；Live 重入；Stop 后仍 capture；点击 PD 峰后把峰顶直接当锁点；未 Confirm 也能 LOCK HERE；APPLY P 重新捕获或覆盖锁点；任何 RTL/Vivado/bitstream 被本轮修改。

下一步唯一任务：用户上板按 `SCAN -> Lock View Live/Capture Once -> CH1 点击目标峰附近 -> Confirm Lock Point -> LOCK HERE -> Kp=0/4/8/16/32 手动 APPLY P -> 判断 polarity -> 异常 SAFE` 做真实工作台验证，并记录 capture/LOCK HERE 现象。

## 2026-07-12 PZT 基础稳频主线纠正与最小闭环

项目最终目标固定为：基于 Red Pitaya 的全自动深度学习参数优化 MTS 激光稳频系统。当前阶段只做最简单、可人工操作的 PZT 基础稳频：`OUT2 -> 激光器专用 PZT / Scan 输入`，`SCAN -> 观察 MTS error -> 人工选择色散过零点 -> LOCK HERE -> 同拍捕获 ERROR_SETPOINT 和 LOCK_BIAS -> P-only 小增益反馈 -> SAFE`。

当前有效安全边界：OUT2 的目标执行器就是激光器专用 PZT / Scan 输入；`MODE=1 SCAN` 和 `MODE=3 P_LOCK` 使用同一个 PZT 接口。必须限制 OUT2 幅度、偏置、`LOCK_CORRECTION_LIMIT` 和 `LOCK_LIMIT`，反馈方向错误、输出接近 limit、持续 saturation、通信失败或波形异常时立即 SAFE。禁止 OUT2 接激光器电流调制输入，禁止接 D2-125 Servo Output / Aux Output，禁止两个设备输出端并联。

当前代码审查结论：RTL 已具备 `SCAN` 输出到 `selected_out2 -> DAC B / OUT2`、`CAPTURE_LOCK_POINT` 同拍捕获 `ERROR_SETPOINT` 与 `LOCK_BIAS`、`P_LOCK` 使用 `laser_error - ERROR_SETPOINT` 后的 `lock_error`、Kp=0 无扰保持 `LOCK_BIAS`、P correction 受 `LOCK_CORRECTION_LIMIT` 限制、最终 OUT2 受绝对 `LOCK_LIMIT` / DAC limit 限制、SAFE 退出。上位机已具备 `SCAN -> Capture Waveform -> 点击目标 -> LOCK HERE -> Apply Kp -> UNLOCK / SAFE` 的最小人工闭环路径；本次新增 `Apply Kp`，只更新 Kp / polarity / limit，不重新捕获 `LOCK_BIAS` 或 `ERROR_SETPOINT`。

当前仍缺失：尚未由用户反馈完成新 bitstream 烧录后的 PZT 基础稳频闭环实测；尚未证明 `custom_debug_capture` 上板 waveform 数据完整可用；尚未证明 LOCK HERE 后小 Kp 能在真实 PZT 上长期保持色散过零点；尚未实现 AI 自动识峰、自动重锁、复杂 PID、Ki/integral 或深度学习参数优化。下一步唯一任务：用户上板按 `SCAN -> 选择锁点 -> LOCK HERE -> 小步 Kp -> 判断 polarity -> 基础稳频 -> SAFE` 做实测记录。

## 2026-07-11 v3LOCK-P0 用户手动 Vivado timing PASS，下一步唯一任务是 Generate Bitstream

当前验证等级：代码与 testbench 已通过；用户手动 `red_pitaya_top` synthesis / implementation / timing 已通过。Implemented Design 已确认存在 `i_custom_debug_capture`、`i_custom_register_bank`、`i_error_setpoint_corrector`。Timing：Setup WNS `+0.031 ns`、TNS `0.000 ns`、Failing Endpoints `0`；Hold WHS `+0.048 ns`、THS `0.000 ns`、Failing Endpoints `0`；Pulse Width WPWS `+1.000 ns`、TPWS `0.000 ns`、Failing Endpoints `0`；Vivado 显示 `All user specified timing constraints are met.`

仍未完成：尚未证明 bitstream 已生成；尚未烧录；尚未读取新 `VERSION=0x00030001`；尚未完成 SAFE/SCAN 示波器回归；尚未验证 `custom_debug_capture` 上板工作；尚未验证 `LOCK HERE`；尚未真实闭环锁定激光。

关键阻塞：timing PASS 不等于 bitstream、烧录、PZT 基础稳频或锁定通过。OUT2 目标执行器是激光器专用 PZT / Scan 输入，但必须限幅、限偏置、小 Kp、异常 SAFE；禁止接激光器电流调制输入、D2-125 Servo Output、D2-125 Aux Output，也禁止与任何 D2-125 输出并联。

## 2026-07-11 v3LOCK-P0 LOCK HERE 与 FPGA 同拍锁点捕获候选

本次按最新安全纠正收敛为第一版人工选点：历史 `board(1).csv` 中的 `54 counts`、`0.704 V`、`0.784 V`、`49.75 Hz` 以及任何峰值/基线/扫描位置，只允许作为问题分析证据，禁止作为 RTL、Python、GUI、测试默认值或锁点配置。
新增候选协议 `VERSION=0x00030001`：`ERROR_SETPOINT`、`LOCK_ERROR_MONITOR`、`CAPTURE_LOCK_POINT`。`CAPTURE_LOCK_POINT` 在 FPGA `clk_i` 域同拍锁存 `ERROR_SETPOINT <= ERROR_MONITOR` 与 `LOCK_BIAS <= OUT2_MONITOR`，并进入 `MODE=3 P_LOCK`；P_LOCK 使用 `lock_error = saturate_14bit(laser_error - error_setpoint)`，不再直接使用原始 `laser_error`。
上位机主流程改为 `SCAN -> Capture Waveform -> 点击当前波形目标 -> LOCK HERE -> FPGA 等待当前 OUT2 重新进入所选窗口 -> 同拍捕获 -> Kp=0/Ki=0 P_LOCK -> 小 Kp 后续人工验证 -> SAFE`。第一版不做 AI、不做自动识峰、不恢复 Ki/integral、不使用历史 LOCK_BIAS。
本次已运行 Python 静态检查、pytest 与 XSim 行为仿真；未运行 Vivado synthesis / implementation，未生成 bitstream，未烧录，未接板子。P_LOCK/LOCK HERE 仍必须先 OUT2 示波器验证，禁止声称已闭环锁定或已替代 D2-125。

## 2026-07-11 custom_debug_capture BRAM 修复，等待用户手动 Vivado implementation 验证

用户手动 Vivado place_design 失败：`custom_debug_capture` 的四通道 4096 深度存储被推断为 LUTRAM / RAM64M / RAM64X1D，触发 `[Place 30-484]`，`LUTRAM/SRL capable slices` 需求 `1630 / 1500`，利用率 `108.667%`。
本次只修改 `v0.94/rtl/custom_debug_capture.sv` 和对应 testbench：为 `mem_ch1..mem_ch4` 添加 `(* ram_style = "block" *)`，删除组合读，改为 1 个 `clk_i` 周期延迟的同步读，目标是让 Vivado 推断 Block RAM。
四通道功能保持不变：CH1=IN1/adc_dat[0]，CH2=IN2/adc_dat[1]，CH3=laser_error，CH4=selected_out2；默认 `DEPTH=4096` 保持不变，未降级通道。
未修改 Auto Lock / P_LOCK / KI / correction limit；未运行 Vivado synthesis / implementation，未生成 bitstream，未烧录，未接板子，未运行 Auto Lock。下一步由用户手动重新运行 Vivado synthesis / implementation，并确认不再出现 `[Place 30-484]`，且 timing 满足 `WNS >= 0, TNS = 0, Failing Endpoints = 0`。

## 2026-07-10 Auto Lock candidate 与单窗口 debug capture 第一版

本轮进入 Auto Lock candidate：新增 P-only `LOCK_CORRECTION_LIMIT`，默认 `128 counts`，`MODE=3 P_LOCK` 的 correction 先被限制后再叠加 `LOCK_BIAS`，最终仍受绝对 DAC limit 保护；`MODE=4 PI_LOCK` 继续退化为 P_LOCK，`KI / integral` 不恢复。
上位机新增 `ARM AUTO LOCK` / `ABORT AUTO LOCK` 候选流程：必须先处于 SCAN，自动寻找 error 过零点，写 `LOCK_BIAS` 和 correction limit，强制 `Kp=0`、`Ki=0` 后进入 `MODE=3 P_LOCK`，再只允许自动小步 `Kp=4/8/16/32`；失败立即 SAFE。
GUI 右侧改为单窗口 `Custom FPGA Scope`，新增 `custom_debug_capture` 候选寄存器读取 IN1 / IN2 / OUT1 / OUT2；没有新 bitstream 或 capture 数据时显示 `custom_debug_capture not available`，不画 0 误导用户。
OUT2 当前已接 PZT / Scan，因此 correction limit 是安全必要条件；本轮未运行 Vivado synthesis / implementation，未生成 bitstream，未烧录，未上板验证，禁止声称已完成激光稳频或 FPGA 已替代 D2-125。

## 2026-07-10 当前 main 主线同步

v3REG-0 SAFE/SCAN 已由用户上板验证：base address `0x40600000`，`MAGIC=0x4D545330`，`VERSION=0x00030000`，GUI / monitor 已可控制 OUT2 三角波并可 SAFE 关闭。
GitHub main 已包含 HOLD / P_LOCK / PI_LOCK 候选，但这些候选尚未完成最新 Vivado synthesis / implementation / timing / bitstream / 烧录 / 上板示波器验证。
当前 LOCK 目标缩小为 P-only：`MODE=3 P_LOCK` 是下一步验证重点；`MODE=4 PI_LOCK` 暂时退化为 P_LOCK，`KI / integral` 当前不要恢复。
当前 PZT 基础稳频主线允许 OUT2 接激光器专用 PZT / Scan 输入；禁止接激光器电流调制输入、D2-125 Servo Output、D2-125 Aux Output，禁止任何输出端并联；禁止声称 FPGA 已经完成全自动锁定或替代 D2-125。

## 2026-07-09 Custom FPGA Lock Host GUI 启动修复

本次只修复上位机 GUI：移除主界面对旧 Official SCPI `self.out1/self.out2` 控件的无条件依赖，解决 `run_mock.bat` 启动 `AttributeError`。
主界面仍保持 Custom FPGA Lock Host，不恢复 Official SCPI/ASG 主工作流。
未修改 RTL，未运行 Vivado，未生成 bitstream；当前有效主线以 2026-07-12 PZT 基础稳频段落为准。

## 2026-07-09 上位机主线收敛为 Custom FPGA Lock Host

上位机主界面不再暴露 Official SCPI/ASG 操作入口，默认流程改为 `Probe Registers -> Status -> SAFE -> SCAN -> Capture Bias -> LOCK -> UNLOCK/SAFE`。
`LOCK` 当前为 P-only：先读取 `OUT2_MONITOR` counts 作为 `LOCK_BIAS`，再写入 `MODE=3 P_LOCK`；不使用 `lock-bias-v` 理想电压估算捕获偏置。
`IN1/IN2` 自定义波形显示仍未实现，只记录 `debug_capture` 寄存器方案；本次未修改 RTL、未运行 Vivado、未生成 bitstream。
当前有效主线已纠正为 OUT2 目标执行器是激光器专用 PZT / Scan 输入；禁止连接激光器电流调制输入或 D2-125 输出。

## 2026-07-09 v3REG P-only timing 修复，等待用户手动 Vivado 验证

用户手动 Vivado implementation 报告当前候选存在严重 timing fail：`WNS=-10.361 ns`、`TNS=-16400.330 ns`、`Failing Endpoints=6099`，疑似来自 `out2_lock_controller` 的 error->P/PI->clamp 长组合路径。
本次将当前 LOCK 目标缩小为 P_LOCK：`MODE=3` 为流水线 P-only；`MODE=4 PI_LOCK` 暂时退化为 P_LOCK，`KI / integral` 在当前 RTL 中禁用。
Register map 和上位机命令保持不变；上位机仍可写 `KI`，但当前 RTL 不使用 `KI`。
Codex 本次不运行 Vivado，不运行 synthesis / implementation，不生成 bitstream，不声称 timing 通过。
当前有效主线已纠正为 OUT2 目标执行器是激光器专用 PZT / Scan 输入；必须限幅、限偏置、小 Kp、异常 SAFE，禁止接激光器电流调制或 D2-125 输出。

## 当前主线

当前主线 = v3REG-0 SAFE/SCAN 已由用户上板验证通过；GitHub main 的 RTL 已包含 v3REG-1 / v3REG-2 候选逻辑，但 HOLD / P_LOCK / PI_LOCK 尚未完成 Vivado synthesis / implementation / timing / bitstream / 上板验证。

```text
OUT1 = laser_error = mixer + LPF error observation
OUT2 = selected_out2
  MODE=0 SAFE: OUT2 = 0
  MODE=1 SCAN: OUT2 = ramp_generator
  MODE=2 HOLD: OUT2 = HOLD_VALUE
  MODE=3 P_LOCK: OUT2 = clamp(LOCK_BIAS + POLARITY * KP * error, LOCK_LIMIT)
  MODE=4 PI_LOCK: 当前暂时退化为 P_LOCK；KI / integral 当前不要恢复
laser_control / pi_controller_seq = 内部候选/历史路径，不是当前 DAC B / OUT2 最终输出
```

v3REG-0 已验证内容：Red Pitaya 加载 `/root/red_pitaya_top.bit.bin` 后，`0x40600000` 可读到 `MAGIC=0x4D545330`、`VERSION=0x00030000`，GUI/monitor SAFE/SCAN 可控制 OUT2 三角波并可 SAFE 关闭。

v3REG-1 / v3REG-2 当前状态：代码和仿真候选已存在，包含 `HOLD_VALUE / KP / POLARITY / LOCK_BIAS / LOCK_LIMIT / ERROR_MONITOR / CONTROL_MONITOR / KI / INTEGRAL_RESET`。这些模式还没有通过 Vivado timing、没有生成新 bitstream、没有烧录、没有上板验证。

强制安全边界：OUT2 只允许接激光器专用 PZT / Scan 输入；禁止接激光器电流调制输入、D2-125 Servo Output、D2-125 Aux Output，禁止任何输出端并联；禁止声称已经完成全自动锁定或已经替代 D2-125。

## 2026-07-05 GUI Custom FPGA Control v1 已接入

上位机 PySide6 GUI 已新增 Custom FPGA Control v1：Probe Registers / Status / SAFE / SCAN。
该路径通过 SSH + `/dev/mem` 访问 `custom_register_bank`，不启动 `redpitaya_scpi`，不使用 Official SCPI ASG 控制 Custom FPGA OUT2。
SAFE / SCAN 写寄存器前必须读到 `MAGIC = 0x4D545330`；`MAGIC = 0x00000000` 时 GUI 提示重新 Probe、检查 Program Device / 旧 bit / base address / timing-pass bitstream。
本次未修改 RTL，未生成 bitstream。

## 2026-07-05 v3REG-0 status 可读但 MAGIC 为 0，已新增只读 probe

用户通过 SSH 执行 `status` 已成功，但读到 `magic/version = 0x00000000`，因此不能 `safe` / `scan`。
脚本新增只读 `probe`，扫描 `0x40000000` 到 `0x40700000` 的 1 MiB base，逐项输出 magic/version。
若 `probe` 全 0，优先重新 Program Device / 重新加载当前 timing-pass 的 `red_pitaya_top.bit`；不要因未打开网页 App 就排除 bitstream 加载问题。

## 2026-07-05 v3REG-0 host SSH quoting 与烧录顺序 SOP 已修正

`custom_fpga_scan_control.py` 已修复 Windows PowerShell -> SSH -> remote bash 的 `python3 -c` quoting，避免远端 bash 误解析 Python 代码。
实验顺序明确为：先 Generate Bitstream 并把 timing-clean bitstream 加载/烧录进 Red Pitaya FPGA，再运行上位机脚本。
Red Pitaya 网页界面不是本阶段必需条件；VPN 可能影响网页、`.local` 或 SSH，建议关闭 VPN 或使用板子实际 IP。
烧录后第一步仍是 `status`，必须读到 `MAGIC=0x4D545330`；之后才允许 `safe` / `scan`。当前 PZT 基础稳频主线下，OUT2 只允许接激光器专用 PZT / Scan 输入。

## 2026-07-05 v3REG0_TIMING_FIX_2 用户手动 Vivado implementation timing PASS

用户手动 Vivado implementation 已通过：`WNS = +0.322 ns`，`TNS = 0.000 ns`，`Failing Endpoints = 0`。
允许进入 Generate Bitstream；当前有效主线已纠正为 OUT2 目标执行器是激光器专用 PZT / Scan 输入。
禁止接激光器电流调制输入、D2-125 Servo Output、D2-125 Aux Output，禁止任何输出端并联。

## 2026-07-05 v3REG0_TIMING_FIX_2 已拆分 ramp_generator 三角波更新路径

用户手动 Vivado 仍剩 1 条 setup fail：`step_q_reg[5]/C -> direction_up_q_reg/D`，WNS/TNS 均为 `-0.085 ns`。
本次只修改 `v0.94/rtl/ramp_generator.sv`，把 tick 后的位置更新拆成候选计算拍和边界/方向提交拍，切断 `step_q` 同周期影响 `direction_up_q` 的路径。
本地 `xvlog -sv rtl/ramp_generator.sv` 通过，0 error；未运行 Vivado synthesis / implementation，未生成 bitstream，未烧录。
用户下一步：Vivado `Reset Runs -> Run Synthesis -> Run Implementation -> Timing Summary`，通过标准仍为 `WNS >= 0, TNS = 0, Failing Endpoints = 0`。

## 2026-07-05 v3REG0_TIMING_FIX_1 已修复 ramp_generator 配置长路径，等待用户重新跑 Vivado

用户手动 Vivado implementation timing failed：

```text
WNS = -3.697 ns
TNS = -274.520 ns
Failing Endpoints = 830

Worst path:
From: i_custom_register_bank/.../C
To:   i_ramp_generator/.../D
Logic Levels = 18
High Fanout = 30
Total Delay = 11.685 ns
Requirement = 8.000 ns
```

结论：v3REG-0 当前不能 Generate Bitstream，不能烧录，不能上板。

本次只做最小 timing 修复：在 `ramp_generator.sv` 内部增加本地配置寄存器 `offset_q / amp_q / step_q / update_div_q / update_div_m1_q / limit_q`。`custom_register_bank` 输出不再直接进入三角波位置更新、限幅和 tick 判断的深组合逻辑；tick 判断改为使用已寄存的 `update_div_m1_q`。

本次未修改 `red_pitaya_top.sv`，未修改 `custom_register_bank.sv`，未修改 `laser_lock_core.sv`，未修改 PI/mixer/LPF/output_protect，未修改 XDC/constraints，未修改 Vivado project structure。未运行 Vivado synthesis / implementation，未生成 bitstream / bin，未烧录 Red Pitaya。

本地语法检查：

```text
xvlog -sv rtl/ramp_generator.sv
结果：0 error
```

用户下一步必须手动 Vivado `Reset Runs`，重新 `Run Synthesis`，重新 `Run Implementation`。通过标准仍然是：

```text
WNS >= 0
TNS = 0
Failing Endpoints = 0
```

只有 timing 通过后才允许继续 Generate Bitstream；在此之前禁止烧录和上板。

## 2026-07-05 v3REG-0 P0-1 host MAGIC 预校验已修复，等待用户手动 Vivado 和示波器验证

本次只修复上位机脚本安全阻塞项，不修改 RTL 功能逻辑。

修复内容：

```text
software/redpitaya_lock_host/scripts/custom_fpga_scan_control.py

safe:
  打开 RegisterWindow
  -> require_magic()
  -> ENABLE=0
  -> MODE=0
  -> 打印 status

scan:
  打开 RegisterWindow
  -> require_magic()
  -> ENABLE=0
  -> 写 SCAN_OFFSET / SCAN_AMP / SCAN_STEP / SCAN_UPDATE_DIV / OUT2_LIMIT
  -> MODE=1
  -> ENABLE=1
  -> 打印 status
```

如果 `MAGIC != 0x4D545330`，脚本会立即非零退出，并且不会写 `MODE`、`ENABLE`、`SCAN_OFFSET`、`SCAN_AMP`、`SCAN_STEP`、`SCAN_UPDATE_DIV`、`OUT2_LIMIT` 等任何寄存器。错误信息会显示实际 magic、期望 magic，并提示旧 bitstream、base address 错误或 `sys[6]` 未连接 `custom_register_bank`。

本次未修改 RTL，未运行 Vivado synthesis / implementation，未生成 bitstream / bin，未烧录 Red Pitaya，未连接 Red Pitaya 执行真实 `safe` / `scan`，未执行 git add / commit / push。

用户下一步仍然是：手动 Vivado synthesis / implementation，timing 通过后生成 bitstream，烧录后只接 OUT2 到示波器，先运行 `status` 确认 `MAGIC=0x4D545330`，再做 SAFE/SCAN 示波器验证。

## 2026-07-04 v3REG-0 最小 register_bank 与 OUT2 host-controlled SCAN 已实现，等待用户手动 Vivado 和示波器验证

本次实现目标是关闭“只能编译时硬编码 OUT2 三角波”的限制，新增最小运行时参数链路：

```text
上位机 SSH
-> Red Pitaya Linux /dev/mem
-> PS M_AXI_GP0
-> sys_bus_if / sys[6]
-> custom_register_bank
-> ramp_generator
-> OUT2
```

当前只支持：

```text
SAFE: OUT2 = 0
SCAN: OUT2 = offset + triangle
```

默认参数：

```text
offset = 0.85 V ~= 6962 counts
amp = +/-0.05 V ~= 410 counts
freq ~= 50 Hz
limit = +/-1 V ~= 8191 counts
```

安全边界不变：本阶段只允许 OUT2 接示波器；不接 Scan/PZT，不接激光器，不接 D2-125 Servo Output，不接 D2-125 Aux Output，不和 D2-125 Aux Output 并联，不声称已经闭环锁定。

Codex 本次未运行 Vivado synthesis / implementation，未生成 bitstream，未烧录 Red Pitaya，未连接 Red Pitaya 网络，未执行 git add / commit / push。

## 2026-07-02 v2B3_scope_safe only-p 上板示波器测试 PASS WITH NOTES

本次记录用户完成的 `v2B3_scope_safe / only-p.csv` 上板示波器数据。该版本使用 `Ki=0` 与 `output_limit=819`，目标是验证 `CONTROL_PATH_MODE=1` 下 `pi_controller_seq` 的 P 路径在示波器-only 条件下是否安全可解释。

本次只记录 Markdown；未修改 RTL，未运行 Vivado，未综合、实现、生成 bit/bin，也未烧录 Red Pitaya。

```text
Board OUT1 / CH1:
Vpp ≈ 0.04874 V
min ≈ -0.01209 V
max ≈ +0.03665 V
RMS ≈ 0.01007 V
mean ≈ +0.00868 V

Board OUT2 / CH4:
Vpp ≈ 0.02410 V
min ≈ -0.00177 V
max ≈ +0.02233 V
RMS ≈ 0.00888 V
mean ≈ +0.00850 V
```

实验判断：

```text
OUT1 error observation 正常，Vpp 约 48.74 mV。
OUT2 Vpp 约 24.10 mV，mean 约 +8.50 mV。
OUT2 不再贴 -0.2 V。
OUT2 不再贴近负向 output_limit。
OUT2 / OUT1 Vpp ≈ 0.02410 / 0.04874 ≈ 0.494。
Ki=0 scope-safe 修正有效。
v2B3_scope_safe 可以判定为 PASS WITH NOTES，并准备关闭。
```

Notes：

```text
这不是闭环锁定。
这不代表 FPGA 已经替代 D2-125。
这不允许直接进入 OUT2 接 Scan/PZT。
OUT2 仍只允许接示波器。
```

记录文件：

```text
version/v2/V2B3_SCOPE_SAFE_ONLY_P_TEST_RECORD.md
```

## 2026-07-02 v2B3 only-pi 示波器测试未通过，进入 v2B3_scope_safe

本次记录用户上传的 `only-pi.csv` / `only-pi_timeseries.png` 示波器测试结论，并生成下一版 `v2B3_scope_safe` 安全修正。Codex 本次只做 Markdown 记录和 `laser_lock_core.sv` 小范围默认参数安全修正；未运行 Vivado，未综合、实现、生成 bit/bin，也未烧录 Red Pitaya。

本次 only-pi 不是 v2B3 通过数据。

```text
OUT1 正常：
Board OUT1 / CH1 能看到 FPGA mixer + LPF 后的 error-like 信号。
Vpp ≈ 0.05385 V，min ≈ -0.02714 V，max ≈ +0.02671 V，RMS ≈ 0.009618 V。

OUT2 未通过：
Board OUT2 / CH4 长期贴在约 -0.2 V 附近。
Vpp ≈ 0.01497 V，min ≈ -0.2036 V，max ≈ -0.1886 V，RMS ≈ 0.1991 V，mean ≈ -0.199 V。
```

判断：

```text
OUT1 error observation 链路基本正常。
OUT2 只剩约 15 mVpp 小动态，不是 v2B3 通过现象。
OUT2 更像是 control_o 被负向 output_limit 限幅，而不是 Red Pitaya +/-1 V 满量程物理削顶。
疑似 sequential PI 的积分项在同号 error 下累积，把 control_o 推到负向 output_limit。
```

同步记录的其他通道：

```text
CH2:
Vpp ≈ 0.151 V
min ≈ 0.593 V
max ≈ 0.744 V
RMS ≈ 0.6554 V

CH3:
Vpp ≈ 2.443 V
min ≈ -1.102 V
max ≈ +1.341 V
RMS ≈ 0.3496 V
```

CH3 外部 D2-125 / analog error 相关信号较大，不能直接进入 Red Pitaya IN1/IN2。IN1/IN2 仍必须保持在 `+/-1 V` 内。

本轮 `v2B3_scope_safe` RTL 参数安全修正：

```text
v0.94/rtl/laser_lock_core.sv

PID_KI_DEFAULT: 16'sd16 -> 16'sd0
PID_OUTPUT_LIMIT_DEFAULT: 14'd1500 -> 14'd819
```

含义：

```text
Ki=0：先关闭积分项，验证 CONTROL_PATH_MODE=1 下 pi_controller_seq 的 P 路径是否安全。
output_limit=819：约等于 +/-0.10 V。
如果 OUT2 仍然偏置明显或接近 limit，下一轮再降到 410 counts，约 +/-0.05 V。
```

当前安全边界：

```text
本次不能进入真实反馈测试。
OUT2 仍只能接示波器。
禁止 OUT2 接激光器。
禁止 OUT2 接 D2-125 Servo Output 三通。
禁止 OUT2 接 D2-125 Aux Output。
禁止 OUT2 接激光器电源 Scan / PZT。
禁止 OUT2 与任何 D2-125 输出并联。
IN1/IN2 必须在 +/-1 V 内。
```

记录文件：

```text
version/v2/V2B3_ONLY_PI_SCOPE_TEST_RECORD.md
```

## 2026-07-01 Aux/PZT 实验数据记录与路线更新

本次只记录用户最新确认的 D2-125 Aux Output / Scan-PZT 数据，并更新后续 scan/lock 开发计划。Codex 本次未修改 RTL，未运行 Vivado，未综合、实现、生成 bit/bin，也未烧录 Red Pitaya。

最新实验结论：

```text
ramp-aux-unlock.csv:
  CH4 = D2-125 Aux Output
  Vpp = 0.1173 V
  min = 0.7505 V
  max = 0.8678 V
  mean 约 0.8087 V
  主频约 52.68 Hz

ramp-aux-unlock1.csv:
  CH4 = D2-125 Aux Output
  Vpp = 0.0626 V
  min = 0.7767 V
  max = 0.8393 V
  mean 约 0.8096 V
  主频约 52.68 Hz

ramp-aux-locking.csv:
  CH4 = D2-125 Aux Output
  Vpp = 0.0169 V
  min = 0.8031 V
  max = 0.8200 V
  mean 约 0.8130 V
```

新的物理认识：

```text
D2-125 Aux Output 不是单纯从 0 V 开始的三角波。
Ramp / Unlock 状态约为 0.81 V DC offset + 0.063~0.117 Vpp triangle，主频约 52.7 Hz。
Lock 状态约为 0.813 V hold + 0.0169 Vpp residual / slow correction。
```

因此，Red Pitaya OUT2 后续如果替代 D2-125 Aux Output，应按下面路线实现：

```text
SCAN:   OUT2 = scan_offset + triangle
HOLD:   OUT2 = captured_vlock
P_LOCK: OUT2 = captured_vlock + Kp * error
PI_LOCK:OUT2 = captured_vlock + Kp * error + Ki * integral(error)
```

当前能力边界仍然是：

```text
历史记录：当时 FPGA 只有 mixer + LPF + 简单 P/PI candidate。
当前 main 纠偏：现在已经有 custom_register_bank 和 selected_out2 scan/lock mode selector。
当前 main 纠偏：上位机已经能在 Custom FPGA Mode 下写 SAFE/SCAN/HOLD/P_LOCK/PI_LOCK 候选寄存器。
当前仍然不能声称已经实现 PZT 锁定。
```

记录文件：

```text
version/v2/V2_AUX_PZT_EXPERIMENT_RECORD.md
```

## 2026-06-30 v2B3 mode=1 sequential PI 时序通过记录

这里记录的是用户手动运行 Vivado Implementation 后给出的结果，只作为项目状态记录。
Codex 本次没有运行 Vivado，没有综合、实现、生成 bitstream，也没有烧录 Red Pitaya。

```text
2026-06-xx 用户手动 Vivado Implementation:
WNS = +0.107 ns
TNS = 0.000 ns
Failing Endpoints = 0
WHS = 0.054 ns
THS = 0
结论：mode=1 sequential PI 候选版本 timing clean。
```

边界说明：

```text
timing clean != 已经锁定激光
timing clean != 已经完成 D2-125 替代
timing clean != 允许把 OUT2 接到激光器
```

下一步仍然只能做示波器验证：

```text
OUT1 -> 示波器：确认 FPGA laser_error / error observation 正常
OUT2 -> 示波器：当前 main 应确认 selected_out2；历史 sequential PI/laser_control 只作为内部候选路径
当前阶段 OUT2 禁止连接激光器、D2-125 Servo Output、D2-125 Aux/Scan，
也禁止连接任何真实执行器通道。
```

## 2026-06-23 v2B3 mode=1 上板候选已准备，等待用户手动 timing 验证

当前实际实验接线记录：

```text
PD -> v1 既有带通/放大链路 -> Red Pitaya IN1
同路解调 REF -> Red Pitaya IN2
OUT1 -> 板内 mixer + LPF 后的 FPGA demodulated error -> 示波器 CH2
OUT2 -> 当前代码产生的 shadow/sequential control -> 示波器 CH4
```

v2B1 timing-safe P-only Shadow Control 上板验证已完成：`mixer.csv` 的 OUT2/OUT1 Vpp 为 `0.515`，`no-mixer.csv` 为 `0.555`；OUT2 没有打到 `+/-1 V`，证明 OUT2 安全输出通道已打通，但这不是激光锁定实验，也不能声称替代 D2-125。

本轮顶层已新增 `LASER_LOCK_CONTROL_PATH_MODE=1` 并显式传给 `laser_lock_core`。这使下一次用户手动生成的候选工程选择 v2B3 sequential PI；OUT1/OUT2 顶层 DAC 路由保持不变。该候选尚未完成新的 Vivado timing 或示波器验证，因此 OUT2 仍只能接示波器。

## 2026-06-22 v2B2/v2B3 sequential PI RTL/SIM 完成，等待 Vivado timing

v2B1 已关闭：OUT2 timing-safe P-only 安全输出已完成上板示波器验证，记录的 implementation 为 `WNS=+0.361 ns`、`TNS=0.000 ns`、`Failing Endpoints=0`，且 OUT2/OUT1 实测约为 `0.515` 与 `0.555`。

本轮新增 `pi_controller_seq.sv`，使用七状态顺序更新：`IDLE -> CAPTURE -> P_CALC -> I_CALC -> I_UPDATE -> SUM -> LIMIT`。完整 PI 算法保持 P、I、offset、对称限幅和 anti-windup 语义，但乘法、积分更新、求和、限幅分拍寄存，避免旧完整 PI 的单条长组合路径。

`laser_lock_core.sv` 现在使用：

```text
CONTROL_PATH_MODE=0：timing-safe P-only Shadow Control，当前默认回退路径。
CONTROL_PATH_MODE=1：新的 pi_controller_seq sequential PI，v2B3 目标路径。
CONTROL_PATH_MODE=2：旧 pi_controller，仅参考/仿真，不作默认板级路径。
```

本轮 XSim：

```text
tb_pi_controller_seq: tests=35 pass=35 fail=0
tb_laser_lock_core_v2b1_shadow_pi_dc_error: tests=27 pass=27 fail=0
```

当前仍不能声称 sequential PI 已 timing-clean 上板，也不能将 OUT2 接激光器、D2-125 Servo Output 或 Scan。下一步由用户手动把 `pi_controller_seq.sv` 加入 Vivado Design Sources 后检查 timing；只有 XSim、Vivado timing、OUT2 示波器都通过，才讨论低增益闭环。

## 2026-06-22 v2B1 timing-safe P-only Shadow Control 上板示波器测试完成

本次由用户完成 Vivado 重新综合、实现、bitstream 生成和 Red Pitaya 烧录；记录的 timing 结果为：

```text
WNS = +0.361 ns
TNS = 0.000 ns
Failing Endpoints = 0
```

本轮接线仅为 `OUT1 -> 示波器`、`OUT2 -> 示波器`。OUT2 没有接激光器、D2-125、Scan 或 Servo Output。

### 上板数据

| 数据文件 | OUT2 shadow control | Board OUT1 error | OUT2 / OUT1 | 其他同步观察 |
|---|---:|---:|---:|---|
| `mixer.csv` | Vpp `0.01771 V`，RMS `0.007694 V` | Vpp `0.03439 V`，RMS `0.003643 V` | `0.515` | Saturated absorption peak：Vpp `0.1893 V`，RMS `0.8157 V`；D2-125 error：Vpp `1.829 V`，RMS `0.3469 V` |
| `no-mixer.csv` | Vpp `0.02644 V`，RMS `0.006752 V` | Vpp `0.04768 V`，RMS `0.004388 V` | `0.555` | Saturated absorption peak：Vpp `0.1793 V`，RMS `0.8147 V`；D2-125 error：Vpp `0.0402 V`，RMS `0.2935 V` |

比例计算：

```text
mixer.csv:    0.01771 / 0.03439 = 0.515
no-mixer.csv: 0.02644 / 0.04768 = 0.555
```

### 实验结论

```text
2026-06-22 v2B1 timing-safe P-only Shadow Control 上板示波器测试完成。

1. OUT1 能输出 FPGA mixer+LPF 后的 error signal，幅度为几十 mVpp。
2. OUT2 能输出由 OUT1 派生的 P-only shadow control。
3. OUT2 / OUT1 比例约为 0.5。
4. OUT2 没有打到 +/-1 V。
5. OUT2 没有出现明显失控、饱和或积分爬升。
6. 该现象与 RTL 中 protected_error >>> 1 的 timing-safe P-only 设计一致。

阶段结论：v2B1 的 OUT2 控制输出通道已经打通。
当前版本可作为“OUT2 安全输出验证通过”的实验记录。
```

### 小白解释：为什么 OUT1 / OUT2 只有几十 mV

这是安全测试版本的正常现象，不是失败。OUT2 当前不是完整 PI/PID 的大范围控制量，而是将 `protected_error` 做 `>>> 1` 后的半幅 P-only 输出；同时没有数字增益放大、没有积分累积，因此 OUT1 和 OUT2 都保持在较小幅度，便于先验证 OUT2 输出通道是否安全、方向是否合理。

### 仍然有效的限制

```text
当前版本不是完整 PI。
当前版本不是 PID。
当前版本不能锁定激光。
当前版本不能声称替代 D2-125。
OUT2 仍然只能接示波器。
OUT2 禁止接激光器。
OUT2 禁止接 D2-125 Servo Output。
OUT2 禁止接 Scan。
D2-125 DC Error 禁止接 Red Pitaya IN1。
```

## 2026-06-16 当前主线：v2B1 timing-safe P-only Shadow Control（当前有效）

手动 Vivado Implementation 已暴露一个关键 timing 问题：完整 `pi_controller.sv` 直接放进 v2B1 主工程路径时，125 MHz 下未通过时序，记录现象约为 `WNS=-10.995 ns`、`TNS=-5029 ns`。最差路径位于：

```text
i_laser_lock_core/u_output_protect/data_o_reg
-> i_laser_lock_core/i_pi_controller
-> control_o_reg
```

该路径穿过 DSP48E1、CARRY4、48-bit integrator、anti-windup freeze、integrator_accepted、P+I+offset limiter 和 `control_o` 更新逻辑。结论是：完整 PI 算法仍然保留为 v2A 已验证核心，但不能再作为 v2B1 默认上板路径。

当前有效 RTL 策略：

```text
v0.94/rtl/pi_controller.sv：不修改，保留完整 PI + anti-windup，供后续 v2B2/v2B3 流水线化使用。
v0.94/rtl/laser_lock_core.sv：默认 USE_FULL_PI_CONTROLLER=0，使用 timing-safe P-only Shadow Control。
OUT1：继续观察 FPGA mixer+LPF error。
OUT2：只输出很小的 P-only shadow control，只接示波器。
```

当前默认板级链路：

```text
IN1 + IN2
-> mixer_core
-> lpf_core
-> output_protect
-> error_o / OUT1

同一个 protected_error
-> timing-safe P-only Shadow Control
-> control_o / OUT2
```

OUT2 预期：约为 OUT1 error 的 1/2，并受 `PID_OUTPUT_LIMIT_DEFAULT=1500` 限制，约 `+/-0.18 V`。当前仍不能接激光器，不能接 D2-125 Servo Output，不能接 Scan，不能声称已经闭环替代 D2-125。

本轮独立 XSim 回归：

```text
xvlog：0 error，0 warning
xelab：0 error，0 warning
xsim：tests=18 pass=18 fail=0
日志：v0.94/xvlog.log，v0.94/xelab.log，v0.94/xsim.log
```

## 2026-06-14 当前主线：v2B1 FPGA MTS Error Shadow PI（当前有效）

当前安全主线已经从旧的“D2-125 DC Error -> Red Pitaya IN1”旁路方案，修正为使用 Red Pitaya 自身 IN1/IN2 生成 FPGA 内部 error，并把该 error 同时送到 OUT1 观察和 OUT2 Shadow PI 控制输出。

### 当前硬件接线边界

```text
Red Pitaya IN1 -> 混频前 PD/MTS 信号，必须在 +/-1 V 内
Red Pitaya IN2 -> 外部 REF，必须在 +/-1 V 内
Red Pitaya OUT1 -> 示波器 CH2：FPGA mixer+LPF error，当前约 0.12~0.15 V
Red Pitaya OUT2 -> 示波器 CH4：FPGA P-only control
```

禁止：

```text
D2-125 DC Error -> Red Pitaya IN1
D2-125 Servo Output -> Red Pitaya IN1
Red Pitaya OUT2 -> 激光器
Red Pitaya OUT2 -> D2-125 Servo Output 三通
Red Pitaya OUT2 -> 激光器电源 Scan
任何超过 +/-1 V 的信号进入 IN1/IN2
```

### 当前代码状态

```text
v0.94/rtl/laser_lock_core.sv：
control_o 不再固定为 0，已接入 pi_controller。

v0.94/rtl/red_pitaya_top.sv：
OUT1 / DAC A 仍为 laser_error；
历史记录：当时 OUT2 / DAC B 曾改为 laser_control。当前 main 中 OUT2 / DAC B 的最终输出为 selected_out2。

v0.94/rtl/pi_controller.sv：
本次未修改，继续使用 v2A 已完成的 PI 控制器核心。

v0.94/sim/tb_laser_lock_core_v2b1_shadow_pi_dc_error.sv：
新增 v2B1 Shadow PI 行为仿真。
```

### 初始参数

```text
PID_ENABLE_DEFAULT = 1
PID_HOLD_DEFAULT = 0
PID_RESET_INTEGRATOR_DEFAULT = 0
PID_POLARITY_DEFAULT = 0
PID_KP_DEFAULT = 16'sd2048
PID_KI_DEFAULT = 16'sd0
PID_OFFSET_DEFAULT = 14'sd0
PID_OUTPUT_LIMIT_DEFAULT = 14'd1500
PID_UPDATE_HZ = 10_000
```

含义：

```text
Kp=2048：OUT2 约为 OUT1 error 的 1/2
Ki=0：避免 OUT2 积分慢慢爬升
output_limit=1500：约 +/-0.18 V，防止 OUT2 接近 +/-1 V
```

### 独立仿真状态

```text
xvlog：0 error
xelab：0 error
xsim：SUMMARY tests=13 pass=13 fail=0
```

### 本轮不执行

```text
Codex 不运行 Vivado
Codex 不运行 synthesis
Codex 不运行 implementation
Codex 不生成 bitstream
Codex 不生成 bin
Codex 不烧录 Red Pitaya
Codex 不修改 redpitaya.xpr
```

Vivado、bitstream、bin 和烧录由用户手动完成。

## 2026-06-14 旧方案记录：v2B1 Shadow PI DC Error（已废弃 / 禁止执行）

> 注意：本节保留为历史记录，不再作为当前执行路线。禁止把 D2-125 DC Error 或 D2-125 Servo Output 接入 Red Pitaya IN1。当前有效主线见本文档最前面的“v2B1 FPGA MTS Error Shadow PI”。

当前下一步不是 `ramp_generator`，不是完整 `scan/lock`，也不是 FPGA 直接替代 D2-125。当前下一步定义为：

```text
v2B1 Shadow PI DC Error 旁路测试

D2-125 DC Error
-> Red Pitaya IN1
-> pi_controller
-> OUT2 示波器
```

当前真实接线：

```text
模拟 mixer 后 error -> D2-125 Error Input
D2-125 Servo Output -> 三通 -> 激光器电源 / 激光器锁定控制端
D2-125 Aux Servo Output -> 激光器电源 Scan
D2-125 Ramp -> 示波器 CH1
D2-125 DC Error -> 示波器 CH3，后续接 Red Pitaya IN1
Red Pitaya OUT2 -> 后续示波器 CH4
```

v2A 已完成的是 FPGA 版 D2-125 Servo Core，不是完整 D2-125 替代：

```text
D2-125 Error Input -> Servo PI/PID -> Servo Output
对应
error_i -> pi_controller.sv -> control_o
```

v2A2 独立仿真报告结论：

```text
tb_pi_controller summary: tests=165 pass=165 fail=0
```

这只证明 `pi_controller.sv` 独立 testbench 通过，不证明它已进入主工程、已接 OUT2、已生成 bitstream、已上板或已控制激光。

下一步代码边界：

```text
允许修改：
v0.94/rtl/laser_lock_core.sv
v0.94/rtl/red_pitaya_top.sv

允许新建：
v0.94/sim/tb_laser_lock_core_v2b1_shadow_pi_dc_error.sv

禁止修改：
v0.94/rtl/pi_controller.sv
v0.94/rtl/mixer_core.sv
v0.94/rtl/lpf_core.sv
v0.94/rtl/output_protect.sv
```

本轮文档任务不修改任何 `.sv`，不运行 XSim，不运行 Vivado，不生成 bitstream，不上板。

## 2026-06-15 注释与路线清理状态

本轮允许对 RTL/SIM 增加解释性注释，但不允许改变功能逻辑。当前已经把 v2B1 的有效路线固定为：

```text
IN1 + IN2 -> mixer_core -> lpf_core -> output_protect -> error_o -> OUT1
error_o -> pi_controller -> control_o -> OUT2
```

所有后续文档和代码注释都必须把 `D2-125 DC Error -> Red Pitaya IN1` 视为历史废弃路线，不得作为当前接线方案。OUT1 在 v2B1-v2F 继续作为 error observation；OUT2 第一阶段只接示波器。

## 当前阶段

```text
v2A 的 PI 核心初次实现完成；
v2a-2 等待一次 Claude Code 集中审查；
下一主阶段为 v2B 系统集成。
```

## 当前协作原则

每个子阶段最多一次 Claude Code 集中审查和一次 Codex 修正。通过回归仿真后关闭子阶段，不再循环审查。

## v1 状态

v1 已完成 FPGA 数字解调基础链路：

```text
PD -> ADC -> mixer -> LPF -> error-like signal -> OUT1 -> D2-125 -> Laser
```

含义：FPGA 已经能产生可用于 D2-125 的 error-like signal。当前真正闭环控制激光的仍然是 D2-125。

## v2 总目标

```text
用 FPGA 数字 PI 逐步替代 D2-125 的基础 servo 功能。
```

v2 目标链路：

```text
PD -> ADC -> mixer -> LPF -> pi_controller -> OUT2 -> Laser actuator
```

OUT1 在 v2B-v2F 始终保留为 error observation。OUT2 第一阶段只接示波器。

## v2 阶段图

```text
v2A：独立数字 PI 核心
  v2a-1：P-only
  v2a-2：I + anti-windup

v2B：系统接口和主工程集成
v2C：Vivado 综合、实现、时序、DRC 和 bitstream
v2D：OUT2 示波器空载上板测试
v2E：真实 MTS error 输入、OUT2 开环观察
v2F：低增益闭环替代 D2-125
v2G：FPGA PI 与 D2-125 性能对比
```

## v2A 当前记录

- v2a-1：P-only 已关闭；不再重复 GPT 或 Claude Code 审查。
- v2a-2：I 通道、integrator 和 anti-windup 已完成初次实现和独立 XSim 回归；等待一次 Claude Code 集中审查。

## v2B 开始前必须回答

1. OUT2 接激光的哪个控制端。
2. 该端允许的电压范围。
3. 控制极性。
4. 执行器响应带宽。
5. 初始 `pid_ce` 频率。

## 当前禁止事项

- 不修改 RTL，除非用户另行明确授权。
- 不运行 XSim，除非用户另行明确授权。
- 不运行 Vivado。
- 不生成 bitstream。
- 不上板。
- 不把 OUT2 接激光。
- 不开始 CNN。
- 不开始相位自动匹配。
- 不开始双 PID。

## 关键文档

- `E:\new\fpga_lock\v94\version\v2\V2_SYSTEM_ARCHITECTURE_AND_STAGE_MAP.md`
- `E:\new\fpga_lock\v94\version\v2\V2_GOAL_AND_CHAIN.md`
- `E:\new\fpga_lock\v94\version\v2\V2_DEVELOPMENT_ROADMAP.md`
- `E:\new\fpga_lock\v94\version\v2\V2_NEXT_STEPS.md`
- `E:\new\fpga_lock\v94\version\v2\GPT_REVIEW_V2_SUMMARY.md`

## 2026-07-12 v3LOCK-P0 APPLY P host fix
- 本次只修改上位机，不修改 RTL / testbench / Vivado project。
- 新增 `update-p-lock` / GUI `APPLY P`：LOCK HERE 后仅小步更新 Kp/polarity，不重新捕获或覆盖 `ERROR_SETPOINT` / `LOCK_BIAS`。
- Kp 仅允许 `0, 4, 8, 16, 32`；非零 Kp 下禁止直接翻转 polarity，需先 APPLY P 到 Kp=0。
- 已通过 `py_compile` 和 `python -m pytest tests`；未运行 Vivado、未生成 bitstream、未烧录、未声明真实稳频完成。
- 下一步唯一人工任务：上板按 `SCAN -> 选择过零点 -> LOCK HERE -> APPLY P 小步 Kp -> 判断 polarity -> 异常 SAFE` 验证。

## 2026-07-12 BASIC LOCK 小白版上位机收敛
- 本次只修改上位机与现有日志，不修改 RTL / testbench / Vivado project。
- 修复 `Custom FPGA Scope` 黑屏风险：显式设置黑底亮轴、亮字、曲线颜色、placeholder 引用和 CH3/CH4 显示 range。
- 新增 BASIC LOCK 顶层入口：用户只需输入 PZT safe min/max，自动计算 offset/amp/freq/step/capture decimation，并用当前 capture 寻找候选 zero crossing。
- BASIC LOCK 仍不是 AI、不是自动重锁、不是长期稳频证明；失败或异常必须 SAFE。
- 已通过 `py_compile` 和 `python -m pytest tests`，结果 `28 passed`；未运行 Vivado、未生成 bitstream、未烧录。
## 2026-07-12 BASIC LOCK 联调阻塞修复
- 本次只修改上位机和现有日志，不修改 RTL / testbench / Vivado project，不运行 Vivado，不生成 bitstream，不烧录。
- 修复 BASIC LOCK 内部 SAFE 步骤会清空自身状态机的问题；内部流程可继续 SAFE -> SCAN -> CAPTURE -> CANDIDATE_FOUND -> CAPTURE_LOCK_POINT -> P_LOCK。
- 启动时自动做只读 status 探测，显示 MAGIC / VERSION / MODE / ENABLE / STATUS / OUT2；失败时显示通信或寄存器原因，不再只显示 `--`。
- `custom_debug_capture` 无数据时明确提示真实 FPGA capture 接口不可用，不伪造波形；无完整波形寄存器时不能替代为 status 单点采样。
- LOCK HERE 成功后停在 MODE=3 P_LOCK 且 Kp=0；后续 Kp 仍需用户手动 APPLY P，禁止自动 Ki/PI。
