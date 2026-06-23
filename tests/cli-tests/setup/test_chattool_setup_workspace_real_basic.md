# test_chattool_setup_workspace_real_basic

验证 `chattool setup workspace` 会生成当前外层模板：根目录只保留 `AGENTS.md`、`TODO.md`、`ARCHIVE.md` 这三个控制文件。

归档相关文件职责：根 `ARCHIVE.md` 是归档操作指南，`archive/index.md` 是已归档内容索引；不再生成 `archive/README.md`。

`--with-chattool` 已从 workspace 初始化 extra 中移除：workspace skill 系统不再负责复制或维护 ChatTool 自带 skills，避免把过时的 ChatTool skills 带入用户 workspace。

`--with-chatblog` 使用真实本地 Git 仓库 fixture 验证：旧 Hexo 结构存在 `source/_posts` 时链接到 `public/chatblog`；新版 Python 包结构没有 `source/_posts` 时只 clone 到 `core/ChatBlog` 并跳过 public posts link，不阻断后续 extras。

`--with-memory` 使用真实本地 Git 仓库 fixture 验证：ChatMemory clone 到 `core/ChatMemory`，只链接共享 groups `skills/chatarch`、`skills/common`、`skills/agents`，同时创建本地非共享目录 `skills/local`，并且不链接 `machine` 等机器/账号特定分组。
