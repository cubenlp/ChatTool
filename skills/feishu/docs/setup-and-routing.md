# 飞书 Skill：配置与路由

## 凭证来源

推荐优先使用 ChatTool 配置：

```bash
chattool env init -t feishu
chattool env set FEISHU_DEFAULT_RECEIVER_ID=f25gc16d
```

也可以直接导出环境变量：

```bash
export FEISHU_APP_ID=cli_xxxxxxxxxxxxxxxx
export FEISHU_APP_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

## `-e/--env`

飞书子命令支持从指定 `.env` 或已保存 profile 读取配置：

```bash
chattool lark info -e ~/.config/chattool/.env
chattool lark info -e work
```

适用场景：

- 多个飞书应用切换使用。
- 当前 shell 环境比较脏，需要显式固定配置来源。

## 路由规则

优先级如下：

1. 能用 `chattool lark` 完成，就不要先写脚本。
2. 业务输入优先走 CLI 参数，不新增临时环境变量。
3. 如果当前需求具有复用价值，优先补 `src/chattool/tools/lark/`，再更新 skill。
4. 如果只是任务侧约定或执行流程，补到 `skills/feishu/`。

## 最小排查顺序

```bash
chattool lark info
chattool lark scopes -f im
chattool lark send <receiver> "hello"
chattool lark listen -l DEBUG
```

顺序含义：

- `info` 看凭证和激活状态。
- `scopes` 看权限是否齐。
- `send` 验证主动发送链路。
- `listen` 验证被动接收链路。
