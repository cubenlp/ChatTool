"""Top-level package for Openai API call."""

__author__ = """Rex Wang"""
__email__ = '1073853456@qq.com'
__version__ = '0.5.2'

import os, requests
from .chattool import Chat, Resp, chat_completion, usage_status
from .checkpoint import load_chats, process_chats
from .proxy import proxy_on, proxy_off, proxy_status
from . import request


# read API key from the environment variable
if os.environ.get('OPENAI_API_KEY') is not None:
    api_key = os.environ.get('OPENAI_API_KEY')
    # skip checking the validity of the API key
    # if not api_key.startswith("sk-"):
    #     print("Warning: The default environment variable `OPENAI_API_KEY` is not a valid API key.")
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

def show_base_url():
    """Show the base url of the API call"""
    print(f"Base url:\t{request.base_url}")

def debug_log( net_url:str="https://www.baidu.com"
             , timeout:int=5
             , message:str="hello world! 你好！"
             , test_usage:bool=True
             , test_response:bool=True):
    """Debug the API call

    Args:
        net_url (str, optional): The url to test the network. Defaults to "https://www.baidu.com".
        timeout (int, optional): The timeout for the network test. Defaults to 5.
        test_usage (bool, optional): Whether to test the usage status. Defaults to True.
        test_response (bool, optional): Whether to test the hello world. Defaults to True.
    
    Returns:
        bool: True if the debug is finished.
    """
    # 1. Test whether the network is available
    try:
        requests.get(net_url, timeout=timeout)
    except:
        print("Warning: Network is not available.")
        return False
    
    print("Your network is available.")
    
    # 2. Check the API key
    print("\nPlease verify the API key:")
    show_apikey()

    # 3. Check the proxy status
    print("\nYour proxy status:")
    proxy_status()
    print("Note that, you don't need to set proxy if your `base_url` has done it!")

    # 4. Base url
    print("\nCheck your base url:")
    show_base_url()
    if request.url is not None:
        print("Warning: the `url` parameter is deprecated, please use `base_url` instead.")

    # 5. Get usage status
    if test_usage:
        print("\nThe usage status of your API key:")
        Chat().show_usage_status(recent=3)

    # 6. Test hello world
    if test_response:
        print("\nTest message:", message)
        chat = Chat(message)
        chat.getresponse(max_requests=3)
        chat.print_log()

    print("\nDebug is finished.")
    return True