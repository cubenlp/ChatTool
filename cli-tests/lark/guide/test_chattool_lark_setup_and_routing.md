# test_chattool_lark_setup_and_routing

校对 `skills/feishu/guide/setup-and-routing.md` 是否仍然准确描述默认配置来源、`-e/--env` 与路由规则。

## 元信息

- 命令：`chattool env init -t feishu`、`chatenv cat -t feishu`、`chattool lark info -e ...`
- 目的：验证配置与路由文档和当前 CLI 约定一致。
- 标签：`cli`, `doc-audit`
- 前置条件：Feishu 配置项与 `-e/--env` 行为已稳定。
- 环境准备：
  - 无
- 回滚：无

## 用例 1：校对默认配置与路由规则

- 初始环境准备：
  - 打开 `skills/feishu/guide/setup-and-routing.md`。
- 相关文件：
  - `skills/feishu/guide/setup-and-routing.md`

预期过程和结果：
  1. 检查文档是否将 `FEISHU_DEFAULT_RECEIVER_ID` 作为默认接收者。
  2. 检查文档是否只在 CLI 真实测试隔离场景下引入 `FEISHU_TEST_USER_ID`。
  3. 检查文档是否把 topic 扩展统一路由到 `chattool lark <topic> ...`。

参考执行脚本（伪代码）：

```sh
sed -n '1,220p' skills/feishu/guide/setup-and-routing.md
chatenv cat -t feishu
python -m chattool.client.main lark info --help
```

