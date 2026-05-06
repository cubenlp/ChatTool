# OAuth refresh token 原理：CRS、Codex 和 ChatGPT 网页 access token 是一回事吗？

在 CRS / Codex / ChatGPT 这类工具里，经常会看到三种 token：

- `access_token`
- `refresh_token`
- `id_token`

它们名字相近，但角色完全不同。理解这三者，才能判断一个 token 能不能刷新、能不能验证、能不能拿去调用 ChatGPT 网页端或 OpenAI API。

结论先说：

- `refresh_token -> access_token` 不是本地算法“生成”，而是 OAuth 授权服务器在 `/oauth/token` 端点校验后签发；
- refresh token 通常是服务端可验证的长凭证，客户端不应该也通常不能自行判断其有效性；
- access token 可能是 JWT，也可能是 opaque token；真正是否有效，以目标资源服务器验证结果为准；
- ChatGPT 网页端 access token 和 OpenAI Platform API Key 不是一个东西；
- 用 ChatGPT 网页 token 去包装“API”属于非官方私有接口路线，历史上有项目做过，但通常脆弱、风险高，也不等价于官方 API。

---

## 先把三个 token 分清楚

### access token

Access token 是“访问资源”的短期凭证。

OAuth 2.0 里，客户端拿 access token 去请求资源服务器，资源服务器负责验证 token 的有效性、过期时间、权限范围等。

它通常短期有效，例如几十分钟到几小时。短期有效的原因很简单：一旦泄露，损害窗口要尽量小。

### refresh token

Refresh token 是“换新 access token”的长期凭证。

它不应该拿去调用业务接口，而是只发给授权服务器的 token endpoint：

```text
POST /oauth/token
Content-Type: application/x-www-form-urlencoded

grant_type=refresh_token
refresh_token=<refresh_token>
```

如果授权服务器判断 refresh token 有效，就返回新的 access token；也可能同时返回新的 refresh token，这叫 refresh token rotation。

### id token

ID token 来自 OpenID Connect，用于表达“这个用户是谁”。它一般是 JWT，里面会有用户身份、issuer、audience、过期时间等 claims。

ID token 不是给你调用 API 的通用凭证。它的核心用途是身份声明，而不是资源访问。

---

## “refresh token 生成 access token”到底走什么算法？

严格说，这不是一个客户端本地算法。

客户端不能拿 refresh token 在本地算出 access token。正确流程是：

1. 客户端把 refresh token 发送给授权服务器；
2. 授权服务器校验 refresh token；
3. 授权服务器决定是否签发新的 access token；
4. 客户端拿新的 access token 访问资源服务器。

也就是说，access token 是授权服务器签发的，不是 refresh token 通过某个公开算法派生出来的。

内部实现可以有几种：

### 1. Opaque random token

服务端生成一个高熵随机字符串，数据库里记录：

- token id；
- 用户；
- client id；
- scope；
- 过期时间；
- 是否撤销；
- 是否已被使用或轮换。

验证时查数据库或缓存。

### 2. Signed JWT

服务端生成 JWT，并用私钥或共享密钥签名。资源服务器可以验证签名、`exp`、`iss`、`aud`、`scope` 等 claims。

这种方式验证速度快，但撤销和实时状态管理更复杂。

### 3. 混合方案

常见做法是 access token 用 JWT 或短期 opaque token，refresh token 用更严格的服务端状态记录。这样能同时兼顾性能和可撤销性。

所以问“走什么算法”，更准确的回答是：

- PKCE 授权阶段用 SHA-256 生成 code challenge；
- ID token 如果是 JWT，会用 JWS 签名算法验证；
- access token 是否可本地验证取决于它是不是 JWT；
- refresh token 通常是 opaque 或服务端状态化凭证，客户端只能交给 token endpoint 验证。

---

## token 有效性怎么看？

### access token

如果 access token 是 JWT，可以解码 header/payload 看：

- `exp`：过期时间；
- `nbf`：不早于某时间可用；
- `iss`：签发者；
- `aud`：受众，即这个 token  intended 给哪个服务用；
- `scope` 或类似权限字段。

但“能解码”不等于“有效”。有效性还需要：

- 验签；
- issuer 匹配；
- audience 匹配；
- 没过期；
- scope 覆盖当前接口；
- token 未被撤销；
- 账号、组织、订阅状态仍然允许。

如果 access token 是 opaque token，客户端看不出任何有效信息，只能调用目标资源服务器或 introspection endpoint，由服务端判断。

### refresh token

