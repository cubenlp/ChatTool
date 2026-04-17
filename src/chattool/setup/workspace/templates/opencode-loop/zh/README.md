# Workspace

人类-AI 协作 workspace 根目录。

当前 workspace 使用 `projects/` 作为实际工作的执行容器。workspace 根目录文件负责提供协议和上下文，project 内文件负责驱动执行。

当前版本已启用 OpenCode loop-aware 模式：

- 外层协议负责帮助模型理解文档含义、需求和规范
- 内层 `chatloop` 负责在模型准备停下时重新进入基于 `PRD.md` 的 fresh-start loop
