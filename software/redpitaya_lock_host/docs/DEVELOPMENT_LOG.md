# 开发日志

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
