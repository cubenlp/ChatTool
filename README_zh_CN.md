# OpenAI API Call

OpenAI API 的简单封装，用于发送 prompt message 并返回 response。

## 安装方法
当前模块未发布到 PyPI，因此需要先 clone 本仓库，然后在本地调用：

```bash
git clone https://github.com/RexWzh/openai_api_call.git
cd openai_api_call
python # 进入 Python 解释器
```

## 使用示例
简单示例：

```python
import openai_api_call
from openai_api_call import prompt2response, show_apikey

# 设置 API key（或者在环境变量中设置）
# openai.api_key = "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
show_apikey() # 查看当前 API key

# 发送 prompt message 并返回 response
prompt = "Hello, GPT-3.5!"
print(prompt2response(prompt, contentonly=True))
```
其中 API 密钥可以在 `.bashrc` 结尾处添加如下代码，进行设置：

```bash
export OPENAI_API_KEY="sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

设置代理：

```python
from openai_api_call import proxy_on, proxy_off, show_proxy
show_proxy() # 查看当前代理
proxy_on("127.0.0.1") # 本地代理，端口默认为 7890
show_proxy() # 查看更新后的代理
print(prompt2response("Hello!", contentonly=True))
proxy_off() # 关闭代理
```

其他选项：

```python
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
