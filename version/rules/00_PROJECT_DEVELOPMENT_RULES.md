 00_PROJECT_DEVELOPMENT_RULES

> 历史阶段规则：本文件保留旧 v1/v2 背景，不再是当前开发总入口。当前工程流程以 `20_FPGA_MTS_ENGINEERING_WORKFLOW.md`、当前代码和 `version/STATUS.md` 为准；不得执行本文件中的固定旧阶段或强制全量读取要求。

## 0. 本文件作用

本文件是 Red Pitaya / FPGA / MTS 激光稳频项目的长期开发总规则。当前状态参见 [[STATUS]]。

优先级顺序：
```
E:\new\fpga_lock\v94\version\STATUS.md          ← 唯一状态源
E:\new\fpga_lock\v94\version\rules              ← 开发规则
E:\new\fpga_lock\v94\version\v<当前版本>        ← 当前版本目录，由 STATUS.md 决定
```

`STATUS.md` 是唯一状态源，当前版本目录由 `STATUS.md` 决定。当前阶段为 v2 时，Codex 必须读取：

```text
E:\new\fpga_lock\v94\version\v2
```

v1 继续保留为历史证据和可回退路径，尤其是已验证的 OUT1 error-like signal 输出链路。旧目录 `E:\new\fpga_lock\v94\v0.94\redpitaya_laser_lock_project\docs` 继续保留为历史资料库和证据库，不再作为唯一主线入口。

`05_CODEX_SKILL_PROMPT_PREFIX_RULES.md` 已废弃，不作为有效规则入口；其内容已合并到 `02_CODEX_WORKFLOW_COMPLETE.md`。

## 1. 项目最终目标

用 Red Pitaya STEMlab 125-14 / FPGA 逐步替代 MTS 调制转移光谱实验中的模拟误差信号产生链路。不是一次性写完一个大模块，而是分阶段学习和验证。

真实模拟链路 → 数字对应关系见 [[V1_GOAL_AND_CHAIN]]。版本路线见 [[V1_GOAL_AND_CHAIN#4-v1-分阶段路线]]。

当前 v2 目标是：用 FPGA 内部 PI/PID 控制器逐步替代 D2-125 的基本 servo 功能。v2 必须建立在 v1 已验证的 FPGA mixer + LPF error-like signal 和 OUT1 可回退路径之上。

## 2. 每个版本必须遵守的流程

1. 先解释物理目标（替代哪个模拟器件）
2. 再解释 FPGA 数据流
3. 再审查代码（按 03_FPGA_CODE_REVIEW_RULES）
4. 再仿真
5. 再 Vivado
6. 再上板
7. 最后记录实验结果（按 04_EXPERIMENT_RECORD_RULES）

## 3. 禁止跨阶段

- v1d 不做 BPF/gain，不接真实 PD
- v1e 才接真实 PD + REF
- v1f 才做 pre-mixer BPF + gain
- v1i 才考虑 D2-125
- v2 才做 PID
- v5 才做 AI
- 未经示波器确认安全前，OUT1 不能接 D2-125
- 当前不能声称已经实现稳频或得到真正 MTS error
- v2 不做 AI，不直接完整 PID，不直接闭环，不破坏 v1 OUT1 error 输出路径
- v2 第一版只允许在明确授权后开发独立 PI controller 和 testbench

完整阶段边界以 [[STATUS]] 为准；历史 v1 路线可参考 [[V1_GOAL_AND_CHAIN]]。

## 4. Codex 每次任务必须读取的文件

```
E:\new\fpga_lock\v94\version\STATUS.md
E:\new\fpga_lock\v94\version\rules\00_PROJECT_DEVELOPMENT_RULES.md
E:\new\fpga_lock\v94\version\rules\01_TEACHING_ENGINEER_RULES.md
E:\new\fpga_lock\v94\version\rules\02_CODEX_WORKFLOW_COMPLETE.md
E:\new\fpga_lock\v94\version\rules\03_FPGA_CODE_REVIEW_RULES.md
E:\new\fpga_lock\v94\version\rules\04_EXPERIMENT_RECORD_RULES.md
E:\new\fpga_lock\v94\version\rules\RULE_CODEX_ENGINEER_TEACHER.md
E:\new\fpga_lock\v94\version\rules\06_V2_PID_DEVELOPMENT_RULES.md（如果存在）
```

同时必须读取 `STATUS.md` 指定的当前版本目录：

- 当前阶段为 v1：读取 `E:\new\fpga_lock\v94\version\v1`
- 当前阶段为 v2：读取 `E:\new\fpga_lock\v94\version\v2`
- 当前阶段为 v3/v4/v5：读取对应版本目录

## 5. 旧文档审查结论

| 类别 | 代表文档 | 后续定位 |
|---|---|---|
| 仍有价值的主线资料 | `docs/project_master/00...08` | 作为背景资料，重要结论迁移到 version |
| v1 直接依据 | v1 实验报告、代码审查、上板测试报告 | 作为 v1 证据来源 |
| 教学规则依据 | beginner_roadmap、learning/L01-L04 | 归纳到 version/rules |
| 历史记录 | docs/reports、docs/old | 保留，不再作为当前唯一操作入口 |
| 过时内容 | 写有旧状态的段落 | 被 STATUS.md 和当前实验结果覆盖 |
| 重复内容 | 多处重复的 Vivado/SOP/安全规则 | 合并为 version/rules 和 version/v1 |

## 6. FPGA 替代对象总览

| 真实链路 | FPGA 模块 | 状态 |
|---|---|---|
| 10 MHz LPF + 1.8 MHz HPF | `bpf_core.sv` / pre-mixer filter | v1f |
| ZFL-500LN+ (~24 dB) | `digital_gain.sv` | v1g |
| ZFM-3+ Mixer | `mixer_core.sv` | ✅ v1c 已通过 |
| mixer 后 LPF | `lpf_core.sv` | 以 STATUS.md 为准 |
| 相位调节 / I-Q | phase register / IQ demod | v1h |
| OUT1 安全输出 | `output_protect.sv` | ✅ 已就位 |
| D2-125 servo / PI/PID | `pi_controller.sv` / 后续 OUT2 控制路径 | v2 目标，当前以 STATUS.md 为准 |

详细模块-器件映射见 [[V1_GOAL_AND_CHAIN]]。
