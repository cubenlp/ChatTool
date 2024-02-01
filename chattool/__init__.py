"""Top-level package for Chattool."""

__author__ = """Rex Wang"""
__email__ = '1073853456@qq.com'
__version__ = '3.1.0'

import os, sys, requests
from .chattool import Chat, Resp
from .checkpoint import load_chats, process_chats
from .proxy import proxy_on, proxy_off, proxy_status
from . import request
from .tokencalc import model_cost_perktoken, findcost
from .asynctool import async_chat_completion
from .functioncall import generate_json_schema, exec_python_code
from typing import Union
import dotenv

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
    base_url = os.getenv('OPENAI_API_BASE_URL') or "https://api.openai.com"
    api_base = os.getenv('OPENAI_API_BASE', os.path.join(base_url, 'v1'))
    base_url = request.normalize_url(base_url)
    api_base = request.normalize_url(api_base)
    model = os.getenv('OPENAI_API_MODEL', "gpt-3.5-turbo")
    return True

def save_envs(env_file:str):
    """Save the environment variables for the API call"""
    global api_key, base_url, model
    with open(env_file, "w") as f:
        f.write(f"OPENAI_API_KEY={api_key}\n")
        f.write(f"OPENAI_API_BASE_URL={base_url}\n")
        f.write(f"OPENAI_API_BASE={api_base}\n")
        f.write(f"OPENAI_API_MODEL={model}\n")
    return True

# load the environment variables
load_envs()

# get the platform
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
    # Network test
    try:
        requests.get(net_url, timeout=timeout)
    except:
        print("Warning: Network is not available.")
        return False
    
    ## Check the proxy status
    print("\nCheck your proxy:")
    proxy_status()

    ## Base url
    print("\nCheck your base url:")
    print(base_url)
    print("\nCheck the OpenAI Base url:")
    print(api_base)
    
    ## Please check your API key
    if test_apikey:
        print("\nPlease verify your API key:")
        print(api_key)

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

