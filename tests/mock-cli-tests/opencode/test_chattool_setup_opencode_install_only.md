# `chattool setup opencode --install-only`

## Case 1: install-only should install or upgrade CLI without writing config

### 初始环境准备

- 准备临时 HOME。
- mock 掉 Node.js 检查。
- mock 掉 npm 安装判断和执行。

### 预期过程和结果

- 执行 `chattool setup opencode --install-only -I`。
- 应完成 OpenCode CLI 的安装/升级逻辑。
- 不应写入 `~/.config/opencode/opencode.json`。

### 参考执行脚本（伪代码）

```sh
prepare temp HOME
stub node/npm install checks
run chattool setup opencode --install-only -I
assert no opencode config file is written
```
