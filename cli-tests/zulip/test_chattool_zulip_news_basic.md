# chattool zulip news 基础用例

## 元信息

- 命令：`chattool zulip news [options]`
- 目的：验证 zulip news 命令的帮助信息、输出文件与回退逻辑。
- 标签：`cli`
- 前置条件：具备可用的 Zulip 凭证与服务。
- 环境准备：确保 `ZULIP_BOT_API_KEY`、`ZULIP_BOT_EMAIL`、`ZULIP_SITE` 已配置。
- 回滚：删除生成的输出文件。
- 来源：`tests/zulip/test_cli_news.py`

## 状态

- TODO：需要确认真实 Zulip 环境与凭证后再落地 `.py`。

## 用例 1：帮助信息不包含 send

### 初始环境准备

- 无

### 相关文件

- 无

### 预期过程和结果

1. 执行 `chattool zulip --help`，预期输出不包含 `send` 子命令。

### 参考执行脚本（伪代码）

```sh
chattool zulip --help
```

### 清理 / 回滚

- 无

## 用例 2：生成新闻摘要文件

### 初始环境准备

- 准备可写的输出目录。

### 相关文件

- `<tmp>/zulip-news.md`

### 预期过程和结果

1. 执行 `chattool zulip news --since-hours 1 --stream general --output <path>`，预期生成 markdown 文件。
2. 打开输出文件，预期包含标题与摘要内容。

### 参考执行脚本（伪代码）

```sh
chattool zulip news --since-hours 1 --stream general --output /tmp/zulip-news.md
```

### 清理 / 回滚

- 删除输出文件。

## 用例 3：LLM 失败时回退

### 初始环境准备

- 准备可写的输出目录。

### 相关文件

- `<tmp>/zulip-news.md`

### 预期过程和结果

1. 执行 `chattool zulip news ...` 并触发 LLM 异常，预期 CLI 提示回退。
2. 输出文件包含规则生成的摘要内容。

### 参考执行脚本（伪代码）

```sh
chattool zulip news --since-hours 1 --stream general --output /tmp/zulip-news.md
```

### 清理 / 回滚

- 删除输出文件。
