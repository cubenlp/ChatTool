# MCP 服务指南

ChatTool 内置了符合 [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) 标准的服务端，允许 LLM 客户端（如 Claude Desktop, Cursor 等）直接调用 ChatTool 的功能。

## 功能模块

ChatTool MCP Server 当前保留以下 legacy 模块：

- [Zulip 集成](./zulip.md): 消息收发、频道管理
- [Network Scanner](../tools/network/index.md)

DNS 管理已迁移到独立 `ChatDNS` / `chatdns` CLI；ChatTool parent 暂不在本次 DNS 分离中维护 DNS MCP 接入，后续如需 MCP 支持再单独 review。

## 安装与使用

ChatTool 提供了便捷的 CLI 命令来管理 MCP 服务。

### 1. 安装 uv (如果尚未安装)

推荐使用 `uv` 来运行 Python 工具，它快速且无需管理复杂的虚拟环境。

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. 配置 Claude Desktop

你需要手动配置 Claude Desktop 以连接到 ChatTool MCP 服务。

1. 打开 Claude Desktop 的配置文件：
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`

2. 添加以下配置（根据你的环境调整路径）：

```json
{
  "mcpServers": {
    "chattool": {
      "command": "uvx",
      "args": [
        "--from",
        "chattool[mcp]",
        "mcp-server-chattool"
      ]
    }
  }
}
```

或者，如果你是开发者安装（本地源码）：

```json
{
  "mcpServers": {
    "chattool": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/absolute/path/to/ChatTool",
        "--extra",
        "mcp",
        "mcp-server-chattool"
      ]
    }
  }
}
```

### 3. 运行服务

如果你需要手动运行服务（例如调试）：

```bash
# 启动 MCP 服务 (STDIO 模式)
chattool mcp start

# 启动 MCP 服务 (HTTP 模式，用于远程调用)
chattool mcp start --transport http --port 8000
```

### 4. 查看服务信息

查看服务暴露的工具和资源详情：

```bash
chattool mcp info

# 兼容旧命令
chattool mcp inspect

# 输出机器可读 JSON
chattool mcp info --json-output
```

## 配置说明

MCP 服务会自动读取 ChatTool 的全局配置。当前 DNS MCP 不在本次分离范围内；DNS 记录管理请使用独立 `chatdns` CLI。

```bash
# 检查当前配置
chatenv cat
```


## 在 TRAE 中使用
1. 点击设置，选择 MCP 服务，手动添加：填入前边提到的配置

![20260202012501](https://qiniu.wzhecnu.cn/FileBed/source/20260202012501.png)

2. 创建智能体：输入概要，智能生成配置的提示词。在工具部分启用上一步的 MCP 工具

![20260202012331](https://qiniu.wzhecnu.cn/FileBed/source/20260202012331.png)

3. 通过该智能体进行聊天，此时智能体可使用当前 legacy MCP 中仍保留的 Zulip / Network 工具。DNS 相关 MCP 能力本轮不维护。

![20260202012244](https://qiniu.wzhecnu.cn/FileBed/source/20260202012244.png)


## 工具组织与安全配置

ChatTool MCP 服务支持对工具进行分组和权限控制，你可以通过环境变量来配置只启用特定的工具组。

### 可用的标签 (Tags)

- `zulip`: 所有 Zulip 聊天工具
- `network`: Network scanner 工具
- `read`: 只读工具（如查询消息、扫描网络信息）
- `write`: 写入工具（如发送消息）

## 在 Claude Desktop 中使用

1. 完成上述配置。
2. 重启 Claude Desktop。
3. 在对话中，你现在可以直接要求 Claude：
   - "帮我列出 Zulip 频道"
   - "帮我查询某个 Zulip 话题下的最近消息"
   - "帮我扫描局域网里在线的主机"

DNS 记录管理、DDNS 与证书自动化不属于当前 ChatTool MCP 范围；请使用 `chatdns` / `chatdns cert` CLI。DNS MCP 如需恢复，应单独 review ChatDNS/ChatTool MCP 边界。
