# Mock CLI Tests 规范

本文档定义 ChatTool 仓库内 mock CLI 测试的长期维护规则。

## 关键要求

- `tests/mock-cli-tests/*.md` 是 mock CLI 测试的长期维护设计面。
- `tests/mock-cli-tests/*.py` 是对应 `.md` 的 mock CLI 执行实现。
- 文档先行：每个 mock CLI 用例先落 `.md`，再决定是否补 `.py`。
- 所有基于 `mock`、`patch`、`monkeypatch`、fake client、fake API 的 CLI 测试都必须收纳到 `tests/mock-cli-tests/`。
- `tests/mock-cli-tests/` 只验证 CLI 编排、参数传递、输出格式、懒加载和交互分支，不把它当成真实链路验收。
- 真实 CLI 链路继续留在 `tests/cli-tests/`；需要外部服务、真实配置或真实远端资源的测试，不要放到 `tests/mock-cli-tests/`。
- `tests/code-tests/` 为代码测试与历史参考区，不再作为新 mock CLI 测试的默认落点。

## 长期规则

- 没有对应 `.md` 的 mock CLI 测试实现不应新增。
- 新功能、重构和 Bugfix 如需用 mock 验证 CLI 编排行为，必须先补对应 `tests/mock-cli-tests/<group>/test_<...>.md`。
- 评审、验收与回归时，要明确区分：
  - `tests/cli-tests/` 看真实链路是否成立。
  - `tests/mock-cli-tests/` 看编排层是否稳定、输出是否可控。

## 目录与模板

- 以 `tests/mock-cli-tests/client/test_chattool_client_dispatch_basic.md` 为模板。
- 每个用例至少包含：
  - 初始环境准备
  - 相关文件
  - 预期过程和结果
  - 参考执行脚本（伪代码）
  - 回滚说明

## 使用边界

- 允许使用 `unittest.mock`、`pytest.monkeypatch`、fake class、fake response。
- mock 目标应尽量收敛在 CLI 入口层依赖，不要把内部实现细节重写成另一套业务。
- 需要验证真实网络、真实第三方配置、真实远端资源时，应切回 `tests/cli-tests/`。
