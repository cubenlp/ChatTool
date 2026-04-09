# test_chattool_setup_basic

测试 `chattool setup` 的基础链路，覆盖 alias/chrome/docker/frp/nodejs/cc-connect/codex/claude/opencode/playground/workspace 等子命令入口。

## 元信息

- 命令：`chattool setup <command> [args]`
- 目的：验证 setup 工具的基础命令可用。
- 标签：`cli`
- 前置条件：无
- 环境准备：按需准备交互参数或依赖。
- 回滚：删除生成的配置或临时文件。

## 用例 1：帮助信息

- 初始环境准备：
  - 无
- 相关文件：
  - 无

预期过程和结果：
  1. 执行 `chattool setup --help`，预期输出子命令列表。

参考执行脚本（伪代码）：

```sh
chattool setup --help
```

## 用例 2：alias

- 初始环境准备：
  - 准备临时 rc 文件路径（如 `.zshrc`）。
- 相关文件：
  - `<tmp>/.zshrc`

预期过程和结果：
  1. 执行 `chattool setup alias --dry-run`，预期输出 alias 变更内容且不写入文件。

参考执行脚本（伪代码）：

```sh
chattool setup alias --dry-run
```

## 用例 3：chrome/docker/frp/nodejs

- 初始环境准备：
  - 确保可安装依赖。
- 相关文件：
  - 可能生成的安装目录或配置文件。

预期过程和结果：
  1. 执行 `chattool setup chrome -i`，预期进入交互式安装流程。
  2. 执行 `chattool setup docker -i`，预期进入 Docker 环境检查流程；若检测到 Docker / Docker Compose / docker 组缺失，应先提示建议命令，并仅在用户明确确认后执行需要 sudo 的安装步骤。
  3. 执行 `chattool setup frp -i`，预期进入交互式安装流程。
  4. 执行 `chattool setup nodejs -i`，预期进入交互式安装流程，并在缺少 `~/.nvm/nvm.sh` 时直接写入内置的 `nvm.sh`。

参考执行脚本（伪代码）：

```sh
chattool setup chrome -i
chattool setup docker -i
chattool setup frp -i
chattool setup nodejs -i
```

## 用例 4：cc-connect/codex/claude/opencode/lark-cli

- 初始环境准备：
  - 准备 API key 与 base_url。
- 相关文件：
  - 可能生成的配置文件。

预期过程和结果：
  1. 执行 `chattool setup cc-connect -i`，预期先检查 Node.js（>= 20），必要时提示执行 `chattool setup nodejs` 安装/升级，然后安装或确认 `cc-connect` CLI。
  2. 执行 `chattool setup codex -i`，预期在收集配置前先检查 Node.js（>= 20）；若不满足，则先提示是否执行 `chattool setup nodejs` 进行安装/升级，然后再进入交互式配置流程。
  3. 执行 `chattool setup codex -e work` 时，预期可显式从 `OpenAI` profile 读取 `OPENAI_API_KEY`、`OPENAI_API_BASE`、`OPENAI_API_MODEL`。
  4. 执行 `chattool setup claude -i`，预期在收集配置前先检查 Node.js（>= 20）；若不满足，则先提示是否执行 `chattool setup nodejs` 进行安装/升级，然后再进入交互式配置流程。
  5. 执行 `chattool setup opencode -i`，预期在收集配置前先检查 Node.js（>= 20）；若不满足，则先提示是否执行 `chattool setup nodejs` 进行安装/升级，然后再进入交互式配置流程。
  6. 执行 `chattool setup lark-cli -i`，预期在收集配置前先检查 Node.js（>= 20）；若不满足，则先提示是否执行 `chattool setup nodejs` 进行安装/升级；随后可直接复用当前 ChatTool Feishu 配置或显式 `-e` 指定的 profile，并调用官方 `lark-cli config init --app-secret-stdin` 落盘到 `~/.lark-cli/config.json`（或 `LARKSUITE_CLI_CONFIG_DIR/config.json`）。

参考执行脚本（伪代码）：

```sh
chattool setup cc-connect -i
chattool setup codex -i
chattool setup codex -e work
chattool setup claude -i
chattool setup opencode -i
chattool setup lark-cli -i
```

## 用例 5：workspace

- 初始环境准备：
  - 准备一个空目录作为工作区根目录。
- 相关文件：
  - `<workspace>/AGENTS.md`
  - `<workspace>/MEMORY.md`
  - `<workspace>/setup.md`
  - `<workspace>/reports/`
  - `<workspace>/playgrounds/`
  - `<workspace>/docs/`
  - `<workspace>/core/`
  - `<workspace>/reference/`

预期过程和结果：
  1. 执行 `chattool setup workspace [PROFILE] [WORKSPACE_DIR]`，预期可生成围绕核心项目的独立协作骨架，包括 `AGENTS.md`、`MEMORY.md`、`setup.md`、`reports/`、`playgrounds/`、`docs/`、`core/`、`reference/`，并默认采用按任务隔离的并发协作结构。
  2. 如显式传 `--with-chattool --chattool-source <repo-or-url>`，预期在 `core/ChatTool/` 下同步仓库，并把 skills 复制到工作区 `skills/`。
  3. 若目标目录已经像一个 workspace，预期保留现有 `AGENTS.md` / `MEMORY.md`，并额外生成 `AGENTS.generated.md`、`MEMORY.generated.md` 与迁移版 `setup.md`。
  4. 执行 `chattool setup workspace <workspace> --dry-run -I`，预期仅打印将创建的目录与文件，不实际写入。

参考执行脚本（伪代码）：

```sh
chattool setup workspace /tmp/my-workspace -I
chattool setup workspace /tmp/my-workspace --with-chattool --chattool-source /path/to/ChatTool -I
chattool setup workspace /tmp/my-workspace --dry-run -I
```

## 清理 / 回滚

- 删除生成的配置文件或安装目录。
