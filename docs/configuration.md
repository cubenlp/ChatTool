# 配置管理指南

ChatTool 从 v5.0.0 开始引入了全新的集中式配置管理系统，支持从 `.env` 文件自动加载配置，并提供了类型安全的代码内访问方式。

## 配置机制

对常规 CLI 与组件而言，配置读取顺序如下（优先级从高到低）：

1. **CLI / 调用方显式指定**：命令行参数、函数参数或调用侧显式传入的值。
2. **env 文件**：项目配置目录下按类型拆分的 env 文件。
3. **系统环境变量**：操作系统层面的环境变量（如 `export OPENAI_API_KEY=...`）。
4. **默认值**：代码中定义的默认值。

对于支持 `-e/--env` 一类显式 env 覆盖源，且同时会读取工具自身默认配置位置（例如 `~/.codex/`、`~/.config/opencode/`、`~/.lark-cli/`）的 setup 命令，优先级进一步细化为：

1. **CLI / 调用方显式指定**
2. **显式 env 引用**：例如 `chattool lark -e work` 或 `chattool lark -e /path/to/file.env`
3. **工具默认配置位置**：例如 `~/.codex/config.toml`、`~/.config/opencode/opencode.json`
4. **系统环境变量**
5. **按类型拆分的内置 env 文件**：例如 `envs/Feishu/.env`
6. **默认值**

说明：

- 该优先级对应 `BaseEnvConfig.load_from_dict()` / `load_all()` 的真实实现：已注册配置项会优先读取当前激活的 typed env 文件，其次才回退到 `os.environ`。
- 当命令显式传入 `-e/--env` 时，会走 `BaseEnvConfig.load_all_with_override()`：先读取类型内置 `.env`，再在其上叠加显式 env；若显式 env 未提供某字段，才继续回退到系统环境变量与默认值。
- 这样 `chatenv init` 或 `chatenv use` 更新 active `.env` 后，会立刻成为当前生效配置，不会被已有 shell 环境变量意外盖掉。
- 但对于 `setup codex` / `setup opencode` / `setup lark-cli` 这类还会读取工具自身默认配置文件的命令，现行策略是优先保留已有工具配置，再回退到系统环境变量与 typed `.env`，避免单纯因为当前 shell 里存在 OpenAI / Feishu 默认值就把已有工具配置覆盖掉。
- `BaseEnvConfig.set()` 是运行时覆盖手段，只修改当前进程内的值；它不属于上面的“默认加载顺序”，也不会自动回写 `.env` 或同步系统环境变量。
- 对于已经注册到 `src/chattool/config/` 的配置项，CLI 与业务代码应优先读取配置对象的 `.value`，不要只直接读取 `os.environ`，否则会绕过 `chatenv` 管理的默认值。
- 例如 `chattool setup playground` 在补 GitHub 鉴权时，会优先读取 `GitHubConfig.GITHUB_ACCESS_TOKEN.value`，从而复用 `chatenv` 当前生效的 GitHub 配置。

## 快速开始

### 1. 使用 CLI 初始化配置 (推荐)

ChatTool 提供了便捷的命令行工具 `chatenv` 来管理配置。

```bash
# 交互式初始化（引导设置各项配置）
chatenv init -i

# 仅设置特定类别的配置（例如只配置网络和 OpenAI）
chatenv init -i -t "OpenAI"
```

该命令会引导你逐步设置所需的 API Key 和其他参数，并自动保存到按类型拆分的 env 文件中，例如 `envs/OpenAI/.env`。

### 2. 手动生成配置模板 (可选)

如果你偏好手动编辑，也可以生成模板：

```python
from chattool import create_env_file

# 生成 .env 文件
create_env_file(".env")
```

### 3. CLI 管理配置

使用 `chatenv` 命令来管理配置：

```bash
# 设置配置
chatenv set OPENAI_API_KEY=sk-new-key

# 查看当前配置（默认隐藏敏感信息）
chatenv cat

# 查看当前配置（显示明文，慎用）
chatenv cat --no-mask

# 获取单个配置
chatenv get OPENAI_API_KEY
```

在代码中，你不再需要手动读取 `os.getenv`，ChatTool 的各个组件会自动读取配置。

```python
from chattool import Chat

# 自动读取 OPENAI_API_KEY 等配置
chat = Chat() 
```

## 配置集管理 (Profiles)

你可以按配置类型保存多个 profile 并单独切换：

