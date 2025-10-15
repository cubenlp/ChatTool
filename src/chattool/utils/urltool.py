import requests
import json
from typing import Union, List

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
