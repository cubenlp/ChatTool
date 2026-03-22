# Skills 多平台兼容指南

本文档梳理主流 AI 编程助手对 skill/instruction 文件的格式要求，帮助 ChatTool `skills/` 目录下的技能适配各平台。

## 平台对比

| 平台 | 文件名 | 路径 | 格式 | frontmatter |
|------|--------|------|------|-------------|
| Claude Code | `SKILL.md` | `~/.claude/skills/<name>/` 或 `<repo>/.claude/skills/<name>/` | Markdown + YAML frontmatter | 支持，有结构化字段 |
| OpenAI Codex（项目指令） | `AGENTS.md` | 仓库根目录 | 纯 Markdown | 无要求 |
| OpenAI Codex（Skills） | `SKILL.md` | `.agents/skills/<name>/`、`$HOME/.agents/skills/<name>/`、`/etc/codex/skills/<name>/` | Markdown + YAML frontmatter | 必需，至少包含 `name` 和 `description` |
| Cursor | `*.mdc` | `<repo>/.cursor/rules/` | Markdown + YAML frontmatter | 支持 `description`、`globs` |
| GitHub Copilot | `copilot-instructions.md` | `<repo>/.github/` | 纯 Markdown | 无要求 |
| Windsurf | `.windsurfrules` | 仓库根目录 | 纯 Markdown | 无要求 |
| Gemini CLI | `GEMINI.md` | 仓库根目录（向上递归查找） | 纯 Markdown | 无要求 |

---

## 各平台详细说明

### Claude Code

**路径**
- 用户级：`~/.claude/skills/<skill-name>/SKILL.md`
- 项目级：`<repo>/.claude/skills/<skill-name>/SKILL.md`

**frontmatter 字段**

| 字段 | 是否必填 | 说明 |
|------|----------|------|
| `name` | 推荐 | 技能名称，省略时使用目录名 |
| `description` | 推荐 | 触发描述，Claude 用于判断何时调用此技能 |
| `argument-hint` | 可选 | 调用时的参数提示 |
| `allowed-tools` | 可选 | 限制技能可使用的工具列表 |
| `model` | 可选 | 指定使用的模型 |
| `effort` | 可选 | 推理强度 |
| `user-invocable` | 可选 | 是否允许用户通过 `/skill-name` 直接调用 |
| `disable-model-invocation` | 可选 | 禁用模型调用，仅执行 hooks |

**示例**

```markdown
---
name: arxiv-explore
description: Search and explore arXiv papers via ChatTool CLI.
allowed-tools:
  - Bash
---

## Quick Start

\`\`\`bash
chattool explore arxiv daily -p ai4math
\`\`\`
```

**说明**
- 同一目录下可放 `SKILL.zh.md` 作为中文版本
- 可放 `agents/` 子目录定义子 agent
- 可放 `scripts/`、`references/` 等辅助文件

---

### OpenAI Codex

OpenAI Codex 里需要区分两类文件：

- 项目指令：`AGENTS.md`
- 可复用 Skills：`SKILL.md`

#### 项目指令（`AGENTS.md`）

**路径**：`AGENTS.md`（仓库根目录）

**格式**：纯 Markdown，无 frontmatter 要求。

**示例**

```markdown
# AGENTS.md

## 编码规范
- 保持改动最小化
- 行为变更必须附带测试

## 禁止操作
- 不得修改 .env 文件
- 不得强制推送主分支
```

**说明**
- Codex 会递归查找父目录中的 `AGENTS.md`，子目录的规则优先级更高
- 支持在子目录放置 `AGENTS.md` 覆盖局部规则

#### Skills（`SKILL.md`）

**路径**
- 项目级：`.agents/skills/<skill-name>/SKILL.md`
- 用户级：`$HOME/.agents/skills/<skill-name>/SKILL.md`
- 系统级：`/etc/codex/skills/<skill-name>/SKILL.md`

**格式**：Markdown + YAML frontmatter。

**最小 frontmatter**

```markdown
---
name: my-skill
description: What this skill does and when to use it.
---
```

**可选文件**
- `agents/openai.yaml`：可选元数据，不是必需文件

**说明**
- `SKILL.md` 是 Skills 的必需入口文件
- `name` 与 `description` 应始终提供，便于 Codex 正确识别和触发
- `openai.yaml`/`openai.yml` 缺失不应视为安装失败原因

---

### Cursor

**路径**
- 现代格式：`<repo>/.cursor/rules/*.mdc`
- 旧格式（兼容）：`<repo>/.cursorrules`

**frontmatter 字段**

| 字段 | 说明 |
|------|------|
| `description` | 规则描述 |
| `globs` | 文件匹配模式，限定规则生效范围 |

**示例**（`.cursor/rules/python.mdc`）

```markdown
---
description: Python 编码规范
globs:
  - "**/*.py"
---

- 公共函数必须加类型注解
- 优先使用小函数，保持可测试性
```

**说明**
- `.mdc` 是当前推荐格式，`.cursorrules` 为旧版兼容路径
- `globs` 为空时规则全局生效

---

### GitHub Copilot

**路径**：`<repo>/.github/copilot-instructions.md`

**格式**：纯 Markdown，无 frontmatter 要求。

**示例**

```markdown
# Copilot Instructions

- 优先复用已有工具，避免引入新依赖
- 行为变更必须附带单元测试
- PR 保持聚焦，改动范围最小化
```

**说明**
- 仅对当前仓库生效
- 2025 年起支持 code review 和 coding agent 场景

---

### Windsurf

**路径**：`<repo>/.windsurfrules`

**格式**：纯 Markdown 或纯文本，无 frontmatter 要求。

**示例**

```markdown
# Windsurf Rules

- 改动范围最小化
- 行为变更时同步更新测试
```

---

### Gemini CLI

**路径**：`GEMINI.md`（当前目录，向上递归查找）

**格式**：纯 Markdown，无 frontmatter 要求。

**示例**

```markdown
# GEMINI.md

## 项目背景
这是一个 Python CLI 工具集。

## 指令
- 修改模块后运行对应测试
- 保持向后兼容，除非明确要求破坏性变更
```

**说明**
- Gemini CLI 会从当前目录向上查找 `GEMINI.md`，直到信任边界
- 子目录的 `GEMINI.md` 优先级高于父目录

---

## ChatTool skills/ 目录规范

ChatTool 的 `skills/` 目录以 `SKILL.md` 为主文件，同时兼顾 Claude Code 与 OpenAI Codex Skills：

```
skills/
└── <skill-name>/
    ├── SKILL.md          # Claude Code / OpenAI Codex Skills 主文件
    ├── SKILL.zh.md       # 中文版（可选）
    ├── agents/           # 子 agent 定义（可选）
    ├── scripts/          # 辅助脚本（可选）
    └── references/       # 参考文档（可选）
```

**SKILL.md 最小结构**

```markdown
---
name: <skill-name>
description: "<一句话描述，用于触发判断>"
---

## Quick Start

\`\`\`bash
chattool ...
\`\`\`
```

**跨平台适配建议**

- `SKILL.md` 的正文内容（去掉 frontmatter）可直接复用为其他平台的 instruction 文件
- `description` 字段内容可作为其他平台 Markdown 文件的首段说明
- 如果目标平台是 OpenAI Codex Skills，必须保留有效的 YAML frontmatter；不能仅保留正文
- 如需为某平台单独维护，在 skill 目录下新增对应文件（如 `AGENTS.md`、`.cursorrules`）
