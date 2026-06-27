# ChatTool 客户端命令行工具文档

ChatTool 提供了两个主要的命令行工具：`chattool` 用于各种服务管理，`chatenv` 用于环境配置管理。

## 命令结构

### chattool

CLI按功能分为几个命令组：

- **`serve`**: 本地服务器实用工具（例如，请求捕获）。
- **`client`**: 远程服务客户端工具。
- **`mcp`**: 模型上下文协议 (MCP) 服务器管理。
- **`lark`**: 保留的飞书最小调试命令（`info` / `send` / `chat`）。
- **`kb`**: 知识库 (Knowledge Base) 管理工具。
- **`zulip`**: Zulip 社区阅读与资讯汇总工具（仅只读）。
- **`setup`**: 环境初始化与依赖安装（Node.js / zsh / cc-connect / Codex / Claude / OpenCode / lark-cli / Docker / Chrome / FRP）。
- **`cc`**: cc-connect 的初始化、启动、日志与诊断工具。

DNS 记录管理和动态 DNS (DDNS) 已迁移到独立 `ChatDNS` / `chatdns` CLI；ChatTool 不再暴露 `chattool dns`。

### chatenv

独立的配置和环境变量管理工具：

- **`init`**: 初始化配置。
- **`set/get/unset`**: 管理单个配置项。
- **`list`**: 管理多环境配置。
- **`cat`**: 查看配置内容。

---

## 0. 环境初始化 (`setup`)

### 0.0 CC-Connect (`setup cc-connect`)

安装或检查 `cc-connect` CLI，并在需要时先补齐 `Node.js >= 20` 与 `npm`：

```bash
chatup cc-connect
```

如需看更详细的阶段日志，可附加：

```bash
chatup cc-connect --log-level DEBUG
```

如果你更习惯从 `cc` 分组进入，也可以继续使用别名：

```bash
chatup cc-connect
```

生成最小可用配置时，如需默认隐藏思考和工具进度中间消息，可直接写入项目级 quiet 配置：

```bash
chattool cc init -i --quiet
chattool cc start --max-failures 5
```

### 0.1 Codex (`setup codex`)

默认交互输入密钥（会读取已有配置并以 mask 形式展示）：

```bash
chatup codex
```

如需更详细地查看依赖检测、npm 安装和配置写入阶段，可附加：

```bash
chatup codex --log-level DEBUG
```

命令会先检查本机是否已有 `Node.js >= 20` 和 `npm`。如果当前终端可交互且依赖不满足，会先提示是否执行 `chatup nodejs` 进行安装或升级。

直接传 API key：

```bash
chatup codex --api-key "sk-xxx"
```

如果你已经在 `chatenv` 里维护了 `oai/openai` 配置，也可以显式复用：

```bash
chatup codex -e work
chatup codex -e ~/.chatarch/envs/OpenAI/work.env
```

这里的 `-e/--env` 支持两种形式：

- `.env` 文件路径
- `OpenAI` 类型下保存过的 profile 名称，例如 `work`

解析顺序为：

1. 显式参数：`--api-key`、`--base-url`、`--model`
2. `-e/--env` 指定的 OpenAI 配置
3. 现有 `~/.codex/` 配置
4. 当前 shell 的系统环境变量
5. `envs/OpenAI/.env` 的 typed 默认值
6. 内置默认值

可选覆盖 `base_url` 和默认模型：

```bash
chatup codex --api-key "sk-xxx" --base-url "https://example.com/openai" --model "gpt-5.4"
```

### 0.2 Claude Code (`setup claude`)

默认交互输入密钥（会读取已有配置并以 mask 形式展示）：

```bash
chatup claude
```

如需查看更详细的安装和写入日志，可附加：

```bash
chatup claude --log-level DEBUG
```

命令同样会先检查本机是否已有 `Node.js >= 20` 和 `npm`；不满足时会优先提示安装/升级，再继续收集 Claude Code 配置。

直接传参：

```bash
chatup claude --auth-token "sk-ant-xxx"
```

可选覆盖 `ANTHROPIC_BASE_URL` 和 `ANTHROPIC_SMALL_FAST_MODEL`：

```bash
chatup claude --auth-token "sk-ant-xxx" --base-url "https://example.com/anthropic" --small-fast-model "claude-opus-4-6"
```

### 0.3 OpenCode (`setup opencode`)

默认交互输入配置项（会读取已有配置并以 mask 形式展示）：

