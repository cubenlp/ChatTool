# test_chattool_setup_workspace_mock_basic

验证 workspace 模板不再生成根 `README.md`、`IDENTITY.md` 或 `MEMORY.md`，而是以 `AGENTS.md`、`TODO.md`、`ARCHIVE.md` 为外层控制文件。

归档相关文件职责：根 `ARCHIVE.md` 是归档操作指南，`archive/index.md` 是已归档内容索引；不再生成 `archive/README.md`。

ChatMemory optional module 只 link 明确允许的共享 skill groups：`common` 和 `chatarch`。不应 link 整个 `ChatMemory/Skills`，也不应默认 link Playground 本地 `Skills/prd-task` 或机器/账号特定分组。
