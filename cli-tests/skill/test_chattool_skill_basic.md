# test_chattool_skill_basic

测试 `chattool skill` 的基础链路，覆盖技能列表与安装流程。

## 元信息

- 命令：`chattool skill <command> [args]`
- 目的：验证技能管理 CLI 的基础可用性。
- 标签：`cli`
- 前置条件：技能目录存在。
- 环境准备：设置 `CHATTOOL_SKILLS_DIR` 或 `--source`。
- 回滚：删除安装的技能目录。

## 用例 1：列出技能

- 初始环境准备：
  - 准备可用技能目录。
- 相关文件：
  - 无

预期过程和结果：
  1. 执行 `chattool skill list --source <dir>`，预期输出技能列表。

参考执行脚本（伪代码）：

```sh
chattool skill list --source /path/to/skills
```

## 用例 2：安装技能

- 初始环境准备：
  - 准备技能源目录与目标目录。
- 相关文件：
  - `<dest>/<skill>/SKILL.md`

预期过程和结果：
  1. 执行 `chattool skill install <name> --source <dir> --dest <dir>`，预期安装成功。

参考执行脚本（伪代码）：

```sh
chattool skill install demo --source /path/to/skills --dest /tmp/skills
chattool skill install --all --source /path/to/skills --dest /tmp/skills
```

## 用例 3：拒绝安装无效 skill

- 初始环境准备：
  - 准备一个包含 `SKILL.md` 但缺少 YAML frontmatter 的 skill 目录。
- 相关文件：
  - `<source>/<skill>/SKILL.md`

预期过程和结果：
  1. 执行 `chattool skill install <name> --source <dir> --dest <dir>`，预期命令失败，并明确提示 `SKILL.md` 缺少 `---` 包裹的 YAML frontmatter。
  2. 目标目录下不应生成该 skill。

参考执行脚本（伪代码）：

```sh
chattool skill install broken --source /path/to/skills --dest /tmp/skills
```

## 清理 / 回滚

- 删除 `/tmp/skills/<name>`。
