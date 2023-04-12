# rewrite the request function

from typing import List, Dict
import requests, json
import datetime, os, warnings

base_url = "https://api.openai.com"
url = None

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
    # initialize chat url
    if url is not None: # deprecated warning
        warnings.warn("The `url` parameter is deprecated. Please use `base_url` instead.", DeprecationWarning)
        chat_url = url
    else:
        chat_url = os.path.join(base_url, "v1/chat/completions")
    
    # get response
    response = requests.post(chat_url, headers=headers, data=json.dumps(payload))
    if response.status_code != 200:
        raise Exception(response.text)
    return response.json()

def usage_status(api_key:str, duration:int=99):
    """Get usage status
    
    Args:
        api_key (str): API key
        duration (int, optional): duration to check. Defaults to 99, which is the maximum duration.
    
    Returns:
        Tuple[float, float, List[float]]: total storage, total usage, daily costs
    """
    headers = {
        "Authorization": "Bearer " + api_key,
        "Content-Type": "application/json"
    }
    # Get storage limit
    subscription_url = os.path.join(base_url, "v1/dashboard/billing/subscription")
    subscription_response = requests.get(subscription_url, headers=headers)
    if subscription_response.status_code == 200:
        data = subscription_response.json()
        total_storage = data.get("hard_limit_usd")
    else:
        raise Exception(subscription_response.text)
    # start_date
    today = datetime.datetime.now()
    start_date = (today - datetime.timedelta(days=duration)).strftime("%Y-%m-%d")
    # end_date = today + 1
    end_date = (today + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    billing_url = os.path.join(base_url, f"v1/dashboard/billing/usage?start_date={start_date}&end_date={end_date}")
    billing_response = requests.get(billing_url, headers=headers)
    # Get usage status
    if billing_response.status_code == 200:
        data = billing_response.json()
        total_usage = data.get("total_usage") / 100
        daily_costs = data.get("daily_costs")
        return total_storage, total_usage, daily_costs
    else:
        raise Exception(billing_response.text)
