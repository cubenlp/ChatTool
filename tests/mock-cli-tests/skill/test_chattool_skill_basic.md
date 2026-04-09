# chattool skill basic

## Case 1: `skill install` should prompt for multi-select when skill name is missing

### 初始环境准备

- 创建临时 skills 源目录，并放入两个最小 skill：`alpha`、`beta`。
- 为目标平台准备临时 home 目录，避免污染真实 `~/.codex/skills`。
- 在交互测试环境下执行 `chattool skill install`，不传 skill 名和 `--all`。

### 预期过程和结果

- 命令应进入多选控制页，而不是直接报 `Missing skill name`。
- 选择 `alpha` 后，应成功安装到目标 skills 目录。

### 参考执行脚本（伪代码）

```sh
prepare temp skills source with alpha and beta
run chattool skill install in pty
select alpha and apply current selection
assert target skills dir contains alpha
```

## Case 1.5: `skill install` should prompt for platform before skill when `-p` is omitted

### 初始环境准备

- 创建临时 skills 源目录，并放入一个最小 skill：`alpha`。
- 不传 `-p/--platform`，也不设置 `CHATTOOL_SKILL_PLATFORM`。
- 在交互测试环境下执行 `chattool skill install`。

### 预期过程和结果

- 命令应先进入平台选择页，再进入 skills 多选控制页。
- 选择 `opencode` 与 `alpha` 后，应安装到 `~/.config/opencode/skills/alpha/`。

### 参考执行脚本（伪代码）

```sh
prepare temp HOME and skills source with alpha
run chattool skill install in pty without -p
choose opencode
select alpha and apply current selection
assert ~/.config/opencode/skills/alpha/SKILL.md exists
```

## Case 2: `skill install -p opencode` should install into global OpenCode skills dir

### 初始环境准备

- 创建临时 HOME 目录，避免污染真实 `~/.config/opencode/skills`。
- 创建一个最小 skill：`alpha`。

### 预期过程和结果

- 执行 `chattool skill install alpha -p opencode --source <dir>`。
- skill 应安装到 `~/.config/opencode/skills/alpha/`。

### 参考执行脚本（伪代码）

```sh
prepare temp HOME and skills source with alpha
run chattool skill install alpha -p opencode --source <dir>
assert ~/.config/opencode/skills/alpha/SKILL.md exists
```

## Case 3: `skill install -p claude` should install into Claude skills dir

### 初始环境准备

- 创建临时 `CLAUDE_HOME`，避免污染真实 `~/.claude/skills`。
- 创建一个最小 skill：`beta`。

### 预期过程和结果

- 执行 `chattool skill install beta -p claude --source <dir>`。
- skill 应安装到 `CLAUDE_HOME/skills/beta/`。

### 参考执行脚本（伪代码）

```sh
prepare temp skills source with beta
set CLAUDE_HOME to temp directory
run chattool skill install beta -p claude --source <dir>
assert $CLAUDE_HOME/skills/beta/SKILL.md exists
```

## Case 4: `skill install` overwrite prompt should support `a` for all

### 初始环境准备

- 创建临时 skills 源目录，包含 `alpha`、`beta` 两个 skill。
- 预先在目标目录写入同名旧 skill。
- 在交互测试环境下执行 `chattool skill install --all`。

### 预期过程和结果

- 第一次覆盖提示输入 `a` 后，不再为后续已存在 skill 逐个确认。
- 两个目标 skill 都应被源目录内容覆盖。

### 参考执行脚本（伪代码）

```sh
prepare temp source and dest with existing alpha beta
run chattool skill install --all --source <dir> --dest <dir> in pty
enter a on first overwrite prompt
assert alpha and beta were replaced from source
```
