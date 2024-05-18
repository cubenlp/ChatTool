"""Top-level package for Chattool."""

__author__ = """Rex Wang"""
__email__ = '1073853456@qq.com'
__version__ = '3.1.7'

import os, sys, requests
from .chattype import Chat, Resp
from .checkpoint import load_chats, process_chats
from .proxy import proxy_on, proxy_off, proxy_status
from . import request
from .tokencalc import model_cost_perktoken, findcost
from .asynctool import async_chat_completion
from .functioncall import generate_json_schema, exec_python_code
from typing import Union
import dotenv 

raw_env_text = f"""# Description: Env file for ChatTool.
# Current version: {__version__}

# The base url of the API (with suffix /v1)
# This will override OPENAI_API_BASE_URL if both are set.
OPENAI_API_BASE=''

# The base url of the API (without suffix /v1)
OPENAI_API_BASE_URL=''

# Your API key
OPENAI_API_KEY=''

# The default model name
OPENAI_API_MODEL=''
"""

def load_envs(env:Union[None, str, dict]=None):
    """Read the environment variables for the API call"""
    global api_key, base_url, api_base, model
    # update the environment variables
    if isinstance(env, str):
        dotenv.load_dotenv(env, override=True)
    elif isinstance(env, dict):
        for key, value in env.items():
            os.environ[key] = value
    # else: load from environment variables
    api_key = os.getenv('OPENAI_API_KEY')
    base_url = os.getenv('OPENAI_API_BASE_URL') # or "https://api.openai.com"
    api_base = os.getenv('OPENAI_API_BASE') # or os.path.join(base_url, 'v1')
    model = os.getenv('OPENAI_API_MODEL') # or "gpt-3.5-turbo"
    return True

def save_envs(env_file:str):
    """Save the environment variables for the API call"""
    global api_key, base_url, model, api_base
    set_key = lambda key, value: dotenv.set_key(env_file, key, value) if value else None
    with open(env_file, "w") as f:
        f.write(raw_env_text)
    set_key('OPENAI_API_KEY', api_key)
    set_key('OPENAI_API_BASE_URL', base_url)
    set_key('OPENAI_API_BASE', api_base)
    set_key('OPENAI_API_MODEL', model)
    return True

# load the environment variables
load_envs()

# get the platform
# tqdm.asyncio.tqdm.gather differs on different platforms
platform = sys.platform
if platform.startswith("win"):
    platform = "windows"
elif platform.startswith("linux"):
    platform = "linux"
elif platform.startswith("darwin"):
    platform = "macos"

def default_prompt(msg:str):
    """Default prompt message for the API call

    Args:
        msg (str): prompt message

    Returns:
        List[Dict]: default prompt message
    """
    return [{"role": "user", "content": msg},]

def get_valid_models(api_key:str=api_key, base_url:str=base_url):
    """Get valid models

    Returns:
        List[str]: list of valid models
    """
    return request.valid_models(api_key, base_url)

def print_secure_api_key(api_key):
    if api_key:
        length = len(api_key)
        if length == 1 or length == 2:
            masked_key = '*' * length
        elif 3 <= length <= 6:
            masked_key = api_key[0] + '*' * (length - 2) + api_key[-1]
        elif 7 <= length <= 14:
            masked_key = api_key[:2] + '*' * (length - 4) + api_key[-2:]
        elif 15 <= length <= 30:
            masked_key = api_key[:4] + '*' * (length - 8) + api_key[-4:]
        else:
            masked_key = api_key[:8] + '*' * (length - 12) + api_key[-8:]
        print("\nPlease verify your API key:")
        print(masked_key)
    else:
        print("No API key provided.")

def debug_log( net_url:str="https://www.baidu.com"
             , timeout:int=5
             , message:str="hello world! 你好！"
             , test_apikey:bool=True
             , test_response:bool=True
             , test_model:bool=True):
    """Debug the API call

    Args:
        net_url (str, optional): The url to test the network. Defaults to "https://www.baidu.com".
        timeout (int, optional): The timeout for the network test. Defaults to 5.
        test_usage (bool, optional): Whether to test the usage status. Defaults to True.
        test_response (bool, optional): Whether to test the hello world. Defaults to True.
    
    Returns:
        bool: True if the debug is finished.
    """
    print("Current version:", __version__)
    # Network test
    try:
        requests.get(net_url, timeout=timeout)
    except:
        print("Warning: Network is not available.")
        return False
    
    ## Check the proxy status
    print("\nCheck your proxy: " +\
          "This is not necessary if the base url is already a proxy link.")
    proxy_status()

    ## Base url
    print("\nCheck the value OPENAI_API_BASE_URL:")
    print(base_url)
    print("\nCheck the value OPENAI_API_BASE: " +\
          "This will override OPENAI_API_BASE_URL if both are set.")
    print(api_base)

    ## Model
    print("\nYour default OPENAI_API_MODEL:")
    print(model)
    
    ## Please check your API key
    if test_apikey:
        print_secure_api_key(api_key)

    # Get model list
    if test_model:
        print("\nThe model list(contains gpt):")
        print(Chat().get_valid_models())
        
    # Test hello world
    if test_response:
        print("\nTest response:", message)
        chat = Chat(message)
        chat.getresponse(max_tries=3)
        chat.print_log()

    print("\nDebug is finished.")
    return True