```bash
chatup opencode
```

如需更详细的依赖检查和配置写入日志，可附加：

```bash
chatup opencode --log-level DEBUG
```

命令会先检查本机是否已有 `Node.js >= 20` 和 `npm`；不满足时会优先提示安装/升级，再继续进入 OpenCode 的配置流程。

直接传参：

```bash
chatup opencode --base-url "https://example.com/openai" --api-key "sk-xxx" --model "gpt-4.1-mini"
```

也可以显式复用 `chatenv` 里的 OpenAI 配置：

```bash
chatup opencode -e work
chatup opencode -e ~/.chatarch/envs/OpenAI/work.env
chatup opencode -e work --plugin auto-loop
```

解析顺序为：

1. 显式参数：`--base-url`、`--api-key`、`--model`
2. `-e/--env` 指定的 OpenAI 配置
3. 现有 `~/.config/opencode/opencode.json` 配置
4. 当前 shell 的系统环境变量
5. `envs/OpenAI/.env` 的 typed 默认值
6. 默认值

如果你希望顺手把 `opencode-auto-loop` 写入 OpenCode 配置，也可以显式加上：

```bash
chatup opencode --plugin auto-loop
```

### 0.4 Lark CLI (`setup lark-cli`)

安装官方 `lark-cli`，并把 ChatTool 当前保存的 Feishu 配置复用过去：

```bash
chatup lark-cli
```

如需更详细地查看 Node.js 检查、npm 安装和 `lark-cli` 初始化阶段，可附加：

```bash
chatup lark-cli --log-level DEBUG
```

命令会先检查本机是否已有 `Node.js >= 20` 和 `npm`；不满足时会优先提示安装/升级，再继续进入 `lark-cli` 的配置流程。

如果你已经在 `chatenv` 里维护了 `feishu/lark` 配置，也可以显式复用：

```bash
chatup lark-cli -e work
chatup lark-cli -e ~/.chatarch/envs/Feishu/work.env
```

这里的 `-e/--env` 支持两种形式：

- `.env` 文件路径
- `Feishu` 类型下保存过的 profile 名称，例如 `work`

解析顺序为：

1. 显式参数：`--app-id`、`--app-secret`、`--brand`
2. `-e/--env` 指定的 Feishu 配置
3. 当前保存的 `feishu/lark` typed env 配置
4. shell 环境变量
5. 现有 `~/.lark-cli/config.json` 中的 app 元信息
6. 默认品牌值 `feishu`

默认情况下，官方 `lark-cli` 配置写到 `~/.lark-cli/config.json`；若设置了 `LARKSUITE_CLI_CONFIG_DIR`，则改写到该目录下的 `config.json`。

执行完成后，下一步再运行：

```bash
lark-cli auth login --recommend
```

### 0.5 Docker (`setup docker`)

检查 Docker、Docker Compose 和当前用户的 docker 组状态：

```bash
chatup docker
```

如需更详细地查看环境检查分支和建议命令判断，可附加：

```bash
chatup docker --log-level DEBUG
```

默认只打印建议命令，不会直接执行 `sudo`。如需允许命令在确认后直接执行，显式传入：

```bash
chatup docker --sudo -i
```

### 0.6 Hermes (`setup hermes`)

安装或检查 ChatArch Hermes Agent，并在需要时配置基础 OpenAI-compatible 参数。该命令封装 ChatArch Hermes `install.sh`；默认使用本地缓存或随包 installer，不主动访问 GitHub 更新，也不安装 Hermes WebUI。

```bash
chatup hermes
chatup hermes -e apple --model openai/gpt-5.4-mini
chatup hermes --installer /path/to/install.sh
chatup hermes --with-webui-env --webui-dir ./hermes-webui --start-webui
```

常用参数：

- `--installer`：使用本地 ChatArch Hermes `install.sh`。
- `--update-installer`：从 ChatArch Hermes URL 更新 ChatTool 缓存里的 installer。
- `--hermes-home`：指定 Hermes home，默认 `~/.hermes`。
- `-e/--env`：OpenAI 配置来源，支持 `.env` 文件路径或保存的 OpenAI profile 名。
- `--api-key` / `--base-url` / `--model`：显式写入 Hermes 基础模型配置。
- `--feishu-env`：显式导入 Feishu 配置；不传时不会自动导入 Feishu。
- `--install-only`：只安装/检查 Hermes，不写入 `.env`、`config.yaml` 或 WebUI env。
- `--with-webui-env`：生成 WebUI env；如果没有 WebUI app files，会提示提供 `--webui-dir`。
- `--start-webui`：使用已有 WebUI 目录的原生入口启动，优先 `./ctl.sh start`，否则 `./start.sh` 或 `python3 bootstrap.py`。

