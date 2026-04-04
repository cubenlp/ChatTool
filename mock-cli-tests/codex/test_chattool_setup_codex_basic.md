# chattool setup codex basic

## Case 1: existing Codex config should win over current env defaults when `-e` is not provided

### 初始环境准备

- 准备临时 HOME，并写入已有 `~/.codex/config.toml` 与 `~/.codex/auth.json`。
- 同时设置 `OPENAI_API_BASE`、`OPENAI_API_KEY`、`OPENAI_API_MODEL` 环境变量为另一组值。
- mock 掉 Node.js 检查与 npm 安装判断。

### 预期过程和结果

- 执行 `chattool setup codex -I`。
- 写出的 `config.toml` 与 `auth.json` 应优先复用已有 Codex 配置，而不是被当前环境变量覆盖。

### 参考执行脚本（伪代码）

```sh
prepare temp HOME with existing codex config and auth
set OPENAI_API_BASE OPENAI_API_KEY OPENAI_API_MODEL to different values
stub node/npm related checks
run chattool setup codex -I
assert config.toml and auth.json keep existing codex values
```

## Case 2: explicit args should override `-e` values

### 初始环境准备

- 准备临时 `CHATTOOL_ENV_DIR` 与 `envs/OpenAI/work.env`。
- mock 掉 Node.js 检查与 npm 安装判断。

### 预期过程和结果

- 执行 `chattool setup codex -I -e work --pam ... --base-url ... --model ...`。
- 写出的配置应使用显式参数，而不是 `-e` 配置。

### 参考执行脚本（伪代码）

```sh
prepare temp OpenAI work.env
run chattool setup codex -I -e work with explicit args
assert written codex config uses explicit values
```
