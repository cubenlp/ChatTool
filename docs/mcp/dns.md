# DNS 管理工具

ChatTool MCP Server 提供了一套完整的 DNS 管理工具，支持阿里云和腾讯云。

## 可用工具

### 1. 基础 DNS 管理
- **dns_list_domains**
  - 描述: 列出账号下的所有域名
  - 参数: 
    - `provider` (可选): 'aliyun' 或 'tencent'
  - 标签: `dns`, `read`

- **dns_get_records**
  - 描述: 获取域名的解析记录
  - 参数:
    - `domain`: 域名 (如 example.com)
    - `rr` (可选): 主机记录 (如 www)
    - `provider` (可选)
  - 标签: `dns`, `read`

- **dns_add_record**
  - 描述: 添加 DNS 解析记录
  - 参数:
    - `domain`: 域名
    - `rr`: 主机记录
    - `type`: 记录类型 (A, CNAME, TXT 等)
    - `value`: 记录值
    - `ttl`: 生存时间 (默认 600)
  - 标签: `dns`, `write`

- **dns_delete_record**
  - 描述: 删除 DNS 解析记录
  - 参数:
    - `domain`: 域名
    - `rr`: 主机记录
    - `type` (可选): 记录类型过滤
  - 标签: `dns`, `write`

### 2. 动态域名 (DDNS)
- **dns_ddns_update**
  - 描述: 执行一次 DDNS 更新（自动获取当前 IP 并更新 DNS）
  - 参数:
    - `domain`: 域名
    - `rr`: 主机记录
    - `ip_type`: 'public' (公网) 或 'local' (内网)
  - 标签: `dns`, `write`

### 3. SSL 证书管理
- **dns_cert_update**
  - 描述: 自动申请或更新 Let's Encrypt 证书（通过 DNS-01 验证）
  - 参数:
    - `domains`: 域名列表
    - `email`: 注册邮箱
    - `staging`: 是否使用测试环境 (默认为 False)
  - 标签: `cert`, `write`
