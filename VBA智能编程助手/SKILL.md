---
name: VBA智能编程助手
description: Excel VBA 一站式开发：自然语言需求 → 现代 OOP 规范 VBA 代码 → 注入 Excel 运行验证。默认交付带测试数据的 .xlsm 工作簿（未指定目标文件时自动新建），支持模块增删改查、宏执行、性能优化与调试。
---

# VBA智能编程助手（VBA-vibcoding）

## 这个 Skill 做什么

- **代码生成**：按现代 OOP 风格 VBA 规范生成高质量代码（禁 Select/Activate、数组批量处理、完整错误处理）
- **注入执行**：通过 `tools/vba_manager.py` 把代码注入 .xlsm 工作簿并运行宏，返回 JSON 结果
- **默认交付带测试数据的 .xlsm**：用户未指定目标文件时，自动新建工作簿并写入测试数据，交付打开即用的成品
- **模块管理**：create / list / read / write / delete / run / export / import 全套增删改查
- **优化与调试**：性能优化规则、Debug.Print/Assert 调试方法、19 项代码质量检查

## 为什么需要这个 Skill

**没有这个 Skill：** 生成的 VBA 只停留在代码文本，用户还要手动开 VBE、粘贴、建文件、造测试数据，质量靠运气。
**使用这个 Skill：** 需求直达可运行的 .xlsm 成品——代码、工作簿、测试数据、执行验证一步到位，且有命令级证据。

## 核心原则

1. **成品优于代码文本** — 默认交付注入并验证过的 .xlsm，不是一段代码
2. **对象优于界面** — 全程禁用 Select/Activate/ActiveSheet 写新代码，参数传递对象
3. **可验证优于可描述** — 每个关键步骤用命令输出（JSON success）做证据，禁止口头确认
4. **门禁优于跳步** — 上一步门禁未过不进入下一步；失败按「位置+原因+修复」处理
5. **测试数据优于空表** — 新建工作簿必带表头与多行测试数据，宏一跑就能看到效果

## 交付物硬性默认

| 分支 | 触发条件 | 行为 |
|------|---------|------|
| **默认：新建带测试数据 xlsm** | 用户未指定目标文件 | `create` 新建 .xlsm 并写入表头+多行测试数据 → 注入代码 → 运行验证 |
| 指定文件 | 用户给出已有 .xlsm 路径 | 校验存在且为 .xlsm → 注入前 `export` 备份同名模块 → 注入 → 验证；不新建文件 |
| 仅代码 | 用户明确说「只要代码」 | 输出 .bas 文件 + Alt+F11 手动粘贴步骤；不执行注入 |

**禁止**：默认分支下只回复代码文本就结束；对 .xlsx 注入（无法保存 VBA）；覆盖用户既有模块而不先备份。

## 执行工作流

> 四步闭环。任一门禁未过不得进入下一步；失败按「位置+原因+修复」报告，同一错误禁止原样重试第 3 次，换方法或求助。

1. **需求分析** — 输入：用户需求与目标文件状态。动作：判定交付分支（见「交付物硬性默认」表）；确认功能边界、数据结构与技术方案（数组/ListObject/Dictionary）；需求含糊先一句追问。产出：分支判定 + 需求一句复述。门禁：目标文件路径明确或已声明新建；不猜测生成。
2. **代码生成** — 输入：确认后的需求与方案。动作：按「现代 VBA 代码规范」编写代码，Write 保存 .bas 文件后 Read 读回验证。产出：.bas 代码文件。门禁：质量检查清单逐项通过，有 Read 证据。
3. **工作簿准备与注入** — 输入：.bas 文件与目标工作簿。动作：默认分支执行 `create` 新建带测试数据 .xlsm；指定文件分支校验文件存在且为 .xlsm 并备份；然后 `write` 注入、`list` 确认模块。产出：含目标模块的 .xlsm。门禁：`write` 与 `list` 两次命令 JSON `success=true`。
4. **运行验证与交付** — 输入：注入后的工作簿。动作：`run` 宏并核对执行输出，失败则修复重跑（最多换 3 种方法）；汇总交付物生成报告。产出：运行结果 + 交付报告（文件路径、模块名、执行摘要）。门禁：执行输出符合需求预期，报告含命令证据。

## 质量检查清单（代码生成门禁，19 项全过）

| 类别 | 检查项 |
|------|--------|
| 基础规范 | ① Option Explicit ② 匈牙利缩写命名(ws/wb/rng/tbl/dict) ③ 无 Select/Activate ④ 参数传对象而非 ActiveSheet ⑤ 错误处理完整(On Error GoTo+CleanUp+ErrorHandler) ⑥ 性能三开关(ScreenUpdating/Calculation/EnableEvents) |
| 结构 | ⑦ 4 空格缩进一致 ⑧ 过程/函数有注释 ⑨ For Each 优先于 For i ⑩ With 减少对象引用 |
| 性能 | ⑪ 大数据量数组批量处理 ⑫ 循环外计算不变量 ⑬ Find 替代整列扫描 |
| 安全 | ⑭ 危险操作前有确认提示 ⑮ 操作前有备份机制 ⑯ 敏感操作有错误恢复 |
| 可维护 | ⑰ 模块化单一职责 ⑱ 关键逻辑 Debug.Print 跟踪 ⑲ 边界条件处理(空数据/单行列) |

