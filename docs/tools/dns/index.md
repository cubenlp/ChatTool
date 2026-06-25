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

- DNS provider client、DNS record CRUD、DDNS 和 IP 探测由 `ChatDNS` 维护。
- DNS MCP 不在本次 ChatTool parent 分离范围内；如需恢复 MCP 支持，应单独 review `ChatDNS`/ChatTool 的 MCP 边界。
- `chattool dns cert` 不属于第一阶段 DNS-only 分离；证书管理涉及 `tools/cert`，后续作为单独边界继续 review。
- 历史设计记录仍保留在 `docs/design/dns-cli-interface.md`，仅作为迁移前接口背景，不代表当前 ChatTool CLI 仍暴露该入口。
