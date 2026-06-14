# 版本阶段计划

## 0. 本文件作用

本文件说明后续版本怎么一步一步推进。

大白话：不要一次做完整 MTS。每个版本只验证一个新能力。

## 1. 我需要理解什么

当前第一阶段使用外部 `REF`：

```text
REF 不由 FPGA 生成
REF 从外部信号发生器进 IN2
EOM 仍由外部信号发生器驱动
```

## 2. 版本计划

| 版本 | 功能 | 目标 |
|---|---|---|
| `v1a_pd_passthrough` | `error_o = pd_i` | 验证 `IN1 -> OUT1` |
| `v1b_ref_passthrough` | `error_o = ref_i` | 验证 `IN2 -> OUT1` |
| `v1ab_passthrough_debug` | 参数选择 `pd_i/ref_i` | 一份代码支持 v1a/v1b |
| `v1c_mixer_only` | `pd_i * ref_i -> error_o` | 验证数字 mixer |
| `v1d_mixer_lpf` | mixer + LPF | 得到基础数字解调输出 |
| `v1e_real_pd_ref` | 真实 PD + REF | 第一次看真实 error-like signal |
| `v1f_bpf_enable` | BPF + mixer + LPF | 替代模拟高通/低通前处理 |
| `v1g_error_to_D2_125` | OUT1 接 D2-125 error input | 用 FPGA error 替代模拟 mixer 输出 |

## 3. 每个版本我需要操作什么

每个版本固定流程：

1. 让 Codex 生成 RTL。
2. 让 Codex 生成 testbench。
3. 跑仿真。
4. 生成 REPORT。
5. 生成 BOARD_TEST。
6. 需要接 top 时，先生成 integration plan。
7. GPT 审查。
8. 用户批准。
9. 再进入 Vivado。

## 4. 我需要发给 GPT 什么

每个版本发：

```text
版本名
目标功能
RTL
testbench
仿真输出
REPORT
BOARD_TEST
integration plan
```

## 5. Codex 应该生成什么

| 阶段 | Codex 产物 |
|---|---|
| RTL 阶段 | `.sv` + testbench |
| 仿真阶段 | 仿真结果写入 REPORT |
| 上板前 | BOARD_TEST |
| 集成前 | INTEGRATION_PLAN |
| 出错时 | CORRECTION |

## 6. 成功标准是什么

每个版本成功标准：

- testbench 通过；
- REPORT 完整；
- 官方工程未被误改；
- 上板 SOP 明确；
- 风险说明明确；
- 上一个版本通过后才进入下一个版本。

## 7. 失败怎么排查

| 阶段 | 回退到哪里 |
|---|---|
| `v1b` 失败 | 回退 `v1a` |
| `v1c` 失败 | 回退 `v1a/v1b` |
| `v1d` 失败 | 回退 `v1c` |
| `v1e` 失败 | 回退信号发生器模拟输入 |
| `v1f` 失败 | bypass BPF |
| `v1g` 失败 | 断开 D2-125，回到示波器 |

## 8. 第一阶段不做什么

第一阶段不做：

- FPGA PID；
- sweep；
- AI；
- lock/relock FSM；
- FPGA 生成 `REF`；
- FPGA 驱动 EOM；
- 激光器反馈闭环。

## 9. 我现在只需要记住什么

版本推进原则：

```text
每次只增加一个新功能。
```
