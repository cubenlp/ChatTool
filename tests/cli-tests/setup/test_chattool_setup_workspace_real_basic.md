# test_chattool_setup_workspace_real_basic

验证 `chattool setup workspace` 会生成当前外层模板：根目录只保留 `AGENTS.md`、`TODO.md`、`ARCHIVE.md` 这三个控制文件。

## Case: 基础 workspace scaffold

- 运行 `chattool setup workspace <tmp>/workspace -I`。
- 应生成 `AGENTS.md`、`TODO.md`、`ARCHIVE.md`、`.trash/`、`projects/`、`archive/`、`core/`、`scripts/`、`skills/`、`public/`。
- 不应生成旧根 `README.md`、`IDENTITY.md` 或 `MEMORY.md`。

## Case: ChatTool extra module

- 使用本地 ChatTool checkout 作为 `--chattool-source`。
- 运行 `chattool setup workspace <tmp>/workspace --with-chattool --chattool-source <repo> -I`。
- 应创建 `core/ChatTool` 并同步 ChatTool skills 到 workspace `skills/`。

## Case: ChatBlog 和 ChatMemory extra modules

- 构造两个本地 git repo：
  - fake ChatBlog 含 `source/_posts/demo.md`。
  - fake ChatMemory 含 `Skills/chatarch/demo/SKILL.md`。
- 运行：
  ```sh
  chattool setup workspace <tmp>/workspace \
    --with-chatblog --chatblog-source <fake-chatblog> \
    --with-memory --memory-source <fake-chatmemory> \
    -I
  ```
- 应创建：
  - `core/ChatBlog`
  - `core/ChatMemory`
  - `public/chatblog` symlink 指向 `core/ChatBlog/source/_posts`
  - `skills/chatarch` symlink 指向 `core/ChatMemory/Skills/chatarch`
- 输出应包含 `ChatBlog repo:` 与 `ChatMemory repo:`，不应包含 `RexBlog repo:`。

## Case: force 覆盖生成文件

- 先初始化 workspace。
- 手动修改生成的 `projects/README.md`。
- 运行 `chattool setup workspace <workspace> --force -I`。
- 文件应恢复为模板内容。

## Case: existing workspace 保留协议文件

- 预先创建 `AGENTS.md`。
- 运行 `chattool setup workspace <workspace> -I`。
- 应保留原 `AGENTS.md` 内容。
