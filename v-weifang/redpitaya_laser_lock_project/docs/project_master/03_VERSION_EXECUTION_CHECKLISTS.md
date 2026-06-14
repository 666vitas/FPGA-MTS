# 版本执行清单

这个文件是最实用的操作清单。每次准备做一个版本时，先看对应章节；如果没有通过上一版本，不要急着进入下一版本。

当前最新顺序：

```text
Step 1: v1ab-1 IN1 -> OUT1
Step 2: v1ab-2 IN2 -> OUT1
Step 3: 两步都真实上板通过后，才进入 v1c_mixer_only
```

当前实际进度：

- `v1ab` RTL 已生成；
- testbench 已通过；
- Vivado `synthesis / implementation / bitstream` 已成功；
- `.bit` 已转换为 `.bit.bin`；
- `.bit.bin` 已上传到 Red Pitaya；
- `fpgautil -b /root/red_pitaya_top.bit.bin` 已显示 `BIN FILE loaded through FPGA manager successfully`；
- 但还没有实际连接信号发生器和示波器完成物理测试。

因此当前下一步不是写 mixer，而是做 `v1ab-1：IN1 -> OUT1`。

## v1ab-1：Vivado 编译检查

当前状态：这一项已经完成过。以后如果改 `LASER_LOCK_OUTPUT_MODE` 或重新生成 bitstream，仍要按本节重新检查。

### 需要理解什么

- `red_pitaya_top` 是总接线板；
- `laser_lock_core.sv` 和 `output_protect.sv` 只是子模块；
- 文件放在 `rtl` 目录里，不等于 Vivado 一定会综合它；
- 必须确认它们出现在 Vivado `Design Sources` 中。

### 需要检查哪些文件

- `E:\new\fpga_lock\v94\v0.94\rtl\red_pitaya_top.sv`
- `E:\new\fpga_lock\v94\v0.94\rtl\laser_lock_core.sv`
- `E:\new\fpga_lock\v94\v0.94\rtl\output_protect.sv`

### Vivado 操作

- 打开 `.xpr`；
- 确认 `Design Sources`；
- 确认 top 是 `red_pitaya_top.sv`，不要把 `laser_lock_core.sv` 设成 top；
- 确认 `i_laser_lock_core` 出现在 `red_pitaya_top` 层级下；
- 确认 `laser_lock_core.sv` 和 `output_protect.sv` 没有重复添加；
- 确认 `USE_LASER_LOCK_CORE = 1'b1`；
- 确认 `LASER_LOCK_OUTPUT_MODE = 0`；
- `Run Synthesis`；
- `Run Implementation`；
- `Generate Bitstream`。

### 报错时发给 GPT 的内容

如果 Vivado 报错，不要只发截图最后一行。请发：

- 当前版本：`v1ab-1`；
- 当前步骤：`Run Synthesis` / `Run Implementation` / `Generate Bitstream`；
- 完整错误文本；
- 报错文件名和行号；
- Vivado `Sources` 中是否能看到 `laser_lock_core.sv` 和 `output_protect.sv`；
- 当前 `USE_LASER_LOCK_CORE`；
- 当前 `LASER_LOCK_OUTPUT_MODE`；
- 最近修改过哪些文件。

## v1ab-2：上板测试 IN1 -> OUT1

这是当前马上要做的 Step 1。

### 前提

- `v1ab-1` 已通过；
- bitstream 对应 `LASER_LOCK_OUTPUT_MODE = 0`；
- `OUT1` 只接示波器；
- 不接 `D2-125`；
- 不接真实 `PD`；
- 不接激光器反馈。

### 接线

- `OUTPUT_MODE=0`；
- 信号发生器 `OUT -> IN1`；
- `OUT1 -> 示波器 CH1`；
- 输入参考 `-> 示波器 CH2`。

### 输入信号

```text
1 kHz sine
100 mVpp
0 V offset
```

### 通过标准

- `OUT1` 有和输入同频的波形；
- 幅度可以不同；
- 极性可以反相；
- 不削顶；
- 不顶死；
- `OUT2` 无异常输出。

