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

## Case 2: `--dry-run` should report planned writes without touching filesystem

### 初始环境准备

- 创建临时目录作为 workspace 根目录。

### 预期过程和结果

- 执行 `chattool setup workspace <workspace-dir> --dry-run -I`。
- 输出应包含 dry-run 摘要。
- 目录内不应出现生成文件。

### 参考执行脚本（伪代码）

```sh
run chattool setup workspace /tmp/workspace --dry-run -I
assert output mentions dry run
assert no generated files exist
```
