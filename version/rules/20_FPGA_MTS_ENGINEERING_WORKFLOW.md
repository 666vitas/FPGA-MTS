Status: ACTIVE
Effective-Gate: ALL
Authority: RULE
Last-Updated: 2026-07-24
Supersedes: NONE
Superseded-By: NONE

# FPGA-MTS 单开发者 Gate 工作流

本文件定义稳定的工程推进、构建、验证和硬件安全规则。动态目标、timing 数值和唯一下一动作只写入 `version/CURRENT_GATE.md` 与 `version/STATUS.md`。

## 1. 唯一产品路线

```text
timing-clean minimal build
-> SAFE / SCAN / aligned capture
-> user selects a valid target
-> exact HOLD / controlled approach
-> P_LOCK Kp=0
-> user-approved minimal nonzero Kp
-> basic P-only hardware lock
-> later board service / deterministic acquisition / PI / relock / AI
```

基础 P-only 未经用户真实硬件验证前，不扩展 PI/Ki、自动重锁、完整自动锁定、AI 参数优化、IQ 重构、双执行器或大规模 GUI 重做。

## 2. 单开发者职责

### 用户

- 唯一真实硬件实验操作者。
- 唯一有权确认硬件 Gate 是否通过的人。
- 负责 Vivado synthesis/implementation、bitstream 生成/烧录、接线、示波器、PZT、谱线位置和真实锁定结果。

### Codex

- 唯一主要开发者，负责分析、最小实现、测试、文档和同线程自检。
- 默认不启动 subagent，不创建多角色审查流程。
- 不能代替用户运行硬件、批准 Gate 或提升硬件证据等级。

## 3. 每轮只推进一个 Gate

开始前依次读取 `AGENTS.md`、`CURRENT_GATE`、`STATUS`、manifest 和 manifest 指定的 active 文件，并检查 branch/working tree。

每轮只回答并执行：

1. 当前 Gate 与 blocker。
2. 本轮是否直接服务 blocker。
3. 允许和禁止修改范围。
4. 最小实现或验证。
5. 与风险相称的测试。
6. Gate 仍需什么用户结果。

Gate 未通过时不得自动进入下一 Gate、扩展额外功能、用测试数量代替 timing/硬件结果，或因设计看起来合理而宣布完成。

## 4. 构建策略

### `LOCK_MVP_BUILD`

第一次真实 P-only 锁定使用的最小构建，必须保留：

- mixer / LPF；
- SAFE / SCAN / HOLD / P_LOCK；
- triangle scan；
- aligned debug capture；
- monitor / readback；
- correction / absolute limits；
- Kp=0 与最小 P-only 数据路径。

允许在编译期关闭 deterministic ARM acquisition 的综合实例或复杂运行路径，但不得删除 ARM 源码、CSR 定义或测试。

### `D1_ARM_BUILD`

保留完整 deterministic ARM acquisition，用于独立仿真、回归和后续 Gate。它不作为第一次 P-only 锁定的必要依赖，也不得反向阻塞 `LOCK_MVP_BUILD` timing closure。

两个 build 必须有明确且可测试的编译期选择；不能依靠运行时常量让被关闭逻辑仍进入 timing path。

## 5. Timing Gate

任何拟上板 build 必须由用户 Vivado 报告同时证明：

```text
WNS >= 0 ns
TNS = 0 ns
WHS >= 0 ns
THS = 0 ns
unconstrained paths = 0
```

行为仿真、综合成功、bitstream 生成或 hold timing 通过都不能替代 setup timing closure。失败时先按 startpoint、endpoint、clock、path group 和 high-fanout 分类，再做最小修改；不得看到 timing failure 就大规模重写 register bank 或官方底层。

## 6. Host / FPGA 边界

