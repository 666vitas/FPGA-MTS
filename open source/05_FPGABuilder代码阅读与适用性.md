# FPGABuilder 代码阅读与适用性

## 1. 项目身份

- `[CONFIRMED]` 定位：YAML 驱动、插件化的跨厂商 FPGA build/packaging
  工具，不是 lock application。
  证据：`FPGABuilder-main/FPGABuilder-main/README.md:1-14`。
- `[CONFIRMED]` 本地版本：`0.2.0`，classifier 为 Alpha。
  证据：`src/core/__init__.py:1-7`；`setup.py:60-68`。
- `[NOT VERIFIED]` commit：本地无 `.git`。
- `[CONFIRMED]` license：CC BY-NC-SA 4.0，含非商业限制。
  证据：根 `LICENSE:1-9`；`setup.py:140`。

目录：

```text
FPGABuilder-main/
├─ src/core/                  config/project/plugin/CLI
├─ src/plugins/vivado/        file scanner, Tcl templates, plugin
├─ src/plugins/quartus/
├─ src/plugins/hls/
├─ scripts/                   packaging/install verification
├─ docs/developer_guide/
└─ tests/
```

没有 Red Pitaya 专用 lock modules、register generator、host GUI generator
或 MTS acquisition/controller。

## 2. 实际能力

`VivadoPlugin`：

- 检测 Vivado 与 version adapter：
  `src/plugins/vivado/plugin.py:44-151`；
- 生成临时 Tcl 并 batch 调用 Vivado：
  `plugin.py:154-251`；
- file scanner + Tcl generator：
  `plugin.py:334-383`；
- project/BD wrapper/GUI/build hooks：
  `plugin.py:385-748`。

审计发现：

- 同一 class 中 `synthesize()`、`implement()`、`generate_bitstream()` 出现
  早期版本和后续重定义；后定义会覆盖前定义。
- 早期 `implement()` / `generate_bitstream()` 在 `plugin.py:293-331`
  直接返回 success placeholder；后面虽有真实 Tcl 路径，但重复定义本身
  显示代码仍在快速演进。
- hooks 在 Windows 使用 `shell=True`：
  `plugin.py:636-676`，引入额外命令执行与供应链边界。
- README 的“全流程、烧录、多厂商、git submodule”范围远大于当前
  FPGA-MTS 的单 Gate 最小 build。

## 3. 对当前项目的价值

### CSR / module composition

`[CONFIRMED]` 本地代码没有从 SystemVerilog schema 自动生成
FPGA-MTS CSR、Python mapper 或 tests 的工具。它主要扫描文件并生成
Vivado Tcl。因此不能解决当前 CSR drift 的核心问题。

### simulation / build automation

`[INFERENCE]` YAML + Tcl template 可以未来统一 build，但引入需要：

- 迁移现有 Red Pitaya v0.94 Tcl/project；
- 证明 source/file-set、defines、LOCK_ACQ_IMPL、XDC 与报告一致；
- 重建当前 timing evidence；
- 接受新的 Python dependencies、license 与 hook execution surface。

这会破坏“先完成真实 P-only”的最小路径。

### Red Pitaya support

`[CONFIRMED]` supported part list含 `xc7z020clg400-1`：
`plugin.py:85-92`，但没有 Red Pitaya board/project semantics。
支持 Zynq part 不等于支持当前 v0.94 project。

## 4. 适用性清单

| 功能 | 源文件 / symbol | 分类 | 结论 | 阶段 |
|---|---|---|---|---|
| YAML project manifest | `src/core/config.py`, README config | CONCEPTUALLY REUSABLE | 可借鉴“单一 build metadata”思想 | FUTURE ONLY |
| source scanner | `vivado/file_scanner.py` | CONCEPTUALLY REUSABLE | 当前 Vivado project/file-set 已有既定来源；迁移风险大 | FUTURE ONLY |
| Tcl templates | `vivado/tcl_templates.py` | REQUIRES ARCHITECTURE CHANGE | 会更换构建入口与证据链 | 当前不引入 |
| Vivado batch runner | `VivadoPlugin._run_vivado_tcl` | NOT APPLICABLE NOW | 当前规则禁止 Codex 自动跑 Vivado，用户已有工程 | 不引入 |
| hooks | `_execute_hook_commands` | DANGEROUS UNDER CURRENT GATE | 扩大 shell/network/git/packaging surface | 禁止 |
| CSR generator | 无 | NOT APPLICABLE | 没有该能力 | 无 |
| lock GUI/host generator | 无 | NOT APPLICABLE | 不是锁频工具 | 无 |

## 5. 四个重点问题

1. 不能直接降低当前 CSR 或 module connection 维护成本；最多未来统一
   build metadata。
2. 现在引入会改变稳定的 v0.94 build/source/XDC 证据链，风险高。
3. 对“先完成真实 P-only”没有直接价值。
4. 推荐明确为 **当前不引入**；H4 后若确有多 build/多板卡维护压力，再用
   一个独立 Gate 评估，且先去除 duplicate methods/placeholders。

## 6. 最终结论

FPGABuilder 是 alpha build framework，不是锁频方案。当前不安装、不运行、
不迁移 v0.94、不使用其 hooks/program 功能。其 license 非商业限制也使
直接纳入产品工具链需要额外法律评估。

