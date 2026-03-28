# test_chattool_skill_practice_make_perfact_reference

校对 `skills/practice-make-perfact` 是否已经包含最小 CLI reference 机制，方便后处理阶段快速判断该复用已有 CLI 还是补新命令。

## 元信息

- 命令：无
- 目的：验证 `practice-make-perfact` skill 不再只有流程说明，也提供 CLI 检索入口。
- 标签：`doc-audit`, `skill`
- 前置条件：仓库内 skill 已更新。
- 环境准备：
  - 无
- 回滚：无

## 用例 1：校对 skill 与 reference 文件

- 初始环境准备：
  - 打开 `skills/practice-make-perfact/SKILL.md`
  - 打开 `skills/practice-make-perfact/SKILL.zh.md`
  - 打开 `skills/practice-make-perfact/references/cli-reference.md`
- 相关文件：
  - `skills/practice-make-perfact/SKILL.md`
  - `skills/practice-make-perfact/SKILL.zh.md`
  - `skills/practice-make-perfact/references/cli-reference.md`

预期过程和结果：
  1. 检查中英文 skill 都提到 CLI reference / 现有 CLI 检查。
  2. 检查 `references/cli-reference.md` 存在，并覆盖 `chattool lark`、`chattool gh`、`chattool setup` 等主线入口。

参考执行脚本（伪代码）：

```sh
sed -n '1,220p' skills/practice-make-perfact/SKILL.md
sed -n '1,220p' skills/practice-make-perfact/SKILL.zh.md
sed -n '1,220p' skills/practice-make-perfact/references/cli-reference.md
```
