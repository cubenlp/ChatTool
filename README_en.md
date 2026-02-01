<div align="center">
    <a href="https://pypi.python.org/pypi/chattool">
        <img src="https://img.shields.io/pypi/v/chattool.svg" alt="PyPI version" />
    </a>
    <a href="https://github.com/cubenlp/chattool/actions/workflows/test.yml">
        <img src="https://github.com/cubenlp/chattool/actions/workflows/test.yml/badge.svg" alt="Tests" />
    </a>
    <a href="https://chattool.cubenlp.com">
        <img src="https://img.shields.io/badge/docs-github_pages-blue.svg" alt="Documentation Status" />
    </a>
    <a href="https://codecov.io/gh/cubenlp/chattool">
        <img src="https://codecov.io/gh/cubenlp/chattool/branch/master/graph/badge.svg" alt="Coverage" />
    </a>
</div>

<div align="center">
    <img src="https://qiniu.wzhecnu.cn/PicBed6/picgo/chattool.jpeg" alt="ChatAPI Toolkit" width="360", style="border-radius: 20px;">

[English](README_en.md) | [简体中文](README.md)
</div>


<!-- 
[![Updates](https://pyup.io/repos/github/cubenlp/chattool/shield.svg)](https://pyup.io/repos/github/cubenlp/chattool/) 
-->

Toolkit for Chat API, supporting multi-turn dialogue and asynchronous data processing.

## Installation

```bash
pip install chattool --upgrade
```

## Usage

### Configuration

ChatTool uses `.env` files for centralized configuration management.

1. **Generate Configuration Template**:
   ```python
   from chattool import create_env_file
   create_env_file(".env")
   ```
   This generates a `.env` template file in the current directory containing all available configuration options.

2. **Manual Configuration**:
   You can also manually create a `.env` file or set environment variables.

   **OpenAI Configuration**
   ```bash
   export OPENAI_API_KEY="sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
   export OPENAI_API_BASE="https://api.example.com/v1" 
   export OPENAI_API_MODEL="gpt-3.5-turbo"
   ```

   **Aliyun DNS Configuration**
   ```bash
   export ALIBABA_CLOUD_ACCESS_KEY_ID="your-access-key-id"
   export ALIBABA_CLOUD_ACCESS_KEY_SECRET="your-access-key-secret"
   export ALIBABA_CLOUD_REGION_ID="cn-hangzhou"
   ```

   **Tencent DNS Configuration**
   ```bash
   export TENCENT_SECRET_ID="your-secret-id"
   export TENCENT_SECRET_KEY="your-secret-key"
   export TENCENT_REGION_ID="ap-guangzhou"
   ```

### Chat Examples

Example 1, simulate multi-turn dialogue:

```python
# first chat
chat = Chat("Hello!")
resp = chat.get_response()

# continue the chat
chat.user("How are you?")
next_resp = chat.get_response()

# add response manually
chat.user("What's your name?")
chat.assistant("My name is GPT-3.5.")

# save the chat history
chat.save("chat.json", mode="w") # default to "a"

# print the chat history
chat.print_log()
```

Example 2, process data in batch (serial), and append to a checkpoint file `chat.jsonl`:

```python
msgs = [str(i) for i in range(1, 10)]
results = []
for m in msgs:
    chat = Chat()
    chat.system("You are a helpful translator for numbers.")
    resp = chat.user(f"Translate this digit to Roman numerals: {m}").get_response()
    results.append(resp.content)
    chat.save("chat.jsonl", mode="a")
```

Example 3, asynchronous concurrency and streaming:

```python
import asyncio
from chattool import Chat

async def run():
    # concurrent Q&A
    base = Chat().system("You are a helpful assistant")
    tasks = [base.copy().user(f"Explain topic {i}").async_get_response() for i in range(2)]
    responses = await asyncio.gather(*tasks)
    for r in responses:
        print(r.content)

    # streaming output
    print("Streaming: ", end="")
    async for chunk in Chat().user("Write a short poem about spring").async_get_response_stream():
        if chunk.delta_content:
            print(chunk.delta_content, end="", flush=True)
    print()

asyncio.run(run())
```

### DNS Toolkit

ChatTool provides a unified DNS management interface supporting Alibaba Cloud and Tencent Cloud.

```python
from chattool.tools.dns import create_dns_client

# Create Aliyun client
aliyun = create_dns_client("aliyun")
aliyun.add_domain_record("example.com", "www", "A", "1.1.1.1")

# Create Tencent Cloud client
tencent = create_dns_client("tencent")
tencent.add_domain_record("example.com", "www", "A", "1.1.1.1")
```

**Command Line Interface (CLI)**

A convenient DDNS (Dynamic DNS) updater tool and SSL certificate manager are provided:

```bash
# Get DNS record
chattool dns get test.example.com

# Set DNS record
chattool dns set test.example.com -v 1.2.3.4

# Aliyun DDNS updater
chattool dns ddns -d example.com -r home --monitor

# SSL Certificate Auto-Update
chattool dns cert-update -d example.com -e admin@example.com --cert-dir ./certs
```

## License

This package is licensed under the MIT license. See the LICENSE file for more details.

## Update Log

- Current version `4.1.0`: unified `Chat` API (sync/async/stream), default env-based configuration, improved retries and debugging helpers.
- History `2.x–3.x`: iterative improvements to async and batch usage.
- For earlier changes, please refer to the repository commits.