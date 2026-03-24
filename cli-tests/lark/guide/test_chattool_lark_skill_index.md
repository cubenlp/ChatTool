# test_chattool_lark_skill_index

校对 `skills/feishu/SKILL.md` 是否仍然是飞书唯一入口索引，并且能把使用者正确路由到 `chattool lark` 与对应 topic 测试目录。

## 元信息

- 命令：`chattool lark`
- 目的：验证飞书主 skill 索引与 `cli-tests/lark/<topic>/` 目录结构一致。
- 标签：`cli`, `doc-audit`
- 前置条件：`skills/feishu/` 与 `cli-tests/lark/` 已完成 topic 收口。
- 环境准备：
  - 无
- 回滚：无

## 用例 1：校对唯一入口与 topic 索引

- 初始环境准备：
  - 打开 `skills/feishu/SKILL.md`。
- 相关文件：
  - `skills/feishu/SKILL.md`

预期过程和结果：
  1. 检查根目录是否只保留一个入口文件 `SKILL.md`。
  2. 检查索引中是否仍以 `chattool lark` 作为唯一推荐入口。
  3. 检查 `guide/`、`messaging/`、`documents/`、`im/`、`troubleshoot/`、`task/`、`calendar/`、`bitable/` 是否都有测试映射。

参考执行脚本（伪代码）：

```sh
sed -n '1,220p' skills/feishu/SKILL.md
find cli-tests/lark -maxdepth 2 -type f | sort
```

