# test_chattool_setup_workspace_mock_basic

验证 workspace 模板不再生成根 `README.md`、`IDENTITY.md` 或 `MEMORY.md`，而是以 `AGENTS.md`、`TODO.md`、`ARCHIVE.md` 为外层控制文件。

归档相关文件职责：根 `ARCHIVE.md` 是归档操作指南，`archive/index.md` 是已归档内容索引；不再生成 `archive/README.md`。
