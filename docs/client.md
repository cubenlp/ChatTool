# ChatTool 客户端命令行工具文档

ChatTool 提供了两个主要的命令行工具：`chattool` 用于各种服务管理，`chatenv` 用于环境配置管理。

## 命令结构

### chattool

CLI按功能分为几个命令组：

- **`dns`**: DNS 记录管理和动态 DNS (DDNS) 工具。
- **`serve`**: 本地服务器实用工具（例如，请求捕获）。
- **`client`**: 远程服务客户端工具。
- **`mcp`**: 模型上下文协议 (MCP) 服务器管理。
- **`lark`**: 保留的飞书最小调试命令（`info` / `send` / `chat`）。
- **`kb`**: 知识库 (Knowledge Base) 管理工具。
- **`zulip`**: Zulip 社区阅读与资讯汇总工具（仅只读）。
- **`setup`**: 环境初始化与依赖安装（Node.js / cc-connect / Codex / Claude / OpenCode / lark-cli / Docker / Chrome / FRP）。
- **`cc`**: cc-connect 的初始化、启动、日志与诊断工具。

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
chattool setup cc-connect
```

如需看更详细的阶段日志，可附加：

```bash
chattool setup cc-connect --log-level DEBUG
```

如果你更习惯从 `cc` 分组进入，也可以继续使用别名：

```bash
chattool cc setup
```

生成最小可用配置时，如需默认隐藏思考和工具进度中间消息，可直接写入项目级 quiet 配置：

```bash
chattool cc init -i --quiet
```

### 0.1 Codex (`setup codex`)

默认交互输入密钥（会读取已有配置并以 mask 形式展示）：

```bash
chattool setup codex
```

如需更详细地查看依赖检测、npm 安装和配置写入阶段，可附加：

```bash
chattool setup codex --log-level DEBUG
```

命令会先检查本机是否已有 `Node.js >= 20` 和 `npm`。如果当前终端可交互且依赖不满足，会先提示是否执行 `chattool setup nodejs` 进行安装或升级。

直接传 API key：

```bash
chattool setup codex --api-key "sk-xxx"
```

如果你已经在 `chatenv` 里维护了 `oai/openai` 配置，也可以显式复用：

```bash
chattool setup codex -e work
chattool setup codex -e ~/.config/chattool/envs/OpenAI/work.env
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
chattool setup codex --api-key "sk-xxx" --base-url "https://example.com/openai" --model "gpt-5.4"
```

### 0.2 Claude Code (`setup claude`)

默认交互输入密钥（会读取已有配置并以 mask 形式展示）：

```bash
chattool setup claude
```

如需查看更详细的安装和写入日志，可附加：

```bash
chattool setup claude --log-level DEBUG
```

命令同样会先检查本机是否已有 `Node.js >= 20` 和 `npm`；不满足时会优先提示安装/升级，再继续收集 Claude Code 配置。

直接传参：

```bash
chattool setup claude --auth-token "sk-ant-xxx"
```

可选覆盖 `ANTHROPIC_BASE_URL` 和 `ANTHROPIC_SMALL_FAST_MODEL`：

```bash
chattool setup claude --auth-token "sk-ant-xxx" --base-url "https://example.com/anthropic" --small-fast-model "claude-opus-4-6"
```

### 0.3 OpenCode (`setup opencode`)

默认交互输入配置项（会读取已有配置并以 mask 形式展示）：

```bash
chattool setup opencode
```

如需更详细的依赖检查和配置写入日志，可附加：

```bash
chattool setup opencode --log-level DEBUG
```

命令会先检查本机是否已有 `Node.js >= 20` 和 `npm`；不满足时会优先提示安装/升级，再继续进入 OpenCode 的配置流程。

直接传参：

```bash
chattool setup opencode --base-url "https://example.com/openai" --api-key "sk-xxx" --model "gpt-4.1-mini"
```

也可以显式复用 `chatenv` 里的 OpenAI 配置：

```bash
chattool setup opencode -e work
chattool setup opencode -e ~/.config/chattool/envs/OpenAI/work.env
```

解析顺序为：

1. 显式参数：`--base-url`、`--api-key`、`--model`
2. `-e/--env` 指定的 OpenAI 配置
3. 现有 `~/.config/opencode/opencode.json` 配置
4. 当前 shell 的系统环境变量
5. `envs/OpenAI/.env` 的 typed 默认值
6. 默认值

### 0.4 Lark CLI (`setup lark-cli`)

安装官方 `lark-cli`，并把 ChatTool 当前保存的 Feishu 配置复用过去：

```bash
chattool setup lark-cli
```

如需更详细地查看 Node.js 检查、npm 安装和 `lark-cli` 初始化阶段，可附加：

```bash
chattool setup lark-cli --log-level DEBUG
```

命令会先检查本机是否已有 `Node.js >= 20` 和 `npm`；不满足时会优先提示安装/升级，再继续进入 `lark-cli` 的配置流程。

如果你已经在 `chatenv` 里维护了 `feishu/lark` 配置，也可以显式复用：

```bash
chattool setup lark-cli -e work
chattool setup lark-cli -e ~/.config/chattool/envs/Feishu/work.env
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
chattool setup docker
```

如需更详细地查看环境检查分支和建议命令判断，可附加：

```bash
chattool setup docker --log-level DEBUG
```

默认只打印建议命令，不会直接执行 `sudo`。如需允许命令在确认后直接执行，显式传入：

```bash
chattool setup docker --sudo -i
```

### 0.6 Playground (`setup playground`)

把一个目录快速初始化或更新为工作区：

1. clone `ChatTool/`
2. 运行 `git submodule update --init --recursive`
3. 生成 `AGENTS.md`、`CHATTOOL.md`、`MEMORY.md`
4. 创建 `reports/`、`playgrounds/`、`knowledge/`
5. 从 clone 出来的 `ChatTool/skills/` 复制 skills 到 `knowledge/skills/`，并为每个 skill 创建 `experience/`

如果目标目录已经是已有工作区，再次执行时会进入更新模式：

- 优先更新 `ChatTool/` 仓库；如果仓库里有本地改动，则默认跳过仓库更新，避免覆盖工作区中的开发状态
- 仓库完成 clone / fast-forward 后，会自动执行 `git submodule update --init --recursive`，确保诸如 `lark-cli/` 这类子模块同步到当前仓库版本
- 交互模式下会提示是否同步工作区 `knowledge/skills/`
- 同步 `knowledge/skills/` 时只覆盖常规文件，不会改动各 skill 下的 `experience/`
- 已存在的工作区说明文件默认仍然保留；只有显式传 `--force` 时才会覆盖这些生成文件

如果目标目录只是普通非空目录而不是现有工作区，交互模式下仍会先提示是否继续；确认后会保留已有文件，并跳过已存在的生成文件。

完成 workspace bootstrap 后，命令还会尝试配置 GitHub 的 HTTPS Git 鉴权：

- 优先读取 `GitHubConfig.GITHUB_ACCESS_TOKEN.value`，也就是 `chatenv cat -t gh` 对应的当前配置值
- 交互模式下会提示是否配置，并允许输入新的 token；直接回车则保留当前配置值
- 非交互模式下如果当前 `chatenv` 里已有 `GITHUB_ACCESS_TOKEN`，会自动写入 `git credential store`
- 该步骤会执行 `git config --global credential.helper store`，并为默认的 ChatTool GitHub 仓库写入一条 repo 级 PAT 凭据，方便后续 clone / push / fetch

在目标空目录里直接执行：

```bash
chattool setup playground
```

默认模板语言是中文。

或显式指定工作区目录：

### 0.6 Workspace (`setup workspace`)

如果你已经有自己的核心项目，只想在项目外围加一层“人类-AI 协作协议 + 多任务并发面 + 知识沉淀”工作区，可以用：

```bash
chattool setup workspace
chattool setup workspace ~/workspace/demo
chattool setup workspace ~/workspace/demo --language en
```

它会生成一套独立骨架，包括：

- `AGENTS.md`：模型主协议
- `MEMORY.md`：跨 session 记忆
- `reports/`：默认按任务隔离的人类汇报目录，也支持任务集目录
- `playgrounds/`：默认按任务隔离的工作目录，也支持任务集共享工作根
- `docs/`：长期文档沉淀
- `core/`：源码仓库目录
- `skills/`：共享 skills 目录
- `public/`：公开网站和发布目录

默认先用常规任务模式；如果是一组围绕同一目标持续推进的大任务，再切换到 `reports/MM-DD-<set-name>/` 与 `playgrounds/task-sets/<set-name>/`。对于后继 task，建议在它自己的 `TASK.md` 开头写清验收需求，并说明不满足时是否需要人类 review，还是允许模型自行决断。

默认模板语言是中文；如果你要英文版协议和 onboarding 文件，可以显式传 `--language en`。

如果只想先看计划不落盘：

```bash
chattool setup workspace ~/workspace/demo --dry-run -I
```

交互模式下还可以额外勾选模块，例如：

- `ChatTool`：下载到 `core/ChatTool/`，并把相关 skills 同步到 `./skills/`
- `RexBlog`：下载到 `core/RexBlog/`，并把 `source/_posts` 链接到 `./public/hexo_blog`

## 1. DNS 管理 (`dns`)

管理 DNS 记录并自动更新动态 DNS。支持阿里云 (Aliyun) 和腾讯云 (Tencent) DNS 提供商。

### 1.1 动态 DNS (DDNS)

使用当前 IP 地址更新 DNS 记录。支持公网 (Public) 和局域网 (Local) IP，以及持续监控模式。

```bash
# 更新域名的公网 IP (一次性)
chattool dns ddns public.example.com

