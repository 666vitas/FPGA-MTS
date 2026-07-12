# 项目上下文

## 固定项目边界

- FPGA 工程目录：`E:\new\fpga_lock\v94\v0.94`
- 上位机开发目录：`E:\new\fpga_lock\v94\software\redpitaya_lock_host`
- 旧的独立上位机目录不再使用；`software/redpitaya_lock_host` 是唯一上位机开发目录。
- 不使用、不引用、不修改任何包含 `weifang` 的目录。
- 除非用户明确授权，Codex 不运行 Vivado，不生成 bitstream，不烧录 Red Pitaya。

## 硬件平台

- Red Pitaya STEMlab 125-14
- 上位机软件栈：Python 3.10+、PySide6、pyqtgraph、numpy、pandas、pyyaml、socket
- SCPI 默认目标：`rp-f0cb13.local:5000`，GUI 中可手动修改

## 当前实验链路

1. PD 信号经过模拟 BPF 和放大器后进入 Red Pitaya IN1。
2. 外部 4.6 MHz REF 进入 Red Pitaya IN2。
3. FPGA 工程位于 `E:\new\fpga_lock\v94\v0.94`。
4. 当前 FPGA 用作 digital mixer + LPF；OUT1 输出 error-like signal，即 `laser_error`。
5. OUT2 当前为 `selected_out2`，由 `custom_register_bank`、`ramp_generator` 和 `out2_lock_controller` 候选模式控制。
6. v3REG-0 SAFE/SCAN 已完成用户上板验证；HOLD/P_LOCK/PI_LOCK 尚未完成 timing、bitstream 和上板验证。

## V2 模式边界

上位机分为两条路径：

- Official SCPI Mode：可以启动 `redpitaya_scpi`，连接 5000 端口，控制官方 ASG OUT1/OUT2，并通过 SCPI 采集 IN1/IN2。启动 `redpitaya_scpi` 可能加载官方 v0.94 overlay，并覆盖当前 custom FPGA bitstream。
- Custom FPGA Mode：保留当前 custom bitstream。当前 RTL 中 `USE_LASER_LOCK_CORE = 1`，OUT1 / DAC A 是 `laser_error`，OUT2 / DAC B 是 `selected_out2`，官方 ASG data 不再直接驱动物理 OUT1/OUT2。

Custom FPGA Mode 下，OUT2 的目标执行器是激光器专用 PZT / Scan 输入。`MODE=1 SCAN` 用三角波驱动 PZT 扫描，`MODE=3 P_LOCK` 用 `LOCK_BIAS + P correction` 驱动同一个 PZT 做基础反馈，`MODE=0 SAFE` 退出扫描和反馈。

上位机当前可以通过 SSH + `/dev/mem` 写 custom FPGA 寄存器。必须限制 OUT2 幅度、偏置、`LOCK_CORRECTION_LIMIT` 和 `LOCK_LIMIT`；禁止 OUT2 接激光器电流调制输入、D2-125 Servo Output、D2-125 Aux Output，禁止两个设备输出端并联。
