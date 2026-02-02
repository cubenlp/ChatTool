<div align="center">
    <a href="https://pypi.python.org/pypi/chattool">
        <img src="https://img.shields.io/pypi/v/chattool.svg" alt="PyPI version" />
    </a>
    <a href="https://github.com/cubenlp/chattool/actions/workflows/test.yml">
        <img src="https://github.com/cubenlp/chattool/actions/workflows/test.yml/badge.svg" alt="Tests" />
    </a>
    <a href="https://chattool.wzhecnu.cn">
        <img src="https://img.shields.io/badge/docs-github_pages-blue.svg" alt="Documentation Status" />
    </a>
    <a href="https://codecov.io/gh/cubenlp/chattool">
        <img src="https://codecov.io/gh/cubenlp/chattool/branch/master/graph/badge.svg" alt="Coverage" />
    </a>
</div>

<div align="center">
    <img src="https://qiniu.wzhecnu.cn/PicBed6/picgo/chattool.jpeg" alt="ChatAPI Toolkit" width="360" style="border-radius: 20px;">
</div>

基于 OpenAI API 的 `Chat` 对象，支持多轮对话以及异步处理数据等。

## 安装方法

```bash
pip install chattool --upgrade
```

## 使用方法

### 环境变量配置

ChatTool 使用集中式配置管理，支持`.env`文件、环境变量和默认值。

1. **CLI 管理配置**（推荐）：
   ```bash
   # 交互式初始化（引导设置各项配置）
   chattool env init -i
   
   # 设置配置项
   chattool env set OPENAI_API_KEY=sk-xxx
   
   # 查看配置
   chattool env list
   ```

2. **手动配置**：
   你可以手动创建 `.env` 文件或设置环境变量。

   **OpenAI 配置**
   ```bash
   export OPENAI_API_KEY="sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
   export OPENAI_API_BASE="https://api.example.com/v1"
   export OPENAI_API_MODEL="gpt-3.5-turbo"
   ```

   **阿里云 DNS 配置**
   ```bash
   export ALIBABA_CLOUD_ACCESS_KEY_ID="your-access-key-id"
   export ALIBABA_CLOUD_ACCESS_KEY_SECRET="your-access-key-secret"
   export ALIBABA_CLOUD_REGION_ID="cn-hangzhou"
   ```

   **腾讯云 DNS 配置**
   ```bash
   export TENCENT_SECRET_ID="your-secret-id"
   export TENCENT_SECRET_KEY="your-secret-key"
   export TENCENT_REGION_ID="ap-guangzhou"
   ```

### Chat 对象使用

示例1，多轮对话：

```python
# 初次对话
chat = Chat("Hello!")
resp = chat.get_response()

# 继续对话
chat.user("How are you?")
next_resp = chat.get_response()

# 人为添加返回内容
chat.user("What's your name?")
chat.assistant("My name is GPT-3.5.")

# 保存对话内容
chat.save("chat.json", mode="w") # 默认为 "a"

# 打印对话历史
chat.print_log()
```

示例2，批量处理数据（串行），并使用缓存文件 `chat.jsonl`：

```python
# 串行处理（按需保存）
msgs = ["1", "2", "3", "4", "5", "6", "7", "8", "9"]
results = []
for m in msgs:
    chat = Chat()
    chat.system("你是一个熟练的数字翻译家。")
    resp = chat.user(f"请将该数字翻译为罗马数字：{m}").get_response()
    results.append(resp.content)
    chat.save("chat.jsonl", mode="a")
```

示例3，异步并发与流式输出：

```python
import asyncio
from chattool import Chat

async def run():
    # 并发问答
    base = Chat().system("你是一个有用的助手")
    tasks = [base.copy().user(f"请解释：主题 {i}").async_get_response() for i in range(2)]
    responses = await asyncio.gather(*tasks)
    for r in responses:
        print(r.content)

    # 流式输出
    print("流式: ", end="")
    async for chunk in Chat().user("写一首关于春天的短诗").async_get_response_stream():
        if chunk.delta_content:
            print(chunk.delta_content, end="", flush=True)
    print()

asyncio.run(run())
```

### MCP 服务

ChatTool 内置了符合 [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) 标准的服务端，允许 LLM 客户端（如 Claude Desktop, Cursor）直接调用 ChatTool 的功能。

- [MCP 服务指南](mcp/index.md)
- [DNS 管理服务](mcp/dns.md)
- [Zulip 集成服务](mcp/zulip.md)

### Zulip 知识库

ZulipKB 是 ChatTool 内置的一个知识库管理应用，旨在将 Zulip 中的聊天记录转化为本地可检索、可管理的知识资产。

- [Zulip 知识库指南](application/zulip_kb.md)
- [Zulip 知识结构](application/zulip_structure.md)

### DNS 工具箱

ChatTool 提供了统一的 DNS 管理接口，支持阿里云和腾讯云。

```python
from chattool.tools.dns import create_dns_client

# 创建阿里云客户端
aliyun = create_dns_client("aliyun")
aliyun.add_domain_record("example.com", "www", "A", "1.1.1.1")

# 创建腾讯云客户端
tencent = create_dns_client("tencent")
tencent.add_domain_record("example.com", "www", "A", "1.1.1.1")
```

**命令行工具 (CLI)**

提供了便捷的 DDNS（动态域名解析）更新工具和 SSL 证书管理：

```bash
# 获取 DNS 记录
chattool dns get test.example.com

# 设置 DNS 记录
chattool dns set test.example.com -v 1.2.3.4

# DDNS 动态域名更新 (公网 IP)
chattool dns ddns -d example.com -r home --monitor

# DDNS 动态域名更新 (局域网 IP)
chattool dns ddns -d example.com -r nas --ip-type local --local-ip-cidr 192.168.1.0/24

# SSL 证书自动更新
chattool dns cert-update -d example.com -e admin@example.com --cert-dir ./certs
```

## 开源协议

使用 MIT 协议开源。

## 更新日志

- 当前版本 `4.1.0`，统一 `Chat` API（同步/异步/流式），默认环境变量配置，改进重试与调试工具
- 历史：`2.x-3.x` 阶段逐步完善异步处理与批量用法
- 更早版本沿革请参考仓库提交记录
