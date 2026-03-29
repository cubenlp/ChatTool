# test_chattool_lark_skill_index

校对 `skills/feishu/` 是否已经收缩为双语入口文件，并把使用者路由到当前的官方 `lark-cli` 文档工作流。

## 元信息

- 命令：`lark-cli`
- 目的：验证飞书 skill 已简化为双语入口，并明确当前文档链路应如何在 `im` / `docs` / `drive` / `wiki` / `chattool lark` 之间分工。
- 标签：`cli`, `doc-audit`, `skill`
- 前置条件：`skills/feishu/` 已完成清理，仅保留入口文件 `SKILL.md` 与 `SKILL.zh.md`。
- 环境准备：
  - 无
- 回滚：无

## 用例 1：校对双语入口与官方 CLI 路由

- 初始环境准备：
  - 打开 `skills/feishu/SKILL.md` 与 `skills/feishu/SKILL.zh.md`。
- 相关文件：
  - `skills/feishu/SKILL.md`
  - `skills/feishu/SKILL.zh.md`

预期过程和结果：
   1. 检查根目录是否只保留两个入口文件 `SKILL.md` 与 `SKILL.zh.md`。
   2. 检查索引中是否已明确把官方 `lark-cli` 作为默认推荐入口。
   3. 检查索引中是否给出子模块目录和仓库内教程地址，包括消息与会话调试博客。
   4. 检查索引中是否写清消息走 `im`、文档正文走 `docs`、评论与权限走 `drive`、wiki 解析走 `wiki`。
   5. 检查索引中是否保留 `chattool lark info/send/chat` 作为最短调试或送达链路。
   6. 检查 `skills/feishu/` 下不再残留其他专题 `.md` 文件。

参考执行脚本（伪代码）：

```sh
sed -n '1,220p' skills/feishu/SKILL.md
sed -n '1,220p' skills/feishu/SKILL.zh.md
find skills/feishu -type f | sort
```