# 以监控模式运行 (每 120 秒检查一次)
chattool dns ddns public.example.com --monitor

# 更新局域网 IP，并指定子网过滤器
chattool dns ddns local.example.com --ip-type local --local-ip-cidr 192.168.1.0/24

# 指定 TTL 和重试参数
chattool dns ddns public.example.com --ttl 600 --max-retries 5 --retry-delay 10
```

**完整选项说明:**
- `full_domain`: 完整域名 (例如 `sub.example.com`)。
- `-d, --domain`: 域名 (例如 `example.com`)。
- `-r, --rr`: 主机记录 (例如 `sub`)。
- `--monitor`: 启用持续监控模式。
- `-i, --interval`: 检查间隔，单位为秒 (默认: 120)。
- `--ip-type`: 更新的 IP 类型: `public` (默认) 或 `local`。
- `--local-ip-cidr`: 局域网 IP 过滤网段 (例如 `192.168.0.0/16`)，仅当 `--ip-type=local` 时有效。
- `-p, --provider`: DNS 提供商: `aliyun` (默认) 或 `tencent`。
- `--ttl`: TTL 值 (默认: 600)。
- `--max-retries`: 最大重试次数 (默认: 3)。
- `--retry-delay`: 重试延迟秒数 (默认: 5)。
- `--log-file`: 日志文件路径 (默认不记录到文件，除非开启监控模式且未指定则使用默认)。
- `--log-level`: 日志级别 (默认: INFO)。

### 1.2 记录管理

**获取记录 (`get`):**
```bash
# 获取域名的所有记录
chattool dns get -d example.com

