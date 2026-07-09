# Lock Workflow Mode 工作流

Lock Workflow Mode 是上位机中用于逐步替代 D2-125 工作流程的过程视图。它不是自动锁定控制器。

## D2-125 替代关系

```text
D2-125 Ramp
-> FPGA scan generator / Custom FPGA SCAN

D2-125 Error Input
-> FPGA mixer + LPF -> laser_error

D2-125 Servo Output
-> future safe actuator path

D2-125 Lock/Scan switch
-> future FPGA FSM + host Lock Workflow（后续功能）

D2-125 Relock / Lock Quality
-> future host judgment + FPGA state machine
```

## 当前步骤

1. 输入安全检查。
2. error signal 观察。
3. OUT2 control / selected_out2 观察。
4. 方向和 polarity 检查。
5. gain / limit 检查。
6. 低增益锁定测试准备状态判断。
7. 未来 Lock Engage。
8. 未来 Relock。

每一步都必须记录接线、示波器观察内容、通过标准、停止条件和下一步。

## 当前限制

v3REG-0 SAFE/SCAN 已经由用户上板验证。当前 RTL / software 已包含 HOLD / P_LOCK / PI_LOCK 候选入口，但它们尚未完成 Vivado timing、bitstream、烧录和上板验证。

在完成 scope-only 验证和安全 SOP 前，OUT2 只能接示波器，不允许接 PZT、Scan input、激光器电流调制、D2-125 Servo Output 或 D2-125 Aux Output。
