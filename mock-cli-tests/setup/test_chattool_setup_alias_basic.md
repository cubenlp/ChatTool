# chattool setup alias basic

## Case 1: `setup alias --dry-run` should use shared multi-select controls

### 初始环境准备

- 在交互测试环境下执行 `chattool setup alias --dry-run`。
- 不实际写入 shell rc 文件。

### 预期过程和结果

- 命令应进入共享的多选控制页，而不是先进入单独的 preset 选择页。
- 通过控制页返回自定义 alias 集合后，dry-run 输出应只包含这些 alias。

### 参考执行脚本（伪代码）

```sh
run chattool setup alias --dry-run in pty
use multi-select controls to keep chatenv and chatskill
assert dry-run output only contains chatenv and chatskill
```
