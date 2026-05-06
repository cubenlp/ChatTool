# ChatTool 服务化接口分层设计

日期：2026-05-07
状态：设计草稿

## 目标

为 ChatTool 的能力定义一条通用服务化路径，让同一个能力可以被多个入口复用，而不是在 CLI、HTTP 服务、MCP 里重复实现业务逻辑。

目标分层是：

1. 纯代码实现，最终产出函数或类；
2. 基于打包好的函数封装成本地 CLI；
3. 基于同一组函数封装成服务 API / 管理页面；
4. 基于服务 API 再封装成本地 client CLI 或 MCP 工具。

长期目标是：本地 CLI 和远程 API 保持同一套语义。一个支持服务化执行的命令，应该只增加后端选择、连接配置和安全校验，不额外发明第二套工作流。

## 为什么需要这一层

ChatTool 里有些能力适合留在本地，有些能力更适合放在受控机器上执行：

- DNS 和证书操作需要云厂商密钥，并且需要按域名、动作做权限边界；
- 浏览器、Selenium、GPU、格式转换等任务可能依赖重型运行环境；
- Webhook、bot、定时任务需要长期运行的服务进程；
- Agent / MCP 客户端需要稳定后端，但不应该直接持有云厂商密钥。

服务 API 可以成为 CLI 和 MCP 共用的执行后端，同时保留本地 CLI 简洁、可脚本化的体验。

## 分层模型

### 第 1 层：纯代码能力

基础层是没有 CLI、HTTP、MCP 假设的 Python 函数或类。

示例：

- `chattool.tools.dns.create_dns_client()`
- `chattool.tools.cert.SSLCertUpdater`
- SVG 转 GIF 的转换函数

约束：

- 凭证、策略、运行参数显式传入，不隐式读取交互上下文；
- 返回结构化结果，或抛出可预期、可映射的异常；
- 核心能力层避免直接依赖 Click、FastAPI、Rich、MCP 等入口层库；
- 文件写入、确认提示、彩色输出等交互行为由上层包装。

### 第 2 层：本地 CLI

CLI 负责把用户输入适配到纯代码能力。

示例：

```bash
chattool dns list
chattool dns records example.com
chattool dns cert apply -d example.com
```

约束：

- CLI 负责人类交互、预览、确认、本地路径解析和输出格式；
- CLI 的命令形态在本地执行和远程执行时尽量一致；
- 对支持服务化的命令，后端可以来自 flag、环境变量或 client profile。

可能的后端选择：

```bash
chattool dns list                          # 默认本地执行
chattool dns list --api-base https://...    # 指定远程服务
CHATTOOL_API_BASE=https://... chattool dns list
```

### 第 3 层：服务 API / 管理页面

服务 API 包装同一组纯代码能力，并在服务端执行权限策略。

示例：

```bash
chattool serve dns --provider aliyun --allow-domain example.com --allow cert:apply
chattool serve cert --host 0.0.0.0 --port 8000
chattool serve svg2gif --host 0.0.0.0 --port 8000
```

约束：

- 服务端拥有云厂商凭证、能力白名单、scope 校验、审计日志和异步任务状态；
- 服务端只暴露被声明的能力，不暴露任意 shell 或任意 Python 执行；
- 服务 API 返回结构化 JSON、稳定错误码和 request id；
- 管理页面只是服务 API 的可视化入口，不应该绕过同一套鉴权和策略。

### 第 4 层：远程 client CLI / MCP

远程 client 复用用户熟悉的能力形态，把动作转发给服务 API。

可以并存两种命令形态：

```bash
chattool client dns list --profile dns-prod
chattool dns list --api-base https://dns.example.com
```

前者明确表达“这是远程 client”。后者适合在后端抽象稳定后，让原始 CLI 自动路由到远程后端。

MCP 初期不单独维护一套登录和 profile 系统，而是复用本地 client profile 或同一套 client abstraction：

```text
Agent -> MCP/Skill -> 本地 ChatTool CLI/client -> 远程 ChatTool serve API
```

## CLI 和服务接口的一致性

对可服务化的能力，本地和远程应共享同一组操作名。

| 能力 | 本地 CLI | 服务 API | 远程 CLI |
| --- | --- | --- | --- |
| 域名列表 | `chattool dns list` | `GET /dns/domains` | `chattool client dns list` |
| 记录列表 | `chattool dns records example.com` | `GET /dns/domains/{domain}/records` | `chattool client dns records example.com` |
| 设置记录 | `chattool dns set ...` | `PUT /dns/domains/{domain}/records/{rr}` | `chattool client dns set ...` |
| 删除记录 | `chattool dns delete ...` | `DELETE /dns/...` | `chattool client dns delete ...` |
| 申请证书 | `chattool dns cert apply ...` | `POST /cert/apply` | `chattool client cert apply ...` |

CLI 仍然是主要用户界面；服务 API 是执行后端。接口设计应优先保证 CLI 语义稳定，再把同一动作映射到 HTTP。

## 环境变量和 profile 选择

远程后端只需要少量连接字段：

```text
CHATTOOL_API_BASE=https://chattool.example.com
CHATTOOL_API_TOKEN=...
CHATTOOL_API_PROFILE=dns-prod
```

设计偏好：

- `CHATTOOL_API_BASE` 用于临时覆盖；
- 长期使用优先落到命名 client profile；
- 已有服务专用环境变量可以保留为兼容 alias；
- profile 中保存服务地址、refresh token、短期 access token、scope、过期时间和能力缓存。

示例：

```bash
chattool client connect dns-prod https://dns.example.com --code 123456
chattool client use dns-prod
chattool dns list --remote
```

## 服务发现

每个服务都应该暴露小型发现接口：

```text
GET /health
GET /info
```

`/info` 返回当前客户端可见的服务、版本、能力和限制：

```json
{
  "service": "dns",
  "version": "0.1",
  "capabilities": ["domains:list", "records:list", "records:set"],
  "scopes": ["dns:read", "dns:write"],
  "limits": {
    "allowed_domains": ["example.com"]
  }
}
```

本地可以展示为：

```bash
chattool client capabilities dns-prod
```

## 和 MCP 的关系

MCP 和服务 API 都是在向非人工调用方暴露能力，但职责不同：

- MCP 是 Agent 协议适配层；
- 服务 API 是带凭证、策略和审计的执行后端；
- CLI 是稳定的人类和脚本入口。

因此，服务 API 可以同时服务 CLI 和 MCP。第一阶段不要让 MCP 自己拥有独立的连接、登录、刷新机制；MCP 应该调用同一套 client profile 或 client abstraction。

## 第一阶段抽象工作

在真正增加云服务之前，先定义这些共享抽象：

- 能力元数据：名称、动作、输入 schema、输出 schema、scope；
- 后端选择：local vs remote；
- 鉴权 profile：server URL、refresh token、access token、scope、过期时间；
- 错误模型：结构化 error code、message、request id；
- 审计模型：action、target、result、actor、request id；
- 任务模型：适配证书申请、转换等异步能力。

这样 DNS 可以作为试点，但不会把服务化路径写成一次性的 DNS 专用逻辑。
