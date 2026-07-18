# Lock Workflow Mode 工作流

> **SUPPORTING / NOT A RULE ENTRY**：本文件只说明现有 GUI 过程视图。当前 Gate、禁止事项和唯一实验以 `version/STATUS.md` 顶部及 `version/rules/20_FPGA_MTS_ENGINEERING_WORKFLOW.md` 为准。

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
-> Linien-style minimal FPGA scan-to-lock FSM（Gate L0 诊断完成后才可设计）

D2-125 Relock / Lock Quality
-> 当前禁止开展；基础 P-only 硬件通过后另行授权
```

## 当前步骤

1. 输入安全检查。
2. error signal 观察。
3. OUT2 control / selected_out2 观察。
4. 方向和 polarity 检查。
5. gain / limit 检查。
6. Gate L0：比较 HOLD 与 LOCK HERE 的 Kp=0 结果。
7. Gate L0 完成后再设计 FPGA 原子 scan-to-lock。
8. 基础 P-only 通过前不开展 Relock。

每一步都必须记录接线、示波器观察内容、通过标准、停止条件和下一步。

## 当前限制

当前 Gate 只诊断：`SCAN -> 选择同一目标/方向 -> HOLD SELECTED COUNT -> 记录 -> SAFE -> 同一目标/方向 -> LOCK HERE, Kp=0 -> 记录 -> SAFE`。Gate L0 未通过前不得 Apply Kp。

OUT2 的目标执行器是激光器专用 PZT / Scan 输入。禁止接激光器电流调制输入、D2-125 Servo Output、D2-125 Aux Output，禁止两个设备输出端并联。必须限制幅度、偏置、`LOCK_CORRECTION_LIMIT` 和 `LOCK_LIMIT`；错误 polarity、持续 saturation、输出冲限或通信失败时立即 SAFE。
