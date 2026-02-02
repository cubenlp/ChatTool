# MCP 服务指南

ChatTool 内置了符合 [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) 标准的服务端，允许 LLM 客户端（如 Claude Desktop, Cursor 等）直接调用 ChatTool 的功能。

## 功能模块

ChatTool MCP Server 包含以下核心模块：

- [DNS 管理](./dns.md): 域名解析、DDNS 和 SSL 证书管理
- [Zulip 集成](./zulip.md): 消息收发、频道管理

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
    "chattool-dns": {
      "command": "uvx",
      "args": [
        "--from",
        "chattool[dev]",
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
    "chattool-dns": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/absolute/path/to/ChatTool",
        "--extra",
        "dev",
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
```

## 配置说明

MCP 服务会自动读取 ChatTool 的全局配置。请确保你已经通过 `chattool env init` 或 `.env` 文件配置了相应的云厂商凭证（阿里云或腾讯云）。

```bash
# 检查当前配置
chattool env list
```


## 在 TRAE 中使用
1. 点击设置，选择 MCP 服务，手动添加：填入前边提到的配置

![20260202012501](https://qiniu.wzhecnu.cn/FileBed/source/20260202012501.png)

2. 创建智能体：输入概要，智能生成配置的提示词。在工具部分启用上一步的 MCP 工具

![20260202012331](https://qiniu.wzhecnu.cn/FileBed/source/20260202012331.png)

3. 通过该智能体进行聊天，此时智能体会根据帮你处理域名解析问题

![20260202012244](https://qiniu.wzhecnu.cn/FileBed/source/20260202012244.png)


## 工具组织与安全配置

ChatTool MCP 服务支持对工具进行分组和权限控制，你可以通过环境变量来配置只启用特定的工具组。这对于保护敏感操作（如修改 DNS 记录）非常有用。

### 可用的标签 (Tags)

- `dns`: 所有 DNS 相关工具
- `cert`: 所有证书相关工具
- `zulip`: 所有 Zulip 聊天工具
- `read`: 只读工具（如查询域名、记录、消息）
- `write`: 写入工具（如添加/删除记录、申请证书、发送消息）

## 在 Claude Desktop 中使用

1. 完成上述配置。
2. 重启 Claude Desktop。
3. 在对话中，你现在可以直接要求 Claude：
   - "帮我列出阿里云上的所有域名"
   - "给 example.com 添加一个 www 解析到 1.1.1.1"
   - "帮我更新 home.example.com 的 DDNS"
   - "为 *.example.com 申请一个 SSL 证书"