# 获取特定记录
chattool dns get test.example.com
```
**选项:**
- `-t, --type`: 记录类型过滤 (例如 `A`, `TXT`, `CNAME`)。
- `-p, --provider`: DNS 提供商 (默认: `aliyun`)。

**设置/更新记录 (`set`):**
```bash
# 设置 A 记录
chattool dns set test.example.com -v 1.2.3.4

# 设置 TXT 记录
chattool dns set -d example.com -r _test -t TXT -v "some-value"
```
**选项:**
- `-v, --value`: 记录值。交互终端里缺少时会自动补问；显式传 `-I` 时才保持直接报错。
- `-t, --type`: 记录类型 (默认: `A`)。
- `--ttl`: TTL 值 (默认: 600)。
- `-p, --provider`: DNS 提供商 (默认: `aliyun`)。

### 1.3 SSL 证书 (`cert-update`)

使用 Let's Encrypt 和 DNS 验证自动申请和续期 SSL 证书。

```bash
chattool dns cert-update -d example.com -d *.example.com -e admin@example.com
chattool dns cert-update
```

在交互终端里，缺少域名或邮箱时会自动补问；显式传 `-I` 时才会禁用交互并直接报错。

**输出文件结构:**
证书将保存在 `<cert-dir>/<domain>/` 目录下，包含以下文件：
- `fullchain.pem`: 完整证书链 (适用于 Nginx/Apache 配置)。
- `privkey.pem`: 私钥文件 (适用于 Nginx/Apache 配置)。
- `cert.pem`: 叶子证书。
- `chain.pem`: 中间证书。

**完整选项说明:**
- `-d, --domains`: 域名列表 (可多次使用，支持通配符)。
- `-e, --email`: 用于 Let's Encrypt 注册的邮箱。
- `-p, --provider`: 用于验证的 DNS 提供商 (`aliyun` 或 `tencent`，默认: `aliyun`)。
- `--cert-dir`: 证书存储根目录 (默认: `certs`)。
- `--staging`: 使用 Let's Encrypt 测试环境 (用于测试)。
- `--log-file`: 日志文件路径 (默认不记录到文件)。

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

## 3. 网络工具 (`network`)

提供基础的网络探测与链接校验能力。

### 3.1 存活扫描 (`network ping`)
```bash
chattool network ping --network 192.168.1.0/24
chattool network ping
```

交互终端里缺少 `--network` 时会自动补问；`-I` 会禁用交互。

### 3.2 端口扫描 (`network ssh`)
```bash
chattool network ssh --network 192.168.1.0/24 --port 22
```

### 3.3 链接有效性检查 (`network links`)
```bash
# 从目录内扫描 URL
chattool network links --path ./docs --glob "*.md"

