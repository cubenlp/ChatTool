# chattool setup zsh basic

## Case 1: setup zsh writes managed alias files safely

### 初始环境准备

- 设置临时 `HOME`，模拟系统已存在 `zsh`。
- 预置一个已有 `~/.zshrc`。
- 执行 `chattool setup zsh --no-omz -I`。

### 预期过程和结果

- 命令应创建或更新 `~/.zsh_aliases` 的 ChatTool managed block。
- `.zsh_aliases` 应包含 QuickSetup 当前 `scripts/config/zsh_aliases` 风格内容，例如 `copy`、`c7`、`pypip`，并追加 ChatTool alias。
- 命令应在 `~/.zshrc` 中追加 source `.zsh_aliases` 的 managed block，同时保留原有内容。
- 默认会在 `~/.bash_profile` 写入 zsh login handoff 的 managed block。
- 重复执行不会产生重复 managed block。

### 参考执行脚本（伪代码）

```sh
set HOME to tmp dir
write ~/.zshrc with existing content
mock which zsh exists
run chattool setup zsh --no-omz -I twice
assert ~/.zsh_aliases has one chattool zsh aliases block
assert ~/.zshrc has existing content and one alias source block
assert ~/.bash_profile has one zsh login block
```

## Case 2: missing zsh should fail with apt hint

### 初始环境准备

- 模拟系统存在 `git` 但不存在 `zsh`。
- 执行 `chattool setup zsh --no-omz --no-aliases -I`。

### 预期过程和结果

- 命令应失败并提示 `sudo apt install zsh -y`。
- 命令不应尝试执行安装命令；系统依赖由用户自行安装。

### 参考执行脚本（伪代码）

```sh
mock which git exists and zsh missing
run chattool setup zsh --no-omz --no-aliases -I
assert exit code is non-zero
assert output includes sudo apt install zsh -y
```

## Case 3: missing git should fail with apt hint when omz is enabled

### 初始环境准备

- 模拟系统存在 `zsh` 但不存在 `git`。
- 执行 `chattool setup zsh --no-aliases --no-login-shell -I`。

### 预期过程和结果

- 命令应失败并提示 `sudo apt install git -y`。
- 命令不应尝试执行安装命令。

### 参考执行脚本（伪代码）

```sh
mock which zsh exists and git missing
run chattool setup zsh --no-aliases --no-login-shell -I
assert exit code is non-zero
assert output includes sudo apt install git -y
```

## Case 4: default mode should not prompt for plugin candidates

### 初始环境准备

- 模拟当前终端可交互，但命令没有传 `-i`。
- 执行 `chattool setup zsh --no-aliases --no-login-shell`。

### 预期过程和结果

- 命令不应打开 oh-my-zsh plugin 候选框。
- 命令应使用脚本同款默认插件集合。

### 参考执行脚本（伪代码）

```sh
mock interactive tty available
run chattool setup zsh --no-aliases --no-login-shell
assert plugin checkbox was not called
assert selected plugins equal all script plugins
```

## Case 5: `-i` should prompt for setup options before plugin candidates

### 初始环境准备

- 模拟当前终端可交互，并执行 `chattool setup zsh --no-aliases --no-login-shell -i`。
- 命令应先展示基础配置项候选框；因为显式传了 `--no-aliases --no-login-shell`，默认只预勾选 `omz`。
- mock setup options 保留 `omz`，plugin 候选框只保留 `git` 和 `zsh-autosuggestions`。

### 预期过程和结果

- 命令应先打开 `Select zsh setup options` 候选框，再打开 `Select oh-my-zsh plugins` 候选框。
- 候选框默认值应包含 QuickSetup 脚本同款插件：`git`、`sudo`、`z`、`zsh-syntax-highlighting`、`zsh-autosuggestions`、`zsh-completions`。
- 传给 oh-my-zsh 配置步骤的插件只包含用户勾选项。

### 参考执行脚本（伪代码）

```sh
mock interactive tty available
run chattool setup zsh --no-aliases --no-login-shell -i
assert checkbox default values include all script plugins
assert selected plugins equal git and zsh-autosuggestions
```


## Case 6: `-i` should show base options with current defaults

### 初始环境准备

- 模拟当前终端可交互，并执行 `chattool setup zsh -i`。
- mock 基础配置项候选框只保留 `aliases` 和 `login_shell`，不保留 `omz`。

### 预期过程和结果

- 第一个候选框应为 `Select zsh setup options`。
- 默认值应包含基础参数当前默认值：`omz`、`aliases`、`login_shell`。
- 取消 `omz` 后不应继续进入 oh-my-zsh plugin 候选框。

### 参考执行脚本（伪代码）

```sh
mock interactive tty available
run chattool setup zsh -i
assert setup options checkbox default values are omz, aliases, login_shell
uncheck omz
assert plugin checkbox is not shown
```
