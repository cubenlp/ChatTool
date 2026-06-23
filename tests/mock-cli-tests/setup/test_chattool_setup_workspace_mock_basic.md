# test_chattool_setup_workspace_mock_basic

验证 workspace 模板不再生成根 `README.md`、`IDENTITY.md` 或 `MEMORY.md`，而是以 `AGENTS.md`、`TODO.md`、`ARCHIVE.md` 为外层控制文件。

归档相关文件职责：根 `ARCHIVE.md` 是归档操作指南，`archive/index.md` 是已归档内容索引；不再生成 `archive/README.md`。

可选 workspace extras 使用明确的目标路径：`ChatBlog` clone 到 `core/ChatBlog`，并只把博客文章目录链接到 `public/chatblog`。如果 `public/chatblog` 已经是用户真实目录，命令必须拒绝覆盖。

ChatMemory optional module 只 link 明确允许的共享 skill groups：`chatarch`、`common` 和 `agents`。同时创建本地非共享目录 `skills/local`。不应 link 整个 `ChatMemory/Skills`，也不应默认 link `prd-task`、`machine` 或其他机器/账号特定分组。
