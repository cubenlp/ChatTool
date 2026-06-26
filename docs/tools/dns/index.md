# DNS 管理已迁移到 ChatDNS

ChatTool 不再持有 DNS 记录管理、DDNS 和 IP 探测的实现，也不再暴露 nested `chattool dns` 命令。

请使用独立 ChatArch 包 `ChatDNS`：

```bash
chatdns --help
chatdns list
chatdns records example.com
chatdns records test.example.com
chatdns set test.example.com -v 1.2.3.4
chatdns delete test.example.com -t A --yes
chatdns ip
chatdns ddns home.example.com --monitor
```

如果从 ChatTool 的可选依赖安装：

```bash
pip install "chattool[dns]"
```

## 边界说明

- DNS provider client、DNS record CRUD、DDNS、IP 探测和 DNS-01 证书自动化由 `ChatDNS` 维护。
- DNS MCP 不在本次 ChatTool parent 分离范围内；如需恢复 MCP 支持，应单独 review `ChatDNS`/ChatTool 的 MCP 边界。
- `chattool dns cert` 旧 nested 入口已移除；请使用 `chatdns cert apply/check`。ChatTool parent 不再持有 `tools/dns` 或 parent-owned `tools/cert` 证书业务实现，只保留 `serve/client cert` 远程服务壳。
- 历史设计记录仍保留在 `docs/design/dns-cli-interface.md`，仅作为迁移前接口背景，不代表当前 ChatTool CLI 仍暴露该入口。
