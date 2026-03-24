# 飞书 Skill：配置与路由

## 默认入口

- 统一从 `chattool lark` 开始。
- 不要先写一次性 OpenAPI 脚本。
- 如果现有 CLI 不够用，先定义目标命令和 `cli-tests/*.md`，再做实现。

## 默认配置来源

推荐优先使用 ChatTool 配置：

```bash
chattool env init -t feishu
chattool env set FEISHU_DEFAULT_RECEIVER_ID=f25gc16d
```

查看当前飞书配置时，优先用：

```bash
chatenv cat -t feishu
```

默认消息接收者统一使用：

- `FEISHU_DEFAULT_RECEIVER_ID`

CLI 测试若需要隔离测试用户，再额外使用：

- `FEISHU_TEST_USER_ID`
- `FEISHU_TEST_USER_ID_TYPE`

## `-e/--env`

飞书子命令支持从指定 `.env` 或已保存 profile 读取配置：

```bash
chattool lark info -e ~/.config/chattool/.env
chattool lark info -e work
```

适用场景：

- 多个飞书应用切换使用
- 当前 shell 环境较脏，需要显式固定配置来源
- 真实测试要锁定一份稳定环境

## 路由规则

1. 能用 `chattool lark` 完成，就不要退回脚本或其它工具名。
2. 高复用动作优先进入 `chattool lark <topic> ...`。
3. 主线命令先看：
   - `info`
   - `scopes`
   - `send`
   - `upload`
   - `reply`
   - `notify-doc`
   - `listen`
   - `chat`
   - `doc ...`
4. 规划中的专题命令统一挂在：
   - `chattool lark bitable ...`
   - `chattool lark calendar ...`
   - `chattool lark im ...`
   - `chattool lark task ...`
   - `chattool lark troubleshoot ...`

## 最小排查顺序

```bash
chattool lark info
chattool lark scopes -f im
chattool lark send "hello"
chattool lark listen -l DEBUG
```

顺序含义：

- `info` 看凭证和激活状态
- `scopes` 看权限是否齐
- `send` 验证主动发送链路
- `listen` 验证被动接收链路
