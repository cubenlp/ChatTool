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

### 参考执行脚本（伪代码）

```sh
run chattool setup workspace /tmp/workspace --language en -I
assert AGENTS.md contains English headings
```

## Case 4: interactive extra repos should prompt repo tokens separately

### 初始环境准备

- 在 mock CLI 环境下调用 `chattool setup workspace`。
- 交互中启用 `chattool` 和 `rexblog` 两个额外模块。
- mock 当前仓库 `.git-credential` 中已存在 GitHub token。

### 预期过程和结果

- 选择额外模块后，应分别提示是否为 `ChatTool` 和 `RexBlog` 配置 GitHub token。
- token 默认值应来自当前仓库对应的 git credential，并以 mask 形式展示在输入标签中。
- 若确认配置，应在 clone 前为对应 repo path 调用 GitHub HTTPS credential 配置。

### 参考执行脚本（伪代码）

```sh
mock current repo credential token -> github_pat_xxx
run chattool setup workspace
assert prompts mention chatgh set-token for ChatTool and RexBlog
assert configure_github_https_token called for cubenlp/ChatTool.git and RexWzh/RexBlog
```
