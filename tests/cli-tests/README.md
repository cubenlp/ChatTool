# CLI Tests 规范

本文档定义 ChatTool 仓库内真实 CLI 测试的长期维护规则。

## 关键要求

- `tests/cli-tests/*.md` 是真实 CLI 测试的长期维护设计面。
- `tests/cli-tests/*.py` 只作为对应 `.md` 的真实 CLI 执行实现。
- 文档先行：每个命令先落 `.md`，再决定是否补 `.py`。
- 真实链路：以真实 CLI 链路为准；对应 `.py` 应标记 `@pytest.mark.e2e`。
- 所有 mock CLI 测试统一放到 `tests/mock-cli-tests/`，不要继续混入 `tests/cli-tests/`。
- GitHub 自动测试当前只跑 `.github/workflows/ci.yml` 里的 stable smoke tests，不包含 `lark` / `dns` 与大多数真实链路用例；相关 `.md` / `.py` 需要本地单独执行。
- 模板一致：以 `tests/cli-tests/env/test_chattool_env_basic.md` 为模板。
- `tests/code-tests/` 只承接代码测试与历史迁移，不再作为新的 CLI 测试维护面。

## 长期规则

- 没有对应 `.md` 的 CLI 测试实现不应新增。
- 新功能、重构和 Bugfix 如涉及 CLI 行为，必须先补对应 `tests/cli-tests/<group>/test_<...>.md`。
- 评审、验收与回归优先查看 `.md`，而不是先看 `.py`。
- `tests/code-tests/` 中的旧测试：
  - 不作为新规范样例。
  - 不作为评审验收依据。
  - 仅在迁移到 `tests/cli-tests/` 时参考其历史行为。

## 目录与模板

- 以 `tests/cli-tests/env/test_chattool_env_basic.md` 为模板。
- 每个用例至少包含：
  - 初始环境准备
  - 相关文件
  - 预期过程和结果
  - 参考执行脚本（伪代码）
  - 回滚说明

## 第三方集成要求

- 真实 CLI 测试必须从默认 `chatenv` / 配置对象读取生效值。
- 不允许通过 mock 伪装成真实链路；如需要 mock，请切换到 `tests/mock-cli-tests/`。
- 文档中必须写清需要的配置项、权限和回滚方式。

## Feishu 约束

- Feishu 测试设计统一放到 `tests/cli-tests/lark/<topic>/`；`skills/feishu/` 现在只保留一个入口 `SKILL.md`，不再要求与 skill 子目录逐一对齐。
- Feishu 真实执行测试只能以这些 `tests/cli-tests/lark/<topic>/*.md` 为准；`tests/code-tests/tools/lark/` 中的历史文件不再作为规范依据。
- Feishu 测试文档至少显式列出：`FEISHU_APP_ID`、`FEISHU_APP_SECRET`、`FEISHU_DEFAULT_RECEIVER_ID`、`FEISHU_DEFAULT_CHAT_ID`。
- Feishu 测试文档必须说明回滚策略，例如删除测试消息、删除测试文档，或说明为何保留测试痕迹。
- 对消息相关任务，优先把 `FEISHU_DEFAULT_RECEIVER_ID` 当作默认用户目标，把 `FEISHU_DEFAULT_CHAT_ID` 当作默认群聊目标。
