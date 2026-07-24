# FPGA-MTS 项目读取指南

本仓库是 Red Pitaya FPGA 激光频率锁定项目的当前本地开发工程。

当前本地项目根目录：

```text
E:\new\fpga_lock\v94
```

当前有效开发目录：

```text
v0.94/
software/
version/
```

默认禁止读取、引用、同步、复制或修改任何历史旁支目录，除非用户明确要求做历史对比。

## 当前主线

当前主线已经进入 v3REG-0：

```text
上位机
-> Red Pitaya Linux
-> FPGA custom_register_bank
-> ramp_generator
-> OUT2 scope-only triangle
```

第一版只支持：

```text
SAFE: OUT2 = 0
SCAN: OUT2 = 0.85 V offset + +/-0.05 V triangle, about 50 Hz
```

第一版只做示波器验证，不接 Scan/PZT，不接激光器，不接 D2-125 Servo Output，不接 D2-125 Aux Output，不和 D2-125 Aux Output 并联。

## 读取优先级

1. `version/`
   - 当前路线、阶段记录、安全边界、下一步实验 SOP。
2. `v0.94/`
   - 当前 FPGA RTL、testbench、Vivado project source list。
3. `software/redpitaya_lock_host/`
   - 上位机 GUI、SSH/SCPI 工具、Custom FPGA host-side 控制脚本。

## 文档语言规则

面向用户的解释、实验 SOP、阶段任务、代码审查说明默认使用中文。

允许保留英文的内容包括：文件路径、RTL 模块名、端口名、寄存器名、Vivado timing 术语、命令行命令、论文标题和引用。

代码相关名称保持原名，例如 `mixer_core`、`lpf_core`、`output_protect`、`pi_controller_seq`、`custom_register_bank`、`ramp_generator`、`OUT1`、`OUT2`、`error_o`、`control_o`、`WNS`、`TNS`、`Vivado`、`bitstream`。

## Agent 分工

GPT 负责读取项目和文档，理解当前实验进度，并根据用户实验目标生成 Codex 指令。

Codex 负责在本地项目中读取和修改文件，执行范围必须符合用户当次任务要求，并在完成后说明实际读取和修改了哪些文件。

Claude Code 负责审查 Codex 生成的代码、RTL 时序风险、SOP 实验安全风险，以及是否存在误接 OUT2 到真实执行器的风险。Claude Code 不能替代用户的 Vivado 和示波器验证。

用户负责手动打开 Vivado，手动运行 synthesis / implementation，手动生成 bitstream，手动烧录 Red Pitaya，手动接线，保存示波器截图/CSV/Vivado timing，并把实验现象反馈给 GPT / Codex。

## 默认安全边界

默认情况下，Codex 不运行 Vivado synthesis / implementation，不生成 bitstream/bin，不烧录 Red Pitaya，不连接 Red Pitaya 网络，不执行 git add / commit / push，不读取或修改任何历史旁支目录。

OUT2 在当前阶段只能接示波器。任何连接到 Scan/PZT、激光器、D2-125 Servo Output、D2-125 Aux Output 或真实执行器的动作，都必须由用户在明确的新阶段 SOP 中授权。
