# 项目根目录与角色分工

> 历史角色说明：目录边界仍可参考，固定 GPT/Codex/Claude 分工不再作为当前工作流。当前职责和独立复核规则见 `20_FPGA_MTS_ENGINEERING_WORKFLOW.md`。

## 1. 当前项目根目录

唯一当前本地开发根目录是：

```text
E:\new\fpga_lock\v94
```

该目录对应 GitHub 项目：

```text
666vitas/FPGA-MTS
```

`E:\new\fpga_lock` 是总归档目录，不能作为当前代码开发根目录。

## 2. 当前主动开发目录

当前主动开发目录：

- `E:\new\fpga_lock\v94\v0.94`
- `E:\new\fpga_lock\v94\version`
- `E:\new\fpga_lock\v94\software`

目录职责：

- `v0.94/`：FPGA RTL / Vivado / Red Pitaya 代码主线。
- `version/`：版本记录、规则、SOP、路线和实验记录。
- `software/`：上位机软件主线。

## 3. 禁止作为当前主线的目录

以下目录不是当前开发根目录，也不是当前代码主线：

- `E:\new\fpga_lock`
- `E:\new\fpga_lock\exp_data`
- `E:\new\fpga_lock\文献阅读`
- `E:\new\fpga_lock\vivado_exp`
- `E:\new\fpga_lock\python_sim`
- `E:\new\fpga_lock\open source`

当前主线不使用任何 weifang 相关目录。默认情况下，Codex 不得读取、同步、复制、修改或引用以下目录作为当前主线：

- `weifang`
- `v-weifang`
- `version-weifang`

如果搜索结果包含这些名字，除非用户明确说明任务是历史对比，否则忽略。

## 4. GPT / Codex / Claude Code / 用户分工

### GPT

GPT 负责：

1. 阅读 GitHub 项目和新生成的项目文件。
2. 理解当前实验进展。
3. 根据用户实验目标生成 Codex 指令。
4. 帮助判断下一步实验接线、正常现象和停止条件。
5. 不直接替代 Codex 做本地代码修改。

### Codex

Codex 负责：

1. 阅读 `E:\new\fpga_lock\v94` 下的文件。
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
3. 审查 SOP 实验安全风险。
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

## 6. Codex 执行报告规则

执行任务前，如果范围已知，Codex 必须说明计划读取哪些文件/目录，以及计划修改哪些文件。

执行任务后，Codex 必须列出实际读取过的关键文件，以及实际创建或修改的文件。

如果任务涉及 Vivado，Codex 默认只能为用户生成手动操作 SOP。除非用户明确请求并确认扩大范围，否则 Codex 不得自动运行 Vivado、synthesis、implementation、bitstream generation、bin generation 或 Red Pitaya programming。