### 示波器应该看到什么

- CH2 应该看到输入参考：`1 kHz sine, 100 mVpp, 0 V offset`；
- CH1 应该看到 `OUT1` 上的 1 kHz 同频波形；
- 幅度不同、反相、有少量延迟或噪声都可以先记录，不要立刻判为失败；
- 如果 CH2 都没有输入波形，先查信号发生器和线缆，不要查 RTL。

### 失败排查

- bitstream 是否是 `OUTPUT_MODE=0`；
- `USE_LASER_LOCK_CORE` 是否为 1；
- 信号发生器是否真的有输出；
- 输入是否真的接到 `IN1`；
- 示波器触发和量程是否正确；
- `OUT1/OUT2` 是否接反；
- reset 是否释放；
- `laser_lock_core.sv` 和 `output_protect.sv` 是否加入 Vivado。

## v1ab-3：上板测试 IN2 -> OUT1

这是 Step 2。只有 `v1ab-2：IN1 -> OUT1` 已经通过，才做本节。

### 前提

- `v1ab-2` 已通过；
- 需要把 `LASER_LOCK_OUTPUT_MODE` 改为 1；
- 修改后必须重新 `Run Synthesis` / `Run Implementation` / `Generate Bitstream`；
- 重新转换 `.bit.bin`；
- 重新 `scp` 上传；
- 重新用 `fpgautil` 加载；
- `OUT1` 仍然只接示波器；
- 不接 `D2-125`；
- 不接真实 `PD`；
- 不接激光器反馈。

### 接线

- `OUTPUT_MODE=1`；
- `4.6 MHz REF` 安全衰减后 `-> IN2`；
- `OUT1 -> 示波器 CH1`；
- 安全衰减后的 `REF -> 示波器 CH2`。

### 输入信号

```text
4.6 MHz
100-500 mVpp
0 V offset
```

禁止：

```text
6.32 Vpp 直接进 IN2。
不要第一次就直接 ±1 V 满幅测试。
```

### 通过标准

- `OUT1` 能看到 4.6 MHz 同频波形；
- `IN2` 输入幅度安全；
- 不削顶；
- 不长时间顶死；
- `OUT2` 无异常输出。

### 失败排查

- 是否已经重新生成 `OUTPUT_MODE=1` 的 bitstream；
- `REF` 是否真的经过安全衰减；
- 示波器是否能在进板前看到 `REF`；
- 输入是否真的接到 `IN2`；
- `IN1/IN2` 是否接反；
- `OUT1/OUT2` 是否接反；
- 如果失败，先回到 `v1ab-2` 的 `IN1 -> OUT1`。

## v1c 执行清单

进入门槛：

```text
v1ab IN1 -> OUT1 已真实上板通过
v1ab IN2 -> OUT1 已真实上板通过
```

只要任何一项没有通过，就不允许进入 v1c。

### 需要理解什么

- mixer 的本质是 signed 乘法；
- 14-bit `pd_i` 乘 14-bit `ref_i` 会得到更宽的结果；
- 乘法结果必须缩放回适合 DAC 的范围；
- 这一版还没有 LPF，所以 `OUT1` 可能仍有高频成分。

### 需要检查哪些文件

- `laser_lock_core.sv`
- `mixer_core.sv`
- `output_protect.sv`
- 对应 `tb_laser_lock_core_v1c.sv`

### Vivado 操作

- Add Sources 加入 `mixer_core.sv`；
- 确认 `laser_lock_core.sv` 是最新版本；
- 重新 `Run Synthesis`；
- 重新 `Run Implementation`；
- 重新 `Generate Bitstream`。

### 实验操作

- 用两个安全小信号分别进 `IN1` 和 `IN2`；
- 第一次建议使用低频同频信号，例如 `100 kHz / 100 kHz`；
- 先用信号发生器，不接真实 PD；
- 不接真实 4.6 MHz REF；
- `OUT1` 只接示波器。

### 成功标准

- `OUT1` 随 `IN1/IN2` 变化；
- 输出不恒为 0；
- 输出不长期满幅；
- signed 极性和仿真一致。

