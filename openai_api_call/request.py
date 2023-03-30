# rewrite the request function

from typing import List, Dict
import requests, json
url = "https://api.openai.com/v1/chat/completions"

## TODO: catch error types
def chat_completion(api_key:str, messages:List[Dict], model:str, **options) -> Dict:
    """Chat completion API call
    
    Args:
        apikey (str): API key
        messages (List[Dict]): prompt message
        model (str): model to use
        **options : options inherited from the `openai.ChatCompletion.create` function.
    
    Returns:
        Dict: API response
    """
    # request data
    payload = {
        "model": model,
        "messages": messages
    }
    # inherit options
    payload.update(options)
    # request headers
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + api_key
    }
    # get response
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    return response.json()
