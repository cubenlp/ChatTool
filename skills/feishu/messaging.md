# 飞书 Skill：消息与调试

这份文档只从 CLI 出发说明消息能力，不再按旧的工具或 skill 名称组织。

## 当前已支持的主线命令

```bash
chattool lark info
chattool lark scopes
chattool lark send
chattool lark upload
chattool lark reply
chattool lark listen
chattool lark chat
```

## 当前可直接使用的命令

### 验证与权限

```bash
chattool lark info
chattool lark scopes -f im
```

### 发送文本、图片、文件、卡片、富文本

```bash
chattool lark send "你好，世界"
chattool lark send <receiver_id> "你好，世界"
chattool lark send <receiver_id> --image ./photo.jpg
chattool lark send <receiver_id> --file ./report.pdf
chattool lark send <receiver_id> --card ./card.json
chattool lark send <receiver_id> --post ./post.json
```

### 上传资源

```bash
chattool lark upload ./photo.jpg
chattool lark upload ./report.pdf
chattool lark upload ./data.bin -t file
```

### 引用回复

```bash
chattool lark reply <message_id> "收到，已处理"
```

### 调试监听

```bash
chattool lark listen
chattool lark listen -v
chattool lark listen -l DEBUG
```

### 本地终端调试 AI 对话

```bash
chattool lark chat
chattool lark chat --system "你是一名飞书助手"
chattool lark chat --user debug_user
```

## 目标扩展方向

消息相关的后续 CLI 继续沿 `chattool lark` 主线扩展，不新开独立 skill 入口。第一阶段按这些 topic 分组规划：

- `chattool lark im ...`
  - 读取历史消息
  - 展开线程
  - 搜索消息
  - 下载消息资源
- `chattool lark troubleshoot ...`
  - 做消息、权限、事件回调、卡片交互的诊断

## 真实测试要求

消息相关 CLI 测试文档必须写清：

- 使用默认 `chatenv` 或 `-e/--env`
- 所需配置项：
  - `FEISHU_APP_ID`
  - `FEISHU_APP_SECRET`
  - `FEISHU_DEFAULT_RECEIVER_ID`
  - `FEISHU_TEST_USER_ID`
  - `FEISHU_TEST_USER_ID_TYPE`
- 回滚方式：
  - 删除测试消息
  - 删除临时上传文件

## 开发补充

- 业务输入直接走 CLI 参数，不新增临时环境变量。
- 先写 `cli-tests/*.md`，再实现 CLI。
- 继续扩消息链路前，先查 `api-reference.md` 和 `channel-rules.md`。
