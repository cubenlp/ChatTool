# CLI Tests 规范

本文档定义 ChatTool 仓库内 CLI 测试的长期维护规则。

## 关键要求

- `cli-tests/*.md` 是唯一长期维护的测试设计面。
- `cli-tests/*.py` 只作为对应 `.md` 的真实 CLI 执行实现。
- 文档先行：每个命令先落 `.md`，再决定是否补 `.py`。
- 真实链路：以真实 CLI 链路为准；对应 `.py` 应标记 `@pytest.mark.e2e`。
- 绝对禁止 mock：宁可缩小测试范围，也不能使用 mock 伪造行为。
- 模板一致：以 `cli-tests/env/test_chattool_env_basic.md` 为模板。
- 仓库根下 `tests/` 为弃用区，仅保留历史参考，不再作为新开发默认维护面。

## 长期规则

- 没有对应 `.md` 的 CLI 测试实现不应新增。
- 新功能、重构和 Bugfix 如涉及 CLI 行为，必须先补对应 `cli-tests/<group>/test_<...>.md`。
- 评审、验收与回归优先查看 `.md`，而不是先看 `.py`。
- 旧的 `tests/` 文件：
  - 不作为新规范样例。
  - 不作为评审验收依据。
  - 仅在迁移到 `cli-tests/` 时参考其历史行为。

## 目录与模板

- 以 `cli-tests/env/test_chattool_env_basic.md` 为模板。
- 每个用例至少包含：
  - 初始环境准备
  - 相关文件
  - 预期过程和结果
  - 参考执行脚本（伪代码）
  - 回滚说明

## 第三方集成要求

- 真实 CLI 测试必须从默认 `chatenv` / 配置对象读取生效值。
- 不允许通过 mock 伪装成真实链路；如环境复杂，优先收窄测试目标或补更明确的前置条件。
- 文档中必须写清需要的配置项、权限和回滚方式。

## Feishu 约束

- Feishu 测试设计统一放到 `cli-tests/lark/<topic>/`，目录应尽量和 `skills/feishu/<topic>/` 的主题划分对应，例如 `guide/`、`messaging/`、`documents/`、`im/`、`troubleshoot/`、`task/`、`calendar/`、`bitable/`。
- Feishu 真实执行测试只能以这些 `cli-tests/lark/<topic>/*.md` 为准；`tests/tools/lark/` 中的历史文件不再作为规范依据。
- Feishu 测试文档至少显式列出：`FEISHU_APP_ID`、`FEISHU_APP_SECRET`、`FEISHU_DEFAULT_RECEIVER_ID`、`FEISHU_TEST_USER_ID`、`FEISHU_TEST_USER_ID_TYPE`。
- Feishu 测试文档必须说明回滚策略，例如删除测试消息、删除测试文档，或说明为何保留测试痕迹。
- 对消息相关任务，优先把 `FEISHU_DEFAULT_RECEIVER_ID` 当作默认测试目标；`FEISHU_TEST_USER_ID` 只在需要隔离真实测试用户时再单独指定。
