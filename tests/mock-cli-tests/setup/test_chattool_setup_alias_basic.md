# chattool setup alias basic

## Case 1: `setup alias --dry-run` should use shared multi-select controls

### 初始环境准备

- 在交互测试环境下执行 `chattool setup alias --dry-run`。
- 不实际写入 shell rc 文件。

### 预期过程和结果

- 命令应进入共享的多选控制页，而不是先进入单独的 preset 选择页。
- 通过控制页返回自定义 alias 集合后，dry-run 输出应只包含这些 alias。
- alias 列表中应包含 `chattp => chattool tplogin`。

### 参考执行脚本（伪代码）

```sh
run chattool setup alias --dry-run in pty
use multi-select controls to keep chatenv and chatskill
assert dry-run output only contains chatenv and chatskill
```

## Case 2: default shell detection should update all detected shells

### 初始环境准备

- 在非交互或 dry-run 环境下执行 `chattool setup alias --dry-run`。
- mock `which zsh` 和 `which bash` 都存在。

### 预期过程和结果

- 不传 `--shell` 时，不应要求用户输入 shell。
- 命令应自动选择所有已探测到的 shell。
- dry-run 输出应同时包含 `.zshrc` 和 `.bashrc` 两个目标文件。

### 参考执行脚本（伪代码）

```sh
mock zsh and bash both available
run chattool setup alias --dry-run
assert output includes .zshrc and .bashrc
```

## Case 3: interactive shell selection should limit target rc files

### 初始环境准备

- 在交互测试环境下执行 `chattool setup alias --dry-run`。
- mock shell 选择页只保留 `bash`，随后 alias 选择页只保留 `chatenv`。

### 预期过程和结果

- 命令应先进入 shell 选择页，再进入 alias 多选页。
- dry-run 输出只应包含 `.bashrc`，不应包含 `.zshrc`。
- alias 输出只应包含 `chatenv => chattool env`。

### 参考执行脚本（伪代码）

```sh
run chattool setup alias --dry-run in pty
use shell multi-select to keep bash only
use alias multi-select to keep chatenv only
assert output includes .bashrc but not .zshrc
assert output includes chatenv => chattool env
```