# 直接检查 URL
chattool network links --url https://example.com
```

### 3.4 服务校验 (`network services`)
用于统一验证 Chromium/Chromedriver/Playwright 服务的连通性与响应特征。

```bash
export CHATTOOL_CHROMIUM_URL="http://host:8080/token/chromium/json/version"
export CHATTOOL_CHROMIUM_TOKEN="your-token"
export CHATTOOL_CHROMEDRIVER_URL="http://host:8080/token/chromedriver/"
export CHATTOOL_PLAYWRIGHT_URL="http://host:8080/token/playwright/"

chattool network services
```

---

## 4. GitHub 工具 (`gh`)

### 4.1 配置
默认行为：

- `repo`：优先从当前 git remote 推断
- `token`：优先从当前仓库对应的 git credential 读取，再回退 `GITHUB_ACCESS_TOKEN`

### 4.2 常用命令
```bash
chatenv cat -t gh

export GITHUB_ACCESS_TOKEN="..."

# 列出 PR
chattool gh pr-list --state open --limit 20

# 查看 PR 详情（含 mergeable / merge state）
chattool gh pr-view --number 123
chattool gh pr-view

# 查看 PR 的可合并状态与 CI / checks 状态
chattool gh pr-check --number 123
chattool gh pr-check --number 123 --wait
chattool gh pr-check --number 123 --wait --interval 10 --timeout 600

# 查看某次 workflow run 与 jobs
chattool gh run-view --run-id 23494900414

# 查看某个 job 的日志
chattool gh job-logs --job-id 68373094563

# 创建 PR
chattool gh pr-create --base vibe/master --head feature-branch --title "Title" --body "Body"
chattool gh pr-create

# 评论 PR
chattool gh pr-comment --number 123 --body "Looks good"

# 合并 PR
chattool gh pr-merge --number 123 --method squash
chattool gh pr-merge --number 123 --method squash --check

# 更新 PR（标题/正文/状态/基线分支）
chattool gh pr-update --number 123 --title "New title" --body "Updated body"

# 为当前 GitHub 仓库配置 repo 级 HTTPS token
chattool gh set-token --token github_pat_xxx

# 如需顺手保存到 ChatTool GitHub 配置
chattool gh set-token --token github_pat_xxx --save-env

