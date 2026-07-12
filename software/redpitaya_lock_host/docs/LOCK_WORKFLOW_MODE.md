# Lock Workflow Mode 工作流

Lock Workflow Mode 是上位机中用于逐步替代 D2-125 工作流程的过程视图。它不是自动锁定控制器。

## D2-125 替代关系

```text
D2-125 Ramp
-> FPGA scan generator / Custom FPGA SCAN

D2-125 Error Input
-> FPGA mixer + LPF -> laser_error

Red Pitaya OUT2
-> 激光器专用 PZT / Scan 输入

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

当前最小闭环是人工操作的 PZT 基础稳频：`SCAN -> 观察 MTS error -> 点击色散过零点 -> LOCK HERE -> Kp=0 捕获锁点 -> Apply Kp 小步增加 -> SAFE`。

OUT2 的目标执行器是激光器专用 PZT / Scan 输入。禁止接激光器电流调制输入、D2-125 Servo Output、D2-125 Aux Output，禁止两个设备输出端并联。必须限制幅度、偏置、`LOCK_CORRECTION_LIMIT` 和 `LOCK_LIMIT`；错误 polarity、持续 saturation、输出冲限或通信失败时立即 SAFE。
