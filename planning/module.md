目前的板块设计：
1. 工具类：tools/ 实现具体的应用能力，在实现功能的基础上，提供 CLI/MCP/SKILLS
2. 安装类: setup/ 辅助搭建环境。可以下分板块，比如
   - 常规的安装 chattool setup ...
   - docker 配置生成，chattool docker ...
   - nginx 配置生成，chattool nginx ...
   - skill 安装，chattool skill ...

3. Utils 基础工具，提供辅助当前仓库的功能构建的，比如：
   - CLI 交互的基础工具
   - 常规函数，网络请求等。

在这些基础上，在目录 mcp/ 下，汇总已有工具的 MCP 接口，提供管理，以及安装选项（比如只安装某些类）。
在 client 目录下，汇总已有工具的客户端代码，作为交互入口。

一些开发规范，比如：模块化设计需求。包括对话提到的。
为了更好地进行拓展，参考的最佳实践：
1. 拓展某一类能力时，维护入口和注册表会更方便，比如环境管理 chatenv test
class BaseEnvConfig:
    """环境变量配置基类"""
    
    _registry: List[Type['BaseEnvConfig']] = []
    _title: str = "Configuration"

    def __init_subclass__(cls, **kwargs):
    def test(self):
2. image 拓展支持不同的平台
3. llm 支持不同的路由
4. setup 安装不同的内容。

放一个统一的路由层，好处在与进一步处理打包成 CLI 时，同类模块可以用类似的交互逻辑。每次拓展，可以从路由层快速验证。