### 失败排查

- 回到 `v1ab` 分别确认 `IN1` 和 `IN2`；
- 检查 signed 位宽；
- 检查缩放右移方向；
- 检查 mixer 输出是否被 reset 或保护逻辑清零。

## v1d 执行清单

### 需要理解什么

- mixer 后会有高频分量；
- LPF 的作用是留下低频解调结果；
- LPF 会引入延迟，这是正常现象；
- reset 时滤波器内部状态必须清零。

### 需要检查哪些文件

- `laser_lock_core.sv`
- `mixer_core.sv`
- `lpf_core.sv`
- `output_protect.sv`
- 对应 testbench。

### Vivado 操作

- Add Sources 加入 `lpf_core.sv`；
- 检查 Sources 中没有旧版重复文件；
- `Run Synthesis`；
- `Run Implementation`；
- `Generate Bitstream`。

### 实验操作

- 用模拟 `PD/REF` 输入；
- 改变相位或幅度；
- 观察 `OUT1` 是否变成更平滑的低频输出。

### 成功标准

- `OUT1` 比 v1c 更平滑；
- 对输入变化有响应；
- 不顶死；
- 不严重削顶。

### 失败排查

- 旁路 LPF 回到 `v1c`；
- 检查 LPF 系数；
- 检查滤波器位宽；
- 降低输入幅度。

## v1e 执行清单

### 需要理解什么

- 这是第一次接真实 `PD` 和真实外部 `REF`；
- 真实信号会有 offset、噪声、幅度变化；
- 目标不是完美锁定，而是看到 `error-like signal`。

### 需要检查哪些文件

- v1d 全部 RTL；
- 当前 gain/scale 设置；
- 当前 BOARD_TEST；
- 当前 REPORT。

### Vivado 操作

- 使用 v1d 通过后的工程；
- 如果只改参数，也要重新生成 bitstream；
- 保存 bitstream 对应版本说明。

### 实验操作

- `PD -> IN1`；
- 安全衰减后的 `4.6 MHz REF -> IN2`；
- `OUT1 -> 示波器`；
- 记录模拟链路 error 作为对照。

### 成功标准

- `OUT1` 出现随实验变化的 `error-like signal`；
- 幅度安全；
- offset 不离谱；
- 不接 D2-125。

### 失败排查

- 用信号发生器替代真实 PD；
- 回到 `v1d`；
- 回到 `v1ab`；
- 重新确认 `REF` 幅度和 `PD` 幅度。

## v1f_bpf_gain_enable 执行清单

### 需要理解什么

- BPF / gain 是为了替代模拟 `10 MHz LPF + 1.8 MHz HPF + RF amplifier` 的前处理和放大作用；
- BPF 参数必须围绕 `4.6 MHz` 设计；
- 数字滤波器系数不能直接照搬模拟滤波器参数；
- 必须根据 ADC 采样率、中心频率、带宽和定点位宽重新设计；
- 初期必须保留 bypass，方便回退。

### 需要检查哪些文件

- `adc_frontend.sv` 或 `bpf_core.sv`；
- gain / scaling 相关模块或逻辑；
- `laser_lock_core.sv`；
- `mixer_core.sv`；
- `lpf_core.sv`；
- testbench。

### Vivado 操作

- Add Sources 加入 BPF/前端模块；
- 检查是否引入 timing 风险；
- 完整生成 bitstream。

### 实验操作

- 同一组真实 PD/REF，分别测试 BPF bypass 和 BPF enable；
- `OUT1` 只接示波器；
- 对比模拟 mixer 输出。

### 成功标准

- BPF enable 后目标频率成分更突出；
- error-like signal 不被破坏；
- 输出安全。

### 失败排查

- 关闭 BPF；
- 降低滤波阶数；
- 重新计算系数；
- 回到 `v1e`。

## v1g 执行清单

### 需要理解什么

- 这是第一次允许考虑 `OUT1 -> D2-125 error input`；
- 只有示波器确认 `OUT1` 幅度和 offset 安全后，才允许接 D2-125；
- 仍不让 FPGA 直接接激光器反馈。

