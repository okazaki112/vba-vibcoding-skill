# VBA智能编程助手（VBA-vibcoding）

**一个让 Excel VBA 开发「开箱即用」的 Agent Skill**：用自然语言描述需求，自动生成符合现代规范的 VBA 代码，注入 Excel 工作簿并运行验证——默认交付**带测试数据的 .xlsm 成品**，而不是一段要自己粘贴的代码。

📖 **在线介绍页**：<https://okazaki112.github.io/vba-vibcoding-skill/>

```
需求分析 → 代码生成 → 新建/打开工作簿 → 注入 → 运行验证 → 交付
```

## ✨ 核心特性

- **成品交付**：未指定目标文件时自动新建 .xlsm 并写入测试数据（表头 + 20 行业务数据），代码注入、实跑验证后交付，打开即见效果
- **现代 VBA 规范**：禁用 Select/Activate、参数传递对象、数组批量处理、完整错误处理，10 项准则 + 19 项质量门禁
- **命令级证据**：注入/执行全程返回 JSON（`success=true` 才算通过），拒绝口头确认
- **模块全生命周期**：create / list / read / write / delete / run / export / import
- **内置质量闭环**：结构机检（check.cmd）+ 3 条验收用例 + 自行进化台账（evolution.md）

## 📦 安装

**前置要求**

| 项 | 要求 |
|----|------|
| 系统 | Windows + Microsoft Excel |
| Python | 3.x，并安装依赖：`pip install pywin32` |
| Excel 设置 | 文件 → 选项 → 信任中心 → 信任中心设置 → 宏设置 → 勾选**「信任对 VBA 工程对象模型的访问」** |
| 文件格式 | 目标工作簿必须为 `.xlsm`（`.xlsx` 无法保存 VBA） |

**安装步骤**：克隆本仓库（仓库根 = 技能集合目录），把其中的 `VBA智能编程助手` 文件夹复制到 Agent 技能目录：

```bash
git clone https://github.com/okazaki112/vba-vibcoding-skill.git
# Claude Code 示例：把其中的 VBA智能编程助手 → C:\Users\<用户名>\.claude\skills\
# Codex 示例：    把其中的 VBA智能编程助手 → C:\Users\<用户名>\.codex\skills\（以其实际技能目录约定为准）
```

重启 Agent 会话后，技能列表中显示为「**VBA智能编程助手**」。

**让 Agent 自行安装**：把下面这段提示词整段发给你的 Agent 即可：

```text
请帮我安装技能「VBA智能编程助手」：
1. 克隆 https://github.com/okazaki112/vba-vibcoding-skill.git 到临时目录，把其中的 VBA智能编程助手 文件夹复制到你的技能目录下（Claude Code 为 ~/.claude/skills/，Codex 为 ~/.codex/skills/，以你实际约定为准），确保 SKILL.md 位于 技能目录/VBA智能编程助手/SKILL.md
2. 安装完成后报告：安装路径、SKILL.md 是否就位，以及前置要求（pip install pywin32；Excel 信任中心勾选「信任对 VBA 工程对象模型的访问」）
```

## 🚀 使用

对 Agent 直接说需求即可，常用问法：

| 你说 | 发生什么 |
|------|---------|
| 「帮我写个宏，把某列数据去重统计」 | 未指定文件 → 自动新建带测试数据的 .xlsm，注入宏并实跑验证 |
| 「往我的 D:\data.xlsm 里加个汇总功能」 | 指定文件 → 先备份同名模块，注入后运行验证 |
| 「这个宏跑得太慢了，帮我优化」 | 定位性能瓶颈，改完注入实测前后对比 |
| 「只要代码，我自己粘贴」 | 仅生成 .bas 文件 + Alt+F11 手动粘贴步骤，不注入 |

也可以双击 `prompts/提示词库.html` 打开**离线提示词库**（搜索 / 一键复制 / 编号深链 / 深浅主题），里面预置了 6 条场景提示词。

## 🛠 vba_manager.py 命令参考

```bash
cd tools
python vba_manager.py create "D:\demo.xlsm" "测试数据" 20 6              # 新建带测试数据的工作簿
python vba_manager.py write  "D:\demo.xlsm" "DataProcessor" "code.bas"   # 注入代码
python vba_manager.py run    "D:\demo.xlsm" "DataProcessor.ProcessData"  # 运行宏
```

| 命令 | 用途 |
|------|------|
| create | 新建 .xlsm 并写入测试数据（默认 20 行 6 列，已存在拒绝覆盖） |
| list / read | 列出模块 / 读取模块代码 |
| write / delete | 写入覆盖模块（自动保存）/ 删除模块 |
| run | 运行宏（支持参数） |
| export / import | 导出模块备份 / 导入模块 |

所有命令返回 JSON，以 `success` 字段判定成败。完整 API 见 [docs/API.md](docs/API.md)。

## 🧪 质量验证

```bash
# 在 skills/VBA智能编程助手/ 目录下运行
check.cmd        # Windows：结构机检 + 验收用例机检
./check.sh       # Linux/macOS
```

机检覆盖：SKILL.md 结构与执行工作流、prompts/ 五文件提示词库、references/acceptance.md 验收用例。深度知识库（代码模板 / Excel 模式 / 性能优化 / 调试 / 最佳实践）见 [references/](references/)。

## 🔄 自行进化

实战使用中发现缺陷或新场景时，按 SKILL.md「自行进化」节走「发现 → 记账 → 提案 → 落版」闭环，台账在 [evolution.md](evolution.md)；机检会对未决条目持续提醒，已采纳条目强制带落点。

## 📁 目录结构

```
vba-vibcoding-skill/        # 仓库根 = 技能集合目录
└── VBA智能编程助手/         # 技能根（安装时复制这个文件夹）
    ├── README.md
    ├── SKILL.md              # 技能主文档（工作流 + 规范 + 命令参考）
    ├── check.cmd / check.sh  # 验证入口（结构机检 + 验收用例）
    ├── evolution.md          # 自行进化台账
    ├── docs/API.md           # vba_manager.py 详细 API
    ├── examples/             # Python 调用示例
    ├── prompts/              # 五文件 HTML 提示词库（双击 html 打开）
    ├── references/           # 深度知识库（6 篇，含验收用例）
    ├── scripts/              # 结构机检脚本
    └── tools/vba_manager.py  # Excel COM 自动化核心工具（pywin32）
```
