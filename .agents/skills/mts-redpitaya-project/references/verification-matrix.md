# 验证矩阵

## 证据等级

只能使用与实际证据相符的等级：`CODE CONFIRMED`、`TEST CONFIRMED`、`VIVADO SYNTHESIS CONFIRMED`、`IMPLEMENTATION CONFIRMED`、`TIMING CONFIRMED`、`BITSTREAM GENERATED`、`BOARD IDENTITY CONFIRMED`、`WAVEFORM CONFIRMED`、`CLOSED-LOOP EXPERIMENT CONFIRMED`、`LONG-TERM STABILITY CONFIRMED`、`WAITING FOR VERIFICATION`。一个等级不能推断另一个等级。

## 修改文档或 Skill

运行 `git diff --check`、检查路径和版本描述、确认没有把等待验证写成通过；不运行 Vivado。

## 修改 Python

在 `software/redpitaya_lock_host` 目录运行：

```powershell
..\.venv\Scripts\python.exe -m py_compile <修改的 Python 文件>
..\.venv\Scripts\python.exe -m pytest tests
```

失败时报告具体错误，不得声称通过。涉及 GUI 显示还要覆盖空数据、非零数据、隐藏通道、自动/固定量程、CH4 偏置、marker、Capture Once、Start/Stop Live、timeout、close event 和不写 FPGA。

## 修改寄存器协议

必须交叉核对 RTL 地址、Python 地址、`MAGIC`、`VERSION`、signed 扩展、默认值、readback、tests、STATUS 和 DEVELOPMENT_LOG。没有对应 bitstream/板端读回时只能写代码或测试证据。

## 修改 RTL

优先运行仓库已有 testbench/仿真流程，并检查语法、端口、source set、位宽、signed、饱和、reset、MODE、SAFE、latency 和 testbench。没有 Vivado 输出时标记 `WAITING FOR VERIFICATION`。

## 实验或 Vivado

Agent 只准备用户可复制步骤和检查报告。用户必须分别提供 synthesis、implementation、timing、bitstream、烧录、MAGIC/VERSION、波形和闭环实验证据；缺一不可跨级声称。
