# CLI Tests 迁移计划

本文档记录从 `tests/` 迁移到 `cli-tests/` 的阶段计划。

## 阶段 0：规则与模板（先完成）

- 对齐 `AGENTS.md` 与 `docs/development-guide/` 的文档先行规则。
- 固化 `sample.test.md` 作为模板。
- 创建 `cli-tests/index.md` 与 `cli-tests/README.md`。

## 阶段 1：CLI 基础用例

- 优先覆盖 `chattool`/`chatenv`/`chatskill` 的 CLI 基本链路。
- 先写文档，再迁移/实现 `.py`。

## 阶段 2：工具级 CLI 用例

- 迁移 `tests/tools/*` 中的 CLI 用例到 `cli-tests/`。
- 非 CLI 的纯单元测试保留在 `tests/`，除非转为 CLI 流程。

## 阶段 3：真实集成用例

- 将真实链路（需要外部资源或真实服务）转为 CLI 文档先行测试。
- 任何修改文件或远端资源的用例必须包含回滚步骤。
