import os
from typing import Union

def proxy_on(http:Union[str, None]=None, https:Union[str, None]=None):
    """Set proxy for the API call

    Args:
        http (str, optional): http proxy. Defaults to None.
        https (str, optional): https proxy. Defaults to None.
    """
    if http is not None:
        os.environ['http_proxy'] = http
    if https is not None:
        os.environ['https_proxy'] = https

def proxy_off():
    """Turn off proxy for the API call"""
    if os.environ.get('http_proxy') is not None:
        os.environ.pop('http_proxy')
    if os.environ.get('https_proxy') is not None:
        os.environ.pop('https_proxy')

def proxy_status():
    http = os.environ.get('http_proxy')
    https = os.environ.get('https_proxy')
    if http is None:
        print("`http_proxy` is not set!")
    else:
        print(f"http_proxy:\t{http}")
    if https is None:
        print("`https_proxy` is not set!")
    else:
        print(f"https_proxy:\t{https}")

def proxy_test(url:str="www.facebook.com"):
    url = url.replace("http://", "").replace("https://", "")
    if os.system("curl -I https://"+url) != 0:
        print("Https: Curl to "+url+" failed!")
    if os.system("curl -I http://"+url) != 0:
        print("Http: Curl to "+url+" failed!")