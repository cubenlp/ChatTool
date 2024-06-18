"""Top-level package for Chattool."""

__author__ = """Rex Wang"""
__email__ = '1073853456@qq.com'
__version__ = '3.3.2'

import os, sys, requests, json
from .chattype import Chat, Resp
from .checkpoint import load_chats, process_chats
from .proxy import proxy_on, proxy_off, proxy_status
from . import request
from .tokencalc import model_cost_perktoken, findcost
from .asynctool import async_chat_completion
from .functioncall import generate_json_schema, exec_python_code
from typing import Union, List
import dotenv
import loguru

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
    """Load the environment variables for the API call
    
    Args:
        env (Union[None, str, dict], optional): The environment file or the environment variables. Defaults to None.
    
    Returns:
        bool: True if the environment variables are loaded successfully.
    
    Examples:
        load_envs("envfile.env")
        load_envs({"OPENAI_API_KEY":"your_api_key"})
        load_envs() # load from the environment variables
    """
    global api_key, base_url, api_base, model
    # update the environment variables
    if isinstance(env, str) and not dotenv.load_dotenv(env, override=True):
        loguru.logger.warning(f"Failed to load the environment file: {env}")
        return False
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
        print("\nThe model list:")
        print(Chat().get_valid_models(gpt_only=False))
        
    # Test hello world
    if test_response:
        print("\nTest response:", message)
        chat = Chat(message)
        chat.getresponse(max_tries=3)
        chat.print_log()

    print("\nDebug is finished.")
    return True

def resp2curl( resp:requests.Response
            , include_headers:Union[List[str], None]=None
            , exclude_headers:Union[List[str], None]=None):
    """
    Convert a Python requests response object to a cURL command.

    Args:
        resp (requests.Response): The response object from a requests call.
        include_headers (Union[List[str], None], optional): A list of headers to include in the cURL command. Defaults to None.
        exclude_headers (Union[List[str], None], optional): A list of headers to exclude from the cURL command. Defaults to None.

    Returns:
        str: A string containing the equivalent cURL command.
    """
    method = resp.request.method
    url = resp.request.url
    headers = resp.request.headers
    body = resp.request.body
    # Start forming the cURL command with method and URL
    curl_cmd = f"curl -X {method} '{url}' \\"
    # List of headers to exclude
    if exclude_headers is None:
        exclude_headers = ['Content-Length']
    if include_headers is None:
        include_headers = ['Content-Type', 'Authorization']
    # Add headers to the cURL command, excluding certain headers
    for k, v in headers.items():
        if k in exclude_headers or (include_headers is not None and k not in include_headers):
            continue
        curl_cmd += f"\n    -H '{k}: {v}' \\"
    # Add body to the cURL command, formatted as pretty JSON if possible
    if body:
        try:
            # Try to parse the body as JSON and format it
            body_json = json.loads(body)
            formatted_body = json.dumps(body_json, indent=4)
            curl_cmd += f"\n    -d '{formatted_body}'"
        except json.JSONDecodeError:
            # If the body is not valid JSON, add it as is
            curl_cmd += f"\n    -d '{body}'"
    else:
        # If there is no body, remove the trailing backslash
        curl_cmd = curl_cmd.rstrip(" \\")
    return curl_cmd
