# Happy 调研：上游 `slopus/happy` 项目怎么工作，以及怎么自建 Happy server

这篇文章只讨论上游项目 **[`slopus/happy`](https://github.com/slopus/happy)** 本身。

重点有两件事：

1. Happy 这个项目到底解决什么问题
2. 如果你不想依赖官方托管服务，怎么自己部署 Happy server

## 1. Happy 是什么

上游 README 对 Happy 的定义很明确：

> Mobile and Web Client for Claude Code & Codex

它不是一个新的模型提供商，也不是一个 OpenAI-compatible relay。它的定位是：

- 把 Claude Code / Codex / Gemini 这类 coding agent 的会话接到手机、网页和另一台终端
- 让你可以远程观察、接管、恢复、通知这些会话
- 全程做端到端加密

换句话说，Happy 主要解决的是 **remote control / session sync**，不是模型 API 转发。

## 2. 上游项目的组成

从 `slopus/happy` 的 README 可以看出它是一个 monorepo，核心有四块：

- `happy-cli`
- `happy-app`
- `happy-agent`
- `happy-server`

它们分别承担不同角色：

- **happy-cli**：你本机上实际运行的 CLI wrapper
- **happy-app / web**：远端控制界面
- **happy-agent**：远程控制 CLI / agent 协议层
- **happy-server**：后端同步与认证服务

## 3. Happy CLI 是怎么工作的

从上游 `happy-cli` 的入口和 README，可以看出 Happy CLI 的典型使用是：

```bash
happy
happy claude
happy codex
happy gemini
```

它不是简单启动一个本地子进程就结束，而是围绕这几件事组织工作流：

- 启动本地 agent 会话
- 在本机建立 daemon
- 通过 Happy server 注册 machine / session
- 把状态同步到手机和 Web
- 在本地和远端之间切换控制权

所以 Happy 的关键能力不在 prompt，而在 **daemon + server + app + encryption** 这条链路。

## 4. Happy 自带的官方模式

Happy CLI 读取这些环境变量：

- `HAPPY_SERVER_URL`
- `HAPPY_WEBAPP_URL`
- `HAPPY_HOME_DIR`

如果你不设置它们，上游项目自己的默认值是：

- `HAPPY_SERVER_URL=https://api.cluster-fluster.com`
- `HAPPY_WEBAPP_URL=https://app.happy.engineering`
- `HAPPY_HOME_DIR=~/.happy`

这就是官方 hosted 模式。

对应的典型流程是：

```bash
npm install -g happy
happy auth login
happy claude
```

## 5. 自建时要部署什么

如果你要自建，不是只配一个 `base_url` 就够了。

Happy 自建的核心是：

- 你自己的 **happy-server**
- 你自己的 **webapp**（如果你要完整替代官方 web 入口）
- 客户端把 `HAPPY_SERVER_URL` / `HAPPY_WEBAPP_URL` 指向你的部署

这里最重要的是区分开：

- **Happy server**：远程控制与同步平面
- **模型 relay**：模型请求转发平面

它们不是同一个东西。

## 6. 上游 happy-server 的自建方式

这部分可以直接从上游 `packages/happy-server/README.md` 读出来。

上游已经给了一个很明确的自建路径：

### 6.1 Docker 单容器模式

Happy server 支持单容器运行，不依赖外部 Postgres / Redis / S3：

```bash
docker build -t happy-server -f Dockerfile .

docker run -p 3005:3005 \
  -e HANDY_MASTER_SECRET=<your-secret> \
  -v happy-data:/data \
  happy-server
```

这个模式下它使用：

- PGlite 作为嵌入式数据库
- 本地文件系统存上传文件
- 内存事件总线

所以如果你的目标是“先搭起来”，这已经是最小可行路径。

### 6.2 最关键的环境变量

根据上游 README，最少关注这些：

- `HANDY_MASTER_SECRET`：必需
- `PUBLIC_URL`
- `PORT`
- `DATA_DIR`
- `PGLITE_DIR`

如果你想换成外部基础设施，还可以再接：

- `DATABASE_URL`
- `REDIS_URL`
- `S3_HOST` 等对象存储配置

## 7. ChatTool 这里最适合做什么

基于上游 Happy 项目本身，ChatTool 最适合做的不是“假装自己也实现了 Happy server”，而是：

- 安装 Happy CLI
- 帮你保存 `HAPPY_SERVER_URL` / `HAPPY_WEBAPP_URL` / `HAPPY_HOME_DIR`
- 给出官方模式和自建模式的使用说明
- 把自建 server 的入口文档整理好

所以 `chattool setup happy` 最合理的边界应该是：

1. 安装 `happy`
2. 可选写入 Happy 自己的配置项
3. 引导你执行：

```bash
happy auth login
happy claude
```

或者如果你是自建：

```bash
chattool setup happy \
  --server-url https://happy.example/api \
  --webapp-url https://happy.example/app

happy auth login
```

## 8. 一句话总结

如果只从上游 `slopus/happy` 项目本身出发，最关键的认识是：

> Happy 解决的是 coding agent 的远程控制和加密同步问题；自建时，重点是部署 `happy-server` 并让 CLI 指向你自己的 server/webapp，而不是先把它和模型 relay 混成一个系统。
