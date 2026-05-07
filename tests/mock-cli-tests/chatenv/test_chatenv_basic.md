# chatenv basic

## Case 1: active typed env should override shell env in `chatenv cat`

### 初始环境准备

- 创建临时 `CHATARCH_ENV_DIR` 与 `CHATARCH_ENV_FILE`。
- 注册一个最小 `MockConfig`，包含 `MOCK_KEY`。
- 在 typed env `envs/Mock/.env` 中写入 `MOCK_KEY='from_file'`。
- 同时在当前进程环境变量中设置 `MOCK_KEY=from_env`。

### 预期过程和结果

- 执行 `chatenv cat -t mock`。
- 输出应展示 typed env 中的 `MOCK_KEY='from_file'`，而不是 shell 环境变量中的 `from_env`。
- 这样可以验证 `chatenv init/new` 刚写入的 active `.env` 会立刻成为当前生效值，不会被已有 shell 环境变量覆盖。

### 参考执行脚本（伪代码）

```sh
prepare temp env dir and register MockConfig
write envs/Mock/.env with MOCK_KEY='from_file'
export MOCK_KEY=from_env
run chatenv cat -t mock
assert output contains MOCK_KEY='from_file'
```

## Case 2: profile and key commands should auto-prompt on missing args

### 初始环境准备

- 创建临时 `CHATARCH_ENV_DIR` 与 `CHATARCH_ENV_FILE`。
- 注册一个最小 `MockConfig`，包含 `MOCK_KEY`。
- mock 交互输入与 profile/config 文件写入。

### 预期过程和结果

- 执行 `chatenv save -t mock`、`use -t mock`、`delete -t mock`、`get`、`unset`、`set`。
- 执行 `chatenv test` 时，缺少 `--target` 也应自动补问。
- 在交互终端下，缺少 `name` / `key` / `KEY=VALUE` 时应自动补问。
- 加 `-I` 时应直接报缺少必要参数。

## Case 3: OpenAI config test should prefer Responses API

### 初始环境准备

- 注册真实 `OpenAIConfig`。
- 设置 `OPENAI_API_BASE`、`OPENAI_API_KEY`、`OPENAI_API_MODEL`。
- mock `httpx.Client.stream`，模拟 `/responses` 成功返回 `response.output_text.delta` SSE 事件。

### 预期过程和结果

- 执行 `chatenv test -t oai`。
- 命令应请求 `<OPENAI_API_BASE>/responses`，请求体包含 `input` 和 `max_output_tokens`。
- 输出应显示 `Responses API generated` 成功，而不是走 `/chat/completions`。

### 参考执行脚本（伪代码）

```sh
mock httpx responses endpoint
run chatenv test -t oai
assert posted url ends with /responses
assert output contains Responses API
```
