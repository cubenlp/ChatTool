"""Top-level package for Openai API call."""

__author__ = """Rex Wang"""
__email__ = '1073853456@qq.com'
__version__ = '0.1.0'

import openai
from typing import List, Dict, Union
import os

# read API key from the environment variable
if os.environ.get('OPENAI_API_KEY') is not None:
    apikey = os.environ.get('OPENAI_API_KEY')
    if not apikey.startswith("sk-"):
        print("Warning: The default environment variable `OPENAI_API_KEY` is not a valid API key.")
    openai.api_key = apikey

def prompt2response( msg:str
                   , contentonly:bool=False
                   , max_requests:int=1
                   , **options):
    """Transform prompt to the API response
    
    Args:
        msg (str): prompt message
        contentonly (bool, optional): whether to return only the content of the response. Defaults to False.
        max_requests (int, optional): maximum number of requests to make. Defaults to 1.
        **options : options for the API call.
    
    Returns:
        dict: API response
    """
    assert max_requests >= 0, "max_requests should be non-negative"
    # initial prompt message
    if isinstance(msg, str): 
        msg = default_prompt(msg)
    # default options
    if not len(options):
        options = {"model":"gpt-3.5-turbo"}
    # make request
    res = {}
    while max_requests:
        try:
            res = openai.ChatCompletion.create(
                  messages=msg, **options)
        except:
            max_requests -= 1
            continue
        break
    else:
        raise Exception("API call failed! You can try to update the API key"
                        + ", increase `max_requests` or set proxy.")
    return getcontent(res) if contentonly else res

getntoken = lambda res: res['usage']['total_tokens']
getcontent = lambda res: res['choices'][0]['message']['content']

def default_prompt(msg:str):
    """Default prompt message for the API call

    Args:
        msg (str): prompt message

    Returns:
        List[Dict]: default prompt message
    """
    return [{"role": "user", "content": msg},]

def proxy_on(host:str, port:int=7890):
    """Set proxy for the API call

    Args:
        host (str): proxy host
        port (int, optional): proxy port. Defaults to 7890.
    """
    os.environ['http_proxy'] = f"http://{host}:{port}"
    os.environ['https_proxy'] = f"https://{host}:{port}"

def proxy_off():
    """Turn off proxy for the API call"""
    if os.environ.get('http_proxy') is not None:
        os.environ.pop('http_proxy')
    if os.environ.get('https_proxy') is not None:
        os.environ.pop('https_proxy')

def show_proxy():
    http = os.environ.get('http_proxy')
    https = os.environ.get('https_proxy')
    if http is None:
        print("`http_proxy` is not set!")
    else:
        print(f"http_proxy:http://{http}")
    if https is None:
        print("`https_proxy` is not set!")
    else:
        print(f"https_proxy:https://{https}")

    