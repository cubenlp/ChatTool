# CLI Tests 迁移计划

本文档记录从 `tests/` 迁移到 `cli-tests/` 的执行顺序与阶段安排。

## 关键要求

- 迁移路径：`tests => cli-tests .md => cli-tests .py`，tests 仅作使用参考。
- 文档先行：每个命令先落 `.md`，再决定是否补 `.py`。
- 真实链路：以真实 CLI 链路为准；后续 `.py` 应标记 `@pytest.mark.e2e`。
- 模板一致：以 `cli-tests/env/test_chattool_env_basic.md` 为模板。
- 目录结构：当前为临时规划，后续会补充 `_xxx.py`（不止 basic）。

## 阶段 1：规则与模板

- 建立 `cli-tests/index.md` 与 `cli-tests/README.md`。
- 完成 `chattool env` 文档作为模板。

## 阶段 2：命令逐个迁移

- 按 `chattool` 命令列表逐一补齐 `.md`：
  - browser / client / dns / docker / env / gh / image / lark / mcp / network / serve / setup / skill / tplogin / zulip

## 阶段 3：真实环境补齐与回归

- 汇总所有 TODO 用例，补齐缺失的环境变量/凭证。
- 将可跑用例补成 `.py` 并以真实链路运行。
- 对失败用例逐一完善，确保 CLI 关键链路稳定。
