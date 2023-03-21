"""Top-level package for Openai API call."""

__author__ = """Rex Wang"""
__email__ = '1073853456@qq.com'
__version__ = '0.1.0'

import openai
from typing import List, Dict, Union
import os
from .response import Resp

# read API key from the environment variable
if os.environ.get('OPENAI_API_KEY') is not None:
    apikey = os.environ.get('OPENAI_API_KEY')
    if not apikey.startswith("sk-"):
        print("Warning: The default environment variable `OPENAI_API_KEY` is not a valid API key.")
    openai.api_key = apikey

def prompt2response( msg:Union[str, List[Dict]]
                   , max_requests:int=1
                   , model:str = "gpt-3.5-turbo"
                   , **options)->Resp:
    """Transform prompt to the API response
    
    Args:
        msg (Union[str, List[Dict]]): prompt message
        max_requests (int, optional): maximum number of requests to make. Defaults to 1.
        model (str, optional): model to use. Defaults to "gpt-3.5-turbo".
        **options : options for the API call.
    
    Returns:
        Resp: API response
    """
    # assert max_requests >= 0, "max_requests should be non-negative"
    assert openai.api_key is not None, "API key is not set!"

    # initialize prompt message
    if isinstance(msg, str): 
        msg = default_prompt(msg)
    
    # default options
    if not len(options):
        options = {}
    # make request
    resp = Resp()
    while max_requests:
        numoftries = 0
        try:
            resp.response = openai.ChatCompletion.create(
                messages=msg, model=model,
                **options)
        except:
            max_requests -= 1
            numoftries += 1
            print(f"API call failed! Try again ({numoftries})")
            continue
        break
    else:
        raise Exception("API call failed!\nYou can try to update the API key"
                        + ", increase `max_requests` or set proxy.")
    return resp

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
    host = host.replace("http://", "").replace("https://", "")
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
        print(f"http_proxy:\t{http}")
    if https is None:
        print("`https_proxy` is not set!")
    else:
        print(f"https_proxy:\t{https}")

def show_apikey():
    if openai.api_key is not None:
        print(f"API key:\t{openai.api_key}")
    else:
        print("API key is not set!")
    
        