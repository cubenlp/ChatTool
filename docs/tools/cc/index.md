# CC-Connect 管理

`chattool cc` 提供 cc-connect 的最小可用管理能力，面向快速上手（单配置、单项目）。

## 快速开始

```bash
chattool setup cc-connect
chattool cc init -i --quiet
chattool cc start
```

默认配置文件：`~/.cc-connect/config.toml`
默认日志文件：`~/.cc-connect/cc-connect.log`

## 命令

- `chattool setup cc-connect`：安装/检查 Node.js、npm 与 cc-connect
- `chattool cc setup`：`chattool setup cc-connect` 的别名
- `chattool cc init`：生成最小可用配置（Agent + Platform + Project）
- `chattool cc start`：启动 cc-connect（前台输出，同时写入日志）
- `chattool cc status`：查看基础状态
- `chattool cc logs`：查看/跟随日志
- `chattool cc doctor`：快速自检

## 说明

- 一阶段只覆盖高频最小能力，更多高级配置请直接编辑 `config.toml`。
- `chattool cc init -i` 若检测到已有配置文件，会先确认是否覆盖；确认后才继续进入 Agent/Platform/Mode 与凭证填写。
- `chattool cc init -i` 会把已有配置与环境候选值直接作为默认值展示，回车即可复用，不再额外询问是否沿用默认。
- `chattool cc init` 现支持 `--quiet/--no-quiet`，写入项目级 `quiet = true/false`，用于控制默认是否隐藏 thinking / tool progress 中间消息。
- 若已有平台凭证且本次不重新填写，`chattool cc init -i` 会保留原有平台配置，不会清空已有 token / secret。
- `chattool cc init -i` 若检测到已有项目级 `quiet` 配置，会把它作为 quiet 提示的默认值展示。
- 飞书平台会直接提示 `app_id` 与 `app_secret`；如果当前 `chatenv` 已配置飞书凭证，会自动作为默认候选值。
- 生成的配置会包含可选代理字段（`proxy`/`proxy_username`/`proxy_password`）注释。
- 如需填写代理配置，请使用 `chattool cc init -i --full-options`。

## 代理说明

当你的 IP 不固定或平台侧有白名单要求时，可以在平台配置下添加代理字段：

```toml
# proxy = ""  # optional: forward proxy for API calls if your IP is dynamic
#             # 可选：正向代理，用于 IP 不固定的场景
#             # e.g. "http://your-vps-ip:8888" — the VPS IP goes into trusted IP list
#             # 示例："http://你的VPS-IP:8888" — 将 VPS IP 加入可信 IP 列表
# proxy_username = ""  # optional: proxy authentication username / 代理认证用户名
# proxy_password = ""  # optional: proxy authentication password / 代理认证密码
```

提示：如果你开启了本地代理，建议设置 `NO_PROXY=127.0.0.1,localhost`，避免本地服务请求被代理转发。
