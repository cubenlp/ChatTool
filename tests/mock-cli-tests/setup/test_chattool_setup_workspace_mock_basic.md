# test_chattool_setup_workspace_mock_basic

## Case 1: missing workspace dir should trigger interactive prompt

### 初始环境准备

- 在 mock CLI 环境下调用 `chattool setup workspace`，不提供 `WORKSPACE_DIR`。
- stub 掉文本输入，避免真实 TTY 依赖。

### 预期过程和结果

- 命令应进入 workspace 路径补全流程，而不是直接报缺参。
- 给出路径后，应调用 workspace setup 主逻辑。

### 参考执行脚本（伪代码）

```sh
mock ask_text -> /tmp/workspace
run chattool setup workspace
assert setup callback received workspace path
```

## Case 2: default language should be Chinese in dry-run output

### 初始环境准备

- 创建临时目录作为 workspace 根目录。

### 预期过程和结果

- 执行 `chattool setup workspace <workspace-dir> --dry-run -I`。
- 输出应包含中文 dry-run 摘要。
- 目录内不应出现生成文件。

### 参考执行脚本（伪代码）

```sh
run chattool setup workspace /tmp/workspace --dry-run -I
assert output mentions Chinese dry run summary
assert no generated files exist
```

## Case 3: explicit `--language en` should switch templates to English

### 初始环境准备

- 创建临时目录作为 workspace 根目录。

### 预期过程和结果

- 执行 `chattool setup workspace <workspace-dir> --language en -I`。
- 生成的 `AGENTS.md` 应包含英文标题 `## Architecture`。
- 不应保留中文标题 `## 架构`。
- 根目录 `README.md` 应使用英文 general-use 文案。

### 参考执行脚本（伪代码）

```sh
run chattool setup workspace /tmp/workspace --language en -I
assert AGENTS.md contains English headings
assert README.md contains English general-use text
```

## Case 4: interactive extra repos should enter repo token input directly

### 初始环境准备

- 在 mock CLI 环境下调用 `chattool setup workspace`。
- 交互中启用 `chattool` 和 `rexblog` 两个额外模块。
- mock 当前仓库 `.git-credential` 中已存在 GitHub token。

### 预期过程和结果

- 选择额外模块后，应直接进入 `ChatTool` 和 `RexBlog` 的 token 输入。
- token 默认值应来自当前仓库对应的 git credential，并以 mask 形式展示在输入标签中。
- 回车应保留当前 token；空值则表示跳过。
- 若保留或输入 token，应在 clone 前把它传给对应 repo 的 HTTPS credential 配置流程。

### 参考执行脚本（伪代码）

```sh
mock current repo credential token -> github_pat_xxx
run chattool setup workspace
assert token inputs appear directly for ChatTool and RexBlog
assert token is passed to cubenlp/ChatTool.git and RexWzh/RexBlog
```

## Case 5: workspace should use `projects/` container instead of `reports/` and `playgrounds/`

### 初始环境准备

- 创建空 workspace 临时目录。

### 预期过程和结果

- 执行 `chattool setup workspace <workspace-dir> -I`。
- 应生成 `projects/README.md`。
- 不应再生成 `reports/README.md` 或 `playgrounds/README.md`。
- `AGENTS.md` 与 `MEMORY.md` 应说明新的 `projects/` 模型，而不是旧的 `reports/` / `playgrounds/` 分桶模型。

### 参考执行脚本（伪代码）

```sh
run chattool setup workspace /tmp/workspace -I
assert projects/README.md exists
assert reports/README.md does not exist
assert playgrounds/README.md does not exist
assert AGENTS.md describes projects model
```

## Case 6: existing workspace should keep current protocol files and rely on workspace README guidance

### 初始环境准备

- 创建一个已有 `AGENTS.md` 和 `MEMORY.md` 的 workspace 目录。

### 预期过程和结果

- 再次执行 `chattool setup workspace <workspace-dir> -I`。
- 原有 `AGENTS.md` 和 `MEMORY.md` 不应被覆盖。
- 不应额外生成 `AGENTS.generated.md` 和 `MEMORY.generated.md`。
- 根目录 `README.md` 应作为当前 workspace 的 general-use 说明存在。

### 参考执行脚本（伪代码）

```sh
prepare existing AGENTS.md and MEMORY.md
run chattool setup workspace /tmp/workspace -I
assert existing files unchanged
assert helper generated files do not exist
assert README.md exists
```

## Case 7: enabling OpenCode loop support should switch template variant and install local `.opencode` assets

### 初始环境准备

- 创建空 workspace 临时目录。

### 预期过程和结果

- 执行 `chattool setup workspace <workspace-dir> -I --with-opencode-loop`。
- 应生成 loop-aware 的 `README.md`、`AGENTS.md`、`projects/README.md`。
- 应安装 `.opencode/opencode.jsonc`。
- 应安装 `.opencode/plugins/chatloop/`。
- 应安装 `.opencode/command/chatloop.md`、`chatloop-project.md`、`chatloop-help.md`、`chatloop-stop.md`。

### 参考执行脚本（伪代码）

```sh
run chattool setup workspace /tmp/workspace -I --with-opencode-loop
assert .opencode/opencode.jsonc exists
assert .opencode/plugins/chatloop/index.ts exists
assert .opencode/command/chatloop.md exists
assert AGENTS.md contains loop-aware wording
```
