---
name: practice-make-perfact
description: 把“先完成任务、后复盘规范”的工作方式沉淀成可复用流程，持续推动 ChatTool 成长。
version: 0.1.0
---

# Practice Make Perfact（中文）

目标：把“先完成任务、后复盘规范”的工作方式沉淀成可复用流程，持续推动 ChatTool 成长。

## 核心原则

- 先做事，再整理：先把任务完成，再统一规范与复盘。  
- 能复用进 `src/` 的能力就进 `src/`；仅任务相关的就放 `skills/`。  
- 过程尽量用 CLI 交互，保持可审计、可复现。  
- 每个任务结束后做一次规范化 review。

## 执行流程

1. **任务执行优先**  
   - 用 CLI 完成读取、查询和数据导出  
   - 避免提前写过多文档

2. **能力归类**  
   - 通用能力：补充到 `src/`（工具层、CLI、MCP）  
   - 任务特定：补充到 `skills/<name>/`

3. **技能落地**  
   - 必须包含 `SKILL.md` 与 `SKILL.zh.md`  

4. **文档同步**  
   - 在 `docs/` 增补“过程说明”  
   - 如新增文档，更新 `mkdocs.yml`

5. **任务后复盘**  
   - 按开发规范检查并更新：`docs/development-guide/index.md`

## 结果要求

- 每次任务都能沉淀到工具、技能或文档。  
- 阶段化输出与命名一致，便于检索与复用。
