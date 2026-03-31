# chatenv new semantics

## Case 1: `chatenv new` should only create profile

### 初始环境准备

- 创建临时 `CHATTOOL_ENV_DIR` 与 `CHATTOOL_ENV_FILE`。
- 注册一个最小 `MockConfig`，包含 `MOCK_KEY`。
- 在 active typed env `envs/Mock/.env` 中写入 `MOCK_KEY='active_value'`。

### 预期过程和结果

- 执行 `chatenv new snapshot -t mock`。
- 应生成 `envs/Mock/snapshot.env`，内容与当前 active 配置一致。
- `envs/Mock/.env` 应保持不变，不应被 `new` 改写。

### 参考执行脚本（伪代码）

```sh
prepare temp env dir and active envs/Mock/.env
run chatenv new snapshot -t mock
assert snapshot.env exists
assert active .env unchanged
```
