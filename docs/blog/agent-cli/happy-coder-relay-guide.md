# Happy 官方 Quickstart：先跑通登录与远程控制，再决定要不要自建 server

这篇文章只基于上游项目 **[`slopus/happy`](https://github.com/slopus/happy)** 的公开资料来写，先讲官方 hosted 用法，再讲怎么自建 `happy-server`。

## 1. Happy 是拿来干什么的

上游 README 的定义很直接：

> Mobile and Web Client for Claude Code & Codex

你可以把它理解成：

- 本机继续跑 Claude Code / Codex / Gemini 这些 coding agent
- Happy 负责把这些会话同步到手机、网页和其他终端
- 通过二维码、Web、daemon 和加密同步，让你远程看、远程接管、远程恢复

如果只是第一次上手，先记住一句话：

> Happy 的官方体验是“在本机运行 agent，用手机或网页远程接管它”。

## 2. 第一步：安装 CLI

上游 README 目前写的是：

```bash
npm install -g happy
```

但按这台机器的实测，`npm install -g happy` 会装到一个同名错误包。当前可用的安装方式是：

```bash
npm install -g happy-coder
```

装完先确认命令是对的：

```bash
which happy
happy --help
```

如果是上游官方 Happy CLI，你应该至少能看到这些命令：

- `happy`
- `happy claude`
- `happy codex`
- `happy auth login`
- `happy auth status`
- `happy doctor`
- `happy daemon ...`

## 3. 第二步：先按官方 hosted 模式登录

第一次使用，不要先自建。直接走官方默认配置。

执行：

```bash
happy auth login
```

### 这一步在做什么

根据上游 `happy-cli` 的认证实现，这一步会：

1. 在本机生成密钥对
2. 向 Happy server 发起认证请求
3. 让你在手机或网页上确认授权
4. 把认证结果、机器信息和密钥材料保存到 `~/.happy`

所以这一步不是填 GitHub token，也不是模型 API key，而是 Happy 自己的登录。

## 4. 第三步：启动会话

### 4.1 Claude Code（默认）

官方推荐直接这样用：

```bash
happy
# 或
happy claude
```

运行后，官方 README 说它会：

1. 启动 Claude Code 会话
2. 显示二维码，供手机连接
3. 建立端到端加密的远程控制通道
4. 在电脑在线时，让你能从手机或网页直接继续控制这个会话

### 4.2 Codex

如果你平时用 Codex：

```bash
happy codex
```

### 4.3 Gemini / 其它 agent

上游 README 里还列了：

```bash
happy gemini
happy openclaw

# 或任意 ACP-compatible agent
happy acp opencode
happy acp -- custom-agent --flag
```

## 5. 第四步：检查状态

如果你觉得登录、daemon 或会话状态不对，官方第一步应该是：

```bash
happy doctor
```

从上游 `doctor` 的输出逻辑看，它会帮助你检查：

- `HAPPY_HOME_DIR`
- `HAPPY_SERVER_URL`
- 本地配置目录
- 认证状态
- daemon 是否在运行
- settings / logs / daemon state

如果只是想看认证本身是否存在，也可以跑：

```bash
happy auth status
```

## 6. daemon 要不要手动管

Happy 有 daemon，但多数时候你不需要自己先启动。

上游 README 里明确写了：

> The daemon starts automatically when you run `happy`

如果你确实想手动管它，再用：

```bash
happy daemon start
happy daemon stop
happy daemon status
happy daemon list
```

## 7. 一个最短的官方上手流程

### Claude 用户

```bash
npm install -g happy-coder
happy auth login
happy
```

### Codex 用户

```bash
npm install -g happy-coder
happy auth login
happy codex
```

### 诊断问题

```bash
happy doctor
happy auth status
```

## 8. 什么时候再考虑自建 server

如果你只是想先用 Happy，根本不需要一开始就自建。

上游 `happy-server` README 甚至明确写了：

> You don't need to self-host!

所以正确顺序应该是：

1. 先跑通官方 hosted 模式
2. 确认 `happy auth login`、`happy` / `happy codex`、`happy doctor` 都工作正常
3. 再决定要不要自建 `happy-server`

## 9. 自建 `happy-server` 的最小 Docker 路径

如果你确定要自己托管，再看这一步。

根据上游 `packages/happy-server/README.md`，最小 Docker 路径是：

```bash
docker build -t happy-server -f Dockerfile .

docker run -p 3005:3005 \
  -e HANDY_MASTER_SECRET=<your-secret> \
  -v happy-data:/data \
  happy-server
```

这条路径的特点是：

- 单容器
- 无需额外 Postgres / Redis / S3
- 使用嵌入式 PGlite 和本地文件系统

如果你只是想“先自己跑起来”，这就是上游给出的最小起点。

## 10. 自建后，CLI 怎么切过去

Happy CLI 自己就支持：

- `HAPPY_SERVER_URL`
- `HAPPY_WEBAPP_URL`

所以你要做的是把 CLI 指向你的部署：

```bash
export HAPPY_SERVER_URL=https://happy.example/api
export HAPPY_WEBAPP_URL=https://happy.example/app
happy auth login
```

如果你想把这些变量交给 ChatTool 管理，再用：

```bash
chattool setup happy --server-url https://happy.example/api --webapp-url https://happy.example/app
chatenv cat -t happy
```

这一步只是保存 Happy 自己的配置，不会替你部署 server。

## 11. 最后一句

如果你现在只是要“把 Happy 用起来”，最值得照着做的其实只有这三步：

```bash
npm install -g happy-coder
happy auth login
happy
```

先把官方 hosted 模式跑通，再去碰自建 server。这样最不容易走偏。
