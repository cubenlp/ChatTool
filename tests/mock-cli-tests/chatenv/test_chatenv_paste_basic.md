# chatenv paste basic

## Case 1: paste should import `chatenv cat --no-mask` output into active typed env

### 初始环境准备

- 创建临时 `CHATTOOL_ENV_DIR` 与 `CHATTOOL_ENV_FILE`。
- 注册 `MockOpenAIConfig` 与 `MockFeishuConfig`，字段包含普通值和敏感值。
- 准备一段形如 `chatenv cat -t mock --no-mask` 的文本：`KEY='VALUE'`。

### 预期过程和结果

- 执行 `chatenv paste --stdin --yes`，输入内容使用 `chatenv cat --no-mask` 风格文本。
- 输出 summary 应包含识别到的配置类型与 key；敏感字段值应被 mask。
- 写入 `envs/MockOpenAI/.env` 与 `envs/MockFeishu/.env`。
- 未出现在 paste 文本中的同类型字段保留当前 active 值或默认值。

### 参考执行脚本（伪代码）

```sh
prepare temp env dir and register mock configs
run chatenv paste --stdin --yes with "MOCK_OPENAI_KEY='sk-one'\nMOCK_FEISHU_SECRET='secret-one'" as stdin
assert active env files exist
assert secret is persisted in file but masked in output
```

## Case 2: paste profile should write same profile name for all matched types

### 初始环境准备

- 创建临时 `CHATTOOL_ENV_DIR` 与 `CHATTOOL_ENV_FILE`。
- 注册 `MockOpenAIConfig` 与 `MockFeishuConfig`。
- 准备 active `.env` 文件作为 profile 基础值。
- 准备 paste 文本命中两个配置类型。

### 预期过程和结果

- 执行 `chatenv paste --value <text> --profile work --yes`。
- 写入 `envs/MockOpenAI/work.env` 与 `envs/MockFeishu/work.env`。
- 不修改两个类型的 active `.env`。
- 两个 profile 使用同一个名称 `work.env`。

### 参考执行脚本（伪代码）

```sh
prepare active env files
run chatenv paste --value "MOCK_OPENAI_KEY='sk-one'\nMOCK_FEISHU_APP_ID='cli-one'" --profile work --yes
assert both work.env files exist
assert active .env files unchanged
```

## Case 3: existing profile requires confirmation or `--yes`

### 初始环境准备

- 创建临时 `CHATTOOL_ENV_DIR` 与 `CHATTOOL_ENV_FILE`。
- 注册 `MockOpenAIConfig`。
- 预先创建 `envs/MockOpenAI/work.env`。

### 预期过程和结果

- 执行 `chatenv paste --value <text> --profile work` 且不提供交互确认。
- 命令失败或中断，不覆盖已有 profile。
- 再执行 `chatenv paste --value <text> --profile work --yes`。
- 命令成功并覆盖 `work.env`。

### 参考执行脚本（伪代码）

```sh
prepare existing envs/MockOpenAI/work.env
run chatenv paste --value "MOCK_OPENAI_KEY='sk-new'" --profile work
assert work.env still contains old value
run chatenv paste --value "MOCK_OPENAI_KEY='sk-new'" --profile work --yes
assert work.env contains new value
```

## Case 4: unknown-only paste should not write files

### 初始环境准备

- 创建临时 `CHATTOOL_ENV_DIR` 与 `CHATTOOL_ENV_FILE`。
- 注册 `MockOpenAIConfig`。
- 准备只包含未知 key 的 paste 文本。

### 预期过程和结果

- 执行 `chatenv paste --value "UNKNOWN_KEY='x'" --yes`。
- 命令失败，输出说明没有识别到已注册 key。
- 不创建新的 typed env 文件。

### 参考执行脚本（伪代码）

```sh
run chatenv paste --value "UNKNOWN_KEY='x'" --yes
assert exit code non-zero
assert no active .env file created
```

## Case 5: stdin and value are mutually exclusive

### 初始环境准备

- 创建临时 `CHATTOOL_ENV_DIR` 与 `CHATTOOL_ENV_FILE`。
- 注册 `MockOpenAIConfig`。

### 预期过程和结果

- 执行 `chatenv paste --value "MOCK_OPENAI_KEY='x'" --stdin --yes`。
- 命令失败并提示 `--value` 与 `--stdin` 不能同时使用。

### 参考执行脚本（伪代码）

```sh
run chatenv paste --value "MOCK_OPENAI_KEY='x'" --stdin --yes
assert error mentions mutually exclusive input options
```

## Case 6: terminal transcript prompts should be tolerated

### 初始环境准备

- 创建临时 `CHATTOOL_ENV_DIR` 与 `CHATTOOL_ENV_FILE`。
- 注册 `MockOpenAIConfig`。
- 准备一段包含 shell prompt、`>:` 输入提示、Confirm box 文本和 env 行的终端复制片段。

### 预期过程和结果

- 执行 `chatenv paste --value <terminal transcript> --yes`。
- 解析器应忽略非 env 行，不输出 python-dotenv parse warning。
- 带 `>:` 前缀的 `KEY='VALUE'` 行仍能被识别并写入 active typed env。

### 参考执行脚本（伪代码）

```sh
run chatenv paste --value ">: MOCK_OPENAI_KEY='sk-one'\n╭ Confirm ╮\nContinue [y/N] y" --yes
assert active .env contains MOCK_OPENAI_KEY
assert output does not contain parse warning
```

## Case 7: interactive paste can choose a profile name

### 初始环境准备

- 创建临时 `CHATTOOL_ENV_DIR` 与 `CHATTOOL_ENV_FILE`。
- 注册 `MockOpenAIConfig`。
- mock 交互：profile name 输入 `work`，确认写入返回 `True`。

### 预期过程和结果

- 执行 `chatenv paste --value <text>`，不显式传 `--profile` / `--yes`。
- 命令应询问 profile name。
- 输入 `work` 后写入 `envs/MockOpenAI/work.env`，不写 active `.env`。

### 参考执行脚本（伪代码）

```sh
mock profile prompt returns work
mock confirm returns yes
run chatenv paste --value "MOCK_OPENAI_KEY='sk-one'"
assert envs/MockOpenAI/work.env contains MOCK_OPENAI_KEY
```

## Case 8: `-I` should disable paste prompts

### 初始环境准备

- 创建临时 `CHATTOOL_ENV_DIR` 与 `CHATTOOL_ENV_FILE`。
- 注册 `MockOpenAIConfig`。

### 预期过程和结果

- 执行 `chatenv paste -I`，不传 `--value` 或 `--stdin`。
- 命令应失败并提示需要 `--value` 或 `--stdin`，不能进入交互式粘贴。

### 参考执行脚本（伪代码）

```sh
run chatenv paste -I
assert output mentions --value or --stdin
```
