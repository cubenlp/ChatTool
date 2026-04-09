# test_chattool_zulip_interactive_basic

测试 `chattool zulip` 在 `topics` / `topic` 缺参时的默认交互补问行为。

## 用例 1：`topics` 缺少 stream 时自动补问

预期过程和结果：
1. 在交互可用环境下执行 `chattool zulip topics`。
2. CLI 应补问 `stream`，随后查询 topics。

## 用例 2：`topic` 缺少 stream/topic 时自动补问

预期过程和结果：
1. 在交互可用环境下执行 `chattool zulip topic`。
2. CLI 应补问 `stream` 和 `topic`，随后导出 thread。

## 用例 3：`-I` 禁用交互时报错

预期过程和结果：
1. 执行 `chattool zulip topics -I`。
2. CLI 应直接报缺少必要参数。
