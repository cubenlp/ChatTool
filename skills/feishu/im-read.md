# 飞书 Skill：IM CLI 规划

这份文档描述目标 `chattool lark im ...` 命令面，以及对应的测试设计方向。虽然文件名保留 `im-read` 语义，但 CLI 主线统一收口为 `im`。

## 目标入口

```bash
chattool lark im ...
```

## 当前已支持命令面

```bash
chattool lark im list --chat-id <chat_id>
chattool lark im download <message_id> <file_key> --type <image|file>
```

常用可选参数：

- `--relative-hours`
- `--start-time`
- `--end-time`
- `--page-size`
- `--page-token`
- `--sort`

## 后续规划命令面

```bash
chattool lark im thread <thread_id>
chattool lark im search --query <text>
```

## CLI 设计原则

- 当前先把 `list / download` 做稳，再继续补 `thread / search`
- 当前真实链路按 `chat_id` 收口，不再先做 `open_id` 分支
- 时间过滤、分页、排序都应是显式 CLI 参数

## 真实测试要求

`cli-tests/lark-im/*.md` 至少覆盖：

- 读取单聊或群聊消息
- 下载消息图片或文件
- thread / search 在接口稳定后再补对应 `.md` / `.py`

文档必须写清：

- 所需配置项：
  - `FEISHU_APP_ID`
  - `FEISHU_APP_SECRET`
  - `FEISHU_TEST_USER_ID`
  - `FEISHU_TEST_USER_ID_TYPE`
- 真实消息来源
- 回滚方式：
  - 删除测试消息
  - 删除临时下载文件

## 当前状态

- 当前已落地 `list` 与 `download` 两条真实 CLI。
- `thread` / `search` 继续保留为后续项，不在这轮假设为已支持。
