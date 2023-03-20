# Package Name

A brief description of the package.

## Installation
To install the package, you can use pip:

```bash
$ pip install package_name
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