重复运行时只更新本次命令管理的 key，不重写整份 `.env` 或 `config.yaml`。

### 0.7 Zsh (`setup zsh`)

参考 QuickSetup-Ubuntu 的 zsh 初始化方式，配置 `zsh`、oh-my-zsh、常用插件、powerlevel10k 主题以及 `~/.zsh_aliases`：

```bash
chatup zsh
chatup zsh --no-omz
chatup zsh -i
```

默认行为：

- 按 QuickSetup 脚本顺序检查本机是否存在 `git` 与 `zsh`；如果缺失，直接退出并提示 `sudo apt install git -y` 或 `sudo apt install zsh -y`，不代替用户执行安装。
- 安装或复用 `~/.oh-my-zsh`，并默认全选脚本同款插件：`git`、`sudo`、`z`、`zsh-syntax-highlighting`、`zsh-autosuggestions`、`zsh-completions`；传 `-i` 时会用候选框选择插件，方便后续扩展更多插件。
- 将 QuickSetup 当前 `scripts/config/zsh_aliases` 风格完整常用 alias 与 ChatTool alias 写入 `~/.zsh_aliases` 的 managed block。
- 在 `~/.zshrc` 中写入 managed source block：如果 `~/.zsh_aliases` 存在则自动加载。
- 默认在 `~/.bash_profile` 写入 managed handoff，复用 QuickSetup 的 `exec $(which zsh) -l` 思路；不需要该行为可传 `--no-login-shell`。

常用参数：

- `-i`：进入交互模式，先用 checkbox 展示基础配置项（oh-my-zsh、aliases、login shell，按当前默认值预勾选），若启用 oh-my-zsh 再进入插件 checkbox（默认全选脚本同款插件）；不传 `-i` 时基础参数都走默认值，不自动进入交互。
- `--no-omz`：只配置 alias 和 zsh login handoff，不安装或修改 oh-my-zsh。
- `--no-aliases`：只配置 zsh/oh-my-zsh，不写 alias。
- `--no-login-shell`：不写入 `~/.bash_profile` handoff。
- `--log-level DEBUG`：查看更详细的阶段日志。

完成后可以运行：

```bash
source ~/.zshrc
```

### 0.8 Workspace (`setup workspace`)

如果你已经有自己的核心项目，只想在项目外围加一层“人类-AI 协作协议 + 多任务并发面 + 知识沉淀”工作区，可以用：

```bash
chatup workspace
chatup workspace ~/workspace/demo
chatup workspace ~/workspace/demo --language en
```

它会生成一套独立骨架，包括：

- `AGENTS.md`：模型主协议
- `TODO.md`：workspace 近期计划
- `ARCHIVE.md`：归档操作指南，说明如何筛选、移动、审查和记录归档内容
- `.trash/`：workspace 级软删除缓冲区
- `projects/`：所有实际工作的执行容器
- `archive/`：归档后的历史 project
- `archive/index.md`：已归档内容索引，记录已经归档了哪些 project
- `core/`：源码仓库目录
- `scripts/`：workspace 级维护脚本目录
- `skills/`：共享 skills 目录
- `public/`：公开网站和发布目录

默认模板语言是中文；如果你要英文版协议和 onboarding 文件，可以显式传 `--language en`。

如果目标目录已经是一个已有 workspace，`setup workspace` 会优先保留现有 `AGENTS.md` 或历史遗留的 `MEMORY.md`，同时补齐当前结构目录。

如果只想先看计划不落盘：

```bash
chatup workspace ~/workspace/demo --dry-run -I
```

交互模式下还可以额外勾选模块，例如：

- `ChatTool`：下载到 `core/ChatTool/`，并把相关 skills 同步到 `./skills/`
- `ChatBlog` / `--with-chatblog`：下载到 `core/ChatBlog/`，并把 `source/_posts` 链接到 `./public/chatblog`
- `ChatMemory` / `--with-memory`：下载到 `core/ChatMemory/`，只把共享 skill groups 链接到 workspace：`./skills/chatarch`、`./skills/common`、`./skills/agents`，并创建本地非共享目录 `./skills/local`

