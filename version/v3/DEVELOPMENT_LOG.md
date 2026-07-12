# v3 开发日志

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
