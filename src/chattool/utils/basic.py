import chattool
import chattool.const
from typing import Union, Optional
from pathlib import Path
import dotenv
import requests

def get_secure_api_key(api_key):
    if not api_key:
        return ""
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
    return masked_key

raw_env_text = """# Description: Env file for ChatTool.
# Current version: {version}

# The base url of the API (with suffix /v1)
# This will override OPENAI_API_BASE_URL if both are set.
OPENAI_API_BASE='{OPENAI_API_BASE}'

# The base url of the API (without suffix /v1)
OPENAI_API_BASE_URL={OPENAI_API_BASE_URL}

# Your API key
OPENAI_API_KEY='{OPENAI_API_KEY}'

# The default model name
OPENAI_API_MODEL='{OPENAI_API_MODEL}'
"""

def load_envs(path:Union[str, Path]):
    """Load the environment variables for the API call
    
    Args:
        path (Union[str, Path]): The path to the environment file.
        
    Returns:
        bool: True if the environment variables are loaded successfully.
        
    Examples:
        load_envs("envfile.env")
    """
    vals = dotenv.dotenv_values(path)
    if 'OPENAI_API_KEY' in vals:
        chattool.const.OPENAI_API_KEY = vals['OPENAI_API_KEY']
    if 'OPENAI_API_BASE_URL' in vals:
        chattool.const.OPENAI_API_BASE_URL = vals['OPENAI_API_BASE_URL']
    if 'OPENAI_API_BASE' in vals:
        chattool.const.OPENAI_API_BASE = vals['OPENAI_API_BASE']
    if 'OPENAI_API_MODEL' in vals:
        chattool.const.OPENAI_API_MODEL = vals['OPENAI_API_MODEL']

def create_env_file(env_file:Union[str, Path], env_vals:Optional[dict] = None):
    """Create the environment file for the API call
    
    Args:
        env_file (Union[str, Path]): The path to the environment file.
        env_vals (Optional[dict], optional): The environment variables. Defaults to None.
        
    Returns:
        bool: True if the environment file is created successfully.
    """
    if env_vals is None:
        env_vals = {
            'OPENAI_API_KEY': chattool.const.OPENAI_API_KEY,
            'OPENAI_API_BASE_URL': chattool.const.OPENAI_API_BASE_URL,
            'OPENAI_API_BASE': chattool.const.OPENAI_API_BASE,
            'OPENAI_API_MODEL': chattool.const.OPENAI_API_MODEL,
        }
    env_file = Path(env_file)
    env_file.parent.mkdir(parents=True, exist_ok=True)
    with open(env_file, "w") as f:
        f.write(raw_env_text.format(version=chattool.__version__, **env_vals))
    return True

# get_valid_models function removed due to dependency issues
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
    print("Current version:", chattool.__version__)
    # Network test
    try:
        requests.get(net_url, timeout=timeout)
    except:
        print("Warning: Network is not available.")
        return False

    ## Base url
    print("\nCheck the value OPENAI_API_BASE_URL:")
    print(chattool.const.OPENAI_API_BASE_URL)
    print("\nCheck the value OPENAI_API_BASE: " +\
          "This will override OPENAI_API_BASE_URL if both are set.")
    print(chattool.const.OPENAI_API_BASE)

    ## Model
    print("\nYour default OPENAI_API_MODEL:")
    print(chattool.const.OPENAI_API_MODEL)
    
    ## Please check your API key
    if test_apikey:
        print_secure_api_key(chattool.const.OPENAI_API_KEY)

    # Get model list
    if test_model:
        print("\nThe model list:")
        print("Model list functionality temporarily disabled")
        
    # Test hello world
    if test_response:
        print("\nTest response:", message)
        chat = chattool.Chat()
        chat.user(message)
        print("Response functionality temporarily disabled")

    print("\nDebug is finished.")
    return True
