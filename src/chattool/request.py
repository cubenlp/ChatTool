# Request functions for chattool
# Documentation: https://platform.openai.com/docs/api-reference

from typing import List, Dict, Union
import requests, json, os
from urllib.parse import urlparse, urlunparse
import warnings

def is_valid_url(url: str) -> bool:
    """Check if the given URL is valid.

    Args:
        url (str): The URL to be checked.

    Returns:
        bool: True if the URL is valid; otherwise False.
    """
    parsed_url = urlparse(url)
    return all([parsed_url.scheme, parsed_url.netloc])

def normalize_url(url: str) -> str:
    """Normalize the given URL to a canonical form.

    Args:
        url (str): The URL to be normalized.

    Returns:
        str: The normalized URL.

    Examples:
        >>> normalize_url("http://api.example.com")
        'http://api.example.com'

        >>> normalize_url("api.example.com")
        'https://api.example.com'
    """
    url = url.replace("\\", '/') # compat to windows
    parsed_url = urlparse(url)
    if not parsed_url.scheme:
        # If no scheme is specified, default to https protocol.
        parsed_url = parsed_url._replace(scheme="https")
    return urlunparse(parsed_url).replace("///", "//")

def chat_completion( api_key:str
                   , chat_url:str
                   , messages:List[Dict]
                   , model:str
                   , timeout:int = 0
                   , **options) -> Dict:
    """Chat completion API call
    Request url: https://api.openai.com/v1/chat/completions
    
    Args:
        apikey (str): API key
        chat_url (str): chat url
        messages (List[Dict]): prompt message
        model (str): model to use
        **options : options inherited from the `openai.ChatCompletion.create` function.
    
    Returns:
        Dict: API response
    """
    # request data
    payload = {
        "model": model,
        "messages": messages,
        **options
    }
    # request headers
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + api_key
    }
    chat_url = normalize_url(chat_url)
    # get response
    if timeout <= 0: timeout = None
    response = requests.post(
        chat_url, headers=headers, 
        data=json.dumps(payload), timeout=timeout)
    if response.status_code != 200:
        raise Exception(response.text)
    return response

def curl_cmd_of_chat_completion( api_key:str
                               , chat_url:str
                               , messages:List[Dict]
                               , model:str
                               , timeout:int = 0
                               , **options) -> str:
    """Chat completion API call
    Request url: https://api.openai.com/v1/chat/completions
    
    Args:
        apikey (str): API key
        chat_url (str): chat url
        messages (List[Dict]): prompt message
        model (str): model to use
        **options : options inherited from the `openai.ChatCompletion.create` function.
    
    Returns:
        Dict: API response
    """
    chat_url = normalize_url(chat_url)
    curl_cmd = f"curl -X POST '{chat_url}' \\"
    # request data
    payload = {
        "model": model,
        "messages": messages,
        **options
    }
    curl_cmd += f"\n    -H 'Content-Type: application/json' \\"
    curl_cmd += f"\n    -H 'Authorization: Bearer {api_key}' \\"
    curl_cmd += f"\n    -d '{json.dumps(payload, indent=4, ensure_ascii=False)}' \\"
    if isinstance(timeout, int) and timeout > 0:
        curl_cmd += f"\n    --max-time {timeout} \\"
    return curl_cmd.rstrip(" \\")

def valid_models(api_key:str, model_url:str, gpt_only:bool=True):
    """Get valid models
    Request url: https://api.openai.com/v1/models

    Args:
        api_key (str): API key
        base_url (str): base url
        gpt_only (bool, optional): whether to return only GPT models. Defaults to True.

    Returns:
        List[str]: list of valid models
    """
    headers = {
        "Authorization": "Bearer " + api_key,
    }
    model_response = requests.get(normalize_url(model_url), headers=headers)
    if model_response.status_code == 200:
        data = model_response.json()
        model_list = [model.get("id") for model in data.get("data")]
        return [model for model in model_list if "gpt" in model] if gpt_only else model_list
    else:
        raise Exception(model_response.text)
