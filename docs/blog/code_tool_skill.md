# ChatTool 实战 ｜ 把 Python 脚本重构为 Agent Skill？

在 AI Agent 席卷而来的今天，我们听到了太多关于模型智能的宏大叙事。但回到代码编辑器前，开发者面临的问题往往非常具体：

**“我写好的 Python 代码，怎么才能被 AI 顺畅地调用？”**

本文将以 [ChatTool](./README.md) 中的 SSL 证书工具为例，复盘它是如何从一个**“只有自己能跑”**的脚本，一步步进化为**“AI 也能用”**的智能体技能。这不仅是代码形态的重构（Script -> CLI -> Server -> Skill），更是一次面向 AI 时代的思维升级。

---

## 引言：跨越“代码”与“智能体”的鸿沟

想象一下，你写了一个完美的 Python 脚本 `cert_gen.py` 来自动申请 SSL 证书。
你自己用得很顺手：配置好环境，敲入参数，回车，搞定。

但当你试图构建一个 AI Agent 来接管运维工作时，尴尬的事情发生了：
**AI 不知道怎么用它。**

*   AI 不知道你的脚本依赖什么环境，甚至不知道它的存在；
*   AI 可能会生成一段调用代码，但无法处理运行时依赖；
*   AI 即使调用成功，也难以理解输出结果的含义。

这揭示了一个核心矛盾：**传统的开发模式是面向“人”的，而智能体时代的工具必须是面向“模型”的。**

要让一个简单的脚本进化为强大的智能体技能，我们需要跨越四个维度的认知升级。

---

## 第一层：代码即能力 (Code Import)

**“能跑就行。”**

这是工具诞生的初级形态。核心逻辑被封装在一个 Python 类或函数中。
以我们的 SSL 证书工具为例，核心逻辑是 `SSLCertUpdater` 类，它负责和 ACME 协议交互、调用 DNS 接口验证域名。

```python
# src/chattool/tools/cert/cert_updater.py
class SSLCertUpdater:
    def __init__(self, domains, email, ...):
        # ... 初始化逻辑 ...
    
    async def run_once(self):
        # ... 核心业务逻辑 ...
```

*   **特点**：纯粹、灵活，无外部依赖。
*   **适用场景**：开发者自己在 IDE 里跑，或者作为库被其他 Python 项目集成。
*   **局限**：对非开发者不友好，环境依赖重，难以复用。

## 第二层：命令行工具 (CLI)

**“一行命令解决问题。”**

为了让非 Python 开发者（或者不想打开 IDE 的自己）也能用，我给代码穿上了一层外衣——CLI。
使用 `click` 这样的库，我们将 `SSLCertUpdater` 包装成了 `chattool dns cert-update`。

```bash
# 申请证书
chattool dns cert-update -d example.com -d *.example.com -e admin@example.com --provider aliyun

# 使用测试环境（Staging）
chattool dns cert-update -d example.com --staging
```

**输出结构**：
证书将保存在 `<cert-dir>/<domain>/` 目录下，包含标准文件：
- `fullchain.pem`: 完整证书链 (适用于 Nginx/Apache)。
- `privkey.pem`: 私钥文件。
- `cert.pem`: 叶子证书。

*   **进化点**：脱离了代码编辑器，变成了系统工具。可以通过 Shell 脚本自动化，可以通过 Cron 定时运行。
*   **适用场景**：运维脚本、CI/CD 流水线、本地快速操作。
*   **局限**：仍然受限于本地环境（网络、文件系统），难以跨机器调用。

## 第三层：服务化与远程调用 (Server-Client)

**“能力云端化，随处可达。”**

当业务变得复杂，比如需要在内网服务器申请证书，但 DNS 秘钥只在另一台安全机器上；或者需要支持多租户隔离，不想让用户直接接触秘钥。
这时候，我们需要将能力“服务化”，实现**操作分离**和**安全性增强**。

