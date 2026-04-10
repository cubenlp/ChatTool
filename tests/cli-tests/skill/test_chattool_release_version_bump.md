# test_chattool_release_version_bump

校对 ChatTool 的 release skill、practice skill、dev review skill、开发文档和发布 workflow 是否一致强调“版本号必须在 PR 阶段先 bump，PyPI 已有同版本时不能靠重推 tag 假装发版”。

## 元信息

- 命令：无
- 目的：避免只改了某一处说明，结果实际发布流程仍然会出现“workflow 跑了但 PyPI 包没更新”的假阳性发版。
- 标签：`doc-audit`, `skill`, `release`
- 前置条件：仓库内相关 skill、开发文档和 `.github/workflows/publish.yml` 已更新。
- 环境准备：
  - 无
- 回滚：无

## 用例 1：校对版本号前置 bump 与 PyPI 重复版本保护

- 初始环境准备：
  - 打开 `skills/chattool-release/SKILL.md`
  - 打开 `skills/chattool-release/SKILL.zh.md`
  - 打开 `skills/practice-make-perfact/SKILL.md`
  - 打开 `skills/practice-make-perfact/SKILL.zh.md`
  - 打开 `skills/chattool-dev-review/SKILL.md`
  - 打开 `skills/chattool-dev-review/SKILL.zh.md`
  - 打开 `docs/development-guide/index.md`
  - 打开 `docs/development-guide/task-driven-iteration.md`
  - 打开 `.github/workflows/publish.yml`
- 相关文件：
  - `skills/chattool-release/SKILL.md`
  - `skills/chattool-release/SKILL.zh.md`
  - `skills/practice-make-perfact/SKILL.md`
  - `skills/practice-make-perfact/SKILL.zh.md`
  - `skills/chattool-dev-review/SKILL.md`
  - `skills/chattool-dev-review/SKILL.zh.md`
  - `docs/development-guide/index.md`
  - `docs/development-guide/task-driven-iteration.md`
  - `.github/workflows/publish.yml`

预期过程和结果：
  1. `chattool-release` 中英文 skill 都明确写出：目标版本必须在 PR 合并前就已经进入 `src/chattool/__init__.py` / `CHANGELOG.md`。
  2. `practice-make-perfact` 中英文 skill 都明确写出：如果任务面向正式包版本，版本 bump 必须发生在 PR/MR 阶段，而不是合并后打 tag 时。
  3. `chattool-dev-review` 中英文 skill 都明确写出：如果 PR 准备作为某个正式版本发出，`__version__` / changelog 应已经在 diff 中。
  4. 开发文档明确写出：如果 PyPI 已存在该版本，必须先走新的版本 bump 变更，不能复用同版本 tag。
  5. `Publish Package` workflow 明确写出：若 PyPI 已存在该版本则直接失败，不再使用 `twine upload --skip-existing`。

参考执行脚本（伪代码）：

```sh
sed -n '1,240p' skills/chattool-release/SKILL.md
sed -n '1,240p' skills/chattool-release/SKILL.zh.md
sed -n '1,240p' skills/practice-make-perfact/SKILL.md
sed -n '1,240p' skills/practice-make-perfact/SKILL.zh.md
sed -n '1,160p' skills/chattool-dev-review/SKILL.md
sed -n '1,160p' skills/chattool-dev-review/SKILL.zh.md
sed -n '140,190p' docs/development-guide/index.md
sed -n '1,120p' docs/development-guide/task-driven-iteration.md
sed -n '1,120p' .github/workflows/publish.yml
```
