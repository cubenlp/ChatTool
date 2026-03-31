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
