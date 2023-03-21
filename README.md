> 以下为 ChatGPT 自动生成的 README.md 文件（待修改），中文文档移步[这里](README_zh_CN.md)。

# Openai API call

[![PyPI version](https://img.shields.io/pypi/v/openai_api_call.svg)](https://pypi.python.org/pypi/openai_api_call)
[![Build Status](https://img.shields.io/travis/RexWzh/openai_api_call.svg)](https://travis-ci.com/RexWzh/openai_api_call)
[![Documentation Status](https://readthedocs.org/projects/openai-api-call/badge/?version=latest)](https://openai-api-call.readthedocs.io/en/latest/?version=latest)
[![Updates](https://pyup.io/repos/github/RexWzh/openai_api_call/shield.svg)](https://pyup.io/repos/github/RexWzh/openai_api_call/)

A short wrapper of the OpenAI api call.

* Free software: MIT license
* Documentation: https://openai-api-call.readthedocs.io.

## Installation
To install the package, you can use pip:

```bash
pip install git+https://github.com/RexWzh/openai_api_call.git
```

## Usage

The main module of this package provides a function called `prompt2response`, which sends a prompt message to GPT-3 and returns the response. Here's an example:

```python
import package_name

msg = "Hello, GPT-3!"
res = package_name.prompt2response(msg)
print(res)
```

This will send the prompt message "Hello, GPT-3!" to GPT-3 using the default options and return the response.

You can also customize the behavior of `prompt2response` by passing in additional arguments:

- `contentonly`: if set to True, only the response message content will be returned (default is False).
- `max_requests`: maximum number of times to retry if the request fails (default is 0).
- `options`: a dictionary of options to pass to the OpenAI API (default is {"model":"gpt-3.5-turbo"}).

## Examples

Here are some more examples of how to use the package:

```python
# Send a prompt message and get only the response message content
res = package_name.prompt2response("What is the meaning of life?", contentonly=True)
print(res)

# Send multiple prompt messages and get the total number of tokens used
res1 = package_name.prompt2response("How are you?")
res2 = package_name.prompt2response("What's your name?")
total_tokens = package_name.getntoken(res1) + package_name.getntoken(res2)
print(total_tokens)
```

## License

This package is licensed under the MIT license. See the LICENSE file for more details.

## Features

* TODO

## Credits

This package was created with [Cookiecutter](https://github.com/audreyr/cookiecutter) and the [audreyr/cookiecutter-pypackage](https://github.com/audreyr/cookiecutter-pypackage) project template.
