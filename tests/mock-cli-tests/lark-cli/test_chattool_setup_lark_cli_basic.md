# chattool setup lark-cli basic

## Case 1: existing lark-cli config should win over current Feishu env defaults when `-e` is not provided

### 初始环境准备

- 准备临时 `LARKSUITE_CLI_CONFIG_DIR`，写入已有 `config.json`。
- 同时设置当前 Feishu 环境变量为另一组值。
- mock 掉 Node.js 检查、npm 安装与 `lark-cli config init` 调用。

### 预期过程和结果

- 执行 `chattool setup lark-cli -I`。
- `lark-cli config init` 应优先使用已有配置值，而不是被当前环境变量覆盖。

### 参考执行脚本（伪代码）

```sh
prepare temp lark-cli config dir with existing config.json
set FEISHU_APP_ID FEISHU_APP_SECRET FEISHU_API_BASE to different values
stub node/npm and lark-cli init calls
run chattool setup lark-cli -I
assert lark-cli init uses existing config values
```

## Case 2: `--log-level` should be forwarded to Node.js requirement checks

### 初始环境准备

- mock 掉 Node.js 检查函数，记录收到的 `log_level`。
- mock 掉 npm 安装与 `lark-cli` 初始化。

### 预期过程和结果

- 执行 `chattool setup lark-cli -I --log-level DEBUG --app-id ... --app-secret ...`。
- `ensure_nodejs_requirement()` 应收到 `log_level="DEBUG"`。

### 参考执行脚本（伪代码）

```sh
stub ensure_nodejs_requirement and record log_level
run chattool setup lark-cli -I --log-level DEBUG with explicit values
assert ensure_nodejs_requirement received DEBUG
```
