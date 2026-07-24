Status: HISTORY
Effective-Gate: ALL
Authority: SUPPORTING
Last-Updated: 2026-07-24
Supersedes: NONE
Superseded-By: AGENTS.md

# 项目目录与工作流规则

> 有效的项目路径、角色、安全和读取优先级已合并到 `AGENTS.md`；本文件只作历史依据。

## 1. 项目目录边界

`E:\new\fpga_lock` 是总项目归档目录，可以包含背景资料、实验数据、旧版本副本和非当前开发材料。

`E:\new\fpga_lock\v94` 是当前本地项目根目录，对应 GitHub 项目 `666vitas/FPGA-MTS`。

当前项目只把以下目录作为主动开发目录：

- `E:\new\fpga_lock\v94\v0.94`
- `E:\new\fpga_lock\v94\version`
- `E:\new\fpga_lock\v94\software`

目录含义：

1. `E:\new\fpga_lock`：总项目归档。
2. `E:\new\fpga_lock\v94`：当前 GitHub / 项目根目录。
3. `v0.94`：FPGA RTL / Vivado / Red Pitaya 代码主线。
4. `version`：版本记录、规则、SOP、路线和实验记录主线。
5. `software`：上位机软件主线。

## 2. 不是当前主线的目录

以下目录不能当作当前开发根目录或当前代码主线：

- `E:\new\fpga_lock`
- `E:\new\fpga_lock\exp_data`
- `E:\new\fpga_lock\文献阅读`
- `E:\new\fpga_lock\vivado_exp`
- `E:\new\fpga_lock\python_sim`
- `E:\new\fpga_lock\open source`

只有在用户明确要求使用背景资料或历史对比时，才可以把这些目录作为参考。

## 3. weifang 目录禁止规则

当前主线不使用任何 weifang 相关目录。

默认严格禁止：

- 读取 `weifang`
- 读取 `v-weifang`
- 读取 `version-weifang`
- 同步 weifang 相关目录
- 从 weifang 相关目录复制内容
- 修改 weifang 相关目录
- 把 weifang 相关目录作为当前主线依据

如果搜索结果包含 `weifang`、`v-weifang` 或 `version-weifang`，除非用户明确说明任务是历史对比，否则忽略这些结果。

## 4. 角色分工

### GPT

GPT 负责：

1. 阅读 GitHub 项目和新生成的项目文件。
2. 理解当前实验进展。
3. 根据用户实验目标生成 Codex 指令。
4. 帮助判断下一步实验接线、正常现象和停止条件。
5. 不直接替代 Codex 做本地代码修改。

### Codex

Codex 负责：

1. 阅读本地 `E:\new\fpga_lock\v94` 项目中的文件。
2. 按用户范围修改 Markdown / RTL / Python。
3. 生成实验 SOP、代码、仿真和记录。
4. 严格报告修改了哪些文件。
5. 默认不运行 Vivado。
6. 默认不生成 bitstream。
7. 默认不烧录 Red Pitaya。

### Claude Code

Claude Code 负责：

1. 审查 Codex 生成的代码。
2. 审查 RTL timing 风险。
3. 审查 SOP 的实验安全风险。
4. 检查 OUT2 是否被错误连接到真实执行器。
5. 不作为唯一实验权威；最终验证仍需要用户手动 Vivado 和示波器检查。

### 用户

用户负责：

1. 手动打开 Vivado。
2. 手动运行 synthesis 和 implementation。
3. 手动生成 bitstream。
4. 手动烧录 Red Pitaya。
5. 手动接线。
6. 保存示波器截图、CSV 数据和 Vivado timing 报告。
7. 把实验现象反馈给 GPT / Codex。

## 5. 默认权限边界

默认情况下，Codex 不得：

- 运行 Vivado
- 运行 synthesis
- 运行 implementation
- 生成 bitstream
- 生成 bin
- 烧录 Red Pitaya
- 修改 `redpitaya.xpr`
- 修改 XDC / SDC
- 接触 `weifang`、`v-weifang` 或 `version-weifang`

只有用户明确请求并确认后，才可以扩大范围。

## 6. 文档语言

项目说明、开发日志、实验记录、SOP、AI 审查记录默认使用中文。文件路径、命令、寄存器名、模块名、信号名和英文缩写保留英文原文。
