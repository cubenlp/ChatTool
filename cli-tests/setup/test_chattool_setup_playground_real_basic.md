# test_chattool_setup_playground_real_basic

验证 `chattool setup playground` 在真实 CLI 下会生成与 workspace 类似的外层协作骨架，同时保留 `ChatTool/` 仓库和同步到 `knowledge/skills/` 的工作区 skills。

## 元信息

- 命令：`chattool setup playground`
- 目的：验证 playground 骨架目录、`knowledge/skills/` 同步位置，以及 ChatTool 仓库 clone 的真实行为。
- 标签：`cli`
- 前置条件：可从本地 ChatTool 仓库作为 clone 源。
- 环境准备：使用临时目录作为 workspace 根目录，不污染仓库。
- 回滚：测试结束后临时目录自动删除。

## 用例 1：基础 playground 落盘新骨架

- 初始环境准备：
  - 创建空临时目录作为 workspace 根目录。
  - 使用当前本地 ChatTool 仓库作为 `--chattool-source`。

预期过程和结果：
  1. 执行 `chattool setup playground --workspace-dir <workspace-dir> --chattool-source <repo-dir> -I`，预期命令成功。
  2. 预期生成 `AGENTS.md`、`CHATTOOL.md`、`MEMORY.md`、`thoughts/current.md`、`reports/README.md`、`playgrounds/README.md`、`knowledge/README.md`。
  3. 预期在目标目录下 clone `ChatTool/`。
  4. 预期 `knowledge/memory/`、`knowledge/skills/`、`playgrounds/scratch/` 存在。
  5. 预期 skills 从 clone 出来的 `ChatTool/skills/` 同步到 `knowledge/skills/`，并给每个 skill 创建 `experience/README.md`。
  6. 预期不再创建旧的顶层 `Memory/`、`skills/`、`scratch/`。

参考执行脚本（伪代码）：

```sh
chattool setup playground --workspace-dir /tmp/my-playground --chattool-source /path/to/ChatTool -I
assert new scaffold files exist
assert ChatTool repo exists
assert knowledge/skills contains copied skills with experience readmes
assert legacy top-level Memory/ skills/ scratch/ do not exist
```
