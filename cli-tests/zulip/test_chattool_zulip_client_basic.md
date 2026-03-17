# chattool zulip 客户端基础用例

## 元信息

- 命令：`chattool zulip <command> [options]`
- 目的：验证 Zulip 客户端的基础能力在 CLI 真实链路中可用。
- 标签：`cli`
- 前置条件：具备可用的 Zulip 凭证与服务。
- 环境准备：确保 `ZULIP_BOT_API_KEY`、`ZULIP_BOT_EMAIL`、`ZULIP_SITE` 已配置。
- 回滚：无
- 来源：`tests/tools/zulip/test_zulip_client.py`

## 状态

- TODO：需要确认真实 Zulip 环境与凭证后再落地 `.py`。

## 用例 1：列出 stream

### 初始环境准备

- Zulip 凭证可用。

### 相关文件

- 无

### 预期过程和结果

1. 执行 `chattool zulip streams`（或等价命令），预期返回 stream 列表。

### 参考执行脚本（伪代码）

```sh
chattool zulip streams
```

### 清理 / 回滚

- 无

## 用例 2：获取消息

### 初始环境准备

- Zulip 凭证可用。

### 相关文件

- 无

### 预期过程和结果

1. 执行 `chattool zulip messages --num-before 5`，预期返回消息列表。

### 参考执行脚本（伪代码）

```sh
chattool zulip messages --num-before 5
```

### 清理 / 回滚

- 无

## 用例 3：发送私信给自己

### 初始环境准备

- Zulip 凭证可用。

### 相关文件

- 无

### 预期过程和结果

1. 执行 `chattool zulip send --to self --type private`，预期返回发送成功。
2. 再次查询消息，预期可看到刚发送的消息。

### 参考执行脚本（伪代码）

```sh
chattool zulip send --to self --type private --content "Integration test message"
chattool zulip messages --num-before 10 --search "Integration test message"
```

### 清理 / 回滚

- 无

## 用例 4：搜索消息

### 初始环境准备

- Zulip 凭证可用。

### 相关文件

- 无

### 预期过程和结果

1. 执行 `chattool zulip messages --search "hello"`，预期返回列表。

### 参考执行脚本（伪代码）

```sh
chattool zulip messages --search "hello"
```

### 清理 / 回滚

- 无