```bash
# 从当前激活配置复制一份新的 profile，不修改当前 active 配置
chatenv new mini -t feishu

# 省略 profile 名时，会先询问名称，再进入该类型的交互配置
chatenv new -t openai

# 保存当前 OpenAI 配置为 'dev' 环境
chatenv save dev -t openai

# 列出所有已保存的 profile
chatenv list

# 只切换 OpenAI 到 'prod' profile
chatenv use prod -t openai

# 查看 OpenAI 的 'prod' profile 内容
chatenv cat prod -t openai

# 删除 OpenAI 的 'test' profile
chatenv delete test -t openai
```

当前目录结构形如：

```text
~/.config/chattool/envs/
├── OpenAI/
│   ├── .env
│   └── prod.env
├── Feishu/
│   ├── .env
│   └── work.env
└── GitHub/
    └── .env
```

约定：

- `envs/<Config>/.env` 表示该类型当前激活的默认配置。
- `envs/<Config>/<profile>.env` 表示该类型下保存的 profile。
- `chatenv new <profile> -t <type>` 的语义是：从当前激活配置复制一份新 profile，但不修改该类型当前的 `.env`。
- `chatenv new -t <type>` 在交互终端里会先询问 profile 名，再像 `init -t <type>` 一样补齐该类型字段，然后只写入该 profile，不会自动激活。
- `chatenv use <profile> -t <type>` 的语义是把对应 profile 激活到该类型的 `.env`。
- 命令如果支持 `-e/--env`，优先接受真实 `.env` 文件路径；如命令做了类型约束，也可以接受该类型下保存过的 profile 名称。

## 高级用法

### 动态修改配置

你可以在运行时动态修改配置，这对多账号切换或测试场景非常有用。修改后，**新创建**的客户端实例将使用新配置。

```python
from chattool.config import BaseEnvConfig, OpenAIConfig
from chattool import Chat

# 查看当前配置
print(OpenAIConfig.OPENAI_API_KEY.value)

# 动态修改 API Key
BaseEnvConfig.set("OPENAI_API_KEY", "new-secret-key")

# 新的 Chat 实例将使用新 Key
chat = Chat()
print(chat.api_key) # 输出: new-secret-key
```

### 访问配置值

你可以直接从配置类中访问当前生效的配置值：

```python
from chattool.config import OpenAIConfig, AliyunConfig

key = OpenAIConfig.OPENAI_API_KEY.value
region = AliyunConfig.ALIBABA_CLOUD_REGION_ID.value
```

### 敏感信息保护

配置系统会自动识别敏感字段（如 API Key、Secret），在打印配置或生成日志时自动进行脱敏处理（用 `*` 代替）。

```python
from chattool.config import BaseEnvConfig

# 打印当前所有配置（敏感信息已脱敏）
BaseEnvConfig.print_config()
```

## 支持的配置项

目前支持以下服务的配置：

- **OpenAI**: `OPENAI_API_KEY`, `OPENAI_API_BASE` 等
- **Azure OpenAI**: `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT` 等
- **阿里云**: `ALIBABA_CLOUD_ACCESS_KEY_ID`, `ALIBABA_CLOUD_ACCESS_KEY_SECRET` 等
- **腾讯云**: `TENCENT_SECRET_ID`, `TENCENT_SECRET_KEY` 等
- **Zulip**: `ZULIP_BOT_EMAIL`, `ZULIP_BOT_API_KEY` 等
- **飞书**: `FEISHU_APP_ID`, `FEISHU_APP_SECRET`, `FEISHU_DEFAULT_RECEIVER_ID`, `FEISHU_DEFAULT_CHAT_ID` 等
- **Skills**: `CHATTOOL_SKILLS_DIR`（skills 源目录，`chattool skill` / `chatskill` 在未传 `--source` 时默认读取）
- **GitHub**: `GITHUB_ACCESS_TOKEN`, `GITHUB_DEFAULT_REPO`

说明：`GITHUB_ACCESS_TOKEN` 是 ChatTool 的 GitHub 全局默认 token；如果你只想给当前 git 仓库配置独立的 HTTPS token，优先使用 `chattool gh set-token`，它会按仓库路径写入本地 git credential，而不是覆盖全局默认 token。

其中飞书相关有两个额外约定：

- `FEISHU_DEFAULT_RECEIVER_ID`：给 `chattool lark send` 提供默认用户发送目标。
- `FEISHU_DEFAULT_CHAT_ID`：给 `chattool lark send -t chat_id` 提供默认群聊发送目标。

## SVG 转 GIF 服务配置

- `CHATTOOL_CHROMEDRIVER_URL`: chromedriver 服务地址（用于 `chattool serve svg2gif`）
- `CHATTOOL_SVG2GIF_SERVER`: svg2gif 服务地址（用于 `chattool client svg2gif`）
- `BROWSER_SELENIUM_REMOTE_URL`: 备用的 Selenium 远程地址（未设置 `CHATTOOL_CHROMEDRIVER_URL` 时使用）