我们用 FastAPI 启动一个 Server (`chattool serve cert`)，并配套相应的 Client (`chattool client cert`)。

### Server 端：核心执行者
Server 负责执行核心逻辑，管理状态（Pending/Success），并处理鉴权。
它通过 HTTP Header 中的 Token 实现多租户物理隔离，不同 Token 的数据互不可见。

```bash
# 在安全服务器启动服务，指定证书存储路径
chattool serve cert --host 0.0.0.0 --port 8000 --output ./secure-certs
```

### Client 端：远程指挥官
Client 负责发送指令，查询状态，下载结果。

1.  **申请证书 (Apply)**:
    ```bash
    chattool client cert apply -d example.com --token "my-secret-token"
    ```
    请求发送后立即返回，Server 在后台异步执行耗时的 ACME 验证。

2.  **查询状态 (List)**:
    ```bash
    chattool client cert list --token "my-secret-token"
    ```
    查看证书有效期、剩余天数等元数据。

3.  **下载证书 (Download)**:
    ```bash
    chattool client cert download example.com -o ./local-certs --token "my-secret-token"
    ```
    安全地将生成的证书文件拉取到本地。

*   **进化点**：解耦了“执行环境”和“触发环境”。支持了异步任务、权限控制和远程调用。
*   **适用场景**：分布式系统、SaaS 服务、多用户协作环境。

## 第四层：智能体技能 (Skill / MCP)

**“让 AI 看懂并使用工具。”**

这是 AI 时代的终极形态。我们不再是给“人”写工具，而是给“模型”写工具。
我们需要告诉 AI：**我是谁？我能干什么？怎么用我？**

这里有两条路径：

1.  **MCP (Model Context Protocol)**：我们将代码直接暴露为 MCP Tool，AI 通过标准协议发现并调用它。
    *   **代码**：`@mcp.tool()` 装饰器。
    *   **特点**：标准化，即插即用，零适配成本。

2.  **Skill 封装**：对于不支持 MCP 的环境，或者复杂的复合工具，我们需要编写一份“说明书”——`SKILL.md`。
    这份文档不仅定义了工具，还定义了**任务路径 (Routes)**。

    在 `skills/cert-manager/SKILL.md` 中，我们清晰地告诉 AI：

    > **Route 1: Code Import**
    > *Scenario*: Python script development.
    > *Tool*: `chattool.tools.cert.cert_updater.SSLCertUpdater`
    >
    > **Route 2: CLI**
    > *Scenario*: Local machine ops.
    > *Tool*: `chattool dns cert-update`
    >
    > **Route 3: Server-Client**
    > *Scenario*: Remote management, multi-tenant.
    > *Tool*: `chattool client cert`

    通过这种方式，AI 不仅仅是“调用函数”，而是像一个高级工程师一样，根据场景选择最合适的工具形态。

*   **进化点**：工具具备了**语义**。它不再是冰冷的二进制，而是可以被 AI 理解、规划和组合的能力单元。
*   **适用场景**：AI Agent、Copilot、自动化智能运维。

---

## 结语：给工具注入“灵魂”

回顾这四个层次的演进，本质上是我们对“使用者”定义的不断修正：

1.  **Code**：为了让**机器**能跑起来。
2.  **CLI**：为了让**人**能方便地用。
3.  **Server**：为了让**系统**能安全地接入。
4.  **Skill**：为了让**智能体**能理解并规划。

在 AI 时代，最好的工具不再是那些拥有最复杂 UI 的软件，而是那些拥有最清晰语义接口的能力单元。
当我们把工具封装成 Skill 或 MCP 时，其实是在给冰冷的代码注入“灵魂”——让它们不仅能被执行，还能被理解、被编排、被创造性地组合。

这或许才是“面向 Agent 编程”的终极浪漫：**我们在构建的不仅仅是工具，而是未来数字世界的积木。**
