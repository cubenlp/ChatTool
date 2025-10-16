import requests
import json
from typing import Union, List, Dict
from urllib.parse import urlparse, urlunparse

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