- GUI：参数、真实波形、用户命令、状态、readback 和失败原因。
- LockService：host 侧唯一状态机、合法命令、目标有效性、失败和 SAFE。
- RegisterMapper：CSR、版本、signed14、单位、写顺序、W1P 和 readback。
- AcquisitionService：aligned frame、capture/scan generation 和统计。
- Red Pitaya Linux：低速 transport 或后续板端 service。
- FPGA：实时 mixer/LPF、scan、capture、P-only、mode/output、limit 和 saturation。

Windows、SSH 和 Linux 轮询不得参与每个 servo sample。当前 Gate 若选择手动 HOLD/approach 路线，它只能是受限的低速 acquisition 操作，不能冒充 FPGA 实时 servo。

## 7. 证据与措辞

证据标签和定义以 `AGENTS.md` 为准。至少分开：

- 代码存在；
- 软件 unit test；
- RTL simulation；
- Vivado timing；
- 用户 GUI；
- 用户真实硬件；
- 短时闭环；
- 持续稳频。

不得把 CH4 `selected_out2` 当真实 OUT2/loaded PZT，把数字 count 正确当模拟电压正确，把 HOLD 当 P-only，把 Kp=0 当负反馈，或把短时锁定当长期稳频。

只有用户提供满足当前 Gate 验收条件的真实记录，才允许提升 timing 或 hardware 证据。Codex 不自动批准 Gate。

## 8. 验证要求

- Python 修改：`tabnanny`、修改文件 `py_compile`、相关 targeted tests，必要时完整 tests。
- RTL 修改：对应 testbench、编译/lint、build 选择和工程 source/file-set 检查。
- Timing 改动：Codex 做本地可用的 RTL 验证；最终 synthesis/implementation 与 timing 报告由用户执行。
- 文档修改：`git diff --check`、conflict-marker、旧路径/悬空链接、范围和 Markdown-only 检查。
- 不删除、skip、xfail 或弱化安全测试。
- 实现、验证或实验改变当前事实时更新 `STATUS`；改变唯一任务或验收条件时更新 `CURRENT_GATE`；改变强制读取集合时更新 manifest。

## 9. 硬件实验与永久安全

硬件轮次一次只给一个实验，写清目的、接线、scope load/coupling/probe、参数、MODE/Kp/Ki/polarity/safe range、步骤、PASS/FAIL、立即 SAFE 条件和返回数据。

永久规则：

1. OUT2 只能连接当前 Gate 授权的激光器专用 PZT/Scan 输入和测量设备。
2. 禁止连接激光器电流调制、D2-125 `Servo Output`、D2-125 `Aux Output` 或任何其他有源输出；禁止输出并联。
3. `MAGIC/VERSION`、通信、SAFE、接线、scope 条件、readback、范围、saturation、削顶、跳变、目标或反馈方向任一不明确，立即 SAFE 并停止。
4. Codex 不自动提高 Kp/Ki、切换 polarity、放宽 limit、扩大 safe range、再次 LOCK 或进入下一 Gate。
5. 真实 P-only 前，ARM、approach 或 GUI 状态都不能作为锁定通过证据。

## 10. Gate 路线

1. `LOCK-MVP-T0`：得到 timing-clean `LOCK_MVP_BUILD`。
2. `LOCK-MVP-S1`：统一最小 Host/FPGA contract，先迁移 CONNECT/SAFE/SCAN。
3. `LOCK-MVP-H1/H2`：真实 scan/capture、HOLD 与受限 approach。
4. `LOCK-MVP-H3`：Kp=0 无不可接受跳变。
5. `LOCK-MVP-H4`：Kp=4 起步的最小 P-only，error 改善、无 saturation、持续锁定。
6. H4 后才能新建板端 service、恢复完整 deterministic acquisition 主线或开展 PI/relock/AI。

历史 D1、L0、HV-*、v1-v5 和旧 review 只作证据追溯，不能覆盖 `CURRENT_GATE`。

## 11. 交接

结束时报告修改文件、原因、实际测试、未运行事项、未验证风险、未修改边界和用户唯一下一步。默认不 commit、不 push。
