# test_chattool_setup_basic

测试 `chattool setup` 的基础链路，覆盖 alias/chrome/frp/nodejs/cc-connect/codex/claude/opencode/playground 等子命令入口。

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

## 用例 3：chrome/frp/nodejs

- 初始环境准备：
  - 确保可安装依赖。
- 相关文件：
  - 可能生成的安装目录或配置文件。

预期过程和结果：
  1. 执行 `chattool setup chrome -i`，预期进入交互式安装流程。
  2. 执行 `chattool setup frp -i`，预期进入交互式安装流程。
  3. 执行 `chattool setup nodejs -i`，预期进入交互式安装流程，并在缺少 `~/.nvm/nvm.sh` 时直接写入内置的 `nvm.sh`。

参考执行脚本（伪代码）：

```sh
chattool setup chrome -i
chattool setup frp -i
chattool setup nodejs -i
```

## 用例 4：cc-connect/codex/claude/opencode

- 初始环境准备：
  - 准备 API key 与 base_url。
- 相关文件：
  - 可能生成的配置文件。

预期过程和结果：
  1. 执行 `chattool setup cc-connect -i`，预期先检查 Node.js（>= 20），必要时提示执行 `chattool setup nodejs` 安装/升级，然后安装或确认 `cc-connect` CLI。
  2. 执行 `chattool setup codex -i`，预期在收集配置前先检查 Node.js（>= 20）；若不满足，则先提示是否执行 `chattool setup nodejs` 进行安装/升级，然后再进入交互式配置流程。
  3. 执行 `chattool setup claude -i`，预期在收集配置前先检查 Node.js（>= 20）；若不满足，则先提示是否执行 `chattool setup nodejs` 进行安装/升级，然后再进入交互式配置流程。
  4. 执行 `chattool setup opencode -i`，预期在收集配置前先检查 Node.js（>= 20）；若不满足，则先提示是否执行 `chattool setup nodejs` 进行安装/升级，然后再进入交互式配置流程。

参考执行脚本（伪代码）：

```sh
chattool setup cc-connect -i
chattool setup codex -i
chattool setup claude -i
chattool setup opencode -i
```

## 用例 5：playground

- 初始环境准备：
  - 准备一个空目录作为工作区根目录。
- 相关文件：
  - `<workspace>/AGENTS.md`
  - `<workspace>/CHATTOOL.md`
  - `<workspace>/MEMORY.md`
  - `<workspace>/Memory/`
  - `<workspace>/skills/`
  - `<workspace>/scratch/`
  - `<workspace>/ChatTool/`

预期过程和结果：
  1. 首次执行 `chattool setup playground --workspace-dir <workspace> --chattool-source <repo-or-url>`，预期在目标目录下 clone `ChatTool/`。
  2. 若目标目录只是普通非空目录且当前终端可交互，预期先提示是否继续；确认后继续初始化，并保留已有文件。
  3. 若目标目录中已经存在 `ChatTool/`（或历史遗留的 `chattool/`），预期进入更新模式：优先更新仓库，并在交互模式下提示是否同步工作区 `skills/`。
  4. 预期生成 `AGENTS.md`、`CHATTOOL.md`、`MEMORY.md`。
  5. 预期创建 `Memory/`、`skills/`、`scratch/`。
  6. 预期从 `ChatTool/skills/` 复制或更新 skills 到工作区 `skills/`，并给每个 skill 创建 `experience/` 目录。
  7. 预期 skills 同步只替换常规文件，不修改已有 `experience/` 内容。

参考执行脚本（伪代码）：

```sh
chattool setup playground --workspace-dir /tmp/my-playground --chattool-source /path/to/ChatTool
```

## 清理 / 回滚

- 删除生成的配置文件或安装目录。
