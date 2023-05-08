"""Top-level package for Openai API call."""

__author__ = """Rex Wang"""
__email__ = '1073853456@qq.com'
__version__ = '0.3.9'

import os
from .chattool import Chat, Resp, chat_completion, usage_status
from .proxy import proxy_on, proxy_off, proxy_status

# read API key from the environment variable
if os.environ.get('OPENAI_API_KEY') is not None:
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key.startswith("sk-"):
        print("Warning: The default environment variable `OPENAI_API_KEY` is not a valid API key.")
else:
    api_key = None

def show_apikey():
    if api_key is not None:
        print(f"API key:\t{api_key}")
    else:
        print("API key is not set!")

def default_prompt(msg:str):
    """Default prompt message for the API call

    Args:
        msg (str): prompt message

    Returns:
        List[Dict]: default prompt message
    """
    return [{"role": "user", "content": msg},]
