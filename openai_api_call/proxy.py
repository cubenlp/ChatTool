import os

def proxy_on(host:str, port:int=7890):
    """Set proxy for the API call

    Args:
        host (str): proxy host
        port (int, optional): proxy port. Defaults to 7890.
    """
    host = host.replace("http://", "").replace("https://", "")
    os.environ['http_proxy'] = f"http://{host}:{port}"
    os.environ['https_proxy'] = f"https://{host}:{port}"

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