也可以在非交互模式中显式启用：

```bash
chatup workspace ~/workspace/demo --with-chatblog --with-memory -I
```

ChatMemory 不会默认 link 全部 `Skills/`，也不会默认 link 机器/账号特定分组。`skills/local` 是当前 workspace / 当前机器本地使用的非共享目录，不从 ChatMemory link。

## 1. DNS 管理（已迁移到 ChatDNS）

DNS 记录管理、DDNS 和 IP 探测已经从 ChatTool parent 分离到独立包 `ChatDNS`。ChatTool 不再暴露 nested `chattool dns` 命令；请使用一等 CLI：

```bash
chatdns --help
chatdns list
chatdns records example.com
chatdns records test.example.com
chatdns set test.example.com -v 1.2.3.4
chatdns delete test.example.com -t A --yes
chatdns ip
chatdns ddns public.example.com --monitor
```

通过 ChatTool 安装依赖时可使用：

```bash
pip install "chattool[dns]"
```

`chattool dns cert` 旧 nested 入口已移除；本地 DNS-01 证书申请/检查由 `ChatDNS>=0.1.1` 的一等 CLI `chatdns cert apply/check` 维护。ChatTool 仅保留 `chattool serve cert` / `chattool client cert` 远程服务入口。

---

## 2. 远程客户端工具 (`client`)

### 2.1 SSL 证书客户端 (`client cert`)

用于与 `chattool serve cert` 服务交互的客户端工具，支持申请、查询和下载证书。

**全局选项:**
- `--server`: 服务地址 (默认: `http://127.0.0.1:8000`)
- `--token`: 鉴权 Token (也可通过 `CHATTOOL_CERT_TOKEN` 环境变量设置)

#### 申请证书 (`apply`)
```bash
chattool client cert apply -d example.com -d *.example.com --token my-secret-token
chattool client cert apply
```
**选项:**
- `-d, --domain`: 域名列表。缺少时会在交互终端里自动补问。
- `-e, --email`: 邮箱。默认优先尝试 `git config user.email`，缺少时会自动补问。
- `-p, --provider`: DNS 提供商 (可选)。
- `--secret-id/--secret-key`: 云厂商凭证 (可选)。

#### 查看证书列表 (`list`)
```bash
chattool client cert list --token my-secret-token
```
列出当前 Token 下申请的所有证书及其有效期信息。

#### 下载证书 (`download`)
```bash
chattool client cert download example.com -o ./my-certs --token my-secret-token
chattool client cert download
```
下载指定域名的证书文件 (`cert.pem`, `privkey.pem`, `fullchain.pem`) 到本地目录。

在交互终端里，`download` 缺少 domain 时会自动补问；显式传 `-I` 时保持直接报错。

---

## 3. 网络工具 (`chatnet`)

网络扫描、端口扫描、链接检查和 service URL 检查已从 ChatTool parent 迁出到独立 `ChatNet` / `chatnet`。ChatTool 不再提供 `chattool network` 子命令，也不在 MCP 中保留 Network 兼容工具。

```bash
# 随 ChatArch 聚合工具安装
pip install 'chattool[arch]'

# 或单独安装/升级
pip install 'ChatNet>=0.2.0,<0.3.0'

# 使用独立 CLI
chatnet --help
chatnet ping --network 192.168.1.0/24
chatnet ssh --network 192.168.1.0/24 --port 22
chatnet links --url https://example.com
```

---

## 4. GitHub 工具 (`chatgh`)

GitHub PR、CI、Actions 和 repo credential 工具已迁移到独立包 `chatgh`。ChatTool 不再内置 GitHub 子命令代码或 typed env schema，但会通过 package dependency 安装 `chatgh>=0.2.4`，因此安装 ChatTool 后可直接使用独立 `chatgh` 命令；也可单独升级：

```bash
pip install "chatgh>=0.2.4" --upgrade
```

### 4.1 配置
`chatgh` 默认行为：

- `repo`：优先从当前 git remote 推断
- `token`：优先从当前仓库对应的 git credential 读取，再回退 `GITHUB_ACCESS_TOKEN`
- ChatTool 不再提供 `chattool gh` 入口，也不再注册 `gh` typed env schema

### 4.2 常用任务

