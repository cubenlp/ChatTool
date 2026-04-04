# test_chattool_setup_playground_mock_basic

## Case 1: missing workspace args should trigger interactive prompt

### 初始环境准备

- 在 mock CLI 环境下调用 `chattool setup playground`，不提供 `workspace_dir` 和 `chattool_source`。
- stub 掉文本输入，避免真实 TTY 依赖。

### 预期过程和结果

- 命令应进入工作区路径和 source 补全流程，而不是直接报缺参。
- 给出路径和 source 后，应调用 playground setup 主逻辑并写出生成文件。

### 参考执行脚本（伪代码）

```sh
mock ask_text -> /tmp/workspace, /tmp/source
run chattool setup playground
assert setup completed with generated files
```
