# Happy 官方用法速查：怎么登录、怎么启动、怎么看状态，以及什么时候需要自建 server

这篇文章只基于上游项目 **[`slopus/happy`](https://github.com/slopus/happy)** 的公开资料来写，不夹带别的体系。

先讲清楚官方用法，再讲自建 `happy-server`。

## 1. Happy 是什么

上游 README 的定义是：

> Mobile and Web Client for Claude Code & Codex

Happy 不是一个新的模型提供商，也不是 OpenAI-compatible relay。它主要解决的是：

- 让你从手机、网页或另一台终端远程观察和接管 coding agent
- 在本地 agent 与远端界面之间做会话同步
- 所有会话内容在离开设备前就完成端到端加密

你可以把它理解成：

- 本地跑 agent：Claude Code / Codex / Gemini / 其它 ACP-compatible agent
- Happy 负责 remote control + sync + auth + daemon

## 2. 先装什么

上游文档给出的安装方式很直接：

```bash
npm install -g happy
```

安装后先确认命令是对的：

```bash
which happy
happy --help
```

如果是官方 Happy CLI，你应该至少能看到这些命令：

- `happy`
- `happy claude`
- `happy codex`
- `happy auth login`
- `happy daemon ...`
- `happy doctor`

## 3. 官方用法：先用 hosted 模式跑通

官方 hosted 模式下，不需要先自建 server。Happy CLI 自己有默认值：

- `HAPPY_SERVER_URL=https://api.cluster-fluster.com`
- `HAPPY_WEBAPP_URL=https://app.happy.engineering`
- `HAPPY_HOME_DIR=~/.happy`

所以第一步最推荐的流程是：

```bash
happy auth login
```

### 这一步在做什么

根据上游 `happy-cli` 的 auth 实现，它会：

1. 生成本地密钥对
2. 向 Happy server 发起认证请求
3. 通过手机或网页完成授权
4. 把凭据和本地 machine 信息保存到 `~/.happy`

也就是说，Happy 不是拿 GitHub token 直接登录，而是走它自己的认证体系。

## 4. 登录后怎么用

### 4.1 Claude Code（默认）

上游 README 里给的默认用法是：

```bash
happy
# 或
happy claude
```

这会：

1. 启动 Claude Code 会话
2. 显示二维码或提供网页连接入口
3. 允许你从手机/网页远程查看和控制当前会话

### 4.2 Codex

```bash
happy codex
```

### 4.3 Gemini / 其它 agent

上游 README 也写了：

```bash
happy gemini
happy openclaw

# 或任意 ACP-compatible CLI
happy acp opencode
happy acp -- custom-agent --flag
```

## 5. daemon 是做什么的

Happy 不是一个“开完终端就算了”的 wrapper。它有 daemon。

上游文档说明 daemon 的作用是：

- 常驻本机
- 管理后台会话
- 接收远端请求
- 让你在没有打开终端窗口时，也能从手机/网页启动或恢复 session

常用命令：

```bash
happy daemon start
happy daemon stop
happy daemon status
happy daemon list
```

不过上游也明确说了：

> The daemon starts automatically when you run `happy`

所以多数情况下你不需要先手动起 daemon。

## 6. `happy doctor` 能看什么

如果你觉得状态不对，先跑：

```bash
happy doctor
```

从上游 `doctor` 输出逻辑看，它至少会显示：

- `HAPPY_HOME_DIR`
- `HAPPY_SERVER_URL`
- 本地配置目录
- 认证状态
- daemon 状态
- settings / logs / daemon state 信息

所以 Happy 的官方排查第一步，应该就是 `happy doctor`，而不是直接猜。

## 7. 常见的官方流程

如果只用官方 hosted 服务，最短路径就是：

```bash
npm install -g happy
happy auth login
happy
```

如果你是 Codex 用户：

```bash
npm install -g happy
happy auth login
happy codex
```

如果你想看诊断：

```bash
happy doctor
```

如果你想看认证状态：

```bash
happy auth status
```

## 8. 什么时候才需要自建 server

如果你只是想先用 Happy，根本不需要一开始就自建。

上游 `happy-server` README 也明确说了：

> You don't need to self-host!

所以自建通常是出于这些原因：

- 你不想依赖官方 hosted 服务
- 你想完全掌控 server 部署与数据位置
- 你想把 Happy 接到自己的域名和基础设施

## 9. 自建 `happy-server` 的最小路径

上游 `packages/happy-server/README.md` 给了一个最小 Docker 路径。

在上游 Happy monorepo 根目录里：

```bash
docker build -t happy-server -f Dockerfile .

docker run -p 3005:3005 \
  -e HANDY_MASTER_SECRET=<your-secret> \
  -v happy-data:/data \
  happy-server
```

这个模式下：

- 使用嵌入式 PGlite
- 使用本地文件系统
- 不需要额外 Postgres / Redis / S3

对于“先搭起来看看”来说，这是最轻的一条路。

## 10. 自建后，CLI 怎么指向你的 server

Happy CLI 本身就支持：

- `HAPPY_SERVER_URL`
- `HAPPY_WEBAPP_URL`

所以自建后，你要做的是让 CLI 指向自己的部署：

```bash
export HAPPY_SERVER_URL=https://happy.example/api
export HAPPY_WEBAPP_URL=https://happy.example/app
happy auth login
```

如果你想把这些变量保存下来，再用 ChatTool 去管理，就可以用：

```bash
chattool setup happy --server-url https://happy.example/api --webapp-url https://happy.example/app
chatenv cat -t happy
```

这里 ChatTool 做的只是：

- 安装 `happy`
- 保存 Happy 自己的配置项

它不负责实现 Happy server 本身。

## 11. 最后一句

如果你只是第一次接触 Happy，正确顺序应该是：

1. 先按官方 hosted 模式跑通
2. 用 `happy doctor` 看清本机状态
3. 再决定要不要自建 `happy-server`

不要一开始就把“官方用法、模型 relay、自建 server、ChatTool 集成”混在一起。先把官方链路跑通，后面的判断才有依据。
