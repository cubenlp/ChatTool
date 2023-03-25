from openai_api_call import proxy_off, proxy_on, proxy_status
import os

def test_proxy():
    proxy_off()
    assert os.environ.get('http_proxy') is None
    assert os.environ.get('https_proxy') is None
    proxy_on(http="127.0.0.1:7890", https="socks://127.0.0.1:7891")
    assert os.environ.get('http_proxy') == "127.0.0.1:7890"
    assert os.environ.get('https_proxy') == "socks://127.0.0.1:7891"
    proxy_off()
    assert os.environ.get('http_proxy') is None
    assert os.environ.get('https_proxy') is None
    proxy_status()
    assert True