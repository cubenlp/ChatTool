# test_chattool_zulip_basic

测试 `chattool zulip` 的基础链路，覆盖 streams/topics/messages/profile/news 等命令。

## 元信息

- 命令：`chattool zulip <command> [args]`
- 目的：验证 Zulip CLI 的核心功能可用。
- 标签：`cli`
- 前置条件：具备可用的 Zulip 凭证与服务。
- 环境准备：配置 `ZULIP_BOT_API_KEY`、`ZULIP_BOT_EMAIL`、`ZULIP_SITE`。
- 回滚：删除生成的输出文件（默认 `zulip-news-YYYYMMDD.md`）。

## 用例 1：列出 streams

- 初始环境准备：
  - Zulip 凭证可用。
- 相关文件：
  - 无

预期过程和结果：
  1. 执行 `chattool zulip streams`，预期输出 stream 列表。

参考执行脚本（伪代码）：

```sh
chattool zulip streams
```

## 用例 1.1：查看 topics 与 topic 导出

- 初始环境准备：
  - 准备有效 stream 名称。
- 相关文件：
  - 无

预期过程和结果：
  1. 执行 `chattool zulip topics --stream <name>`，预期输出 topic 列表。
  2. 执行 `chattool zulip topic --stream <name> --topic <topic>`，预期输出完整线程。

参考执行脚本（伪代码）：

```sh
chattool zulip topics --stream general
chattool zulip topic --stream general --topic announcements
```

## 用例 2：获取消息

- 初始环境准备：
  - Zulip 凭证可用。
- 相关文件：
  - 无

预期过程和结果：
1. 执行 `chattool zulip messages --before 5`，预期返回消息列表。

参考执行脚本（伪代码）：

```sh
chattool zulip messages --before 5
```

## 用例 2.1：profile

- 初始环境准备：
  - Zulip 凭证可用。
- 相关文件：
  - 无

预期过程和结果：
  1. 执行 `chattool zulip profile`，预期输出用户信息 JSON。

参考执行脚本（伪代码）：

```sh
chattool zulip profile
```

## 用例 3：新闻摘要

- 初始环境准备：
  - 准备输出文件路径。
- 相关文件：
  - `<tmp>/zulip-news.md`

预期过程和结果：
  1. 执行 `chattool zulip news --since-hours 1 --stream general --output <path>`，预期生成 markdown 文件。

参考执行脚本（伪代码）：

```sh
chattool zulip news --since-hours 1 --stream general --output /tmp/zulip-news.md
```

## 清理 / 回滚

- 删除输出文件。
