---
name: "dns"
description: "使用 ChatTool 管理 DNS 记录、DDNS 和 SSL 证书。当用户想要列出域名、修改 DNS 记录或更新证书时调用。"
---

# DNS 管理器

本技能允许您使用 ChatTool 库管理 DNS 记录和 SSL 证书。

## 功能

- **列出域名**: 查看配置账户下的所有域名（阿里云/腾讯云）。
- **获取记录**: 检索特定域名的 DNS 记录。
- **添加/删除记录**: 修改 DNS 记录。
- **DDNS**: 更新动态 DNS 记录。
- **SSL 证书**: 请求或续期 Let's Encrypt 证书。

## 工具

您应该使用可用的 MCP 工具进行这些操作：
- `dns_list_domains`
- `dns_get_records`
- `dns_add_record`
- `dns_delete_record`
- `dns_ddns_update`
- `dns_cert_update`

## 配置

确保已设置 DNS 提供商的环境变量（例如 `ALIBABA_CLOUD_ACCESS_KEY_ID`, `TENCENT_CLOUD_SECRET_ID` 等）。