refresh token 的有效性通常只能通过 token endpoint 判断。

常见失败原因：

- 过期；
- 被撤销；
- 已经轮换，旧 token 重放；
- client id 不匹配；
- 用户改密、退出登录、撤销授权；
- 风控认为环境异常；
- scope 请求超出原授权。

所以 refresh token 的判断方式不是“本地解码”，而是发起 refresh 请求，看授权服务器是否返回新 token 或错误。

---

## 服务端怎么验证 token？

### 资源服务器验证 access token

资源服务器收到：

```text
Authorization: Bearer <access_token>
```

通常会检查：

- token 格式和签名；
- token 是否过期；
- token 的 issuer；
- token 的 audience 是否就是自己；
- scope 是否允许当前操作；
- 用户/组织/订阅/风控状态是否允许；
- token 是否被撤销。

OAuth 规范没有强制规定资源服务器必须怎么验证 access token，因为 token 格式可以是 JWT，也可以是 opaque。具体由服务提供方实现。

### 授权服务器验证 refresh token

授权服务器收到 refresh 请求后，会检查：

- `grant_type` 是否是 `refresh_token`；
- refresh token 是否存在；
- refresh token 是否属于这个 client；
- 是否过期或撤销；
- 是否触发 rotation reuse；
- 请求 scope 是否不超过原授权；
- 是否需要额外 client authentication。

通过后才签发新的 access token。

---

## CRS 里 OpenAI token 是怎么刷新的

CRS 里 OpenAI OAuth 相关代码主要在：

- `src/routes/admin/openaiAccounts.js`
- `src/services/account/openaiAccountService.js`

CRS 的流程是：

1. 生成 OpenAI OAuth 授权 URL；
2. 使用 PKCE：生成 `codeVerifier`，再计算 `codeChallenge`；
3. 用户授权后，拿 authorization code 调 token endpoint；
4. 保存返回的 `id_token`、`access_token`、`refresh_token`、`expires_in`；
5. 后续 access token 过期时，用 refresh token 换新 access token。

CRS 中 refresh 的核心请求形态是：

```text
POST https://auth.openai.com/oauth/token
Content-Type: application/x-www-form-urlencoded

grant_type=refresh_token
client_id=<OpenAI/Codex client id>
refresh_token=<stored refresh token>
scope=openid profile email
```

刷新成功后，CRS 会更新：

- `accessToken`
- `expiresAt`
- `idToken`，如果返回了；
- `refreshToken`，如果服务端返回了新的。

同时 CRS 会使用分布式锁，避免同一个账号在多进程场景下并发刷新。

这个设计很重要，因为 refresh token rotation 场景下，两个进程同时用同一个旧 refresh token，可能导致其中一个或两个都失败。

---

## 这和 ChatGPT 网页端 access token 是一个东西吗？

不是一个“完全等价”的东西，但属于同一大类：OAuth/OIDC 风格的 bearer credential。

区别在于：

- ChatGPT 网页端 access token 是给 ChatGPT Web 后端/相关资源服务器用的；
- Codex/CRS 里的 OpenAI OAuth token 使用特定 client id、scope 和回调流程；
- OpenAI Platform API Key 是另一套凭证系统，用于官方 API billing/project/key 管理；
- ChatGPT Plus/Pro 订阅权益不等于 OpenAI API 额度。

所以，不能把 ChatGPT 网页 access token 理解成“官方 OpenAI API Key”。

它可能能访问部分 ChatGPT 私有后端接口，但那取决于：

- token 的 audience；
- scope；
- 服务端是否接受这个 client 的 token；
- 是否还需要 cookie、CSRF、设备/浏览器上下文、组织状态或风控信号；
- 私有接口当前是否仍然存在。

这些都不是公开稳定契约。

---

## 能不能用它编辑网页对话、用文生图模型、或者转 API？

从技术上看，如果一个 access token 被某个私有资源服务器接受，它就能在该服务器允许的范围内调用接口。

但这里有几个关键限制：

1. **不是官方 API**
   ChatGPT 网页后端接口不是 OpenAI Platform API。它的路径、参数、权限和风控都可能随时变化。

2. **scope/audience 不一定匹配**
   一个 token 能访问 A 服务，不代表能访问 B 服务。OAuth token 不是“万能登录票”。

3. **网页功能不等于 API 能力**
   ChatGPT 网页里的对话、图片、文件、项目、连接器等能力，可能依赖一整套 Web session、账户状态、产品开关、服务端编排和风控，而不是一个 access token 就能稳定复刻。

