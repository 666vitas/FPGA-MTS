# Lock Workflow Mode 工作流

> **SUPPORTING / NOT A RULE ENTRY**：本文件只说明 GUI 过程视图和 D1 目标流程。当前 Gate、禁止事项和唯一下一动作以 `version/STATUS.md` 顶部及 `version/rules/20_FPGA_MTS_ENGINEERING_WORKFLOW.md` 为准。

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
-> deterministic FPGA acquisition FSM（当前 Gate D1-A/D1-B）

D2-125 Relock / Lock Quality
-> 当前禁止开展；基础 P-only 硬件通过后另行授权
```

## 当前 D1 步骤

1. 冻结 target shadow registers、ARM/ABORT、state/event、fault 和验收契约。
2. 实现并仿真 FPGA acquisition FSM。
3. host 预装 target 并 ARM；Linux 退出实时触发判断。
4. 软件/RTL 集成验证。
5. 编写但不执行新硬件 SOP。
6. 用户验证 Kp=0 deterministic transition。
7. 用户批准最小非零 Kp。
8. 基础 P-only 通过前不开展 Relock。

每一步都必须记录接线、示波器观察内容、通过标准、停止条件和下一步。

## 当前与目标路径

当前 legacy 路径：

```text
host target wait -> CAPTURE_LOCK_POINT
```

D1 目标路径：

```text
capture -> user select -> confirm -> preload target -> ARM
-> FPGA 自主等待 scan direction + target window + ERROR crossing
-> FPGA 原子进入 P_LOCK_KP0
-> host 只读状态和事件
```

原 Gate L0 HOLD/LOCK HERE A/B 是保留但暂缓的 historical/superseded diagnostic path，不删除、不标为 PASS。当前不进行硬件实验；新硬件 SOP 等软件和 RTL 仿真通过后再生成。

OUT2 的目标执行器仍只允许是激光器专用 PZT / Scan 输入。禁止接激光器电流调制输入、D2-125 Servo Output、D2-125 Aux Output，禁止两个设备输出端并联。必须限制幅度、偏置、`correction_limit` 和 `absolute_limit`；错误 polarity、持续 saturation、输出冲限或通信失败时立即 SAFE。
