# CLI 树

`chattool --tree` 从真实 Click/LazyGroup 注册面生成，用于锁定当前 parent command surface。此页面只记录 ChatTool parent 当前仍拥有的顶层命令；已迁出的能力（如 `dns`、`gh`、`image` 等）不在这里重新暴露。

```text
chattool  # Unified entry point for ChatTool services and scripts.
├── --help  # Show help for the current command.
├── --version  # Show package version.
├── --tree  # Print the registered CLI tree.
├── browser  # Browser automation helpers.
├── cc  # cc-connect helper commands.
├── client  # Remote client tools.
├── crs  # Claude Relay Service helper commands.
├── docker  # Docker utility commands.
├── explore  # Research and data exploration helpers.
├── mcp  # MCP server inspection and launch helpers.
├── nginx  # Nginx configuration generation helpers.
├── serve  # Local service helpers.
├── skill  # Install and manage ChatTool skills.
└── tplogin  # TP-Link router helpers.
```

## 验证

- 源码入口：`chattool.client.main.cli`
- 回归测试：`tests/mock-cli-tests/client/test_chattool_version_tree_basic.py`
- 发布版本：`chattool==7.1.4`
