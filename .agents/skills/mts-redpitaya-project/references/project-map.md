# 项目地图

## 身份与当前基线

- 仓库：`666vitas/FPGA-MTS`；正式主线：`main`。
- 最终目标：基于 Red Pitaya 的全自动深度学习参数优化 MTS 激光稳频系统。
- 长期分工：FPGA 负责数字解调、误差、快速控制、限幅和保护；上位机负责扫描、锁点、参数、观察、采集和记录；AI 后续负责识别、建议、优化、重锁、异常检测和分析。
- 当前基线仅供启动定位，不能替代每次读取的 `STATUS.md`、manifest 和当前代码：v3LOCK-P0、人工锁点、P-only 小增益、`MODE=0/1/2/3/4 = SAFE/SCAN/HOLD/P_LOCK/PI_LOCK`，`PI_LOCK` 当前退化为 P_LOCK。

## 证据入口

Tier 0 是 `v0.94/rtl/**`、`v0.94/project/redpitaya.xpr`、当前实际执行的 Python 和 tests。Tier 1 是 `STATUS.md` 顶部快照、`CURRENT_REVIEW_MANIFEST.md`、`AI_REVIEW_README.md`。Tier 2 是当前版本日志、上位机日志和用户截图/日志/示波器/Vivado 报告。Tier 3 是普通 README、设计文档和注释。Tier 9 是 `v-weifang`、`version-weifang`、`version/v1`、`version/v2`、`old`、`before`。

## 信号路径

```text
IN1/PD + IN2/REF
 -> laser_lock_core
 -> mixer_core / lpf_core / output_protect
 -> laser_error
 -> DAC A / OUT1 (error observation)
```

```text
GUI -> SSH -> /dev/mem -> custom_register_bank
 -> ramp_generator / out2_lock_controller
 -> selected_out2 -> DAC B / OUT2
 -> laser dedicated PZT / Scan input
```

```text
CH1=IN1/PD, CH2=IN2/REF, CH3=OUT1/laser_error, CH4=OUT2/selected_out2
 -> custom_debug_capture -> capture registers
 -> SSH /dev/mem -> Python backend -> PySide6/pyqtgraph
```

```text
SCAN -> capture -> click CH1 feature -> resolve CH3 zero crossing
 -> Confirm Lock Point -> CAPTURE_LOCK_POINT
 -> ERROR_SETPOINT + LOCK_BIAS -> MODE=3, Kp=0
 -> manual APPLY P -> SAFE on failure
```

## 当前源码锚点

- `v0.94/rtl/red_pitaya_top.sv`：顶层选择和 DAC A/B 最终来源。
- `custom_register_bank.sv`：寄存器地址、默认值、`MAGIC`、`VERSION`、捕获控制。
- `ramp_generator.sv`：SCAN 波形、步进、幅度和饱和。
- `laser_lock_core.sv`、`mixer_core.sv`、`lpf_core.sv`、`output_protect.sv`：误差观察链。
- `error_setpoint_corrector.sv`、`custom_debug_capture.sv`、`out2_lock_controller`：锁点捕获、采集和 OUT2 候选控制。
- `software/redpitaya_lock_host/redpitaya_lock_host/main_window.py`：GUI、Live、Capture、锁点和显示。
- `custom_fpga_backend.py`、`connection_workers.py`、`scripts/custom_fpga_scan_control.py`：SSH、`/dev/mem`、寄存器协议和 SAFE。
- `tests/test_custom_fpga_backend.py`：协议、GUI、安全和显示回归证据。

寄存器身份和地址以当前 `custom_register_bank.sv` 与 Python 实现交叉核对为准，不使用历史值猜测。
