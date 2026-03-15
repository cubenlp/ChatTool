tools/
xxx/
- core.py 函数核心逻辑
- client.py 命令行封装
- serve 服务化
  - client.py 结合服务化的命令行封装 
  - serve.py 服务化封装
- mcp 工具接口转化为 mcp 

这里，core/local client/mcp 通常是必要的。对于安全敏感，或者本地配置复杂，或者计算开销大的工具，serve 可以把交互服务化。

通常，每个工具写完，会在仓库/skills 目录，基于 MCP/local client/server 提供 skills 配置。（提供中英版）