判定：17-19 优秀 / 14-16 良好 / 11-13 合格 / <11 不合格必须修复。注入验证以命令 JSON 为准：`write` success → `list` 可见 → `read` 内容与源文件一致。

## VBA 管理器命令参考

运行目录：`{skill目录}/tools`；所有命令返回 JSON，以 `success` 字段判定成败。

| 命令 | 用法 | 说明 |
|------|------|------|
| **create** | `create "<文件路径>" [工作表名] [行数] [列数]` | 新建 .xlsm 并写入测试数据（表头+随机业务数据行，默认 20 行 6 列；文件已存在则拒绝覆盖） |
| list | `list "<文件路径>"` | 列出所有 VBA 模块 |
| read | `read "<文件路径>" "<模块名>"` | 读取模块代码 |
| write | `write "<文件路径>" "<模块名>" "<代码文件>"` | 写入/覆盖模块（自动保存） |
| delete | `delete "<文件路径>" "<模块名>"` | 删除模块 |
| run | `run "<文件路径>" "<宏名>" [参数...]` | 运行宏，如 `Module1.ProcessData "10" "20"` |
| export | `export "<文件路径>" "<模块名>" "<输出文件>"` | 导出模块备份 |
| import | `import "<文件路径>" "<模块文件>" [新名称]` | 导入模块 |

```bash
# 默认交付分支：新建带测试数据的工作簿（工作表"测试数据"，20 行 6 列）
python vba_manager.py create "D:\\demo.xlsm" "测试数据" 20 6
# 注入并运行
python vba_manager.py write "D:\\demo.xlsm" "DataProcessor" "D:\\temp\\data_processor.bas"
python vba_manager.py run "D:\\demo.xlsm" "DataProcessor.ProcessData"
```

前置要求：① Excel 启用「信任对 VBA 工程对象模型的访问」（文件 → 选项 → 信任中心）；② 文件必须 .xlsm（.xlsx 无法保存 VBA）；③ `pip install pywin32`。

## 现代 VBA 代码规范（10 项准则）

| # | 准则 | 旧式做法 | 现代做法 |
|---|------|---------|------------|
| 1 | 禁止 Select/Activate | `Range("A1").Select: Selection.Copy` | `Range("A1").Copy Destination:=...` |
| 2 | 参数传递对象 | `Set ws = ActiveSheet` | `Sub Process(ws As Worksheet)` |
| 3 | For Each 优先 | `For i = 1 To 100: Cells(i,1)...` | `For Each cell In rng...` |
| 4 | With 链式调用 | 重复 `ws.Range(...).Font...` | `With ws.Range("A1"): .Font...` |
| 5 | ListObject 表格 | `Range("A2:D100")` | `tbl.ListObjects("表1").DataBodyRange` |
| 6 | Dictionary 键值对 | 数组+下标查找 | `dict.Exists(key)` 秒查 |
| 7 | Offset/Resize | `"A" & row & ":D" & lastRow` | `rng.Offset(1).Resize(n)` |
| 8 | 类型缩写命名 | `Dim sheet1, x, temp` | `Dim wsData, rowIdx, arrCache` |
| 9 | 纯函数设计 | 修改全局状态 | 返回结果，参数明确 |
| 10 | xlam 环境捕获 | 直接用 ActiveSheet | `Set wsUser = ActiveSheet` 后全用对象 |

**标准模板**（生成代码的骨架基线）：

```vba
Option Explicit

' 参数传递工作表对象，绝不依赖ActiveSheet
Sub 标准宏(ws As Worksheet)
    Dim wsData As Worksheet
    Dim startTime As Double
    Set wsData = IIf(ws Is Nothing, ActiveSheet, ws)  ' xlam安全：明确捕获环境
    startTime = Timer
    On Error GoTo ErrorHandler
    With Application                                  ' 性能优化三开关
        .ScreenUpdating = False
        .Calculation = xlCalculationManual
        .EnableEvents = False
    End With

    ' ===== 主代码区域（全部使用 wsData，绝不碰 ActiveSheet）=====

CleanUp:
    With Application
        .ScreenUpdating = True
        .Calculation = xlCalculationAutomatic
        .EnableEvents = True
    End With
    Debug.Print "执行完成，用时: " & Format(Timer - startTime, "0.00") & "秒"
    Exit Sub

ErrorHandler:
    MsgBox "错误 " & Err.Number & ": " & Err.Description, vbCritical
    Resume CleanUp
End Sub
```

## 参考资料索引

