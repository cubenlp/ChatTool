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

- 执行 `chattool setup codex -I -e work --api-key ... --base-url ... --model ...`。
- 写出的配置应使用显式参数，而不是 `-e` 配置。

### 参考执行脚本（伪代码）

```sh
prepare temp OpenAI work.env
run chattool setup codex -I -e work with explicit args
assert written codex config uses explicit values
```

## Case 3: missing required key should enter interactive flow by default

### 初始环境准备

- 准备临时 HOME，确保不存在已有 `~/.codex/config.toml` 与 `~/.codex/auth.json`。
- 不提供 `OPENAI_API_KEY`。
- mock 掉 Node.js 检查与 npm 安装判断。
- mock 交互输入，依次提供 `OPENAI_API_KEY`、`base_url`、`model`。

### 预期过程和结果

- 执行 `chattool setup codex`。
- 因为缺少必要参数 `OPENAI_API_KEY`，预期默认进入交互式流程。
- 预期按顺序询问：`OPENAI_API_KEY`、`base_url`、`model`。
- 预期根据输入写出 `config.toml` 与 `auth.json`。

### 参考执行脚本（伪代码）

```sh
prepare empty temp HOME
stub node/npm related checks
stub prompt answers for OPENAI_API_KEY, base_url, model
run chattool setup codex
assert prompts happen in expected order
assert config.toml and auth.json are written from prompt answers
```

## Case 4: `-i` should force interactive flow even when values already exist

### 初始环境准备

- 准备临时 HOME，并写入已有 `~/.codex/config.toml` 与 `~/.codex/auth.json`。
- mock 掉 Node.js 检查与 npm 安装判断。
- mock 交互输入，允许覆盖或保留已有值。

### 预期过程和结果

- 执行 `chattool setup codex -i`。
- 即使已有值已足够完成写入，预期也进入交互式流程。
- 预期按顺序询问：`OPENAI_API_KEY`、`base_url`、`model`。
- 如果敏感值 prompt 直接回车，预期保留当前 key。

### 参考执行脚本（伪代码）

```sh
prepare temp HOME with existing codex config and auth
stub node/npm related checks
stub prompt answers including empty answer for API key
run chattool setup codex -i
assert interactive prompts always appear
assert empty API key input keeps existing key
```

## Case 5: `-I` should fail fast when required key is still missing

### 初始环境准备

- 准备临时 HOME，确保没有已有 Codex 配置。
- 不提供 `OPENAI_API_KEY`。
- mock 掉 Node.js 检查与 npm 安装判断。

### 预期过程和结果

- 执行 `chattool setup codex -I`。
- 预期不进入交互。
- 预期直接报错退出。
- 预期输出 usage。

### 参考执行脚本（伪代码）

```sh
prepare empty temp HOME
stub node/npm related checks
run chattool setup codex -I
assert command exits with error
assert no prompt is called
assert usage is shown
```

## Case 6: no TTY should not trigger implicit interactive flow

### 初始环境准备

- 准备临时 HOME，确保没有已有 Codex 配置。
- 不提供 `OPENAI_API_KEY`。
- mock 掉 Node.js 检查与 npm 安装判断。
- mock 当前终端为非交互环境。

### 预期过程和结果

- 执行 `chattool setup codex`。
- 由于当前没有 TTY，预期不进入隐式交互。
- 预期直接报错退出。
- 预期不会调用 prompt。

### 参考执行脚本（伪代码）

```sh
prepare empty temp HOME
stub node/npm related checks
stub non-interactive terminal
run chattool setup codex
assert command exits with error
assert no prompt is called
```

## Case 7: sensitive key prompt should mask current value and keep it on empty input

### 初始环境准备

- 准备临时 HOME，并写入已有 `~/.codex/auth.json`。
- mock 掉 Node.js 检查与 npm 安装判断。
- mock 交互输入，让 `OPENAI_API_KEY` 返回空字符串。

### 预期过程和结果

- 执行 `chattool setup codex -i`。
- 预期 `OPENAI_API_KEY` prompt 带有脱敏后的当前值提示。
- 预期当用户直接回车时，保留当前 key，而不是写成空值。

### 参考执行脚本（伪代码）

```sh
prepare temp HOME with existing codex auth
stub node/npm related checks
stub API key prompt returns empty string
run chattool setup codex -i
assert API key prompt contains masked current value
assert written auth.json keeps existing key
```

## Case 8: interactive defaults should match final written values for base_url and model

### 初始环境准备

- 准备临时 HOME，并写入已有 `~/.codex/config.toml`。
- mock 掉 Node.js 检查与 npm 安装判断。
- mock 交互输入，让 `base_url` 和 `model` 都直接回车使用默认值。

### 预期过程和结果

- 执行 `chattool setup codex -i`。
- 预期 `base_url` prompt 中展示的默认值，与最终写入 `config.toml` 的 `base_url` 一致。
- 预期 `model` prompt 中展示的默认值，与最终写入 `config.toml` 的 `model` 一致。

### 参考执行脚本（伪代码）

```sh
prepare temp HOME with existing codex config
stub node/npm related checks
stub prompts so base_url and model accept defaults
run chattool setup codex -i
assert shown defaults for base_url and model match final written config.toml
```
