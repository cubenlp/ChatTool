# chattool setup nodejs basic

## Case 1: default shell detection should update all detected rc files

### 初始环境准备

- 在非交互环境下执行 `chattool setup nodejs`。
- mock 当前机器未安装可用的 Node.js，且 `which zsh` 与 `which bash` 都存在。
- 使用临时 HOME，避免污染真实 `~/.nvm`、`.zshrc` 和 `.bashrc`。

### 预期过程和结果

- 命令应写入内置 `nvm.sh` 到 `~/.nvm/nvm.sh`。
- 命令应同时更新 `.zshrc` 和 `.bashrc`，写入同一段 ChatTool 管理的 nvm 初始化块。
- 安装完成后应输出 Node.js 与 npm 版本信息。

### 参考执行脚本（伪代码）

```sh
mock node runtime as missing
mock zsh and bash both available
run chattool setup nodejs with temp HOME
assert ~/.nvm/nvm.sh exists
assert ~/.zshrc and ~/.bashrc contain chattool nvm block
assert output includes node and npm version
```

## Case 2: `setup nodejs --log-level DEBUG` should configure staged logger level

### 初始环境准备

- mock 掉后续 Node.js 安装链路，仅校验 logger 初始化参数。

### 预期过程和结果

- 执行 `chattool setup nodejs --log-level DEBUG -I`。
- 命令应接受 `-l/--log-level`。
- 内部 logger 应按 `DEBUG` 级别初始化。

### 参考执行脚本（伪代码）

```sh
stub setup logger and stop command early
run chattool setup nodejs --log-level DEBUG -I
assert logger is configured with DEBUG
```