ChatTool 不再维护 GitHub 子命令的旧实现或 deprecated 兼容层；新增/修复 GitHub 能力时，请直接在独立 `chatgh` 仓库中推进。ChatTool 这里只保留迁移入口和常见任务示例：

```bash
# 查看或配置 ChatGH 使用的 typed env
chatenv cat -t gh
export GITHUB_ACCESS_TOKEN="***"

# PR / CI / Actions 任务
chatgh pr list --state open --limit 20
chatgh pr view 123
chatgh pr checks 123
chatgh run view --run-id 23494900414
chatgh run logs --job-id 68373094563

# repo credential / permission 任务
chatgh set-token --token github_pat_xxx
chatgh set-token --token github_pat_xxx --save-env
chatgh repo-perms --repo owner/repo --token github_pat_xxx
```

`chatgh` 的 token 解析顺序保持为：

1. 显式 `--token`。
2. 当前仓库对应的 repo-scoped git credential，路径按 `owner/repo` 规范化。
3. `chatenv gh` / ChatEnv 中的默认 `GITHUB_ACCESS_TOKEN`。

这个顺序让仓库级 token 可以优先隔离权限；没有 repo-scoped credential 时，再回退到默认 GitHub token。当前 ChatTool 不再注册 `GITHUB_ACCESS_TOKEN` schema，相关配置由 ChatGH / ChatEnv 负责。

如果只是 clone / fetch / push 某个仓库，通常至少需要 contents 读写权限；PR 评论、合并、Actions 读取等任务再按仓库策略补充对应权限。需要机器可读结果时，优先使用 ChatGH 命令的 `--json-output`。

后续 repo 发现、status、checkout 等能力也应作为 ChatGH 的任务导向能力推进，而不是重新放回 ChatTool。

### 4.3 API Reference

后续扩展 `chatgh` 时，优先查这些官方文档：

- GitHub REST API 根文档: https://docs.github.com/en/rest
- Pull requests API: https://docs.github.com/en/rest/pulls/pulls
- Check runs API: https://docs.github.com/en/rest/checks/runs
- Workflow runs API: https://docs.github.com/en/rest/actions/workflow-runs
- Workflow jobs API: https://docs.github.com/en/rest/actions/workflow-jobs
- Commit statuses API: https://docs.github.com/en/rest/commits/statuses

---

## 5. Zulip 工具 (`zulip`)

用于读取 Zulip 社区消息并生成资讯摘要（**只读**，不提供发送接口以避免误发）。

### 5.1 配置

使用 `chatenv` 查看或配置：

```bash
chatenv cat -t zulip
```

常用配置项：
- `ZULIP_BOT_EMAIL`
- `ZULIP_BOT_API_KEY`
- `ZULIP_SITE`
- `ZULIP_NEWS_STREAMS` (逗号分隔的默认 streams)
- `ZULIP_NEWS_TOPICS` (逗号分隔的默认 topics)
- `ZULIP_NEWS_SINCE_HOURS` (默认 24)
- `ZULIP_NEWS_PER_STREAM` (默认 200)

### 5.2 常用命令

```bash
# 列出订阅的 streams
chattool zulip streams

# 缺少 stream/topic 时自动补问
chattool zulip topics
chattool zulip topic

# 查看消息（支持过滤）
chattool zulip messages --stream general --before 20

# 生成资讯摘要（控制台 + Markdown 文件）
chattool zulip news --since-hours 24 --stream general --stream announcements
```

默认输出文件：`zulip-news-YYYYMMDD.md`（当前目录），可用 `--output` 覆盖。

在交互终端里，`topics` / `topic` 缺少关键参数时会自动补问；显式传 `-I` 时保持直接报错。

---

## 6. 环境管理 (`env`)

管理存储在 `.env` 文件中的全局配置和环境变量。

```bash
# 交互式初始化或更新配置
chatenv init -i

# 列出所有配置
chatenv list

# 设置配置值
chatenv set CHATTOOL_DNS_PROVIDER=tencent

# 获取配置值
chatenv get CHATTOOL_DNS_PROVIDER

# 删除配置值
chatenv unset CHATTOOL_DNS_PROVIDER

# 粘贴导入从 chatenv cat --no-mask 复制来的配置
chatenv paste
chatenv paste --stdin --yes < openai.env
chatenv paste --stdin --profile work --yes < openai.env

# 缺少 key / profile 名时自动补问
chatenv save -t gh
chatenv use -t gh
chatenv delete -t gh
chatenv get
chatenv set
chatenv unset
```

