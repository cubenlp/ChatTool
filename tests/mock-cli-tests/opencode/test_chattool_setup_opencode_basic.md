# chattool setup opencode basic

## Case 1: `setup opencode -e` should reuse OpenAI profile values

### 初始环境准备

- 创建临时 `CHATTOOL_ENV_DIR` 与 `CHATTOOL_ENV_FILE`。
- 在 `envs/OpenAI/work.env` 中写入 `OPENAI_API_BASE`、`OPENAI_API_KEY`、`OPENAI_API_MODEL`。
- 准备临时 HOME 目录，避免污染真实 `~/.config/opencode/opencode.json`。
- mock 掉 Node.js 检查与 npm 安装判断，让测试只验证参数流与配置写入。

### 预期过程和结果

- 执行 `chattool setup opencode -I -e work`。
- 命令应成功完成，并打印 `Reused ChatTool OpenAI config: work`。
- 写出的 `opencode.json` 应包含 profile 中的 `baseURL`、`apiKey` 和默认 `model`。

### 参考执行脚本（伪代码）

```sh
prepare temp HOME and ChatTool OpenAI profile work.env
stub node/npm related checks
run chattool setup opencode -I -e work
assert opencode.json contains profile base url api key model
```

## Case 2: existing OpenCode config should win over current env defaults when `-e` is not provided

### 初始环境准备

- 准备临时 HOME，并写入已有 `~/.config/opencode/opencode.json`。
- 同时设置 `OPENAI_API_BASE`、`OPENAI_API_KEY`、`OPENAI_API_MODEL` 环境变量为另一组值。
- mock 掉 Node.js 检查与 npm 安装判断。

### 预期过程和结果

- 执行 `chattool setup opencode -I`。
- 命令应优先复用已有 `opencode.json`，而不是被当前环境变量覆盖。

### 参考执行脚本（伪代码）

```sh
prepare temp HOME with existing opencode.json
set OPENAI_API_BASE OPENAI_API_KEY OPENAI_API_MODEL to different values
stub node/npm related checks
run chattool setup opencode -I
assert written opencode.json keeps existing config values
```

## Case 3: explicit args should override `-e` values

### 初始环境准备

- 准备临时 `CHATTOOL_ENV_DIR` 与 `envs/OpenAI/work.env`。
- mock 掉 Node.js 检查与 npm 安装判断。

### 预期过程和结果

- 执行 `chattool setup opencode -I -e work --base-url ... --api-key ... --model ...`。
- 写出的 `opencode.json` 应使用显式参数，而不是 `-e` 配置。

### 参考执行脚本（伪代码）

```sh
prepare temp OpenAI work.env
run chattool setup opencode -I -e work with explicit args
assert written opencode.json uses explicit values
```

## Case 4: plugin option should add `opencode-auto-loop` to OpenCode config

### 初始环境准备

- 准备临时 HOME，并写入已有 `~/.config/opencode/opencode.json` 基础配置。
- mock 掉 Node.js 检查与 npm 安装判断。

### 预期过程和结果

- 执行 `chattool setup opencode -I --base-url ... --api-key ... --model ... --plugin auto-loop`。
- 命令应成功完成。
- 写出的 `opencode.json` 应保留原有 provider/model 配置。
- 同时应新增 `plugin` 数组，并包含 `opencode-auto-loop`。

### 参考执行脚本（伪代码）

```sh
prepare temp HOME with existing opencode.json
stub node/npm related checks
run chattool setup opencode -I --base-url ... --api-key ... --model ... --plugin auto-loop
assert written opencode.json contains plugin entry opencode-auto-loop
```

## Case 5: interactive setup should offer plugin checklist selection

### 初始环境准备

- 准备临时 HOME。
- mock 掉 Node.js 检查与 npm 安装判断。
- mock 交互输入，让 `base_url`、`api_key`、`model` 直接沿用默认值，并在 `plugins` 多选列表中勾选 `auto-loop`。

### 预期过程和结果

- 执行 `chattool setup opencode`。
- 命令在 `base_url`、`api_key`、`model` 之后，应继续显示 `plugins` 多选列表。
- 勾选 `auto-loop` 后，写出的 `opencode.json` 应包含 `plugin: ["opencode-auto-loop"]`。

### 参考执行脚本（伪代码）

```sh
prepare temp HOME
stub node/npm related checks
stub prompts for base_url api_key model and plugins checkbox selection
run chattool setup opencode
assert written opencode.json contains plugin entry opencode-auto-loop
```

## Case 6: install-only should install or upgrade CLI without writing config

### 初始环境准备

- 准备临时 HOME。
- mock 掉 Node.js 检查与 npm 安装判断。

### 预期过程和结果

- 执行 `chattool setup opencode --install-only -I`。
- 命令应成功完成。
- 不应写入 `~/.config/opencode/opencode.json`。

### 参考执行脚本（伪代码）

```sh
prepare temp HOME
stub node/npm install checks
run chattool setup opencode --install-only -I
assert no opencode config file is written
```