| 文件 | 内容 |
|------|------|
| references/code_templates.md | 完整代码模板（标准结构、数组、文件对话框、进度显示） |
| references/excel_patterns.md | Excel 自动化模式（单元格、格式、图表、透视表、事件） |
| references/optimization_rules.md | 性能优化规则（数组、循环、对象、内存） |
| references/best_practices.md | 最佳实践（命名、错误处理、安全、常见陷阱） |
| references/debugging_best_practices.md | 调试方法（Debug.Print/Assert/MsgBox 决策与条件编译） |
| references/acceptance.md | 验收用例（可判定场景） |
| docs/API.md | vba_manager.py 命令与调用详情 |

## 提示词库索引

`prompts/` 为五文件 HTML 提示词库，双击 `prompts/提示词库.html` 打开（搜索 / 一键复制 / #编号深链 / 深浅主题）。

### 场景索引
- [完整默认流程：零到一建表宏](prompts/提示词库.html#SCN-01) - 未指定文件，新建带测试数据 .xlsm 并注入验证
- [已有工作簿增强](prompts/提示词库.html#SCN-02) - 用户指定 .xlsm，注入前备份、注入后验证
- [性能与调试](prompts/提示词库.html#SCN-03) - 模块运行慢或报错的诊断修复
- [模块管理备份](prompts/提示词库.html#SCN-04) - list/read/export 清单备份与审查

### 系统/通用
- [系统任务入口](prompts/提示词库.html#SYS-01) - 完整流程处理 VBA 开发需求
- [仅生成代码文本](prompts/提示词库.html#GEN-01) - 手动粘贴分支，不执行注入

## 脚本说明

**领域脚本** `tools/vba_manager.py`（跟随目标技术栈）：
- 技术栈取证：脚本既有依赖 pywin32（`import win32com.client`），产物为 Windows Excel COM 自动化，命中项目既有工具链
- 运行命令：`python tools/vba_manager.py <命令> [参数]`（命令表见上节）
- exit 0 判据：输出 JSON 且 `success=true`；冒烟链路 create → write → list → run 全绿
- Python 调用方式与常见错误码详见 docs/API.md

**元层验证器**（与领域栈无关的标准化结构校验器）：
- `scripts/validate.py` — 结构完整性（YAML、执行工作流、五文件提示词库、data.js 字段）
- `scripts/validate_acceptance.py` — references/acceptance.md 用例校验
- 运行入口：根目录 `check.cmd`（Windows）/ `./check.sh`；降级直跑 `python -X utf8 scripts/validate.py .`

## 最佳实践

### DO
- 每次先判定交付分支；未指定文件就 `create` 新建带测试数据的 .xlsm
- 每个关键步骤留命令证据（JSON success / list 输出 / run 结果）
- 注入用户已有文件前先 `export` 备份同名模块
- 用测试数据让宏有数据可跑，验证结果更真实

### DON'T
- 不要对 .xlsx 注入代码（无法保存 VBA）
- 不要在默认分支只给代码文本就结束
- 不要用 Select/Activate/ActiveSheet 写新代码
- 不要跳过质量检查清单直接注入
- 不要覆盖用户既有模块而不备份

## 自行进化

实战使用中发现本 skill 自身的缺陷、更优解或场景缺口时，走「发现 → 记账 → 提案 → 落版」四步闭环，台账为根目录 `evolution.md`：

| 类别 | 触发 | 节奏 |
|------|------|------|
| E1 缺陷 | 按本 skill 执行得到错误结果、命令失效、指令矛盾 | 阻塞缺陷当场问用户；其余记账绕行，收尾批量提案 |
| E2 更优解 | 实战中找到比现行做法更优的方案 | 记台账，收尾提案 |
| E3 场景缺口 | 遇到未覆盖的真实场景（含提示词库无对应条目） | 记台账，收尾提案 |
| E4 环境漂移 | Excel 版本/系统/依赖变化使既有假设失效 | 记台账，收尾提案 |
| E5 用户反馈 | 用户指出本 skill 行为不当 | 记台账，收尾提案 |

- **记账**：evolution.md 新增 `## EV-<序号> <日期> <类别> <状态>`，先查台账去重；条目必带 触发/证据/提案 字段
- **提案**：收尾时问用户「实战发现 `<现象>`（证据 `<位置>`），建议修订 `<文件+概要>`。是否修复？」
- **落版**：批准后修订 → 跑 `check.cmd` 验证 → 台账记落点 → git 提交
- **红线**：只修订本 skill 自身文件，永不借机改动用户项目；已采纳条目必须带落点

## 总结

本 Skill 把「写 VBA」升级为「交付可运行成品」：需求分析定分支 → 规范生成代码 → create/write 注入 → run 验证交付。默认产物是带测试数据的 .xlsm 工作簿，全程命令级证据、门禁推进、失败三段式反馈。深度知识（模板/模式/优化/调试）按需查阅 references/ 目录。
