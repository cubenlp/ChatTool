import asyncio
import requests
from pathlib import Path
from typing import Union, Optional

import chattool
from chattool.config import BaseEnvConfig

def load_envs(path:Optional=None):
    # Deprecated
    return True

def create_env_file(env_file:Union[str, Path], env_vals:Optional[dict] = None):
    """Create the environment file for the API call
    
    Args:
        env_file (Union[str, Path]): The path to the environment file.
        env_vals (Optional[dict], optional): The environment variables. Defaults to None.
        
    Returns:
        bool: True if the environment file is created successfully.
    """
    env_file = Path(env_file)
    env_file.parent.mkdir(parents=True, exist_ok=True)
    
    # If user provided specific values, update the config temporarily
    if env_vals:
        for key, value in env_vals.items():
            for config_cls in BaseEnvConfig._registry:
                if key in config_cls.get_fields():
                    config_cls.get_fields()[key].value = value
    
    # Generate content using the config framework
    content = BaseEnvConfig.generate_env_template(chattool.__version__)
    
    with open(env_file, "w") as f:
        f.write(content)
    return True

def debug_log( net_url:str="https://www.baidu.com"
             , timeout:int=5
             , message:str="hello world! 你好！"
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
    print("Current version:", chattool.__version__)
    # Network test
    print("\nNetwork test:")
    try:
        requests.get(net_url, timeout=timeout)
    except:
        print("Warning: Network is not available.")
        return False

    # Print all configurations using the new framework
    # This replaces manual printing of base_url, model, key etc.
    BaseEnvConfig.print_config()

    # Test hello world
    if test_response:
        print("\nTest response:", message)
        chat = chattool.Chat()
        chat.user(message)
        print("Response functionality temporarily disabled")

    print("\nDebug is finished.")
    return True

def setup_jupyter_async():
    try:
        from IPython import get_ipython
        if get_ipython() is not None:
            import nest_asyncio
            loop = asyncio.get_running_loop()
            if not hasattr(loop, '_nest_asyncio_patched'):
                nest_asyncio.apply()
                # 标记已经应用过
                loop._nest_asyncio_patched = True
    except Exception:
        pass

def mask_secret(api_key: str) -> str:
    """Mask the secret key
    
    Args:
        api_key (str): The secret key to be masked.
    
    Returns:
        str: The masked secret key.
    """
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
