# 06_V2_PID_DEVELOPMENT_RULES

## 1. v2 目标

v2 目标是用 FPGA PI/PID 逐步替代 D2-125 的基本 servo 功能。

## 2. v2 第一版边界

第一版只做独立 pi_controller.sv 和 tb_pi_controller.sv。
不接顶层，不生成 bitstream，不上板，不闭环。

v2a 默认不运行任何工具。

用户明确批准后，可以运行仅包含
pi_controller.sv + tb_pi_controller.sv
的独立 XSim 仿真。

独立仿真不等于允许：
- 接入 Vivado 主工程；
- 综合；
- 实现；
- bitstream；
- 上板；
- OUT2；
- 激光闭环。

## 3. D2-125 替代边界

D2-125 是 PI^2D，不是普通 PID。
v2 第一版 PI 只是最小可行闭环验证，不是完整复刻 D2-125。
D2-125 main/aux output 可到 ±10 V，Red Pitaya OUT2 约 ±1 V，不能直接等价。
D2-125 error input max 为 ±500 mV，必须做幅度映射。

## 4. PI controller 必须具备

- pid_ce_i
- enable_i
- hold_i
- reset_integrator_i
- polarity_i
- kp_i
- ki_i
- offset_i
- output_limit_i
- control_o
- p_term_o / i_term_o / sat_o debug 输出

## 5. 安全默认值

- enable 默认 0
- reset 后 control_o = 0
- ki 初始 0
- kp 初始极小
- output_limit 初始很小
- OUT2 第一阶段只接示波器

## 6. 开发顺序

1. GPT 审查文档
2. 写独立 pi_controller.sv
3. 写 tb_pi_controller.sv
4. 仿真 P-only
5. 仿真 I-only
6. 仿真 PI
7. 仿真 saturation / anti-windup
8. GPT / Claude Code 审查
9. 再考虑接 laser_lock_core.sv
10. 再考虑 OUT2 示波器
11. 最后才考虑低增益接入实验链路

## 7. 禁止事项

- 不直接完整 PID
- 不直接 D 通道
- 不直接 AI
- 不直接闭环
- 不直接接激光
- 不破坏 v1 OUT1 error 输出
- 不把 D2-125 的 4 MHz Peak Lock dither 和当前 MTS 4.6 MHz REF 混淆
- 不把 digital gain 当作模拟低噪声放大器