### 需要检查哪些文件

- v1f 全部 RTL；
- gain/offset/limit 保护；
- BOARD_TEST_v1g；
- D2-125 输入安全范围记录。

### Vivado 操作

- 使用 v1f 通过后的工程；
- 确认输出保护已经启用；
- 生成明确命名 bitstream。

### 实验操作

- `OUT1 -> 示波器`；
- 确认安全后，`OUT1 -> D2-125 error input`；
- 观察 D2-125 行为；
- 保持人工监控。

### 成功标准

- D2-125 能接收 FPGA error；
- 没有异常饱和；
- 断开 FPGA 后系统可回到原模拟链路。

### 失败排查

- 立即断开 D2-125；
- 回到示波器；
- 回到 `v1f`；
- 降低 gain 或增加 limit。

## v2 执行清单

### 需要理解什么

- `v2_fpga_pid` 是用 FPGA 自己算 PID；
- `error_o` 变成 PID 输入；
- `control_o` 变成控制输出候选；
- `OUT2` 必须先接示波器或假负载。

### 需要检查哪些文件

- `pid_lock_core.sv`
- `laser_lock_core.sv`
- PID testbench
- PID safety report

### Vivado 操作

- Add Sources 加入 PID；
- 检查乘法器和 timing；
- 生成测试 bitstream。

### 实验操作

- 假 error 输入；
- `OUT2 -> 示波器`；
- 不直接闭环激光器。

### 成功标准

- `OUT2` 对 error 有合理响应；
- reset/disable 时安全；
- 不积分失控。

### 失败排查

- PID disable；
- 积分项清零；
- 回到 v1g。

## v3 执行清单

### 需要理解什么

- sweep 是慢速扫描；
- 目标约 `50 Hz`、约 `400 mVpp`；
- sweep 不是 MTS 解调本身，是后续找峰和锁定辅助。

### 需要检查哪些文件

- sweep generator；
- amplitude/offset limit；
- testbench；
- board test。

### Vivado 操作

- Add Sources；
- 综合实现；
- 生成测试 bitstream。

### 实验操作

- `OUT` 先接示波器；
- 测频率、幅度、offset；
- 不接激光器反馈。

### 成功标准

- 频率约 `50 Hz`；
- 幅度约 `400 mVpp` 或按实验要求可调；
- enable/disable 正常。

### 失败排查

- disable sweep；
- 检查计数器；
- 检查 DAC scaling。

## v4 执行清单

### 需要理解什么

- FSM 是状态机；
- 它决定 scan、find peak、lock、lost lock、relock；
- 每个状态必须有安全出口。

### 需要检查哪些文件

- `lock_relock_fsm.sv`
- 状态定义文档；
- testbench；
- safety report。

### Vivado 操作

- Add Sources；
- 综合检查状态机；
- 不允许出现未知状态无处理。

### 实验操作

- 先离线或半自动；
- 记录状态；
- 不无人值守。

### 成功标准

- 状态转换正确；
- 失锁能回到扫描；
- enable/disable 安全。

### 失败排查

- FSM disable；
- 回到手动模式；
- 回到 v3。

## v5 执行清单

### 需要理解什么

- AI 初期建议在 PC/PS 端，不急着放进 FPGA PL；
- FPGA 可以负责输出数据窗口、特征和状态；
- AI 不能未经审查直接控制激光器。

### 需要检查哪些文件

- 数据导出逻辑；
- feature extraction；
- AI 离线脚本；
- 数据集记录。

### Vivado 操作

- 只综合必要的数据导出模块；
- 不把复杂 AI 模型直接塞进 PL。

### 实验操作

- 采集 error/sweep/lock state；
- 人工标注；
- 离线验证 AI 判断。

### 成功标准

- AI 能辅助识别峰和锁定状态；
- 不影响 FPGA 主链路；
- AI disable 后系统仍可手动工作。

### 失败排查

- AI disable；
- 回到 FSM；
- 回到人工判断。
