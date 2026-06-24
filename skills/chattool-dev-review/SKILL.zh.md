---
name: chattool-dev-review
description: 对 ChatTool 或 ChatArch 改动做开发后 review，检查 lazy import、交互式 CLI、chatstyle/chatenv 边界、文档测试变更记录和发版边界。
version: 0.3.0
---

# ChatTool 开发 Review

在 ChatTool 或 ChatArch 的功能、CLI、skill 或 scaffold 更新完成后使用这个 skill。

默认范围是当前改动，不是全仓审计，除非用户明确要求扩大范围。

边界：这个 skill 只负责开发验收。合并时机、tag、包发布和 PyPI 校验交给 `$chattool-release`。

## 检查重点

1. Lazy import 和命令接线
   - `src/chattool/client/main.py` 的子命令应保持 lazy load。
   - CLI 模块避免在 import 阶段加载重实现模块。
   - 只在命令执行时需要的导入通常应放到命令函数内部。

2. 交互式 CLI 行为
   - 可恢复缺参在 TTY 中应自动进入交互。
   - `-i` 应强制进入当前命令的 prompt 流程。
   - `-I` 应禁止提示，并在必填输入缺失时快速失败。
   - prompt 展示默认值必须与实际执行默认值一致。
   - 敏感值必须在 prompt 和 summary 中脱敏。

3. ChatStyle 边界
   - 外部 `chatstyle` 是共享 prompt、choice、render、mask、schema 行为的 canonical runtime。
   - ChatTool 命令需要 ChatTool policy、usage、warning filters 或旧 mock patch 点时，使用 `chattool.interaction`。
   - 独立 ChatArch 包应直接导入 `chatstyle`，不得依赖 `chattool.interaction`。
   - 不要在 ChatTool 内重新创建本地 style/runtime 层。

4. ChatEnv 边界
   - `chatenv` 是独立 typed env/profile CLI。
   - ChatTool 通过 `[project.entry-points."chatenv.configs"]` 暴露具体 config schema。
   - 新业务包只注册 provider module，不复制 env CLI，也不让 `chatenv` 硬编码业务包 import。
   - 示例应使用 `chatenv init -t <alias>` 和 `chatenv cat -t <alias>`，不要写嵌套在 ChatTool 下的 env 命令。

5. PyPI scaffold 正确性
   - `chatpypi` 示例必须匹配独立 ChatPyPI 命令面：`init/build/check/probe/upload`。
   - `chatarch` scaffold 示例应包含 `chatstyle` / `chatenv` 依赖和当前 mkdocs/workflow 选项。
   - 可以说明 `chatpypi <name>` 是 `chatpypi init <name>` 的便捷 wrapper。

6. 文档、测试和变更记录
   - 行为变更同步更新相关 `docs/`。
   - 用户可见行为同步更新 `README.md`。
   - feature/fix/skill 更新同步更新 `CHANGELOG.md`。
   - CLI 变更保持 `tests/cli-tests/` 的 doc-first case 或 `tests/mock-cli-tests/` 的 mock case 对齐。
   - 如果 PR 计划作为特定版本发出，版本和 changelog 必须在合并前就已经出现在 diff 里。

## Review 流程

1. 用 `git diff --stat`、`git diff --name-only` 和用户上下文确定范围。
2. 检查变更的 CLI 入口、命令模块、skills、docs 和 tests。
3. 搜索旧命令名和边界违规。
4. 为变更路径运行最小有用验证命令或测试。
5. 先输出 findings，按严重程度排序，并写明具体文件位置和风险。

## 常用命令

```bash
git diff --stat
git diff --name-only
rg -n "click\.prompt|click\.confirm|--interactive|--no-interactive|-i/-I|resolve_interactive_mode|ask_text|ask_confirm|ask_select|ask_path" src docs tests skills
rg -n "pypi|cert|chatenv|chatstyle|chattool.interaction" skills docs tests README.md CHANGELOG.md
rg -n "chatstyle|chattool.interaction|chatenv.configs|BaseEnvConfig|EnvField" src docs tests skills pyproject.toml
```

## 输出要求

- 按 code review 风格输出。
- 先写 findings，并按严重程度排序。
- 每条 finding 给出文件位置和具体风险。
- 简短总结放在 findings 之后。
- 如果没有问题，明确写“未发现问题”，并补充剩余测试风险。
