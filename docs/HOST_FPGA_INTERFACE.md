# Host–FPGA Interface Contract

- Status: ACTIVE
- Authority: Host/FPGA 接口与兼容性
- Last-Updated: 2026-09-09
- Current Interface: v1-candidate

本文件是寄存器、数据通道、控制语义和版本对应关系的唯一接口入口。当前接口尚未绑定正式 bit release，因此只能称为 v1-candidate，不能写成已发布、已上板验证的 v1。

## 当前候选基线

| 项目 | 当前审查快照 |
| --- | --- |
| FPGA project | v0.94/project/redpitaya.xpr |
| FPGA top | red_pitaya_top |
| FPGA commit | `7c7b6570d4197939cd8e0101b096928d2ff67486` + 本次未提交 RTL/Host/测试修改；NOT RELEASED |
| Host path | software/redpitaya_lock_host |
| Host version | 未识别独立 tag/release；NOT RELEASED |
| Interface | v1-candidate |
| Current bit | NONE |
| CSR base | 0x40600000 |
| MAGIC | 0x4D545330 |
| Documented VERSION | 0x00030200；发布前须由当前 RTL 和 Host 再确认 |
| Documented L1 capability | offset 0xE4，value 0x4C310001；发布前须再确认 |

未提交工作树不能由单一 commit 重现，上表不得作为 bit 兼容性证明。

## 当前数据接口语义

| 通道 | 语义 | 当前用途 |
| --- | --- | --- |
| IN1 | PD | 激光器探测信号输入 |
| IN2 | REF | 参考信号输入 |
| OUT1 | laser_error | 混频、LPF 和保护后的误差信号 |
| OUT2 | selected_out2 | SAFE/SCAN/HOLD/P_LOCK 控制输出，连接激光器专用 PZT/Scan 输入 |
| Capture CH1 | IN1/PD | 原始 PD 观测 |
| Capture CH2 | IN2/REF | 原始参考观测 |
| Capture CH3 | laser_error | 误差信号观测 |
| Capture CH4 | selected_out2 | PZT 控制输出观测 |

OUT2 与 D2-125 AUX 输出不得并联驱动同一执行器。

## 控制模式语义

| 值 | 模式 | 合同语义 |
| --- | --- | --- |
| 0 | SAFE | 安全输出，退出主动扫描或锁定 |
| 1 | SCAN | 输出受控扫描斜坡 |
| 2 | HOLD | 保持指定控制点 |
| 3 | P_LOCK | 仅比例项的当前 Gate 锁定模式 |
| 4 | PI_LOCK | 候选/未来模式；不属于当前 Gate，不能作为已验证能力 |

模式数值、进入条件、单位、位宽、符号、缩放、饱和和复位值都属于接口合同，不得只改 FPGA 或只改 Host。

### 采集状态与事件时序

`ARM VALIDATE` 首次读回通常为 `VALIDATING (2)`。验证事件写入 sticky event 后，FPGA 回到 `SCAN (1)`，保持 MODE=SCAN、ENABLE=1 和原有 Kp/偏置不变；这表示验证完成但尚未接入反馈。若事件在 Host 首次读回前已完成，Host 只有在读到 `event_type=VALIDATED (7)`、`valid=1`、sequence 不同于 ARM 前从 FPGA 读取的基线，且 generation/扫描方向/过零方向与本次目标完全一致时，才可把该次 VALIDATE 视为成功。同代际旧事件也必须拒绝。

`ARM ACTIVE` 后的状态 3/4/5 分别表示 ARMED、ACQUIRING、P_LOCKED。`Apply P` 的命令传输成功不等于锁定；Host 必须以 FPGA 状态读回为准，状态 4 保持 ACQUIRING，状态 5 才能显示 P_LOCKED，其它状态进入 SAFE/FAILED。

GUI 完成 capture 回调后记录 capture ID，确认选点后将完整不可变 `LockTarget` 绑定到持久 AcquisitionService。worker 必须与该目标逐字段一致，不能采用请求中的 capture ID 为自身背书。重扫、影响目标的参数变化、连接目标/基址变化和断连清除绑定；旧上下文的异步成功/失败回复不能恢复旧目标。此状态仅在当前 Host 进程内持久，不提供多客户端互斥；外部脚本/第二客户端并发改写 CSR 不在本轮已验证范围。

本次仍为未发布的 `v1-candidate` 修复，VERSION 数值保持 `0x00030200`。该 VERSION 不能区分修复前后 bit，后续候选必须绑定源码差异/哈希和 bit SHA256；不得以版本寄存器相同宣称旧 bit 已含本次修复。

## 寄存器变化规则

任何寄存器新增、删除、偏移变化、位域变化、复位值变化、读写属性变化或语义变化，必须在同一变更中完成：

1. 更新 FPGA register bank/相关 RTL。
2. 更新 Host register map、读写逻辑和兼容性检查。
3. 更新本文件中的接口说明和版本。
4. 增加或更新 RTL 与 Host 测试。
5. 更新 docs/CURRENT_STATUS.md 和 docs/CHANGELOG.md。
6. 若发布 bit，在 release manifest 中绑定 FPGA commit、Host version 和 Interface version。

已发布寄存器地址不得静默复用为不同语义。需要废弃时应保留兼容读取或明确提升接口主版本。

## 数据接口变化规则

以下任一变化都视为接口变化：

- IN/OUT 或 Capture 通道语义变化。
- 采样率、数据宽度、符号、定点小数位或缩放变化。
- 数据顺序、长度、触发条件、时间戳或溢出行为变化。
- SAFE/SCAN/HOLD/P_LOCK 状态机行为或状态码变化。
- 参数单位、允许范围、默认值、饱和或错误处理变化。

接口变化必须先写迁移说明，再同步修改 FPGA 与 Host，并用同一组已知输入证明双方解释一致。

## 版本对应关系

每个正式 release 必须包含以下一一对应关系：

| FPGA commit | Host version/commit | Interface | bit SHA256 | Release |
| --- | --- | --- | --- | --- |
| 当前无正式映射 | 当前无正式映射 | v1-candidate | NONE | NOT RELEASED |

版本策略：

- 不兼容的寄存器或数据语义变化：提升 Interface 主版本。
- 向后兼容的新寄存器/能力：保留主版本，更新 FPGA VERSION/能力位，并记录 Host 的最低兼容版本。
- 仅内部实现变化且接口完全不变：Interface 不变，但 release 仍须记录新 FPGA commit 和 bit hash。
- Host 启动时必须检查 MAGIC、VERSION 和必要 capability；不兼容时进入只读诊断或拒绝控制，不得盲写寄存器。

## 同步修改约束

禁止接口相关的 FPGA 和 Host 单边修改。纯内部 RTL 优化或纯 UI 显示变化只有在接口合同确实不变、CHANGELOG 明确记录 Interface impact: NONE 时，才可单侧提交；正式 release 仍须重新确认版本对应关系。

## 变更记录模板

- Change ID:
- Date:
- Gate:
- FPGA commit:
- Host version/commit:
- Interface before/after:
- Register changes:
- Data interface changes:
- Compatibility:
- Tests:
- Release:
