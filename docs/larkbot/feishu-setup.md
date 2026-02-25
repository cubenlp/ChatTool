# 飞书平台配置教程

本章介绍在 [飞书开放平台](https://open.feishu.cn/) 创建机器人应用、获取凭证、申请权限、配置事件订阅的完整流程。**所有步骤均需要在飞书开放平台操作，本文会标注每一步的截图位置。**

---

## 第一步：创建企业自建应用

1. 打开 [飞书开放平台](https://open.feishu.cn/)，使用企业管理员账号登录。
2. 点击右上角「**开发者后台**」。
3. 在「应用列表」页面，点击「**创建企业自建应用**」。

!!! info "截图占位"
    <!-- TODO: 上传截图 → 「创建企业自建应用」按钮位置 -->
    ![20260226020952](https://qiniu.wzhecnu.cn/FileBed/source/20260226020952.png){ loading=lazy }

1. 填写应用名称（如 `AI 助手`）、应用描述，选择应用图标，点击「**确认创建**」。

!!! info "截图占位"
    <!-- TODO: 上传截图 → 填写应用信息表单 -->
    ![20260226021050](https://qiniu.wzhecnu.cn/FileBed/source/20260226021050.png){ loading=lazy }

---

## 第二步：获取 App ID 和 App Secret

创建成功后，进入应用详情页：

1. 点击左侧菜单「**凭证与基础信息**」。
2. 复制 **App ID** 和 **App Secret**（点击「复制」图标）。

!!! info "截图占位"
    <!-- TODO: 上传截图 → 凭证与基础信息页面 -->
    ![20260226021130](https://qiniu.wzhecnu.cn/FileBed/source/20260226021130.png){ loading=lazy }

!!! warning "安全提示"
    App Secret 相当于密码，请勿提交到 Git 仓库。推荐使用 `.env` 文件或环境变量管理：
    
    ```bash
    chatenv init -i -t feishu
    ```

将凭证写入环境变量后，`LarkBot` 会自动读取：

```python
from chattool.tools.lark import LarkBot

bot = LarkBot()  # 自动从环境变量读取
```

也可以显式传入：

```python
from chattool.tools.lark import LarkBot
from chattool.config.main import FeishuConfig

config = FeishuConfig()
config.FEISHU_APP_ID.value = "cli_xxx"
config.FEISHU_APP_SECRET.value = "xxx"
bot = LarkBot(config=config)
```

---

## 第三步：开启机器人能力

在应用详情页：

1. 点击左侧菜单「**应用功能**」→「**机器人**」。
2. 开启「**机器人**」开关。

!!! info "截图占位"
    <!-- TODO: 上传截图 → 开启机器人能力 -->
    ![开启机器人](../assets/screenshots/larkbot/04_enable_bot.png){ loading=lazy }

---

## 第四步：申请权限（Scope）

在应用详情页：

1. 点击左侧菜单「**权限管理**」。
2. 在搜索框输入权限名，找到后点击「**申请**」。

!!! info "截图占位"
    <!-- TODO: 上传截图 → 权限管理页面，搜索并申请权限 -->
    ![权限管理](../assets/screenshots/larkbot/05_permissions.png){ loading=lazy }

### 常用权限速查

根据你的使用场景申请对应权限：

| 场景 | 权限名 | 说明 |
|------|--------|------|
| 发送消息给用户（user_id 方式） | `im:message` + `contact:user.employee_id:readonly` | 必须同时申请 |
| 发送消息给群（chat_id 方式） | `im:message` | — |
| 查看群信息 | `im:chat:readonly` | — |
| 管理群成员 | `im:chat.member` | — |
| 读取消息历史 | `im:message:readonly` | — |
| 接收消息事件 | `im:message.receive_v1`（事件权限） | 在「事件订阅」中单独配置 |
| 管理群公告 | `im:chat:announcement` | — |

!!! tip "权限审批"
    自建应用的权限申请通常**无需审批**，立即生效。  
    如果是第三方应用，需要企业管理员在管理后台审批。

---

## 第五步：配置事件订阅

### 方式一：WebSocket 长连接（推荐本地开发）

1. 点击左侧菜单「**事件订阅**」。
2. 「请求方式」选择「**使用长连接接收事件**」。
3. 无需填写请求 URL。

!!! info "截图占位"
    <!-- TODO: 上传截图 → 事件订阅选择「长连接」 -->
    ![WebSocket 长连接](../assets/screenshots/larkbot/06_websocket_mode.png){ loading=lazy }

4. 在「**添加事件**」中搜索并订阅所需事件，例如 `接收消息`（`im.message.receive_v1`）。

!!! info "截图占位"
    <!-- TODO: 上传截图 → 添加 im.message.receive_v1 事件 -->
    ![添加事件](../assets/screenshots/larkbot/07_add_event.png){ loading=lazy }

启动代码只需一行：

```python
bot.start()          # 默认使用 WebSocket 模式
# 或
bot.start(mode="ws") # 显式指定
```

### 方式二：Webhook（生产环境）

1. 「请求方式」选择「**将事件发送至开发者服务器**」。
2. 填写「**请求 URL**」（需要 HTTPS 公网地址，例如 `https://your-server.com/webhook/event`）。
3. 填写 **Encrypt Key** 和 **Verification Token**（可选，用于安全验证）。

!!! info "截图占位"
    <!-- TODO: 上传截图 → Webhook 配置页面 -->
    ![Webhook 配置](../assets/screenshots/larkbot/08_webhook_config.png){ loading=lazy }

启动 Flask Webhook 服务：

```python
bot.start(
    mode="flask",
    encrypt_key="your_encrypt_key",          # 对应开放平台填写的值
    verification_token="your_verify_token",   # 对应开放平台填写的值
    host="0.0.0.0",
    port=7777,
    path="/webhook/event",
)
```

---

## 第六步：配置应用可见范围

默认情况下，机器人**只对应用的可见成员**可用。需要在开放平台设置：

1. 点击左侧菜单「**应用发布**」→「**版本管理与发布**」。
2. 或者点击「**权限管理**」→「**成员权限**」配置可见范围。

!!! info "截图占位"
    <!-- TODO: 上传截图 → 应用可见范围设置 -->
    ![可见范围](../assets/screenshots/larkbot/09_visibility.png){ loading=lazy }

!!! tip
    在企业内测阶段，可以将可见范围设为「全员」方便测试，发布后再收窄。

---

## 第七步：发布应用（可选）

完成测试后，提交应用审核以正式发布：

1. 点击「**应用发布**」→「**版本管理与发布**」。
2. 点击「**创建版本**」，填写更新日志。
3. 点击「**提交发布**」，等待企业管理员审批。

!!! info "截图占位"
    <!-- TODO: 上传截图 → 创建版本并提交发布 -->
    ![发布应用](../assets/screenshots/larkbot/10_publish.png){ loading=lazy }

---

## 环境变量速查

```bash
# 必填
FEISHU_APP_ID=cli_xxxxxxxxxxxxxxxx
FEISHU_APP_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# 可选（Webhook 模式才需要）
FEISHU_ENCRYPT_KEY=your_encrypt_key
FEISHU_VERIFICATION_TOKEN=your_verification_token

# 可选（国际版 Lark 使用）
FEISHU_API_BASE=https://open.larksuite.com
```

---

## 常见错误与排查

| 错误码 | 含义 | 解决方法 |
|--------|------|----------|
| `99991663` | 用户不在应用可见范围内 | 在「权限管理」→「成员权限」中添加该用户 |
| `99991672` / `230013` | 权限不足 | 在「权限管理」中申请对应 Scope |
| `99991401` | 无效的 Token | 检查 App ID / App Secret 是否正确 |
| `230002` | 机器人未激活 | 在「应用功能」→「机器人」中开启机器人 |
| `9499` | 事件订阅未配置 | 在「事件订阅」中添加并订阅事件 |

---

## 下一步

- [快速开始](quickstart.md) — 发出第一条消息
- [接收消息与路由](receiving.md) — 配置好后来这里写处理逻辑