**命令详解:**
- `init`: 初始化或更新配置文件。使用 `-i, --interactive` 进入交互模式。
- `list`: 列出所有当前生效的配置值。
- `set`: 设置单个配置项，格式为 `KEY=VALUE`。
- `get`: 获取单个配置项的值。
- `unset`: 删除（置空）单个配置项的值。
- `paste`: 粘贴导入 `KEY='VALUE'` / `.env` / `export KEY=VALUE` 文本，识别已注册 key 后按类型写入 active `.env`；传 `--profile NAME` 或在交互中输入 profile name 时，写入各命中类型的同名 profile。

在交互终端里，`save/use/delete/get/set/unset/test` 缺少关键参数时都会自动补问，显式传 `-I` 才禁用交互并直接报错；`paste` 会读取粘贴内容、询问可选 profile name，并在写入前展示概要确认，非交互导入请配合 `--stdin` / `--value` 与 `--yes`。

---

## 6. 本地服务器工具 (`serve`)

### 4.1 请求捕获 (`capture`)

启动一个本地 HTTP 服务器，捕获并记录所有传入的请求。常用于调试 Webhook 或检查 API 调用。

```bash
# 在默认端口 (8000) 启动捕获服务器
chattool serve capture

# 后台运行并启用自动重载
chattool serve capture --host 0.0.0.0 --port 8080 --daemon --reload
```

**服务器功能:**
- 详细记录请求头 (Headers)、查询参数 (Query Params) 和请求体 (Body)。
- 自动生成用于复现请求的 `curl` 命令。
- 在 `/docs` 提供 Web 文档界面。

**选项说明:**
- `--host`: 监听地址 (默认: `0.0.0.0`)。
- `--port`: 监听端口 (默认: `8000`)。
- `-d, --daemon`: 后台运行模式（使用线程）。
- `--reload`: 启用自动重载（开发模式）。

### 4.2 SSL 证书服务 (`cert`)

启动一个 REST API 服务，提供 SSL 证书的异步申请和安全下载功能。支持多租户隔离，使用 Token 进行鉴权和数据隔离。

```bash
# 启动服务，监听 8000 端口，证书存储在 ./certs
chattool serve cert --provider aliyun

# 指定监听地址、端口和输出目录
chattool serve cert --host 0.0.0.0 --port 8080 --output ./my-certs
```

**核心特性:**
- **Token 隔离**: 使用请求 Header 中的 Token 的哈希值作为子目录名，实现多租户物理隔离。不同 Token 无法访问彼此的数据。
- **异步申请**: 提交申请后立即返回，后台执行 ACME 验证流程。
- **元数据管理**: 自动记录证书的生成时间、过期时间和剩余天数，支持列表查询。

**API 接口 (需在 Header 中携带 `X-ChatTool-Token`):**

1.  **申请证书**: `POST /cert/apply`
    *   Body:
        ```json
        {
          "domains": ["example.com", "*.example.com"],
          "email": "admin@example.com",
          "provider": "aliyun",
          "secret_id": "...",
          "secret_key": "..."
        }
        ```
    *   Response: `{"status": "pending", "message": "..."}`

2.  **获取证书列表**: `GET /cert/list`
    *   返回该 Token 下所有已生成的证书信息（包含有效期、路径等）。
    *   Response:
        ```json
        [
          {
            "domain": "example.com",
            "created_at": "2023-10-27T10:00:00",
            "expires_at": "2024-01-25T10:00:00",
            "days_remaining": 89,
            "cert_path": "example.com/cert.pem",
            ...
          }
        ]
        ```

3.  **下载证书**: `GET /cert/download/{domain}/{filename}`
    *   `domain`: 主域名 (如 `example.com`)
    *   `filename`: 文件名 (如 `fullchain.pem`)

**选项说明:**
- `--host`: 监听地址 (默认: `0.0.0.0`)。
- `-p, --port`: 监听端口 (默认: `8000`)。
- `-o, --output`: 证书存储根目录 (默认: `certs`)。
- `--provider`: 默认 DNS 提供商 (`aliyun` 或 `tencent`)。
- `--secret-id`: 默认云厂商 Secret ID (可选)。
- `--secret-key`: 默认云厂商 Secret Key (可选)。

---

## 7. Skill 管理 (`skill`)

