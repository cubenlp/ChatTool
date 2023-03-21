# OpenAI API Call

OpenAI API 的简单封装，用于发送 prompt message 并返回 response。

## 安装方法

```bash
pip install git+https://github.com/RexWzh/openai_api_call.git
```

## 使用方法

### 设置 API 密钥

```py
import openai
openai.api_key = "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

或者直接在 `~/.bashrc` 中设置 `OPENAI_API_KEY`，每次启动终端可以自动设置：

```bash
# 在 ~/.bashrc 中添加如下代码
export OPENAI_API_KEY="sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

### 设置代理（可选）

```py
from openai_api_call import proxy_on, proxy_off, show_proxy
# 查看当前代理
show_proxy()

# 设置本地代理，端口号默认为 7890
proxy_on("127.0.0.1", port=7890)

# 查看更新后的代理
show_proxy()

# 关闭代理
proxy_off() 
```

### 基本使用

示例一，发送 prompt 并返回信息：
```python
from openai_api_call import prompt2response, show_apikey

# 检查 API 密钥是否设置
show_apikey()

# 查看是否开启代理
show_proxy()

# 发送 prompt 并返回 response
prompt = "Hello, GPT-3.5!"
print(prompt2response(prompt, contentonly=True))
```


示例二，自定义消息模板，并返回信息和消耗的 tokens 数量：

```python
import openai_api_call
from openai_api_call import getntoken, getcontent

# 自定义发送模板
openai_api_call.default_prompt = lambda msg: [
    {"role": "system", "content": "帮我翻译这段文字"},
    {"role": "user", "content": msg}
]
prompt = "Hello!"
# 设置重试次数为 Inf
response = prompt2response(prompt, temperature=0.5, max_requests=-1)
print("消耗 tokens 数量：", getntoken(response))
print("返回内容：", getcontent(response))
```

## 开源协议

这个项目使用 MIT 协议开源。

## 未来计划

* TODO

## 致谢

这个项目是使用 [Cookiecutter](https://github.com/audreyr/cookiecutter) 和 [audreyr/cookiecutter-pypackage](https://github.com/audreyr/cookiecutter-pypackage) 模板创建的。
