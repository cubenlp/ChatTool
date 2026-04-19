# Workspace

人类-AI 协作 workspace 根目录。

当前 workspace 使用 `projects/` 作为实际工作的执行容器。workspace 根目录文件负责提供协议和上下文，project 内文件负责驱动执行。

当前版本已启用 OpenCode loop-aware 模式：

- 外层协议负责帮助模型理解文档含义、需求和规范
- 内层 `chatloop` 只会在显式触发 `/chatloop ...` 后介入，并在模型准备停下时重新进入基于 `PRD.md` 的 fresh-start loop

另外：

- 需要修改的源码仓库默认保留在 `core/`
- 如果某个 project 需要更短的源码访问路径，可在 project 内按需手动创建到 `core/<repo-name>` 的符号链接，但不作为默认自动行为
- 跨多个 project 可复用的长期参考材料，优先沉淀到 workspace 根目录 `reference/`
- 跨多个 project 的整理约定与维护规范，优先沉淀到 `docs/themes/`
