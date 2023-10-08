import os
from typing import Union

def proxy_on(http:Union[str, None]=None, https:Union[str, None]=None):
    """Set proxy for the API call

    Args:
        http (str, optional): http proxy. Defaults to None.
        https (str, optional): https proxy. Defaults to None.
    
    Example:
        # use local proxy
        proxy_on(http="127.0.0.1:7890, https="127.0.0.1:7890")
        # use socks5 proxy
        proxy_on(http="127.0.0.1:7890, https="socks5://127.0.0.1:7891")
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