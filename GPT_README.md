# FPGA-MTS 项目读取指南

本仓库是 Red Pitaya FPGA 激光频率锁定项目的当前本地开发工程。

## 当前项目边界

当前本地项目根目录：

```text
E:\new\fpga_lock\v94
```

当前 GitHub 工程：

```text
666vitas/FPGA-MTS
```

当前 active baseline：

```text
v0.94 + version/v2 + software
```

当前有效开发目录：

- `v0.94/`
- `version/`
- `software/`

默认忽略以下目录，禁止把它们作为当前主线依据：

- `weifang`
- `v-weifang`
- `version-weifang`

## 文档语言规则

后续 Codex 生成或修改的项目文档默认必须使用中文。

允许保留英文的内容包括：

- 文件路径
- RTL 模块名
- 端口名
- 寄存器名
- Vivado timing 术语
- 命令行命令
- 论文题目和引用

面向用户的解释、实验 SOP、路线图、阶段任务、代码审查说明，必须优先使用中文。

中文文档不等于把所有英文都翻译掉。代码相关内容必须保留原名，例如 `mixer_core`、`lpf_core`、`output_protect`、`pi_controller_seq`、`OUT1`、`OUT2`、`error_o`、`control_o`、`WNS`、`TNS`、`Vivado`、`bitstream`。

## Agent 分工

GPT 负责读取 GitHub 项目和新生成的项目文件，理解当前实验进度，并根据用户实验目标生成 Codex 指令。

Codex 负责在本地 `E:\new\fpga_lock\v94` 项目中执行文件读取和修改，执行范围必须符合用户当次任务要求，并在完成后说明实际读取和修改了哪些文件。

Claude Code 负责审查 Codex 生成的代码、RTL 时序风险、SOP 实验安全风险，以及是否存在误接 OUT2 到真实执行器的风险。Claude Code 不能替代用户的 Vivado 和示波器验证。

用户负责手动打开 Vivado、手动运行 synthesis / implementation、手动生成 bitstream、手动烧录 Red Pitaya、手动接线、保存示波器截图/CSV/Vivado timing，并把实验现象反馈给 GPT / Codex。

## 默认安全边界

默认情况下，Codex 不运行 Vivado，不运行 synthesis，不运行 implementation，不生成 bitstream/bin，不烧录 Red Pitaya，不修改 `redpitaya.xpr`，不修改 XDC/SDC，不读取或修改任何 weifang 相关目录。
