# TEMPLATE_EXTRACTION_PLAN

## 1. 目标

从当前 `version` 文件夹中提取可复用模板，先服务 FPGA 激光稳频项目，再扩展到通用工科研究生项目。

提取原则：

```text
先保留真实项目味道，再抽象通用结构。
```

## 2. 第一步：提取 FPGA 模板

| 来源 | 提取成什么 | 保留什么 | 去掉什么 |
|---|---|---|---|
| `STATUS.md` | FPGA 项目状态模板 | 阶段、禁止项、下一步 | 本机绝对路径 |
| `V2_SYSTEM_ARCHITECTURE_AND_STAGE_MAP.md` | FPGA 阶段地图模板 | v1-v5、信号链、验证层级 | 具体未公开实验细节 |
| `V2_CODE_REVIEW_CHECKLIST.md` | RTL 审查模板 | signed/unsigned、位宽、reset、enable、saturation | 具体文件行号 |
| `V2_EXPERIMENT_SOP.md` | 上板实验 SOP 模板 | 接线、示波器、参数、结论 | 实验室敏感信息 |
| `V2A2_PI_ANTI_WINDUP_SIMULATION_REPORT.md` | XSim 仿真报告模板 | 测试总数、PASS/FAIL、日志路径 | 完整源码细节 |

### FPGA 模板清单

- [ ] `FPGA_PROJECT_STATE_TEMPLATE.md`
- [ ] `FPGA_STAGE_MAP_TEMPLATE.md`
- [ ] `FPGA_RTL_REVIEW_TEMPLATE.md`
- [ ] `FPGA_SIMULATION_REPORT_TEMPLATE.md`
- [ ] `FPGA_EXPERIMENT_SOP_TEMPLATE.md`
- [ ] `FPGA_VERIFICATION_MATRIX_TEMPLATE.md`

## 3. 第二步：提取通用工科项目模板

把 FPGA 特有词汇替换成更通用的工科结构。

| FPGA 项目词汇 | 通用工科词汇 |
|---|---|
| RTL | 实现文件 |
| XSim | 仿真/单元测试工具 |
| Vivado 综合/实现 | 构建/编译/部署验证 |
| 上板 | 上机/上设备/实物测试 |
| 示波器 | 测量仪器/传感器读数 |
| OUT1/OUT2 | 观察输出/控制输出 |
| 激光执行器 | 被控对象执行机构 |
| bitstream | 可部署固件/构建产物 |

### 通用模板清单

- [ ] `ENGINEERING_PROJECT_STATE_TEMPLATE.md`
- [ ] `ENGINEERING_VERIFICATION_MATRIX_TEMPLATE.md`
- [ ] `AI_REVIEW_PACKAGE_TEMPLATE.md`
- [ ] `AI_TASK_TEMPLATE.md`
- [ ] `EXPERIMENT_LOG_TEMPLATE.md`
- [ ] `WEEKLY_REPORT_TEMPLATE.md`

## 4. 第三步：扩展到三类项目

| 项目类型 | 可复用结构 | 需要新增字段 |
|---|---|---|
| 嵌入式项目 | 状态页、验证矩阵、构建报告、上机日志 | MCU/SoC 型号、固件版本、外设接口 |
| 控制项目 | 控制器阶段、仿真、实物闭环、性能对比 | 被控对象、采样率、执行器、稳定性指标 |
| 实验类项目 | SOP、实验日志、数据路径、周报 | 样品、仪器、环境条件、误差来源 |

## 5. 推荐执行顺序

1. 复制当前 Red Pitaya 示例，制作脱敏版。
2. 从脱敏版中标出变量字段，例如 `<PROJECT_NAME>`、`<CURRENT_STAGE>`、`<TEST_TOOL>`。
3. 把每个模板拆成“空白模板”和“示例模板”。
4. 用一个非 FPGA 的小项目测试通用性。
5. 再整理嵌入式、控制、实验三类专用扩展字段。

## 6. 质量检查清单

- [ ] 模板不是空泛项目管理，而是保留设计、实现、验证、实验、论文证据链。
- [ ] 每个模板都有示例字段。
- [ ] 每个模板都有禁止项或边界条件。
- [ ] 每个模板都能导出 Markdown。
- [ ] 模板不会诱导 AI 越权修改代码或跳过实验安全检查。
- [ ] 模板能解释“完成了哪一层证据，还没完成哪一层证据”。

