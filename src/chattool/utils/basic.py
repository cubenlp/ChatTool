import requests
from pathlib import Path
from typing import Union, Optional

import chattool
import chattool.const
from chattool.config import BaseEnvConfig

def load_envs(path:Union[str, Path, None] = None):
    """Load the environment variables for the API call
    
    Args:
        path (Union[str, Path], optional): The path to the environment file. 
        If None, attempts to find .env in default locations.
        
    Returns:
        bool: True if the environment variables are loaded successfully.
        
    Examples:
        load_envs("envfile.env")
        load_envs() # tries to find .env automatically
    """
    if path is None:
        # Try to find .env in current or parent directories
        # Simple strategy: look in current dir
        import os
        if os.path.exists(".env"):
            path = ".env"
        # If still None, we might just rely on OS envs, but BaseEnvConfig.load_all expects a path
        # Actually BaseEnvConfig.load_all uses dotenv_values(env_path), if env_path is None dotenv might not like it
        # or might load nothing.
        
        # Let's check dotenv behavior. dotenv_values(None) -> {}
        # But we want to support default behavior.
        # If path is None, let's assume we want to load from .env if it exists
        if path is None:
             # Fallback to empty load if no file found, but still trigger refresh from os.environ
             # Wait, BaseEnvConfig.load_from_dict merges dict > os.getenv > default.
             # So even with empty dict, it will refresh from os.getenv.
             # We can pass an empty path or handle it.
             # But dotenv_values requires a path-like or stream.
             
             # Let's try to locate it relative to project root if possible, or just skip file loading
             # and only refresh from os.environ
             pass

    if path:
        BaseEnvConfig.load_all(path)
    else:
        # Just refresh from OS envs
        BaseEnvConfig.load_from_dict({})
    
    # Inject loaded values into const module
    # This keeps chattool.const.SOME_KEY up-to-date
    vars(chattool.const).update(BaseEnvConfig.get_all_values())
    
    # Re-apply special logic for OPENAI_API_BASE in const
    # (Since we just overwrote everything, we need to ensure the derived logic runs)
    
    _api_base = chattool.const.OPENAI_API_BASE
    _api_base_url = chattool.const.OPENAI_API_BASE_URL
    
    # However, to be safe and consistent with const.py behavior:
    if not _api_base and _api_base_url:
         chattool.const.OPENAI_API_BASE = _api_base_url.rstrip('/') + '/v1'
         
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

    # Print all configurations using the new framework
    # This replaces manual printing of base_url, model, key etc.
    BaseEnvConfig.print_config()

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