4. **风险高**
   把网页 token 交给第三方 proxy，相当于把账号会话交给别人。它可能能读取或操作你的 ChatGPT 账号范围内的数据。

5. **合规风险**
   通过私有接口包装成 API，通常不属于官方支持路径，也可能违反服务条款。

因此，面向长期可维护系统，应该优先使用官方 OpenAI API 或明确支持的 OAuth/API 机制。网页 access token 路线更适合“研究协议边界”，不适合生产依赖。

---

## 网上有没有“ChatGPT access token 转 API”的项目？

有过，而且不止一个。

### chatgpt-api 的 unofficial proxy 路线

早期 `chatgpt-api` 这类项目提供过 `ChatGPTUnofficialProxyAPI`，用 ChatGPT Web access token 访问非官方 ChatGPT 后端。项目文档也明确把它和官方 API Key 路线区分开：一个是官方 API，一个是 unofficial proxy。

这类方案的特点是：

- 看起来更像 ChatGPT 网页体验；
- 依赖私有后端接口；
- 容易受 Cloudflare、风控、接口变更影响；
- 维护者通常也建议优先使用官方 API。

### Pandora / fakeopen 路线

Pandora 生态曾经广泛使用 ChatGPT access token 来模拟网页端能力，并提供 proxy/API 风格入口。

这类项目的共同点是：

- 依赖 ChatGPT Web session 或 access token；
- token 有效期和获取方式受 OpenAI 登录机制变化影响；
- 项目生命周期经常受接口变动影响；
- 需要高度信任部署方。

### 普通 OpenAI reverse proxy

还有很多叫 “ChatGPT proxy” 的项目，其实不是用 ChatGPT 网页 access token，而是把官方 OpenAI API Key 放在服务端，再提供 OpenAI-compatible endpoint。

这类项目本质上是 API Key 代理，不是“ChatGPT access token 转 API”。

判断一个项目属于哪类，要看它需要你提供的是：

- `OPENAI_API_KEY`：通常是官方 API proxy；
- ChatGPT Web access token / session token：通常是非官方网页后端 proxy；
- CRS `cr_...` key：通常是自建中转网关的下游 key。

---

## 对 ChatTool / CRS 的实践建议

对于我们当前的 `chattool crs`：

- 不接入 ChatGPT Web 私有 token；
- 不做网页端 conversation 编辑；
- 不把 ChatGPT access token 包装成 OpenAI API；
- 只读取 CRS 暴露的公开 self-stat 和只读 admin endpoint；
- OpenAI OAuth refresh/access token 逻辑交给 CRS 后台账号服务处理。

如果后续要在 ChatTool 里增加 OAuth token 相关命令，建议只做这些低风险能力：

- 显示 token 过期时间；
- 显示账号是否有 refresh token，但不输出明文；
- 触发 CRS 官方后台已有的只读检查；
- 对 refresh 这类写操作单独 PRD、单独确认、默认 dry-run。

不建议做：

- 从浏览器 cookie/session 中抓 ChatGPT token；
- 把 ChatGPT Web token 转成 OpenAI-compatible API；
- 自动编辑网页会话；
- 绕过官方 API billing 或产品限制。

---

## 总结

Refresh token 的本质不是“算法种子”，而是授权服务器认可的长期凭证。Access token 的本质也不是“万能 API key”，而是带 audience、scope、有效期和服务端策略的短期访问凭证。

CRS 里的 OpenAI refresh 逻辑是标准 OAuth 思路：refresh token 发给 `auth.openai.com/oauth/token`，授权服务器校验后返回新的 access token。CRS 只是保存、刷新和加密管理这些 token，不是在本地生成它们。

至于 ChatGPT 网页端 access token，它和 OpenAI Platform API Key 不是同一类生产接口凭证。用它包装 API 的项目历史上存在，但属于非官方私有接口路线，稳定性、安全性和合规性都不适合作为长期工程依赖。

---

## 参考资料

- OAuth 2.0 RFC 6749: <https://www.rfc-editor.org/rfc/rfc6749>
- JWT RFC 7519: <https://www.rfc-editor.org/rfc/rfc7519>
- OpenID Connect Core 1.0: <https://openid.net/specs/openid-connect-core-1_0.html>
- ChatGPT API / unofficial proxy historical project: <https://github.com/Good0007/chatgpt-api>
- Pandora-ChatGPT package notes: <https://pypi.org/project/Pandora-ChatGPT/1.3.0/>
- CRS local source: `src/routes/admin/openaiAccounts.js`, `src/services/account/openaiAccountService.js`
