# chattool skill basic

## Case 1: `skill install` should prompt when skill name is missing

### 初始环境准备

- 创建临时 skills 源目录，并放入两个最小 skill：`alpha`、`beta`。
- 为目标平台准备临时 home 目录，避免污染真实 `~/.codex/skills`。
- 在交互测试环境下执行 `chattool skill install`，不传 skill 名和 `--all`。

### 预期过程和结果

- 命令应进入选择页，而不是直接报 `Missing skill name`。
- 选择 `alpha` 后，应成功安装到目标 skills 目录。

### 参考执行脚本（伪代码）

```sh
prepare temp skills source with alpha and beta
run chattool skill install in pty
choose alpha
assert target skills dir contains alpha
```
