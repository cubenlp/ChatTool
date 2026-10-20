# CRS 已迁移至 ChatCRS

CRS 最初在 ChatTool 中孵化，现已由独立的 **ChatCRS** 维护。ChatTool 7.1.5 移除了父包 `crs` 命令、HTTP/CLI 实现和 CRSConfig provider；请使用一级命令 `chatcrs`。

```bash
pip install "chattool[crs]"
# 或独立安装
pip install ChatCRS
chatcrs --help
chatcrs remote --help
chatenv init -t crs
```

已有 CRS profile 文件不会被删除或修改。CRS 字段与动态管理员 token 的归属、接口与命令以 [ChatCRS 文档](https://arch.gh.wzhecnu.cn/ChatCRS/) 为准；不要照搬早期父包命令参数。

`chattool serve oauth` 是仍保留的通用 OAuth 服务，其 helper 已移到 `chattool.serve.openai_oauth`，不再依赖 CRS 目录。该服务的参数和行为保持不变。
