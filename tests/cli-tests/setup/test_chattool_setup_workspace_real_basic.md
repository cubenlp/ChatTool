# test_chattool_setup_workspace_real_basic

验证 `chattool setup workspace` 会生成当前外层模板：根目录只保留 `AGENTS.md`、`TODO.md`、`ARCHIVE.md` 这三个控制文件。

归档相关文件职责：根 `ARCHIVE.md` 是归档操作指南，`archive/index.md` 是已归档内容索引；不再生成 `archive/README.md`。