用于安装和管理 ChatTool skills（默认从项目 `skills/` 目录读取）。

```bash
# 列出可用 skills
chattool skill list

# 安装单个 skill 到 Codex
chattool skill install cert-manager -p codex

# 安装到 Claude（可显式指定目标目录）
chattool skill install cert-manager -p claude -d ~/.claude/skills

# 安装到 OpenCode
chattool skill install cert-manager -p opencode

# 安装全部 skills
chattool skill install -a -p codex

# 安装时添加 chattool- 前缀
chattool skill install cert-manager -p codex --prefix
```

**选项说明 (`install`):**
- `-p/--platform`: 目标平台（`codex` / `claude` / `opencode`）。
- `-s/--source`: Skills 源目录（默认自动定位项目的 `skills/`）。
- `-d/--dest`: 目标目录（可覆盖平台默认目录）。
- `--prefix`: 安装时为 skill 名称添加 `chattool-` 前缀（默认不加）。
- `-f/--force`: 覆盖已存在的 skill（未指定时会提示是否覆盖，输入 `a` 可允许后续全部覆盖）。

交互模式下：
- 省略 `-p` 时会先进入平台选择页
- 省略 skill 名时会进入 skills 多选页
- 多选页顶部提供一个可联动的“全选”项；在它上面按空格可切换全选/清空

安装前会校验源 skill 的 `SKILL.md`。当前要求：
- 文件开头必须包含 `---` 包裹的 YAML frontmatter
- frontmatter 至少包含 `name`、`description`
- `version` 可以保留为可选元信息，但安装时不会强制校验
- `openai.yaml`/`openai.yml` 不是必需文件

---

## 8. MCP 服务器 (`mcp`)

管理 ChatTool 模型上下文协议 (MCP) 服务器。

```bash
# 运行 MCP 服务器 (标准输入输出模式，默认)
chattool mcp start

# 运行 MCP 服务器 (HTTP 模式)
chattool mcp start --transport http --port 8000

# 查看服务器能力信息
chattool mcp info

# 兼容旧命令
chattool mcp inspect

# JSON 输出（便于自动化）
chattool mcp info --json-output
```

**选项说明 (`start`):**
- `-t, --transport`: 传输模式，可选 `stdio` (默认) 或 `http`。
- `--host`: HTTP 服务器主机地址 (默认: `127.0.0.1`)。
- `--port`: HTTP 服务器端口 (默认: `8000`)。

**其他子命令:**
- `info` / `inspect`: 查看 MCP 工具清单，支持 `--json-output`。

---

## 9. 知识库管理 (`kb`)

管理基于 Zulip 的知识库工作区。支持消息同步、搜索、导出及处理。

### 基本用法

```bash
# 初始化工作区
chattool kb init [name]

# 跟踪 Zulip Stream
chattool kb track [name] "general"

# 同步消息 (快照模式，获取最新消息)
chattool kb sync [name] --latest --limit 100

# 列出主题
chattool kb list [name] --stream "general"

# 显示特定主题的消息
chattool kb show [name] "general" "welcome"
```

### 命令详解

**`init`**: 初始化一个新的知识库工作区。
- `name`: 工作区名称（可选，默认使用 Zulip 站点名）。

**`track` / `untrack`**: 跟踪或取消跟踪 Zulip 中的 Stream。
- `name`: 工作区名称。
- `stream`: Stream 名称。

**`sync`**: 同步已跟踪 Stream 的消息。
- `name`: 工作区名称。
- `--latest`: 仅获取最新消息（快照模式）。
- `--limit`: 获取消息的最大数量 (默认: 1000)。

**`list`**: 列出工作区中的主题。
- `name`: 工作区名称。
- `--stream`: 按 Stream 过滤。
- `--export`: 导出结果到 CSV 文件。

**`show`**: 显示特定主题的消息内容。
- `name`: 工作区名称。
- `stream`: Stream 名称。
- `topic`: Topic 名称。
- `--limit`: 显示消息数量 (默认: 50)。
- `--export`: 导出消息到 TXT 文件。

**`search`**: 全文搜索知识库消息。
- `name`: 工作区名称。
- `query`: 搜索关键词。

**`process`**: 处理主题内容并重新发布（演示功能）。
- `name`: 工作区名称。
- `stream`: 源 Stream。
- `topic`: 源 Topic。
- `--to-stream`: 目标 Stream。
- `--to-topic`: 目标 Topic。