# 查看当前 token 对仓库的权限列表
chattool gh repo-perms --repo owner/repo --token github_pat_xxx
```

在交互终端里，`pr-create` / `pr-view` / `pr-check` / `run-view` / `job-logs` / `pr-comment` / `pr-merge` / `pr-update` 缺少关键参数时都会自动补问；显式传 `-I` 才禁用交互并直接报错。

`set-token` 只在当前目录存在 git remote，且 `origin` 指向 GitHub 仓库时生效。它会按仓库路径写入本地 Git HTTPS credential，因此不同仓库可以使用不同 token。

默认情况下，`set-token` 不会改写 `GITHUB_ACCESS_TOKEN`。只有显式传 `--save-env`，才会把 token 写入 `chatenv gh` 对应的 GitHub 配置。

这里的 `ghp_xxx` / `github_pat_xxx` 都是 GitHub 的 Personal Access Token。来源是：

1. GitHub `Settings`
2. `Developer settings`
3. `Personal access tokens`
4. 创建 classic token，或 fine-grained token

如果只是 clone / fetch / push 某个仓库，通常至少需要该仓库的 contents 读写权限；更细的 issue / PR / Actions 操作，再按需补权限。

如果你想直接验证 token 对某个仓库的权限，可用 `repo-perms` 查看 GitHub 返回的 `permissions` 字段，例如 `pull` / `push` / `admin`。

`pr-view` 和 `pr-check` 现在都会直接展示 PR 相对 base 分支的可合并状态：

- `mergeable`
- `mergeable_state`

`pr-check` 还会按 PR 的 head commit 汇总三层信息，适合排查 CI：

- combined status
- check runs
- workflow runs

如果追加 `--wait`，CLI 会持续轮询直到 checks 和 workflow runs 都结束：

- 默认不设超时，会一直等到全部结束
- 可用 `--interval <seconds>` 控制轮询间隔
- 只有显式传 `--timeout <seconds>` 时，才会在超时后报错退出

如果希望在执行 `pr-merge` 前顺手做一次强校验，可追加 `--check`。当 checks / workflow runs 里存在失败、取消或未完成项，或者 PR 当前 `mergeable=False` / `mergeable_state` 处于 `dirty`、`blocked`、`behind`、`draft`、`unknown` 时，CLI 会拒绝合并并提示先运行 `pr-check`；不带 `--check` 时则保持当前直接调用 GitHub merge 的行为。

如果 `pr-check` 已经定位到具体 workflow run / job，可以继续使用：

- `run-view --run-id <id>`：查看某次 workflow run 的元信息、jobs 与 step 状态
- `job-logs --job-id <id>`：直接抓取 job 日志；默认输出尾部，可用 `--tail 0` 查看完整日志，或用 `--output` 落盘

需要机器可读结果时可加 `--json-output`。

在执行 `pr-create`、汇报“CI 是否通过”或准备 merge 前，先 `git fetch origin <base>`，再确认两件事：

- `pr-view` / `pr-check` 显示 `mergeable` 不是 `False`，`mergeable_state` 不是 `dirty`
- 本地基于最新 base 做一次 merge 或 rebase 演练，并在该结果上跑最相关测试

### 4.3 API Reference

后续扩展 `chattool gh` 时，优先查这些官方文档：

- GitHub REST API 根文档: https://docs.github.com/en/rest
- Pull requests API: https://docs.github.com/en/rest/pulls/pulls
- Check runs API: https://docs.github.com/en/rest/checks/runs
- Workflow runs API: https://docs.github.com/en/rest/actions/workflow-runs
- Workflow jobs API: https://docs.github.com/en/rest/actions/workflow-jobs
- Commit statuses API: https://docs.github.com/en/rest/commits/statuses
- PyGithub 文档: https://pygithub.readthedocs.io/
- PyGithub `PullRequest` 参考: https://pygithub.readthedocs.io/en/latest/github_objects/PullRequest.html
- PyGithub `Repository` 参考: https://pygithub.readthedocs.io/en/latest/github_objects/Repository.html

---

## 5. Zulip 工具 (`zulip`)

用于读取 Zulip 社区消息并生成资讯摘要（**只读**，不提供发送接口以避免误发）。

### 5.1 配置

使用 `chatenv` 查看或配置：

```bash
chattool chatenv cat -t zulip
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
chattool env init -i

# 列出所有配置
chattool env list

# 设置配置值
chattool env set CHATTOOL_DNS_PROVIDER=tencent

# 获取配置值
chattool env get CHATTOOL_DNS_PROVIDER

# 删除配置值
chattool env unset CHATTOOL_DNS_PROVIDER

# 缺少 key / profile 名时自动补问
chattool env save -t gh
chattool env use -t gh
chattool env delete -t gh
chattool env get
chattool env set
chattool env unset
```

**命令详解:**
- `init`: 初始化或更新配置文件。使用 `-i, --interactive` 进入交互模式。
- `list`: 列出所有当前生效的配置值。
- `set`: 设置单个配置项，格式为 `KEY=VALUE`。
- `get`: 获取单个配置项的值。
- `unset`: 删除（置空）单个配置项的值。

在交互终端里，`save/use/delete/get/set/unset/test` 缺少关键参数时都会自动补问；显式传 `-I` 才禁用交互并直接报错。

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
