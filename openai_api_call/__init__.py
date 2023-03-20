"""Top-level package for Openai API call."""

__author__ = """Rex Wang"""
__email__ = '1073853456@qq.com'
__version__ = '0.1.0'

import openai
import openai_api_call.data as data
from typing import List, Dict, Union

def prompt2response( msg:str
                   , contentonly:bool=False
                   , max_requests:int=0
                   , **options):
    """Transform prompt to the API response
    
    Args:
        msg (str): prompt message
        contentonly (bool, optional): whether to return only the content of the response. Defaults to False.
        max_requests (int, optional): maximum number of requests to make. Defaults to 0.
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
    while max_requests-1:
        try:
            res = openai.ChatCompletion.create(
                  messages=msg, **options)
        except:
            max_requests -= 1
            continue
        break
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