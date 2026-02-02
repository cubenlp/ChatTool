# Zulip 聊天集成

ChatTool MCP Server 提供了与 Zulip 聊天系统交互的能力。

## 可用工具

- **zulip_list_streams**
  - 描述: 列出订阅的频道 (Stream)
  - 参数:
    - `include_public`: 是否包含所有公开频道 (默认 True)
  - 标签: `zulip`, `read`

- **zulip_get_messages**
  - 描述: 获取消息历史（支持高级过滤）
  - 参数:
    - `anchor`: 起始消息 ID 或 "newest"
    - `num_before`: 向前获取数量
    - `stream`: 频道名称过滤
    - `topic`: 话题过滤
    - `sender`: 发送者邮箱过滤
    - `search`: 关键词搜索
  - 标签: `zulip`, `read`

- **zulip_send_message**
  - 描述: 发送消息
  - 参数:
    - `to`: 接收目标 (频道名称或用户 ID 列表)
    - `content`: 消息内容 (Markdown)
    - `type`: "stream" (频道) 或 "private" (私信)
    - `topic`: 话题名称 (频道消息必填)
  - 标签: `zulip`, `write`

- **zulip_react**
  - 描述: 给消息添加表情反应
  - 参数:
    - `message_id`: 消息 ID
    - `emoji_name`: 表情名称 (如 "thumbs_up")
  - 标签: `zulip`, `write`

- **zulip_upload_file**
  - 描述: 上传文件到 Zulip
  - 参数:
    - `file_path`: 本地文件绝对路径
  - 返回: 文件上传后的 URI
  - 标签: `zulip`, `write`
