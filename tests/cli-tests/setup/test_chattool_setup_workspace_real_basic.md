# test_chattool_setup_workspace_real_basic

验证 `chattool setup workspace` 会生成当前外层模板：根目录只保留 `AGENTS.md`、`TODO.md`、`ARCHIVE.md` 这三个控制文件。

归档相关文件职责：根 `ARCHIVE.md` 是归档操作指南，`archive/index.md` 是已归档内容索引；不再生成 `archive/README.md`。

`--with-chatblog` 使用真实本地 Git 仓库 fixture 验证：ChatBlog clone 到 `core/ChatBlog`，`source/_posts` 链接到 `public/chatblog`。

`--with-memory` 使用真实本地 Git 仓库 fixture 验证：ChatMemory clone 到 `core/ChatMemory`，只链接共享 groups `skills/chatarch`、`skills/common`、`skills/agents`，同时创建本地非共享目录 `skills/local`，并且不链接 `machine` 等机器/账号特定分组。
