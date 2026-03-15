ChatTool 板块

处于开发速度考虑，添加工具的过程，没有固定的规范，快速生长为主。但为了方便后续维护，需要逐步规范收敛。

1. 模型能力 llm/：llm 路由，基础对话接口，模型编排（当前还没有）等等。
2. 配置维护 config/：管理工具等的环境配置
   - 比如解析顺序 specific > default config file > environment var.
   - 模块化管理，方便拓展
3. Tool 板块(chattool 核心的部分）：
   - 实现各类，具体的功能，比如 github/dns...
   - 提供代码实现，CLI 实现（目前有一些代码逻辑放到了 cli/ 下），MCP 实现
   - 特别地，CLI 是其中最主要的能力，通过 utils/tui.py 来辅助交互体验。
4. skills 板块
5. setup 板块
   - 整合环境配置相关的逻辑，一些脚本安装逻辑
   - 对应 sudo 权限，主要直接打印脚本，让用户执行（也可以加 --sudo 来允许执行）
6. docker 板块
   - 配置常用的 docker-compose 文件，从 .env 到端口等。
7. serve 板块
   - 对于客户端能力不足（比如算力），或者密钥敏感等，放云上，拆分成 clien-serve.
   - 比如 ddns-serve，云端 serve 证书服务，本地拉去证书。
   - 当前代码没有解耦，还在 cli/serve 下。
8. client 板块（当前主流）
   - 提供可执行命令的 cli 入口（各自 CLI 应该分拆到各自目录下，比如 tools/xxx/ 之类，再从这里接入 chattool xxx）
   - 对接本地的 tool，以及 serve 板块的服务。


文档方面，除了几个板块的介绍（setup/docker 可以放一块），config 归 env 管理。还包括,blog 板块，以及 design 板块（当前还没有，详细介绍某些功能的设计逻辑，方便查阅和对齐需求）。

在 CLI 方面，遵循原则是：
- 在必要参数不完整时，触发 interactive。
- 当手动 -i/-I 可以强制开启或关闭，如果参数不全则抛出错误
- 参数会读取对应的默认变量，放到提示里（密钥 mask)

一些应该清理的文件夹(当前忽略即可）：
- application 应用板块，目前没想好设计逻辑。
- 当前的 serve/ 文件夹，开发 browser 特性引入。

一些原则，比如最小 import,避免开发多了 CLI 启动太慢。