# Mock CLI Tests

`mock-cli-tests/` 用于收纳 ChatTool 仓库内所有基于 mock 的 CLI 测试。

## 定位

- `cli-tests/`：真实 CLI 链路、真实环境、真实外部依赖验收。
- `mock-cli-tests/`：CLI 编排、参数流向、输出格式、懒加载、交互分支验证。

两者都采用 doc-first，但职责不同，不应混放。

## 什么时候放到 `mock-cli-tests/`

- 使用了 `unittest.mock`
- 使用了 `pytest.monkeypatch`
- 通过 fake client / fake API / fake response 驱动 CLI
- 只想验证 CLI 入口编排，而不是验证真实外部服务

## 什么时候不要放到 `mock-cli-tests/`

- 需要真实网络、真实第三方凭证、真实远端资源
- 需要确认 `chatenv` 默认配置在真实链路下是否生效
- 需要把测试结果当成最终验收依据

这些场景应继续写到 `cli-tests/`。

## 目录规则

- 先写 `mock-cli-tests/<group>/test_<...>.md`
- 文档评审通过后再补同名 `.py`
- 命名沿用当前 CLI 命令名
- mock 目标尽量收敛在 CLI 入口层依赖，避免把内部业务全部重写成另一套假实现

## 当前迁移原则

- 历史上散落在 `cli-tests/` 的 mock CLI 测试，统一迁入 `mock-cli-tests/`
- 新增 mock CLI 测试时，不再写进 `cli-tests/`
