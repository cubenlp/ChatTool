# test_chattool_skill_release_boundary

校对 `chattool-dev-review` 与新拆出的 `chattool-release` 是否已经形成清晰边界，避免把正式发版动作混入开发 review。

## 元信息

- 命令：无
- 目的：验证开发 review skill 只负责开发验收，版本 tag / 发布 / release.log 另由独立 release skill 处理。
- 标签：`doc-audit`, `skill`
- 前置条件：仓库内相关 skill 已更新。
- 环境准备：
  - 无
- 回滚：无

## 用例 1：校对 skill 边界与串联关系

- 初始环境准备：
  - 打开 `skills/chattool-dev-review/SKILL.md`
  - 打开 `skills/chattool-dev-review/SKILL.zh.md`
  - 打开 `skills/chattool-release/SKILL.md`
  - 打开 `skills/chattool-release/SKILL.zh.md`
  - 打开 `skills/practice-make-perfact/SKILL.md`
  - 打开 `skills/practice-make-perfact/SKILL.zh.md`
- 相关文件：
  - `skills/chattool-dev-review/SKILL.md`
  - `skills/chattool-dev-review/SKILL.zh.md`
  - `skills/chattool-release/SKILL.md`
  - `skills/chattool-release/SKILL.zh.md`
  - `skills/practice-make-perfact/SKILL.md`
  - `skills/practice-make-perfact/SKILL.zh.md`

预期过程和结果：
  1. `chattool-dev-review` 中英文 skill 都明确写出 release / tag / publish / `release.log` 不属于该 skill，需交给 `chattool-release`。
  2. `chattool-release` 中英文 skill 都明确写出 tag 只能从已合并主线创建，并覆盖 `Publish Package`、PyPI 校验与 `release.log`。
  3. `practice-make-perfact` 中英文 skill 都明确说明：如果任务进入正式发版阶段，应切到 `chattool-release`，而不是继续把发版动作混在 post-task review 里。

参考执行脚本（伪代码）：

```sh
sed -n '1,220p' skills/chattool-dev-review/SKILL.md
sed -n '1,220p' skills/chattool-dev-review/SKILL.zh.md
sed -n '1,260p' skills/chattool-release/SKILL.md
sed -n '1,260p' skills/chattool-release/SKILL.zh.md
sed -n '1,220p' skills/practice-make-perfact/SKILL.md
sed -n '1,220p' skills/practice-make-perfact/SKILL.zh.md
```
