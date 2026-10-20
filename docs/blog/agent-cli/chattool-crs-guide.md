# 从 ChatTool CRS 孵化入口迁移到独立 ChatCRS

早期 CRS 用量、自统计与管理接口先挂载在 ChatTool 中验证。能力成熟后已迁移到独立 ChatCRS，父包在 7.1.5 中撤掉对应命令、源码和配置 provider，避免两套实现与配置归属分叉。

```bash
pip install "chattool[crs]"
chatcrs --help
chatcrs remote --help
```

已有 CRS profiles 保留，升级不会改变凭据或激活 profile。当前接口和字段请查 [ChatCRS 文档](https://arch.gh.wzhecnu.cn/ChatCRS/)，父包旧教程的参数不再作为现行接口。

通用的 `chattool serve oauth` 保持可用；其 helper 已迁到 `chattool.serve.openai_oauth`，不依赖父包 CRS 目录。
