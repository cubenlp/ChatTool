---
name: chattool-dev-review
description: 对 ChatTool 新功能做开发后 review。适用于检查 lazy import、缺参自动交互、统一 utils/tui 交互样式，以及相关文档/测试/变更记录是否同步更新。
version: 0.2.1
---

# ChatTool 开发 Review

这个 skill 用于在 ChatTool 新功能或 CLI 变更完成后做一轮开发验收。

默认只 review 本次 feature 相关改动，除非用户明确要求做全局检查。

边界：这个 skill 只负责开发验收，不负责发版时机、tag、`Publish Package`、PyPI 校验或 `release.log`。这些动作统一交给 `$chattool-release`。

## 检查重点

1. 最小 import / lazy import
   - 统一入口保持 lazy load，重点看 [src/chattool/client/main.py](src/chattool/client/main.py)。
   - CLI 模块避免在顶层直接导入重实现模块。
   - 如果某个导入只在命令执行时需要，优先下沉到函数内部。

2. 缺参时是否自动进入交互
   - 可通过提问补全的必填参数，缺失时应自动进入 interactive。
   - `-i` 应强制进入当前命令的交互流程。
   - `-I` 应完全禁止交互，缺参时快速失败。
   - 交互里展示的默认值必须与真实执行一致。

3. 是否使用统一交互样式
   - 新增 CLI 交互优先走 [src/chattool/interaction](src/chattool/interaction)。
   - 不要为新的交互流程继续直接写 `click.prompt` / `click.confirm`，除非有明确理由并在文档中说明。
   - 敏感信息在 prompt 和输出中必须脱敏。

4. 文档和测试是否同步
   - 更新相关 `docs/`
   - 用户可见功能同步更新 [README.md](README.md)
   - 更新 [CHANGELOG.md](CHANGELOG.md)
   - CLI 变更同步更新 [cli-tests](cli-tests) 下对应 `.md` 与需要的 `.py`
   - 如果这个 PR 计划作为某个正式包版本发出，那么目标 `__version__` 和 changelog 变更必须在合并前就已经出现在 diff 里；不要把版本号调整拖到合并后打 tag 阶段。

## Review 流程

1. 先确定范围
   - 优先看当前 diff：`git diff --stat`、`git diff --name-only`、`git diff --cached --name-only`
   - 如果用户指定了功能或文件，先聚焦这些位置
   - 只有在用户明确要求时才做全仓检查

2. 再看 CLI 入口和改动命令
   - 检查 `cli.py` / `main.py` 是否引入了新的顶层重导入
   - 检查新的交互流程里是否出现 `click.prompt` / `click.confirm`
   - 检查 `--interactive/--no-interactive`、`-i/-I` 和缺参处理是否一致

3. 检查文档与测试
   - 在 `docs/`、`README.md`、`CHANGELOG.md`、`cli-tests/` 中搜索对应命令名
   - 新参数、新环境变量、新行为如果没有同步文档，记为 finding

4. 做最小必要验证
   - 运行最相关、最小的一条测试或 CLI 命令
   - 如果无法验证，要在结论里明确说明

## 常用命令

```bash
git diff --stat
git diff --name-only
rg -n "click\\.prompt|click\\.confirm|--interactive|--no-interactive|-i/-I|resolve_interactive_mode|ask_text|ask_confirm|ask_select|ask_path" src docs tests cli-tests
rg -n "lazy import|src/chattool/interaction|interactive" docs/development-guide docs README.md
```

## 输出要求

- 按 code review 风格输出
- 先写 findings，再写简短总结
- 每条 finding 给出文件位置和具体风险
- 如果没有问题，要明确写出 “未发现问题”，并补充剩余测试风险
